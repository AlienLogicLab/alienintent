"""Wave 2A upstream integration (WO-220211, node A): wiring only, over one composed UpstreamProfile.

inventory -> ambiguity -> premise/proof -> design applicability -> initial compilation -> lint and retained
assessment consumption. Every stage is the unchanged predecessor service; this module only carries values between
them. The design gate is always asked with the current revision vector, recomputed from the current inputs of every
stage, never with the vector a candidate pinned: each requirement's revision counts only while it is eligible in the
current inventory and ELIGIBLE in an inspection of that same inventory, and the architecture baseline, premise
evidence and direction authority are re-read through the design admission's own checks.
Governing decisions are re-read by path and digest, and the pinned proof plans compared with the current ones, for
the same reason. A changed source, decision or design
therefore invalidates downstream applicability and readiness instead of reusing stale evidence.

Nothing here writes lifecycle, release, Issue or Project state, and no output asserts release: READY stays
eligibility for the separate release gate.
"""
from hashlib import sha256
from pathlib import Path

from alienintent.composition.compilation import CurrentProofPlanDocuments
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.application.design_admission_service import DesignStateInvalid
from alienintent.context_assembly.domain.ambiguity import ELIGIBLE, AmbiguityHold, snapshot_from_document
from alienintent.context_assembly.domain.compilation import CompilationHold, canonical
from alienintent.context_assembly.domain.design_admission import DesignInvalid, design_from_document, inspect_design
from alienintent.context_assembly.domain.initial_compilation import CompilationCandidate
from alienintent.context_assembly.domain.inventory import InventoryHold
from alienintent.context_assembly.domain.readiness import LintHold, Outcome
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.execution_coordination.domain.readiness import Hold, ReadinessEligibility

UNAVAILABLE = "UNAVAILABLE"
NO_DESIGN_VECTOR = {"design": None}  # Applicability of an absent or unreadable design is a hold, never current.


class UpstreamIntegration:
    def __init__(self, profile: UpstreamProfile, decision_root: Path) -> None:
        if profile.initial_compilation is None or profile.readiness is None:
            raise ValueError("the integration needs initial compilation and readiness admission composed")
        self.profile, self._decisions = profile, Path(decision_root)

    def current_vector(self, design_key: str) -> dict:
        """The revision vector of the current design of design_key over the current inputs of every stage."""
        admission = self.profile.design
        try:
            _, state = admission.read(design_key)
            report = admission.retained(ref_from_document(state["report_ref"]))
            design = design_from_document(admission.retained(ref_from_document(report["design_ref"])))
        except (DesignStateInvalid, DesignInvalid, EvidenceHold, KeyError, TypeError, ValueError):
            return dict(NO_DESIGN_VECTOR)
        architecture = admission.architecture.run() if admission.architecture is not None else None
        authority = admission.authority.read() if admission.authority is not None else None
        premises = (tuple(admission.premises.check(p["premise_id"], frozenset(p["requested"]))
                          for p in design.premises) if admission.premises is not None else None)
        vector = inspect_design(design, architecture, authority, premises).vector
        revisions = self._revisions()
        return {**vector, "requirements": {r: revisions.get(r) for r in sorted(design.requirements)}}

    def _revisions(self) -> dict[str, str]:
        """Each current requirement revision that is authorized and eligible for preparation, as initial compilation
        pins it: exactly one eligible definition in the current inventory, reported ELIGIBLE by an inspection of that
        same inventory. Anything else is absent, so no design pinning it is current."""
        try:
            _, document = self.profile.inventory.read()
            inventory = snapshot_from_document(document) if document else None
            inspection = self.profile.ambiguity.report()
        except (AmbiguityHold, InventoryHold, EvidenceHold, KeyError, TypeError, ValueError):
            return {}
        if inventory is None or inspection is None or inspection.inventory_digest != inventory.digest:
            return {}
        reports = {r.requirement_id: r for r in inspection.requirements}
        revisions = {}
        for requirement in inventory.current:
            report = reports.get(requirement.requirement_id)
            if sum(r.requirement_id == requirement.requirement_id for r in inventory.current) == 1 \
                    and requirement.eligible and not requirement.retired and report is not None \
                    and report.revision == requirement.revision and report.preparation == ELIGIBLE:
                revisions[requirement.requirement_id] = requirement.revision
        return revisions

    def compile(self, design_key: str, authority_limits: dict) -> CompilationCandidate | CompilationHold:
        return self.profile.initial_compilation.compile(design_key, self.current_vector(design_key), authority_limits)

    def decisions(self, paths: tuple[str, ...]) -> tuple[str, ...]:
        """Each governing decision as path@sha256 of its current bytes; unreadable or outside the decision root is
        path@UNAVAILABLE."""
        revisions = []
        for path in paths:
            target = (self._decisions / path).resolve()
            try:
                if not target.is_relative_to(self._decisions.resolve()):
                    raise OSError("outside the decision root")
                revisions.append(f"{path}@sha256:{sha256(target.read_bytes()).hexdigest()}")
            except OSError:
                revisions.append(f"{path}@{UNAVAILABLE}")
        return tuple(revisions)

    def candidate(self, compiled: CompilationCandidate, identity: str, decisions: tuple[str, ...]) -> dict:
        """One derived unit as the pinned readiness candidate; its text is the unit's canonical document."""
        document = compiled.document()
        unit = next(u for u in document["units"] if u["identity"] == identity)
        contract = unit["contract"]
        return {"contract": contract, "text": canonical(unit), "baseline": ",".join(contract["baselines"]),
                "design_key": document["inputs"]["design"]["design_key"],
                "design_vector": self.current_vector(document["inputs"]["design"]["design_key"]),
                "dependency_edges": [e["from"] for e in document["edges"] if e["to"] == identity],
                "governing_decisions": list(self.decisions(decisions))}

    @staticmethod
    def proof_plan(compiled: CompilationCandidate, identity: str) -> tuple[str, ...]:
        """The digests of the proof plans the unit was derived from; any unplanned requirement leaves none pinned."""
        document = compiled.document()
        unit = next(u for u in document["units"] if u["identity"] == identity)
        plans = document["inputs"]["proof_plans"]
        requirements = unit["contract"]["satisfied_requirement_ids"]
        if not requirements or any(not plans.get(r) for r in requirements):
            return ()
        return tuple(sorted(plans[r] for r in requirements))

    def current_plans(self, requirement_ids: list[str]) -> tuple[str, ...]:
        """The digests of the current feasible proof plans; any requirement without one leaves none."""
        plans = CurrentProofPlanDocuments(self.profile.proofs)
        documents = [plans.document(r) for r in requirement_ids]
        if not requirement_ids or any(d is None for d in documents):
            return ()
        return tuple(sorted(d["digest"] for d in documents))

    def _refreshed(self, candidate: dict, proof_plan: tuple[str, ...]) -> dict | LintHold:
        """The candidate re-read against the current design vector, governing decision revisions and proof plans."""
        contract = candidate.get("contract") if isinstance(candidate.get("contract"), dict) else {}
        identity = contract.get("identity", "<unidentified>")
        paths = tuple(d.rsplit("@", 1)[0] for d in candidate.get("governing_decisions") or ())
        decisions = self.decisions(paths)
        unavailable = [d for d in decisions if d.endswith("@" + UNAVAILABLE)]
        if unavailable:
            return LintHold(identity, "decision", "governing_decisions", "unavailable: " + ",".join(unavailable))
        requirements = contract.get("satisfied_requirement_ids")
        if isinstance(requirements, list) and tuple(sorted(proof_plan or ())) != self.current_plans(requirements):
            return LintHold(identity, "verification", "proof_plan", "pinned proof plan is not the current plan")
        return {**candidate, "design_vector": self.current_vector(str(candidate.get("design_key"))),
                "governing_decisions": list(decisions)}

    def assess(self, candidate: dict, proof_plan: tuple[str, ...]) -> Outcome:
        refreshed = self._refreshed(candidate, proof_plan)
        return refreshed if isinstance(refreshed, LintHold) else self.profile.readiness.assess(refreshed, proof_plan)

    def current(self, candidate: dict, proof_plan: tuple[str, ...]) -> ReadinessEligibility | Hold | LintHold:
        """Read-time readiness of a previously assessed candidate against the current upstream."""
        refreshed = self._refreshed(candidate, proof_plan)
        return refreshed if isinstance(refreshed, LintHold) else self.profile.readiness.current(refreshed, proof_plan)
