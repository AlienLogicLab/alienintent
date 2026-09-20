"""Provider-neutral worker invocation boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.custody import CandidateRef


@dataclass(frozen=True)
class WorkerInvocation:
    work_identity: str
    correlation_id: str


@dataclass(frozen=True)
class WorkerOutcome:
    kind: str
    candidate: CandidateRef | None = None

    @classmethod
    def success(cls, candidate: CandidateRef) -> "WorkerOutcome":
        return cls("success", candidate)


class WorkerProvider(Protocol):
    def start(self, invocation: WorkerInvocation, context: object, grants: frozenset[str], budget: object) -> WorkerOutcome: ...
    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None: ...
