"""Typed evidence evaluation, with no lifecycle mutation capability."""
from typing import Protocol

from alienintent.evidence_learning.domain.records import Header, Verdict
from alienintent.evidence_learning.domain.refs import Ref


class ExecutionVerdict(Protocol):
    def evaluate(self, *, header: Header, definition_ref: Ref, observation_refs: tuple[Ref, ...],
                 evaluator: str, authority_ref: Ref, policy_ref: Ref, worker_claimed_success: bool = False) -> Verdict: ...
