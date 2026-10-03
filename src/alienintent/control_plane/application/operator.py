"""Named operator application services; CLI adapters never write the store."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
import logging
from pathlib import Path
from typing import Any, Protocol

from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.escalation import DecisionSubmission
from alienintent.execution_coordination.ports.worker_provider import VERIFIER


logger = logging.getLogger(__name__)


class OperatorDenied(ValueError):
    pass


class WorkMigration(Protocol):
    """The project's work identity service as `work migrate` uses it (bound by the profile's composition)."""

    def migrate(self, snapshot: Mapping[str, object], profiles: Sequence[str]) -> object: ...


def migrate_work(identities: WorkMigration, snapshot: object, profiles: Sequence[str]) -> dict[str, object]:
    """`work migrate`: hand the identity snapshot and the named profiles to the project's work identity service,
    which owns the one transaction; the operator surface only validates the shape and reports."""
    if isinstance(snapshot, Mapping) and isinstance(snapshot.get("identity_snapshot"), Mapping):
        snapshot = snapshot["identity_snapshot"]  # An authority-limits document carries the snapshot inside.
    if not isinstance(snapshot, Mapping) or not profiles or not all(isinstance(p, str) and p for p in profiles):
        raise OperatorDenied("work migrate needs an identity snapshot object and at least one profile")
    report = identities.migrate(snapshot, list(profiles))
    return asdict(report) if is_dataclass(report) else dict(report)


class WorkRecords(Protocol):
    """The project's work-record operations as `work register`, `work import` and `work show` use them (bound by
    the profile's composition)."""

    def register(self, packet: bytes, repo: str, path: str, commit: str, label: str, kind: str,
                 parent_id: str | None) -> Any: ...

    def import_completed(self, packet: bytes, repo: str, path: str, commit: str, label: str, issue: str,
                         evidence: Mapping[str, object]) -> Any: ...

    def show(self, id_or_label: str) -> Any: ...


def register_work(records: WorkRecords, packet: bytes, repo: str, path: str, commit: str, label: str, kind: str,
                  parent_id: str | None) -> dict[str, object]:
    """`work register`: the packet file's bytes go to the project's work-record service, which owns the one
    transaction and the byte comparison with Git; the operator surface only reports the row."""
    return asdict(records.register(packet, repo, path, commit, label, kind, parent_id))


def import_work(records: WorkRecords, packet: bytes, repo: str, path: str, commit: str, label: str, issue: str,
                evidence: Mapping[str, object]) -> dict[str, object]:
    """`work import`: earlier completed work at DONE with exactly the evidence references given."""
    return asdict(records.import_completed(packet, repo, path, commit, label, issue, evidence))


def show_work(records: WorkRecords, id_or_label: str) -> dict[str, object]:
    """`work show`: the row, its parent, its children and the packet text at the pinned commit. A name no row holds
    is the read answer UNKNOWN_IDENTITY, not a failure."""
    record = records.show(id_or_label)
    if record is None:
        return {"answer": "UNKNOWN_IDENTITY"}
    value = asdict(record)
    value["packet"] = None if record.packet is None else record.packet.decode("utf-8")
    return value


class WorkAssessment(Protocol):
    """The project's packet assessment as `work assess` uses it (bound by the profile's composition)."""

    def assess(self, id_or_label: str, revision: tuple[bytes, str] | None, recover: str | None) -> Any: ...


def assess_work(assessment: WorkAssessment, id_or_label: str, revision: tuple[bytes, str] | None,
                recover: str | None) -> dict[str, object]:
    """`work assess`: the item id, attempt id, disposition and saved reference, or a refusal or hold returned as the
    read answer naming its code, the way `work show` answers UNKNOWN_IDENTITY."""
    result = assessment.assess(id_or_label, revision, recover)
    value = asdict(result)
    if "reason_code" in value:
        value["answer"] = value.pop("reason_code")
    return value


class WorkAuthorizations(Protocol):
    """The project's work authorization as `work authorize` uses it (bound by the profile's composition)."""

    def authorize(self, id_or_label: str, commit: str, attempt: str, baseline: str, quote: str) -> Any: ...


def authorize_work(authorization: WorkAuthorizations, id_or_label: str, commit: str, attempt: str, baseline: str,
                   quote: str) -> dict[str, object]:
    """`work authorize`: the item, its evidence reference and the recorded release authorization, or a refusal
    returned as the read answer naming its code. It records the Founder's approval; it does not grant it."""
    return asdict(authorization.authorize(id_or_label, commit, attempt, baseline, quote))


class WorkCompletions(Protocol):
    """The project's completed-work recording as `work record-completed` uses it (bound by the profile's
    composition)."""

    def record(self, id_or_label: str, candidate: str, landing: str, record_path: str, verifications: Sequence[Any],
               approval: Any, quote: str) -> Any: ...


def record_completed_work(completion: WorkCompletions, id_or_label: str, candidate: str, landing: str,
                          record_path: str, verifications: Sequence[Any], approval: Any,
                          quote: str) -> dict[str, object]:
    """`work record-completed`: the item and its `work-completion` evidence reference once the row is DONE, or a
    refusal returned as the read answer naming its code. It records completed work; it does not judge it."""
    return asdict(completion.record(id_or_label, candidate, landing, record_path, verifications, approval, quote))


class WorkLinks(Protocol):
    """The project's link service as `work link` and `work display` use it (bound by the profile's composition)."""

    def link(self, id_or_label: str, issue: int | None) -> Any: ...

    def display(self, id_or_label: str) -> Any: ...


def link_work(links: WorkLinks, id_or_label: str, issue: int | None) -> dict[str, object]:
    """`work link`: the item's Issue, card and the duplicates closed, or a refusal returned as the read answer
    naming its code, the way `work show` answers UNKNOWN_IDENTITY."""
    return asdict(links.link(id_or_label, issue))


def display_work(links: WorkLinks, id_or_label: str) -> dict[str, object]:
    """`work display`: `unchanged` or `updated` once read back, or a refusal returned as the read answer."""
    return asdict(links.display(id_or_label))


# The stated answer of the read-only worker profile to every command other than `work context`.
NOT_AVAILABLE_IN_WORKER_PROFILE = "not-available-in-worker-profile"


class WorkContexts(Protocol):
    """The project's context assembly as `work context` uses it (bound by the profile's composition)."""

    def assemble(self, identity: str, role: str, correlation: str, contract_digest: str | None,
                 candidate: Any = None, clone: Path | None = None) -> Any: ...


def context_work(context: WorkContexts, id_or_label: str, role: str, correlation: str, candidate: str | None,
                 workspace: Path) -> dict[str, object]:
    """`work context`: the role's context package for the work item and attempt, or the hold that prevents launch,
    as the read answer. The command holds no invocation contract digest; a VERIFIER runs it in its candidate clone
    (`workspace`), where the diff is taken."""
    return context.assemble(id_or_label, role, correlation, None, candidate,
                            workspace if role == VERIFIER else None).document()


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
        _, state = self._store.read_state(self._profile, f"factory:{identity}")
        kernel_version = state.get("version")
        if not isinstance(kernel_version, int) or kernel_version < 0:
            raise OperatorDenied("decision target has no kernel version")
        record = DecisionInbox(self._store, self._coordinator, self._profile).submit(DecisionSubmission(str(fields["actor"]), str(fields["authority"]), identity, biu_version, kernel_version, str(fields["idempotency_key"]), str(fields["choice"])))
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
