"""FX-U5 assertions: architecture checks first, independent exact-revision review, invalidation and readiness."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from alienintent.composition.design_admission import (
    EDGE_AUTHORITY_GAP, RepositoryArchitectureChecks, RetainedDirectionAuthority)
from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.context_assembly.application.design_admission_service import ReadinessDecision
from alienintent.context_assembly.domain.design_admission import (
    DESIGN_FIELDS, EXISTING_CHECKS, MECHANICALLY_HELD, REVIEW_REQUIRED, ArchitectureReport, CheckResult,
    CurrentVerified, DesignInvalid, DirectionAuthority, Held, MechanicalReport, PremiseResult, ReviewAdmitted,
    ReviewRefused, Stale, admit_review, applicability, design_from_document, inspect_design, review_from_document)
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage

ROOT = Path(__file__).resolve().parents[2]
PROJECT, PROFILE = "AlienLogicLab/alienintent", "fx-u5"
INVOCATION = "AlienLogicLab/alienintent#97:PRODUCER:a206da1a-2d97-4fe5-86c7-42e8e9eacaa3"
PREMISE_MAPPING = "docs/evidence/wo-220203-fx-u3-premise-mapping.json"
PREMISE_SHA256 = "598abb9c11791428069e2b5605b51f7ebf61afd537f2ca02c39e6bc8ec1bd589"
DESIGN = "docs/evidence/wave2-design-contracts.json"
DESIGN_SHA256 = "56676dd97cd09031882ee01e61af2a15071f1b92f6c914fde2169b682f056242"
CHECKER, SOURCE = ROOT / "tools" / "fitness" / "check_architecture.py", ROOT / "src" / "alienintent"
FORBIDDEN_FIXTURE = ROOT / "tests" / "fixtures" / "fitness" / "layering"
PREMISE = "platform-isolation:wave1-sandbox"
OBSERVABLES = ["OUTSIDE_STATE_READBACK", "OUT_OF_SCOPE_REJECTION", "POSITIVE_TARGET_ACCESS", "PROFILE_SCOPING"]
KEY, REVISION = "SF-REQ-900", "sha256:" + "a" * 64
PRODUCER, VERIFIER = ("Morty", "producer-invocation-1"), ("JC", "verifier-invocation-1")
REVIEWERS = frozenset({"JC", "Morty"})  # Morty reviews other work; never their own design.


def ref(name: str) -> Ref:
    return Ref(PROJECT, PROFILE, name, "sha256:" + sha256(name.encode()).hexdigest(), "fixture:" + name)


def contract(**changes) -> dict:
    document = {
        "schema_version": 1, "record_kind": "DesignContract", "design_key": KEY, "requirements": {KEY: REVISION},
        "producer": {"actor": PRODUCER[0], "invocation": PRODUCER[1]},
        "fields": {**{f: {"value": [f.replace("_", " ") + " for the fixture change"]} for f in DESIGN_FIELDS},
                   "satisfied_requirements": {"value": [KEY]}},
        "decisions": [
            {"id": "D-API", "category": "PUBLIC_API", "status": "FIXED", "statement": "check(design_key, vector)", "bound": ""},
            {"id": "D-LOCAL", "category": "IMPLEMENTATION_LOCAL", "status": "OPEN", "statement": "private helper names",
             "bound": "private helpers inside context_assembly; no predicate, identity or persistence change"}],
        "interface_manifest": [{"port": "DesignApplicability.check", "producer": "context_assembly",
                                "consumer": "readiness", "provides": ["design_key", "current_revision_vector"],
                                "requires": ["current_revision_vector"]}],
        "premises": [{"premise_id": PREMISE, "criterion": "four-part sandbox isolation", "requested": list(OBSERVABLES)}],
        "dependency_edges": []}
    document.update(changes)
    return document


def review(report: MechanicalReport, reviewer=VERIFIER, decision="VERIFIED", findings=(), producer=PRODUCER) -> dict:
    return {"reviewer": {"actor": reviewer[0], "invocation": reviewer[1]},
            "producer": {"actor": producer[0], "invocation": producer[1]}, "design_digest": report.design_digest,
            "mechanical_report_digest": report.digest, "revision_vector": deepcopy(report.vector),
            "findings": [dict(f) for f in findings], "decision": decision,
            "authority": "independent VERIFIER role under the WO-220205 allocation"}


class _Recorded:
    """The real checker's report over src/alienintent, computed once per test process."""
    report = None

    def run(self) -> ArchitectureReport:
        if _Recorded.report is None:
            _Recorded.report = RepositoryArchitectureChecks(CHECKER, SOURCE).run()
        return _Recorded.report


class DesignAdmissionTests(unittest.TestCase):
    """Composed profile over a real temporary SQLite store, local evidence, U3 premise evidence and the checker."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state = Path(self._tmp.name)

    def profile(self, checks=None, name="state") -> UpstreamProfile:
        state = self.state / name
        state.mkdir()
        self.store = SQLiteOperationalStore(state / "operational.sqlite")
        return UpstreamProfile(
            LocalEvidenceRepository(state / "evidence", PROJECT, PROFILE), self.store, PROJECT, PROFILE,
            ref("FX-U5-contract"), INVOCATION, "Founder", frozenset({"private"}),
            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT, PROFILE),
            premise_target="AlienLogicLab/alienintent-sandbox", design_checks=checks or _Recorded(),
            design_authority=RetainedDirectionAuthority(ROOT, DESIGN, DESIGN_SHA256, EDGE_AUTHORITY_GAP, PROJECT, PROFILE),
            design_reviewers=REVIEWERS)

    def assertHolds(self, report, reason):
        self.assertIsInstance(report, MechanicalReport)
        self.assertEqual(report.status, MECHANICALLY_HELD)
        self.assertIn(reason, [h.reason_code for h in report.holds])

    def assertRefused(self, result, reason):
        self.assertIsInstance(result, ReviewRefused)
        self.assertEqual(result.reason_code, reason)

    def inspected(self, profile, document, version):
        """A hold is asserted as a type first, so a refused inspection fails the assertion, never errors."""
        report = profile.design.inspect(document, version)
        self.assertIsInstance(report, MechanicalReport)
        return report

    def verified(self, profile, document=None, version=0):
        report = self.inspected(profile, document or contract(), version)
        self.assertEqual(report.status, REVIEW_REQUIRED, report.holds)
        admitted = profile.design.record_review(KEY, review(report), version + 1)
        self.assertIsInstance(admitted, ReviewAdmitted)
        return report

    # --- AC-06 and 051-review-applicability conforming control --------------------------------------

    def test_conforming_independent_review_is_current_and_ready(self):
        profile = self.profile()
        self.assertIsNotNone(profile.design)
        self.assertIsNotNone(profile.design_readiness)
        report = self.verified(profile)
        self.assertEqual([c["check"] for c in report.checks][0], "existing-architecture")
        self.assertEqual([c["name"] for c in report.checks[0]["existing"]], list(EXISTING_CHECKS))
        self.assertTrue(all(c["result"] == "PASS" for c in report.checks))
        self.assertTrue(report.premises[0]["feasible"])
        current = profile.design.check(KEY, report.vector)
        self.assertIsInstance(current, CurrentVerified)
        decision = profile.design_readiness.admit(KEY, report.vector)
        self.assertEqual((decision.admitted, decision.reason_code), (True, "CURRENT_VERIFIED"))
        self.assertEqual([e for e, _ in profile.design.history(KEY)], ["design.review_required", "design.verified"])

    def test_readiness_refuses_missing_design_review_and_authority_without_project_state(self):
        profile = self.profile()
        refused = profile.design_readiness.admit(KEY, {})
        self.assertEqual((refused.admitted, refused.reason_code), (False, "NO_DESIGN"))
        report = profile.design.inspect(contract(), 0)
        refused = profile.design_readiness.admit(KEY, report.vector)
        self.assertEqual((refused.admitted, refused.reason_code), (False, REVIEW_REQUIRED))
        edge = [{"source": "execution_coordination", "target": "context_assembly.application"}]
        other = profile.design.inspect(contract(design_key="SF-REQ-901", requirements={"SF-REQ-901": REVISION},
                                                fields={**contract()["fields"],
                                                        "satisfied_requirements": {"value": ["SF-REQ-901"]}},
                                                dependency_edges=edge), 0)
        refused = profile.design_readiness.admit("SF-REQ-901", other.vector)
        self.assertEqual((refused.admitted, refused.reason_code), (False, MECHANICALLY_HELD))
        self.assertIn("ARCHITECTURE_AUTHORITY_HOLD", refused.applicability.affected)
        self.assertEqual({a for a, _, _ in self.store.list_states(PROFILE)},
                         {"upstream:design:" + KEY, "upstream:design:SF-REQ-901"})
        self.assertEqual([s.value for s in LifecycleStage], ["IMPLEMENT", "VERIFY", "REVIEW", "ACCEPT", "DONE"])

    # --- 051-architecture-boundary --------------------------------------------------------------------

    def test_direction_dependent_admission_holds_on_open_authority(self):
        profile = self.profile()
        authority = profile.design.authority.read()
        self.assertEqual((authority.gap_id, authority.status), (EDGE_AUTHORITY_GAP, "OPEN"))
        edge = [{"source": "execution_coordination", "target": "context_assembly.application"}]
        report = profile.design.inspect(contract(dependency_edges=edge), 0)
        self.assertHolds(report, "ARCHITECTURE_AUTHORITY_HOLD")
        self.assertEqual(report.checks[0]["result"], "PASS")  # Existing checks still ran, first.
        self.assertRefused(profile.design.record_review(KEY, review(report), 1), "MECHANICAL_HOLD_OUTSTANDING")
        self.assertFalse(profile.design_readiness.admit(KEY, report.vector).admitted)

    def test_observed_edge_is_not_permission(self):
        profile = self.profile()
        observed = profile.design.authority.read().observed_edges
        self.assertIn("installation", observed["execution_coordination"])
        edge = [{"source": "execution_coordination", "target": "installation"}]
        report = profile.design.inspect(contract(dependency_edges=edge), 0)
        self.assertHolds(report, "ARCHITECTURE_AUTHORITY_HOLD")
        self.assertIn("execution_coordination -> installation",
                      next(h for h in report.holds if h.reason_code == "ARCHITECTURE_AUTHORITY_HOLD").affected)

    def test_forbidden_adapter_import_holds_before_review(self):
        profile = self.profile(RepositoryArchitectureChecks(CHECKER, FORBIDDEN_FIXTURE))
        report = profile.design.inspect(contract(), 0)
        self.assertHolds(report, "ARCHITECTURE_CHECK_FAILED")
        failed = next(h for h in report.holds if h.reason_code == "ARCHITECTURE_CHECK_FAILED")
        self.assertTrue(any("domain imports adapters" in v for v in failed.affected), failed.affected)
        self.assertRefused(profile.design.record_review(KEY, review(report), 1), "MECHANICAL_HOLD_OUTSTANDING")

    def test_incompatible_consumer_input_holds(self):
        manifest = [{"port": "DesignApplicability.check", "producer": "context_assembly", "consumer": "readiness",
                     "provides": ["design_key"], "requires": ["current_revision_vector"]}]
        report = self.profile().design.inspect(contract(interface_manifest=manifest), 0)
        self.assertHolds(report, "INCOMPATIBLE_INTERFACE")

    # --- 051-review-applicability ---------------------------------------------------------------------

    def test_review_before_checks_is_refused(self):
        profile = self.profile()
        report = inspect_design(design_from_document(contract()), _Recorded().run(), None, None)
        self.assertRefused(profile.design.record_review(KEY, review(report), 0), "NO_MECHANICAL_REPORT")
        self.assertEqual(profile.design_readiness.admit(KEY, report.vector).reason_code, "NO_DESIGN")

    def test_self_review_is_refused_and_downstream_holds(self):
        profile = self.profile()
        report = profile.design.inspect(contract(), 0)
        self.assertRefused(profile.design.record_review(KEY, review(report, reviewer=("Morty", "other-invocation")), 1),
                           "SELF_REVIEW")
        self.assertEqual(profile.design_readiness.admit(KEY, report.vector).reason_code, REVIEW_REQUIRED)
        self.assertEqual([e for e, _ in profile.design.history(KEY)][-1], "design.review_refused")

    def test_shared_producer_invocation_is_self_review(self):
        profile = self.profile()
        report = profile.design.inspect(contract(), 0)
        self.assertRefused(profile.design.record_review(KEY, review(report, reviewer=("JC", PRODUCER[1])), 1),
                           "SELF_REVIEW")
        self.assertFalse(profile.design_readiness.admit(KEY, report.vector).admitted)

    def test_stale_design_review_replay_holds(self):
        profile = self.profile()
        first = self.verified(profile)
        changed = contract()
        changed["decisions"][0]["statement"] = "check(design_key, vector, consumer)"
        second = self.inspected(profile, changed, 2)
        self.assertEqual(second.status, REVIEW_REQUIRED)
        self.assertRefused(profile.design.record_review(KEY, review(first), 3), "STALE_REVIEW")
        self.assertFalse(profile.design_readiness.admit(KEY, second.vector).admitted)
        self.assertIsInstance(profile.design.record_review(KEY, review(second), 4), ReviewAdmitted)
        self.assertTrue(profile.design_readiness.admit(KEY, second.vector).admitted)

    def test_unauthorized_reviewer_is_refused(self):
        profile = self.profile()
        report = profile.design.inspect(contract(), 0)
        self.assertRefused(profile.design.record_review(KEY, review(report, reviewer=("Mallory", "m-1")), 1),
                           "UNAUTHORIZED_REVIEWER")
        self.assertFalse(profile.design_readiness.admit(KEY, report.vector).admitted)

    # --- AC-05 ----------------------------------------------------------------------------------------

    def test_changed_requirement_revision_is_stale(self):
        profile = self.profile()
        report = self.verified(profile)
        moved = {**deepcopy(report.vector), "requirements": {KEY: "sha256:" + "b" * 64}}
        result = profile.design.check(KEY, moved)
        self.assertIsInstance(result, Stale)
        self.assertEqual(result.changed, ("requirements",))
        # Invalidation is durable until re-inspection and a fresh review.
        self.assertIsInstance(profile.design.check(KEY, report.vector), Stale)
        self.assertEqual(profile.design_readiness.admit(KEY, report.vector).reason_code, "STALE")

    def test_new_design_revision_invalidates_and_retains_history(self):
        profile = self.profile()
        first = self.verified(profile)
        changed = contract()
        changed["decisions"][0]["statement"] = "check(design_key, vector, consumer)"
        second = self.inspected(profile, changed, 2)
        self.assertEqual(profile.design.check(KEY, second.vector), Held(REVIEW_REQUIRED))
        self.assertIsInstance(profile.design.check(KEY, first.vector), Stale)
        history = profile.design.history(KEY)
        self.assertEqual([e for e, _ in history], ["design.review_required", "design.verified", "design.review_required"])
        prior = profile.design.retained(history[1][1])
        self.assertEqual((prior["review"]["decision"], prior["review"]["design_digest"]), ("VERIFIED", first.design_digest))
        prior_report = profile.design.retained(history[0][1])
        self.assertEqual(prior_report["report"]["design_digest"], first.design_digest)

    def test_stale_design_is_not_reverified_in_place(self):
        profile = self.profile()
        report = self.verified(profile)
        moved = {**deepcopy(report.vector), "requirements": {KEY: "sha256:" + "b" * 64}}
        self.assertIsInstance(profile.design.check(KEY, moved), Stale)
        self.assertRefused(profile.design.record_review(KEY, review(report), 3), "STALE_REVIEW")
        again = self.inspected(profile, contract(), 4)
        self.assertEqual(again.status, REVIEW_REQUIRED)
        self.assertIsInstance(profile.design.record_review(KEY, review(again), 5), ReviewAdmitted)

    def test_attributed_rejection_stands_until_repair(self):
        profile = self.profile()
        report = self.inspected(profile, contract(), 0)
        finding = {"id": "F-1", "blocking": True, "disposition": "premise needs a repaired design"}
        self.assertIsInstance(profile.design.record_review(KEY, review(report, decision="REJECTED", findings=[finding]), 1),
                              ReviewAdmitted)
        self.assertRefused(profile.design.record_review(KEY, review(report, reviewer=("Morty", "m-2"),
                                                                    producer=PRODUCER), 2), "SELF_REVIEW")
        self.assertRefused(profile.design.record_review(KEY, review(report), 3), "BLOCKING_FINDINGS")
        repaired = contract()
        repaired["fields"]["invariants"] = {"value": ["repaired invariant for the fixture change"]}
        report = self.inspected(profile, repaired, 4)
        self.assertIsInstance(profile.design.record_review(KEY, review(report), 5), ReviewAdmitted)

    def test_corrupted_state_is_a_hold(self):
        profile = self.profile()
        report = self.verified(profile)
        version, state = self.store.read_state(PROFILE, "upstream:design:" + KEY)
        self.store.commit(PROFILE, "upstream:design:" + KEY, version, {**state, "history": state["history"][:1]})
        self.assertEqual(profile.design.check(KEY, report.vector), Held("INCOMPATIBLE_DESIGN_STATE", (KEY,)))
        self.assertFalse(profile.design_readiness.admit(KEY, report.vector).admitted)

    # --- AC-01 ----------------------------------------------------------------------------------------

    def test_incomplete_design_holds(self):
        fields = {k: v for k, v in contract()["fields"].items() if k != "security"}
        report = self.profile().design.inspect(contract(fields=fields), 0)
        self.assertHolds(report, "INCOMPLETE_DESIGN")
        self.assertIn("security", report.holds[0].affected)

    def test_unexplained_inapplicability_holds(self):
        profile = self.profile()
        blank = profile.design.inspect(contract(fields={**contract()["fields"], "persistence": {"inapplicable": " "}}), 0)
        self.assertHolds(blank, "UNEXPLAINED_INAPPLICABILITY")
        explained = profile.design.inspect(contract(fields={**contract()["fields"], "persistence": {
            "inapplicable": "the change reads existing aggregates only and persists nothing new"}}), 1)
        self.assertEqual(explained.status, REVIEW_REQUIRED, explained.holds)

    # --- AC-02 ----------------------------------------------------------------------------------------

    def test_open_material_decision_blocks_and_bounded_local_choice_stays_open(self):
        profile = self.profile()
        decisions = deepcopy(contract()["decisions"])
        decisions[0]["status"] = "OPEN"
        report = profile.design.inspect(contract(decisions=decisions), 0)
        self.assertHolds(report, "UNRESOLVED_MATERIAL_DECISION")
        self.assertEqual(report.holds[0].affected, ("D-API",))
        bounded = profile.design.inspect(contract(), 1)
        self.assertEqual(bounded.status, REVIEW_REQUIRED, bounded.holds)

    def test_unbounded_local_choice_holds(self):
        decisions = deepcopy(contract()["decisions"])
        decisions[1]["bound"] = ""
        report = self.profile().design.inspect(contract(decisions=decisions), 0)
        self.assertHolds(report, "UNBOUNDED_LOCAL_CHOICE")

    def test_blocking_finding_cannot_be_verified(self):
        profile = self.profile()
        report = profile.design.inspect(contract(), 0)
        finding = {"id": "F-1", "blocking": True,
                   "disposition": "D-LOCAL hides a persistence decision; return it to SPECIFY"}
        self.assertRefused(profile.design.record_review(KEY, review(report, findings=[finding]), 1), "BLOCKING_FINDINGS")
        rejected = profile.design.record_review(KEY, review(report, decision="REJECTED", findings=[finding]), 2)
        self.assertIsInstance(rejected, ReviewAdmitted)
        self.assertEqual(profile.design_readiness.admit(KEY, report.vector).reason_code, "REVIEW_REJECTED")

    # --- AC-04 ----------------------------------------------------------------------------------------

    def test_impossible_premise_is_rejected_despite_complete_checklist(self):
        profile = self.profile()
        premises = [{"premise_id": PREMISE, "criterion": "an out-of-scope Project token request is denied",
                     "requested": OBSERVABLES + ["CREDENTIAL_DENIAL"]}]
        report = profile.design.inspect(contract(premises=premises), 0)
        self.assertHolds(report, "INFEASIBLE_PREMISE")
        self.assertEqual([c["result"] for c in report.checks if c["check"] != "platform-premise"], ["PASS"] * 5)
        self.assertEqual((report.premises[0]["reason"], report.premises[0]["missing"]),
                         ("UNACHIEVABLE_PREMISE", ["CREDENTIAL_DENIAL"]))
        self.assertTrue(report.premises[0]["evidence_refs"])
        self.assertRefused(profile.design.record_review(KEY, review(report), 1), "MECHANICAL_HOLD_OUTSTANDING")
        finding = {"id": "P-1", "blocking": True,
                   "disposition": "credential denial is unachievable under SWF-34 capability evidence"}
        self.assertIsInstance(profile.design.record_review(KEY, review(report, decision="REJECTED", findings=[finding]), 2),
                              ReviewAdmitted)
        self.assertFalse(profile.design_readiness.admit(KEY, report.vector).admitted)

    def test_verified_review_of_held_design_is_refused(self):
        profile = self.profile()
        decisions = deepcopy(contract()["decisions"])
        decisions[0]["status"] = "OPEN"
        report = profile.design.inspect(contract(decisions=decisions), 0)
        self.assertRefused(profile.design.record_review(KEY, review(report), 1), "MECHANICAL_HOLD_OUTSTANDING")
        self.assertEqual(profile.design_readiness.admit(KEY, report.vector).reason_code, MECHANICALLY_HELD)


class DesignAdmissionDomainTests(unittest.TestCase):
    """Pure domain rules; these stay green when the composed caller is disconnected."""

    ARCH = ArchitectureReport("sha256:" + "c" * 64, tuple(CheckResult(n, True) for n in EXISTING_CHECKS))
    OPEN = DirectionAuthority(EDGE_AUTHORITY_GAP, "OPEN", "Founder", None, {"execution_coordination": ["installation"]})

    def inspect(self, document=None, architecture=ARCH, authority=OPEN, premises=()):
        return inspect_design(design_from_document(document or contract(premises=[])), architecture, authority, premises)

    def test_malformed_design_is_invalid(self):
        for change in ({"fields": {"unknown": {"value": ["x"]}}}, {"decisions": [{"id": "D"}]}, {"schema_version": 2},
                       {"requirements": {}}, {"premises": [{"premise_id": "p", "criterion": "c", "requested": []}]}):
            with self.assertRaises(DesignInvalid, msg=change):
                design_from_document(contract(**change))

    def test_checks_run_in_order_and_all_report(self):
        report = self.inspect(architecture=None)
        self.assertEqual([c["check"] for c in report.checks],
                         ["existing-architecture", "interface-compatibility", "contract-completeness", "decisions",
                          "platform-premise", "direction-authority"])
        self.assertEqual(report.holds[0].reason_code, "ARCHITECTURE_BASELINE_MISSING")
        partial = ArchitectureReport(self.ARCH.baseline, self.ARCH.results[:2])
        self.assertEqual(self.inspect(architecture=partial).holds[0].reason_code, "ARCHITECTURE_CHECK_UNAVAILABLE")

    def test_premises_without_evidence_hold(self):
        report = inspect_design(design_from_document(contract()), self.ARCH, self.OPEN, None)
        self.assertEqual([h.reason_code for h in report.holds], ["PREMISE_EVIDENCE_UNAVAILABLE"])
        feasible = (PremiseResult(PREMISE, True, None, (), (ref("evidence"),)),)
        self.assertEqual(inspect_design(design_from_document(contract()), self.ARCH, self.OPEN, feasible).status,
                         REVIEW_REQUIRED)

    def test_disposed_authority_still_never_passes_a_declared_edge(self):
        disposed = DirectionAuthority(EDGE_AUTHORITY_GAP, "FOUNDER_DISPOSED", "Founder", ref("disposition"), {})
        edge = [{"source": "evidence_learning", "target": "installation"}]
        report = self.inspect(contract(premises=[], dependency_edges=edge), authority=disposed)
        self.assertEqual([h.reason_code for h in report.holds], ["DIRECTION_SCOPE_UNREVIEWED"])
        self.assertEqual([h.reason_code for h in self.inspect(contract(premises=[], dependency_edges=edge),
                                                              authority=None).holds], ["ARCHITECTURE_AUTHORITY_HOLD"])

    def test_requirement_link_must_match(self):
        fields = {**contract()["fields"], "satisfied_requirements": {"value": ["SF-REQ-999"]}}
        self.assertEqual([h.reason_code for h in self.inspect(contract(premises=[], fields=fields)).holds],
                         ["REQUIREMENT_LINK_MISMATCH"])
        fields["satisfied_requirements"] = {"inapplicable": "none"}
        self.assertEqual([h.reason_code for h in self.inspect(contract(premises=[], fields=fields)).holds],
                         ["REQUIREMENT_LINK_MISMATCH"])

    def test_review_admission_rules(self):
        design = design_from_document(contract(premises=[]))
        report = self.inspect()
        admit = lambda document: admit_review(design, report, review_from_document(document), REVIEWERS)
        self.assertIsInstance(admit(review(report)), ReviewAdmitted)
        self.assertEqual(admit(review(report, producer=("Other", "x"))).reason_code, "PRODUCER_MISMATCH")
        self.assertEqual(review_from_document({**review(report), "decision": "REJECTED"}).reason_code, "INVALID_REVIEW")
        self.assertEqual(review_from_document({"reviewer": {}}).reason_code, "INVALID_REVIEW")
        moved = review(report)
        moved["revision_vector"]["architecture"] = "sha256:" + "d" * 64
        self.assertEqual(admit(moved).reason_code, "STALE_REVIEW")

    def test_applicability_states(self):
        report = self.inspect()
        self.assertEqual(applicability(None, None, None, None, {}), Held("NO_DESIGN"))
        self.assertEqual(applicability("REVIEW_REQUIRED", report, None, "REJECTED", report.vector), Held("REVIEW_REJECTED"))
        self.assertIsInstance(applicability("VERIFIED", report, "sha256:r", "VERIFIED", report.vector), CurrentVerified)
        self.assertEqual(applicability("STALE", report, "sha256:r", "VERIFIED", report.vector), Stale(("stale",)))
        self.assertIsInstance(ReadinessDecision(False, "NO_DESIGN", Held("NO_DESIGN")), ReadinessDecision)


if __name__ == "__main__":
    unittest.main()
