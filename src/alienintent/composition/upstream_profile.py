"""Upstream profile: Inventory -> AmbiguityInspection -> DecisionResolution adapter -> existing DecisionInbox,
plus the pinned PremiseEvidence bridge, pre-implementation ProofPlanning over it, and DesignAdmission whose
applicability gates readiness processing."""
from alienintent.composition.design_admission import PremiseReaderCheck
from alienintent.context_assembly.application.design_admission_service import DesignAdmission, DesignReadiness
from alienintent.context_assembly.adapters.decision_resolution import DecisionInboxQuestions
from alienintent.context_assembly.application.ambiguity_service import AmbiguityService, UpstreamQuestionAdmission
from alienintent.context_assembly.application.inventory_service import InventoryService
from alienintent.context_assembly.ports.design_admission import ArchitectureChecks, DirectionAuthoritySource
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.evidence_learning.application.premise_service import PremiseEvidenceReader
from alienintent.evidence_learning.application.proof_planning_service import ProofPlanning
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.evidence_learning.ports.premise_evidence import PremiseEvidence
from alienintent.evidence_learning.ports.proof_planning import PredicateMappingSource
from alienintent.execution_coordination.ports.operational_store import OperationalStore

IMPLEMENTATION_ROOTS = ("src", "tests", "tools")


class UpstreamProfile:
    """One store/profile and EvidenceRepository shared by inventory, questions and decisions.

    No worker provider or coordinator is composed here: question creation and answer receipt
    cannot launch work.
    """

    def __init__(self, repository: EvidenceRepository, store: OperationalStore, project: str, profile: str,
                 definition_ref: Ref, invocation: str, decision_actor: str, access_scope: frozenset[str],
                 premise_evidence: PremiseEvidence | None = None, premise_target: str | None = None,
                 proof_mappings: PredicateMappingSource | None = None, mapping_reviewer: str | None = None,
                 supersession_authority: str | None = None, design_checks: ArchitectureChecks | None = None,
                 design_authority: DirectionAuthoritySource | None = None,
                 design_reviewers: frozenset[str] = frozenset()) -> None:
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
        # Proof plans are derived from reviewed mappings and the premise reader above, never from code.
        if proof_mappings is not None and not (mapping_reviewer and supersession_authority):
            raise ValueError("proof_mappings requires a mapping reviewer and a supersession authority")
        self.proofs = (ProofPlanning(repository, store, proof_mappings, self.premises, project, profile, definition_ref,
                                     invocation, mapping_reviewer, supersession_authority, IMPLEMENTATION_ROOTS,
                                     access_scope)
                       if proof_mappings is not None else None)
        # Existing architecture checks and pinned premise evidence feed admission; readiness consumes only its
        # applicability, so neither the compiler nor readiness processing can bypass the design gate.
        self.design = (DesignAdmission(repository, store, project, profile, definition_ref, invocation, access_scope,
                                       design_checks, PremiseReaderCheck(self.premises) if self.premises else None,
                                       design_authority, frozenset(design_reviewers))
                       if design_reviewers else None)
        self.design_readiness = DesignReadiness(self.design) if self.design is not None else None
