"""Event-driven offline factory coordinator for the PY-04 walking skeleton."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Iterable

from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore, verify_in_fresh_process
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.escalation import DecisionRecord, HumanDecisionRequired, SupersededDecision
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage, transition
from alienintent.execution_coordination.domain.release import ReleaseRequest, ReleaseSource, admit_release
from alienintent.execution_coordination.domain.verdict import EvidenceDefinition, Observation, evaluate_verdict
from alienintent.execution_coordination.ports.operational_store import OperationalStore, ReservationRejected
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.control_plane.ports.decision_notifier import DecisionNotifier, DeliveryHealth


class StopReason(StrEnum):
    EXHAUSTED = "eligible-backlog-exhausted"
    BLOCKED = "dependencies-or-authority-blocked"
    CAPACITY_UNAVAILABLE = "capacity-unavailable"


@dataclass(frozen=True)
class RunSummary:
    stop_reason: StopReason
    dispatched: tuple[str, ...]
    authority_blocked: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectedState:
    state: ExecutionState
    outcome: str | None

    def __getattr__(self, name: str):
        return getattr(self.state, name)


class FactoryCoordinator:
    def __init__(self, store: OperationalStore, work: WorkManagement, worker: WorkerProvider, artifacts: LocalArtifactStore, profile: str, *, automatic_release: bool = True, notifier: DecisionNotifier | None = None) -> None:
        self._store, self._work, self._worker, self._artifacts, self._profile = store, work, worker, artifacts, profile
        self._automatic_release = automatic_release
        self._released: set[str] = set()
        self._notifier = notifier
        self.delivery_health: dict[str, DeliveryHealth] = {}

    def start(self) -> RunSummary:
        items = self._work.import_ready_snapshot()
        if not self._recover(items):
            return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
        dispatched: list[str] = []
        while (item := self._next_item(items)) is not None:
            result = self._run(item)
            if result is StopReason.CAPACITY_UNAVAILABLE:
                return RunSummary(result, tuple(dispatched))
            if result is None:
                dispatched.append(item.identity)
        return RunSummary(
            self._stop_reason(items), tuple(dispatched),
            tuple(item.identity for item in items if self._outcome(item.identity) == "authority-block"),
            tuple(item.identity for item in items if self._outcome(item.identity) in {"failure", "timeout"}),
        )

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

    def cancel(self, identity: str, actor: str, reason: str, idempotency_key: str) -> dict[str, object]:
        """Apply an attributable operator cancellation through the coordinator boundary."""
        version, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(identity)
        prior = raw.get("cancellation")
        if isinstance(prior, dict) and prior.get("idempotency_key") == idempotency_key:
            return {"status": "cancelled", "target": identity, "idempotent": True}
        cancellation = {"actor": actor, "reason": reason, "idempotency_key": idempotency_key}
        self._worker.cancel(identity, reason)
        self._store.commit(self._profile, self._aggregate(identity), version, raw | {"outcome": "cancelled-by-operator", "cancellation": cancellation})
        return {"status": "cancelled", "target": identity, "idempotent": False}

    def stop_owned(self, reason: str, idempotency_key: str) -> dict[str, object]:
        """Quiesce durable, nonterminal work instead of reporting a false service stop."""
        stopped = []
        for identity, _, raw in self._store.list_states(self._profile, "factory:"):
            if raw.get("outcome") in {"cancelled-by-operator", "cancelled-by-decision"}:
                continue
            stopped.append(self.cancel(identity.removeprefix("factory:"), "operator", reason, f"{idempotency_key}:{identity}"))
        return {"stopped": stopped}

    def _next_item(self, items: Iterable[ReadyWorkItem]) -> ReadyWorkItem | None:
        eligible = [item for item in items if self._eligible(item)]
        return min(eligible, key=lambda item: (item.priority is None, item.priority if item.priority is not None else 0, item.fifo), default=None)

    def _eligible(self, item: ReadyWorkItem) -> bool:
        try:
            projected = self.state(item.identity)
            if projected.stage is LifecycleStage.DONE or projected.outcome in {"authority-block", "blocked-by-authority", "cancelled-by-decision", "failure", "timeout"}:
                return False
        except KeyError:
            pass
        return (self._is_automatic(item) or self._is_released(item.identity)) and all(self._is_done(dep) for dep in item.dependencies)

    def _run(self, item: ReadyWorkItem) -> StopReason | None:
        source = ReleaseSource.AUTOMATIC_POLICY if self._is_automatic(item) else ReleaseSource.EXPLICIT_HUMAN
        try:
            capabilities = {"python", "filesystem", "process-control"}
            if self._has_authorizing_decision(item.identity):
                capabilities.update(item.contract.required_capabilities)
            admit_release({}, ReleaseRequest(item.identity, item.contract, item.readiness_digest, frozenset(item.dependencies), frozenset(capabilities), {dimension: 1 for dimension in item.contract.budget_policy.required_dimensions}, "offline-profile", source))
        except ValueError:
            state = ExecutionState.for_contract(item.contract)
            self._record_result(item, state, "release", "authority-block")
            self._register_escalation(self._authority_request(item, state.version, "Release admission requires authority not present in this profile."))
            self._block_dependents(item, self._work.import_ready_snapshot())
            return StopReason.BLOCKED
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
            prepared = self._encode(current) | {key: raw[key] for key in ("decision_key", "decision_choice") if key in raw}
            self._store.commit_with_effect(self._profile, self._aggregate(item.identity), version, prepared, correlation, {"correlation": correlation, "work": item.identity})
            self._store.claim_effect(self._profile, correlation)
            outcome = self._worker.start(WorkerInvocation(item.identity, correlation), item.contract, frozenset(item.contract.required_capabilities), item.contract.budget_policy)
            try:
                self._store.confirm_effect(self._profile, correlation, f"outcome:{outcome.kind}")
            except ReservationRejected:
                return StopReason.BLOCKED if self._park_unknown_effect(item, reservation) else StopReason.CAPACITY_UNAVAILABLE
            completed = self._completed_for_outcome(item, current, outcome)
            unresolved = self._has_unresolved_effect(item.identity)
            if unresolved:
                self._record_result(item, current, correlation, "authority-block")
                self._register_escalation(self._authority_request(item, current.version, "The external effect outcome is unknown and requires reconciliation authority."))
                self._block_dependents(item, self._work.import_ready_snapshot())
                self._store.release(self._profile, "repository", item.repository, correlation, reservation.fence)
                return StopReason.BLOCKED
            read_back = self._record_result(item, completed, correlation, outcome.kind)
            if outcome.kind == "authority-block":
                self._register_escalation(outcome.escalation or self._authority_request(
                    item, current.version, "The worker raised an authority block that requires a durable decision."
                ))
                self._block_dependents(item, self._work.import_ready_snapshot())
                self._finalize_workspace(item.identity, correlation, retain=True)
            elif read_back:
                self._finalize_workspace(item.identity, correlation, retain=False)
            self._work.project_execution_state(item.identity, completed.stage, completed.version)
            return None
        finally:
            if read_back and not self._has_unresolved_effect(item.identity):
                self._store.release(self._profile, "repository", item.repository, correlation, reservation.fence)

    def _completed_for_outcome(self, item: ReadyWorkItem, current: ExecutionState, outcome: WorkerOutcome) -> ExecutionState:
        if outcome.kind == "rework":
            return current
        if outcome.kind != "success" or outcome.candidate is None:
            return current
        # The custody gate is control-plane enforcement: it always rechecks
        # candidate retrieval rather than trusting a producer-set assertion.
        verified = verify_in_fresh_process(outcome.candidate, self._artifacts.verifier_root)
        verified_state = transition(current, current.version, "verify", candidate=verified)
        reviewed = transition(verified_state, verified_state.version, "review")
        verdict = evaluate_verdict(EvidenceDefinition(frozenset(item.contract.required_evidence)), (Observation("artifact-verified", True, True),), worker_claimed_success=True)
        accepted = transition(reviewed, reviewed.version, "accept", verdict=verdict)
        return transition(accepted, accepted.version, "close", completed_closure_actions=frozenset(item.contract.required_closure_actions))

    def _record_result(self, item: ReadyWorkItem, state: ExecutionState, correlation: str, outcome: str) -> bool:
        version, prior = self._store.read_state(self._profile, self._aggregate(item.identity))
        persisted = self._encode(state) | {"correlation": correlation, "outcome": outcome}
        for key in ("decision_key", "decision_choice"):
            if key in prior:
                persisted[key] = prior[key]
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
                if not self._park_unknown_effect(item, reservation):
                    return False
                continue
            try:
                self._store.confirm_effect(self._profile, reservation.owner, f"outcome:{outcome.kind}")
            except ReservationRejected:
                # A crash may occur after the durable worker outcome was confirmed
                # but before the correlated domain result was recorded.  The held
                # reservation and worker read-back still make reconciliation safe.
                pass
            _, raw = self._store.read_state(self._profile, self._aggregate(identity))
            if raw.get("correlation") == reservation.owner and raw.get("outcome") == outcome.kind:
                if outcome.kind == "authority-block":
                    self._restore_authority_block(
                        item, replace(self._decode(raw), contract=item.contract), outcome, reservation.owner, items
                    )
                self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
                continue
            current = replace(self._decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
            if not self._record_result(item, self._completed_for_outcome(item, current, outcome), reservation.owner, outcome.kind):
                return False
            if outcome.kind == "authority-block":
                self._restore_authority_block(item, current, outcome, reservation.owner, items)
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
        return True

    def _restore_authority_block(self, item: ReadyWorkItem, state: ExecutionState, outcome: WorkerOutcome, correlation: str, items: Iterable[ReadyWorkItem]) -> None:
        self._register_escalation(outcome.escalation or self._authority_request(
            item, state.version, "The worker raised an authority block that requires a durable decision."
        ))
        self._block_dependents(item, items)
        self._finalize_workspace(item.identity, correlation, retain=True)

    def _park_unknown_effect(self, item: ReadyWorkItem, reservation) -> bool:
        """Turn an unreadable FD-05 effect into a scoped, durable authority block."""
        version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
        current = replace(self._decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
        blocked = self._encode(current) | {"correlation": reservation.owner, "outcome": "authority-block"}
        try:
            self._store.park_unknown_effect(self._profile, reservation.owner, version, blocked)
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
        except ReservationRejected:
            return False
        self._register_escalation(self._authority_request(item, current.version, "The external effect outcome is unknown and requires reconciliation authority."))
        self._block_dependents(item, self._work.import_ready_snapshot())
        self._finalize_workspace(item.identity, reservation.owner, retain=True)
        return True

    def _finalize_workspace(self, identity: str, correlation: str, *, retain: bool) -> None:
        finalize = getattr(self._worker, "finalize", None)
        if callable(finalize):
            finalize(WorkerInvocation(identity, correlation), retain)

    def _is_done(self, identity: str) -> bool:
        try:
            return self.state(identity).stage is LifecycleStage.DONE
        except KeyError:
            return False

    def _stop_reason(self, items: Iterable[ReadyWorkItem]) -> StopReason:
        pending = [
            item
            for item in items
            if not self._is_done(item.identity)
            and self._outcome(item.identity) not in {"cancelled-by-decision", "failure", "timeout"}
        ]
        if not pending:
            return StopReason.EXHAUSTED
        if any(not self._is_automatic(item) and not self._is_released(item.identity) for item in pending):
            return StopReason.BLOCKED
        if any(self._outcome(item.identity) == "authority-block" for item in pending):
            return StopReason.BLOCKED
        return StopReason.BLOCKED

    def _outcome(self, identity: str) -> str | None:
        try:
            return self.state(identity).outcome
        except KeyError:
            return None

    def _has_unresolved_effect(self, identity: str) -> bool:
        return any(
            effect.aggregate == self._aggregate(identity) or effect.payload.get("work") == identity
            for effect in self._store.unresolved_effects(self._profile)
        )

    def _is_released(self, identity: str) -> bool:
        if identity in self._released:
            return True
        _, raw = self._store.read_state(self._profile, self._release_aggregate(identity))
        return raw.get("identity") == identity and raw.get("source") == ReleaseSource.EXPLICIT_HUMAN

    def _is_automatic(self, item: ReadyWorkItem) -> bool:
        return self._automatic_release and item.automatic_release

    def _has_authorizing_decision(self, identity: str) -> bool:
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        return raw.get("decision_choice") == "authorize"

    def _authority_request(self, item: ReadyWorkItem, version: int, reason: str) -> HumanDecisionRequired:
        return HumanDecisionRequired(
            profile=self._profile, project=item.repository, work_item=item.identity, biu_version=version,
            decision="Authorize the blocked execution to continue through normal admission guards.", reason=reason,
            options=("authorize", "defer"), tradeoffs=("authorize permits the bounded work to resume", "defer retains the scoped authority block"),
            recommendation="defer", affected_requirements=tuple(item.contract.satisfied_requirement_ids) or ("authority-required",),
            affected_architecture=("FD-05",), cost_of_waiting="The affected work and transitive dependents remain blocked.",
            authorizations=("authorize permits one normal guarded re-admission", "defer authorizes continued blocking"),
        )

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

    def _register_escalation(self, escalation: HumanDecisionRequired) -> None:
        version, raw = self._store.read_state(self._profile, "decision-inbox")
        open_items = dict(raw.get("open", {}))
        open_items.setdefault(escalation.work_item, {
            "profile": escalation.profile, "project": escalation.project, "work_item": escalation.work_item,
            "biu_version": escalation.biu_version, "decision": escalation.decision, "reason": escalation.reason,
            "options": list(escalation.options), "tradeoffs": list(escalation.tradeoffs), "recommendation": escalation.recommendation,
            "affected_requirements": list(escalation.affected_requirements), "affected_architecture": list(escalation.affected_architecture),
            "cost_of_waiting": escalation.cost_of_waiting, "authorizations": list(escalation.authorizations),
        })
        self._store.commit(self._profile, "decision-inbox", version, {"open": open_items})
        if self._notifier is not None:
            self.delivery_health[escalation.work_item] = self._notifier.notify(escalation)

    def _block_dependents(self, root: ReadyWorkItem, items: Iterable[ReadyWorkItem]) -> None:
        pending = {root.identity}
        all_items = tuple(items)
        while pending:
            parent = pending.pop()
            for item in all_items:
                if parent not in item.dependencies:
                    continue
                pending.add(item.identity)
                version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
                if raw.get("outcome") in {"authority-block", "blocked-by-authority"}:
                    continue
                state = replace(self._decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
                self._store.commit(self._profile, self._aggregate(item.identity), version, self._encode(state) | {"outcome": "blocked-by-authority", "blocked_by": root.identity})

    def _cancel_blocked_dependents(self, root: str, items: Iterable[ReadyWorkItem]) -> None:
        descendants = {root}
        all_items = tuple(items)
        while True:
            expanded = descendants | {
                item.identity for item in all_items
                if any(parent in descendants for parent in item.dependencies)
            }
            if expanded == descendants:
                break
            descendants = expanded
        for item in all_items:
            if item.identity == root or item.identity not in descendants:
                continue
            version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
            if raw.get("outcome") != "blocked-by-authority":
                continue
            self._store.commit(
                self._profile, self._aggregate(item.identity), version,
                raw | {"outcome": "cancelled-by-decision", "cancelled_by": root},
            )

    def record_decision(self, record: DecisionRecord) -> None:
        version, raw = self._store.read_state(self._profile, self._aggregate(record.event.work_item))
        already_recorded = raw.get("decision_key") == record.event.idempotency_key
        if not already_recorded:
            self.validate_decision(record)
        state = self._decode(raw)
        items = self._work.import_ready_snapshot()
        if not already_recorded:
            outcome = "cancelled-by-decision" if record.submission.choice == "cancel" else "decision-recorded"
            decision_state = self._encode(state) | {"outcome": outcome, "decision_key": record.event.idempotency_key, "decision_choice": record.submission.choice}
            if record.submission.choice == "cancel":
                self._store.commit(self._profile, self._aggregate(record.event.work_item), version, decision_state)
            else:
                authorized = (
                    record.submission.choice == "authorize"
                    and isinstance(raw.get("correlation"), str)
                    and self._store.authorize_unknown_effect(self._profile, raw["correlation"], self._aggregate(record.event.work_item), version, decision_state)
                )
                if not authorized:
                    self._store.commit(self._profile, self._aggregate(record.event.work_item), version, decision_state)
        if record.submission.choice == "cancel":
            self._cancel_blocked_dependents(record.event.work_item, items)
            return
        descendants = {record.event.work_item}
        changed = True
        while changed:
            changed = False
            for item in items:
                if item.identity not in descendants and any(parent in descendants for parent in item.dependencies):
                    descendants.add(item.identity)
                    changed = True
        for item in items:
            if item.identity not in descendants or item.identity == record.event.work_item:
                continue
            dependent_version, dependent = self._store.read_state(self._profile, self._aggregate(item.identity))
            if dependent.get("outcome") == "blocked-by-authority":
                self._store.commit(self._profile, self._aggregate(item.identity), dependent_version, dependent | {"outcome": "decision-recorded"})

    def resume_after_decision(self) -> None:
        self.start()

    def validate_decision(self, record: DecisionRecord) -> None:
        _, raw = self._store.read_state(self._profile, self._aggregate(record.event.work_item))
        if not raw or raw.get("outcome") != "authority-block":
            raise SupersededDecision("decision target is not authority blocked")
        state = self._decode(raw)
        if state.version != record.submission.expected_version or record.submission.biu_version != state.version:
            raise SupersededDecision("decision target version is superseded")
