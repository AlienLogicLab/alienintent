#!/usr/bin/env python3
"""FX-U1 intact/fault/restored discrimination using isolated source copies."""
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
from alienintent.context_assembly.adapters.versioned_source import GitRequirementSource, historical_manifest
from alienintent.context_assembly.domain.inventory import assemble
from alienintent.context_assembly.application.inventory_service import InventoryService
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

ROOT = Path(__file__).resolve().parents[2]
INVOCATION = "AlienLogicLab/alienintent#76:PRODUCER:c03b4f78-22a9-43d1-829e-26042274efc8"
DOMAIN = "src/alienintent/context_assembly/domain/inventory.py"
ADAPTER = "src/alienintent/context_assembly/adapters/versioned_source.py"
TEST = "tests.context_assembly.test_inventory.InventoryTests."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    repository = LocalEvidenceRepository(args.output/"evidence", "AlienLogicLab/alienintent", "fx-u1")
    contract = ROOT/"docs/evidence/wo-220201-fx-u1.md"
    definition_ref = Ref("AlienLogicLab/alienintent", "fx-u1", "FX-U1-contract",
                         "sha256:"+sha256(contract.read_bytes()).hexdigest(), "repository:docs/evidence/wo-220201-fx-u1.md")
    manifest = historical_manifest(ROOT/"docs/evidence/wave2-design-contracts.json")
    snapshot = assemble(manifest.project, GitRequirementSource(ROOT).read(manifest))
    (args.output/"historical-manifest.json").write_text(json.dumps(asdict(manifest), indent=2)+"\n")
    (args.output/"historical-snapshot.json").write_text(json.dumps(asdict(snapshot), indent=2)+"\n")
    service = InventoryService(repository, SQLiteOperationalStore(args.output/"current.sqlite"), manifest.project,
                               "fx-u1", definition_ref, INVOCATION, frozenset({"private"}))
    _, snapshot_ref = service.publish(manifest, snapshot, 0)
    assert service.read()[1]["defined_ids"] == list(snapshot.defined_ids)
    controls = [
        ("canonical-parser-disabled", DOMAIN, 'if form == "canonical_requirement":', 'if form == "canonical_requirement" and False:', "test_historical_exact_manifest"),
        ("recorded-parser-disabled", DOMAIN, 'if form == "recorded_as":', 'if form == "recorded_as" and False:', "test_historical_exact_manifest"),
        ("conflicting-definition-effective", DOMAIN, 'if requirement_id in snapshot.conflicts:', 'if False and requirement_id in snapshot.conflicts:', "test_conflicts_aliases_revision_retirement_and_local_holds"),
        ("weakened-token-grammar", DOMAIN, '[0-9]{3,}(?:[A-Z])?', '[0-9]{3}', "test_all_forms_exact_tokens_and_issues"),
        ("stripped-suffix", DOMAIN, 'def classify(raw: str, namespaces: tuple[str, ...]) -> Token:\n', 'def classify(raw: str, namespaces: tuple[str, ...]) -> Token:\n    raw = re.sub(r"(?<=[0-9])[A-Z]$", "", raw)\n', "test_all_forms_exact_tokens_and_issues"),
        ("malformed-token-suppressed", DOMAIN, 'if "-REQ-" in raw:', 'if "-REQ-" in raw and "extra" not in raw:', "test_issue_holds_only_affected_span_within_one_source"),
        ("acceptance-wrong-kind", DOMAIN, 'kind, parent = "AcceptanceCriterionId",', 'kind, parent = "RequirementIdentifier",', "test_reference_kinds_and_definition_rejection"),
        ("compound-operand-loss", DOMAIN, 'kind, operands = "CompoundReference", expanded', 'kind, operands = "CompoundReference", expanded[:1]', "test_reference_kinds_and_definition_rejection"),
        ("excluded-scope-scanned", ADAPTER, '        return tuple(records)',
         '''        from dataclasses import replace
        from hashlib import sha256
        excluded = self.root / "excluded.md"
        if excluded.exists():
            text = excluded.read_text()
            spec = replace(manifest.entries[0], path="excluded.md", digest=sha256(text.encode()).hexdigest(), definitions=(), references=((1, 1),))
            records.append(SourceRecord(spec, text))
        return tuple(records)''', "test_source_scope_digest_and_provenance"),
        ("manifest-digest-mismatch-ignored", DOMAIN, 'elif sha256(record.text.encode()).hexdigest() != spec.digest:',
         'elif False and sha256(record.text.encode()).hexdigest() != spec.digest:', "test_source_scope_digest_and_provenance"),
    ]
    observations = []
    def run(root, name, phase, test, applications):
        cmd = [sys.executable, "-m", "unittest", TEST+test, "-v"]
        env = dict(os.environ, PYTHONPATH=str(root/"src"), PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(cmd, cwd=root, env=env, capture_output=True, timeout=120)
        raw = completed.stdout + completed.stderr
        filename = name+"-"+phase+".log"
        (args.output/filename).write_bytes(raw)
        expected = "nonzero assertion failure" if phase == "fault" else "exit 0"
        observation = {"schema_version": 1, "fixture": "FX-U1", "control": name, "phase": phase,
                       "command": cmd, "expected": expected, "exit_status": completed.returncode,
                       "raw_output_sha256": sha256(raw).hexdigest(), "raw_output": filename,
                       "application_count": applications}
        logical = name+"/"+phase
        value = json.dumps(observation, sort_keys=True)
        record = Observation(Header("AlienLogicLab/alienintent", "fx-u1", logical, sha256(value.encode()).hexdigest(),
                                    (definition_ref,), "private"), definition_ref, logical, "python-unittest-real-mutated-copy",
                             (), value, None, "Morty", INVOCATION, "sha256:"+sha256(raw).hexdigest())
        observation["observation_ref"] = asdict(repository.put(record))
        observations.append(observation)
        print(name, phase, completed.returncode, flush=True)
        return completed.returncode, raw
    with tempfile.TemporaryDirectory(prefix="fx-u1-") as tmp:
        root = Path(tmp)
        shutil.copytree(ROOT/"src", root/"src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT/"tests", root/"tests", ignore=shutil.ignore_patterns("__pycache__"))
        (root/"docs/evidence").mkdir(parents=True)
        shutil.copy2(ROOT/"docs/evidence/wave2-design-contracts.json", root/"docs/evidence/wave2-design-contracts.json")
        (root/".git").write_text((ROOT/".git").read_text())
        outcomes = []
        for name, path, old, new, test in controls:
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
            outcomes.append({"control": name, "discriminated": intact == 0 and fault != 0 and b"FAIL:" in raw and restored == 0})
    report = {"schema_version": 1, "fixture": "FX-U1", "baseline": "901d17444aa0aa1e5098017c3726d0d0daad1442",
              "invocation": INVOCATION, "candidate_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "source_manifest_digest": sha256(json.dumps(json.loads((ROOT/"docs/evidence/wave2-design-contracts.json").read_text())["contracts"][0]["identifier_contract"]["historical_fixture_manifest"], sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
              "implementation_files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/"src/alienintent/context_assembly").rglob("*.py"))},
              "historical_snapshot_ref": asdict(snapshot_ref), "historical_snapshot_digest": snapshot.digest,
              "tokens": None, "cost": None, "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable",
              "controls": outcomes, "observations": observations, "verdict": "independent verifier pending"}
    (args.output/"report.json").write_text(json.dumps(report, indent=2)+"\n")
    return 0 if all(o["discriminated"] for o in outcomes) else 1

if __name__ == "__main__":
    sys.exit(main())
