#!/usr/bin/env python3
"""FX-R6: reuse the canonical live admission fixture and retain R6 custody/readback."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OLD_GATE = ROOT / "tools/live/release_admission.py"
INSTALLED_GATE = Path.home() / ".local/share/alienintent-bootstrap/release_admission.py"
PROFILE = Path.home() / ".config/alienintent/self-hosting.json"
STATE = Path.home() / ".local/state/alienintent/state.json"
INVOCATION = "AlienLogicLab/alienintent#138:PRODUCER:5bd7c385-7f0b-4c3e-b4c2-c08d5365d994"
REQUIRED_NEGATIVE_CASES = (
    "03-identity-replay", "04-policy-source-mismatch", "05-readiness-digest-mismatch",
    "06-unsatisfied-dependency", "07-missing-capability", "08-missing-budget-dimension",
    "E1-eligibility-not-released", "09-no-release-record", "10-record-does-not-authorize",
    "11-no-exact-baseline", "12a-null-baseline", "12b-absent-baseline",
    "13-unreachable-baseline", "14-unsuperseded-denial",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def check_cases(cases: list[dict]) -> list[str]:
    by_name = {case.get("case"): case for case in cases}
    return [name for name in REQUIRED_NEGATIVE_CASES
            if name not in by_name or by_name[name].get("expected_worker_starts") != 0
            or by_name[name].get("observed_worker_starts") != 0
            or by_name[name].get("matches_expected") is not True]


def old_gate_control(path: Path = OLD_GATE) -> dict:
    spec = importlib.util.spec_from_file_location("old_release_admission", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    facts = {"status": "READY", "agent_ready": "READY",
             "release_record": {"authorizes_implement": True, "baseline": "a" * 40},
             "baseline_resolves": True, "baseline_ancestral": True, "body": "",
             "open_dependencies": [], "active_invocations": [], "held": False,
             "wip_limit": 1, "active_claims_total": 0,
             "priority_reconciliation": {"status": "ALREADY_MATCHED"}}
    intact = module.admit(facts)
    fault = module.admit(facts | {"agent_ready": None})
    restored = module.admit(facts)
    return {"intact": intact, "fault": fault, "restored": restored,
            "passed": intact == [] and [f["check"] for f in fault] == ["agent_ready"] and restored == []}


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        parser.error("output directory already exists; evidence is immutable")
    if not PROFILE.is_file() or not STATE.is_file() or not INSTALLED_GATE.is_file():
        parser.error("configured profile, runtime state or installed gate is unavailable")
    source = git("rev-parse", "HEAD").stdout.decode().strip()
    baseline = git("merge-base", "HEAD", "origin/main").stdout.decode().strip()
    old_before = OLD_GATE.read_bytes()
    installed_before = INSTALLED_GATE.read_bytes()
    state_before = STATE.read_bytes()
    committed_old = git("show", "HEAD:tools/live/release_admission.py").stdout
    if old_before != committed_old:
        parser.error("old protection differs from committed source")
    control_before = old_gate_control()
    installed_control_before = old_gate_control(INSTALLED_GATE)
    if not control_before["passed"] or not installed_control_before["passed"]:
        parser.error("old protection control failed before live probe")
    out.mkdir(parents=True)
    command = [sys.executable, "tools/live/fx_b3_release_admission_proof.py", "--target", "production",
               "--out", str(out / "live")]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (out / "command.stdout").write_text(proc.stdout)
    (out / "command.stderr").write_text(proc.stderr)
    live_path = out / "live/result.json"
    live = json.loads(live_path.read_text()) if live_path.exists() else {}
    case_failures = check_cases(live.get("cases", []))
    positive = next((c for c in live.get("cases", []) if c.get("case") == "02-positive-control"), {})
    old_after = OLD_GATE.read_bytes()
    installed_after = INSTALLED_GATE.read_bytes()
    control_after = old_gate_control() if old_after == old_before else {"passed": False}
    installed_control_after = old_gate_control(INSTALLED_GATE) if installed_after == installed_before else {"passed": False}
    readback = {"old_protection_path": "tools/live/release_admission.py",
                "before_sha256": digest(old_before), "after_sha256": digest(old_after),
                "unchanged": old_before == old_after == committed_old,
                "before_control": control_before, "after_control": control_after,
                "installed_gate_path": str(INSTALLED_GATE),
                "installed_before_sha256": digest(installed_before),
                "installed_after_sha256": digest(installed_after),
                "installed_unchanged": installed_before == installed_after,
                "installed_differs_from_repository": installed_before != committed_old,
                "installed_before_control": installed_control_before,
                "installed_after_control": installed_control_after,
                "project": live.get("target", {}).get("project_id"),
                "project_non_interference": live.get("non_interference", {}).get("target"),
                "cleanup": live.get("cleanup"), "runtime_state_after_sha256": digest(STATE.read_bytes())}
    write(out / "readback.json", readback)
    checks = {"live_exit_zero": proc.returncode == 0, "live_passed": live.get("passed") is True,
              "all_negative_cases_zero_launches": not case_failures,
              "positive_control_one_launch": positive.get("observed_worker_starts") == 1,
              "old_protection_unchanged": readback["unchanged"],
              "old_protection_control": control_before["passed"] and control_after["passed"],
              "installed_protection_unchanged": readback["installed_unchanged"],
              "installed_protection_control": installed_control_before["passed"] and installed_control_after["passed"],
              "project_non_interference": bool(readback["project_non_interference"] and
                                               readback["project_non_interference"].get("unchanged")),
              "cleanup_verified": bool(readback["cleanup"] and readback["cleanup"].get("verified"))}
    write(out / "proven-red.json", {"mechanical_control": control_before,
                                     "restored_control": control_after,
                                     "installed_control": installed_control_before,
                                     "installed_restored_control": installed_control_after,
                                     "upstream_offline_test": "tools/live/test_fx_b3_release_admission_proof.py"})
    write(out / "independent-verdict.json", {"status": "PENDING_INDEPENDENT_VERIFIER",
                                             "claim": "Producer evidence only; no independent verdict is claimed"})
    record = {"fixture": "FX-R6", "work_unit": "WO-220606", "issue": 138,
              "invocation": INVOCATION, "source_revision": source, "release_baseline": baseline,
              "fixture_revision": source, "candidate_revision": "RECORDED_ON_ISSUE_AFTER_COMMIT",
              "profile_path": str(PROFILE), "profile_sha256": digest(PROFILE.read_bytes()),
              "runtime_state_before_sha256": digest(state_before),
              "command": command, "exit_status": proc.returncode,
              "expected": "one scripted valid launch; zero invalid launches; old protection retained",
              "observed": live.get("totals"), "invalid_cases": case_failures,
              "checks": checks, "passed": all(checks.values()),
              "proof_level": "OPERATIONAL_OR_EXTERNAL_AUTHORITY",
              "scope": "Project #1 labelled disposable probes; no real worker provider calls or publications",
              "old_protection_readback": "readback.json",
              "predecessor_proof": "docs/evidence/wave2-proof-fixtures/FX-B3/phase2-project1/result.json"}
    write(out / "execution-record.json", record)
    for observation in (live_path, out / "readback.json", out / "command.stdout", out / "command.stderr"):
        if observation.is_file():
            payload = observation.read_bytes()
            destination = out / "observations" / digest(payload)
            destination.parent.mkdir(exist_ok=True)
            if not destination.exists():
                shutil.copyfile(observation, destination)
    manifest = {str(path.relative_to(out)): digest(path.read_bytes()) for path in sorted(out.rglob("*")) if path.is_file()}
    write(out / "digest-manifest.json", manifest)
    print(json.dumps({"passed": record["passed"], "checks": checks, "output": str(out)}, indent=2))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
