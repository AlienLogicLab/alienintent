"""Event-driven offline factory coordinator for the PY-04 walking skeleton."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Callable, Iterable, Mapping

from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore, verify_in_fresh_process
from alienintent.execution_coordination.application.release_admission import ReleasePreconditionGate
from alienintent.execution_coordination.domain.closure import (
    ACTIONS, CANDIDATE_PUBLISHED, CLOSURE_HOLD, CLOSURE_REWORK, READY_TO_LAND, is_fixed, parse_finding, parse_receipt)
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.escalation import DecisionRecord, HumanDecisionRequired, SupersededDecision
from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage, transition
from alienintent.execution_coordination.domain.release import ReleasePreconditionRefused, ReleaseRequest, ReleaseSource, admit_release
from alienintent.execution_coordination.domain.satisfiability import ARTIFACT_VERIFIED, BASE_CAPABILITIES, VERIFIER_EVIDENCE
from alienintent.execution_coordination.domain.verdict import EvidenceDefinition, Observation, VerdictKind, evaluate_verdict
from alienintent.execution_coordination.ports.operational_store import OperationalStore, ReservationRejected, VersionConflict
from alienintent.execution_coordination.ports.release_admission import ExecutionAllocation
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
from alienintent.execution_coordination.ports.worker_provider import CLOSURE, MISSING_TERMINAL_RESULT, PRODUCER, VERIFIER, WorkerInvocation, WorkerOutcome, WorkerProvider
from alienintent.control_plane.ports.decision_notifier import DecisionNotifier, DeliveryHealth

# K2: each nonterminal stage is advanced by exactly one canonical role.
ROLE_BY_STAGE = {LifecycleStage.IMPLEMENT: PRODUCER, LifecycleStage.VERIFY: VERIFIER, LifecycleStage.ACCEPT: CLOSURE}
# Execution-record fields that survive every later commit of the same aggregate.
CARRIED = ("decision_key", "decision_choice", "producer_correlation", "rejections", "findings", "verdict")
# One WIP slot per admitted work item, held until its recorded state is DONE or a final outcome: an outcome the
# coordinator records as ending the work item with nothing able to resume it (authority holds are resumable).
WIP_SCOPE = "wip"
FINAL_OUTCOMES = frozenset({"cancelled-by-operator", "cancelled-by-decision", "failure", "timeout"})
# `launch` answers that launch nothing.
CLOSURE_NOT_AUTOMATED, NOT_ELIGIBLE = "closure-not-automated", "not-eligible"
# The one registry-wide `work launch` reservation (an ordinary store reservation). Only `work launch` takes and releases
# it; recovery runs inside it and never touches it, so another launch's reservation recovery acts on is a dead one.
LAUNCH_SCOPE, LAUNCH_KEY = "launch", "registry"
# The park reason of a launch that was saved (its effect `pending`) but never claimed, so never started.
NEVER_STARTED = "launch saved but never started"


@dataclass(frozen=True)
class _Advance:
    state: ExecutionState
    outcome: str
    fields: dict[str, object]
    hold: str | None = None


class StopReason(StrEnum):
    EXHAUSTED = "eligible-backlog-exhausted"
    BLOCKED = "dependencies-or-authority-blocked"
    CAPACITY_UNAVAILABLE = "capacity-unavailable"
    WIP_LIMIT_UNAVAILABLE = "wip-limit-unavailable"


class _WipSkip(StrEnum):
    """A work item not admitted to IMPLEMENT this run; the run continues with other work items."""
    REFUSED = "wip-refused"
    UNAVAILABLE = "wip-limit-unavailable"


class TerminalWork(ValueError):
    """A normal domain refusal to alter terminal or accepted work."""


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
    record: dict[str, object] | None = None

    def __getattr__(self, name: str):
        return getattr(self.state, name)


class FactoryCoordinator:
    def __init__(self, store: OperationalStore, work: WorkManagement, worker: WorkerProvider, artifacts: LocalArtifactStore, profile: str, *, automatic_release: bool = True, notifier: DecisionNotifier | None = None,
                 release_gate: ReleasePreconditionGate | None = None, allocation: ExecutionAllocation | None = None,
                 wip_limit: Callable[[], int | None] | None = None,
                 recorded_completion: Callable[[str], bool] | None = None,
                 landing_enabled: Callable[[], bool] = lambda: False,
                 started_item: Callable[[str, str], ReadyWorkItem | None] | None = None,
                 completed: Callable[[str], None] | None = None,
                 stage_shown: Callable[[str], None] | None = None) -> None:
        self._store, self._work, self._worker, self._artifacts, self._profile = store, work, worker, artifacts, profile
        # Whether a dependency with no coordinator record is recorded complete (`work record-completed`); None (the
        # default) counts only a coordinator record at DONE.
        self._recorded_completion = recorded_completion
        self._automatic_release = automatic_release
        # SWF-21 release preconditions and the attributable per-BIU budget
        # (WO-220611). A profile that supplies neither keeps its prior
        # admission behaviour; see _available_budget.
        self._release_gate, self._allocation = release_gate, allocation
        self._released: set[str] = set()
        # The configured WIP limit, read on every admission; None (the default) means no WIP admission at all.
        self._wip_limit = wip_limit
        self._notifier = notifier
        self.delivery_health: dict[str, DeliveryHealth] = {}
        # Automated closure: whether landing is enabled, the resolver of a started item from its registry record
        # (when the READY view no longer lists it) and the DONE projection hook, which never raises into this class.
        self._landing_enabled, self._started_item, self._completed = landing_enabled, started_item, completed
        self._stage_shown = stage_shown
        self.projection_diagnostics: dict[str, str] = {}

    def start(self) -> RunSummary:
        items = self._work.import_ready_snapshot()
        if not self._recover(items):
            return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
        dispatched: list[str] = []
        skipped: dict[str, _WipSkip] = {}
        closed_once: set[str] = set()  # CLOSURE runs at most once per item in one call
        while (item := self._next_item([ready for ready in items if ready.identity not in skipped
                                        and ready.identity not in closed_once])) is not None:
            producing = self._role(item.identity) == PRODUCER
            if self._role(item.identity) == CLOSURE:
                closed_once.add(item.identity)
            result = self._run(item)
            if isinstance(result, _WipSkip):
                skipped[item.identity] = result
                continue
            if result is StopReason.CAPACITY_UNAVAILABLE:
                return RunSummary(result, tuple(dispatched))
            if result is None and producing:
                dispatched.append(item.identity)
        stop_reason = self._stop_reason(items)
        if skipped:
            stop_reason = StopReason.WIP_LIMIT_UNAVAILABLE if _WipSkip.UNAVAILABLE in skipped.values() else StopReason.CAPACITY_UNAVAILABLE
        return RunSummary(
            stop_reason, tuple(dispatched),
            tuple(item.identity for item in items if self._outcome(item.identity) == "authority-block"),
            tuple(item.identity for item in items if self._outcome(item.identity) in {"failure", "timeout"}),
        )

    def release_and_start(self, identity: str) -> RunSummary:
        version, existing = self._store.read_state(self._profile, self._release_aggregate(identity))
        if not existing:
            self._store.commit(self._profile, self._release_aggregate(identity), version, {"identity": identity, "source": ReleaseSource.EXPLICIT_HUMAN})
        self._released.add(identity)
        return self.start()

    def launch(self, identity: str) -> RunSummary | str:
        """One role step for exactly the named work item: the PRODUCER at IMPLEMENT, the VERIFIER at VERIFY or
        CLOSURE at ACCEPT.

        At ACCEPT, writing nothing before the last step: the item is resolved from the READY snapshot, or else
        `started_item`; a contract whose closure actions are not exactly the five fixed names answers
        CLOSURE_NOT_AUTOMATED; an item at `ready-to-land` while landing is not enabled answers READY_TO_LAND.
        Otherwise it writes the explicit human release as `release_and_start` does, runs the existing recovery once
        (which may record already-durable outcomes of other launches and starts no worker), projects every recorded
        DONE through `completed`, retries card stages, and, only if the item is in the READY snapshot or resolved by
        `started_item` and `_eligible` admits it, runs `_run` once for it. It never calls `start()`, so no other
        work item runs and the next role waits for the next `launch`.
        """
        accepted: ReadyWorkItem | None = None
        try:
            projected = self.state(identity)
        except KeyError:
            projected = None
        if projected is not None and projected.stage is LifecycleStage.ACCEPT:
            accepted = self._resolve(identity, self._work.import_ready_snapshot(), projected.record or {})
            if accepted is None or not is_fixed(accepted.contract.required_closure_actions):
                return CLOSURE_NOT_AUTOMATED
            if projected.outcome == READY_TO_LAND and not self._landing_enabled():
                return READY_TO_LAND
        version, existing = self._store.read_state(self._profile, self._release_aggregate(identity))
        if not existing:
            self._store.commit(self._profile, self._release_aggregate(identity), version, {"identity": identity, "source": ReleaseSource.EXPLICIT_HUMAN})
        self._released.add(identity)
        items = self._work.import_ready_snapshot()
        if not self._recover(items):
            return RunSummary(StopReason.CAPACITY_UNAVAILABLE, ())
        self._project_done()
        self._show_stages(identity)
        item = next((ready for ready in items if ready.identity == identity), None)
        if item is None:
            try:
                item = self._resolve(identity, items, self.state(identity).record or {})
            except KeyError:
                pass
        if item is None or not self._eligible(item):
            return NOT_ELIGIBLE
        producing = self._role(identity) == PRODUCER
        result = self._run(item)
        if isinstance(result, _WipSkip):
            return result.value
        outcome = self._outcome(identity)
        return RunSummary(result or self._stop_reason((item,)), (identity,) if result is None and producing else (),
                          (identity,) if outcome == "authority-block" else (),
                          (identity,) if outcome in {"failure", "timeout"} else ())

    def state(self, identity: str) -> ProjectedState:
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(identity)
        return ProjectedState(self.decode(raw), raw.get("outcome") if isinstance(raw.get("outcome"), str) else None, dict(raw))

    def _role(self, identity: str) -> str | None:
        try:
            return ROLE_BY_STAGE.get(self.state(identity).stage)
        except KeyError:
            return PRODUCER

    def guard_account(self, identity: str) -> dict[str, object]:
        """Expose the same eligibility decision the scheduler applies, read-only."""
        version, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(f"unknown work item: {identity}")
        items = self._work.import_ready_snapshot()
        item = self._resolve(identity, items, raw)
        outcome = raw.get("outcome")
        terminal = raw.get("stage") == LifecycleStage.DONE.value or outcome in {"cancelled-by-operator", "cancelled-by-decision", "failure", "timeout"}
        eligible = bool(item is not None and self._eligible(item))
        if terminal:
            reason = "terminal"
        elif outcome in {"authority-block", "blocked-by-authority"}:
            reason = "authority-block"
        elif item is None:
            reason = "not-in-upstream-ready-snapshot"
        elif not all(self._dependency_done(dependency) for dependency in item.dependencies):
            reason = "dependencies-incomplete"
        elif not eligible:
            reason = "release-not-admitted"
        else:
            reason = "eligible"
        return {"target": identity, "eligible": eligible, "reason": reason, "lifecycle": raw.get("stage"), "outcome": outcome, "evidence": {"execution_revision": version}}

    def reconcile(self, identity: str) -> dict[str, object]:
        """Recover durable effects without importing upstream terminal truth."""
        items = self._work.import_ready_snapshot()
        if not self._recover(items):
            raise ReservationRejected("recovery could not establish durable execution truth")
        version, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(f"unknown work item: {identity}")
        return {"target": identity, "source": "execution-revision", "status": "reconciled", "execution_revision": version}

    def cancel(self, identity: str, actor: str, authority: str, expected_version: int, reason: str, idempotency_key: str) -> dict[str, object]:
        """Apply an attributable operator cancellation through the coordinator boundary."""
        version, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            raise KeyError(identity)
        prior = raw.get("cancellation")
        if isinstance(prior, dict) and prior.get("idempotency_key") == idempotency_key:
            return {"status": "cancelled", "target": identity, "idempotent": True}
        if isinstance(prior, dict) and raw.get("outcome") == "cancelled-by-operator":
            return {"status": "cancelled", "target": identity, "idempotent": True}
        if raw.get("stage") == LifecycleStage.DONE.value or raw.get("accepted"):
            raise TerminalWork("terminal or accepted work cannot be cancelled")
        if version != expected_version:
            raise VersionConflict("stale expected version")
        cancellation = {"actor": actor, "authority": authority, "reason": reason, "idempotency_key": idempotency_key}
        self._worker.cancel(identity, reason)
        self._store.commit(self._profile, self._aggregate(identity), version, raw | {"outcome": "cancelled-by-operator", "cancellation": cancellation})
        self._release_ended_wip(identity)
        return {"status": "cancelled", "target": identity, "idempotent": False}

    def stop_owned(self, actor: str, authority: str, expected_version: int, reason: str, idempotency_key: str) -> dict[str, object]:
        """Quiesce durable, nonterminal work instead of reporting a false service stop."""
        candidates: list[tuple[str, int]] = []
        for identity, version, raw in self._store.list_states(self._profile, "factory:"):
            if raw.get("stage") == LifecycleStage.DONE.value or raw.get("accepted") or raw.get("outcome") in {"cancelled-by-operator", "cancelled-by-decision"}:
                continue
            candidates.append((identity, version))
        if any(version > expected_version for _, version in candidates):
            raise VersionConflict("stale expected version")
        # A profile may legitimately contain independent in-flight aggregates
        # at different revisions.  Apply each cancellation against the exact
        # snapshot revision it was enumerated with; cancel() remains the guard
        # that rejects a concurrent change rather than making stop impossible.
        stopped = [self.cancel(identity.removeprefix("factory:"), actor, authority, version, reason, f"{idempotency_key}:{identity}") for identity, version in candidates]
        return {"stopped": stopped}

    def _requirement_ids(self, item: ReadyWorkItem) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.contract.satisfied_requirement_ids))

    def _single_requirement(self, item: ReadyWorkItem) -> str | None:
        requirements = self._requirement_ids(item)
        return requirements[0] if len(requirements) == 1 else None

    def _focus_aggregate(self) -> str:
        return "scheduler:requirement-focus"

    def _requirement_focus(self) -> tuple[str, int | None] | None:
        _, raw = self._store.read_state(self._profile, self._focus_aggregate())
        requirement = raw.get("requirement") if raw else None
        priority = raw.get("priority") if raw else None
        if not isinstance(requirement, str) or not requirement:
            return None
        if priority is not None and (not isinstance(priority, int) or isinstance(priority, bool) or priority < 0):
            return None
        return requirement, priority

    def _set_requirement_focus(self, requirement: str, priority: int | None) -> None:
        version, raw = self._store.read_state(self._profile, self._focus_aggregate())
        if raw.get("requirement") == requirement and raw.get("priority") == priority:
            return
        self._store.commit(self._profile, self._focus_aggregate(), version, {
            "requirement": requirement,
            "priority": priority,
        })

    @staticmethod
    def _priority_key(item: ReadyWorkItem) -> tuple[bool, int, int]:
        return (item.priority is None, item.priority if item.priority is not None else 0, item.fifo)

    def _next_item(self, items: Iterable[ReadyWorkItem]) -> ReadyWorkItem | None:
        eligible = [item for item in items if self._eligible(item)]
        if not eligible:
            return None

        best = min(eligible, key=self._priority_key)
        focus = self._requirement_focus()
        if focus is not None:
            requirement, focus_priority = focus
            # A genuinely higher-priority requirement preempts the current focus.
            if best.priority is not None and (focus_priority is None or best.priority < focus_priority):
                parent = self._single_requirement(best)
                if parent is not None:
                    self._set_requirement_focus(parent, best.priority)
                return best

            focused = [item for item in eligible if requirement in self._requirement_ids(item)]
            if focused:
                return min(focused, key=self._priority_key)

            # No dependency-eligible BIU exists yet for the focused requirement.
            # Run the next eligible work without forgetting the requirement focus.
            return best

        parent = self._single_requirement(best)
        if parent is not None:
            self._set_requirement_focus(parent, best.priority)
        return best

    def _eligible(self, item: ReadyWorkItem) -> bool:
        try:
            projected = self.state(item.identity)
            if projected.stage is LifecycleStage.DONE or projected.outcome in {"authority-block", "blocked-by-authority", "cancelled-by-operator", "cancelled-by-decision", "failure", "timeout"}:
                return False
            if projected.stage not in ROLE_BY_STAGE:
                return False
            if projected.stage is LifecycleStage.ACCEPT and projected.outcome == READY_TO_LAND \
                    and not self._landing_enabled():
                return False
        except KeyError:
            pass
        return (self._is_automatic(item) or self._is_released(item.identity)) and all(self._dependency_done(dep) for dep in item.dependencies)

    def _run(self, item: ReadyWorkItem) -> StopReason | _WipSkip | None:
        version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
        current = replace(self.decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
        role = ROLE_BY_STAGE.get(current.stage)
        if role is None:
            return StopReason.BLOCKED
        if role == PRODUCER:
            # A work item already holding its WIP slot is never admitted again and needs no limit to continue.
            admitting = self._wip_limit is not None and not self._holds_wip(item.identity)
            # Release admission guards only the producer; a verifier or closure
            # invocation acts on work already admitted and never resets it.
            source = ReleaseSource.AUTOMATIC_POLICY if self._is_automatic(item) else ReleaseSource.EXPLICIT_HUMAN
            try:
                if self._release_gate is not None:
                    self._release_gate.check(item)
                capabilities = set(BASE_CAPABILITIES)
                if self._has_authorizing_decision(item.identity):
                    capabilities.update(item.contract.required_capabilities)
                admit_release({}, ReleaseRequest(item.identity, item.contract, item.readiness_digest, frozenset(item.dependencies), frozenset(capabilities), self._available_budget(item, raw), "offline-profile", source))
            except ReleasePreconditionRefused as refusal:
                self._record_result(item, current, "release", "authority-block", {"hold_reason": f"release-precondition:{refusal.check}"})
                self._register_escalation(self._authority_request(item, current.version, f"Release precondition refused: {refusal}."))
                self._block_dependents(item, self._work.import_ready_snapshot())
                return StopReason.BLOCKED
            except ValueError:
                self._record_result(item, current, "release", "authority-block")
                self._register_escalation(self._authority_request(item, current.version, "Release admission requires authority not present in this profile."))
                self._block_dependents(item, self._work.import_ready_snapshot())
                return StopReason.BLOCKED
            if admitting:
                limit = self._wip_limit()
                if limit is None:
                    return _WipSkip.UNAVAILABLE
                try:
                    self._store.acquire_within(self._profile, WIP_SCOPE, item.identity, self._wip_owner(item.identity), limit)
                except ReservationRejected:
                    return _WipSkip.REFUSED
            self._work.propose_release(item)
            version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
        elif role == CLOSURE and raw.get("outcome") == READY_TO_LAND and self._wip_limit is not None \
                and not self._holds_wip(item.identity):
            # `ready-to-land` released the slot; landing work is in progress again only within the limit.
            limit = self._wip_limit()
            if limit is None:
                return _WipSkip.UNAVAILABLE
            try:
                self._store.acquire_within(self._profile, WIP_SCOPE, item.identity, self._wip_owner(item.identity), limit)
            except ReservationRejected:
                return _WipSkip.REFUSED
        correlation = f"launch:{item.identity}:{version}"
        try:
            reservation = self._store.acquire(self._profile, "repository", item.repository, correlation)
        except ReservationRejected:
            return StopReason.CAPACITY_UNAVAILABLE
        read_back = False
        try:
            if role == PRODUCER and current.implement_cycles == 0:
                # The first admitted PRODUCER launch enters IMPLEMENT: counted in this launch's own commit, on
                # `current` so the recorded result built from it keeps the count. Unknown (None) stays unknown.
                current = replace(current, implement_cycles=1)
            invocation = self._invocation(item, correlation, role, current)
            # The invocation's own candidate is retained: a later rework clears
            # the state's candidate, and recovery must re-ask the same question.
            prepared = self._encode(current) | self._carried(raw) | {"role": role, "invocation_candidate": self._encode_candidate(invocation.candidate)}
            self._store.commit_with_effect(self._profile, self._aggregate(item.identity), version, prepared, correlation, {"correlation": correlation, "work": item.identity, "role": role})
            self._store.claim_effect(self._profile, correlation)
            outcome = self._worker.start(invocation, item.contract, frozenset(item.contract.required_capabilities), item.contract.budget_policy)
            if not self._correlated(invocation, outcome):
                return StopReason.BLOCKED if self._park_unknown_effect(item, reservation) else StopReason.CAPACITY_UNAVAILABLE
            try:
                self._store.confirm_effect(self._profile, correlation, f"outcome:{outcome.kind}")
            except ReservationRejected:
                return StopReason.BLOCKED if self._park_unknown_effect(item, reservation) else StopReason.CAPACITY_UNAVAILABLE
            advanced = self._advance(item, current, prepared, invocation, outcome)
            unresolved = self._has_unresolved_effect(item.identity)
            if unresolved:
                self._record_result(item, current, correlation, "authority-block")
                self._register_escalation(self._authority_request(item, current.version, "The external effect outcome is unknown and requires reconciliation authority."))
                self._block_dependents(item, self._work.import_ready_snapshot())
                self._store.release(self._profile, "repository", item.repository, correlation, reservation.fence)
                return StopReason.BLOCKED
            read_back = self._record_result(item, advanced.state, correlation, advanced.outcome, advanced.fields | {"role": role, "outcome_kind": outcome.kind, "invocation_candidate": prepared["invocation_candidate"]})
            if advanced.outcome == "authority-block":
                self._register_escalation(outcome.escalation or self._authority_request(
                    item, current.version, advanced.hold or "The worker raised an authority block that requires a durable decision."
                ))
                self._block_dependents(item, self._work.import_ready_snapshot())
                if role == PRODUCER:
                    self._finalize_workspace(item.identity, correlation, retain=True)
            elif read_back and role == PRODUCER:
                self._finalize_workspace(item.identity, correlation, retain=False)
            if read_back and advanced.state.stage is LifecycleStage.DONE:
                self._project(item.identity)
            self._work.project_execution_state(item.identity, advanced.state.stage, advanced.state.version)
            return None
        finally:
            if read_back and not self._has_unresolved_effect(item.identity):
                self._store.release(self._profile, "repository", item.repository, correlation, reservation.fence)

    def _available_budget(self, item: ReadyWorkItem, raw: dict[str, object]) -> Mapping[str, int]:
        """The budget admit_release checks: the configured allocation less durable consumption.

        Without a configured allocation the profile is unmetered and every
        required dimension is admitted, as before WO-220611.
        """
        if self._allocation is None:
            return {dimension: 1 for dimension in item.contract.budget_policy.required_dimensions}
        consumed = {"attempts": int(raw.get("rejections", 0) or 0)} if raw else {}
        return self._allocation.available_budget(item.identity, item.contract, consumed)

    @staticmethod
    def _invocation(item: ReadyWorkItem, correlation: str, role: str, state: ExecutionState) -> WorkerInvocation:
        """One role invocation; verifier and closure act on the exact custodied candidate."""
        return WorkerInvocation(item.identity, correlation, item.contract.content_digest, role, None if role == PRODUCER else state.candidate)

    def _correlated(self, invocation: WorkerInvocation, outcome: WorkerOutcome) -> bool:
        """Only an outcome the worker durably reads back for this invocation is execution truth.

        A process that exits successfully without a correlated durable result,
        or whose result reads back as another kind, candidate, finding or
        receipt, holds here.
        """
        durable = self._worker.read_back(invocation)
        return durable is not None and self._observables(durable) == self._observables(outcome)

    @staticmethod
    def _observables(outcome: WorkerOutcome) -> tuple[object, ...]:
        return outcome.kind, outcome.candidate, tuple(outcome.findings), tuple(outcome.receipts)

    def _advance(self, item: ReadyWorkItem, current: ExecutionState, prior: dict[str, object], invocation: WorkerInvocation, outcome: WorkerOutcome) -> _Advance:
        """The canonical lifecycle consequence of one correlated role outcome.

        Producer success advances only to VERIFY. Only a distinct verifier's
        verdict on the exact custodied candidate reaches REVIEW, and only a
        trusted policy verdict reaches ACCEPT. DONE requires read-back receipts
        for every required closure action. Anything else holds or reworks.
        """
        if outcome.kind == "authority-block":
            return _Advance(current, "authority-block", {})
        if outcome.kind == MISSING_TERMINAL_RESULT:
            # No lifecycle consequence: the unchanged stage re-dispatches its
            # own role on the same custodied candidate, bounded at launch.
            return _Advance(current, outcome.kind, {})
        if invocation.role == PRODUCER:
            if outcome.kind != "success" or outcome.candidate is None:
                return _Advance(current, outcome.kind, {})
            # The custody gate is control-plane enforcement: it always rechecks
            # candidate retrieval rather than trusting a producer-set assertion.
            verified = verify_in_fresh_process(outcome.candidate, self._artifacts.verifier_root)
            return _Advance(transition(current, current.version, "verify", candidate=verified), "success", {"producer_correlation": invocation.correlation_id})
        if invocation.role == VERIFIER:
            if outcome.kind in {"failure", "timeout"}:
                return _Advance(current, outcome.kind, {})
            producer = prior.get("producer_correlation")
            if (
                outcome.kind not in {"accept", "reject"}
                or not self._same_candidate(outcome.candidate, current.candidate)
                or not isinstance(producer, str) or producer == invocation.correlation_id
                or (outcome.kind == "reject" and not outcome.findings)
            ):
                return _Advance(current, "authority-block", {"hold_reason": f"verifier-outcome-not-attributable:{outcome.kind}"},
                                "The verifier outcome does not attest the exact custodied candidate from an independent invocation.")
            feature_receipts = tuple(receipt for receipt in outcome.receipts
                                     if receipt.startswith("feature-regressions:sha256:"))
            if not feature_receipts:
                return _Advance(current, "authority-block",
                                {"hold_reason": "feature-regressions-missing"},
                                "VERIFY did not retain a passing feature-regression receipt for the exact candidate.")
            if outcome.kind == "reject":
                return self._rework(item, current, prior, invocation, "verifier", outcome.findings)
            reviewed = transition(current, current.version, "review")
            observations = (Observation(ARTIFACT_VERIFIED, True, bool(current.candidate and current.candidate.verify_admissible)), Observation(VERIFIER_EVIDENCE, True, True))
            verdict = evaluate_verdict(EvidenceDefinition(frozenset(item.contract.required_evidence) | {VERIFIER_EVIDENCE}), observations, worker_claimed_success=True)
            if verdict.kind is not VerdictKind.ACCEPT:
                return self._rework(item, reviewed, prior, invocation, "review", (verdict.reason,))
            accepted = transition(reviewed, reviewed.version, "accept", verdict=verdict)
            return _Advance(accepted, "accept", {"verdict": {"kind": str(verdict.kind), "reason": verdict.reason, "verifier_correlation": invocation.correlation_id}})
        if is_fixed(item.contract.required_closure_actions):
            return self._advance_closure(item, current, prior, invocation, outcome)
        receipts = frozenset(outcome.receipts)
        if outcome.kind != "closed" or not self._same_candidate(outcome.candidate, current.candidate) or not set(item.contract.required_closure_actions) <= receipts:
            return _Advance(current, "authority-block", {"hold_reason": "closure-receipts-incomplete", "receipts": sorted(receipts)},
                            "Closure did not read back every required closure action for the accepted candidate.")
        return _Advance(transition(current, current.version, "close", completed_closure_actions=receipts), "closed", {"receipts": sorted(receipts)})

    def _advance_closure(self, item: ReadyWorkItem, current: ExecutionState, prior: dict[str, object],
                         invocation: WorkerInvocation, outcome: WorkerOutcome) -> _Advance:
        """The fixed-name rule: only receipts naming this item and the full custodied revision count."""
        revision = None if current.candidate is None else current.candidate.locator.rpartition("@")[2]
        exact = sorted(text for text in outcome.receipts
                       if (parsed := parse_receipt(text)) is not None and parsed[1:] == (item.identity, revision))
        kept = {text.split(":", 1)[0] for text in exact}
        if outcome.kind == "closed" and self._same_candidate(outcome.candidate, current.candidate):
            if kept == set(ACTIONS):
                return _Advance(transition(current, current.version, "close", completed_closure_actions=frozenset(kept)),
                                "closed", {"receipts": exact})
            control = [parsed for text in outcome.findings if (parsed := parse_finding(text)) is not None]
            kinds = [kind for kind, _ in control]
            if kept == {CANDIDATE_PUBLISHED} and kinds == [READY_TO_LAND]:
                return _Advance(current, READY_TO_LAND, {"receipts": exact, "ready_to_land": control[0][1][0]})
            if CLOSURE_REWORK in kinds and CLOSURE_HOLD not in kinds:
                return self._rework(item, current, prior, invocation, "closure", tuple(outcome.findings))
            held = next((parts for kind, parts in control if kind == CLOSURE_HOLD), None)
            if held is not None:
                return _Advance(current, "authority-block", {"hold_reason": f"closure-hold:{held[0]}", "receipts": exact},
                                f"Closure holds ({held[0]}): {':'.join(held[1:]) or 'no facts'}.")
        missing = [action for action in ACTIONS if action not in kept]
        return _Advance(current, "authority-block", {"hold_reason": "closure-receipts-incomplete", "receipts": exact},
                        f"Closure did not read back these closure actions for the accepted candidate: {', '.join(missing)}.")

    @staticmethod
    def _same_candidate(reported: CandidateRef | None, custodied: CandidateRef | None) -> bool:
        return reported is not None and custodied is not None and (reported.kind, reported.identity, reported.content_digest) == (custodied.kind, custodied.identity, custodied.content_digest)

    def _rework(self, item: ReadyWorkItem, state: ExecutionState, prior: dict[str, object], invocation: WorkerInvocation, source: str, findings: tuple[str, ...]) -> _Advance:
        """Record attributable findings and return to IMPLEMENT within the attempt budget."""
        rejections = int(prior.get("rejections", 0) or 0) + 1
        recorded = [*prior.get("findings", ()), {
            "source": source, "correlation": invocation.correlation_id,
            "candidate": None if state.candidate is None else state.candidate.identity, "findings": list(findings),
        }]
        reworked = transition(state, state.version, "rework")
        fields: dict[str, object] = {"rejections": rejections, "findings": recorded}
        if rejections >= item.contract.budget_policy.maximum_attempts:
            return _Advance(reworked, "failure", fields | {"hold_reason": "attempt-budget-exhausted"})
        return _Advance(reworked, "rework", fields)

    @staticmethod
    def _carried(raw: dict[str, object]) -> dict[str, object]:
        return {key: raw[key] for key in CARRIED if key in raw}

    def _record_result(self, item: ReadyWorkItem, state: ExecutionState, correlation: str, outcome: str, fields: dict[str, object] | None = None) -> bool:
        version, prior = self._store.read_state(self._profile, self._aggregate(item.identity))
        persisted = self._encode(state) | self._carried(prior) | (fields or {}) | {"correlation": correlation, "outcome": outcome}
        self._store.commit(self._profile, self._aggregate(item.identity), version, persisted)
        _, read_back = self._store.read_state(self._profile, self._aggregate(item.identity))
        recorded = read_back.get("correlation") == correlation and read_back.get("outcome") == outcome
        if recorded:
            self._release_ended_wip(item.identity)
            if self._stage_shown is not None:
                try:
                    self._stage_shown(item.identity)
                except Exception as error:  # noqa: BLE001 - board display cannot change a recorded result
                    self.projection_diagnostics[item.identity] = f"{item.identity}: {type(error).__name__}: {error}"
        return recorded

    @staticmethod
    def _wip_owner(identity: str) -> str:
        return f"work:{identity}"

    def _wip_reservations(self, identity: str):
        return [reservation for reservation in self._store.recovery_reservations(self._profile)
                if reservation.scope == WIP_SCOPE and reservation.key == identity and reservation.owner == self._wip_owner(identity)]

    def _holds_wip(self, identity: str) -> bool:
        return bool(self._wip_reservations(identity))

    def _release_ended_wip(self, identity: str) -> None:
        """Release the work item's WIP slot once its recorded state reads back as DONE or a final outcome.

        Every other state (authority holds, reworks, retries, unknown effects) keeps the slot.
        """
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if raw.get("stage") != LifecycleStage.DONE.value and raw.get("outcome") not in FINAL_OUTCOMES | {READY_TO_LAND}:
            return
        for reservation in self._wip_reservations(identity):
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)

    def _recover(self, items: Iterable[ReadyWorkItem]) -> bool:
        by_identity = {item.identity: item for item in items}
        reservations = self._store.recovery_reservations(self._profile)
        # WIP slots first, from the recorded work item state alone (not the READY snapshot): a crash between the
        # recorded DONE or final outcome and its release is completed here; every other slot is kept.
        for reservation in reservations:
            if reservation.scope == WIP_SCOPE:
                self._release_ended_wip(reservation.key)
        for reservation in reservations:
            if reservation.scope == WIP_SCOPE or (reservation.scope, reservation.key) == (LAUNCH_SCOPE, LAUNCH_KEY):
                continue
            if reservation.scope != "repository" or not reservation.owner.startswith("launch:"):
                return False
            try:
                _, identity, _ = reservation.owner.rsplit(":", 2)
            except ValueError:
                return False
            item = by_identity.get(identity)
            if item is None and self._started_item is not None:
                # Recovery of a started item never depends on its board status.
                item = self._started_item(identity, reservation.owner)
            if item is None:
                return False
            effect = self._effect_status(reservation.owner)
            if effect == "none":
                # Crashed after the repository reservation and before `commit_with_effect`: with the record still at
                # the launch's version, nothing was saved or started, so only the reservation is released.
                version, _ = self._store.read_state(self._profile, self._aggregate(identity))
                if str(version) == reservation.owner.rsplit(":", 1)[1]:
                    self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
                    continue
            elif effect == "pending":
                # Saved but never claimed (a worker starts only after `claim_effect`): parked for a decision.
                self._store.claim_effect(self._profile, reservation.owner)
                if not self._park_unknown_effect(item, reservation, f"{NEVER_STARTED}: {reservation.owner}"):
                    return False
                continue
            _, raw = self._store.read_state(self._profile, self._aggregate(identity))
            current = replace(self.decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
            role = str(raw.get("role") or PRODUCER)
            given = raw.get("invocation_candidate")
            invocation = WorkerInvocation(identity, reservation.owner, item.contract.content_digest, role, self._decode_candidate(given) if isinstance(given, dict) else None)
            outcome = self._worker.read_back(invocation)
            reconcile = getattr(self._worker, "reconcile_closure", None)
            if outcome is None and role == CLOSURE and callable(reconcile):
                # A begun landing is settled from the journal and the remote, never by a model session.
                outcome = reconcile(invocation)
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
            if raw.get("correlation") == reservation.owner and raw.get("outcome_kind", raw.get("outcome")) == outcome.kind:
                if raw.get("outcome") == "authority-block":
                    self._restore_authority_block(item, current, outcome, reservation.owner, items, role)
                self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
                continue
            advanced = self._advance(item, current, raw, invocation, outcome)
            if not self._record_result(item, advanced.state, reservation.owner, advanced.outcome, advanced.fields | {"role": role, "outcome_kind": outcome.kind, "invocation_candidate": given}):
                return False
            if advanced.state.stage is LifecycleStage.DONE:
                self._project(identity)
            if advanced.outcome == "authority-block":
                self._restore_authority_block(item, current, outcome, reservation.owner, items, role, advanced.hold)
            elif role == PRODUCER:
                # A recovered PRODUCER result disposes of its worktree, owned by the correlation; a recorded
                # missing-terminal-result keeps it (its progress stays for diagnosis).
                self._finalize_workspace(identity, reservation.owner, retain=outcome.kind == MISSING_TERMINAL_RESULT)
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
        return True

    def _resolve(self, identity: str, items: Iterable[ReadyWorkItem], raw: Mapping[str, object]) -> ReadyWorkItem | None:
        """The READY row of a work item, else the item built from its registry record (`started_item`)."""
        item = next((ready for ready in items if ready.identity == identity), None)
        correlation = raw.get("correlation")
        if item is None and self._started_item is not None and isinstance(correlation, str):
            item = self._started_item(identity, correlation)
        return item

    def _project(self, identity: str) -> None:
        """The DONE projection hook; a refusal or error is a diagnostic, never raised into the coordinator."""
        if self._completed is None:
            return
        try:
            self._completed(identity)
            self.projection_diagnostics.pop(identity, None)
        except Exception as error:  # noqa: BLE001 - the row stays unchanged and the next launch retries
            self.projection_diagnostics[identity] = f"{identity}: {type(error).__name__}: {error}"

    def _project_done(self) -> None:
        """Every recorded DONE is projected again, whatever its board status, so any crash is repaired."""
        if self._completed is None:
            return
        try:
            states = self._store.list_states(self._profile, "factory:")
        except Exception as error:  # noqa: BLE001 - an unreadable store is a diagnostic; the launch continues
            self.projection_diagnostics["*"] = f"list_states: {type(error).__name__}"
            return
        for aggregate, _, raw in states:
            if raw.get("stage") == LifecycleStage.DONE.value:
                self._project(aggregate.removeprefix("factory:"))

    def _show_stages(self, identity: str) -> None:
        """Retry the named card and active recorded cards from one state snapshot."""
        if self._stage_shown is None:
            return
        targets = {identity}
        try:
            states = self._store.list_states(self._profile, "factory:")
        except Exception as error:  # noqa: BLE001 - a failed sweep cannot change admission
            self.projection_diagnostics["*"] = f"list_states: {type(error).__name__}: {error}"
            states = ()
        for aggregate, _, raw in states:
            if raw.get("stage") != LifecycleStage.DONE.value and raw.get("outcome") not in FINAL_OUTCOMES:
                targets.add(aggregate.removeprefix("factory:"))
        for target in targets:
            try:
                self._stage_shown(target)
            except Exception as error:  # noqa: BLE001 - board display cannot change admission
                self.projection_diagnostics[target] = f"{target}: {type(error).__name__}: {error}"

    def _restore_authority_block(self, item: ReadyWorkItem, state: ExecutionState, outcome: WorkerOutcome, correlation: str, items: Iterable[ReadyWorkItem], role: str = PRODUCER, hold: str | None = None) -> None:
        self._register_escalation(outcome.escalation or self._authority_request(
            item, state.version, hold or "The worker raised an authority block that requires a durable decision."
        ))
        self._block_dependents(item, items)
        if role == PRODUCER:
            self._finalize_workspace(item.identity, correlation, retain=True)

    def _effect_status(self, correlation: str) -> str | None:
        """The correlation's effect status in the store's read-only ledger, "none" when it has no effect row, or None
        when the store keeps no ledger."""
        ledger = getattr(self._store, "effect_ledger", None)
        if not callable(ledger):
            return None
        return next((status for identity, status, _ in ledger(self._profile) if identity == correlation), "none")

    def _park_unknown_effect(self, item: ReadyWorkItem, reservation, reason: str | None = None) -> bool:
        """Turn an unreadable FD-05 effect into a scoped, durable authority block."""
        version, raw = self._store.read_state(self._profile, self._aggregate(item.identity))
        current = replace(self.decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
        blocked = self._encode(current) | self._carried(raw) | {"correlation": reservation.owner, "outcome": "authority-block"}
        try:
            self._store.park_unknown_effect(self._profile, reservation.owner, version, blocked)
            self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
        except ReservationRejected:
            return False
        self._register_escalation(self._authority_request(item, current.version, reason or "The external effect outcome is unknown and requires reconciliation authority."))
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

    def _dependency_done(self, identity: str) -> bool:
        """A dependency's coordinator record decides when it has one (DONE counts; any other stage does not, whatever
        the work registry row says); with none, the injected reader of a recorded completion decides."""
        try:
            return self.state(identity).stage is LifecycleStage.DONE
        except KeyError:
            return self._recorded_completion is not None and self._recorded_completion(identity)

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
    def _encode_candidate(candidate: CandidateRef | None) -> dict[str, object] | None:
        return None if candidate is None else {"kind": candidate.kind, "identity": candidate.identity, "content_digest": candidate.content_digest, "locator": candidate.locator, "provenance": candidate.provenance, "independent_read_back_proven": candidate.independent_read_back_proven}

    @staticmethod
    def _decode_candidate(record: dict[str, object]) -> CandidateRef:
        return CandidateRef(CandidateKind(str(record["kind"])), str(record["identity"]), str(record["content_digest"]), str(record["locator"]), str(record["provenance"]), bool(record["independent_read_back_proven"]))

    @classmethod
    def _encode(cls, state: ExecutionState) -> dict[str, object]:
        return {"stage": state.stage, "version": state.version, "accepted": state.accepted, "closure": sorted(state.completed_closure_actions), "candidate": cls._encode_candidate(state.candidate),
                "implement_cycles": state.implement_cycles, "verify_cycles": state.verify_cycles}

    @classmethod
    def decode(cls, raw: Mapping[str, object]) -> ExecutionState:
        """The coordinator's own decoding of a recorded `factory:<identity>` state."""
        record = raw.get("candidate")
        candidate = cls._decode_candidate(record) if isinstance(record, dict) else None
        stage = LifecycleStage(str(raw["stage"]))
        return ExecutionState(stage, int(raw["version"]), candidate, bool(raw["accepted"]), frozenset(raw["closure"]), None, *cls._cycles(raw, stage))

    @staticmethod
    def _cycles(raw: Mapping[str, object], stage: LifecycleStage) -> tuple[int | None, int | None]:
        """Recorded counts; for an older record without them, only what its retained history proves.

        A record proves a PRODUCER launch only by `producer_correlation`, a non-zero `rejections`, non-empty
        `findings` or a stage past IMPLEMENT; every rework retains `rejections`. Anything else is unknown (None).
        """
        if "implement_cycles" in raw or "verify_cycles" in raw:
            implement, verify = raw.get("implement_cycles"), raw.get("verify_cycles")
            return (implement if type(implement) is int else None), (verify if type(verify) is int else None)
        rejections = raw.get("rejections") or 0
        if type(rejections) is not int:
            return None, None
        past_implement = stage is not LifecycleStage.IMPLEMENT
        if not (isinstance(raw.get("producer_correlation"), str) or rejections or raw.get("findings") or past_implement):
            return None, None
        return 1 + rejections, rejections + (1 if past_implement else 0)

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
                state = replace(self.decode(raw), contract=item.contract) if raw else ExecutionState.for_contract(item.contract)
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
            self._release_ended_wip(item.identity)

    def record_decision(self, record: DecisionRecord) -> None:
        version, raw = self._store.read_state(self._profile, self._aggregate(record.event.work_item))
        already_recorded = raw.get("decision_key") == record.event.idempotency_key
        if not already_recorded:
            self.validate_decision(record)
        state = self.decode(raw)
        items = self._work.import_ready_snapshot()
        if not already_recorded:
            outcome = "cancelled-by-decision" if record.submission.choice == "cancel" else "decision-recorded"
            decision_state = self._encode(state) | self._carried(raw) | {"outcome": outcome, "decision_key": record.event.idempotency_key, "decision_choice": record.submission.choice}
            if isinstance(raw.get("correlation"), str):
                decision_state["correlation"] = raw["correlation"]
            if record.submission.choice == "cancel":
                self._store.commit(self._profile, self._aggregate(record.event.work_item), version, decision_state)
                self._release_ended_wip(record.event.work_item)
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
        state = self.decode(raw)
        if state.version != record.submission.expected_version or record.submission.biu_version != state.version:
            raise SupersededDecision("decision target version is superseded")
