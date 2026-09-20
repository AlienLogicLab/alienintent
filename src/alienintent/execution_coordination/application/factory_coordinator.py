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
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerProvider


class StopReason(StrEnum):
    EXHAUSTED = "eligible-backlog-exhausted"
    BLOCKED = "dependencies-or-authority-blocked"
    CAPACITY_UNAVAILABLE = "capacity-unavailable"
    AWAITING_RELEASE = "awaiting-explicit-release"
    AUTHORITY_BLOCKED = "authority-blocked"
    FAILURE = "worker-failure"


@dataclass(frozen=True)
class RunSummary:
    stop_reason: StopReason
    dispatched: tuple[str, ...]


class FactoryCoordinator:
    """Coordinates a single offline repository mutation stream without polling."""

    def __init__(self, store: OperationalStore, work: WorkManagement, worker: WorkerProvider, artifacts: LocalArtifactStore, profile: str) -> None:
        self._store, self._work, self._worker, self._artifacts, self._profile = store, work, worker, artifacts, profile
        self._released: set[str] = set()

    def start(self, *, limit: int | None = None) -> RunSummary:
        items = self._work.import_ready_snapshot()  # the only backlog read in a run
        if not self._recover(items):
            return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
        dispatched: list[str] = []
        while limit is None or len(dispatched) < limit:
            next_item = self._next_item(items)
            if next_item is None:
                return RunSummary(self._stop_reason(items), tuple(dispatched))
            result = self._run(next_item)
            if result is not None:
                return RunSummary(result, tuple(dispatched))
            dispatched.append(next_item.identity)
        return RunSummary(StopReason.CAPACITY_UNAVAILABLE, tuple(dispatched))

    def release_and_start(self, identity: str) -> RunSummary:
        version, existing = self._store.read_state(self._profile, self._release_aggregate(identity))
        if not existing:
            self._store.commit(self._profile, self._release_aggregate(identity), version, {"identity": identity, "source": ReleaseSource.EXPLICIT_HUMAN})
        self._released.add(identity)
        return self.start()

    def state(self, identity: str) -> ExecutionState:
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(identity)
        return self._decode(raw)

    def _next_item(self, items: Iterable[ReadyWorkItem]) -> ReadyWorkItem | None:
        candidates = []
        for item in items:
            try:
                state = self.state(item.identity)
            except KeyError:
                state = ExecutionState.for_contract(item.contract)
            if state.stage is LifecycleStage.DONE:
                continue
            dependencies_done = all(self._is_done(dependency) for dependency in item.dependencies)
            if dependencies_done:
                candidates.append(item)
        eligible = [item for item in candidates if item.automatic_release or self._is_released(item.identity)]
        return min(eligible, key=lambda item: (item.priority is None, item.priority if item.priority is not None else 0, item.fifo), default=None)

    def _run(self, item: ReadyWorkItem) -> StopReason | None:
        try:
            source = ReleaseSource.AUTOMATIC_POLICY if item.automatic_release else ReleaseSource.EXPLICIT_HUMAN
            admit_release({}, ReleaseRequest(item.identity, item.contract, item.readiness_digest, frozenset(item.dependencies), frozenset({"python", "filesystem", "process-control"}), {dimension: 1 for dimension in item.contract.budget_policy.required_dimensions}, "offline-profile", source))
        except ValueError:
            return StopReason.AUTHORITY_BLOCKED
        self._work.propose_release(item)
        owner = f"{item.identity}:launch"
        try:
            reservation = self._store.acquire(self._profile, "repository", item.repository, owner)
        except ReservationRejected:
            return StopReason.CAPACITY_UNAVAILABLE
        result_read_back = False
        try:
            version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
            current = self._decode(raw) if raw else ExecutionState.for_contract(item.contract)
            if current.contract is None:
                current = replace(current, contract=item.contract)
            effect_id = f"launch:{item.identity}:{version}"
            self._store.commit_with_effect(self._profile, self._aggregate(item.identity), version, self._encode(current), effect_id, {"correlation": effect_id, "work": item.identity})
            effect = self._store.claim_effect(self._profile, effect_id)
            outcome = self._worker.start(WorkerInvocation(item.identity, effect.identity), item.contract, frozenset(item.contract.required_capabilities), item.contract.budget_policy)
            self._store.confirm_effect(self._profile, effect_id, f"outcome:{outcome.kind}")
            if outcome.kind == "authority-block":
                result_read_back = self._record_result(item, current, effect_id, outcome.kind)
                self._work.project_execution_state(item.identity, "authority-blocked")
                return StopReason.AUTHORITY_BLOCKED
            if outcome.kind == "rework":
                result_read_back = self._record_result(item, current, effect_id, outcome.kind)
                self._work.project_execution_state(item.identity, LifecycleStage.IMPLEMENT)
                return None
            if outcome.kind != "success" or outcome.candidate is None:
                result_read_back = self._record_result(item, current, effect_id, outcome.kind)
                self._work.project_execution_state(item.identity, "failure")
                return StopReason.FAILURE
            current = self._complete_success(item, current, outcome.candidate)
            result_read_back = self._record_result(item, current, effect_id, outcome.kind)
            self._work.project_execution_state(item.identity, current.stage)
            return None
        finally:
            # An unknown launch, or a result not durably read back, retains capacity for recovery.
            if result_read_back and not self._store.unresolved_effects(self._profile):
                self._store.release(self._profile, "repository", item.repository, owner, reservation.fence)

    def _record_result(self, item: ReadyWorkItem, state: ExecutionState, correlation: str, outcome: str) -> bool:
        version, _ = self._store.read_state(self._profile, self._aggregate(item.identity))
        persisted = self._encode(state)
        persisted["correlation"] = correlation
        persisted["outcome"] = outcome
        self._store.commit(self._profile, self._aggregate(item.identity), version, persisted)
        _, read_back = self._store.read_state(self._profile, self._aggregate(item.identity))
        return read_back.get("correlation") == correlation and read_back.get("outcome") == outcome

    def _recover(self, items: Iterable[ReadyWorkItem]) -> bool:
        by_identity = {item.identity: item for item in items}
        for reservation in self._store.recovery_reservations(self._profile):
            if reservation.scope != "repository" or not reservation.owner.startswith("launch:"):
                return False
            _, identity, _ = reservation.owner.rsplit(":", 2)
            item = by_identity.get(identity)
            if item is None:
                return False
            invocation = WorkerInvocation(identity, reservation.owner)
            outcome = self._worker.read_back(invocation)
            if outcome is None:
                return False
            try:
                self._store.confirm_effect(self._profile, reservation.owner, f"recovered:{outcome.kind}")
            except ReservationRejected:
                return False
            version, raw = self._store.read_state(self._profile, self._aggregate(identity))
            current = self._decode(raw) if raw else ExecutionState.for_contract(item.contract)
            current = replace(current, contract=item.contract)
            if outcome.kind != "success" or outcome.candidate is None:
                return False
            completed = self._complete_success(item, current, outcome.candidate)
            if not self._record_result(item, completed, reservation.owner, outcome.kind):
                return False
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
            self._work.project_execution_state(identity, completed.stage)
        return True

    @staticmethod
    def _complete_success(item: ReadyWorkItem, state: ExecutionState, candidate: CandidateRef) -> ExecutionState:
        verified = verify_in_fresh_process(candidate)
        verified_state = transition(state, state.version, "verify", candidate=verified)
        reviewed = transition(verified_state, verified_state.version, "review")
        verdict = evaluate_verdict(EvidenceDefinition(frozenset(item.contract.required_evidence)), (Observation("artifact-verified", True, True),), worker_claimed_success=True)
        accepted = transition(reviewed, reviewed.version, "accept", verdict=verdict)
        return transition(accepted, accepted.version, "close", completed_closure_actions=frozenset(item.contract.required_closure_actions))

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
        return StopReason.BLOCKED

    @staticmethod
    def _aggregate(identity: str) -> str:
        return f"factory:{identity}"

    @staticmethod
    def _release_aggregate(identity: str) -> str:
        return f"release:{identity}"

    def _is_released(self, identity: str) -> bool:
        if identity in self._released:
            return True
        _, release = self._store.read_state(self._profile, self._release_aggregate(identity))
        return release.get("identity") == identity and release.get("source") == ReleaseSource.EXPLICIT_HUMAN

    @staticmethod
    def _encode(state: ExecutionState) -> dict[str, object]:
        candidate = None if state.candidate is None else {"kind": state.candidate.kind, "identity": state.candidate.identity, "digest": state.candidate.content_digest, "locator": state.candidate.locator, "provenance": state.candidate.provenance, "read_back": state.candidate.independent_read_back_proven}
        return {"stage": state.stage, "version": state.version, "accepted": state.accepted, "closure": sorted(state.completed_closure_actions), "candidate": candidate}

    @staticmethod
    def _decode(raw: dict[str, object]) -> ExecutionState:
        candidate_raw = raw.get("candidate")
        candidate = None
        if isinstance(candidate_raw, dict):
            candidate = CandidateRef(CandidateKind(str(candidate_raw["kind"])), str(candidate_raw["identity"]), str(candidate_raw["digest"]), str(candidate_raw["locator"]), str(candidate_raw["provenance"]), bool(candidate_raw["read_back"]))
        return ExecutionState(LifecycleStage(str(raw["stage"])), int(raw["version"]), candidate, bool(raw["accepted"]), frozenset(raw["closure"]), None)
