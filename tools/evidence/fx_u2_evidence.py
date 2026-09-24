#!/usr/bin/env python3
"""FX-U2 intact/fault/restored discrimination using isolated source copies."""
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
INVOCATION = "AlienLogicLab/alienintent#80:PRODUCER:fe10b943-9ca2-450f-9478-88103cf9fd1b"
BASELINE = "ec9645adc4013c83b405f9080dde3215af90dcb5"
DOMAIN = "src/alienintent/context_assembly/domain/ambiguity.py"
APP = "src/alienintent/context_assembly/application/ambiguity_service.py"
ADAPTER = "src/alienintent/context_assembly/adapters/decision_resolution.py"
TEST = "tests.context_assembly.test_ambiguity.AmbiguityTests."
AC01 = "test_missing_fields_and_conflicting_sources_open_source_linked_questions"
AC02 = "test_only_matching_attributed_decision_resolves_that_question"
AC03 = "test_complete_requirement_passes_and_semantic_review_holds_without_editing_intent"
AC04 = "test_unrelated_requirement_stays_preparable_and_no_worker_launches"
CONTROLS = [
    ("revision-matching-removed", APP, 'if last["status"] == STALE or input_revision != finding.requirement_revision:',
     'if last["status"] == STALE:', AC02),
    ("authority-matching-removed", ADAPTER, 'if submission.actor != finding.required_actor or event.actor != submission.actor:',
     'if False:', AC02),
    ("unattributed-answer-accepted", ADAPTER, 'if recorded != decision:', 'if False:', AC02),
    ("stale-transition-removed", APP, 'if fid not in current and prior[fid] != STALE:', 'if False:', AC02),
    ("resolve-applies-to-every-finding", APP,
     'findings = {**state["findings"], finding_id: {**entry, "history": entry["history"] + [event]}}',
     'findings = {fid: {**e, "history": e["history"] + [event]} for fid, e in state["findings"].items()}', AC02),
    ("missing-intent-rule-disabled", DOMAIN, 'if not present.get("Intent"):', 'if False:', AC01),
    ("scope-conflict-rule-disabled", DOMAIN, 'if scope & {i.casefold() for i in _items(present.get("Non-goals", ""))}:',
     'if False:', AC01),
    ("acceptance-placeholder-accepted", DOMAIN, 'if not match or match[1].strip().rstrip(".").casefold() in PLACEHOLDERS:',
     'if not match:', AC01),
    ("conflicting-sources-ignored", DOMAIN, 'rules = (("CONFLICTING_SOURCES",) if requirement_id in snapshot.conflicts',
     'rules = (() if requirement_id in snapshot.conflicts', AC01),
    ("semantic-finding-not-holding", DOMAIN,
     'for f in own if statuses.get(f.finding_id, OPEN) != RESOLVED]',
     'for f in own if f.origin == "MECHANICAL" and statuses.get(f.finding_id, OPEN) != RESOLVED]', AC03),
    ("hold-propagates-globally", DOMAIN, 'blocked = sorted(entry["dependencies"] & held)', 'blocked = sorted(held)', AC04),
    ("worker-launch-injected", APP,
     '        return None  # Resuming preparation is a new validated operation and launches no worker.',
     '        import gc\n        [o.start() for o in gc.get_objects() if type(o).__name__ == "FactoryCoordinator"]', AC04),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", default=INVOCATION)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    repository = LocalEvidenceRepository(args.output/"evidence", "AlienLogicLab/alienintent", "fx-u2")
    contract = ROOT/"docs/evidence/wo-220202-fx-u2.md"
    definition_ref = Ref("AlienLogicLab/alienintent", "fx-u2", "FX-U2-contract",
                         "sha256:"+sha256(contract.read_bytes()).hexdigest(), "repository:docs/evidence/wo-220202-fx-u2.md")
    observations = []

    def run(root, name, phase, test, applications):
        cmd = [sys.executable, "-m", "unittest", TEST+test, "-v"]
        env = dict(os.environ, PYTHONPATH=str(root/"src")+os.pathsep+str(root), PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(cmd, cwd=root, env=env, capture_output=True, timeout=120)
        raw = completed.stdout + completed.stderr
        filename = name+"-"+phase+".log"
        (args.output/filename).write_bytes(raw)
        expected = "nonzero assertion failure" if phase == "fault" else "exit 0"
        observation = {"schema_version": 1, "fixture": "FX-U2", "control": name, "phase": phase,
                       "command": cmd, "expected": expected, "exit_status": completed.returncode,
                       "raw_output_sha256": sha256(raw).hexdigest(), "raw_output": filename,
                       "application_count": applications}
        logical = name+"/"+phase
        value = json.dumps(observation, sort_keys=True)
        record = Observation(Header("AlienLogicLab/alienintent", "fx-u2", logical, sha256(value.encode()).hexdigest(),
                                    (definition_ref,), "private"), definition_ref, logical, "python-unittest-real-mutated-copy",
                             (), value, None, "Morty", args.invocation, "sha256:"+sha256(raw).hexdigest())
        observation["observation_ref"] = asdict(repository.put(record))
        observations.append(observation)
        print(name, phase, completed.returncode, flush=True)
        return completed.returncode, raw

    with tempfile.TemporaryDirectory(prefix="fx-u2-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT/"src", root/"src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT/"tests", root/"tests", ignore=shutil.ignore_patterns("__pycache__"))
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
    report = {"schema_version": 1, "fixture": "FX-U2", "baseline": BASELINE, "invocation": args.invocation,
              "candidate_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "contract_sha256": sha256(contract.read_bytes()).hexdigest(),
              "implementation_files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                                       for p in sorted((ROOT/"src/alienintent/context_assembly").rglob("*.py"))
                                       + [ROOT/"src/alienintent/composition/upstream_profile.py", ROOT/"tests/context_assembly/test_ambiguity.py"]},
              "tokens": None, "cost": None, "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable",
              "controls": outcomes, "observations": observations, "verdict": "independent verifier pending"}
    (args.output/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    return 0 if all(o["discriminated"] for o in outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
