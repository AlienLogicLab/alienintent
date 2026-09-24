"""Upstream profile: Inventory -> AmbiguityInspection -> DecisionResolution adapter -> existing DecisionInbox,
plus the pinned PremiseEvidence bridge."""
from alienintent.context_assembly.adapters.decision_resolution import DecisionInboxQuestions
from alienintent.context_assembly.application.ambiguity_service import AmbiguityService, UpstreamQuestionAdmission
from alienintent.context_assembly.application.inventory_service import InventoryService
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.evidence_learning.application.premise_service import PremiseEvidenceReader
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.evidence_learning.ports.premise_evidence import PremiseEvidence
from alienintent.execution_coordination.ports.operational_store import OperationalStore


class UpstreamProfile:
    """One store/profile and EvidenceRepository shared by inventory, questions and decisions.

    No worker provider or coordinator is composed here: question creation and answer receipt
    cannot launch work.
    """

    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, decision_actor: str, access_scope: frozenset[str],
                 premise_evidence: PremiseEvidence | None = None, premise_target: str | None = None) -> None:
        self.inventory = InventoryService(repository, store, project, profile, definition_ref, invocation, access_scope)
        self.inbox = DecisionInbox(store, UpstreamQuestionAdmission(decision_actor), profile)
        self.questions = DecisionInboxQuestions(self.inbox, profile)
        self.ambiguity = AmbiguityService(self.inventory, repository, store, self.questions, project, profile,
                                          definition_ref, invocation, decision_actor, access_scope, self.questions)
        # Retained capability evidence enters as neutral values; no probe runs here.
        if (premise_evidence is None) != (premise_target is None):
            raise ValueError("premise_evidence and premise_target must be configured together")
        self.premises = (PremiseEvidenceReader(premise_evidence, premise_target)
                         if premise_evidence is not None and premise_target is not None else None)
