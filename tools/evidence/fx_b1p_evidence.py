"""FX-B1P local, self-supervised proof (WO-220610): the live trajectory-capture composition.

Runs against committed source; output must be a new directory, and every rerun keeps its own
immutable observations. The real per-user systemd manager is required for the composed probe:
a skipped or unavailable manager is a HOLD, never a PASS. The execution record is rewritten
after every stage, so a stopped run leaves a durable INCOMPLETE record. Nothing here binds an
operational target, touches a live host, queue, provider, bootstrap service or profile.
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
TEST = "tests/evidence_learning/test_trajectory_capture.py"
HOST_TEST = "tests/composition/test_trajectory_capture_host.py"
SYSTEMD_TEST = "tests/composition/test_trajectory_capture_systemd.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-B1P/FX-B1P.md"
ADMISSION_BASELINE = "322baf4ae45776acb59d303370b12d48d76085ee"
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
SOURCES = ("src/alienintent/evidence_learning/domain/trajectory_capture.py",
           "src/alienintent/evidence_learning/ports/trajectory_journal.py",
           "src/alienintent/evidence_learning/adapters/trajectory_journal.py",
           "src/alienintent/evidence_learning/application/trajectory_capture_service.py",
           "src/alienintent/composition/trajectory_capture.py")
# Predecessor sources this node composes and must leave byte-identical to the admission baseline.
UNCHANGED = ("src/alienintent/composition/monitor_host.py", "src/alienintent/composition/offline_proof.py",
             "src/alienintent/control_plane/domain/monitor_host.py",
             "src/alienintent/control_plane/ports/monitor_host.py",
             "src/alienintent/control_plane/application/monitor_supervision.py",
             "src/alienintent/control_plane/adapters/monitor_host_repository.py",
             "src/alienintent/control_plane/adapters/monitor_host_alerts.py",
             "src/alienintent/control_plane/adapters/systemd_host_manager.py",
             "src/alienintent/evidence_learning/adapters/local_evidence_repository.py",
             "src/alienintent/execution_coordination/adapters/sqlite_store.py")
# (BIU, DAG node, issue, fixture, accepted candidate, landing merge).
PREDECESSORS = (
    ("WO-220101", "S0", 69, "FX-S0", "761a3cb4d6e24dc24ec370de45e25fe8c505eeda",
     "9174849713df2685117de7a8150126d916a4b644"),
    ("WO-220305", "C5", 114, "FX-C5", "ef29d04e9c6bbc4fe3211472daa66819aca7298d",
     "7ccb1e74b1abd3bfe356595258d5222b6ede91cb"),
)
DOMAIN = "src/alienintent/evidence_learning/domain/trajectory_capture.py"
SERVICE = "src/alienintent/evidence_learning/application/trajectory_capture_service.py"
COMPOSITION = "src/alienintent/composition/trajectory_capture.py"
RESTART = TEST + "::test_restart_reconciles_accepted_events_without_loss_or_duplication"
SEEDED = TEST + "::test_each_seeded_anomaly_class_is_recorded_durably"
# One discriminating control per material failure class and anomaly kind, applied once each in a
# disposable copy: (control, failure class, file, needle, replacement, pytest node ids that must fail).
CONTROLS = (
    ("order_from_journal_position", "identity/order/timestamp assignment is incorrect", DOMAIN,
     '    event = {"capture_seq": state.events + 1,', '    event = {"capture_seq": state.entries + 1,',
     (TEST + "::test_capture_assigns_identity_order_and_time",)),
    ("capture_time_not_monotonic", "identity/order/timestamp assignment is incorrect", DOMAIN,
     "        captured_at = state.last_captured_at\n", "", (SEEDED,)),
    ("ack_without_durable_commit", "an already-accepted event is lost across the restart", SERVICE,
     "        self.version = self.journal.append(self.version, entry)\n",
     '        self.version = self.version if entry["kind"] == "EVENT" else self.journal.append(self.version, entry)\n',
     (RESTART,)),
    ("duplicate_recaptured", "an already-accepted event is duplicated across the restart", DOMAIN,
     "    original = state.event_ids.get((submission.source, submission.event_id))\n", "    original = None\n",
     (RESTART, SEEDED)),
    ("restart_clean_start", "a supervised restart does not reconcile the accepted journal", COMPOSITION,
     "stream=config.host_invocation,", "stream=invocation,",
     (HOST_TEST + "::test_a_killed_capture_is_detected_and_its_granted_restart_loses_and_duplicates_nothing",)),
    ("sequence_gap_undetected", "a seeded anomaly class is not detected or not recorded durably", DOMAIN,
     "    if submission.source_seq > high_seq + 1:\n", "    if False:\n", (SEEDED,)),
    ("out_of_order_undetected", "a seeded anomaly class is not detected or not recorded durably", DOMAIN,
     "    elif submission.source_seq <= high_seq:\n", "    elif False:\n", (SEEDED,)),
    ("timestamp_regression_undetected", "a seeded anomaly class is not detected or not recorded durably", DOMAIN,
     "    if submission.source_seq > high_seq and high_observed is not None and submission.observed_at < high_observed:\n",
     "    if False:\n", (SEEDED, TEST + "::test_source_clock_regression_is_measured_against_the_highest_reported_time")),
    ("capture_stall_undetected", "a seeded anomaly class is not detected or not recorded durably", DOMAIN,
     "    if since is None or now - since <= policy.stall_micros or state.stalled_since == since:\n",
     "    if True:\n", (SEEDED,)),
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
                   "PYTHONDONTWRITEBYTECODE": "1",
                   "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}", **(extra or {})}
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


def discriminates(targets, intact, fault, restored):
    failed = failed_ids(fault["stdout"])
    return (intact["exit_status"] == 0 and restored["exit_status"] == 0 and fault["exit_status"] == 1
            and all(any(f == t or f.startswith(t + " ") for f in failed) for t in targets))


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=ROOT, text=True).strip()


def predecessor_custody():
    records = []
    for biu, node, issue, fixture, candidate, merge in PREDECESSORS:
        ancestry = {ref: subprocess.run(["git", "merge-base", "--is-ancestor", ref, "HEAD"], cwd=ROOT).returncode == 0
                    for ref in (candidate, merge)}
        records.append({"biu": biu, "dag_node": node, "issue": issue, "fixture": fixture,
                        "accepted_candidate": candidate, "landing_merge": git("rev-parse", merge),
                        "ancestor_of_candidate": ancestry})
    return records


def unchanged_sources():
    changed = subprocess.run(["git", "diff", "--name-only", ADMISSION_BASELINE, "HEAD", "--", *UNCHANGED], cwd=ROOT,
                             text=True, capture_output=True, check=True).stdout.split()
    return {"baseline": ADMISSION_BASELINE, "paths": list(UNCHANGED), "changed": changed}


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
    with tempfile.TemporaryDirectory(prefix="fx-b1p-baseline-") as temporary:
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
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220610.md"),
             Path("docs/evidence/wave2-readiness-assessments/WO-220610.2026-09-27T023136.204114Z.assessment.json"),
             Path("docs/evidence/wave2-dependency-dag.json"), Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220610.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220610.allocation.json"),
             *(Path(f"docs/evidence/wave2-proof-fixtures/{f}/execution-record.json") for f in ("FX-C5",)),
             Path(TEST), Path(HOST_TEST), Path(SYSTEMD_TEST), Path(__file__).relative_to(ROOT),
             *(Path(s) for s in SOURCES), *(Path(s) for s in UNCHANGED),
             Path("tools/verification/feature_regressions.json")]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-B1P",
        "work_unit": "WO-220610", "dag_node": "B1P", "issue": 140, "invocation": invocation,
        "source_revision": git("rev-parse", "HEAD"),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "predecessors": predecessor_custody(),
        "unchanged_predecessor_sources": unchanged_sources(),
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths if (ROOT / p).exists()},
        "missing_inputs": [str(p) for p in paths if not (ROOT / p).exists()],
        "commands": [], "holds": [], "baseline_conditions": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_SELF_SUPERVISED", "live_proof": "NOT_ESTABLISHED",
        "labels": ["REAL_USER_SYSTEMD_MANAGER_LOCAL", "C5_SUPERVISION_REUSED_UNCHANGED",
                   "FAKE_MANAGER_FOR_COMPOSED_NEGATIVE_CONTROLS", "SYNTHETIC_SOURCE_DIRECT_FEED",
                   "NO_BUFFERED_UPSTREAM_SOURCE", "NO_OPERATIONAL_TARGET_BOUND"],
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    if report["missing_inputs"]:
        report["holds"].append("pinned inputs missing")
    if not all(all(p["ancestor_of_candidate"].values()) for p in report["predecessors"]):
        report["holds"].append("a predecessor candidate is not an ancestor of this candidate")
    if report["unchanged_predecessor_sources"]["changed"]:
        report["holds"].append("a composed predecessor source changed from the admission baseline")
    mutations, readback = [], None
    readback_path = Path(tempfile.mkdtemp(prefix="fx-b1p-readback-")) / "readback.json"
    for label, command, extra in (
        ("focused", pytest(TEST, HOST_TEST), None),
        ("systemd_composed", pytest(SYSTEMD_TEST), {"FX_B1P_READBACK": str(readback_path)}),
        ("c5_regression", pytest("tests/control_plane/test_monitor_host.py",
                                 "tests/control_plane/test_monitor_host_systemd.py"), None),
        ("s0_regression", pytest("tests/composition/test_offline_proof.py"), None),
        ("feature_regressions", [sys.executable, "-B", "tools/verification/run_feature_regressions.py",
                                 "--base", ADMISSION_BASELINE, "--candidate", "HEAD"], None),
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
        elif label == "c5_regression" and (observation["exit_status"] != 0 or "skipped" in observation["stdout"]):
            report["holds"].append("c5_regression failed or skipped its real-manager probe")
        elif label == "python_regression" and observation["exit_status"] != 0:
            failures = failed_ids(observation["stdout"])
            entry["failed"] = failures
            if failures and failures == baseline_failures:
                report["baseline_conditions"].append({
                    "condition": "PRE_EXISTING_BASELINE_FAILURE", "count": len(failures),
                    "baseline": ADMISSION_BASELINE, "baseline_ref": baseline_ref,
                    "note": "identical failing node ids at the admission baseline; no FX-B1P file is involved"})
            else:
                report["holds"].append(label + " failed beyond the recorded baseline condition")
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
        report["commands"].append(entry)
    shutil.rmtree(readback_path.parent, ignore_errors=True)
    with tempfile.TemporaryDirectory(prefix="fx-b1p-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, failure_class, relative, needle, replacement, targets in CONTROLS:
            checkpoint(output, report, mutations, "control:" + name)
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                report["holds"].append(f"{name}: mutation count {count}, expected exactly one")
                mutations.append({"control": name, "file": relative, "application_count": count, "discriminates": False})
                continue
            command = pytest(*targets)
            intact = execute(copy, command)
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            ok = discriminates(targets, intact, fault, restored)
            mutations.append({"control": name, "failure_class": failure_class, "file": relative,
                "application_count": count, "source_digest": digest(original.encode()),
                "mutation": {"remove": needle, "replace_with": replacement}, "command": command,
                "required_failures": list(targets), "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "fault_failed": failed_ids(fault["stdout"]),
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    report["run_state"] = "COMPLETE"
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "(a) identity/order/timestamp assignment is stable and correct across a supervised kill/restart":
            ["test_capture_assigns_identity_order_and_time",
             "test_restart_reconciles_accepted_events_without_loss_or_duplication",
             "systemd_composed: acks vs journal after restart (capture_seq, identity, captured_at unchanged)"],
        "(b) every already-accepted event survives the restart without loss or duplication":
            ["test_restart_reconciles_accepted_events_without_loss_or_duplication",
             "test_an_unacknowledged_submission_was_never_accepted",
             "test_a_killed_capture_is_detected_and_its_granted_restart_loses_and_duplicates_nothing",
             "systemd_composed: SIGKILL -> observer alert -> granted restart; retry recorded DUPLICATE"],
        "(c) each seeded anomaly class produces a durable anomaly evidence record":
            ["test_each_seeded_anomaly_class_is_recorded_durably",
             "test_stall_is_measured_from_the_later_of_last_event_and_session_and_not_repeated",
             "systemd_composed: all five kinds read back after restart"],
        "(d) captured events and anomaly records are durably persisted and readable after restart":
            ["test_restart_reconciles_accepted_events_without_loss_or_duplication",
             "test_a_broken_or_inconsistent_journal_holds", "systemd_composed: restarted stage journal readback"],
        "(e) runs under this operator's own local systemd --user supervision only":
            ["test_the_c5_supervisor_launches_and_observes_the_capture_host",
             "test_the_capture_host_refuses_outside_its_owned_unit_before_opening_the_journal",
             "systemd_composed: transient units removed at the end of the run"],
        "C5 / WO-220101 not regressed": ["unchanged_predecessor_sources", "c5_regression", "s0_regression"],
        "negative controls": ["proven-red.json: " + ", ".join(c[0] for c in CONTROLS)],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "systemd_command": report["commands"][1],
        "composed_readback": readback,
        "boundaries": "local self-supervised proof only on this workstation's per-user systemd manager; synthetic "
                      "events fed directly; no operational target, live trajectory receipts, buffered upstream "
                      "source, observer replacement or retirement",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]},
        indent=2, default=str) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-B1P", "exit_status": report["exit_status"], "holds": report["holds"],
                      "baseline_conditions": len(report["baseline_conditions"]), "controls": len(mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
