"""FX-K1 disposable local proof. Never touches a live host, queue, provider, model or profile.

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
WORKER = "src/alienintent/invocation_runtime/application/real_worker.py"
COORDINATOR = "src/alienintent/execution_coordination/application/factory_coordinator.py"
PORT = "src/alienintent/execution_coordination/ports/worker_provider.py"
JOURNAL_PORT = "src/alienintent/invocation_runtime/ports/invocation_journal.py"
JOURNAL = "src/alienintent/invocation_runtime/adapters/invocation_journal.py"
TEST = "tests/invocation_runtime/test_real_worker_outcome.py"
FIXTURE = "tests/invocation_runtime/k1_fixture.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-K1.md"
ADMISSION_BASELINE = "308188c9bce7eb5557d1307bf4d017d907ade16a"
FOCUSED = (TEST, "tests/execution_coordination/test_factory_coordinator.py", "tests/invocation_runtime/test_scripted_worker.py")
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
# (control, material class, file, needle, replacement, pytest node ids, required assertion text)
CONTROLS = (
    ("readback_not_durable", "durable-correlated-readback-across-restart", WORKER,
     '        """With a journal, answer only from durable, correlated evidence; this survives a restart."""\n'
     "        if self._journal is None:\n",
     '        """With a journal, answer only from durable, correlated evidence; this survives a restart."""\n'
     "        if True:\n",
     ("test_real_path_durably_retains_attributable_outcome_and_reads_it_back_after_restart",),
     ("reopened.worker.read_back(invocation) == WorkerOutcome.success(candidate)",)),
    ("transition_gate_removed", "process-success-without-durable-result-holds", COORDINATOR,
     "        return durable is not None and (durable.kind, durable.candidate) == (outcome.kind, outcome.candidate)\n",
     "        return True\n",
     ("test_process_success_without_a_durable_result_holds_the_transition",),
     ("summary.dispatched == ()",)),
    ("role_correlation_unchecked", "wrong-correlation-holds", WORKER,
     '        if entry.get("work_identity") != invocation.work_identity or entry.get("role") != str(InvocationRole.PRODUCER):\n',
     '        if entry.get("work_identity") != invocation.work_identity:\n',
     ("test_miscorrelated_durable_result_holds_rather_than_being_accepted[role]",),
     ("summary.dispatched == ()",)),
    ("recovery_identity_replaced", "restart-preserves-identity-without-duplication", COORDINATOR,
     "            outcome = self._worker.read_back(WorkerInvocation(identity, reservation.owner, item.contract.content_digest))\n",
     '            outcome = self._worker.read_back(WorkerInvocation(identity, f"launch:{identity}:restarted", item.contract.content_digest))\n',
     ("test_restart_after_crash_reads_back_the_original_identity_without_duplicating_the_result",),
     ("state.stage is LifecycleStage.DONE",)),
)


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
    with tempfile.TemporaryDirectory(prefix="fx-k1-baseline-") as temporary:
        tree = Path(temporary) / "tree"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), baseline], cwd=ROOT, check=True, capture_output=True)
        try:
            observation = execute(tree, pytest(*nodes))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def run(output, invocation, baseline):
    output.mkdir(parents=True, exist_ok=False)
    paths = [CONTRACT, "docs/work-units/wave2/WO-220401.md", "docs/evidence/wave2-execution-packets/WO-220401.packet.json",
             "docs/evidence/wave2-execution-packets/WO-220401.allocation.json",
             "docs/evidence/wave2-execution-packets/WO-220401.proof-packet.md",
             "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json",
             TEST, FIXTURE, str(Path(__file__).relative_to(ROOT)), WORKER, COORDINATOR, PORT, JOURNAL_PORT, JOURNAL]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-K1", "biu_id": "WO-220401",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "code_baseline": baseline,
        "input_digests": {p: digest((ROOT / p).read_bytes()) for p in paths},
        "commands": [], "holds": [], "residuals": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": 0,
                         "reason": "no provider or model is composed; the worker is a local python child process. Token/cost UNKNOWN, not zero"}}
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
                                       f"{baseline}; outside the K1 extent, returned to their owners")
    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-k1-controls-") as temporary:
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
    mapping = {
        "durable-correlated-readback-across-restart": ["test_real_path_durably_retains_attributable_outcome_and_reads_it_back_after_restart"],
        "process-success-without-durable-result-holds": ["test_process_success_without_a_durable_result_holds_the_transition"],
        "wrong-correlation-holds": ["test_miscorrelated_durable_result_holds_rather_than_being_accepted"],
        "restart-preserves-identity-without-duplication": ["test_restart_after_crash_reads_back_the_original_identity_without_duplicating_the_result"],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"material_class_to_probes": mapping, "focused_command": report["commands"][0],
        "boundaries": "K1 seam only: no success-collapse removal, VERIFY/IMPLEMENT loop or verifier invocation (K2); no RoleOutcomeRecord or sidecar owner",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-K1", "exit_status": report["exit_status"], "holds": report["holds"],
                      "residuals": report["residuals"], "controls": len(controls), "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--baseline", required=True, help="code baseline commit for regression comparison")
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation, arguments.baseline))
