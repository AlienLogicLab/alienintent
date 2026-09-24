"""Context reconstruction boundary; the DecisionInbox queue is reused, never merged."""
from typing import Protocol

from alienintent.context_assembly.domain.reconstruction import ContextHold, ReconstructedContext


class ContextAssembler(Protocol):
    def pin(self) -> str: ...
    def reconstruct(self, manifest_ref: str) -> ReconstructedContext | ContextHold: ...
