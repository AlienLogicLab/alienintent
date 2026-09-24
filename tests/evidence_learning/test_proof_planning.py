"""FX-U4 assertions: pre-implementation proof plans, qualified controls, premise, judgment and repair."""
import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.proof_mapping import (
    RetainedPredicateMapping, retained_design_ref, retained_requirement_revision)
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.battery import ControlRun, evaluate_control
from alienintent.evidence_learning.domain.premise import InfeasibleProof
from alienintent.evidence_learning.domain.proof_order import ProofStep, proof_order_diagnostics
from alienintent.evidence_learning.domain.proof_plan import (
    MappedPredicate, PlanHold, PredicateKind, PredicateMapping, ProofPlan, RequirementRevision, derive_plan)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.evidence_learning.domain.repair import ReplayStatus
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

ROOT = Path(__file__).resolve().parents[2]
PROJECT, PROFILE, REQUIREMENT = "AlienLogicLab/alienintent", "fx-u4", "SF-REQ-014"
MAPPING = "docs/evidence/wo-220204-fx-u4-predicate-mapping.json"
MAPPING_SHA256 = "aed79fa4dcb1bed44b493b015b0a3e14e1d042fcc24d3dab3c76856874aae00c"
PREMISE_MAPPING = "docs/evidence/wo-220203-fx-u3-premise-mapping.json"
PREMISE_SHA256 = "598abb9c11791428069e2b5605b51f7ebf61afd537f2ca02c39e6bc8ec1bd589"
RETAINED = ("docs/evidence/py09b-live-checks-2026-09-21.json", "docs/evidence/py10/proof-run.json")
SPECIFICATION, DESIGN = "docs/evidence/wave2-specified-requirements.json", "docs/evidence/wave2-design-contracts.json"
REVISION = "sha256:898c6bff3c7b2dab7257a9a416925af1034966b0e433aa6f93fe5dfe39b3c93d"
REVIEWER, SUPERSEDER = "POSTW1-VERIFY-010", "Founder"
AC = {n: f"{REQUIREMENT}/SF-REQ-014-AC-0{n}/" for n in range(1, 5)}
AC1, AC2, AC3 = AC[1] + "pinned-before-implementation", AC[2] + "qualified-control", AC[3] + "four-part-isolation"
AC4, JUDGMENT = AC[4] + "judgment-attribution-and-coverage", AC[4] + "mapping-faithfulness-judgment"
PROOF_MODULES = tuple("src/alienintent/evidence_learning/" + m for m in (
    "domain/proof_plan.py", "domain/battery.py", "domain/proof_order.py", "domain/repair.py",
    "ports/proof_planning.py", "application/proof_planning_service.py"))


def ref(name: str) -> Ref:
    return Ref(PROJECT, PROFILE, name, "sha256:" + sha256(name.encode()).hexdigest(), "fixture:" + name)


def run(phase, exit_status=0, applications=0, failed=(), errors=()):
    return ControlRun(phase, exit_status, applications, tuple(failed), tuple(errors))


def mechanical(acceptance: str, key: str, **changes) -> MappedPredicate:
    return replace(MappedPredicate(acceptance, key, PredicateKind.MECHANICAL, "statement", ("docs/spec.md#" + acceptance,),
                                   "FX", ("input",), "expected", "endpoint", "command", ("obligation_id",), "guard"),
                   **changes)


class ProofPlanDomainTests(unittest.TestCase):
    """Pure domain rules; these stay green when the composed caller is disconnected."""

    def requirement(self):
        return RequirementRevision(REQUIREMENT, ("A1", "A2"), ref("requirement"))

    def mapping(self, *predicates):
        return PredicateMapping(ref("mapping"), REQUIREMENT, ref("requirement").revision_digest,
                                ref("design").revision_digest, REVIEWER, ref("review"), tuple(predicates))

    def derive(self, mapping, prior=None):
        return derive_plan(self.requirement(), ref("design"), mapping, None, prior, REVIEWER, SUPERSEDER, ("src", "tests"))

    def test_domain_plan_links_every_obligation_to_the_requirement_revision(self):
        plan = self.derive(self.mapping(mechanical("A1", "k"), mechanical("A2", "k")))
        self.assertIsInstance(plan, ProofPlan)
        self.assertEqual({o.requirement_revision for o in plan.obligations}, {ref("requirement").revision_digest})
        self.assertEqual([o.obligation_id for o in plan.obligations], [f"{REQUIREMENT}/A1/k", f"{REQUIREMENT}/A2/k"])

    def test_obligation_revision_hashes_expected_inputs(self):
        first = self.derive(self.mapping(mechanical("A1", "k"), mechanical("A2", "k")))
        second = self.derive(self.mapping(mechanical("A1", "k", expected="other"), mechanical("A2", "k")))
        self.assertEqual(first.obligations[0].obligation_id, second.obligations[0].obligation_id)
        self.assertNotEqual(first.obligations[0].revision, second.obligations[0].revision)

    def test_unreviewed_mapping_and_other_design_hold(self):
        mapping = self.mapping(mechanical("A1", "k"), mechanical("A2", "k"))
        self.assertEqual(self.derive(replace(mapping, reviewer="PRODUCER")).reason_code, "UNREVIEWED_MAPPING")
        self.assertEqual(self.derive(replace(mapping, design_revision=ref("x").revision_digest)).reason_code, "DESIGN_MISMATCH")
        self.assertEqual(self.derive(self.mapping(mechanical("A1", "k"), mechanical("A9", "k"))).reason_code, "UNKNOWN_ACCEPTANCE")
        self.assertEqual(self.derive(self.mapping(mechanical("A1", "k"), mechanical("A1", "k"), mechanical("A2", "k"))).reason_code,
                         "DUPLICATE_OBLIGATION")

    def test_isolation_predicate_without_premise_reader_holds(self):
        isolation = mechanical("A2", "iso", kind=PredicateKind.PLATFORM_ISOLATION, premise_id="p",
                               premise_observables=("POSITIVE_TARGET_ACCESS",))
        result = self.derive(self.mapping(mechanical("A1", "k"), isolation))
        self.assertEqual(result.reason_code, "PREMISE_EVIDENCE_UNAVAILABLE")

    def test_battery_qualifies_a_discriminating_kill(self):
        verdict = evaluate_control("o", "g", "test_a", (run("intact"), run("fault", 1, 1, ["test_a"]), run("restored")))
        self.assertTrue(verdict.qualified)
        self.assertEqual(verdict.reason, "QUALIFIED_KILL")

    def test_battery_refuses_unconditional_success(self):
        verdict = evaluate_control("o", "g", "test_a", (run("intact"), run("fault", 0, 1), run("restored")))
        self.assertEqual(verdict.reason, "UNCONDITIONAL_SUCCESS")
        self.assertFalse(verdict.qualified)

    def test_battery_refuses_zero_application(self):
        verdict = evaluate_control("o", "g", "test_a", (run("intact"), run("fault", 1, 0, ["test_a"]), run("restored")))
        self.assertEqual(verdict.reason, "ZERO_APPLICATION")
        self.assertFalse(verdict.qualified)

    def test_battery_refuses_overdetermined_kill(self):
        for fault in (run("fault", 1, 2, ["test_a"]), run("fault", 1, 1, ["test_a", "test_b"])):
            verdict = evaluate_control("o", "g", "test_a", (run("intact"), fault, run("restored")))
            self.assertEqual(verdict.reason, "OVERDETERMINED")
            self.assertFalse(verdict.qualified)

    def test_battery_refuses_unrelated_failure(self):
        for fault in (run("fault", None, 1), run("fault", 1, 1, ["test_a"], ["ImportError"]), run("fault", 1, 1, ["test_b"])):
            verdict = evaluate_control("o", "g", "test_a", (run("intact"), fault, run("restored")))
            self.assertEqual(verdict.reason, "UNRELATED_FAILURE")
            self.assertFalse(verdict.qualified)

    def test_battery_refuses_unclean_or_missing_phases(self):
        fault = run("fault", 1, 1, ["test_a"])
        self.assertEqual(evaluate_control("o", "g", "test_a", (run("intact", 1), fault, run("restored"))).reason, "INTACT_NOT_CLEAN")
        self.assertEqual(evaluate_control("o", "g", "test_a", (run("intact"), fault, run("restored", 1))).reason, "RESTORED_NOT_CLEAN")
        self.assertEqual(evaluate_control("o", "g", "test_a", (run("intact"), fault)).reason, "MISSING_PHASE")

    def steps(self):
        plan, intact = ProofStep(ref("plan"), "plan", None, (), "o"), ProofStep(ref("i"), "intact", "c", (ref("plan"),), "o")
        fault = ProofStep(ref("f"), "fault", "c", (ref("i"),), "o")
        return plan, intact, fault, ProofStep(ref("r"), "restored", "c", (ref("f"),), "o")

    def test_ordered_control_is_clean(self):
        self.assertEqual(proof_order_diagnostics(self.steps()), ())

    def test_out_of_order_evidence_is_diagnosed(self):
        plan, intact, fault, restored = self.steps()
        early = replace(fault, preceding=(ref("plan"),))
        names = {d.name for d in proof_order_diagnostics((plan, intact, early, replace(restored, preceding=(ref("i"),))))}
        self.assertIn("proof-order/fault-before-intact", names)
        self.assertIn("proof-order/restored-before-fault", names)
        self.assertTrue(all(d.strength == "ADVISORY" for d in proof_order_diagnostics((plan, intact, early))))

    def test_missing_plan_ancestry_is_diagnosed(self):
        plan, intact, fault, restored = self.steps()
        orphan = replace(intact, preceding=(ref("absent"),))
        names = [d.name for d in proof_order_diagnostics((plan, orphan, fault, restored))]
        self.assertIn("proof-order/missing-plan-ancestry", names)
        self.assertIn("proof-order/unresolved-ancestor", names)


class ProofPlanningTests(unittest.TestCase):
    """Composed through UpstreamProfile over a real temporary SQLite store and evidence root."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fx-u4-"))
        self.addCleanup(shutil.rmtree, self.tmp)
        self.root, self.state = self.tmp / "retained", self.tmp / "state"
        for path in (MAPPING, PREMISE_MAPPING, *RETAINED):
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, self.root / path)
        self.mapping_sha256 = MAPPING_SHA256
        self.state.mkdir()

    def profile(self) -> UpstreamProfile:
        contract = Ref(PROJECT, PROFILE, "FX-U4-contract", "sha256:" + "0" * 64, "repository:docs/evidence/wo-220204-fx-u4.md")
        return UpstreamProfile(
            LocalEvidenceRepository(self.state / "evidence", PROJECT, PROFILE),
            SQLiteOperationalStore(self.state / "operational.sqlite"), PROJECT, PROFILE, contract, "fx-u4-test", "Founder",
            frozenset({"private"}),
            premise_evidence=RetainedDoctorPremiseEvidence(self.root, Path(PREMISE_MAPPING), PREMISE_SHA256, PROJECT, PROFILE),
            premise_target="AlienLogicLab/alienintent-sandbox",
            proof_mappings=RetainedPredicateMapping(self.root, Path(MAPPING), self.mapping_sha256, PROJECT, PROFILE),
            mapping_reviewer=REVIEWER, supersession_authority=SUPERSEDER)

    def remap(self, change):
        """Change the mapping and repin it, modelling an authority re-review, so only the semantics differ."""
        mapping = json.loads((self.root / MAPPING).read_text())
        change(mapping)
        body = json.dumps(mapping).encode()
        (self.root / MAPPING).write_bytes(body)
        self.mapping_sha256 = sha256(body).hexdigest()

    def predicate(self, mapping, key):
        return next(p for p in mapping["predicates"] if p["predicate_key"] == key)

    def derive(self, requirement=None):
        profile = self.profile()
        self.assertIsNotNone(profile.proofs, "UpstreamProfile must compose ProofPlanning")
        requirement = requirement or retained_requirement_revision(ROOT, SPECIFICATION, REQUIREMENT, PROJECT, PROFILE)
        version, _ = profile.proofs.read(REQUIREMENT)
        return profile.proofs.derive(requirement, retained_design_ref(ROOT, DESIGN, REQUIREMENT, PROJECT, PROFILE), version)

    def assertHold(self, result, reason, *affected):
        self.assertIsInstance(result, PlanHold)
        self.assertNotIsInstance(result, ProofPlan)
        self.assertEqual(result.reason_code, reason)
        for item in affected:
            self.assertTrue(any(item in a for a in result.affected), (item, result.affected))

    def test_composed_profile_derives_and_persists_the_fx_u4_plan(self):
        plan = self.derive()
        self.assertIsInstance(plan, ProofPlan)
        self.assertEqual([o.obligation_id for o in plan.obligations], [AC1, AC2, AC3, AC4, JUDGMENT])
        self.assertEqual({o.requirement_revision for o in plan.obligations}, {REVISION})
        for obligation in plan.obligations:
            if obligation.predicate.kind is not PredicateKind.JUDGMENT:
                p = obligation.predicate
                self.assertTrue(all((p.inputs, p.expected, p.endpoint, p.command, p.evidence_schema, p.guard)))
        current = self.profile().proofs.current(REQUIREMENT)
        self.assertEqual(current, plan)
        self.assertEqual(current.digest, plan.digest)

    def test_incomplete_mechanical_obligation_holds(self):
        self.remap(lambda m: self.predicate(m, "pinned-before-implementation").update(command=""))
        self.assertHold(self.derive(), "INCOMPLETE_OBLIGATION", AC1 + ":command")
        self.assertIsNone(self.profile().proofs.current(REQUIREMENT))

    def test_mapping_for_another_requirement_revision_holds(self):
        self.remap(lambda m: m["requirement"].update(revision_digest="sha256:" + "1" * 64))
        self.assertHold(self.derive(), "REVISION_MISMATCH", "sha256:" + "1" * 64)
        self.assertIsNone(self.profile().proofs.current(REQUIREMENT))

    def test_implementation_derived_predicate_is_refused(self):
        self.remap(lambda m: self.predicate(m, "qualified-control").update(
            derived_from=["src/alienintent/evidence_learning/domain/battery.py"]))
        self.assertHold(self.derive(), "CIRCULAR_ORACLE", AC2)

    def test_composed_plan_pins_the_four_observable_premise(self):
        plan = self.derive()
        isolation = plan.obligation(AC3)
        self.assertEqual(set(isolation.predicate.premise_observables),
                         {"POSITIVE_TARGET_ACCESS", "PROFILE_SCOPING", "OUT_OF_SCOPE_REJECTION", "OUTSIDE_STATE_READBACK"})
        self.assertIn("repository:" + PREMISE_MAPPING, {r.locator for r in isolation.premise_refs})
        self.assertEqual({o.obligation_id for o in plan.obligations if o.premise_refs}, {AC3})

    def test_credential_denial_obligation_is_infeasible_proof(self):
        self.remap(lambda m: self.predicate(m, "four-part-isolation")["premise_observables"].append("CREDENTIAL_DENIAL"))
        result = self.derive()
        self.assertIsInstance(result, InfeasibleProof)
        self.assertNotIsInstance(result, ProofPlan)
        self.assertEqual(result.reason_code, "UNACHIEVABLE_PREMISE")
        self.assertIn("CREDENTIAL_DENIAL", result.missing)
        self.assertEqual(result.required_action, "return the premise to source authority")

    def test_isolation_obligation_omitting_an_observable_is_infeasible(self):
        self.remap(lambda m: self.predicate(m, "four-part-isolation")["premise_observables"].remove("OUTSIDE_STATE_READBACK"))
        result = self.derive()
        self.assertIsInstance(result, InfeasibleProof)
        self.assertEqual(result.reason_code, "INCOMPLETE_PREMISE_REQUEST")

    def test_unattributed_judgment_holds(self):
        self.remap(lambda m: self.predicate(m, "mapping-faithfulness-judgment").update(reviewer=""))
        self.assertHold(self.derive(), "UNATTRIBUTED_JUDGMENT", JUDGMENT)

    def test_judgment_claiming_mechanical_pass_is_refused(self):
        self.remap(lambda m: self.predicate(m, "mapping-faithfulness-judgment").update(command="true", expected="PASS"))
        self.assertHold(self.derive(), "JUDGMENT_CLAIMS_MECHANICAL_PASS", JUDGMENT)

    def test_judgment_obligation_names_reviewer_inputs_and_decision_record(self):
        judgment = self.derive().obligation(JUDGMENT).predicate
        self.assertEqual(judgment.kind, PredicateKind.JUDGMENT)
        self.assertTrue(judgment.reviewer and judgment.inspection_inputs and judgment.decision_record)
        self.assertEqual((judgment.command, judgment.expected), ("", ""))

    def test_removed_required_predicate_blocks_admission(self):
        first = self.derive()
        self.remap(lambda m: m["predicates"].remove(self.predicate(m, "four-part-isolation")))
        self.assertHold(self.derive(), "COVERAGE_HOLD", "SF-REQ-014-AC-03")
        self.assertEqual(self.profile().proofs.current(REQUIREMENT), first)

    def test_dropped_prior_obligation_holds(self):
        self.derive()
        self.remap(lambda m: m["predicates"].remove(self.predicate(m, "mapping-faithfulness-judgment")))
        self.assertHold(self.derive(), "PRIOR_OBLIGATION_DROPPED", JUDGMENT)

    def test_changed_judgment_reviewer_inputs_hold(self):
        self.derive()
        self.remap(lambda m: self.predicate(m, "mapping-faithfulness-judgment")["inspection_inputs"].pop())
        self.assertHold(self.derive(), "PRIOR_OBLIGATION_CHANGED", JUDGMENT)

    def supersede(self, authorized_by=SUPERSEDER):
        def change(mapping):
            self.predicate(mapping, "pinned-before-implementation").update(predicate_key="pinned-before-implementation-r2",
                                                                           expected="revised expected result")
            mapping["supersessions"].append({"prior_obligation_id": AC1, "replacement_obligation_id": AC1 + "-r2",
                                             "authorized_by": authorized_by, "reason": "authoritative predicate revision",
                                             "authority": {"path": MAPPING, "sha256": "2" * 64}})
        self.remap(change)

    def test_unauthorized_supersession_holds(self):
        self.derive()
        self.supersede(authorized_by="PRODUCER")
        self.assertHold(self.derive(), "UNAUTHORIZED_SUPERSESSION", AC1)

    def repaired(self, supersede=False):
        first = self.derive()
        if supersede:
            self.supersede()
        second = self.derive()
        self.assertIsInstance(second, ProofPlan)
        self.assertEqual(second.prior_plan_digest, first.digest)
        return second

    def replay(self, **changes):
        passed = {AC1: ReplayStatus.PASSED, AC2: ReplayStatus.PASSED, AC3: ReplayStatus.PASSED, AC4: ReplayStatus.PASSED}
        return {**passed, **changes}

    def test_replayed_prior_proof_is_accepted(self):
        self.repaired()
        accepted = self.profile().proofs.evaluate_repair(REQUIREMENT, self.replay())
        self.assertEqual(set(accepted.preserved), {AC1, AC2, AC3, AC4, JUDGMENT})

    def test_dropped_prior_proof_is_rejected(self):
        self.repaired()
        replay = self.replay()
        del replay[AC2]
        self.assertHold(self.profile().proofs.evaluate_repair(REQUIREMENT, replay), "PRIOR_PROOF_DROPPED", AC2)

    def test_skipped_prior_proof_is_rejected(self):
        self.repaired()
        self.assertHold(self.profile().proofs.evaluate_repair(REQUIREMENT, self.replay(**{AC2: ReplayStatus.SKIPPED})),
                        "PRIOR_PROOF_SKIPPED", AC2)

    def test_failed_prior_proof_is_rejected(self):
        self.repaired()
        self.assertHold(self.profile().proofs.evaluate_repair(REQUIREMENT, self.replay(**{AC2: ReplayStatus.FAILED})),
                        "PRIOR_PROOF_FAILED", AC2)

    def test_authorized_supersession_with_passing_replacement_is_accepted(self):
        plan = self.repaired(supersede=True)
        self.assertEqual([s.prior_obligation_id for s in plan.superseded], [AC1])
        accepted = self.profile().proofs.evaluate_repair(REQUIREMENT, self.replay(**{AC1 + "-r2": ReplayStatus.PASSED}))
        self.assertEqual(accepted.superseded, (AC1,))

    def test_supersession_without_passing_replacement_is_rejected(self):
        self.repaired(supersede=True)
        for status in (ReplayStatus.FAILED, ReplayStatus.SKIPPED):
            self.assertHold(self.profile().proofs.evaluate_repair(REQUIREMENT, self.replay(**{AC1 + "-r2": status})),
                            "REPLACEMENT_PROOF_MISSING", AC1)

    def test_recorded_proof_evidence_is_ordered_and_clean(self):
        plan = self.derive()
        proofs = self.profile().proofs
        _, state = proofs.read(REQUIREMENT)
        refs, previous = [Ref(**state["plan_ref"])], ()
        for phase, code in (("intact", 0), ("fault", 1), ("restored", 0)):
            recorded = proofs.record(AC2, ref("candidate"), "sha256:" + "3" * 64, "fx-u4-test", "exit 0", str(code), code,
                                     control="c", phase=phase, preceding=previous)
            self.assertIsInstance(recorded, Ref)
            refs.append(recorded)
            previous = (recorded,)
        self.assertEqual(proofs.proof_order(tuple(refs)), ())
        self.assertEqual(plan.digest, proofs.current(REQUIREMENT).digest)
        self.assertIn("proof-order/fault-before-intact", {d.name for d in proofs.proof_order((refs[0], refs[2]))})

    def test_evidence_for_an_unplanned_obligation_is_refused(self):
        self.derive()
        result = self.profile().proofs.record(AC1 + "-unplanned", ref("candidate"), "sha256:" + "3" * 64, "i", "e", "o", 0,
                                              control="c", phase="intact")
        self.assertHold(result, "UNPLANNED_OBLIGATION")

    def test_stale_expected_version_holds(self):
        self.derive()
        profile = self.profile()
        requirement = retained_requirement_revision(ROOT, SPECIFICATION, REQUIREMENT, PROJECT, PROFILE)
        self.assertHold(profile.proofs.derive(requirement, retained_design_ref(ROOT, DESIGN, REQUIREMENT, PROJECT, PROFILE), 0),
                        "STALE_INPUT")

    def test_unpinned_or_malformed_mapping_holds_without_raising(self):
        self.mapping_sha256 = "0" * 64
        self.assertHold(self.derive(), "MAPPING_UNAVAILABLE", "digest mismatch")
        for change in (lambda m: m.update(predicates="x"), lambda m: m["predicates"][0].update(kind="GUESS"),
                       lambda m: m["predicates"][0].update(inputs=[1]), lambda m: m.pop("review"),
                       lambda m: m["supersessions"].append({"prior_obligation_id": AC1})):
            self.setUp()
            self.remap(change)
            self.assertHold(self.derive(), "MAPPING_UNAVAILABLE")

    def test_tampered_persisted_plan_is_refused(self):
        self.derive()
        profile = self.profile()
        version, state = profile.proofs.read(REQUIREMENT)
        profile.proofs.store.commit(PROFILE, profile.proofs.aggregate(REQUIREMENT), version,
                                    {**state, "plan_digest": "sha256:" + "4" * 64})
        self.assertHold(self.profile().proofs.current(REQUIREMENT), "PERSISTED_PLAN_INVALID")

    def test_proof_modules_import_no_installation_composition_or_context_assembly(self):
        forbidden = ("alienintent.installation", "alienintent.composition", "alienintent.context_assembly")
        for module in PROOF_MODULES:
            tree = ast.parse((ROOT / module).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertEqual(node.level, 0, module)
                    names = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
                elif isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                else:
                    continue
                for name in names:
                    self.assertFalse(any(name == f or name.startswith(f + ".") for f in forbidden), (module, name))


if __name__ == "__main__":
    unittest.main()
