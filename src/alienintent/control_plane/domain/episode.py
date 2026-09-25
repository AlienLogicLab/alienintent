"""Bounded coordinator tenure (SF-REQ-053): pure policy, usage validity and contradiction admission.

Times are integer UTC microseconds on the episode's tenure clock (persisted UTC anchor plus
in-process monotonic progress); reaching any limit ends tenure and nothing renews it silently.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
import json
import math
from typing import Mapping

SECOND = 1_000_000
EPISODE_PREFIX = "episode:"
DEFAULT_THRESHOLD = 0.8


class UsageBinding(StrEnum):
    UNBOUND = "UNBOUND"
    BOUND = "BOUND"


class EpisodeState(StrEnum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class EndCause(StrEnum):
    AGE_LIMIT = "AGE_LIMIT"
    TRANSITION_LIMIT = "TRANSITION_LIMIT"
    BLOCKED_LIMIT = "BLOCKED_LIMIT"
    CONTRADICTION = "CONTRADICTION"
    STALE_VECTOR = "STALE_VECTOR"
    CONTEXT_USAGE_LIMIT = "CONTEXT_USAGE_LIMIT"
    CONTEXT_USAGE_UNAVAILABLE = "CONTEXT_USAGE_UNAVAILABLE"
    CONTEXT_USAGE_INVALID = "CONTEXT_USAGE_INVALID"
    CONTEXT_EXHAUSTED = "CONTEXT_EXHAUSTED"
    TERMINAL_OUTCOME = "TERMINAL_OUTCOME"
    OBJECTIVE_CHANGE = "OBJECTIVE_CHANGE"
    AUTHORITY_CHANGE = "AUTHORITY_CHANGE"
    PROVIDER_CHANGE = "PROVIDER_CHANGE"
    MODEL_CHANGE = "MODEL_CHANGE"
    EXPLICIT_REQUEST = "EXPLICIT_REQUEST"


# Identity changes observed against the value bound at begin (U-5, U-6).
CHANGE_CAUSES = {"objective": EndCause.OBJECTIVE_CHANGE, "authority": EndCause.AUTHORITY_CHANGE,
                 "provider": EndCause.PROVIDER_CHANGE, "model": EndCause.MODEL_CHANGE}
# Durable events that end tenure immediately.
SIGNAL_CAUSES = {"terminal": EndCause.TERMINAL_OUTCOME, "context_exhausted": EndCause.CONTEXT_EXHAUSTED}


class HoldReason(StrEnum):
    CLOCK_REGRESSION = "CLOCK_REGRESSION"
    NO_EPISODE = "NO_EPISODE"
    EPISODE_ACTIVE = "EPISODE_ACTIVE"
    EPISODE_CONFLICT = "EPISODE_CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    ONE_BIU = "ONE_BIU"
    CONTEXT_UNAVAILABLE = "CONTEXT_UNAVAILABLE"
    SOURCE_UNCHECKABLE = "SOURCE_UNCHECKABLE"
    RESERVATION_RETAINED = "RESERVATION_RETAINED"
    STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
    INVALID_RECORD = "INVALID_RECORD"


class EpisodeHold(Exception):
    """A typed refusal to proceed; nothing was admitted or ended."""

    def __init__(self, reason: HoldReason, detail: str = "") -> None:
        self.reason, self.detail = reason, detail
        super().__init__(f"{reason}: {detail}".rstrip(": "))


class InvalidPolicy(ValueError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def digest(value: object) -> str:
    return "sha256:" + sha256(canonical(value)).hexdigest()


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


@dataclass(frozen=True)
class TenurePolicy:
    """Versioned composition policy; proposed configurable defaults, not authority or budget."""
    max_age_s: int = 3600
    max_transitions: int = 32
    max_blocked_s: int = 300
    max_accepted_contradictions: int = 1
    usage: UsageBinding = UsageBinding.UNBOUND
    threshold: float | None = None

    def __post_init__(self) -> None:
        if not all(_positive_int(v) for v in (self.max_age_s, self.max_transitions, self.max_blocked_s,
                                              self.max_accepted_contradictions)):
            raise InvalidPolicy("limits must be positive integers")
        try:
            object.__setattr__(self, "usage", UsageBinding(self.usage))
        except ValueError as error:
            raise InvalidPolicy("unknown usage binding") from error
        if self.usage is UsageBinding.UNBOUND:
            if self.threshold is not None:
                raise InvalidPolicy("UNBOUND usage has no numeric threshold")
            return
        threshold = DEFAULT_THRESHOLD if self.threshold is None else self.threshold
        if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 < threshold <= 1:
            raise InvalidPolicy("BOUND threshold must be finite in (0, 1]")
        object.__setattr__(self, "threshold", float(threshold))

    def document(self) -> dict[str, object]:
        return {**asdict(self), "usage": str(self.usage)}

    def digest(self) -> str:
        return digest(self.document())


@dataclass(frozen=True)
class Usage:
    invocation: str
    check_id: str
    used: float
    limit: float


@dataclass(frozen=True)
class Unavailable:
    reason: str


@dataclass(frozen=True)
class UsageVerdict:
    cause: EndCause | None
    detail: str
    ratio: float | None


def _finite(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_usage(policy: TenurePolicy, observation: object, *, invocation: str, check_id: str) -> UsageVerdict:
    """UNBOUND is recorded as such, never as zero; BOUND needs a valid same-invocation current-check sample."""
    if policy.usage is UsageBinding.UNBOUND:
        return UsageVerdict(None, "UNBOUND", None)
    if observation is None or isinstance(observation, Unavailable):
        return UsageVerdict(EndCause.CONTEXT_USAGE_UNAVAILABLE, "unavailable", None)
    if not isinstance(observation, Usage):
        return UsageVerdict(EndCause.CONTEXT_USAGE_INVALID, "malformed", None)
    if observation.invocation != invocation:
        return UsageVerdict(EndCause.CONTEXT_USAGE_INVALID, "wrong-invocation", None)
    if observation.check_id != check_id:
        return UsageVerdict(EndCause.CONTEXT_USAGE_UNAVAILABLE, "prior-check", None)
    if not _finite(observation.used) or observation.used < 0:
        return UsageVerdict(EndCause.CONTEXT_USAGE_INVALID, "invalid-used", None)
    if not _finite(observation.limit) or observation.limit <= 0:
        return UsageVerdict(EndCause.CONTEXT_USAGE_INVALID, "invalid-limit", None)
    ratio = observation.used / observation.limit
    if ratio >= policy.threshold:
        return UsageVerdict(EndCause.CONTEXT_USAGE_LIMIT, "threshold-reached", ratio)
    return UsageVerdict(None, "below-threshold", ratio)


@dataclass(frozen=True)
class OperatorGrant:
    """An authorized episode operator for one objective (the C1 ResolverGrant precedent)."""
    actor: str
    authority: str
    objective: str


def authorized(grants: tuple[OperatorGrant, ...], actor: str, objective: str, authority: str) -> OperatorGrant | None:
    """A grant counts only under the episode's own authority."""
    return next((g for g in grants if (g.actor, g.objective, g.authority) == (actor, objective, authority)), None)


@dataclass(frozen=True)
class ContradictionJudgment:
    actor: str
    objective: str
    epoch: int
    vector_digest: str
    conflicting_refs: tuple[str, ...]
    rationale: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AcceptedContradiction:
    judgment: ContradictionJudgment
    authority: str
    digest: str


@dataclass(frozen=True)
class InvalidJudgment:
    reason: str


def admit_contradiction(judgment: ContradictionJudgment, *, objective: str, epoch: int, vector_digest: str,
                        authority: str, grants: tuple[OperatorGrant, ...],
                        resolvable: frozenset[str]) -> AcceptedContradiction | InvalidJudgment:
    """Admission only: semantic truth of the contradiction stays operator judgment."""
    grant = authorized(grants, judgment.actor, objective, authority)
    if grant is None:
        return InvalidJudgment("UNAUTHORIZED")
    if judgment.objective != objective:
        return InvalidJudgment("WRONG_EPISODE")
    if judgment.epoch != epoch:
        return InvalidJudgment("STALE_EPOCH")
    if judgment.vector_digest != vector_digest:
        return InvalidJudgment("STALE_VECTOR")
    if not judgment.conflicting_refs:
        return InvalidJudgment("MISSING_REFS")
    if any(ref not in resolvable for ref in judgment.conflicting_refs):
        return InvalidJudgment("UNRESOLVABLE_REF")
    if not isinstance(judgment.rationale, str) or not judgment.rationale.strip():
        return InvalidJudgment("EMPTY_RATIONALE")
    return AcceptedContradiction(judgment, grant.authority, digest(asdict(judgment)))


@dataclass(frozen=True)
class EpisodeRecord:
    objective: str
    epoch: int
    invocation: str
    state: EpisodeState
    cause: EndCause | None
    began_us: int
    deadline_us: int
    last_check_us: int
    check_seq: int
    transitions: int
    blocked_since_us: int | None
    accepted_contradictions: int
    provider: str
    model: str
    authority: str
    objective_revision: str
    manifest_ref: str
    context_digest: str
    reservation: tuple[str, str, str, int] | None
    usage_binding: UsageBinding
    policy_digest: str
    admitted_total: int
    epochs: int

    @property
    def aggregate(self) -> str:
        return EPISODE_PREFIX + self.objective

    def document(self) -> dict[str, object]:
        body = asdict(self)
        body.update(state=str(self.state), cause=None if self.cause is None else str(self.cause),
                    usage_binding=str(self.usage_binding),
                    reservation=None if self.reservation is None else list(self.reservation))
        return body

    @classmethod
    def from_document(cls, body: Mapping[str, object]) -> EpisodeRecord:
        values = dict(body)
        values.update(state=EpisodeState(values["state"]),
                      cause=None if values["cause"] is None else EndCause(values["cause"]),
                      usage_binding=UsageBinding(values["usage_binding"]),
                      reservation=None if values["reservation"] is None else tuple(values["reservation"]))
        return cls(**values)


def blocked(document: Mapping[str, object], objective: str) -> bool:
    """U-3: the objective's own item is in blocked_set and has no authorized next action."""
    in_blocked = any(item.get("work") == objective for item in document.get("blocked_set", ()))
    has_action = any(item.get("work") == objective for item in document.get("authorized_next_action_set", ()))
    return in_blocked and not has_action


def next_blocked_since(record: EpisodeRecord, is_blocked: bool, now_us: int) -> int | None:
    """An unblock resets only the blocked interval; no other counter is touched."""
    if not is_blocked:
        return None
    return now_us if record.blocked_since_us is None else record.blocked_since_us


def evaluate_tenure(record: EpisodeRecord, policy: TenurePolicy, now_us: int) -> EndCause | None:
    """Reaching (>=) any numeric limit ends tenure (U-2)."""
    if now_us - record.began_us >= policy.max_age_s * SECOND:
        return EndCause.AGE_LIMIT
    if record.transitions >= policy.max_transitions:
        return EndCause.TRANSITION_LIMIT
    if record.blocked_since_us is not None and now_us - record.blocked_since_us >= policy.max_blocked_s * SECOND:
        return EndCause.BLOCKED_LIMIT
    if record.accepted_contradictions >= policy.max_accepted_contradictions:
        return EndCause.CONTRADICTION
    return None
