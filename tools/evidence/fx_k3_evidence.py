"""FX-K3 disposable local proof. Never touches a live host, queue, provider, model or profile.

Run against committed source; output must be a new directory. Each discriminating control
(one per material failure class, plus one per further distinct invariant) is applied exactly
once to a disposable copy: intact exit 0, fault exit 1 at the named assertion, restored exit 0.
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
GUARD = "src/alienintent/composition/role_binding.py"
SANDBOX = "src/alienintent/composition/sandbox_run_profile.py"
GITHUB = "src/alienintent/composition/github_profile.py"
COORDINATOR = "src/alienintent/execution_coordination/application/factory_coordinator.py"
PORT = "src/alienintent/execution_coordination/ports/worker_provider.py"
WORKER = "src/alienintent/invocation_runtime/application/real_worker.py"
CLI = "src/alienintent/invocation_runtime/adapters/cli_worker.py"
TEST = "tests/composition/test_role_binding.py"
FIXTURE = "tests/composition/k3_fixture.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-K3.md"
ADMISSION_BASELINE = "178732f464a516f0cd6c108f18e25f1c6b978445"
FOCUSED = (TEST, "tests/composition/test_sandbox_run_profile.py", "tests/execution_coordination/test_github_work_management.py",
           "tests/invocation_runtime/test_real_worker_outcome.py", "tests/execution_coordination/test_role_orchestration.py",
           "tests/execution_coordination/test_factory_coordinator.py")
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
# (control, material class, file, needle, replacement, pytest node ids, required assertion text)
CONTROLS = (
    ("role_grant_unchecked", "refuse-unbound-role-authority-custody-or-correlation-before-launch", GUARD,
     "        if (grant.invocation_id, str(grant.role), grant.issuer, grant.target) != (invocation.correlation_id, invocation.role, self._profile, self._repository):\n",
     "        if (grant.invocation_id, grant.issuer, grant.target) != (invocation.correlation_id, self._profile, self._repository):\n",
     ("test_sandbox_profile_refuses_a_verifier_launch_whose_grant_names_another_role",),
     ("state.stage is LifecycleStage.VERIFY",)),
    ("outcome_correlation_disconnected", "refuse-unbound-role-authority-custody-or-correlation-before-launch", GUARD,
     '        return self._journal is not None and getattr(self.provider, "journal", None) is self._journal\n',
     "        return self._journal is not None\n",
     ("test_github_profile_refuses_an_unbound_or_disconnected_worker_before_launch[disconnected]",),
     ("summary.dispatched == ()",)),
    ("profile_journal_unbound", "bound-real-adapter-correlated-success-rejection-restart-readback", SANDBOX,
     "            now=clock, sleep=time.sleep, journal=self.journal,\n",
     "            now=clock, sleep=time.sleep,\n",
     ("test_bound_profiles_reach_correlated_success_through_every_role[sandbox]",),
     ("state.stage is LifecycleStage.DONE",)),
    ("binding_guard_bypassed", "bypassed-guard-or-disconnected-correlation-fails-before-advancement", GITHUB,
     "            self.store, self.work, self.worker,\n",
     "            self.store, self.work, worker,\n",
     ("test_github_profile_refuses_an_unbound_or_disconnected_worker_before_launch[missing]",),
     ("summary.dispatched == ()",)),
    ("sidecar_state_owner", "no-sidecar-state-owner-or-live-activation", GUARD,
     "        self.retained[invocation.correlation_id] = ownership\n",
     '        self._store.commit(self._profile, "k3-outcome:" + invocation.correlation_id, 0, {"kind": MISSING_TERMINAL_RESULT})\n'
     "        self.retained[invocation.correlation_id] = ownership\n",
     ("test_the_binding_guard_owns_no_state_and_introduces_no_outcome_record",),
     ("assert forbidden not in source",)),
    ("client_exit_releases_ownership", "owned-background-work-retains-invocation-ownership", CLI,
     "            process.communicate(timeout=wall_clock_seconds)\n",
     "            process.wait(timeout=wall_clock_seconds)\n",
     ("test_client_exit_with_owned_background_work_active_does_not_end_the_invocation",),
     ("the candidate was taken before owned background work finished",)),
    ("ownership_assumed_terminal", "unknown-ownership-refuses-replacement-conclusive-loss-replaces-once", GUARD,
     "        if invocation.correlation_id not in self._concluded:\n"
     '            return False, "owning-call-not-concluded"\n',
     "        return True, \"assumed\"\n",
     ("test_no_replacement_launches_while_ownership_is_unknown_after_the_owner_died",),
     ('runs(tmp_path) == [("PRODUCER", PRODUCER_0)]',)),
    ("raising_call_assumed_concluded", "unknown-ownership-refuses-replacement-conclusive-loss-replaces-once", GUARD,
     "        outcome = self.provider.start(invocation, context, grants, budget)  # type: ignore[attr-defined]\n",
     "        self._concluded.add(invocation.correlation_id)\n"
     "        outcome = self.provider.start(invocation, context, grants, budget)  # type: ignore[attr-defined]\n",
     ("test_a_raising_owning_call_leaves_its_effects_unknown_and_is_never_replaced",),
     ("a replacement launched over an unknown effect",)),
    ("missing_result_advanced_as_verdict", "unknown-ownership-refuses-replacement-conclusive-loss-replaces-once", COORDINATOR,
     "        if outcome.kind == MISSING_TERMINAL_RESULT:\n",
     "        if False:\n",
     ("test_a_conclusively_lost_verifier_result_re_dispatches_the_verifier_on_the_same_candidate",),
     ("state.stage is LifecycleStage.DONE",)),
    ("replacement_unbounded", "unknown-ownership-refuses-replacement-conclusive-loss-replaces-once", GUARD,
     '        return "replacement-allowance-exhausted" if lost > self._replacements else None\n',
     "        return None\n",
     ("test_a_second_loss_in_the_same_phase_is_refused_at_launch_and_held",),
     ("unbounded replacement launch",)),
)
MAPPING = {
    "refuse-unbound-role-authority-custody-or-correlation-before-launch": [
        "test_sandbox_profile_refuses_a_verifier_launch_whose_grant_names_another_role",
        "test_sandbox_profile_refuses_a_verifier_given_a_candidate_the_producer_never_published",
        "test_github_profile_refuses_an_unbound_or_disconnected_worker_before_launch[missing|disconnected]",
        "test_a_refused_launch_journals_nothing_and_reads_back_nothing"],
    "bound-real-adapter-correlated-success-rejection-restart-readback": [
        "test_bound_profiles_reach_correlated_success_through_every_role[sandbox|github]",
        "test_bound_sandbox_profile_reads_back_a_rejection_and_repairs_through_implement",
        "test_bound_sandbox_profile_recovers_the_verifier_outcome_after_a_crash_without_re_running_it"],
    "bypassed-guard-or-disconnected-correlation-fails-before-advancement": [
        "test_every_shared_profile_coordinator_reaches_its_worker_only_through_the_binding_guard",
        "test_github_profile_refuses_an_unbound_or_disconnected_worker_before_launch[missing|disconnected]"],
    "no-sidecar-state-owner-or-live-activation": ["test_the_binding_guard_owns_no_state_and_introduces_no_outcome_record"],
    "owned-background-work-retains-invocation-ownership": ["test_client_exit_with_owned_background_work_active_does_not_end_the_invocation"],
    "unknown-ownership-refuses-replacement-conclusive-loss-replaces-once": [
        "test_no_replacement_launches_while_ownership_is_unknown_after_the_owner_died",
        "test_conclusive_loss_without_a_durable_result_is_retained_and_replaced_exactly_once",
        "test_a_second_loss_in_the_same_phase_is_refused_at_launch_and_held",
        "test_a_raising_owning_call_leaves_its_effects_unknown_and_is_never_replaced",
        "test_a_conclusively_lost_verifier_result_re_dispatches_the_verifier_on_the_same_candidate"],
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
    with tempfile.TemporaryDirectory(prefix="fx-k3-baseline-") as temporary:
        tree = Path(temporary) / "tree"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), baseline], cwd=ROOT, check=True, capture_output=True)
        try:
            observation = execute(tree, pytest(*nodes))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def run(output, invocation, baseline):
    output.mkdir(parents=True, exist_ok=False)
    paths = [CONTRACT, "docs/work-units/wave2/WO-220403.md", "docs/evidence/wave2-execution-packets/WO-220403.packet.json",
             "docs/evidence/wave2-execution-packets/WO-220403.allocation.json",
             "docs/evidence/wave2-execution-packets/WO-220403.proof-packet.md",
             "docs/evidence/wave2-readiness-assessments/WO-220403.2026-09-25T193627.519498Z.assessment.json",
             TEST, FIXTURE, str(Path(__file__).relative_to(ROOT)), GUARD, SANDBOX, GITHUB, COORDINATOR, PORT, WORKER, CLI]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-K3", "biu_id": "WO-220403",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "code_baseline": baseline,
        "input_digests": {p: digest((ROOT / p).read_bytes()) for p in paths},
        "commands": [], "holds": [], "residuals": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": 0,
                         "reason": "no provider or model is composed; the worker is a local bash child process. Token/cost UNKNOWN, not zero"}}
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
                                       f"{baseline}; outside the K3 extent, returned to their owners")
    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-k3-controls-") as temporary:
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
        "boundaries": "K3 composed_role_bindings only: local composed proof over the actual sandbox_run_profile and github_profile constructors; no live/shared-profile activation; no RoleOutcomeRecord or sidecar owner",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-K3", "exit_status": report["exit_status"], "holds": report["holds"],
                      "residuals": report["residuals"], "controls": len(controls), "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--baseline", required=True, help="code baseline commit for regression comparison")
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation, arguments.baseline))
