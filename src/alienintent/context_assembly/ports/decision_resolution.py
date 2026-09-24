"""Question and answer boundaries; the existing Decision Inbox stays the decision authority."""
from typing import Protocol

from alienintent.context_assembly.domain.ambiguity import Finding
from alienintent.execution_coordination.domain.escalation import DecisionRecord


class InventoryReader(Protocol):
    def read(self) -> tuple[int, dict | None]: ...


class QuestionChannel(Protocol):
    def open(self, finding: Finding) -> None: ...


class DecisionResolution(Protocol):
    """Validates an existing attributable decision; it never mints an approval.

    Returns None when the decision answers exactly this finding, else a hold reason code.
    """
    def validate(self, finding: Finding, decision: DecisionRecord) -> str | None: ...
