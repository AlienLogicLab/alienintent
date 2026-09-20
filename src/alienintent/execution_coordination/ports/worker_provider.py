"""Worker-provider boundary used by the offline test double."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
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
    def start(self, invocation: WorkerInvocation, context: BiuContract, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome: ...
    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None: ...
