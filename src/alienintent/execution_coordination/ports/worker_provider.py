"""Worker-provider boundary used by the offline test double."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy
from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired

PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"
# K3: the durable terminal outcome retained against an invocation whose
# ownership ended conclusively without any result of its own. It is not a
# verdict, candidate or failure: the stage is unchanged and its role may be
# re-dispatched once under the composed replacement allowance.
MISSING_TERMINAL_RESULT = "missing-terminal-result"
NO_CHANGE = "no-change"
# A plan-derived PRODUCER candidate whose actual diff leaves its assessed scope or touches a protected path: nothing
# was published, and the coordinator reworks it exactly like NO_CHANGE, using no VERIFIER attempt.
SCOPE_VIOLATION = "scope-violation"
# VERIFIER outcomes that carry no engineering judgment: the session ended without a valid verdict (its process failed
# or timed out, or it left no verdict, a malformed one or one for another revision), or the feature-regression
# receipt is absent or invalid (`feature-regressions-missing`: the REGRESSION-GATE produced no whole-suite result, or,
# in a profile without a gate, the receipt beside the verdict): the gate alone owns whole-suite execution, so a missing
# result is never compensated by a session running the suite. The coordinator retries the VERIFIER on the same candidate; only
# a valid REJECT is a rejection. A candidate that cannot be retrieved (`candidate-unavailable`) is a custody refusal,
# not infrastructure: it still holds. VERIFICATION-OUTCOME-INTEGRITY: only an admitted REJECT is a rejection, so
# verification evidence that is not valid (`verification-evidence-invalid`: a malformed packet mutation spec, or a
# session REJECT whose findings lack typed evidence or do not reproduce at the candidate) and a mutation harness that
# gave no result (`mutation-harness-unavailable`) are retried the same way.
VERIFIER_INFRASTRUCTURE = frozenset({"failure", "timeout", "verdict-missing", "verdict-malformed", "verdict-miscorrelated",
                                     "feature-regressions-missing", "verification-evidence-invalid",
                                     "mutation-harness-unavailable"})


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
    def accept(cls, candidate: CandidateRef, findings: tuple[str, ...] = (),
               receipts: tuple[str, ...] = ()) -> "WorkerOutcome":
        return cls("accept", candidate, findings=tuple(findings), receipts=tuple(receipts))

    @classmethod
    def reject(cls, candidate: CandidateRef, findings: tuple[str, ...],
               receipts: tuple[str, ...] = ()) -> "WorkerOutcome":
        return cls("reject", candidate, findings=tuple(findings), receipts=tuple(receipts))

    @classmethod
    def closed(cls, candidate: CandidateRef, receipts: tuple[str, ...]) -> "WorkerOutcome":
        return cls("closed", candidate, receipts=tuple(receipts))


class WorkerProvider(Protocol):
    def start(self, invocation: WorkerInvocation, context: BiuContract, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome: ...
    def read_back(self, invocation: WorkerInvocation) -> WorkerOutcome | None: ...
    def cancel(self, invocation_id: str, reason: str) -> object: ...
