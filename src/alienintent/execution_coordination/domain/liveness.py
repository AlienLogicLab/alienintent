"""SF-REQ-056 known-active liveness values and the pure inspection rule.

Times are integer UTC microseconds since the Unix epoch, as in C4 monitor
health, so G/I/C boundaries compare exactly. Inspection proposes; it never
authorizes, dispatches, retries or changes a lifecycle stage or generation.
"""
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
import json
import math

# The only stages with an expected canonical actor/effect (design: state changes and identity).
PRODUCER, VERIFIER, CLOSURE = "producer", "verifier", "closure"
EXPECTED_ROLE = {"IMPLEMENT": PRODUCER, "VERIFY": VERIFIER, "ACCEPT": CLOSURE}
# Completed results that need judgment, never a missing actor (AC-04).
JUDGMENT_OUTCOMES = frozenset({"FOUNDER_EXCEPTION", "HUMAN_DECISION_REQUIRED", "AUTHORITY_BLOCK"})
EFFECT_STATUSES = frozenset({"ABSENT", "PENDING", "UNKNOWN", "CONFIRMED"})
JUDGMENT_STATUSES = frozenset({"PENDING", "SEEN", "RESOLVED"})


class LivenessHold(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _duration(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


@dataclass(frozen=True)
class LivenessPolicy:
    """Grace G, scan interval I and confirmation bound C; design defaults 300/60/90 seconds."""
    grace_seconds: int | float = 300
    interval_seconds: int | float = 60
    confirmation_seconds: int | float = 90

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if not all(_duration(v) for v in (self.grace_seconds, self.interval_seconds, self.confirmation_seconds)):
            raise LivenessHold("POLICY_INVALID")

    @staticmethod
    def _micros(seconds: int | float) -> Fraction:
        return Fraction(seconds) * 1_000_000

    @property
    def grace_micros(self) -> Fraction:
        return self._micros(self.grace_seconds)

    @property
    def interval_micros(self) -> Fraction:
        return self._micros(self.interval_seconds)

    @property
    def confirmation_micros(self) -> Fraction:
        return self._micros(self.confirmation_seconds)

    def document(self) -> dict[str, object]:
        return {"grace_seconds": self.grace_seconds, "interval_seconds": self.interval_seconds,
                "confirmation_seconds": self.confirmation_seconds}

    def digest(self) -> str:
        return "sha256:" + sha256(_canonical(self.document())).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _text(*values: object) -> bool:
    return all(isinstance(v, str) and v.strip() for v in values)


@dataclass(frozen=True)
class KnownActive:
    """A durable nonterminal lifecycle entry written by the canonical transition, never by a scan."""
    biu: str
    repository: str
    contract_digest: str
    stage: str
    generation: int
    entered_at: int
    authority: str
    budget_admitted: bool
    candidate: str | None = None
    closure_actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (not _text(self.biu, self.repository, self.contract_digest, self.stage, self.authority)
                or type(self.generation) is not int or self.generation < 1
                or type(self.entered_at) is not int or self.entered_at < 0
                or type(self.budget_admitted) is not bool
                or self.candidate is not None and not _text(self.candidate)
                or not isinstance(self.closure_actions, tuple) or not all(_text(a) for a in self.closure_actions)
                or len(set(self.closure_actions)) != len(self.closure_actions)):
            raise LivenessHold("INVALID_KNOWN_ACTIVE")

    def document(self) -> dict[str, object]:
        return {"biu": self.biu, "repository": self.repository, "contract_digest": self.contract_digest,
                "stage": self.stage, "generation": self.generation, "entered_at": self.entered_at,
                "authority": self.authority, "budget_admitted": self.budget_admitted,
                "candidate": self.candidate, "closure_actions": list(self.closure_actions)}

    @classmethod
    def from_document(cls, body: dict[str, object]) -> "KnownActive":
        try:
            return cls(body["biu"], body["repository"], body["contract_digest"], body["stage"],
                       body["generation"], body["entered_at"], body["authority"], body["budget_admitted"],
                       body["candidate"], tuple(body["closure_actions"]))
        except (KeyError, TypeError) as error:
            raise LivenessHold("INVALID_KNOWN_ACTIVE") from error


def active_aggregate(biu: str) -> str:
    return "liveness-active:" + biu


def lane_aggregate(effect: str) -> str:
    return "liveness-lane:" + effect


@dataclass(frozen=True)
class ExpectedEffect:
    role_key: str
    effect_key: str


def effect_key(profile: str, active: KnownActive, role_key: str) -> str:
    """hash(profile, repository, BIU, contract digest, lifecycle-entry generation, role/closure key).

    Original delivery and every scan derive this same key; delivery IDs and scan
    times never enter it.
    """
    body = [profile, active.repository, active.biu, active.contract_digest, active.generation, role_key]
    return "liveness-effect:" + sha256(_canonical(body)).hexdigest()


def expected_effects(profile: str, active: KnownActive) -> tuple[ExpectedEffect, ...]:
    role = EXPECTED_ROLE.get(active.stage)
    if role is None:
        return ()
    keys = tuple(f"{CLOSURE}:{a}" for a in active.closure_actions) if role == CLOSURE else (role,)
    return tuple(ExpectedEffect(k, effect_key(profile, active, k)) for k in keys)


@dataclass(frozen=True)
class EffectEvidence:
    status: str
    intended_at: int | None = None

    def __post_init__(self) -> None:
        if (self.status not in EFFECT_STATUSES
                or (self.status == "ABSENT") != (self.intended_at is None)
                or self.intended_at is not None and type(self.intended_at) is not int):
            raise LivenessHold("INVALID_EFFECT_EVIDENCE")


@dataclass(frozen=True)
class CorrelatedOutcome:
    """A durable outcome for the SAME work and lifecycle-entry generation; `sequence` orders them."""
    identity: str
    biu: str
    generation: int
    role_key: str
    kind: str
    sequence: int

    def __post_init__(self) -> None:
        if (not _text(self.identity, self.biu, self.role_key, self.kind)
                or type(self.generation) is not int or type(self.sequence) is not int):
            raise LivenessHold("INVALID_OUTCOME")

    @property
    def judgment(self) -> bool:
        return self.kind in JUDGMENT_OUTCOMES


@dataclass(frozen=True)
class ObservationSnapshot:
    active_invocations: tuple[str, ...]
    effects: tuple[tuple[str, EffectEvidence], ...]
    outcomes: tuple[CorrelatedOutcome, ...]
    legacy_effect: str | None = None

    def effect(self, key: str) -> EffectEvidence:
        return dict(self.effects).get(key, EffectEvidence("ABSENT"))


@dataclass(frozen=True)
class NoAction:
    reason: str


@dataclass(frozen=True)
class Gap:
    active: KnownActive
    missing: tuple[ExpectedEffect, ...]
    age: int


@dataclass(frozen=True)
class Suppressed:
    reason: str
    outcome: CorrelatedOutcome
    attention: str | None = None


@dataclass(frozen=True)
class EvidenceHold:
    reason: str
    effect_key: str | None = None


Decision = NoAction | Gap | Suppressed | EvidenceHold


def latest_outcome(active: KnownActive, snapshot: ObservationSnapshot) -> CorrelatedOutcome | None:
    same = [o for o in snapshot.outcomes if (o.biu, o.generation) == (active.biu, active.generation)]
    return max(same, key=lambda o: o.sequence, default=None)


def inspect(profile: str, active: KnownActive, snapshot: ObservationSnapshot, now: object,
            policy: LivenessPolicy, judgment_resolved: bool | None) -> Decision:
    """Ordered rule. `judgment_resolved` is the matching attention state of the latest outcome."""
    if type(now) is not int or now < 0:
        return EvidenceHold("CLOCK_INVALID")
    expected = expected_effects(profile, active)
    if not expected:
        return NoAction("ACCEPT_NO_OUTSTANDING_CLOSURE" if active.stage == "ACCEPT" else "NO_EXPECTED_EFFECT")
    latest = latest_outcome(active, snapshot)
    if latest is not None and latest.judgment and judgment_resolved is not True:
        # Regardless of age: completed judgment is suppression, not a missing actor.
        return Suppressed("JUDGMENT_UNRESOLVED", latest)
    if snapshot.legacy_effect == "UNKNOWN":
        return EvidenceHold("LEGACY_EFFECT_UNKNOWN")
    if snapshot.legacy_effect == "PENDING":
        return NoAction("LEGACY_EFFECT_PENDING")
    if snapshot.active_invocations:
        return NoAction("ACTIVE_INVOCATION")
    if now < active.entered_at:
        return EvidenceHold("CLOCK_REGRESSION")
    age = now - active.entered_at
    if age < policy.grace_micros:
        return NoAction("WITHIN_GRACE")
    completed = {o.role_key for o in snapshot.outcomes
                 if (o.biu, o.generation) == (active.biu, active.generation) and not o.judgment}
    if latest is not None and latest.judgment and judgment_resolved is True:
        # A resolution permits reinspection only; its role stays completed for this
        # generation, and a relaunch needs a canonical new-generation transition.
        completed.add(latest.role_key)
    missing, pending = [], False
    for effect in expected:
        evidence = snapshot.effect(effect.effect_key)
        if evidence.status == "CONFIRMED" or effect.role_key in completed:
            continue
        if evidence.status in ("PENDING", "UNKNOWN"):
            assert evidence.intended_at is not None
            if now - evidence.intended_at >= policy.confirmation_micros:
                # Past C without readback: hold for readback, never fabricate absence.
                return EvidenceHold("CONFIRMATION_OVERDUE", effect.effect_key)
            pending = True
            continue
        missing.append(effect)
    if pending:
        return NoAction("PENDING_EFFECT")
    if not missing:
        return NoAction("COMPLETED_AWAITING_PROJECTION")
    return Gap(active, tuple(missing), age)
