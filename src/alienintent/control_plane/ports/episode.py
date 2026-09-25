"""Episode control, context-usage, contradiction and context-source boundaries (contract 8)."""
from dataclasses import dataclass
from typing import Mapping, Protocol

from alienintent.control_plane.domain.episode import (
    AcceptedContradiction, ContradictionJudgment, EpisodeRecord, InvalidJudgment, Unavailable, Usage,
)


@dataclass(frozen=True)
class CoordinatorResult:
    """One authority-bearing coordinator command, bound to the context and epoch it was computed from."""
    episode: str
    work: str
    epoch: int
    invocation: str
    manifest_ref: str
    action: str
    expected_version: int
    effect_id: str
    candidate: Mapping[str, object] | None = None
    verdict: str | None = None


@dataclass(frozen=True)
class Admitted:
    record: EpisodeRecord
    version: int
    delivery: str


@dataclass(frozen=True)
class Refused:
    """No authoritative state was written by this result."""
    reason: str
    detail: str
    record: EpisodeRecord | None


@dataclass(frozen=True)
class ContextView:
    manifest_ref: str
    document: Mapping[str, object]
    digest: str


@dataclass(frozen=True)
class ContextUnavailable:
    reason: str
    refs: tuple[str, ...] = ()


class ContextSource(Protocol):
    """A control-plane view of C2 reconstruction; composition supplies the implementation."""
    def pin(self) -> str | ContextUnavailable: ...
    def entries(self, manifest_ref: str) -> tuple[tuple[str, int], ...] | ContextUnavailable: ...
    def reconstruct(self, manifest_ref: str) -> ContextView | ContextUnavailable: ...


class ContextUsageObservation(Protocol):
    def read(self, invocation_id: str, check_id: str) -> Usage | Unavailable: ...


class ContradictionObservation(Protocol):
    def record(self, judgment: ContradictionJudgment) -> AcceptedContradiction | InvalidJudgment: ...


class DeadlineTimer(Protocol):
    """Injected timer; the caller drives `tick` when it fires, independent of any model."""
    def arm(self, objective: str, epoch: int, deadline_us: int) -> None: ...


class EpisodeRepository(Protocol):
    def load(self, objective: str) -> tuple[int, EpisodeRecord | None]: ...
    def save(self, expected_version: int, record: EpisodeRecord, event: Mapping[str, object]) -> int: ...
    def history(self, objective: str) -> tuple[dict[str, object], ...]: ...


class EpisodeControl(Protocol):
    def begin(self, objective: str, *, actor: str, provider: str, model: str, authority: str,
              objective_revision: str) -> EpisodeRecord: ...
    def submit(self, result: CoordinatorResult) -> Admitted | Refused: ...
    def end(self, objective: str, *, epoch: int, actor: str) -> EpisodeRecord: ...
