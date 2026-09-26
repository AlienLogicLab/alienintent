"""FX-C5 local/composed proof (WO-220305): the independently supervised monitor host.

Runs against committed source; output must be a new directory, and every rerun keeps its own
immutable observations. The real per-user systemd manager is required for the composed probe:
a skipped or unavailable manager is a HOLD, never a PASS. The execution record is rewritten
after every stage, so a stopped run leaves a durable INCOMPLETE record. Nothing here touches
a live host, queue, provider, bootstrap service or profile.
"""
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
TEST = "tests/control_plane/test_monitor_host.py"
SYSTEMD_TEST = "tests/control_plane/test_monitor_host_systemd.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-C5/FX-C5.md"
ADMISSION_BASELINE = "9cf86c959e60163631d49cefa778ad9bf40ff0fb"
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
SOURCES = ("src/alienintent/control_plane/domain/monitor_host.py", "src/alienintent/control_plane/ports/monitor_host.py",
           "src/alienintent/control_plane/application/monitor_supervision.py",
           "src/alienintent/control_plane/adapters/monitor_host_repository.py",
           "src/alienintent/control_plane/adapters/monitor_host_alerts.py",
           "src/alienintent/control_plane/adapters/systemd_host_manager.py",
           "src/alienintent/composition/monitor_host.py")
# Predecessor candidates composed unchanged: (BIU, issue, fixture, accepted candidate, landing merge).
PREDECESSORS = (
    ("WO-220304", 96, "FX-C4", "4c806feb8456c68a590b1482ae340338b7d47c7d", "3285c9e087b78909501995a662a008e9e0565dc5"),
    ("WO-220306", 112, "FX-L1", "3cac3912ff7f7d17648fc8dcee4ab7195baaefc8", "1753fde3638c26e47f33d793e59d11a6799ce74b"),
)
# One discriminating control per material failure class. Classes 2 and 3 each name two distinct
# invariants (stall detection / preservation; restart grant / observation identity). Applied once
# each, in a disposable copy.
# (control, failure class, file, needle, replacement, pytest node ids, required assertions)
CONTROLS = (
    ("host_outside_unit_accepted",
     "supervisor ownership is external to the model session and attributable to the intended invocation",
     "src/alienintent/composition/monitor_host.py",
     '        if cgroup() != ownership.cgroup:\n            raise HostHold("HOST_OUTSIDE_OWNED_UNIT")\n', "",
     ("test_host_refuses_to_run_outside_its_owned_unit",),
     ("a process outside the owned unit (a session or shell background process) must not host the monitor",)),
    ("stall_trusts_running_unit",
     "terminate or stall: external health detection observes the failure",
     "src/alienintent/control_plane/domain/monitor_host.py",
     "    if report.status in (HealthStatus.STALE, HealthStatus.UNVERIFIED):\n", "    if False:\n",
     ("test_stalled_host_is_detected_externally_and_restart_preserves_generation_and_pending_state",),
     ("a stalled host with a running unit must be detected from the durable health record",)),
    ("restart_clean_start",
     "authorized restart preserves generation/pending state rather than fabricating a clean start",
     "src/alienintent/composition/monitor_host.py",
     "        self.monitor = MonitorProfile(root, project=config.project,",
     # A restarted host (predecessor generation > 0) reopens a fresh store: a fabricated clean start.
     "        self.monitor = MonitorProfile((root / launch_id).mkdir() or root / launch_id "
     "if ownership.predecessor_generation else root, project=config.project,",
     ("test_stalled_host_is_detected_externally_and_restart_preserves_generation_and_pending_state",),
     ("restart must continue the generation, not fabricate a clean start",)),
    ("grant_identity_unchecked",
     "restart with wrong unit/invocation identity is refused; no duplicate host or silent substitution",
     "src/alienintent/control_plane/application/monitor_supervision.py",
     "        if (grant.profile, grant.unit, grant.host_invocation) != (binding.profile, binding.unit,\n"
     "                                                                   binding.host_invocation):\n"
     '            raise HostHold("GRANT_IDENTITY_MISMATCH")\n', "",
     ("test_restart_with_wrong_identity_is_refused",),
     ("a restart naming another unit, invocation, launch, alert or actor must be refused",)),
    ("observation_identity_unchecked",
     "observation with wrong unit/invocation identity is refused; no silent process substitution",
     "src/alienintent/control_plane/domain/monitor_host.py",
     "    if ownership.systemd_invocation_id is not None and unit.invocation_id != ownership.systemd_invocation_id:\n"
     '        return "UNIT_INVOCATION_MISMATCH"\n', "",
     ("test_observation_of_a_substituted_unit_or_instance_is_refused",),
     ("an observation of a unit the supervisor did not launch must be refused",)),
    ("non_systemd_mode_accepted",
     "missing/invalid supervision configuration holds before launch/restart",
     "src/alienintent/control_plane/domain/monitor_host.py",
     '        if document.get("schema_version") != 1 or document.get("mode") != "systemd":\n',
     '        if document.get("schema_version") != 1:\n',
     ("test_missing_or_invalid_configuration_holds_before_launch",),
     ("a missing or invalid supervision configuration must hold before launch",)),
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


def execute(cwd, argv, extra=None):
    environment = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd),
                   "PYTHONDONTWRITEBYTECODE": "1", **(extra or {})}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=1800)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def pytest(*targets):
    return [sys.executable, "-B", "-m", "pytest", "-q", "-rfEs", "-p", "no:cacheprovider", *targets]


def failed_ids(stdout):
    return sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", stdout, re.MULTILINE)))


def discriminates(assertions, intact, fault, restored):
    return (intact["exit_status"] == 0 and restored["exit_status"] == 0 and fault["exit_status"] == 1
            and all(a in fault["stdout"] for a in assertions) and "AssertionError" in fault["stdout"])


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=ROOT, text=True).strip()


def predecessor_custody():
    records = []
    for biu, issue, fixture, candidate, merge in PREDECESSORS:
        ancestry = {ref: subprocess.run(["git", "merge-base", "--is-ancestor", ref, "HEAD"], cwd=ROOT).returncode == 0
                    for ref in (candidate, merge)}
        records.append({"biu": biu, "issue": issue, "fixture": fixture, "accepted_candidate": candidate,
                        "landing_merge": git("rev-parse", merge), "ancestor_of_candidate": ancestry})
    return records


def checkpoint(output, report, mutations, stage):
    """Durable progress: an interrupted run reads as INCOMPLETE with a null exit, never as a pass."""
    record = report | {"run_state": "INCOMPLETE", "stage": stage, "exit_status": None,
                       "holds": report["holds"] + ["INCOMPLETE: run stopped at stage " + stage]}
    for name, body in (("execution-record.json", record),
                       ("proven-red.json", {"controls": mutations, "holds": record["holds"]})):
        partial = output / (name + ".partial")
        partial.write_text(json.dumps(body, indent=2) + "\n")
        os.replace(partial, output / name)


def baseline_regression():
    """The full Python suite at the admission baseline, in a disposable detached worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-c5-baseline-") as temporary:
        tree = Path(temporary) / "baseline"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), ADMISSION_BASELINE], cwd=ROOT,
                       check=True, capture_output=True)
        try:
            return execute(tree, pytest())
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)


def systemd_passed(observation):
    """The composed probe counts only if it actually ran on the real manager."""
    return (observation["exit_status"] == 0 and re.search(r"\b1 passed\b", observation["stdout"]) is not None
            and "skipped" not in observation["stdout"])


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220305.md"),
             Path("docs/evidence/wave2-readiness-assessments/WO-220305.2026-09-25T115944.821126Z.assessment.json"),
             Path("docs/evidence/wave2-design-contracts.json"), Path("docs/evidence/wave2-dependency-dag.json"),
             Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220305.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220305.allocation.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220305.proof-packet.md"),
             *(Path(f"docs/evidence/wave2-proof-fixtures/{f}/execution-record.json") for f in ("FX-C4", "FX-L1")),
             Path(TEST), Path(SYSTEMD_TEST), Path(__file__).relative_to(ROOT), *(Path(s) for s in SOURCES),
             Path("tools/verification/feature_regressions.json")]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-C5",
        "work_unit": "WO-220305", "issue": 114, "invocation": invocation,
        "source_revision": git("rev-parse", "HEAD"),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "predecessors": predecessor_custody(),
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths if (ROOT / p).exists()},
        "missing_inputs": [str(p) for p in paths if not (ROOT / p).exists()],
        "commands": [], "holds": [], "baseline_conditions": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "labels": ["REAL_USER_SYSTEMD_MANAGER_LOCAL", "FAKE_MANAGER_FOR_NEGATIVE_CONTROLS",
                   "RESTART_REQUIRES_GRANT_NO_AUTOMATIC_RETRY", "DOCTOR_CONFIGURATION_SURFACE_NOT_ADDED"],
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    if report["missing_inputs"]:
        report["holds"].append("pinned inputs missing")
    if not all(all(p["ancestor_of_candidate"].values()) for p in report["predecessors"]):
        report["holds"].append("a predecessor candidate is not an ancestor of this candidate")
    mutations, readback = [], None
    readback_path = Path(tempfile.mkdtemp(prefix="fx-c5-readback-")) / "readback.json"
    for label, command, extra in (
        ("focused", pytest(TEST), None),
        ("systemd_composed", pytest(SYSTEMD_TEST), {"FX_C5_READBACK": str(readback_path)}),
        ("bounded_initial_python", pytest("tests/control_plane/test_monitor_health.py",
                                          "tools/orchestration/test_factory_director_host.py"), None),
        ("bounded_initial_node", ["node", "--test", "test/systemd-supervision.test.mjs"], None),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE], None),
        ("architecture_fitness_tests", pytest("tests/test_architecture_fitness.py"), None),
        ("python_regression", pytest(), None),
        ("node_regression", ["node", "scripts/check.mjs", "all"], None),
    ):
        if label == "python_regression":
            checkpoint(output, report, mutations, "baseline_regression")
            try:
                baseline = baseline_regression()
                baseline_ref, baseline_failures = retain(output, baseline), failed_ids(baseline["stdout"])
            except (subprocess.CalledProcessError, OSError) as error:
                report["holds"].append("baseline regression unavailable: " + repr(error))
                baseline_ref, baseline_failures = None, None
        checkpoint(output, report, mutations, label)
        observation = execute(ROOT, command, extra)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        if label == "systemd_composed":
            entry["ran_on_real_manager"] = systemd_passed(observation)
            if not entry["ran_on_real_manager"]:
                report["holds"].append("systemd_composed did not pass on a real per-user manager (skip is a HOLD)")
            if readback_path.is_file():
                readback = json.loads(readback_path.read_text())
                entry["readback_ref"] = retain(output, readback)
            else:
                report["holds"].append("systemd_composed readback unavailable")
        elif label == "python_regression" and observation["exit_status"] != 0:
            failures = failed_ids(observation["stdout"])
            entry["failed"] = failures
            if failures and failures == baseline_failures:
                report["baseline_conditions"].append({
                    "condition": "PRE_EXISTING_BASELINE_FAILURE", "count": len(failures),
                    "baseline": ADMISSION_BASELINE, "baseline_ref": baseline_ref,
                    "note": "identical failing node ids at the admission baseline; no FX-C5 file is involved"})
            else:
                report["holds"].append(label + " failed beyond the recorded baseline condition")
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
        report["commands"].append(entry)
    shutil.rmtree(readback_path.parent, ignore_errors=True)
    with tempfile.TemporaryDirectory(prefix="fx-c5-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, failure_class, relative, needle, replacement, tests, assertions in CONTROLS:
            checkpoint(output, report, mutations, "control:" + name)
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                report["holds"].append(f"{name}: mutation count {count}, expected exactly one")
                mutations.append({"control": name, "file": relative, "application_count": count, "discriminates": False})
                continue
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
                "fault_failed": failed_ids(fault["stdout"]),
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    report["run_state"] = "COMPLETE"
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "class 1: supervisor external to the model session; durably attributable to the intended monitor invocation":
            ["test_launch_binds_the_owned_unit_to_the_monitor_invocation",
             "test_host_refuses_to_run_outside_its_owned_unit", "test_constructing_the_supervisor_launches_nothing",
             "systemd_composed: launched stage, HOST_OUTSIDE_OWNED_UNIT from the session process"],
        "class 2: terminate or stall -> external detection/alert -> authorized restart preserves generation and "
        "pending state":
            ["test_stalled_host_is_detected_externally_and_restart_preserves_generation_and_pending_state",
             "test_terminated_host_is_detected_from_the_unit_before_health_goes_stale",
             "systemd_composed: stall_alerted (SIGSTOP), restarted_after_stall, SIGKILL alert, final"],
        "class 3: wrong unit/invocation identity refused; no duplicate host ownership or silent substitution":
            ["test_restart_with_wrong_identity_is_refused", "test_restart_of_a_healthy_host_or_duplicate_launch_is_refused",
             "test_observation_of_a_substituted_unit_or_instance_is_refused",
             "test_monitor_instance_not_launched_by_the_supervisor_is_refused",
             "systemd_composed: wrong_identity_refused"],
        "class 4: missing/invalid supervision configuration holds before launch/restart":
            ["test_missing_or_invalid_configuration_holds_before_launch",
             "test_supervisor_without_configuration_or_manager_holds_before_any_mutation",
             "test_restart_under_a_changed_configuration_holds"],
        "negative controls": ["proven-red.json: " + ", ".join(c[0] for c in CONTROLS)],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "systemd_command": report["commands"][1],
        "composed_readback": readback,
        "boundaries": "local/composed proof only on this workstation's per-user systemd manager; no bootstrap "
                      "monitor/observer service retired or reconfigured; no operational replacement, live G+I, "
                      "cutover or retirement; Doctor configuration stays with SF-REQ-037/038",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]},
        indent=2, default=str) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-C5", "exit_status": report["exit_status"], "holds": report["holds"],
                      "baseline_conditions": len(report["baseline_conditions"]), "controls": len(mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
