"""Worker-provider boundary used by the offline test double."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired


@dataclass(frozen=True)
class WorkerInvocation:
    work_identity: str
    correlation_id: str


@dataclass(frozen=True)
class WorkerOutcome:
    kind: str
    candidate: CandidateRef | None = None
    escalation: HumanDecisionRequired | None = None

    @classmethod
    def success(cls, candidate: CandidateRef) -> "WorkerOutcome":
        return cls("success", candidate)

    @classmethod
    def authority_block(cls, escalation: HumanDecisionRequired) -> "WorkerOutcome":
        return cls("authority-block", escalation=escalation)


class WorkerProvider(Protocol):
    def start(self, invocation: WorkerInvocation, context: BiuContract, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome: ...
    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None: ...
    def cancel(self, invocation_id: str, reason: str) -> object: ...
