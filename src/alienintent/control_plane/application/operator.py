"""Named operator application services; CLI adapters never write the store."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, is_dataclass
import logging
from typing import Any

from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.escalation import DecisionSubmission


logger = logging.getLogger(__name__)


class OperatorDenied(ValueError):
    pass


class OperatorControlPlane:
    def __init__(self, profile: str, store: Any, work: Any, coordinator: Any, readiness: Callable[[], bool], clock: Callable[[], str] = lambda: "not-recorded") -> None:
        self._profile, self._store, self._work, self._coordinator, self._readiness, self._clock = profile, store, work, coordinator, readiness, clock

    def status(self) -> dict[str, object]:
        diagnostics: list[dict[str, object]] = []
        try:
            upstream = {"source": "work-management", "status": "available", "items": [item.identity for item in self._work.import_ready_snapshot()]}
        except Exception:
            upstream = {"source": "work-management", "status": "unavailable"}
            diagnostics.append(self._coalesce_diagnostic("upstream-unavailable", "work-management unavailable"))
        items = [
            {"identity": identity.removeprefix("factory:"), "revision": version, "lifecycle": state.get("stage"), "outcome": state.get("outcome")}
            for identity, version, state in self._store.list_states(self._profile, "factory:")
        ]
        delivery = getattr(self._coordinator, "delivery_health", {})
        projection = "healthy" if delivery and all(value.delivered for value in delivery.values()) else "unknown"
        logger.info("operator_status", extra={"profile": self._profile, "upstream": upstream["status"], "projection": projection})
        return {"profile": self._profile, "upstream": upstream, "execution": {"source": "operational-store", "status": "known", "items": items, "wip": len(items)}, "projection": {"source": "decision-notifier", "status": projection}, "diagnostics": diagnostics}

    def _coalesce_diagnostic(self, condition: str, message: str) -> dict[str, object]:
        """Persist changed-condition evidence without emitting duplicate diagnostics."""
        identity = f"control-plane-diagnostic:{condition}"
        # Status must remain available during an outage even when another
        # operator records the same persistent condition concurrently.
        for _ in range(4):
            version, prior = self._store.read_state(self._profile, identity)
            now = self._clock()
            transition = not prior or prior.get("message") != message
            state = {
                "condition": condition, "message": message,
                "first_seen": now if transition else prior.get("first_seen"), "last_seen": now,
                "repeat_count": 1 if transition else int(prior.get("repeat_count", 0)) + 1,
            }
            try:
                self._store.commit(self._profile, identity, version, state)
                return state | {"transition": transition}
            except Exception as error:
                from alienintent.execution_coordination.ports.operational_store import VersionConflict
                if not isinstance(error, VersionConflict):
                    raise
        return {"condition": condition, "message": "work-management unavailable", "transition": False, "coalescing": "contended"}

    def explain(self, target: str) -> dict[str, object]:
        account = self._coordinator.guard_account(target)
        evidence = account.pop("evidence")
        account.pop("target", None)
        return {"target": target, "guard_outcomes": account, "evidence": evidence}

    def run(self, **fields: object) -> object:
        self._admit(fields)
        if not self._readiness():
            raise OperatorDenied("readiness gate failed; autonomous work was not started")
        return self._coordinator.start()

    def resume(self, **fields: object) -> object:
        self._admit(fields)
        self._coordinator.reconcile(str(fields["target"]))
        if not self._readiness():
            raise OperatorDenied("readiness gate failed; autonomous work was not started")
        return self._coordinator.start()

    def cancel(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.cancel(str(fields["target"]), str(fields["actor"]), str(fields["authority"]), int(fields["expected_version"]), str(fields["reason"]), str(fields["idempotency_key"]))

    def stop(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.stop_owned(str(fields["actor"]), str(fields["authority"]), int(fields["expected_version"]), str(fields["reason"]), str(fields["idempotency_key"]))

    def reconcile(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.reconcile(str(fields["target"]))

    def decisions_list(self) -> list[dict[str, object]]:
        return [asdict(value) for value in DecisionInbox(self._store, self._coordinator, self._profile).list_open()]

    def decisions_show(self, identity: str) -> dict[str, object]:
        value = DecisionInbox(self._store, self._coordinator, self._profile).show(identity)
        return asdict(value) if is_dataclass(value) else value

    def decisions_decide(self, identity: str, **fields: object) -> dict[str, object]:
        self._admit(fields)
        biu_version = fields.get("biu_version")
        if not isinstance(biu_version, int) or biu_version < 0:
            raise OperatorDenied("BIU version is required")
        record = DecisionInbox(self._store, self._coordinator, self._profile).submit(DecisionSubmission(str(fields["actor"]), str(fields["authority"]), identity, biu_version, int(fields["expected_version"]), str(fields["idempotency_key"]), str(fields["choice"])))
        return asdict(record)

    def _admit(self, fields: dict[str, object]) -> None:
        required = ("actor", "authority", "target", "intent", "reason", "idempotency_key")
        if any(not isinstance(fields.get(key), str) or not fields[key] for key in required):
            raise OperatorDenied("actor, authority, target, intent, reason and idempotency key are required")
        expected = fields.get("expected_version")
        if not isinstance(expected, int) or expected < 0:
            raise OperatorDenied("expected version is required")
        revision, state = self._store.read_state(self._profile, f"factory:{fields['target']}")
        prior = state.get("cancellation") if state else None
        if isinstance(prior, dict) and prior.get("idempotency_key") == fields["idempotency_key"]:
            return
        if state and revision != expected:
            raise OperatorDenied("stale expected version")
