"""Upstream profile: Inventory -> AmbiguityInspection -> DecisionResolution adapter -> existing DecisionInbox,
plus the pinned PremiseEvidence bridge, pre-implementation ProofPlanning over it, DesignAdmission whose
applicability gates readiness processing, compiler validation behind that gate, and the SF-REQ-015 readiness
consumer (lint, bound ReadinessAssessment producer and retained-evidence consumer)."""
from pathlib import Path

from alienintent.composition.compilation import VerifiedDesignDecisions
from alienintent.composition.design_admission import PremiseReaderCheck
from alienintent.composition.readiness import resolve_binding
from alienintent.context_assembly.application.design_admission_service import DesignAdmission, DesignReadiness
from alienintent.context_assembly.adapters.compilation_repository import EvidenceAssessmentHistory
from alienintent.context_assembly.adapters.decision_resolution import DecisionInboxQuestions
from alienintent.context_assembly.adapters.readiness_clarification import InboxClarifications
from alienintent.context_assembly.application.compilation_validation_service import CompilationValidation
from alienintent.context_assembly.application.ambiguity_service import AmbiguityService, UpstreamQuestionAdmission
from alienintent.context_assembly.application.inventory_service import InventoryService
from alienintent.context_assembly.application.readiness_service import ReadinessAdmission
from alienintent.context_assembly.ports.compilation import DependencyLifecycle
from alienintent.context_assembly.ports.design_admission import ArchitectureChecks, DirectionAuthoritySource
from alienintent.context_assembly.ports.readiness import SplitTransactionHandoff
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.evidence_learning.application.premise_service import PremiseEvidenceReader
from alienintent.evidence_learning.application.proof_planning_service import ProofPlanning
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.ports.evidence_repository import EvidenceRepository
from alienintent.evidence_learning.ports.premise_evidence import PremiseEvidence
from alienintent.evidence_learning.ports.proof_planning import PredicateMappingSource
from alienintent.execution_coordination.adapters.assessment_consumer import (
    RetainedAssessmentConsumer, RetainedSurrogateHistory)
from alienintent.execution_coordination.ports.operational_store import OperationalStore
from alienintent.execution_coordination.ports.readiness import ReadinessAssessment

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
                 design_reviewers: frozenset[str] = frozenset(),
                 dependency_lifecycle: DependencyLifecycle | None = None,
                 readiness_producer: ReadinessAssessment | None = None, readiness_executable: Path | None = None,
                 readiness_transport: str = "cli", split_handoff: SplitTransactionHandoff | None = None) -> None:
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
        # Compiler validation consumes that gate, the open questions and the execution lifecycle; it writes only its
        # own upstream:compilation: pointers and immutable records, never lifecycle, release or projection state.
        self.compilation = (CompilationValidation(repository, store, project, profile, definition_ref, invocation,
                                                  access_scope, self.design_readiness,
                                                  VerifiedDesignDecisions(self.design), self.ambiguity,
                                                  dependency_lifecycle,
                                                  EvidenceAssessmentHistory(repository, access_scope))
                            if self.design_readiness is not None and dependency_lifecycle is not None else None)
        # Readiness admission sits behind the same design gate and lifecycle. The producer binding is resolved here,
        # from the configured executable's installed metadata; unbound or unestablished provenance holds before
        # launch. READY is eligibility for the existing release gate only; nothing here releases.
        self.readiness_binding = resolve_binding(readiness_executable, readiness_transport)
        self.readiness_consumer = RetainedAssessmentConsumer(repository, store, project, profile, definition_ref,
                                                             invocation, access_scope)
        self.readiness_history = RetainedSurrogateHistory(repository, project, profile, definition_ref, invocation,
                                                          access_scope)
        self.readiness = (ReadinessAdmission(self.readiness_consumer, readiness_producer, self.readiness_binding,
                                             self.design_readiness, dependency_lifecycle,
                                             InboxClarifications(self.inbox, profile, project, decision_actor),
                                             split_handoff)
                          if self.design_readiness is not None and dependency_lifecycle is not None else None)
