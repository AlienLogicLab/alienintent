"""FX-U3 assertions: retained doctor evidence becomes a neutral isolation premise or InfeasibleProof."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from alienintent.composition.premise_evidence import RetainedDoctorPremiseEvidence
from alienintent.composition.upstream_profile import UpstreamProfile
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.premise import (
    ISOLATION_OBSERVABLES, InfeasibleProof, IsolationObservable, PlatformIsolationPremise)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

ROOT = Path(__file__).resolve().parents[2]
MAPPING = Path("docs/evidence/wo-220203-fx-u3-premise-mapping.json")
PY09B, PY10 = "docs/evidence/py09b-live-checks-2026-09-21.json", "docs/evidence/py10/proof-run.json"
PROJECT, PROFILE, TARGET, PREMISE = "AlienLogicLab/alienintent", "fx-u3", "AlienLogicLab/alienintent-sandbox", "platform-isolation:wave1-sandbox"
MAPPING_SHA256 = "8f6c9f063a934a8c63ea724fb1c554154cdd6bf8a70b250a0d06d09480b2ba23"
PREMISE_MODULES = ("src/alienintent/evidence_learning/domain/premise.py",
                   "src/alienintent/evidence_learning/ports/premise_evidence.py",
                   "src/alienintent/evidence_learning/application/premise_service.py")


class PremiseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fx-u3-"))
        self.addCleanup(shutil.rmtree, self.tmp)
        self.mapping_sha256 = MAPPING_SHA256

    def profile(self, root: Path, target: str = TARGET) -> UpstreamProfile:
        state = Path(tempfile.mkdtemp(prefix="state-", dir=self.tmp))
        definition = Ref(PROJECT, PROFILE, "FX-U3-contract", "sha256:" + "0" * 64, "repository:docs/evidence/wo-220203-fx-u3.md")
        return UpstreamProfile(LocalEvidenceRepository(state / "evidence", PROJECT, PROFILE),
                               SQLiteOperationalStore(state / "operational.sqlite"), PROJECT, PROFILE, definition,
                               "fx-u3-test", "Founder", frozenset({"private"}),
                               premise_evidence=RetainedDoctorPremiseEvidence(root, MAPPING, self.mapping_sha256, PROJECT, PROFILE),
                               premise_target=target)

    def copy(self) -> Path:
        root = self.tmp / "retained"
        for path in (MAPPING, Path(PY09B), Path(PY10)):
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, root / path)
        return root

    def rewrite(self, root: Path, key: str, path: str, change, repin=True):
        """Change a retained artifact; repin models a re-pinned mapping so only the semantics differ."""
        document = json.loads((root / path).read_text())
        change(document)
        body = json.dumps(document, indent=1).encode()
        (root / path).write_bytes(body)
        if repin:
            self.remap(root, lambda m: m["artifacts"][key].update(sha256=sha256(body).hexdigest()))

    def remap(self, root: Path, change, repin=True):
        """Change the mapping; repin models an authority re-review that pins the new mapping digest."""
        mapping = json.loads((root / MAPPING).read_text())
        change(mapping)
        body = json.dumps(mapping).encode()
        (root / MAPPING).write_bytes(body)
        if repin:
            self.mapping_sha256 = sha256(body).hexdigest()

    def read(self, root: Path, **kwargs):
        profile = self.profile(root)
        self.assertIsNotNone(profile.premises, "UpstreamProfile must compose the PremiseEvidence reader")
        return profile.premises.read(PREMISE, **kwargs)

    def assertInfeasible(self, result, reason, *missing):
        self.assertIsInstance(result, InfeasibleProof)
        self.assertNotIsInstance(result, PlatformIsolationPremise)
        self.assertEqual(result.reason_code, reason)
        for item in missing:
            self.assertIn(item, result.missing)
        self.assertEqual(result.required_action, "return the premise to source authority")

    def test_composed_profile_reads_retained_doctor_evidence_as_isolation_premise(self):
        before = {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in (PY09B, PY10, str(MAPPING))}
        result = self.read(ROOT)
        self.assertIsInstance(result, PlatformIsolationPremise)
        self.assertEqual((result.premise_id, result.target), (PREMISE, TARGET))
        self.assertEqual(len(result.observations), 8)
        self.assertEqual({o.observable for o in result.observations}, set(ISOLATION_OBSERVABLES))
        self.assertTrue(all(o.satisfied is True and o.target == TARGET for o in result.observations))
        digests = {o.source_ref.logical_id: o.source_ref.revision_digest for o in result.observations}
        self.assertEqual(digests, {"py09b-live-checks": "sha256:526435a058a7b5d68c1c504fd18015e6d3fa87da9356d7b7555a564b21acffaf",
                                   "py10-proof-run": "sha256:d8fa0efab6bec2b26f6da129bb6c7be0e93473c37ee8e0ebd199fdfe60ec5358"})
        self.assertEqual(result.mapping_ref.revision_digest, "sha256:" + MAPPING_SHA256)
        self.assertEqual(result.doctor_ref.locator,
                         "repository:" + PY09B + "#doctor_returns_typed_outcomes_against_the_sandbox")
        rejection = [o.predicate for o in result.observations if o.observable == IsolationObservable.OUT_OF_SCOPE_REJECTION]
        self.assertEqual(rejection, ["project_identity_resolution_fails_closed_on_mismatch", "delivery_for_another_project_is_refused"])
        self.assertEqual(before, {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in before})

    def test_missing_outside_state_artifact_is_infeasible_proof(self):
        root = self.copy()
        (root / PY10).unlink()
        self.assertInfeasible(self.read(root), "MISSING_PREMISE", "OUTSIDE_STATE_READBACK", "artifact:py10-proof-run")

    def test_tampered_artifact_fails_its_digest_pin(self):
        root = self.copy()
        self.rewrite(root, "py10-proof-run", PY10, lambda d: d.update(repository=TARGET), repin=False)
        self.assertInfeasible(self.read(root), "MISSING_PREMISE", "artifact:py10-proof-run")

    def test_absent_mapped_check_is_a_missing_premise(self):
        root = self.copy()
        self.rewrite(root, "py09b-live-checks", PY09B, lambda d: d.update(
            checks=[c for c in d["checks"] if c["check"] != "delivery_for_another_project_is_refused"]))
        self.assertInfeasible(self.read(root), "MISSING_PREMISE", "predicate:delivery_for_another_project_is_refused")

    def test_failed_out_of_scope_rejection_is_unsatisfied(self):
        root = self.copy()

        def fail(document):
            for check in document["checks"]:
                if check["check"] == "project_identity_resolution_fails_closed_on_mismatch":
                    check["ok"] = False
        self.rewrite(root, "py09b-live-checks", PY09B, fail)
        self.assertInfeasible(self.read(root), "UNSATISFIED_PREMISE", "OUT_OF_SCOPE_REJECTION")

    def test_changed_outside_state_is_unsatisfied(self):
        root = self.copy()
        self.rewrite(root, "py10-proof-run", PY10,
                     lambda d: d["after"]["production_project"].update(state_digest="sha256:" + "1" * 64))
        result = self.read(root)
        self.assertInfeasible(result, "UNSATISFIED_PREMISE", "OUTSIDE_STATE_READBACK")
        self.assertEqual(result.missing, ("OUTSIDE_STATE_READBACK",))

    def test_unobserved_outside_state_is_unsatisfied(self):
        root = self.copy()

        def unobserved(document):
            document["before"]["production_project"]["observed"] = False
            document["after"]["production_project"]["observed"] = False
        self.rewrite(root, "py10-proof-run", PY10, unobserved)
        self.assertInfeasible(self.read(root), "UNSATISFIED_PREMISE", "OUTSIDE_STATE_READBACK")

    def test_doctor_evidence_that_is_not_a_full_pass_is_infeasible(self):
        for outcomes in ({"configuration": "PASS"}, {**{c: "PASS" for c in (
                "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence")},
                "execution": "FAIL"}):
            with self.subTest(outcomes=outcomes):
                root = self.copy()

                def doctor(document, outcomes=outcomes):
                    for check in document["checks"]:
                        if check["check"] == "doctor_returns_typed_outcomes_against_the_sandbox":
                            check["detail"] = "disposition=PASS exit=0 outcomes=" + json.dumps(outcomes)
                self.rewrite(root, "py09b-live-checks", PY09B, doctor)
                self.assertInfeasible(self.read(root), "DOCTOR_EVIDENCE_UNAVAILABLE", "installation-doctor")
                shutil.rmtree(root)

    def test_evidence_for_another_target_is_a_target_mismatch(self):
        root = self.copy()
        self.rewrite(root, "py10-proof-run", PY10, lambda d: d.update(repository="AlienLogicLab/alienintent"))
        self.assertInfeasible(self.read(root), "TARGET_MISMATCH", "AlienLogicLab/alienintent")

    def test_configured_target_must_match_the_retained_target(self):
        profile = self.profile(ROOT, target="AlienLogicLab/alienintent")
        self.assertInfeasible(profile.premises.read(PREMISE), "TARGET_MISMATCH", TARGET)

    def test_credential_denial_premise_is_unachievable_not_waived(self):
        requested = frozenset(o.value for o in ISOLATION_OBSERVABLES) | {"CREDENTIAL_DENIAL"}
        self.assertInfeasible(self.read(ROOT, requested=requested), "UNACHIEVABLE_PREMISE", "CREDENTIAL_DENIAL")
        partial = frozenset(o.value for o in ISOLATION_OBSERVABLES) - {"OUTSIDE_STATE_READBACK"}
        self.assertInfeasible(self.read(ROOT, requested=partial), "INCOMPLETE_PREMISE_REQUEST", "OUTSIDE_STATE_READBACK")
        self.assertFalse(any("DENIAL" in o.value for o in IsolationObservable))

    def test_premise_modules_import_no_installation_or_composition(self):
        for path in PREMISE_MODULES:
            tree = ast.parse((ROOT / path).read_text())
            modules = ["." * n.level + (n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            modules += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
            for module in modules:
                with self.subTest(path=path, module=module):
                    self.assertFalse({"installation", "composition"} & set(module.split(".")))

    def test_premise_id_is_bound_to_the_pinned_mapping(self):
        profile = self.profile(ROOT)
        self.assertInfeasible(profile.premises.read("credential-denial:production"), "PREMISE_MISMATCH", PREMISE)

    def test_unpinned_or_missing_mapping_is_infeasible(self):
        root = self.copy()
        self.remap(root, lambda m: m["observables"].__setitem__(slice(None), m["observables"][:1] * 4), repin=False)
        self.assertInfeasible(self.read(root), "MAPPING_UNAVAILABLE", "predicate-mapping")
        (root / MAPPING).unlink()
        self.assertInfeasible(self.read(root), "MAPPING_UNAVAILABLE", "mapping:" + str(MAPPING))

    def test_malformed_mapping_is_infeasible_not_an_exception(self):
        changes = {
            "credential-denial-observable": lambda m: m["observables"].append(
                {"observable": "CREDENTIAL_DENIAL", "artifact": "py09b-live-checks", "check": "x"}),
            "undeclared-artifact": lambda m: m["observables"][3].update(artifact="py09b-typo"),
            "entry-without-predicate": lambda m: m["observables"][0].pop("check"),
            "no-doctor": lambda m: m.pop("doctor"),
            "not-an-object": lambda m: m.clear(),
        }
        for name, change in changes.items():
            with self.subTest(name=name):
                root = self.copy()
                self.remap(root, change)
                self.assertInfeasible(self.read(root), "MAPPING_UNAVAILABLE", "predicate-mapping")
                shutil.rmtree(root)

    def test_null_or_empty_readback_is_not_an_unchanged_state(self):
        for value in (None, "", {}, []):
            with self.subTest(value=value):
                root = self.copy()

                def blank(document, value=value):
                    for side in ("before", "after"):
                        for field in ("state_digest", "identity_digest", "project_updated_at"):
                            document[side]["production_project"][field] = value
                        document[side]["node_bootstrap"]["bootstrap_port_answers"] = value
                self.rewrite(root, "py10-proof-run", PY10, blank)
                self.assertInfeasible(self.read(root), "UNSATISFIED_PREMISE", "OUTSIDE_STATE_READBACK")
                shutil.rmtree(root)

    def test_vacuous_out_of_scope_refusal_is_unsatisfied(self):
        root = self.copy()

        def vacuous(document):
            for check in document["checks"]:
                if check["check"] == "delivery_for_another_project_is_refused":
                    check["detail"] = "no recorded delivery for another Project was available to replay in this run"
        self.rewrite(root, "py09b-live-checks", PY09B, vacuous)
        self.assertInfeasible(self.read(root), "UNSATISFIED_PREMISE", "OUT_OF_SCOPE_REJECTION")

    def test_malformed_doctor_or_target_evidence_is_infeasible_not_an_exception(self):
        cases = {
            "null-detail": ("doctor_returns_typed_outcomes_against_the_sandbox", None, "DOCTOR_EVIDENCE_UNAVAILABLE"),
            "duplicate-outcome": ("doctor_returns_typed_outcomes_against_the_sandbox",
                                  'disposition=PASS exit=0 outcomes={"configuration": "FAIL", '
                                  + ", ".join(f'"{c}": "PASS"' for c in ("configuration", "secrets", "work_management",
                                  "source_control", "provider", "transport", "persistence", "execution"))
                                  + "}", "DOCTOR_EVIDENCE_UNAVAILABLE"),
        }
        for name, (check_name, detail, reason) in cases.items():
            with self.subTest(name=name):
                root = self.copy()

                def change(document, check_name=check_name, detail=detail):
                    for check in document["checks"]:
                        if check["check"] == check_name:
                            check["detail"] = detail
                self.rewrite(root, "py09b-live-checks", PY09B, change)
                self.assertInfeasible(self.read(root), reason)
                shutil.rmtree(root)

    def test_unreadable_artifact_target_is_a_missing_premise(self):
        for value in ("", None, 5):
            with self.subTest(value=value):
                root = self.copy()
                self.rewrite(root, "py10-proof-run", PY10, lambda d, value=value: d.update(repository=value))
                self.assertInfeasible(self.read(root), "MISSING_PREMISE", "target:py10-proof-run", "OUTSIDE_STATE_READBACK")
                shutil.rmtree(root)

    def test_premise_evidence_requires_a_configured_target(self):
        with self.assertRaises(ValueError):
            UpstreamProfile(LocalEvidenceRepository(self.tmp / "e", PROJECT, PROFILE), SQLiteOperationalStore(self.tmp / "s.sqlite"),
                            PROJECT, PROFILE, Ref(PROJECT, PROFILE, "c", "sha256:" + "0" * 64, "repository:c"), "fx-u3-test",
                            "Founder", frozenset({"private"}),
                            premise_evidence=RetainedDoctorPremiseEvidence(ROOT, MAPPING, MAPPING_SHA256, PROJECT, PROFILE))


if __name__ == "__main__":
    unittest.main()
