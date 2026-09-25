"""Prior Readiness Assessment records read back from the shared EvidenceRepository; never written here."""
from hashlib import sha256

from alienintent.context_assembly.ports.compilation import AssessmentHistory
from alienintent.evidence_learning.domain.records import Observation, ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository

RETAINED_ASSESSMENT = "readiness.assessment.retained"


class EvidenceAssessmentHistory(AssessmentHistory):
    """The digest of a retained assessment's exact bytes; unreadable or foreign evidence is None, never a match."""

    def __init__(self, repository: EvidenceRepository, access_scope: frozenset[str]) -> None:
        self.repository, self.access_scope = repository, access_scope

    def digest(self, ref: dict) -> str | None:
        try:
            record = self.repository.get(ref_from_document(ref), self.access_scope)
        except (EvidenceHold, KeyError, TypeError, ValueError):
            return None
        if not isinstance(record, Observation) or record.evidence_id != RETAINED_ASSESSMENT \
                or not isinstance(record.value, str):
            return None
        return "sha256:" + sha256(record.value.encode()).hexdigest()
