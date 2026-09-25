"""SF-REQ-056 known-active liveness reconciliation over the fenced local lane.

The reconciler scans only already-known active lifecycle records; it never
discovers backlog work, toggles a status, allocates a generation or adds retry
entitlement. Original delivery and recovery share one admission entrypoint and
one canonical effect key, so the durable identity fence decides which one acts.
Every explicit call uses an injected clock; nothing here runs a thread or host.
"""
from collections.abc import Callable
from dataclasses import dataclass, replace

from alienintent.execution_coordination.application.guarded_effect_execution import GuardedEffectExecutor
from alienintent.execution_coordination.domain.liveness import (
    CLOSURE, VERIFIER, Decision, EvidenceHold, ExpectedEffect, Gap, KnownActive, LivenessHold, LivenessPolicy,
    NoAction, Suppressed, active_aggregate, expected_effects, inspect, lane_aggregate, latest_outcome,
)
from alienintent.execution_coordination.ports.fenced_store import EffectConfirmation, FencedOperationalStore, GuardVector
from alienintent.execution_coordination.ports.liveness import (
    EffectObservation, JudgmentAttention, MonitorHealthView, Unavailable,
)
from alienintent.execution_coordination.ports.operational_store import (
    Reservation, ReservationRejected, SchemaIncompatible, StoreUnavailable, VersionConflict,
)
from alienintent.execution_coordination.ports.scan_progress import ScanOutcome, ScanProgress

LANE_SCOPE = "liveness-lane"
BOUND_CLAIMED = "G_PLUS_I_CLAIMED"


@dataclass(frozen=True)
class Intent:
    effect_key: str
    reservations: tuple[Reservation, ...]
    vector: GuardVector


@dataclass(frozen=True)
class Admitted:
    effect_key: str
    receipt: str
    source: str


@dataclass(frozen=True)
class Refused:
    effect_key: str
    reason: str


@dataclass(frozen=True)
class Held:
    effect_key: str
    reason: str


@dataclass(frozen=True)
class LivenessEvent:
    kind: str
    biu: str
    effect_key: str | None
    reason: str
    attention: str | None = None


@dataclass(frozen=True)
class ScanReport:
    at: int
    outcome: str
    events: tuple[LivenessEvent, ...]
    policy_digest: str
    bound_claim: str


class CanonicalEffectAdmission:
    """The one admission entrypoint for original delivery and liveness recovery.

    Authorized gap -> reserve -> re-read evidence/admission -> durable intent ->
    fenced dispatch -> receipt/readback. The local consumer is the store's
    durable guarded journal; no remote provider is bound (park, never relax).
    """

    def __init__(self, store: FencedOperationalStore, *, profile: str, clock: Callable[[], object]) -> None:
        self.store, self.profile, self.clock = store, profile, clock
        self.executor = GuardedEffectExecutor(store)

    def _authority(self, name: str) -> tuple[int, dict[str, object]] | None:
        version, body = self.store.read_state(self.profile, name)
        if (not body or body.get("schema_version") != 1 or body.get("active") is not True
                or type(body.get("epoch")) is not int or not isinstance(body.get("invocation"), str)):
            return None
        return version, body

    def intend(self, active: KnownActive, revision: int, expected: ExpectedEffect, source: str) -> Intent | Refused | Held:
        key = expected.effect_key
        try:
            authority = self._authority(active.authority)
            if authority is None:
                return Held(key, "AUTHORITY_UNAVAILABLE")
            version, body = self.store.read_state(self.profile, active_aggregate(active.biu))
            if not body:
                return Held(key, "KNOWN_ACTIVE_UNAVAILABLE")
            if version != revision or KnownActive.from_document(body) != active:
                return Refused(key, "STALE_SNAPSHOT")
            if expected not in expected_effects(self.profile, active):
                return Refused(key, "NOT_EXPECTED")
            if not active.budget_admitted:
                return Held(key, "BUDGET_UNAVAILABLE")
            if expected.role_key.split(":")[0] in (VERIFIER, CLOSURE) and active.candidate is None:
                return Held(key, "CUSTODY_UNAVAILABLE")
            now = self.clock()
            if type(now) is not int or now < 0:
                return Held(key, "CLOCK_INVALID")
            authority_version, grant = authority
            invocation = str(grant["invocation"])
            try:
                reservations = self.store.acquire_many(self.profile, ((LANE_SCOPE, key),), invocation)
            except ReservationRejected:
                return Refused(key, "RESERVED")
            lane = lane_aggregate(key)
            try:
                lane_version, _ = self.store.read_state(self.profile, lane)
            except (StoreUnavailable, SchemaIncompatible):
                self._release(reservations)
                raise
            vector = GuardVector(((active_aggregate(active.biu), revision), (active.authority, authority_version),
                                  (lane, lane_version)), active.authority, int(grant["epoch"]), invocation)
            state = {"schema_version": 1, "effect_key": key, "biu": active.biu, "generation": active.generation,
                     "role_key": expected.role_key, "active_revision": revision, "authority": active.authority,
                     "authority_version": authority_version, "epoch": vector.epoch, "invocation": invocation,
                     "intended_at": now, "source": source}
            payload = {"kind": "liveness-canonical-effect", "effect_key": key, "biu": active.biu,
                       "generation": active.generation, "role_key": expected.role_key, "candidate": active.candidate}
            try:
                post = self.store.commit_guarded(self.profile, lane, lane_version, vector, reservations, state, key, payload)
            except (ReservationRejected, VersionConflict) as error:
                self._release(reservations)
                used = "effect identity already used" in str(error)
                return Refused(key, "EFFECT_IDENTITY_USED" if used else "ADMISSION_REFUSED:" + str(error))
            except (StoreUnavailable, SchemaIncompatible):
                # The transaction rolled back, so no intent exists; do not strand the reservation.
                self._release(reservations)
                raise
        except (StoreUnavailable, SchemaIncompatible, LivenessHold) as error:
            return Held(key, "ADMISSION_EVIDENCE_UNAVAILABLE:" + type(error).__name__)
        return Intent(key, reservations, replace(vector, versions=tuple(
            (k, post if k == lane else v) for k, v in vector.versions)))

    def deliver(self, intent: Intent, source: str) -> Admitted | Held:
        try:
            result = self.executor.execute(self.profile, intent.effect_key, intent.reservations, intent.vector)
        except (ReservationRejected, VersionConflict, StoreUnavailable, SchemaIncompatible) as error:
            # The intent stays durable with its reservation; startup/readback decides.
            return Held(intent.effect_key, "DELIVERY_REFUSED:" + str(error))
        return self._settle(intent.effect_key, intent.reservations, result, source)

    def admit(self, active: KnownActive, revision: int, expected: ExpectedEffect, source: str) -> Admitted | Refused | Held:
        intent = self.intend(active, revision, expected, source)
        return intent if not isinstance(intent, Intent) else self.deliver(intent, source)

    def resume(self, key: str) -> Admitted | Held:
        """Reopen a durable intent: pending unsent executes by canonical claim; claimed reads back only."""
        try:
            version, lane = self.store.read_state(self.profile, lane_aggregate(key))
            if not lane:
                return Held(key, "INTENT_UNAVAILABLE")
            reservations = tuple(r for r in self.store.recovery_reservations(self.profile)
                                 if (r.scope, r.key) == (LANE_SCOPE, key))
            vector = GuardVector(((active_aggregate(str(lane["biu"])), int(lane["active_revision"])),
                                  (str(lane["authority"]), int(lane["authority_version"])),
                                  (lane_aggregate(key), version)), str(lane["authority"]), int(lane["epoch"]),
                                 str(lane["invocation"]))
            pending = {e.identity for e in self.store.pending_effects(self.profile)}
            unknown = {e.identity for e in self.store.unresolved_effects(self.profile)}
            if key in pending:
                result = self.executor.execute(self.profile, key, reservations, vector)
            elif key in unknown:
                result = self.executor.reconcile(self.profile, key, reservations)
            else:
                receipt = self.store.readback_guarded(self.profile, key)
                if receipt is None:
                    return Held(key, "EFFECT_STATE_INCONSISTENT")
                self._release(reservations)
                return Admitted(key, receipt.digest, "readback")
        except (ReservationRejected, VersionConflict, StoreUnavailable, SchemaIncompatible, KeyError, TypeError, ValueError) as error:
            return Held(key, "RESUME_REFUSED:" + str(error))
        return self._settle(key, reservations, result, "readback")

    def _settle(self, key: str, reservations: tuple[Reservation, ...], result: object, source: str) -> Admitted | Held:
        if not isinstance(result, EffectConfirmation):
            return Held(key, "READBACK_PENDING")
        self._release(reservations)
        return Admitted(key, result.receipt.digest, source)

    def _release(self, reservations: tuple[Reservation, ...]) -> bool:
        """Best effort: a reservation left behind is reopened by `release_orphans` at startup."""
        released = True
        for r in reservations:
            try:
                self.store.release(self.profile, r.scope, r.key, r.owner, r.fence)
            except (ReservationRejected, StoreUnavailable, SchemaIncompatible):
                released = False
        return released

    def release_orphans(self) -> tuple[str, ...]:
        """Release lane reservations left by a crash before any durable intent existed.

        A live contender that still holds such a reservation is fenced: its
        guarded intent is then refused as stale.
        """
        orphans = []
        for r in self.store.recovery_reservations(self.profile):
            if r.scope == LANE_SCOPE and not self.store.read_state(self.profile, lane_aggregate(r.key))[1]:
                if self._release((r,)):
                    orphans.append(r.key)
        return tuple(orphans)


class LivenessReconciler:
    def __init__(self, store: FencedOperationalStore, observations: EffectObservation, attention: JudgmentAttention,
                 health: MonitorHealthView, admission: CanonicalEffectAdmission, *, profile: str,
                 policy: LivenessPolicy | None, clock: Callable[[], object], progress: ScanProgress | None = None) -> None:
        if policy is None:
            raise LivenessHold("POLICY_MISSING")
        if not isinstance(policy, LivenessPolicy):
            raise LivenessHold("POLICY_INVALID")
        policy.validate()
        self.store, self.observations, self.attention, self.health = store, observations, attention, health
        self.admission, self.profile, self.policy, self.clock, self.progress = admission, profile, policy, clock, progress
        self.started, self._unrecorded = False, False

    def start(self) -> tuple[Admitted | Held, ...]:
        """Persist the policy digest, then reopen every durable intent without a new launch."""
        name = "liveness-policy:" + self.profile
        version, body = self.store.read_state(self.profile, name)
        document = {"schema_version": 1, "policy": self.policy.document(), "policy_digest": self.policy.digest()}
        if body != document:
            self.store.commit(self.profile, name, version, document)
        self.admission.release_orphans()
        pending = {e.identity for e in (*self.store.pending_effects(self.profile), *self.store.unresolved_effects(self.profile))}
        retained = {r.key for r in self.store.recovery_reservations(self.profile) if r.scope == LANE_SCOPE}
        reopened = tuple(self.admission.resume(str(lane["effect_key"]))
                         for _, _, lane in self.store.list_states(self.profile, lane_aggregate(""))
                         if lane.get("effect_key") in pending | retained)
        self.started = True
        return reopened

    def known_active(self) -> tuple[tuple[int, KnownActive], ...]:
        return tuple((version, KnownActive.from_document(body))
                     for _, version, body in self.store.list_states(self.profile, active_aggregate("")))

    def inspect(self, active: KnownActive) -> Decision:
        """Read-only classification of one known-active record."""
        snapshot = self.observations.observe(active)
        if isinstance(snapshot, Unavailable):
            return EvidenceHold("OBSERVATION_UNAVAILABLE:" + snapshot.reason)
        latest = latest_outcome(active, snapshot)
        resolved, attention = None, None
        if latest is not None and latest.judgment:
            state = self.attention.ensure_judgment(active, latest)
            if isinstance(state, Unavailable):
                return EvidenceHold("ATTENTION_UNAVAILABLE:" + state.reason)
            resolved, attention = state.status == "RESOLVED", state.attention
        decision = inspect(self.profile, active, snapshot, self.clock(), self.policy, resolved)
        return replace(decision, attention=attention) if isinstance(decision, Suppressed) else decision

    def bound_claim(self) -> str:
        try:
            status, reason = self.health.health()
        except Exception as error:  # any health read failure withdraws the claim; it never stops reconciliation
            return "WITHDRAWN:UNVERIFIED:HEALTH_UNREADABLE:" + type(error).__name__
        return BOUND_CLAIMED if status == "HEALTHY" else f"WITHDRAWN:{status}:{reason}"

    def _progress(self, step: Callable[[], object]) -> str | None:
        try:
            step()
        except Exception as error:  # an unhealthy monitor withdraws the claim; reconciliation continues
            return type(error).__name__ + ":" + str(error)
        return None

    def scan(self) -> ScanReport:
        if not self.started:
            raise LivenessHold("NOT_STARTED")
        self._unrecorded = False
        progress = None if self.progress is None else self._progress(self.progress.scan_started)
        now = self.clock()
        events: list[LivenessEvent] = []
        try:
            entries = self.known_active()
        except (StoreUnavailable, SchemaIncompatible, LivenessHold) as error:
            return self._finish(now, "FAILED", events, "known-active store unavailable: " + type(error).__name__, progress)
        for revision, active in entries:
            try:
                events.extend(self._reconcile(revision, active))
            except (StoreUnavailable, SchemaIncompatible, ReservationRejected, VersionConflict, LivenessHold) as error:
                event = LivenessEvent("liveness.evidence_hold", active.biu, None, "SCAN_STORE_FAILURE:" + type(error).__name__)
                self._record_hold(active, event)
                events.append(event)
        if self._unrecorded:
            return self._finish(now, "FAILED", events, "a hold could not be recorded durably", progress)
        held = any(e.kind == "liveness.evidence_hold" for e in events)
        return self._finish(now, "EVIDENCE_HOLD" if held else "COMPLETE", events,
                            "evidence hold recorded" if held else None, progress)

    def _finish(self, now: object, outcome: str, events: list[LivenessEvent], error: str | None,
                progress: str | None) -> ScanReport:
        if self.progress is not None and progress is None:
            progress = self._progress(lambda: self.progress.scan_finished(  # type: ignore[union-attr]
                ScanOutcome(outcome, error, len(events))))  # type: ignore[arg-type]
        claim = self.bound_claim() if progress is None else "WITHDRAWN:PROGRESS_UNRECORDED:" + progress
        return ScanReport(now if type(now) is int else -1, outcome, tuple(events), self.policy.digest(), claim)

    def _reconcile(self, revision: int, active: KnownActive) -> list[LivenessEvent]:
        decision = self.inspect(active)
        if isinstance(decision, NoAction):
            return [LivenessEvent("liveness.no_action", active.biu, None, decision.reason)]
        if isinstance(decision, Suppressed):
            return [LivenessEvent("liveness.suppressed", active.biu, None, decision.reason, decision.attention)]
        if isinstance(decision, EvidenceHold):
            events = []
            if decision.reason == "CONFIRMATION_OVERDUE" and decision.effect_key is not None:
                result = self.admission.resume(decision.effect_key)
                if isinstance(result, Admitted):
                    return [LivenessEvent("liveness.readback_confirmed", active.biu, result.effect_key, result.source)]
                events.append(LivenessEvent("liveness.evidence_hold", active.biu, result.effect_key, result.reason))
            else:
                events.append(LivenessEvent("liveness.evidence_hold", active.biu, decision.effect_key, decision.reason))
            self._record_hold(active, events[-1])
            return events
        assert isinstance(decision, Gap)
        events = [LivenessEvent("liveness.gap", active.biu, e.effect_key, "MISSING:" + e.role_key) for e in decision.missing]
        for effect in decision.missing:
            result = self.admission.admit(active, revision, effect, "liveness-scan")
            if isinstance(result, Admitted):
                events += [LivenessEvent("liveness.recovery_intent", active.biu, effect.effect_key, effect.role_key),
                           LivenessEvent("liveness.readback_confirmed", active.biu, effect.effect_key, result.receipt)]
            elif isinstance(result, Refused):
                events.append(LivenessEvent("liveness.refused", active.biu, effect.effect_key, result.reason))
            else:
                events.append(LivenessEvent("liveness.evidence_hold", active.biu, effect.effect_key, result.reason))
                self._record_hold(active, events[-1])
        return events

    def _record_hold(self, active: KnownActive, event: LivenessEvent) -> None:
        """A durable hold record, never a speculative launch (AC-06)."""
        name = "liveness-hold:" + active.biu
        body = {"schema_version": 1, "biu": active.biu, "generation": active.generation,
                "effect_key": event.effect_key, "reason": event.reason, "policy_digest": self.policy.digest()}
        try:
            version, current = self.store.read_state(self.profile, name)
            if {k: v for k, v in current.items() if k != "at"} != body:
                self.store.commit(self.profile, name, version, body | {"at": self.clock()})
        except (StoreUnavailable, SchemaIncompatible, VersionConflict, ReservationRejected):
            # Never silent: an unrecorded hold makes the scan FAILED, not quiet success.
            self._unrecorded = True
