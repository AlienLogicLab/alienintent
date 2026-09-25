"""FX-L1 disposable local proof. Never touches a live host, queue, provider or profile.

Run against committed source; output must be a new directory. Every rerun keeps
its own immutable observations. The final custody comment identifies the evidence
commit, whose source files must match the recorded source candidate digests.
"""
from dataclasses import asdict
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = "src/alienintent/execution_coordination/domain/liveness.py"
APP = "src/alienintent/execution_coordination/application/liveness.py"
ADAPTER = "src/alienintent/execution_coordination/adapters/liveness_observations.py"
PORTS = ("src/alienintent/execution_coordination/ports/liveness.py",)
PROFILE = "src/alienintent/composition/liveness_profile.py"
TEST = "tests/execution_coordination/test_liveness_reconciliation.py"
BOUNDED = ("tests/control_plane/test_monitor_health.py", "tests/control_plane/test_attention.py")
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-L1/FX-L1.md"
ADMISSION_BASELINE = "98a56bf3c9f424b2507ee39ba3bcd1628bf85eae"
# Observed failing at ADMISSION_BASELINE before any L1 change; owned by WO-220204 (FX-U4), not repaired here.
BASELINE_FAILING_FILE = "tests/evidence_learning/test_proof_planning.py"
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
# One control per material failure class; two are the AC-07 pinned controls.
# (control, failure class, file, needle, replacement, pytest node ids, required assertions)
CONTROLS = (
    ("grace_ignored", "missing effect after configured grace G yields one gap", DOMAIN,
     "    if age < policy.grace_micros:", "    if False:",
     ("test_grace_boundary[below]",), ("before G nothing is recovered",)),
    ("unknown_as_absent", "unknown correlated evidence holds rather than fabricating absence", DOMAIN,
     '        if evidence.status in ("PENDING", "UNKNOWN"):', '        if evidence.status == "PENDING":',
     ("test_unknown_effect_holds_at_confirmation_bound[below]",), ("unknown evidence must hold rather than launch",)),
    ("judgment_suppression_removed", "AC-07: completed judgment suppresses relaunch until resolution", DOMAIN,
     "    if latest is not None and latest.judgment and judgment_resolved is not True:", "    if False:",
     ("test_completed_judgment_suppresses_relaunch_indefinitely[FOUNDER_EXCEPTION]",),
     ("a completed judgment outcome must suppress relaunch",)),
    ("identity_fence_removed", "AC-07: delayed original + contenders + restart keep one effect identity", APP,
     "        key = expected.effect_key\n", '        key = expected.effect_key + ":" + source\n',
     ("test_race_delayed_original_contenders_and_restart",), ("delayed original must not act again",)),
    ("bound_claim_unconditional", "stale/unavailable monitor health withdraws the G+I claim", APP,
     '        return BOUND_CLAIMED if status == "HEALTHY" else f"WITHDRAWN:{status}:{reason}"',
     "        return BOUND_CLAIMED",
     ("test_bound_claim_requires_healthy_monitor",), ("a scan must not claim G+I on unhealthy monitor evidence",)),
)


def digest(body):
    return "sha256:" + sha256(body).hexdigest()


def encoded(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str).encode()


def retain(output, record):
    body = encoded(record)
    name = sha256(body).hexdigest()
    target = output / "observations" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != body:
            raise RuntimeError("immutable observation collision")
    else:
        with target.open("xb") as stream:
            stream.write(body)
    return {"revision_digest": "sha256:" + name, "locator": "observations/" + name}


def execute(cwd, argv):
    environment = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd),
                   "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=900)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def pytest(*targets):
    return [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets]


def failed_ids(stdout):
    return sorted(set(re.findall(r"^FAILED (\S+)", stdout, re.MULTILINE)))


def discriminates(assertions, intact, fault, restored):
    return (intact["exit_status"] == 0 and restored["exit_status"] == 0 and fault["exit_status"] == 1
            and all(a in fault["stdout"] for a in assertions)
            and ("AssertionError" in fault["stdout"] or "Failed: DID NOT RAISE" in fault["stdout"]))


def baseline_regression(output):
    """Run the known-failing file at the admission baseline in a disposable worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-l1-baseline-") as temporary:
        tree = Path(temporary) / "baseline"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), ADMISSION_BASELINE], cwd=ROOT,
                       check=True, capture_output=True)
        try:
            observation = execute(tree, pytest(BASELINE_FAILING_FILE))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def readback(output):
    """Composed disposable run; every value below is read back from the durable stores."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tests.execution_coordination import test_liveness_reconciliation as fx
    with tempfile.TemporaryDirectory(prefix="fx-l1-readback-") as temporary:
        root = Path(temporary)
        (root / "recovery").mkdir()
        (root / "judgment").mkdir()
        clock = fx.Clock()
        recovery = fx.started(root / "recovery", clock)
        steps = []
        for now in (fx.T0 + fx.G - fx.SECOND, fx.T0 + fx.G, fx.T0 + 2 * fx.G):
            report = fx.scan(recovery, clock, now)
            steps.append({"scenario": "lost-trigger", "now": now, "outcome": report.outcome,
                          "bound_claim": report.bound_claim, "events": [asdict(e) for e in report.events]})
        late = fx.delayed_original(root / "recovery", fx.T0 + 2 * fx.G + fx.SECOND, "readback-delivery")
        effect = fx.expected(recovery)
        judged = fx.judged(root / "judgment", clock)
        for n in (1, 3, 10):
            report = fx.scan(judged, clock, fx.T0 + n * fx.G)
            steps.append({"scenario": "judgment", "now": clock.now, "outcome": report.outcome,
                          "bound_claim": report.bound_claim, "events": [asdict(e) for e in report.events]})
        clock.now = fx.T0 + 10 * fx.G + 3 * fx.I
        stale = judged.reconciler.scan()
        steps.append({"scenario": "monitor-overdue", "now": clock.now, "outcome": stale.outcome,
                      "bound_claim": stale.bound_claim})
        receipt = recovery.store.readback_guarded(fx.PROFILE, effect.effect_key)
        body = {"steps": steps, "delayed_original": late,
                "consumer_outcomes": fx.consumers(recovery),
                "readback_receipt": None if receipt is None else asdict(receipt),
                "lane": recovery.store.read_state(fx.PROFILE, "liveness-lane:" + effect.effect_key),
                "lifecycle": recovery.store.read_state(fx.PROFILE, "liveness-active:" + fx.BIU),
                "policy": recovery.store.read_state(fx.PROFILE, "liveness-policy:" + fx.PROFILE),
                "judgment_consumer_outcomes": fx.consumers(judged),
                "attention": [asdict(i) for i in judged.judgment.attention.list_pending()],
                "monitor": asdict(judged.reconciler.progress.repository.read(fx.PROFILE))}
        assert len(body["consumer_outcomes"]) == 1 and late["reason"] == "EFFECT_IDENTITY_USED"
        assert body["judgment_consumer_outcomes"] == [] and len(body["attention"]) == 1
        return retain(output, body), body


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220306.md"),
             Path("docs/evidence/wave2-design-contracts.json"), Path("docs/evidence/wave2-dependency-dag.json"),
             Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220306.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220306.allocation.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220306.proof-packet.md"),
             Path("docs/evidence/wave2-proof-fixtures/FX-C1/execution-record.json"),
             Path("docs/evidence/wave2-proof-fixtures/FX-C4/execution-record.json"),
             Path("docs/evidence/wave2-proof-fixtures/FX-S2/execution-record.json"),
             Path(TEST), Path(__file__).relative_to(ROOT), *map(Path, (DOMAIN, APP, ADAPTER, PROFILE, *PORTS))]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-L1",
        "work_unit": "WO-220306", "issue": 112, "invocation": invocation,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE,
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths if (ROOT / p).exists()},
        "missing_inputs": [str(p) for p in paths if not (ROOT / p).exists()],
        "commands": [], "holds": [], "baseline_conditions": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    if report["missing_inputs"]:
        report["holds"].append("pinned inputs missing")
    baseline, baseline_ref = baseline_regression(output)
    baseline_failures = failed_ids(baseline["stdout"])
    for label, command in (
        ("focused", pytest(TEST)),
        ("bounded_initial", pytest(*BOUNDED)),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", pytest("tests/test_architecture_fitness.py")),
        ("python_regression", pytest()),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        observation = execute(ROOT, command)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        if label == "python_regression" and observation["exit_status"] != 0:
            failures = failed_ids(observation["stdout"])
            entry["failed"] = failures
            if failures and failures == baseline_failures:
                report["baseline_conditions"].append({
                    "condition": "PRE_EXISTING_BASELINE_FAILURE", "file": BASELINE_FAILING_FILE,
                    "count": len(failures), "baseline": ADMISSION_BASELINE, "baseline_ref": baseline_ref,
                    "owner": "WO-220204 (FX-U4 proof planning); not repaired inside WO-220306",
                    "note": "identical failing node ids at the admission baseline; no FX-L1 file is involved"})
            else:
                report["holds"].append(label + " failed beyond the recorded baseline condition")
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
        report["commands"].append(entry)
    mutations = []
    with tempfile.TemporaryDirectory(prefix="fx-l1-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, failure_class, relative, needle, replacement, tests, assertions in CONTROLS:
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f"{name}: mutation count {count}, expected exactly one")
            command = pytest(*(TEST + "::" + t for t in tests))
            intact = execute(copy, command)
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            ok = discriminates(assertions, intact, fault, restored)
            mutations.append({"control": name, "failure_class": failure_class, "file": relative,
                "application_count": count, "source_digest": digest(original.encode()),
                "mutation": {"remove": needle, "replace_with": replacement}, "command": command,
                "assertions": list(assertions), "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    try:
        report["readback_ref"], observed = readback(output)
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
        observed = None
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "fixed choices: G=300/I=60/C=90 configurable, digest persisted, missing/invalid policy blocks startup":
            ["test_policy_defaults_and_digest", "test_policy_invalid_blocks_startup", "test_policy_digest_persisted_at_start"],
        "SF-REQ-056-AC-01": ["test_grace_boundary", "test_detection_bound_g_plus_i"],
        "SF-REQ-056-AC-02": ["test_correlated_evidence_yields_no_recovery", "test_accept_recovers_each_missing_required_closure_effect",
                             "test_unknown_effect_holds_at_confirmation_bound", "test_unavailable_observation_is_evidence_hold"],
        "SF-REQ-056-AC-03": ["test_race_delayed_original_contenders_and_restart", "test_stale_lifecycle_snapshot_refused",
                             "test_pending_unsent_intent_past_c_executes_by_canonical_claim",
                             "test_unknown_effect_with_durable_receipt_confirms_by_readback"],
        "SF-REQ-056-AC-04": ["test_completed_judgment_suppresses_relaunch_indefinitely"],
        "SF-REQ-056-AC-05": ["test_seen_only_leaves_suppression", "test_valid_resolution_permits_reinspection_only",
                             "test_newer_nonjudgment_outcome_permits_reevaluation", "test_out_of_lane_resolution_keeps_suppression",
                             "test_stale_resolution_keeps_suppression"],
        "SF-REQ-056-AC-06": ["test_missing_authority_budget_or_custody_records_hold",
                             "test_recovery_uses_canonical_effect_path_without_status_toggling", "test_scanner_cannot_create_generation",
                             "test_effect_key_excludes_delivery_and_scan_time"],
        "SF-REQ-056-AC-07": ["proven-red.json: identity_fence_removed, judgment_suppression_removed"],
        "monitor-health evidence withdraws the G+I claim": ["test_bound_claim_requires_healthy_monitor", "test_scan_progress_reported_to_monitor"],
        "non-claim: no work-discovery polling": ["test_unknown_record_outside_known_active_is_not_discovered"],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"),
        "composed_readback": observed,
        "boundaries": "local/composed fixture only; host unassigned (R1-GAP-MONITOR-HOST); no bootstrap liveness "
                      "retirement, live monitor-host replacement, remote provider binding or work-discovery polling; "
                      "SF-REQ-056-AC-08 live exercise not attempted",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]},
        indent=2, default=str) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-L1", "exit_status": report["exit_status"], "holds": report["holds"],
                      "baseline_conditions": len(report["baseline_conditions"]), "controls": len(mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
