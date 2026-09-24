"""Pinned platform/consumer capability evidence, supplied by the outer composition boundary."""
from typing import Protocol

from alienintent.evidence_learning.domain.premise import RetainedPremiseEvidence


class PremiseEvidence(Protocol):
    """Reads retained evidence only; implementations run no credential or doctor probe."""

    def observe(self) -> RetainedPremiseEvidence: ...
