"""Compiler-validation inputs bound at the composition boundary: execution lifecycle and verified design decisions.

context_assembly imports neither execution_coordination.application nor its adapters; the coordinator and the
U5 admission service are injected here.
"""
from alienintent.context_assembly.application.design_admission_service import DesignAdmission, DesignStateInvalid
from alienintent.context_assembly.domain.design_admission import DesignInvalid, design_from_document
from alienintent.context_assembly.ports.compilation import DependencyLifecycle, DesignDecisions
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


class VerifiedDesignDecisions(DesignDecisions):
    """FIXED decisions read back from the retained design of the exact verified revision."""

    def __init__(self, admission: DesignAdmission) -> None:
        self._admission = admission

    def fixed_decisions(self, design_key: str, design_digest: str) -> dict[str, str] | None:
        try:
            _, state = self._admission.read(design_key)
            report = self._admission.retained(ref_from_document(state["report_ref"]))
            design = design_from_document(self._admission.retained(ref_from_document(report["design_ref"])))
        except (DesignStateInvalid, DesignInvalid, EvidenceHold, KeyError, TypeError, ValueError):
            return None
        if design.digest != design_digest:
            return None
        return {d["id"]: d["statement"] for d in design.decisions if d["status"] == "FIXED"}
