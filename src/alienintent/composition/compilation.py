"""Compiler inputs bound at the composition boundary: execution lifecycle, the verified design and its decisions,
and current proof-plan documents.

context_assembly imports neither execution_coordination.application nor its adapters; the coordinator and the
U5 admission service are injected here.
"""
from alienintent.context_assembly.application.design_admission_service import DesignAdmission, DesignStateInvalid
from alienintent.context_assembly.domain.design_admission import DesignContract, DesignInvalid, design_from_document
from alienintent.context_assembly.ports.compilation import DependencyLifecycle, DesignDecisions, ProofPlans, VerifiedDesigns
from alienintent.evidence_learning.application.proof_planning_service import ProofPlanning
from alienintent.evidence_learning.domain.proof_plan import ProofPlan, plan_document
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator


class CoordinatorDependencyLifecycle(DependencyLifecycle):
    """FactoryCoordinator.state(identity).stage, the same source its DONE eligibility rule reads."""

    def __init__(self, coordinator: FactoryCoordinator) -> None:
        self._coordinator = coordinator

    def stage(self, identity: str) -> str | None:
        try:
            return self._coordinator.state(identity).stage.value
        except KeyError:
            return None


class VerifiedDesignDecisions(DesignDecisions, VerifiedDesigns):
    """The retained design of the exact verified revision, and its FIXED decisions."""

    def __init__(self, admission: DesignAdmission) -> None:
        self._admission = admission

    def design(self, design_key: str, design_digest: str) -> DesignContract | None:
        try:
            _, state = self._admission.read(design_key)
            report = self._admission.retained(ref_from_document(state["report_ref"]))
            design = design_from_document(self._admission.retained(ref_from_document(report["design_ref"])))
        except (DesignStateInvalid, DesignInvalid, EvidenceHold, KeyError, TypeError, ValueError):
            return None
        return design if design.digest == design_digest else None

    def fixed_decisions(self, design_key: str, design_digest: str) -> dict[str, str] | None:
        design = self.design(design_key, design_digest)
        if design is None:
            return None
        return {d["id"]: d["statement"] for d in design.decisions if d["status"] == "FIXED"}


class CurrentProofPlanDocuments(ProofPlans):
    """The current feasible U4 plan as its retained document and digest; a held or absent plan is None."""

    def __init__(self, planning: ProofPlanning) -> None:
        self._planning = planning

    def document(self, requirement_id: str) -> dict | None:
        plan = self._planning.current(requirement_id)
        return {**plan_document(plan), "digest": plan.digest} if isinstance(plan, ProofPlan) else None
