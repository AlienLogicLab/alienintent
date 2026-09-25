"""Read-only inputs of compiler validation, supplied by the outer composition boundary."""
from typing import Mapping, Protocol

from alienintent.context_assembly.domain.ambiguity import Finding


class DesignGate(Protocol):
    """The U5 design gate: only an exact current VERIFIED design admits (satisfied by DesignReadiness)."""

    def admit(self, design_key: str, current_vector: dict): ...


class DesignDecisions(Protocol):
    """FIXED decisions of the exact verified design revision, id -> statement; None when not readable as that revision."""

    def fixed_decisions(self, design_key: str, design_digest: str) -> Mapping[str, str] | None: ...


class OpenQuestions(Protocol):
    """Upstream questions by status (satisfied by AmbiguityService.questions)."""

    def questions(self, status: str | None = ...) -> tuple[tuple[Finding, str, tuple[dict, ...]], ...]: ...


class DependencyLifecycle(Protocol):
    """The execution lifecycle stage of one work identity; None when no execution state exists."""

    def stage(self, identity: str) -> str | None: ...


class AssessmentHistory(Protocol):
    """Read-only lookup of a retained prior assessment record: the sha256 of its bytes, or None."""

    def digest(self, ref: dict) -> str | None: ...
