"""Named operator application services; CLI adapters never write the store."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from typing import Any

from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.escalation import DecisionSubmission


class OperatorDenied(ValueError):
    pass


class OperatorControlPlane:
    def __init__(self, profile: str, store: Any, work: Any, coordinator: Any, readiness: Callable[[], bool]) -> None:
        self._profile, self._store, self._work, self._coordinator, self._readiness = profile, store, work, coordinator, readiness

    def status(self) -> dict[str, object]:
        try:
            upstream = {"source": "work-management", "status": "available", "items": [item.identity for item in self._work.import_ready_snapshot()]}
        except Exception:
            upstream = {"source": "work-management", "status": "unavailable"}
        items = [
            {"identity": identity.removeprefix("factory:"), "revision": version, "lifecycle": state.get("stage"), "outcome": state.get("outcome")}
            for identity, version, state in self._store.list_states(self._profile, "factory:")
        ]
        delivery = getattr(self._coordinator, "delivery_health", {})
        return {"profile": self._profile, "upstream": upstream, "execution": {"source": "operational-store", "status": "known", "items": items, "wip": len(items)}, "projection": {"source": "decision-notifier", "status": "healthy" if all(value.delivered for value in delivery.values()) else "unknown"}}

    def explain(self, target: str) -> dict[str, object]:
        version, state = self._store.read_state(self._profile, f"factory:{target}")
        if not state:
            raise OperatorDenied(f"unknown work item: {target}")
        return {"target": target, "guard_outcomes": {"lifecycle": state.get("stage"), "outcome": state.get("outcome"), "decision": state.get("decision_choice")}, "evidence": {"execution_revision": version}}

    def run(self, **fields: object) -> object:
        self._admit(fields)
        if not self._readiness():
            raise OperatorDenied("readiness gate failed; autonomous work was not started")
        return self._coordinator.start()

    def resume(self, **fields: object) -> object:
        return self.run(**fields)

    def cancel(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.cancel(str(fields["target"]), str(fields["actor"]), str(fields["authority"]), str(fields["reason"]), str(fields["idempotency_key"]))

    def stop(self, **fields: object) -> object:
        self._admit(fields)
        return self._coordinator.stop_owned(str(fields["actor"]), str(fields["authority"]), str(fields["reason"]), str(fields["idempotency_key"]))

    def reconcile(self, **fields: object) -> object:
        self._admit(fields)
        return {"target": str(fields["target"]), "source": "execution-revision", "status": "reconciled"}

    def decisions_list(self) -> list[dict[str, object]]:
        return [asdict(value) for value in DecisionInbox(self._store, self._coordinator, self._profile).list_open()]

    def decisions_show(self, identity: str) -> dict[str, object]:
        value = DecisionInbox(self._store, self._coordinator, self._profile).show(identity)
        return asdict(value) if is_dataclass(value) else value

    def decisions_decide(self, identity: str, **fields: object) -> dict[str, object]:
        self._admit(fields)
        record = DecisionInbox(self._store, self._coordinator, self._profile).submit(DecisionSubmission(str(fields["actor"]), str(fields["authority"]), identity, int(fields["expected_version"]), int(fields["expected_version"]), str(fields["idempotency_key"]), str(fields["choice"])))
        return asdict(record)

    def _admit(self, fields: dict[str, object]) -> None:
        required = ("actor", "authority", "target", "reason", "idempotency_key")
        if any(not isinstance(fields.get(key), str) or not fields[key] for key in required):
            raise OperatorDenied("actor, authority, target, reason and idempotency key are required")
        expected = fields.get("expected_version")
        if not isinstance(expected, int) or expected < 0:
            raise OperatorDenied("expected version is required")
        _, state = self._store.read_state(self._profile, f"factory:{fields['target']}")
        if state and state.get("version") != expected:
            raise OperatorDenied("stale expected version")
