"""Event-driven offline factory coordinator for the PY-04 walking skeleton."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Iterable

from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore, verify_in_fresh_process
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage, transition
from alienintent.execution_coordination.domain.release import ReleaseRequest, ReleaseSource, admit_release
from alienintent.execution_coordination.domain.verdict import EvidenceDefinition, Observation, evaluate_verdict
from alienintent.execution_coordination.ports.operational_store import OperationalStore, ReservationRejected
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider


class StopReason(StrEnum):
    EXHAUSTED = "eligible-backlog-exhausted"
    BLOCKED = "dependencies-or-authority-blocked"
    CAPACITY_UNAVAILABLE = "capacity-unavailable"
    AWAITING_RELEASE = "awaiting-explicit-release"
    AUTHORITY_BLOCKED = "authority-blocked"


@dataclass(frozen=True)
class RunSummary:
    stop_reason: StopReason
    dispatched: tuple[str, ...]


@dataclass(frozen=True)
class ProjectedState:
    state: ExecutionState
    outcome: str | None

    def __getattr__(self, name: str):
        return getattr(self.state, name)


class FactoryCoordinator:
    def __init__(self, store: OperationalStore, work: WorkManagement, worker: WorkerProvider, artifacts: LocalArtifactStore, profile: str) -> None:
        self._store, self._work, self._worker, self._artifacts, self._profile = store, work, worker, artifacts, profile
        self._released: set[str] = set()

    def start(self) -> RunSummary:
        items = self._work.import_ready_snapshot()
        if not self._recover(items):
            return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
        dispatched: list[str] = []
        while (item := self._next_item(items)) is not None:
            result = self._run(item)
            if result is StopReason.CAPACITY_UNAVAILABLE:
                return RunSummary(result, tuple(dispatched))
            dispatched.append(item.identity)
        return RunSummary(self._stop_reason(items), tuple(dispatched))

    def release_and_start(self, identity: str) -> RunSummary:
        version, existing = self._store.read_state(self._profile, self._release_aggregate(identity))
        if not existing:
            self._store.commit(self._profile, self._release_aggregate(identity), version, {"identity": identity, "source": ReleaseSource.EXPLICIT_HUMAN})
        self._released.add(identity)
        return self.start()

    def state(self, identity: str) -> ProjectedState:
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(identity)
        return ProjectedState(self._decode(raw), raw.get("outcome") if isinstance(raw.get("outcome"), str) else None)

    def _next_item(self, items: Iterable[ReadyWorkItem]) -> ReadyWorkItem | None:
        eligible = [item for item in items if self._eligible(item)]
        return min(eligible, key=lambda item: (item.priority is None, item.priority if item.priority is not None else 0, item.fifo), default=None)

    def _eligible(self, item: ReadyWorkItem) -> bool:
        try:
            projected = self.state(item.identity)
            if projected.stage is LifecycleStage.DONE or projected.outcome in {"authority-block", "failure", "timeout"}:
                return False
        except KeyError:
            pass
        return (item.automatic_release or self._is_released(item.identity)) and all(self._is_done(dep) for dep in item.dependencies)

    def _run(self, item: ReadyWorkItem) -> StopReason | None:
        source = ReleaseSource.AUTOMATIC_POLICY if item.automatic_release else ReleaseSource.EXPLICIT_HUMAN
        try:
            admit_release({}, ReleaseRequest(item.identity, item.contract, item.readiness_digest, frozenset(item.dependencies), frozenset({"python", "filesystem", "process-control"}), {dimension: 1 for dimension in item.contract.budget_policy.required_dimensions}, "offline-profile", source))
        except ValueError:
            self._record_result(item, ExecutionState.for_contract(item.contract), "release", "authority-block")
            return StopReason.AUTHORITY_BLOCKED
        self._work.propose_release(item)
        version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
        current = replace(self._decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
        correlation = f"launch:{item.identity}:{version}"
        try:
            reservation = self._store.acquire(self._profile, "repository", item.repository, correlation)
        except ReservationRejected:
            return StopReason.CAPACITY_UNAVAILABLE
        read_back = False
        try:
            self._store.commit_with_effect(self._profile, self._aggregate(item.identity), version, self._encode(current), correlation, {"correlation": correlation, "work": item.identity})
            self._store.claim_effect(self._profile, correlation)
            outcome = self._worker.start(WorkerInvocation(item.identity, correlation), item.contract, frozenset(item.contract.required_capabilities), item.contract.budget_policy)
            self._store.confirm_effect(self._profile, correlation, f"outcome:{outcome.kind}")
            completed = self._completed_for_outcome(item, current, outcome)
            read_back = self._record_result(item, completed, correlation, outcome.kind)
            self._work.project_execution_state(item.identity, completed.stage)
            return None
        finally:
            if read_back and not self._store.unresolved_effects(self._profile):
                self._store.release(self._profile, "repository", item.repository, correlation, reservation.fence)

    def _completed_for_outcome(self, item: ReadyWorkItem, current: ExecutionState, outcome: WorkerOutcome) -> ExecutionState:
        if outcome.kind == "rework":
            return current
        if outcome.kind != "success" or outcome.candidate is None:
            return current
        verified = verify_in_fresh_process(outcome.candidate, self._artifacts.verifier_root)
        verified_state = transition(current, current.version, "verify", candidate=verified)
        reviewed = transition(verified_state, verified_state.version, "review")
        verdict = evaluate_verdict(EvidenceDefinition(frozenset(item.contract.required_evidence)), (Observation("artifact-verified", True, True),), worker_claimed_success=True)
        accepted = transition(reviewed, reviewed.version, "accept", verdict=verdict)
        return transition(accepted, accepted.version, "close", completed_closure_actions=frozenset(item.contract.required_closure_actions))

    def _record_result(self, item: ReadyWorkItem, state: ExecutionState, correlation: str, outcome: str) -> bool:
        version, _ = self._store.read_state(self._profile, self._aggregate(item.identity))
        persisted = self._encode(state) | {"correlation": correlation, "outcome": outcome}
        self._store.commit(self._profile, self._aggregate(item.identity), version, persisted)
        _, read_back = self._store.read_state(self._profile, self._aggregate(item.identity))
        return read_back.get("correlation") == correlation and read_back.get("outcome") == outcome

    def _recover(self, items: Iterable[ReadyWorkItem]) -> bool:
        by_identity = {item.identity: item for item in items}
        for reservation in self._store.recovery_reservations(self._profile):
            if reservation.scope != "repository" or not reservation.owner.startswith("launch:"):
                return False
            try:
                _, identity, _ = reservation.owner.rsplit(":", 2)
                item = by_identity[identity]
            except (ValueError, KeyError):
                return False
            outcome = self._worker.read_back(WorkerInvocation(identity, reservation.owner))
            if outcome is None:
                return False
            try:
                self._store.confirm_effect(self._profile, reservation.owner, f"outcome:{outcome.kind}")
            except ReservationRejected:
                return False
            _, raw = self._store.read_state(self._profile, self._aggregate(identity))
            current = replace(self._decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
            if not self._record_result(item, self._completed_for_outcome(item, current, outcome), reservation.owner, outcome.kind):
                return False
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
        return True

    def _is_done(self, identity: str) -> bool:
        try:
            return self.state(identity).stage is LifecycleStage.DONE
        except KeyError:
            return False

    def _stop_reason(self, items: Iterable[ReadyWorkItem]) -> StopReason:
        pending = [item for item in items if not self._is_done(item.identity)]
        if not pending:
            return StopReason.EXHAUSTED
        if any(not item.automatic_release and not self._is_released(item.identity) for item in pending):
            return StopReason.AWAITING_RELEASE
        if any(self._outcome(item.identity) == "authority-block" for item in pending):
            return StopReason.AUTHORITY_BLOCKED
        return StopReason.BLOCKED

    def _outcome(self, identity: str) -> str | None:
        try:
            return self.state(identity).outcome
        except KeyError:
            return None

    def _is_released(self, identity: str) -> bool:
        if identity in self._released:
            return True
        _, raw = self._store.read_state(self._profile, self._release_aggregate(identity))
        return raw.get("identity") == identity and raw.get("source") == ReleaseSource.EXPLICIT_HUMAN

    @staticmethod
    def _aggregate(identity: str) -> str: return f"factory:{identity}"
    @staticmethod
    def _release_aggregate(identity: str) -> str: return f"release:{identity}"

    @staticmethod
    def _encode(state: ExecutionState) -> dict[str, object]:
        candidate = state.candidate
        encoded = None if candidate is None else {"kind": candidate.kind, "identity": candidate.identity, "content_digest": candidate.content_digest, "locator": candidate.locator, "provenance": candidate.provenance, "independent_read_back_proven": candidate.independent_read_back_proven}
        return {"stage": state.stage, "version": state.version, "accepted": state.accepted, "closure": sorted(state.completed_closure_actions), "candidate": encoded}

    @staticmethod
    def _decode(raw: dict[str, object]) -> ExecutionState:
        record = raw.get("candidate")
        candidate = CandidateRef(CandidateKind(str(record["kind"])), str(record["identity"]), str(record["content_digest"]), str(record["locator"]), str(record["provenance"]), bool(record["independent_read_back_proven"])) if isinstance(record, dict) else None
        return ExecutionState(LifecycleStage(str(raw["stage"])), int(raw["version"]), candidate, bool(raw["accepted"]), frozenset(raw["closure"]), None)
