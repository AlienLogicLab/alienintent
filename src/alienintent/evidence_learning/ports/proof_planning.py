"""Authority-reviewed predicate mappings, supplied by the outer composition boundary."""
from typing import Protocol

from alienintent.evidence_learning.domain.proof_plan import PlanHold, PredicateMapping


class PredicateMappingSource(Protocol):
    """Loads reviewed mapping data only; implementations never derive predicates from code."""

    def load(self, requirement_id: str) -> PredicateMapping | PlanHold: ...
