"""Bounded coordinator episodes and stale-command refusal (SF-REQ-053, contract 8).

Every authority-bearing result goes through S2 `commit_guarded` with the episode's pinned
relevant vector (U-4): the C2 manifest's live aggregates plus `episode:<objective>`, which is
also the S2 authority record (U-1). Tenure is checked on each result, event and injected
timer tick. Ending never renews and never cancels an already-admitted effect.
"""
from collections.abc import Callable
from dataclasses import replace
from typing import Mapping

from alienintent.control_plane.domain.episode import (
    CHANGE_CAUSES, SECOND, SIGNAL_CAUSES, AcceptedContradiction, ContradictionJudgment, EndCause, EpisodeHold,
    EpisodeRecord, EpisodeState, HoldReason, InvalidJudgment, InvalidPolicy, OperatorGrant, TenurePolicy,
    UsageBinding, admit_contradiction, authorized, blocked, digest, evaluate_tenure, next_blocked_since,
    validate_usage,
)
from alienintent.control_plane.ports.episode import (
    Admitted, ContextSource, ContextUnavailable, ContextUsageObservation, ContextView, ContradictionObservation,
    CoordinatorResult, DeadlineTimer, EpisodeControl, EpisodeRepository, Refused,
)
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.domain.lifecycle import (
    AuthorityBlocked, ExecutionState, LifecycleError, LifecycleStage, transition,
)
from alienintent.execution_coordination.domain.verdict import Verdict, VerdictKind
from alienintent.execution_coordination.ports.fenced_store import FencedOperationalStore, GuardVector
from alienintent.execution_coordination.ports.operational_store import (
    Reservation, ReservationRejected, SchemaIncompatible, StoreUnavailable, VersionConflict,
)

RESERVATION_SCOPE = "episode-work"


def _decode(raw: Mapping[str, object]) -> ExecutionState:
    """The durable `factory:<id>` shape FactoryCoordinator writes; absent means a fresh IMPLEMENT."""
    if not raw:
        return ExecutionState()
    record = raw.get("candidate")
    candidate = None if not isinstance(record, dict) else _candidate(record)
    return ExecutionState(LifecycleStage(str(raw["stage"])), int(raw["version"]), candidate, bool(raw["accepted"]),
                          frozenset(raw["closure"]), None)


def _candidate(record: Mapping[str, object] | None) -> CandidateRef | None:
    if record is None:
        return None
    return CandidateRef(CandidateKind(str(record["kind"])), str(record["identity"]), str(record["content_digest"]),
                        str(record["locator"]), str(record["provenance"]), bool(record["independent_read_back_proven"]))


def _encode(state: ExecutionState, raw: Mapping[str, object]) -> dict[str, object]:
    candidate = state.candidate
    encoded = None if candidate is None else {
        "kind": str(candidate.kind), "identity": candidate.identity, "content_digest": candidate.content_digest,
        "locator": candidate.locator, "provenance": candidate.provenance,
        "independent_read_back_proven": candidate.independent_read_back_proven}
    return {**raw, "stage": str(state.stage), "version": state.version, "accepted": state.accepted,
            "closure": sorted(state.completed_closure_actions), "candidate": encoded}


class EpisodeControlService(EpisodeControl, ContradictionObservation):
    def __init__(self, repository: EpisodeRepository, store: FencedOperationalStore, context: ContextSource, *,
                 profile: str, invocation: str, monotonic: Callable[[], int], utc_clock: Callable[[], int],
                 timer: DeadlineTimer, policy: TenurePolicy, usage: ContextUsageObservation | None,
                 operators: tuple[OperatorGrant, ...]) -> None:
        if (usage is None) is (policy.usage is UsageBinding.BOUND):
            raise InvalidPolicy("BOUND usage requires an injected same-invocation source; UNBOUND takes none")
        self.repository, self.store, self.context = repository, store, context
        self.profile, self.invocation, self.timer = profile, invocation, timer
        self.policy, self.usage, self.operators = policy, usage, operators
        self._monotonic = monotonic
        # Persisted UTC anchors restart; monotonic progress measures tenure within this process.
        self._mono0 = self._last = monotonic()
        self._utc0 = utc_clock()

    # -- clocks -------------------------------------------------------------------------------
    def now(self) -> int:
        reading = self._monotonic()
        if type(reading) is not int or reading < self._last:
            raise EpisodeHold(HoldReason.CLOCK_REGRESSION, "monotonic clock regressed")
        self._last = reading
        return self._utc0 + (reading - self._mono0)

    def store_seconds(self) -> float:
        """The S2 store's injected clock, on the same tenure time base as `expires_at`."""
        return self.now() / SECOND

    def _checked_now(self, record: EpisodeRecord | None) -> int:
        now = self.now()
        if record is not None and now < record.last_check_us:
            raise EpisodeHold(HoldReason.CLOCK_REGRESSION, "UTC is earlier than the persisted tenure check")
        return now

    # -- durable state ------------------------------------------------------------------------
    def _load(self, objective: str) -> tuple[int, EpisodeRecord | None]:
        try:
            return self.repository.load(objective)
        except (StoreUnavailable, SchemaIncompatible) as error:
            raise EpisodeHold(HoldReason.STORE_UNAVAILABLE, str(error)) from error

    def _active(self, objective: str) -> tuple[int, EpisodeRecord]:
        version, record = self._load(objective)
        if record is None:
            raise EpisodeHold(HoldReason.NO_EPISODE, objective)
        return version, record

    def _save(self, version: int, record: EpisodeRecord, event: Mapping[str, object]) -> int:
        try:
            return self.repository.save(version, record, event)
        except VersionConflict as error:
            raise EpisodeHold(HoldReason.EPISODE_CONFLICT, str(error)) from error

    def _end(self, version: int, record: EpisodeRecord, cause: EndCause, now: int,
             event: Mapping[str, object]) -> EpisodeRecord:
        """End tenure. The pointer goes inactive first, so S2 refuses every later guarded command."""
        ended = replace(record, state=EpisodeState.ENDED, cause=cause, last_check_us=now)
        self._save(version, ended, {**event, "action": "END", "cause": str(cause), "at": now})
        if ended.state is EpisodeState.ENDED and record.reservation is not None:
            try:
                self.store.release(self.profile, *record.reservation)
            except (ReservationRejected, StoreUnavailable):
                pass  # an admitted, unresolved effect keeps its reservation; nothing is cancelled
        return ended

    def vector_digest(self, objective: str) -> str:
        version, record = self._active(objective)
        return self._vector_digest(version, record)

    @staticmethod
    def _vector_digest(version: int, record: EpisodeRecord) -> str:
        return digest({"manifest_ref": record.manifest_ref, "episode": [record.aggregate, version]})

    def _fresh_context(self) -> ContextView:
        pointer = self.context.pin()
        if isinstance(pointer, ContextUnavailable):
            raise EpisodeHold(HoldReason.CONTEXT_UNAVAILABLE, pointer.reason)
        view = self.context.reconstruct(pointer)
        if isinstance(view, ContextUnavailable):
            raise EpisodeHold(HoldReason.CONTEXT_UNAVAILABLE, view.reason)
        return view

    # -- tenure checks ------------------------------------------------------------------------
    def _check(self, record: EpisodeRecord, now: int,
               document: Mapping[str, object] | None) -> tuple[EndCause | None, EpisodeRecord, dict[str, object]]:
        seq = record.check_seq + 1
        if document is not None:
            record = replace(record, blocked_since_us=next_blocked_since(record, blocked(document, record.objective), now))
        record = replace(record, check_seq=seq, last_check_us=now)
        check_id = f"check:{record.epoch}:{seq}"
        observation = None if self.usage is None else self.usage.read(record.invocation, check_id)
        usage = validate_usage(self.policy, observation, invocation=record.invocation, check_id=check_id)
        event = {"check_id": check_id, "at": now, "usage_binding": str(self.policy.usage),
                 "usage": None if usage.ratio is None else {"ratio": usage.ratio}, "usage_detail": usage.detail,
                 "blocked_since_us": record.blocked_since_us}
        return evaluate_tenure(record, self.policy, now) or usage.cause, record, event

    def tick(self, objective: str) -> EpisodeRecord:
        """The injected deadline timer's callback; no result or model is involved."""
        version, record = self._active(objective)
        if record.state is EpisodeState.ENDED:
            return record
        now = self._checked_now(record)
        pointer = self.context.pin()
        view = None if isinstance(pointer, ContextUnavailable) else self.context.reconstruct(pointer)
        document = view.document if isinstance(view, ContextView) else None
        cause, record, event = self._check(record, now, document)
        if cause is not None:
            return self._end(version, record, cause, now, {**event, "source": "tick"})
        self._save(version, record, {**event, "action": "CHECK", "source": "tick"})
        return record

    # -- lifecycle ----------------------------------------------------------------------------
    def begin(self, objective: str, *, actor: str, provider: str, model: str, authority: str,
              objective_revision: str) -> EpisodeRecord:
        """Only an explicit authorized begin opens an epoch; budget accounting carries over."""
        grant = authorized(self.operators, actor, objective)
        if grant is None:
            raise EpisodeHold(HoldReason.UNAUTHORIZED, f"{actor} may not begin {objective}")
        version, prior = self._load(objective)
        if prior is not None and prior.state is EpisodeState.ACTIVE:
            raise EpisodeHold(HoldReason.EPISODE_ACTIVE, f"epoch {prior.epoch} has not ended")
        now = self._checked_now(prior)
        view = self._fresh_context()
        try:
            (reservation,) = self.store.acquire_many(self.profile, ((RESERVATION_SCOPE, objective),), self.invocation)
        except ReservationRejected as error:
            raise EpisodeHold(HoldReason.RESERVATION_RETAINED, str(error)) from error
        record = EpisodeRecord(
            objective=objective, epoch=1 if prior is None else prior.epoch + 1, invocation=self.invocation,
            state=EpisodeState.ACTIVE, cause=None, began_us=now, deadline_us=now + self.policy.max_age_s * SECOND,
            last_check_us=now, check_seq=0, transitions=0,
            blocked_since_us=now if blocked(view.document, objective) else None, accepted_contradictions=0,
            provider=provider, model=model, authority=authority, objective_revision=objective_revision,
            manifest_ref=view.manifest_ref, context_digest=view.digest,
            reservation=(reservation.scope, reservation.key, reservation.owner, reservation.fence),
            usage_binding=self.policy.usage, policy_digest=self.policy.digest(),
            admitted_total=0 if prior is None else prior.admitted_total,
            epochs=1 if prior is None else prior.epochs + 1)
        try:
            self.repository.save(version, record, {"action": "BEGIN", "at": now, "actor": actor,
                                                   "authority": grant.authority, "policy": self.policy.document()})
        except VersionConflict as error:
            self.store.release(self.profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)
            raise EpisodeHold(HoldReason.EPISODE_CONFLICT, str(error)) from error
        self.timer.arm(objective, record.epoch, record.deadline_us)
        return record

    def end(self, objective: str, *, epoch: int, actor: str) -> EpisodeRecord:
        grant = authorized(self.operators, actor, objective)
        if grant is None:
            raise EpisodeHold(HoldReason.UNAUTHORIZED, f"{actor} may not end {objective}")
        version, record = self._active(objective)
        if record.epoch != epoch:
            raise EpisodeHold(HoldReason.EPISODE_CONFLICT, f"epoch {epoch} is not current")
        if record.state is EpisodeState.ENDED:
            return record
        now = self._checked_now(record)
        return self._end(version, record, EndCause.EXPLICIT_REQUEST, now, {"actor": actor, "authority": grant.authority})

    def observe(self, objective: str, kind: str, identity: str | None) -> EpisodeRecord:
        """Objective/authority/provider/model identity against the value bound at begin (U-5, U-6)."""
        if kind not in CHANGE_CAUSES:
            raise ValueError(kind)
        version, record = self._active(objective)
        if record.state is EpisodeState.ENDED:
            return record
        if identity is None:
            raise EpisodeHold(HoldReason.SOURCE_UNCHECKABLE, kind)
        now = self._checked_now(record)
        bound = {"objective": record.objective_revision, "authority": record.authority,
                 "provider": record.provider, "model": record.model}[kind]
        if identity != bound:
            return self._end(version, record, CHANGE_CAUSES[kind], now, {"observed": kind, "identity": identity})
        return record

    def signal(self, objective: str, kind: str, source: str) -> EpisodeRecord:
        """A durable terminal-outcome or context-exhausted event ends tenure immediately."""
        if kind not in SIGNAL_CAUSES:
            raise ValueError(kind)
        version, record = self._active(objective)
        if record.state is EpisodeState.ENDED:
            return record
        now = self._checked_now(record)
        return self._end(version, record, SIGNAL_CAUSES[kind], now, {"signal": kind, "source": source})

    def record(self, judgment: ContradictionJudgment) -> AcceptedContradiction | InvalidJudgment:
        """Admit an operator contradiction judgment; only an accepted one counts toward tenure."""
        version, record = self._load(judgment.objective)
        if record is None:
            return InvalidJudgment("NO_EPISODE")
        if record.state is EpisodeState.ENDED:
            return InvalidJudgment("NOT_ACTIVE")
        entries = self.context.entries(record.manifest_ref)
        if isinstance(entries, ContextUnavailable):
            return InvalidJudgment("CONTEXT_UNAVAILABLE")
        outcome = admit_contradiction(judgment, objective=record.objective, epoch=record.epoch,
                                      vector_digest=self._vector_digest(version, record), grants=self.operators,
                                      resolvable=frozenset(aggregate for aggregate, _ in entries))
        if isinstance(outcome, InvalidJudgment):
            return outcome
        now = self._checked_now(record)
        record = replace(record, accepted_contradictions=record.accepted_contradictions + 1, last_check_us=now)
        event = {"contradiction": outcome.digest, "actor": judgment.actor, "authority": outcome.authority,
                 "conflicting_refs": list(judgment.conflicting_refs), "rationale": judgment.rationale,
                 "evidence_refs": list(judgment.evidence_refs)}
        cause = evaluate_tenure(record, self.policy, now)
        if cause is not None:
            self._end(version, record, cause, now, event)
        else:
            self._save(version, record, {**event, "action": "CONTRADICTION", "at": now})
        return outcome

    # -- guarded admission --------------------------------------------------------------------
    @staticmethod
    def _admitted_identity(result: CoordinatorResult, record: EpisodeRecord) -> tuple[int, str] | None:
        if (result.epoch, result.invocation) != (record.epoch, record.invocation):
            return None
        return result.epoch, result.invocation

    def submit(self, result: CoordinatorResult) -> Admitted | Refused:
        version, record = self._active(result.episode)
        if result.work != record.objective:
            return Refused("ONE_BIU", f"episode is bound to {record.objective}", record)
        if record.state is EpisodeState.ENDED:
            return Refused("NOT_ACTIVE", str(record.cause), record)
        identity = self._admitted_identity(result, record)
        if identity is None:
            return Refused("STALE_EPOCH", f"result epoch {result.epoch} is not current epoch {record.epoch}", record)
        now = self._checked_now(record)
        cause, record, event = self._check(record, now, None)
        if cause is not None:
            return Refused(str(cause), "tenure ended", self._end(version, record, cause, now, event))
        version = self._save(version, record, {**event, "action": "CHECK", "source": "result"})
        entries = self.context.entries(result.manifest_ref)
        if isinstance(entries, ContextUnavailable):
            return Refused("CONTEXT_UNAVAILABLE", entries.reason, record)
        stale = [aggregate for aggregate, pinned in entries if self.store.read_state(self.profile, aggregate)[0] != pinned]
        if stale:
            ended = self._end(version, record, EndCause.STALE_VECTOR, now, {"stale": stale, "effect_id": result.effect_id})
            return Refused("STALE_VECTOR", ", ".join(stale), ended)
        view = self.context.reconstruct(result.manifest_ref)
        if isinstance(view, ContextUnavailable):
            return Refused("CONTEXT_UNAVAILABLE", view.reason, record)
        record = replace(record, manifest_ref=view.manifest_ref, context_digest=view.digest,
                         blocked_since_us=next_blocked_since(record, blocked(view.document, record.objective), now))
        offered = {(a["work"], a["action"], a["expected_version"]) for a in view.document["authorized_next_action_set"]}
        if (result.work, result.action, result.expected_version) not in offered:
            return Refused("AUTHORITY_REFUSED", "action is not authorized by the reconstructed context", record)
        target, pinned = "factory:" + record.objective, dict(entries)
        if target not in pinned:
            return Refused("AUTHORITY_REFUSED", "the objective has no pinned execution record", record)
        _, raw = self.store.read_state(self.profile, target)
        try:
            verdict = None if result.verdict is None else Verdict(VerdictKind(result.verdict), "coordinator result")
            state = transition(_decode(raw), result.expected_version, result.action,
                               candidate=_candidate(result.candidate), verdict=verdict,
                               completed_closure_actions=_decode(raw).completed_closure_actions)
        except AuthorityBlocked as error:
            return Refused("AUTHORITY_BLOCKED", str(error), record)
        except (LifecycleError, ValueError, KeyError, TypeError) as error:
            return Refused("AUTHORITY_REFUSED", str(error), record)
        epoch, invocation = identity
        vector = GuardVector((*entries, (record.aggregate, version)), record.aggregate, epoch, invocation)
        reservation = Reservation(*record.reservation)
        payload = {"work": result.work, "action": result.action, "epoch": epoch, "manifest_ref": result.manifest_ref}
        try:
            committed = self.store.commit_guarded(self.profile, target, pinned[target], vector, (reservation,),
                                                  _encode(state, raw), result.effect_id, payload)
        except VersionConflict as error:
            ended = self._end(version, record, EndCause.STALE_VECTOR, now, {"conflict": str(error)})
            return Refused("STALE_VECTOR", str(error), ended)
        except ReservationRejected as error:
            return Refused("FENCE_REFUSED", str(error), record)
        delivery = self._deliver(result.effect_id, reservation,
                                 replace(vector, versions=tuple((a, committed if a == target else v) for a, v in vector.versions)))
        record = replace(record, transitions=record.transitions + 1, admitted_total=record.admitted_total + 1)
        event = {"admitted": result.effect_id, "action": "ADMIT", "work": result.work, "transition": result.action,
                 "at": now, "delivery": delivery}
        cause = EndCause.TERMINAL_OUTCOME if state.stage is LifecycleStage.DONE else evaluate_tenure(record, self.policy, now)
        if cause is not None:
            record = self._end(version, record, cause, now, event)
            return Admitted(record, self._load(record.objective)[0], delivery)
        return Admitted(record, self._save(version, record, event), delivery)

    def _deliver(self, effect_id: str, reservation: Reservation, vector: GuardVector) -> str:
        """Local durable journal delivery; an interrupted delivery stays UNKNOWN and keeps its reservation."""
        try:
            self.store.claim_guarded(self.profile, effect_id, (reservation,), vector)
            receipt = self.store.consume_guarded(self.profile, effect_id, (reservation,), vector)
            self.store.confirm_guarded(self.profile, effect_id, (reservation,), receipt)
        except (ReservationRejected, StoreUnavailable):
            return "UNKNOWN"
        return "CONFIRMED"
