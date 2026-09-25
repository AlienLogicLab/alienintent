"""Store-backed SF-REQ-056 observation of already-known active records only.

Reads the fenced lane/effect/consumer records, correlated invocation and outcome
records for the SAME work and generation, and legacy `launch:` effects for the
same work. It never queries backlog discovery. Any unreadable or malformed
record is `Unavailable`, never an empty set.
"""
from alienintent.execution_coordination.domain.liveness import (
    CorrelatedOutcome, EffectEvidence, KnownActive, LivenessHold, ObservationSnapshot, active_aggregate,
    expected_effects, lane_aggregate,
)
from alienintent.execution_coordination.ports.fenced_store import FencedOperationalStore
from alienintent.execution_coordination.ports.liveness import EffectObservation, LifecycleJournal, Unavailable
from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible, StoreUnavailable

_INVOCATIONS, _OUTCOMES = "liveness-invocation:", "liveness-outcome:"


def _outcome_document(outcome: CorrelatedOutcome) -> dict[str, object]:
    return {"identity": outcome.identity, "biu": outcome.biu, "generation": outcome.generation,
            "role_key": outcome.role_key, "kind": outcome.kind, "sequence": outcome.sequence}


class StoreEffectObservation(EffectObservation):
    def __init__(self, store: FencedOperationalStore, *, profile: str) -> None:
        self.store, self.profile = store, profile

    def observe(self, active: KnownActive) -> ObservationSnapshot | Unavailable:
        try:
            return self._observe(active)
        except (StoreUnavailable, SchemaIncompatible, LivenessHold, KeyError, TypeError, ValueError) as error:
            return Unavailable(type(error).__name__ + ":" + str(error))

    def _observe(self, active: KnownActive) -> ObservationSnapshot | Unavailable:
        pending = {e.identity: e for e in self.store.pending_effects(self.profile)}
        unknown = {e.identity: e for e in self.store.unresolved_effects(self.profile)}
        effects = []
        for expected in expected_effects(self.profile, active):
            _, lane = self.store.read_state(self.profile, lane_aggregate(expected.effect_key))
            if not lane:
                continue
            if lane.get("schema_version") != 1 or lane.get("effect_key") != expected.effect_key:
                return Unavailable("LANE_RECORD_INVALID")
            key = expected.effect_key
            if key in pending:
                status = "PENDING"
            elif key in unknown:
                status = "UNKNOWN"
            elif self.store.readback_guarded(self.profile, key) is not None:
                status = "CONFIRMED"
            else:
                return Unavailable("EFFECT_STATE_INCONSISTENT")
            effects.append((key, EffectEvidence(status, int(lane["intended_at"]))))
        _, invocations = self.store.read_state(self.profile, _INVOCATIONS + active.biu)
        if invocations and invocations.get("schema_version") != 1:
            return Unavailable("INVOCATION_RECORD_INVALID")
        running = tuple(sorted(i for i, record in dict(invocations.get("invocations", {})).items()
                               if record["generation"] == active.generation and record["running"] is True))
        _, outcomes = self.store.read_state(self.profile, _OUTCOMES + active.biu)
        if outcomes and outcomes.get("schema_version") != 1:
            return Unavailable("OUTCOME_RECORD_INVALID")
        correlated = tuple(CorrelatedOutcome(**o) for o in outcomes.get("outcomes", ())
                           if (o["biu"], o["generation"]) == (active.biu, active.generation))
        legacy = [status for status, table in (("UNKNOWN", unknown), ("PENDING", pending))
                  for identity, effect in table.items()
                  if identity.startswith("launch:") and effect.payload.get("work") == active.biu]
        if not legacy:
            # FactoryCoordinator projects every legacy launch onto `factory:<work>`; a settled one
            # has no generation alias here, so it is reported, never ignored.
            _, projection = self.store.read_state(self.profile, "factory:" + active.biu)
            if str(projection.get("correlation", "")).startswith("launch:"):
                legacy = ["UNALIASED"]
        return ObservationSnapshot(running, tuple(effects), correlated, legacy[0] if legacy else None)


class StoreLifecycleJournal(LifecycleJournal):
    """Local stand-in for the canonical transition and runtime/outcome writers."""

    def __init__(self, store: FencedOperationalStore, *, profile: str) -> None:
        self.store, self.profile = store, profile

    def enter(self, active: KnownActive) -> int:
        name = active_aggregate(active.biu)
        version, body = self.store.read_state(self.profile, name)
        document = {"schema_version": 1, **active.document()}
        if body == document:
            return version
        if body and KnownActive.from_document(body).generation >= active.generation:
            raise LivenessHold("GENERATION_NOT_ADVANCED")
        return self.store.commit(self.profile, name, version, document)

    def record_invocation(self, active: KnownActive, invocation: str, running: bool) -> int:
        name = _INVOCATIONS + active.biu
        version, body = self.store.read_state(self.profile, name)
        invocations = dict(body.get("invocations", {}))
        invocations[invocation] = {"generation": active.generation, "running": running}
        return self.store.commit(self.profile, name, version, {"schema_version": 1, "invocations": invocations})

    def record_outcome(self, outcome: CorrelatedOutcome) -> int:
        name = _OUTCOMES + outcome.biu
        version, body = self.store.read_state(self.profile, name)
        existing = list(body.get("outcomes", ()))
        document = _outcome_document(outcome)
        if document in existing:
            return version
        if any(o["identity"] == outcome.identity or o["sequence"] >= outcome.sequence for o in existing):
            raise LivenessHold("OUTCOME_CONFLICT")
        return self.store.commit(self.profile, name, version, {"schema_version": 1, "outcomes": [*existing, document]})
