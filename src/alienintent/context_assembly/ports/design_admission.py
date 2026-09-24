"""Read-only inputs of design admission, supplied by the outer composition boundary."""
from typing import Protocol

from alienintent.context_assembly.domain.design_admission import ArchitectureReport, DirectionAuthority, PremiseResult


class ArchitectureChecks(Protocol):
    """Runs the existing approved architecture checks; it never grants approval."""

    def run(self) -> ArchitectureReport: ...


class PremiseCheck(Protocol):
    """Reads pinned platform capability evidence for one requested premise."""

    def check(self, premise_id: str, requested: frozenset[str]) -> PremiseResult: ...


class DirectionAuthoritySource(Protocol):
    """Reads the pinned directional-authority record; it cannot dispose the question."""

    def read(self) -> DirectionAuthority: ...
