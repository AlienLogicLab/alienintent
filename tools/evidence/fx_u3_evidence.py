#!/usr/bin/env python3
"""FX-U3 intact/fault/restored discrimination using isolated source copies."""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import Header, Observation
from alienintent.evidence_learning.domain.refs import Ref

ROOT = Path(__file__).resolve().parents[2]
INVOCATION = "AlienLogicLab/alienintent#81:PRODUCER:b2ddac1f-5d65-45bc-9511-5e8996123534"
BASELINE = "06e7e0c1f384e29c304788b11e0e559d8bdacc73"
CONTRACT = "docs/evidence/wo-220203-fx-u3.md"
MAPPING = "docs/evidence/wo-220203-fx-u3-premise-mapping.json"
RETAINED = ("docs/evidence/py09b-live-checks-2026-09-21.json", "docs/evidence/py10/proof-run.json")
DOMAIN = "src/alienintent/evidence_learning/domain/premise.py"
ADAPTER = "src/alienintent/composition/premise_evidence.py"
PROFILE = "src/alienintent/composition/upstream_profile.py"
TEST = "tests.evidence_learning.test_premise_evidence.PremiseEvidenceTests."
CONTROLS = [
    ("missing-observable-accepted", DOMAIN, "if missing or evidence.unavailable:", "if False:",
     "test_missing_outside_state_artifact_is_infeasible_proof"),
    ("unsatisfied-observation-accepted", DOMAIN, "if unsatisfied:", "if False:",
     "test_failed_out_of_scope_rejection_is_unsatisfied"),
    ("digest-pin-removed", ADAPTER, 'if sha256(body).hexdigest() != spec["sha256"]:', "if False:",
     "test_tampered_artifact_fails_its_digest_pin"),
    ("target-binding-removed", DOMAIN, "if mismatched:", "if False:",
     "test_evidence_for_another_target_is_a_target_mismatch"),
    ("credential-denial-premise-accepted", DOMAIN, "if unachievable:", "if False:",
     "test_credential_denial_premise_is_unachievable_not_waived"),
    ("doctor-precondition-removed", DOMAIN, "if not evidence.doctor_passed or evidence.doctor_ref is None:",
     "if evidence.doctor_ref is None:", "test_doctor_evidence_that_is_not_a_full_pass_is_infeasible"),
    ("doctor-required-checks-removed", ADAPTER,
     ' \\\n            and set(outcomes) == set(REQUIRED_CHECKS) and all(v == "PASS" for v in outcomes.values())', "",
     "test_doctor_evidence_that_is_not_a_full_pass_is_infeasible"),
    ("outside-state-comparison-removed", ADAPTER,
     "satisfied = all(_read_back(b) and b == a for _, b, a in pairs)", "satisfied = all(_read_back(b) for _, b, a in pairs)",
     "test_changed_outside_state_is_unsatisfied"),
    ("absent-check-invented", ADAPTER, "            if check is None:\n                return None\n",
     '            if check is None:\n                check = {"ok": True}\n',
     "test_absent_mapped_check_is_a_missing_premise"),
    ("composition-disconnected", PROFILE, "if premise_evidence is not None and premise_target is not None else None)",
     "if False else None)", "test_composed_profile_reads_retained_doctor_evidence_as_isolation_premise"),
    ("premise-bridge-import-added", DOMAIN, "from alienintent.evidence_learning.domain.refs import Ref\n",
     "from alienintent.evidence_learning.domain.refs import Ref\nfrom alienintent.installation.application.doctor import REQUIRED_CHECKS\n",
     "test_premise_modules_import_no_installation_or_composition"),
    # Revision 1: controls for the independent-review repairs.
    ("premise-identity-unbound", DOMAIN, "if evidence.premise_id != premise_id:", "if False:",
     "test_premise_id_is_bound_to_the_pinned_mapping"),
    ("mapping-pin-removed", ADAPTER, "if sha256(body).hexdigest() != self._mapping_sha256:", "if False:",
     "test_unpinned_or_missing_mapping_is_infeasible"),
    ("mapping-validation-removed", ADAPTER, "if not _valid_mapping(mapping):", "if not isinstance(mapping, dict):",
     "test_malformed_mapping_is_infeasible_not_an_exception"),
    ("empty-readback-accepted", ADAPTER, "if value is _ABSENT or value is None or value is False:",
     "if value is _ABSENT or value is False:", "test_null_or_empty_readback_is_not_an_unchanged_state"),
    ("detail-predicate-removed", ADAPTER, ' and all(s in detail for s in entry.get("detail_requires", ()))', "",
     "test_vacuous_out_of_scope_refusal_is_unsatisfied"),
    ("duplicate-key-accepted", ADAPTER, "if len(keys) != len(set(keys)):", "if False:",
     "test_malformed_doctor_or_target_evidence_is_infeasible_not_an_exception"),
    ("absent-target-accepted", ADAPTER, "elif loaded[2] is None:", "elif False:",
     "test_unreadable_artifact_target_is_a_missing_premise"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", default=INVOCATION)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    repository = LocalEvidenceRepository(args.output/"evidence", "AlienLogicLab/alienintent", "fx-u3")
    contract = ROOT/CONTRACT
    definition_ref = Ref("AlienLogicLab/alienintent", "fx-u3", "FX-U3-contract",
                         "sha256:"+sha256(contract.read_bytes()).hexdigest(), "repository:"+CONTRACT)
    observations = []

    def run(root, name, phase, test, applications):
        cmd = [sys.executable, "-m", "unittest", TEST+test, "-v"]
        env = dict(os.environ, PYTHONPATH=str(root/"src")+os.pathsep+str(root), PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(cmd, cwd=root, env=env, capture_output=True, timeout=120)
        raw = completed.stdout + completed.stderr
        filename = name+"-"+phase+".log"
        (args.output/filename).write_bytes(raw)
        expected = "nonzero assertion failure" if phase == "fault" else "exit 0"
        observation = {"schema_version": 1, "fixture": "FX-U3", "control": name, "phase": phase,
                       "command": cmd, "expected": expected, "exit_status": completed.returncode,
                       "raw_output_sha256": sha256(raw).hexdigest(), "raw_output": filename,
                       "application_count": applications}
        logical = name+"/"+phase
        value = json.dumps(observation, sort_keys=True)
        record = Observation(Header("AlienLogicLab/alienintent", "fx-u3", logical, sha256(value.encode()).hexdigest(),
                                    (definition_ref,), "private"), definition_ref, logical, "python-unittest-real-mutated-copy",
                             (), value, None, "Morty", args.invocation, "sha256:"+sha256(raw).hexdigest())
        observation["observation_ref"] = asdict(repository.put(record))
        observations.append(observation)
        print(name, phase, completed.returncode, flush=True)
        return completed.returncode, raw

    with tempfile.TemporaryDirectory(prefix="fx-u3-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT/"src", root/"src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT/"tests", root/"tests", ignore=shutil.ignore_patterns("__pycache__"))
        for path in (MAPPING, *RETAINED):
            (root/path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/path, root/path)
        outcomes = []
        for name, path, old, new, test in CONTROLS:
            target = root/path
            original = target.read_text()
            count = original.count(old)
            if count != 1:
                raise RuntimeError(f"{name}: expected exactly one mutation site, got {count}")
            intact, _ = run(root, name, "intact", test, 0)
            target.write_text(original.replace(old, new))
            fault, raw = run(root, name, "fault", test, count)
            target.write_text(original)
            restored, _ = run(root, name, "restored", test, 0)
            outcomes.append({"control": name, "test": test, "discriminated": intact == 0 and fault != 0 and b"FAIL:" in raw and restored == 0})
    report = {"schema_version": 1, "fixture": "FX-U3", "baseline": BASELINE, "invocation": args.invocation,
              "candidate_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "contract_sha256": sha256(contract.read_bytes()).hexdigest(),
              "mapping_sha256": sha256((ROOT/MAPPING).read_bytes()).hexdigest(),
              "retained_artifacts": {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in RETAINED},
              "implementation_files": {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in (
                  DOMAIN, "src/alienintent/evidence_learning/ports/premise_evidence.py",
                  "src/alienintent/evidence_learning/application/premise_service.py", ADAPTER, PROFILE,
                  "tests/evidence_learning/test_premise_evidence.py")},
              "tokens": None, "cost": None, "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable",
              "controls": outcomes, "observations": observations, "verdict": "independent verifier pending"}
    (args.output/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    return 0 if all(o["discriminated"] for o in outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
