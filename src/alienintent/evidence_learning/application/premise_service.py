"""Read a pinned platform-isolation premise through the PremiseEvidence port."""
from alienintent.evidence_learning.domain.premise import (
    ISOLATION_OBSERVABLES, InfeasibleProof, PlatformIsolationPremise, evaluate_isolation_premise)
from alienintent.evidence_learning.ports.premise_evidence import PremiseEvidence


class PremiseEvidenceReader:
    def __init__(self, source: PremiseEvidence, target: str) -> None:
        self._source, self._target = source, target

    def read(self, premise_id: str, requested: frozenset[str] = frozenset(o.value for o in ISOLATION_OBSERVABLES)
             ) -> PlatformIsolationPremise | InfeasibleProof:
        return evaluate_isolation_premise(premise_id, self._target, frozenset(requested), self._source.observe())
