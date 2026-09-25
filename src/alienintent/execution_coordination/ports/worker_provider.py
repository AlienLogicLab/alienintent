"""Worker-provider boundary used by the offline test double."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired

PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"


@dataclass(frozen=True)
class WorkerInvocation:
    work_identity: str
    correlation_id: str
    contract_digest: str | None = None
    # K2 role routing: which canonical role this invocation plays and, for a
    # verifier or closure invocation, the exact custodied candidate it acts on.
    role: str = PRODUCER
    candidate: CandidateRef | None = None


@dataclass(frozen=True)
class WorkerOutcome:
    kind: str
    candidate: CandidateRef | None = None
    escalation: HumanDecisionRequired | None = None
    # A verifier's findings and a closure invocation's performed, read-back
    # action receipts; neither has another carrier in this contract.
    findings: tuple[str, ...] = ()
    receipts: tuple[str, ...] = ()

    @classmethod
    def success(cls, candidate: CandidateRef) -> "WorkerOutcome":
        return cls("success", candidate)

    @classmethod
    def authority_block(cls, escalation: HumanDecisionRequired) -> "WorkerOutcome":
        return cls("authority-block", escalation=escalation)

    @classmethod
    def accept(cls, candidate: CandidateRef, findings: tuple[str, ...] = ()) -> "WorkerOutcome":
        return cls("accept", candidate, findings=tuple(findings))

    @classmethod
    def reject(cls, candidate: CandidateRef, findings: tuple[str, ...]) -> "WorkerOutcome":
        return cls("reject", candidate, findings=tuple(findings))

    @classmethod
    def closed(cls, candidate: CandidateRef, receipts: tuple[str, ...]) -> "WorkerOutcome":
        return cls("closed", candidate, receipts=tuple(receipts))


class WorkerProvider(Protocol):
    def start(self, invocation: WorkerInvocation, context: BiuContract, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome: ...
    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None: ...
    def cancel(self, invocation_id: str, reason: str) -> object: ...
