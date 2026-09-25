"""FX-K2 disposable local proof. Never touches a live host, queue, provider, model or profile.

Run against committed source; output must be a new directory. Each discriminating control
(one per material failure class) is applied exactly once to a disposable copy: intact exit 0,
fault exit 1 at the named assertion, restored exit 0.
"""
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
COORDINATOR = "src/alienintent/execution_coordination/application/factory_coordinator.py"
PORT = "src/alienintent/execution_coordination/ports/worker_provider.py"
WORKER = "src/alienintent/invocation_runtime/application/real_worker.py"
SCRIPTED = "src/alienintent/invocation_runtime/adapters/scripted_worker.py"
SOURCE_CONTROL = "src/alienintent/invocation_runtime/adapters/git_source_control.py"
RUNTIME = "src/alienintent/invocation_runtime/domain/runtime.py"
TEST = "tests/execution_coordination/test_role_orchestration.py"
FIXTURE = "tests/execution_coordination/k2_fixture.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-K2.md"
ADMISSION_BASELINE = "e3371827223d1a9abd3c4a1144667de1c61f3778"
FOCUSED = (TEST, "tests/execution_coordination/test_factory_coordinator.py", "tests/invocation_runtime/test_real_worker_outcome.py",
           "tests/composition/test_sandbox_run_profile.py")
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
COLLAPSE = (
    '            verified_state = transition(current, current.version, "verify", candidate=verified)\n'
    '            reviewed = transition(verified_state, verified_state.version, "review")\n'
    '            verdict = evaluate_verdict(EvidenceDefinition(frozenset(item.contract.required_evidence)), (Observation("artifact-verified", True, True),), worker_claimed_success=True)\n'
    '            accepted = transition(reviewed, reviewed.version, "accept", verdict=verdict)\n'
    '            return _Advance(transition(accepted, accepted.version, "close", completed_closure_actions=frozenset(item.contract.required_closure_actions)), "success", {"producer_correlation": invocation.correlation_id})\n'
)
# (control, material class, file, needle, replacement, pytest node ids, required assertion text)
CONTROLS = (
    ("success_collapse_restored", "producer-success-advances-only-to-verify", COORDINATOR,
     '            return _Advance(transition(current, current.version, "verify", candidate=verified), "success", {"producer_correlation": invocation.correlation_id})\n',
     COLLAPSE,
     ("test_producer_success_advances_only_to_verify",),
     ("state.stage is LifecycleStage.VERIFY",)),
    ("rejection_budget_unenforced", "verifier-rejection-returns-to-implement-under-budget", COORDINATOR,
     "        if rejections >= item.contract.budget_policy.maximum_attempts:\n",
     "        if False:\n",
     ("test_rejection_beyond_the_attempt_budget_is_terminal_failure",),
     ('state.outcome == "failure"',)),
    ("closure_inferred_from_contract", "acceptance-through-review-and-closure-receipts-only", COORDINATOR,
     "        receipts = frozenset(outcome.receipts)\n",
     "        receipts = frozenset(outcome.receipts) | frozenset(item.contract.required_closure_actions)\n",
     ("test_closure_records_only_actions_actually_read_back",),
     ("state.completed_closure_actions == frozenset()",)),
    ("role_observables_narrowed", "missing-duplicate-stale-miscorrelated-evidence-holds", COORDINATOR,
     "        return outcome.kind, outcome.candidate, tuple(outcome.findings), tuple(outcome.receipts)\n",
     "        return outcome.kind, outcome.candidate\n",
     ("test_missing_duplicate_stale_or_miscorrelated_role_evidence_holds[closure-receipts]",),
     ('summary.stop_reason.value == "dependencies-or-authority-blocked"',)),
    ("scripted_lifecycle_write", "shared-worker-boundary-no-shortcut-or-sidecar-owner", SCRIPTED,
     '            "provider_calls": provider_calls, "wall_clock_seconds": wall_clock_seconds,\n',
     '            "provider_calls": provider_calls, "wall_clock_seconds": wall_clock_seconds, "stage": "DONE",\n',
     ("test_deterministic_and_real_workers_share_the_production_boundary",),
     ('not any("stage" in entry',)),
)
MAPPING = {
    "producer-success-advances-only-to-verify": ["test_producer_success_advances_only_to_verify",
                                                 "test_the_full_lifecycle_is_three_distinct_role_invocations_with_exact_custody"],
    "verifier-rejection-returns-to-implement-under-budget": ["test_verifier_rejection_records_findings_and_repairs_through_implement",
                                                             "test_rejection_beyond_the_attempt_budget_is_terminal_failure",
                                                             "test_a_candidate_that_carries_its_own_verdict_is_not_self_approved"],
    "acceptance-through-review-and-closure-receipts-only": ["test_closure_records_only_actions_actually_read_back",
                                                            "test_accepted_closure_carries_the_read_back_receipts"],
    "missing-duplicate-stale-miscorrelated-evidence-holds": ["test_missing_duplicate_stale_or_miscorrelated_role_evidence_holds",
                                                             "test_restart_after_the_verifier_outcome_recovers_its_role_without_re_running_it",
                                                             "test_restart_after_a_recorded_rejection_recovers_without_wedging_the_profile"],
    "shared-worker-boundary-no-shortcut-or-sidecar-owner": ["test_deterministic_and_real_workers_share_the_production_boundary",
                                                            "test_no_parallel_role_outcome_state_owner_exists_in_source",
                                                            "tests/invocation_runtime/test_real_worker_outcome.py (real CLI child worker through the same boundary)"],
}


def digest(body):
    return "sha256:" + sha256(body).hexdigest()


def encoded(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


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
    environment = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=1800)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def failed_nodes(observation):
    return sorted(line.split(" - ")[0].removeprefix("FAILED ").strip()
                  for line in observation["stdout"].splitlines() if line.startswith("FAILED "))


def pytest(*targets):
    return [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets]


def discriminates(assertions, intact, fault, restored):
    return (intact["exit_status"], fault["exit_status"], restored["exit_status"]) == (0, 1, 0) and all(
        a in fault["stdout"] for a in assertions)


def baseline_failures(output, baseline, nodes):
    """Run the candidate's failing nodes at the code baseline, in its own detached worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-k2-baseline-") as temporary:
        tree = Path(temporary) / "tree"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), baseline], cwd=ROOT, check=True, capture_output=True)
        try:
            observation = execute(tree, pytest(*nodes))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def run(output, invocation, baseline):
    output.mkdir(parents=True, exist_ok=False)
    paths = [CONTRACT, "docs/work-units/wave2/WO-220402.md", "docs/evidence/wave2-execution-packets/WO-220402.packet.json",
             "docs/evidence/wave2-execution-packets/WO-220402.allocation.json",
             "docs/evidence/wave2-execution-packets/WO-220402.proof-packet.md",
             "docs/evidence/wave2-readiness-assessments/WO-220402.2026-09-25T120043.382139Z.assessment.json",
             "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json",
             TEST, FIXTURE, str(Path(__file__).relative_to(ROOT)), COORDINATOR, PORT, WORKER, SCRIPTED, SOURCE_CONTROL, RUNTIME]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-K2", "biu_id": "WO-220402",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "code_baseline": baseline,
        "input_digests": {p: digest((ROOT / p).read_bytes()) for p in paths},
        "commands": [], "holds": [], "residuals": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": 0,
                         "reason": "no provider or model is composed; the workers are the deterministic scripted process and a local python child. Token/cost UNKNOWN, not zero"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    regression = None
    for label, command in (
        ("focused", pytest(*FOCUSED)),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", pytest("tests/test_architecture_fitness.py")),
        ("python_regression", pytest()),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        observation = execute(ROOT, command)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"], "observation_ref": retain(output, observation)}
        report["commands"].append(entry)
        if label == "python_regression":
            regression = (entry, observation)
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
    entry, observation = regression
    if observation["exit_status"] != 0:
        # A failure is admissible only if the identical node already fails at the code baseline.
        candidate_failed = failed_nodes(observation)
        base, base_ref = baseline_failures(output, baseline, candidate_failed) if candidate_failed else ({"exit_status": None, "stdout": ""}, None)
        baseline_failed = failed_nodes(base)
        new = sorted(set(candidate_failed) - set(baseline_failed))
        entry["baseline_comparison"] = {"baseline": baseline, "baseline_exit_status": base["exit_status"], "baseline_observation_ref": base_ref,
                                        "candidate_failed": candidate_failed, "baseline_failed": baseline_failed, "new_failures": new}
        if new or not candidate_failed:
            report["holds"].append("python_regression failed beyond the baseline")
        else:
            report["residuals"].append(f"PREEXISTING_BASELINE_FAILURES: {len(baseline_failed)} nodes fail identically at code baseline "
                                       f"{baseline}; outside the K2 extent, returned to their owners")
    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-k2-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools", "docs/evidence/wave2-proof-fixtures/FX-S0"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, material, relative, needle, replacement, tests, assertions in CONTROLS:
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
            controls.append({"control": name, "material_class": material, "file": relative, "application_count": count,
                "source_digest": digest(original.encode()), "mutation": {"remove": needle, "replace_with": replacement},
                "command": command, "assertions": list(assertions), "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault), "restored_ref": retain(output, restored),
                "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    report["exit_status"] = 1 if report["holds"] else 0
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"material_class_to_probes": MAPPING, "focused_command": report["commands"][0],
        "boundaries": "K2 canonical_role_orchestration only: local composed proof; no live/shared-profile activation; no RoleOutcomeRecord or sidecar owner",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-K2", "exit_status": report["exit_status"], "holds": report["holds"],
                      "residuals": report["residuals"], "controls": len(controls), "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--baseline", required=True, help="code baseline commit for regression comparison")
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation, arguments.baseline))
