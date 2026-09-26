"""FX-O disposable local proof (WO-220404). Never touches a live host, queue, provider, model or profile.

Run against committed source; output must be a new directory. It runs the
focused suites, the pinned proof command inside an unprivileged user+network
namespace, the architecture checks and the broad regression once, then applies
each discriminating control exactly once to a disposable copy: intact exit 0,
fault exit 1 at the named assertion, restored exit 0. The two environment
controls (network denial absent, credential present) must turn the proof
command into a HOLD (exit 2), never a PASS.
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
CAPSTONE = "src/alienintent/composition/lifecycle_capstone.py"
GUARD = "src/alienintent/composition/role_binding.py"
OFFLINE = "src/alienintent/composition/offline_profile.py"
SANDBOX = "src/alienintent/composition/sandbox_run_profile.py"
COORDINATOR = "src/alienintent/execution_coordination/application/factory_coordinator.py"
WORKER = "src/alienintent/invocation_runtime/application/real_worker.py"
CLI = "src/alienintent/invocation_runtime/adapters/cli_worker.py"
OWNERSHIP = "src/alienintent/invocation_runtime/adapters/process_ownership.py"
OWNERSHIP_PORT = "src/alienintent/invocation_runtime/ports/process_ownership.py"
RUNTIME = "src/alienintent/invocation_runtime/domain/runtime.py"
TEST = "tests/composition/test_lifecycle_capstone.py"
OWNED = "tests/invocation_runtime/test_owned_work.py"
MANIFEST = "docs/evidence/wave2-proof-fixtures/FX-O/manifest.json"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-O.md"
ADMISSION_BASELINE = "4a9a3b67a1f5fea5d3caedd2f597bab23a94cf12"
PACKET_BOUNDED = ("tests/composition/test_offline_proof.py", "tests/composition/test_sandbox_run_profile.py",
                  "tests/execution_coordination/test_factory_coordinator.py", "tests/invocation_runtime/test_runtime.py")
FOCUSED = (TEST, OWNED, *PACKET_BOUNDED, "tests/composition/test_role_binding.py", "tests/invocation_runtime/test_real_worker_outcome.py",
           "tests/execution_coordination/test_role_orchestration.py", "tests/invocation_runtime/test_scripted_worker.py")
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
CLASSES = {
    "denied-network-publication-retrieval-wrong-candidate": "Denied-network lifecycle uses actual local Git publication and fresh verifier retrieval and rejects wrong/unpublished candidate identity.",
    "rework-review-accept-closure-without-collapse": "Distinct producer/verifier flow exercises rejection-repair-fresh-candidate and accepted REVIEW/ACCEPT/closure without success-collapse shortcuts.",
    "outcome-evidence-holds-restart-idempotent": "Missing, stale or miscorrelated durable role/invocation/candidate outcome evidence holds despite process success; duplicate/restart remains idempotent.",
    "judgment-hold-one-authorized-effect": "Judgment-required outcomes hold correctly and exactly one authorized effect/readback identity is retained.",
    "custody-verifier-binding-correlation-controls": "Custody, verifier independence, binding and correlation negative controls fail while restored canonical behavior passes.",
    "AC-07": "Malformed, missing, delayed, duplicate or miscorrelated outcomes never advance lifecycle; delayed correlated readback and duplicate idempotency are proved.",
    "AC-08": "Crash-before-output and progress-then-crash preserve original identity/evidence; UNKNOWN ownership blocks replacement, while conclusively dead + confirmed missing result triggers bounded deterministic recovery without a Director/status retrigger.",
}
# (control, material class, file, needle, replacement, pytest node ids, required assertion text)
CONTROLS = (
    ("custody_unchecked", "denied-network-publication-retrieval-wrong-candidate", GUARD,
     '        if outcome is None or outcome.kind != "success" or not _same_candidate(outcome.candidate, candidate):\n            return "candidate-custody-unattributable"\n',
     '        if outcome is None or outcome.kind != "success" or not _same_candidate(outcome.candidate, candidate):\n            pass\n',
     (f"{TEST}::test_a_candidate_the_producer_never_published_is_refused_before_the_verifier_launches",),
     ("W1 wrong candidate refused before launch",)),
    ("rework_skipped", "rework-review-accept-closure-without-collapse", COORDINATOR,
     '            if outcome.kind == "reject":\n',
     "            if False:\n",
     (f"{TEST}::test_the_lifecycle_rejects_reworks_and_closes_through_distinct_roles_and_actual_git_custody",),
     ("L5 rejection recorded and reworked into a fresh candidate",)),
    ("outcome_correlation_bypassed", "outcome-evidence-holds-restart-idempotent", COORDINATOR,
     "        return durable is not None and self._observables(durable) == self._observables(outcome)\n",
     "        return True\n",
     (f"{TEST}::test_a_miscorrelated_duplicate_or_malformed_outcome_holds_despite_process_success[miscorrelated-outcome-M1]",),
     ("M1 misattribute-producer-outcome holds despite process success",)),
    ("judgment_released_without_decision", "judgment-hold-one-authorized-effect", COORDINATOR,
     '            if projected.stage is LifecycleStage.DONE or projected.outcome in {"authority-block", "blocked-by-authority", "cancelled-by-operator", "cancelled-by-decision", "failure", "timeout"}:\n',
     '            if projected.stage is LifecycleStage.DONE or projected.outcome in {"blocked-by-authority", "cancelled-by-operator", "cancelled-by-decision", "failure", "timeout"}:\n',
     (f"{TEST}::test_a_judgment_required_outcome_holds_until_one_attributable_decision",),
     ("J1 judgment-required outcome holds with one JUDGMENT attention item",)),
    ("verifier_self_approval", "custody-verifier-binding-correlation-controls", COORDINATOR,
     '            return _Advance(transition(current, current.version, "verify", candidate=verified), "success", {"producer_correlation": invocation.correlation_id})\n',
     '            return self._advance(item, transition(current, current.version, "verify", candidate=verified), prior | {"producer_correlation": "self-approved"}, replace(invocation, role=VERIFIER, candidate=verified), WorkerOutcome.accept(verified, (), ("feature-regressions:sha256:self",)))\n',
     (f"{TEST}::test_the_lifecycle_rejects_reworks_and_closes_through_distinct_roles_and_actual_git_custody",),
     ("L2 distinct canonical role invocations",)),
    ("binding_guard_bypassed", "custody-verifier-binding-correlation-controls", CAPSTONE,
     "        return RoleBindingGuard(self.real_worker, self.journal, self.store, self.manifest.profile, self.manifest.repository, self.clock)\n",
     "        return self.real_worker\n",
     (f"{TEST}::test_the_capstone_reaches_its_worker_only_through_the_binding_guard",),
     ("a verifier launched under a grant for another role",)),
    ("duplicate_outcome_accepted", "AC-07", WORKER,
     "    if len(started) != 1 or len(finished) != 1:\n",
     "    if len(started) != 1 or not finished:\n",
     (f"{TEST}::test_a_miscorrelated_duplicate_or_malformed_outcome_holds_despite_process_success[duplicate-outcome-N1]",),
     ("N1 duplicate-producer-outcome holds despite process success",)),
    ("owned_work_ignored", "AC-08", CLI,
     "            if not self._await_owned(invocation_id, process, deadline):\n",
     "            if False:\n",
     (f"{OWNED}::test_client_exit_with_detached_owned_work_active_does_not_end_the_invocation",),
     ("the invocation ended while owned background work was still active",)),
    ("attested_recovery_disabled", "AC-08", GUARD,
     '        if not terminal and ownership == "owning-call-not-concluded":\n            terminal, ownership = self._attested_terminal(invocation)\n',
     "",
     (f"{TEST}::test_conclusive_owner_death_with_a_missing_result_recovers_deterministically[crash-before-output-C]",),
     ("C1 conclusive owner death with a confirmed missing result recovers deterministically",)),
    ("escaped_effect_assumed_absent", "AC-08", WORKER,
     "        if any(record.get(\"event\") == PUBLICATION_STARTED for record in own):\n            return answer(EFFECT_UNKNOWN)\n",
     "",
     (f"{TEST}::test_an_escaped_effect_holds_until_one_decision_authorizes_exactly_one_effect",),
     ("E1 an escaped effect is UNKNOWN and is never replaced",)),
    ("live_owner_assumed_dead", "AC-08", WORKER,
     '        if state != "terminated":\n',
     "        if False:\n",
     (f"{TEST}::test_unknown_ownership_blocks_replacement[owner-alive-A1]",),
     ("A1 UNKNOWN ownership blocks replacement",)),
    ("owned_work_assumed_absent", "AC-08", WORKER,
     "        if work is None or work:\n",
     "        if False:\n",
     (f"{TEST}::test_unknown_ownership_blocks_replacement[owned-work-active-B1]",),
     ("B1 UNKNOWN ownership blocks replacement",)),
    ("reused_pid_read_as_owner", "AC-08", OWNERSHIP,
     '        if started != start or state in {"Z", "X"}:\n',
     '        if state in {"Z", "X"}:\n',
     (f"{OWNED}::test_the_owner_identity_distinguishes_a_live_process_from_an_ended_or_reused_one",),
     ("a reused pid read as the owner",)),
    ("owner_marker_ignored", "AC-08", OWNERSHIP,
     "                if owner is not None:\n",
     "                if False:\n",
     (f"{OWNED}::test_another_owners_work_with_the_same_invocation_identity_is_neither_awaited_nor_stopped",),
     ("another owner's work was awaited",)),
)
MAPPING = {
    "denied-network-publication-retrieval-wrong-candidate": ["proof command inside unshare -rn (network ENFORCED)", "L3", "L4", "W1", "U1"],
    "rework-review-accept-closure-without-collapse": ["L1", "L2", "L5", "L6", "L7"],
    "outcome-evidence-holds-restart-idempotent": ["M1", "N1", "F1", "D1", "L9"],
    "judgment-hold-one-authorized-effect": ["J1", "J2", "J3", "J4", "E1", "E2", "L8"],
    "custody-verifier-binding-correlation-controls": ["custody_unchecked", "verifier_self_approval", "binding_guard_bypassed", "outcome_correlation_bypassed"],
    "AC-07": ["M1", "N1", "F1", "D1"],
    "AC-08": ["test_owned_work.py (owned background work, wall-clock stop, owner identity, marker scan, owner-bound markers, marked-only attestation, pid namespace)", "C1", "C2", "P1", "P2", "A1", "B1", "E1"],
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


def execute(cwd, argv, environment=None):
    environment = environment or {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=3600)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error), "stdout": str(error.stdout), "stderr": str(error.stderr)}


def failed_nodes(observation):
    return sorted(line.split(" - ")[0].removeprefix("FAILED ").strip()
                  for line in observation["stdout"].splitlines() if line.startswith("FAILED "))


def pytest(*targets):
    return [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets]


def stated(home, **extra):
    """The proof command's environment, stated in full: no inherited credential or route."""
    home.mkdir(parents=True, exist_ok=True)
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8", "PYTHONPATH": str(ROOT / "src"),
            "PYTHONDONTWRITEBYTECODE": "1", **extra}


def proof(root, *, namespace):
    command = [sys.executable, "-B", "-m", "alienintent.composition.lifecycle_capstone", "--root", str(root), "--manifest", str(ROOT / MANIFEST), "--network-timeout", "1"]
    return ["unshare", "-rn", *command] if namespace else command


def discriminates(assertions, intact, fault, restored, expected=(0, 1, 0)):
    return (intact["exit_status"], fault["exit_status"], restored["exit_status"]) == expected and all(
        a in fault["stdout"] + fault["stderr"] for a in assertions)


def baseline_failures(output, baseline, nodes):
    """Run the candidate's failing nodes at the code baseline, in its own detached worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-o-baseline-") as temporary:
        tree = Path(temporary) / "tree"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), baseline], cwd=ROOT, check=True, capture_output=True)
        try:
            observation = execute(tree, pytest(*nodes))
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def report_of(root):
    path = Path(root) / "run-report.json"
    return json.loads(path.read_text()) if path.exists() else None


def run(output, invocation, baseline):
    output.mkdir(parents=True, exist_ok=False)
    paths = [CONTRACT, MANIFEST, "docs/work-units/wave2/WO-220404.md", "docs/evidence/wave2-execution-packets/WO-220404.packet.json",
             "docs/evidence/wave2-execution-packets/WO-220404.allocation.json", "docs/evidence/wave2-execution-packets/WO-220404.proof-packet.md",
             "docs/evidence/wave2-readiness-assessments/WO-220404.2026-09-26T002627.317407Z.assessment.json",
             TEST, OWNED, str(Path(__file__).relative_to(ROOT)), CAPSTONE, GUARD, OFFLINE, SANDBOX, COORDINATOR, WORKER, CLI, OWNERSHIP, OWNERSHIP_PORT, RUNTIME]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-O", "biu_id": "WO-220404",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "code_baseline": baseline,
        "input_digests": {p: digest((ROOT / p).read_bytes()) for p in paths},
        "commands": [], "holds": [], "residuals": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "no provider or model is composed; the worker is the Deterministic Test Worker. Token/cost UNKNOWN, not zero; provider calls are read from the proof report"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    regression = None
    with tempfile.TemporaryDirectory(prefix="fx-o-proof-") as temporary:
        proof_root = Path(temporary) / "run"
        observation = execute(ROOT, proof(proof_root, namespace=True), stated(Path(temporary) / "home"))
        proof_report = report_of(proof_root)
        entry = {"id": "proof_command", "command": observation["argv"], "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation), "report_ref": None if proof_report is None else retain(output, proof_report)}
        report["commands"].append(entry)
        if observation["exit_status"] != 0 or proof_report is None or proof_report.get("verdict") != "PASS":
            report["holds"].append("proof command did not PASS inside the enforced network namespace")
        else:
            calls = [c for s in proof_report["scenarios"].values() for c in s["checks"] if c["id"] == "L10"]
            report["measurements"]["provider_calls"] = calls[0]["observed"]["provider_calls"] if calls else None
            report["proof_checks"] = {name: [(c["id"], c["status"]) for c in s["checks"]] for name, s in proof_report["scenarios"].items()}
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
                                       f"{baseline}; outside the FX-O extent, returned to their owners")
    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-o-environment-") as temporary:
        temporary = Path(temporary)
        for name, namespace, extra, reason in (
            ("network_denial_absent", False, {}, "outbound network denial not established"),
            ("credential_present", True, {"GITHUB_TOKEN": "fx-o-sentinel"}, "credential variables present"),
        ):
            intact = execute(ROOT, proof(temporary / f"{name}-intact", namespace=True), stated(temporary / "home"))
            fault = execute(ROOT, proof(temporary / f"{name}-fault", namespace=namespace), stated(temporary / "home", **extra))
            restored = execute(ROOT, proof(temporary / f"{name}-restored", namespace=True), stated(temporary / "home"))
            held = report_of(temporary / f"{name}-fault") or {}
            ok = discriminates(('"verdict": "HOLD"',), intact, fault, restored, (0, 2, 0)) and any(r.startswith(reason) for r in held.get("hold_reasons", []))
            controls.append({"control": name, "material_class": "denied-network-publication-retrieval-wrong-candidate", "application_count": 1,
                "fault": {"namespace": namespace, "extra_environment": sorted(extra)}, "assertions": [reason], "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"], "intact_ref": retain(output, intact),
                "fault_ref": retain(output, fault), "fault_report_ref": retain(output, held), "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    with tempfile.TemporaryDirectory(prefix="fx-o-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools", "docs/evidence/wave2-proof-fixtures/FX-S0", "docs/evidence/wave2-proof-fixtures/FX-O"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, material, relative, needle, replacement, tests, assertions in CONTROLS:
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f"{name}: mutation count {count}, expected exactly one")
            command = pytest(*tests)
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
    uncovered = sorted(set(CLASSES) - {control["material_class"] for control in controls})
    if uncovered:
        report["holds"].append(f"material classes without a discriminating control: {uncovered}")
    report["exit_status"] = 1 if report["holds"] else 0
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"material_classes": CLASSES, "material_class_to_probes": MAPPING,
        "focused_command": next(c for c in report["commands"] if c["id"] == "focused"),
        "proof_command": report["commands"][0],
        "boundaries": "WO-220404 offline capstone over bound K1/K2/K3/S0/C1 seams plus the bounded AC-08 implementation in Invocation Runtime (process ownership, owner-attested journal, restart attestation) consumed at the K3 guard; no live/shared-profile activation; no RoleOutcomeRecord or sidecar owner",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-O", "exit_status": report["exit_status"], "holds": report["holds"],
                      "residuals": report["residuals"], "controls": len(controls), "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--baseline", required=True, help="code baseline commit for regression comparison")
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation, arguments.baseline))
