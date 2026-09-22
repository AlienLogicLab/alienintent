"""Retain FX-S0 evidence by running the pinned commands and writing the retained artifacts.

Runs C1 (substrate tests), C2 (intact proof under `unshare -rn`), the C3/C4/C5
negative controls and C7 (fitness, full Python suite, Node suites) exactly as
`docs/evidence/wave2-proof-fixtures/FX-S0/fixture-plan.json` pins them, then
writes the run report, trajectory, raw journal/receipts, proven-red record,
offline-suite record and an execution record under the output directory. A
command that cannot run is recorded as a hold; nothing is inferred.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/evidence/wave2-proof-fixtures/FX-S0/fixture-plan.json"
MANIFEST = ROOT / "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json"
SUBSTRATE_TESTS = ("tests/invocation_runtime/test_scripted_worker.py", "tests/execution_coordination/test_local_work_management.py", "tests/composition/test_offline_proof.py")


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, env: dict[str, str] | None = None, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout, check=False)


def summary_line(completed: subprocess.CompletedProcess[str]) -> str:
    lines = [line for line in (completed.stdout + completed.stderr).splitlines() if line.strip()]
    return lines[-1] if lines else ""


def proof(root: Path, manifest: Path, *, namespace: bool, extra: dict[str, str] | None = None) -> tuple[list[str], subprocess.CompletedProcess[str], dict]:
    home = root / "home"
    home.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "LANG": "C.UTF-8", "PYTHONPATH": str(ROOT / "src")} | (extra or {})
    command = [sys.executable, "-m", "alienintent.composition.offline_proof", "--root", str(root), "--manifest", str(manifest), "--network-timeout", "3"]
    if namespace:
        command = ["unshare", "-rn", *command]
    completed = run(command, env=env)
    report_path = root / "run-report.json"
    return command, completed, json.loads(report_path.read_text()) if report_path.exists() else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "docs/evidence/wave2-proof-fixtures/FX-S0")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args(argv)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "negative-controls").mkdir(exist_ok=True)
    (out / "raw").mkdir(exist_ok=True)
    started = now()
    commands: list[dict[str, object]] = []
    holds: list[str] = []
    unshare_ok = run(["unshare", "-rn", "true"]).returncode == 0

    def rendered(text: str) -> str:
        """Paths outside the repository are ephemeral; record them by role, not by machine location."""
        return text.replace(str(ROOT), "<repo>").replace(sys.executable, "python3").replace(tempfile.gettempdir(), "<tmp>")

    def record(identifier: str, purpose: str, command: list[str], completed: subprocess.CompletedProcess[str], expected: int, extra: dict[str, object] | None = None) -> bool:
        ok = completed.returncode == expected
        commands.append({"id": identifier, "purpose": purpose, "command": rendered(" ".join(command)), "exit_status": completed.returncode, "expected_exit": expected, "ok": ok, "summary": rendered(summary_line(completed)), **(extra or {})})
        return ok

    c1 = [sys.executable, "-m", "pytest", "-q", *SUBSTRATE_TESTS]
    record("C1", "unit and composed tests for the substrate", c1, run(c1), 0)

    with tempfile.TemporaryDirectory(prefix="fx-s0-") as scratch:
        scratch_root = Path(scratch)
        if unshare_ok:
            command, completed, report = proof(scratch_root / "intact", args.manifest, namespace=True)
            record("C2", "intact FX-S0 proof under enforced network denial", command, completed, 0, {"verdict": report.get("verdict"), "network_denial": report.get("network_denial", {}).get("status")})
            for name in ("run-report.json", "trajectory.jsonl"):
                shutil.copyfile(scratch_root / "intact" / name, out / name)
            for source, target in (("worker-journal/journal.jsonl", "raw/journal.jsonl"), ("work-management/receipts.jsonl", "raw/receipts.jsonl"), ("work-management/ready-snapshot.json", "raw/ready-snapshot.json")):
                shutil.copyfile(scratch_root / "intact" / source, out / target)
        else:
            holds.append("C2: `unshare -rn` is unavailable on this platform; network-denial evidence NOT_ESTABLISHED")
        proven: list[dict[str, object]] = []
        command, completed, report = proof(scratch_root / "c3", args.manifest, namespace=False)
        ok = record("C3", "fault: same proof without the network namespace", command, completed, 2, {"verdict": report.get("verdict"), "network_denial": report.get("network_denial", {}).get("status")})
        proven.append({"check": "network_denial_is_not_assumed", "ok": ok and report.get("network_denial", {}).get("status") == "NOT_ESTABLISHED", "detail": f"C2 exit {commands[1]['exit_status'] if len(commands) > 1 and commands[1]['id'] == 'C2' else 'HOLD'} with the namespace; C3 exit {completed.returncode} verdict {report.get('verdict')} without it"})
        if report:
            shutil.copyfile(scratch_root / "c3" / "run-report.json", out / "negative-controls" / "C3-run-report.json")
        command, completed, report = proof(scratch_root / "c4", args.manifest, namespace=unshare_ok, extra={"GITHUB_TOKEN": "fx-s0-sentinel"})
        ok = record("C4", "fault: a credential variable present in the proof environment", command, completed, 2, {"verdict": report.get("verdict"), "credentials_present": report.get("credentials_present")})
        proven.append({"check": "credential_presence_is_a_hold", "ok": ok and report.get("credentials_present") == ["GITHUB_TOKEN"], "detail": f"C4 exit {completed.returncode} verdict {report.get('verdict')} with GITHUB_TOKEN set; credentials_present {report.get('credentials_present')}"})
        if report:
            shutil.copyfile(scratch_root / "c4" / "run-report.json", out / "negative-controls" / "C4-run-report.json")
        if unshare_ok:
            document = json.loads(args.manifest.read_text())
            document["work_items"][0]["script"] = ["provider-call"]
            faulted = scratch_root / "provider-call-manifest.json"
            faulted.write_text(json.dumps(document))
            command, completed, report = proof(scratch_root / "c5", faulted, namespace=True)
            ok = record("C5", "fault: a scripted step that attempts a provider call", command, completed, 1, {"verdict": report.get("verdict"), "provider_calls_observed": report.get("provider_calls_observed", {}).get("value")})
            proven.append({"check": "zero_provider_calls_can_go_red", "ok": ok and report.get("provider_calls_observed", {}).get("value") == 1, "detail": f"C5 exit {completed.returncode} verdict {report.get('verdict')} with provider_calls_observed {report.get('provider_calls_observed', {}).get('value')}; C2 observed 0"})
            if report:
                shutil.copyfile(scratch_root / "c5" / "run-report.json", out / "negative-controls" / "C5-run-report.json")
        else:
            holds.append("C5: requires `unshare -rn`")
        proven.append({"check": "candidate_revision_determined_by_manifest_and_clock", "ok": commands[0]["ok"], "detail": "C1 test_the_candidate_revision_is_determined_by_manifest_and_injected_clock: same manifest reproduces the revision in an isolated root; a different injected clock changes it"})
        proven.append({"check": "journal_read_back_discriminates_recorded_from_missing", "ok": commands[0]["ok"], "detail": "C1 test_a_crash_between_start_and_outcome_reads_back_as_unresolved and test_reopening_the_same_root_reads_back_the_same_truth_and_dispatches_nothing"})
        proven.append({"check": "reopened_seed_mismatch_is_refused", "ok": commands[0]["ok"], "detail": "C1 test_reopening_the_same_root_with_the_same_seed_keeps_receipts_and_refuses_a_different_seed"})
    (out / "proven-red.json").write_text(json.dumps({"ok": all(entry["ok"] for entry in proven) and not holds, "checks": proven, "holds": holds, "recorded_at": now()}, indent=1) + "\n")

    fitness = [sys.executable, "tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all"]
    record("C7a", "architecture fitness", fitness, run(fitness), 0)
    pytest_all = [sys.executable, "-m", "pytest", "-q"]
    full = run(pytest_all)
    record("C7b", "full Python suite", pytest_all, full, 0)
    (out / "offline-suite.json").write_text(json.dumps({"command": "python3 -m pytest -q", "summary": summary_line(full), "exit_status": full.returncode, "recorded_at": now()}, indent=1) + "\n")
    node = ["node", "scripts/check.mjs", "all"]
    record("C7c", "Node runtime, preflight, RAI and policy suites", node, run(node), 0)

    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    status = run(["git", "status", "--porcelain", "--", "src", "tests", "tools", "docs/evidence/schema", "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json", "docs/evidence/wave2-proof-fixtures/FX-S0/fixture-plan.json"]).stdout.strip().splitlines()
    artifacts = {str(path.relative_to(ROOT)): sha(path) for path in sorted(out.rglob("*")) if path.is_file() and path.name != "execution-record.json"}
    execution = {
        "record_kind": "ProofFixtureExecution", "schema_version": "1", "fixture_id": "FX-S0", "biu_id": "WO-220101", "issue_number": 69,
        "plan": {"path": str(PLAN.relative_to(ROOT)), "sha256": sha(PLAN)}, "manifest": {"path": str(args.manifest.relative_to(ROOT)) if args.manifest.is_relative_to(ROOT) else str(args.manifest), "sha256": sha(args.manifest)},
        "status": "HOLD" if holds or not all(entry["ok"] for entry in commands) else "EXECUTED",
        "started_at": started, "ended_at": now(), "source_revision": head, "uncommitted_source_paths_at_run": status,
        "platform": {"system": platform.platform(), "python": platform.python_version(), "git": run(["git", "--version"]).stdout.strip(), "unshare": run(["unshare", "--version"]).stdout.strip(), "unshare_rn_available": unshare_ok},
        "commands": commands, "holds": holds, "artifacts": artifacts,
        "not_claimed": ["multi-role producer/verifier/closure proof", "live proof", "any scenario beyond the single seeded success"],
    }
    (out / "execution-record.json").write_text(json.dumps(execution, indent=1) + "\n")
    print(json.dumps({"status": execution["status"], "commands": [(c["id"], c["exit_status"], c["ok"]) for c in commands], "holds": holds}))
    return 0 if execution["status"] == "EXECUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
