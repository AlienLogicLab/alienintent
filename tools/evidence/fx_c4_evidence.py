"""FX-C4 disposable local proof. Never touches a live host, queue, provider or profile.

Run against committed source; output must be a new directory. Every rerun keeps
its own immutable observations. The final custody comment identifies the evidence
commit, whose source files must match the recorded source candidate digests.
"""
from dataclasses import asdict
from hashlib import sha256
import argparse
import gc
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DOMAIN = "src/alienintent/control_plane/domain/monitor_health.py"
APP = "src/alienintent/control_plane/application/monitor_health.py"
ADAPTER = "src/alienintent/control_plane/adapters/monitor_health_repository.py"
PROFILE = "src/alienintent/composition/control_plane_profile.py"
PORTS = ("src/alienintent/control_plane/ports/monitor_health.py", "src/alienintent/execution_coordination/ports/scan_progress.py")
TEST = "tests/control_plane/test_monitor_health.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-C4/FX-C4.md"
ADMISSION_BASELINE = "710da9053eafa7d0cebe8ee33525aa2f8a9ebdf9"
LABELS = ("LOCAL_EPISODE_END_STAND_IN", "SCAN_AGE_FROM_LAST_COMPLETION")
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
_TIMING = ("    if _overdue(now - tick_reference, bound):\n"
           "        return HealthStatus.STALE, \"TICK_OVERDUE\"\n"
           "    if _overdue(now - scan_reference, bound):\n"
           "        return HealthStatus.STALE, \"SCAN_OVERDUE\"\n")
_DEGRADED = ("    if record.last_scan_outcome in INCOMPLETE_SCAN_OUTCOMES:\n"
             "        return HealthStatus.DEGRADED, \"SCAN_\" + record.last_scan_outcome\n")
_SERVICE = "        self.monitor = MonitorService(self.repository, profile=name, policy=policy, clock=clock, next_id=next_id)"
_TICK = '        return self._write(current, {"action": "TICK", "at": now}, last_monitor_tick=now)'
# (control, file, needle, replacement, pytest node ids or None for the architecture check, required assertions)
CONTROLS = (
    ("stale_boundary", DOMAIN, "    return age > bound", "    return age >= bound",
     ("test_tick_age_boundary[at]",), ("at exactly 2*I the monitor stays in bound",)),
    ("stale_bound_removed", DOMAIN, "    return age > bound", "    return False",
     ("test_tick_age_boundary[above]", "test_frozen_monitor_while_work_quiet"),
     ("above 2*I the monitor is STALE", "a frozen monitor is STALE even while work is quiet")),
    ("scan_overdue_removed", DOMAIN, "    if _overdue(now - scan_reference, bound):", "    if False:",
     ("test_scan_overdue_boundary[above]",), ("an overdue last scan completion is STALE",)),
    ("interval_hardcoded", DOMAIN, "    bound = 2 * policy.interval_micros", "    bound = 2 * Fraction(60) * 1_000_000",
     ("test_interval_from_policy",), ("the 2*I bound comes from the persisted policy interval",)),
    ("degraded_removed", DOMAIN, "    if record.last_scan_outcome in INCOMPLETE_SCAN_OUTCOMES:", "    if False:",
     ("test_failed_or_incomplete_scan",), ("a failed or incomplete latest scan is DEGRADED",)),
    ("incomplete_advances", APP, 'last_scan_outcome="STARTED"', 'last_scan_outcome="STARTED", last_scan_completed_at=now',
     ("test_failed_or_incomplete_scan[started_only]",), ("an incomplete scan must not advance last_scan_completed_at",)),
    ("precedence_swapped", DOMAIN, _TIMING + _DEGRADED, _DEGRADED + _TIMING,
     ("test_stale_precedes_degraded",), ("STALE takes precedence over DEGRADED",)),
    ("clock_regression_accepted", APP, "        if current is not None and now < current.record.latest_observation():",
     "        if False:", ("test_clock[regressing]",), ("DID NOT RAISE",)),
    ("persisted_regression_ignored", DOMAIN, "    if now < record.latest_observation():", "    if False:",
     ("test_clock[regressing_across_restart]",), ("a clock earlier than the persisted observation is UNVERIFIED",)),
    ("absent_clock_healthy", APP, 'return HealthReport(HealthStatus.UNVERIFIED, "CLOCK_ABSENT", record, None)',
     'return HealthReport(HealthStatus.HEALTHY, "CLOCK_ABSENT", record, None)',
     ("test_clock[absent]",), ("an absent clock is UNVERIFIED",)),
    ("unavailable_healthy", APP, "return HealthReport(HealthStatus.UNVERIFIED, snapshot.reason, None, None)",
     "return HealthReport(HealthStatus.HEALTHY, snapshot.reason, None, None)",
     ("test_store_unavailable",), ("an unreadable health store is UNVERIFIED",)),
    ("no_record_healthy", DOMAIN, 'return HealthStatus.UNVERIFIED, "NO_RECORD"', 'return HealthStatus.HEALTHY, "NO_RECORD"',
     ("test_no_record",), ("a missing record is UNVERIFIED",)),
    ("generation_reused", APP, "current.record.generation + 1", "current.record.generation",
     ("test_restart_new_generation",), ("restart must allocate a new generation",)),
    ("workload_gated_tick", APP, _TICK,
     '        if not any(h["observation"].get("active_work") for h in self.repository.history(self.profile)):\n'
     "            return current.record\n" + _TICK,
     ("test_quiet_work_is_not_health",), ("quiet work must not stop monitor ticks",)),
    ("episode_end_resets", PROFILE, _SERVICE, _SERVICE + "\n        self.monitor.start()",
     ("test_episode_end_preserves_monitor",), ("episode end must not reset monitor state",)),
    ("cas_bypassed", ADAPTER, "        version = self.store.commit(self.name, identity, expected_version,",
     "        version = self.store.commit(self.name, identity, self.store.read_state(self.name, identity)[0],",
     ("test_concurrent_writer_cas",), ("a concurrent stale writer must receive exactly one VersionConflict",)),
    ("composition_disconnected", PROFILE, "profile=name, policy=policy", 'profile=name + "-disconnected", policy=policy',
     ("test_monitor_profile_composed",), ("inspect must read the composed monitor record",)),
    ("adapter_import_added", APP, "from alienintent.control_plane.ports.monitor_health import MonitorRepository\n",
     "from alienintent.control_plane.ports.monitor_health import MonitorRepository\n"
     "from alienintent.control_plane.adapters.monitor_health_repository import DurableMonitorRepository\n",
     None, ("application imports adapters",)),
    # Producer addition after preparatory review; not one of the 18 pinned controls.
    ("stale_instance_accepted", APP, "        if (snapshot.record.instance_id, snapshot.record.generation) != self.instance:",
     "        if False:", ("test_stale_instance_cannot_write",), ("DID NOT RAISE",)),
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
    environment = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd),
                   "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=600)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def control_command(tests):
    if tests is None:
        return [sys.executable, "-B", *ARCHITECTURE]
    return [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *(TEST + "::" + t for t in tests)]


def discriminates(tests, assertions, fault, restored):
    if restored["exit_status"] != 0 or fault["exit_status"] != 1:
        return False
    if not all(a in fault["stdout"] for a in assertions):
        return False
    return tests is None or "AssertionError" in fault["stdout"] or "Failed: DID NOT RAISE" in fault["stdout"]


def readback(output, invocation):
    """Composed disposable run; every value below is read back from the durable store/evidence."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from alienintent.composition.control_plane_profile import MonitorProfile
    from alienintent.control_plane.domain.monitor_health import MonitorPolicy
    from tests.control_plane.test_monitor_health import I, SECOND, T0, Clock, FakeScanner, LaunchSpy, episode, outcome
    spy, clock, policy = LaunchSpy(), Clock(), MonitorPolicy(60)
    configuration = {"project": "project", "name": "fixture", "invocation": invocation,
                     "policy": {**policy.document(), "policy_digest": policy.digest()},
                     "clock": "injected UTC microseconds since epoch", "t0": T0,
                     "scanner": "injected fake scanner (COMPLETE, FAILED, STARTED-only)",
                     "labels": list(LABELS), "host": "unassigned (R1-GAP-MONITOR-HOST)"}
    with tempfile.TemporaryDirectory(prefix="fx-c4-readback-") as temporary:
        root = Path(temporary)
        names = iter(("instance-1", "instance-2"))
        def profile():
            return MonitorProfile(root, project="project", name="fixture", invocation=invocation,
                                  policy=policy, clock=clock, next_id=lambda: next(names))
        observations = []
        def observe(label, p, now):
            clock.now = now
            report = p.monitor.inspect()
            observations.append({"step": label, "now": now, "status": str(report.status), "reason": report.reason})
            return report
        p = profile()
        observe("before_start", p, T0)
        p.monitor.start()
        p.monitor.tick()
        scanner = FakeScanner(p.monitor)
        scanner.run(clock, outcome())
        active = episode(root / "episode", spy)
        observe("at_2I", p, T0 + 2 * I)
        observe("above_2I", p, T0 + 2 * I + 1)
        clock.now = T0 + 2 * I + 1
        p.monitor.tick()
        scanner.run(clock, outcome())
        observe("recovered", p, T0 + 2 * I + 1)
        scanner.run(clock, outcome("FAILED", "FX-C4 injected scan failure"), started_at=T0 + 2 * I + 2)
        observe("failed_scan", p, T0 + 2 * I + 3)
        scanner.run(clock, outcome(active_work=0), started_at=T0 + 3 * I, finished_at=T0 + 3 * I + SECOND)
        before = p.store.read_state("fixture", "monitor:fixture")
        history = p.repository.history("fixture")
        # LOCAL_EPISODE_END_STAND_IN: discard every service/activation object and reopen.
        del p, active, scanner
        gc.collect()
        reopened = profile()
        after = reopened.store.read_state("fixture", "monitor:fixture")
        assert after == before and reopened.repository.history("fixture") == history
        observe("after_episode_end", reopened, T0 + 3 * I + 2 * SECOND)
        clock.now = T0 + 4 * I
        restarted = reopened.monitor.start()
        assert restarted.generation == 2
        observe("restart_generation_2", reopened, T0 + 4 * I + SECOND)
        clock.now = T0 + 4 * I - SECOND
        observe("clock_regression", reopened, T0 + 4 * I - SECOND)
        assert spy.count == 0
        body = {"observations": observations, "episode_end": {"label": LABELS[0], "pointer_before": before,
                "pointer_after": after, "history_identical": True},
                "restart": asdict(restarted), "model_launch_count": spy.count,
                "monitor_history": reopened.repository.history("fixture"),
                "operational_readback": reopened.store.list_states("fixture", "monitor:"),
                "immutable_history_objects": {path.name: json.loads(path.read_bytes())
                    for path in sorted(reopened.evidence.objects.iterdir()) if not path.name.startswith(".")}}
        return retain(output, body), retain(output, configuration), spy.count, configuration["policy"], observations


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220304.md"),
             Path("docs/evidence/wave2-design-contracts.json"), Path("docs/evidence/wave2-dependency-dag.json"),
             Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220304.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220304.allocation.json"),
             Path("docs/evidence/wave2-proof-fixtures/FX-C1/execution-record.json"),
             Path(TEST), Path(__file__).relative_to(ROOT), *map(Path, (DOMAIN, APP, ADAPTER, PROFILE, *PORTS))]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-C4",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE,
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths},
        "labels": list(LABELS), "commands": [], "holds": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    for label, command in (
        ("focused", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", TEST]),
        ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"]),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_architecture_fitness.py"]),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        observation = execute(ROOT, command)
        report["commands"].append({"id": label, "command": command, "exit_status": observation["exit_status"],
                                   "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
    mutations = []
    with tempfile.TemporaryDirectory(prefix="fx-c4-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, relative, needle, replacement, tests, assertions in CONTROLS:
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f"{name}: mutation count {count}, expected exactly one")
            command = control_command(tests)
            intact = execute(copy, command)
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            ok = intact["exit_status"] == 0 and discriminates(tests, assertions, fault, restored)
            mutations.append({"control": name, "file": relative, "application_count": count,
                "source_digest": digest(original.encode()), "mutation": {"remove": needle, "replace_with": replacement},
                "command": command, "assertions": list(assertions), "intact_exit": intact["exit_status"],
                "fault_exit": fault["exit_status"], "restored_exit": restored["exit_status"],
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    try:
        (report["readback_ref"], report["profile_ref"], report["model_launch_count"],
         report["policy"], observed) = readback(output, invocation)
        report["profile_digest"] = report["profile_ref"]["revision_digest"]
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
        report["model_launch_count"], report["policy"], observed = None, None, None
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "persist instance/generation, tick and scan outcomes": ["test_restart_new_generation", "test_stale_instance_cannot_write", "test_monitor_profile_composed", "test_concurrent_writer_cas"],
        "independent of model life/workload": ["test_quiet_work_is_not_health", "test_independent_of_model_and_workload"],
        "at 2*I remains in bound, above becomes STALE": ["test_tick_age_boundary", "test_interval_from_policy", "test_scan_overdue_boundary", "test_tick_overdue_with_recent_scan", "test_frozen_monitor_while_work_quiet"],
        "failed/incomplete scan DEGRADED": ["test_failed_or_incomplete_scan", "test_stale_precedes_degraded"],
        "absent/unreadable/regressing clock UNVERIFIED": ["test_clock", "test_clock_invalid_reading", "test_store_unavailable", "test_malformed_pointer_unverified", "test_no_record"],
        "end episode without losing local monitor state": ["test_episode_end_preserves_monitor"],
        "missing/invalid policy blocks startup": ["test_policy_invalid_blocks_start"],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"),
        "composed_observations": observed, "model_launch_count": report["model_launch_count"],
        "labels": {"LOCAL_EPISODE_END_STAND_IN": "episode end = discard service/activation objects and reopen from the store; not C3 EpisodeControl",
                   "SCAN_AGE_FROM_LAST_COMPLETION": "scan staleness is now - last_scan_completed_at > 2*I; next_scan_due is recorded only"},
        "boundaries": "service/inspection fixture only; host unassigned (R1-GAP-MONITOR-HOST); no supervision, G/C policy, reconciliation or trajectory capture",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-C4", "exit_status": report["exit_status"], "holds": report["holds"],
                      "controls": len(mutations), "model_launch_count": report["model_launch_count"], "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
