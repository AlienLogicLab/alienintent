"""Neutral SF-REQ-056 observation, judgment-attention and monitor-health ports.

Unavailable data is a typed value, never an empty set. Composition binds the
control-plane attention and monitor services behind these ports.
"""
from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.liveness import CorrelatedOutcome, KnownActive, ObservationSnapshot


@dataclass(frozen=True)
class Unavailable:
    reason: str


@dataclass(frozen=True)
class JudgmentState:
    attention: str
    status: str


class EffectObservation(Protocol):
    def observe(self, active: KnownActive) -> ObservationSnapshot | Unavailable: ...


class JudgmentAttention(Protocol):
    def ensure_judgment(self, active: KnownActive, outcome: CorrelatedOutcome) -> JudgmentState | Unavailable: ...


class MonitorHealthView(Protocol):
    def health(self) -> tuple[str, str]: ...


class LifecycleJournal(Protocol):
    """Canonical lifecycle/runtime writers the reconciler never holds (no scanner mutation)."""
    def enter(self, active: KnownActive) -> int: ...
    def record_invocation(self, active: KnownActive, invocation: str, running: bool) -> int: ...
    def record_outcome(self, outcome: CorrelatedOutcome) -> int: ...
