"""Readiness routes out of Requirements / Planning: the SF-REQ-035 Decision Inbox and U8's SplitTransaction."""
from typing import Protocol

from alienintent.context_assembly.domain.readiness import SplitResultSet


class ClarificationChannel(Protocol):
    """One inbox question per Agent Ready owner clarification, registered verbatim with no default answer."""

    def open(self, identity: str, attempt_id: str, index: int, question: str) -> str: ...

    def resolved(self, work_item: str) -> str | None:
        """None when an attributable resolve decision is recorded; otherwise the reason it is still pending."""
        ...


class SplitTransactionHandoff(Protocol):
    """Consumer side of U8's SplitTransaction port (C#/contracts/2/ports/3); the transaction itself is U8 (DV-7)."""

    def handoff(self, identity: str, attempt_id: str, assessment_ref: dict, raw_assessment: str,
                recommended_boundaries: tuple) -> SplitResultSet | None: ...
