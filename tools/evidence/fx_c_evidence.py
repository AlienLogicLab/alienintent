"""FX-C disposable local proof (WO-220307). Never touches a live host, queue, provider or profile.

Run against committed source; output must be a new directory. Every rerun keeps its own
immutable observations. The final custody comment identifies the evidence commit, whose
source files must match the recorded source candidate digests. The execution record is rewritten
after every stage, so a run stopped at any point leaves a durable INCOMPLETE record (a HOLD, never a PASS).
"""
from dataclasses import asdict
from hashlib import sha256
import argparse
import gc
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "src/alienintent/composition/bounded_control_profile.py"
TEST = "tests/composition/test_bounded_control_capstone.py"
BOUNDED = ("tests/control_plane/test_episode_control.py", "tests/control_plane/test_attention.py",
           "tests/control_plane/test_monitor_health.py")
PREDECESSOR_L1 = "tests/execution_coordination/test_liveness_reconciliation.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-C/FX-C.md"
ADMISSION_BASELINE = "b86b9fbd1978ccf3c341155d0dd64d153ad6cb19"
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
# Predecessor candidates composed unchanged: (BIU, issue, fixture, accepted candidate, landing merge).
PREDECESSORS = (
    ("WO-220303", 99, "FX-C3", "d69c00480c895da80d63eb185b534ca1befad0c7", "fc5c0a7"),
    ("WO-220304", 96, "FX-C4", "4c806feb8456c68a590b1482ae340338b7d47c7d", "3285c9e087b78909501995a662a008e9e0565dc5"),
    ("WO-220306", 112, "FX-L1", "3cac3912ff7f7d17648fc8dcee4ab7195baaefc8", "1753fde3638c26e47f33d793e59d11a6799ce74b"),
)
# One discriminating control per material failure class, applied once each in a disposable copy.
# (control, failure class, file, needle, replacement, pytest node ids, required assertions)
CONTROLS = (
    # Drops the acting-process check, so an old-epoch process can send by copying the current identity.
    ("stale_epoch_sends",
     "episode termination/restart reconstructs the same authorized state and stale epoch actions cannot send",
     "src/alienintent/control_plane/application/episode_control.py",
     "        if (result.epoch, result.invocation, self.invocation) != (record.epoch, record.invocation, record.invocation):",
     "        if (result.epoch, result.invocation) != (record.epoch, record.invocation):",
     ("test_episode_end_during_duplicate_and_delayed_outcomes",),
     ("a stale epoch cannot send",)),
    ("judgment_attention_detached",
     "durable attention survives restart and completed judgment suppresses recovery until resolution",
     PROFILE, "attention=self.attention, monitor=self.monitor,",
     'attention=AttentionProfile(Path(__import__("tempfile").mkdtemp()), project=project, name=name, '
     'invocation=invocation, clock=lambda: "detached", next_id=lambda: "detached", resolvers=resolvers), '
     "monitor=self.monitor,",
     ("test_judgment_attention_survives_episode_end_and_suppresses_recovery",),
     ("judgment attention must be durable in the store every fresh context reconstructs",)),
    ("health_bridge_unconditional",
     "stopped/stale/degraded monitor evidence stays explicit and never becomes a healthy claim",
     "src/alienintent/composition/liveness_profile.py",
     "        return str(report.status), report.reason\n", '        return "HEALTHY", "IN_BOUND"\n',
     ("test_stopped_scans_surface_stale_or_degraded_never_healthy",),
     ("a scan must never claim G+I while the monitor's ticks have stopped",)),
    ("identity_fence_removed",
     "duplicate/delayed outcomes preserve one authorized effect/readback identity across the composed path",
     "src/alienintent/execution_coordination/application/liveness.py",
     "        key = expected.effect_key\n", '        key = expected.effect_key + ":" + source\n',
     ("test_episode_end_during_duplicate_and_delayed_outcomes",),
     ("a duplicate recovery during the episode end must not create a second intent",)),
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
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=1800)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def pytest(*targets):
    return [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets]


def failed_ids(stdout):
    return sorted(set(re.findall(r"^(?:FAILED|ERROR) (\S+)", stdout, re.MULTILINE)))


def discriminates(assertions, intact, fault, restored):
    return (intact["exit_status"] == 0 and restored["exit_status"] == 0 and fault["exit_status"] == 1
            and all(a in fault["stdout"] for a in assertions) and "AssertionError" in fault["stdout"])


def git(*argv):
    return subprocess.check_output(["git", *argv], cwd=ROOT, text=True).strip()


def predecessor_custody():
    """Each predecessor candidate and its landing merge must be ancestors of this candidate."""
    records = []
    for biu, issue, fixture, candidate, merge in PREDECESSORS:
        ancestry = {ref: subprocess.run(["git", "merge-base", "--is-ancestor", ref, "HEAD"], cwd=ROOT).returncode == 0
                    for ref in (candidate, merge)}
        records.append({"biu": biu, "issue": issue, "fixture": fixture, "accepted_candidate": candidate,
                        "landing_merge": git("rev-parse", merge), "ancestor_of_candidate": ancestry})
    return records


def checkpoint(output, report, mutations, stage):
    """Durable progress: an interrupted run reads as INCOMPLETE with a non-null exit, never as a pass."""
    record = report | {"run_state": "INCOMPLETE", "stage": stage, "exit_status": None,
                       "holds": report["holds"] + ["INCOMPLETE: run stopped at stage " + stage]}
    for name, body in (("execution-record.json", record),
                       ("proven-red.json", {"controls": mutations, "holds": record["holds"]})):
        partial = output / (name + ".partial")
        partial.write_text(json.dumps(body, indent=2) + "\n")
        os.replace(partial, output / name)


def baseline_regression(output):
    """The full Python suite at the admission baseline, in a disposable detached worktree."""
    with tempfile.TemporaryDirectory(prefix="fx-c-baseline-") as temporary:
        tree = Path(temporary) / "baseline"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), ADMISSION_BASELINE], cwd=ROOT,
                       check=True, capture_output=True)
        try:
            observation = execute(tree, pytest())
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)
    return observation, retain(output, observation)


def readback(output):
    """Composed disposable runs; every value below is read back from the durable stores."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tests.context_assembly.test_context_reconstruction import seed
    from tests.composition import test_bounded_control_capstone as fx
    from alienintent.execution_coordination.domain.liveness import CorrelatedOutcome
    with tempfile.TemporaryDirectory(prefix="fx-c-readback-") as temporary:
        roots = {name: Path(temporary) / name for name in ("recovery", "judgment")}
        for root in roots.values():
            root.mkdir()
            seed(root)
        # Episode end while a dispatched verifier is still in flight; a fresh context completes it once.
        clock = fx.Clock()
        first = fx.open_first(roots["recovery"], clock)
        effect = fx.verifier_effect()
        ended_view = fx.reconstruct(first)
        lifecycle, _ = first.liveness.store.read_state(fx.PROFILE, "liveness-active:" + fx.OBJECTIVE)
        clock.now = fx.T0 + fx.G - 5 * fx.SECOND
        first.liveness.admission.intend(fx.known(), lifecycle, effect, "original-delivery:coordinator-epoch-1")
        ended = first.episode.episodes.end(fx.OBJECTIVE, epoch=1, actor="director")
        during_end = fx.scan(first, clock, fx.T0 + fx.G)
        del first
        gc.collect()
        clock.now = fx.T0 + fx.G + fx.C
        fresh = fx.compose(roots["recovery"], clock, "coordinator-epoch-2")
        fresh_view = fx.reconstruct(fresh)
        independent_view = fx.reconstruct_independently(roots["recovery"])
        fresh.monitor.monitor.start()
        reopened = fresh.liveness.reconciler.start()
        epoch2 = fx.begin(fresh)
        receipt = fresh.liveness.store.readback_guarded(fx.PROFILE, effect.effect_key)
        recovery = {
            "ended_episode": ended.document(), "scan_during_end": asdict(during_end),
            "reconstruction_equal": ended_view == fresh_view == independent_view, "fresh_view": fresh_view,
            "reopened": [asdict(r) for r in reopened], "consumer_outcomes": fx.consumers(fresh),
            "readback_receipt": None if receipt is None else asdict(receipt),
            "lane": fresh.liveness.store.read_state(fx.PROFILE, "liveness-lane:" + effect.effect_key),
            "episode_pointer": fresh.episode.store.read_state(fx.PROFILE, "episode:" + fx.OBJECTIVE),
            "episode_history": [h["event"] for h in fresh.episode.repository.history(fx.OBJECTIVE)],
            "epoch_2": epoch2.document(), "monitor": asdict(fresh.monitor.repository.read(fx.PROFILE))}
        # A judgment outcome: durable attention, a blocked-limit end and suppression after restart.
        clock, timer = fx.Clock(), fx.Timer()
        first = fx.open_first(roots["judgment"], clock, timer=timer)
        clock.now = fx.T0 + 10 * fx.SECOND
        first.liveness.journal.record_outcome(
            CorrelatedOutcome("verifier-outcome-1", fx.OBJECTIVE, 1, "verifier", "HUMAN_DECISION_REQUIRED", 1))
        fx.scan(first, clock, fx.T0 + fx.G)
        first.episode.episodes.tick(fx.OBJECTIVE)
        fx.run_monitor(first, clock, clock.now + 300 * fx.SECOND)
        blocked_end = first.episode.episodes.tick(fx.OBJECTIVE)
        del first
        gc.collect()
        clock.now = fx.T0 + 20 * fx.G
        fresh = fx.compose(roots["judgment"], clock, "coordinator-epoch-2")
        fresh.monitor.monitor.start()
        fresh.liveness.reconciler.start()
        suppressed = fx.scan(fresh, clock, clock.now + fx.SECOND)
        clock.now += 2 * fx.I + fx.SECOND
        stale_claim = fresh.liveness.reconciler.scan().bound_claim
        judgment = {
            "blocked_end": blocked_end.document(), "suppressed_scan": asdict(suppressed),
            "attention": [asdict(i) for i in fx.judgment_items(fresh.attention.attention)],
            "fresh_view": fx.reconstruct(fresh), "consumer_outcomes": fx.consumers(fresh),
            "stopped_ticks_claim": stale_claim, "monitor_inspection": asdict(fresh.monitor.monitor.inspect()),
            "hold_records": fresh.liveness.store.list_states(fx.PROFILE, "liveness-hold:")}
        body = {"recovery": recovery, "judgment": judgment}
        assert recovery["reconstruction_equal"] and len(recovery["consumer_outcomes"]) == 1
        assert judgment["consumer_outcomes"] == [] and len(judgment["attention"]) == 1
        assert str(ended.cause) == "EXPLICIT_REQUEST" and str(blocked_end.cause) == "BLOCKED_LIMIT"
        assert stale_claim.startswith("WITHDRAWN:STALE:")
        return retain(output, body), body


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220307.md"),
             Path("docs/evidence/wave2-readiness-assessments/WO-220307.2026-09-25T221218.340064Z.assessment.json"),
             Path("docs/evidence/wave2-design-contracts.json"), Path("docs/evidence/wave2-dependency-dag.json"),
             Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220307.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220307.allocation.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220307.proof-packet.md"),
             *(Path(f"docs/evidence/wave2-proof-fixtures/{f}/execution-record.json") for f in ("FX-C3", "FX-C4", "FX-L1")),
             Path(TEST), Path(__file__).relative_to(ROOT), Path(PROFILE),
             *(Path(c[2]) for c in CONTROLS if c[2] != PROFILE)]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-C",
        "work_unit": "WO-220307", "issue": 118, "invocation": invocation,
        "source_revision": git("rev-parse", "HEAD"),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "predecessors": predecessor_custody(),
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
    if not all(all(p["ancestor_of_candidate"].values()) for p in report["predecessors"]):
        report["holds"].append("a predecessor candidate is not an ancestor of this candidate")
    mutations = []
    for label, command in (
        ("focused", pytest(TEST)),
        ("bounded_initial", pytest(*BOUNDED)),
        ("predecessor_l1", pytest(PREDECESSOR_L1)),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", pytest("tests/test_architecture_fitness.py")),
        ("python_regression", pytest()),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        if label == "python_regression":
            # The slow baseline suite runs after the focused proof, so a stopped run has already kept it.
            checkpoint(output, report, mutations, "baseline_regression")
            try:
                baseline, baseline_ref = baseline_regression(output)
                baseline_failures = failed_ids(baseline["stdout"])
            except (subprocess.CalledProcessError, OSError) as error:
                report["holds"].append("baseline regression unavailable: " + repr(error))
                baseline_ref, baseline_failures = None, None
        checkpoint(output, report, mutations, label)
        observation = execute(ROOT, command)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        if label == "python_regression" and observation["exit_status"] != 0:
            failures = failed_ids(observation["stdout"])
            entry["failed"] = failures
            if failures and failures == baseline_failures:
                report["baseline_conditions"].append({
                    "condition": "PRE_EXISTING_BASELINE_FAILURE", "count": len(failures),
                    "baseline": ADMISSION_BASELINE, "baseline_ref": baseline_ref,
                    "note": "identical failing node ids at the admission baseline; no FX-C file is involved"})
            else:
                report["holds"].append(label + " failed beyond the recorded baseline condition")
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
        report["commands"].append(entry)
    with tempfile.TemporaryDirectory(prefix="fx-c-controls-") as temporary:
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
                "intact_ref": retain(output, intact), "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": ok})
            if not ok:
                report["holds"].append(name + " did not discriminate")
    checkpoint(output, report, mutations, "readback")
    try:
        report["readback_ref"], observed = readback(output)
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
        observed = None
    report["run_state"] = "COMPLETE"
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {
        "SF-REQ-053-AC-04 / FX-C: end a coordinator episode during duplicate/delayed outcomes; stale epoch cannot send":
            ["test_episode_end_during_duplicate_and_delayed_outcomes"],
        "FX-C: a fresh context reconstructs identical authorized actions (authorized_view predicate; class 1 over "
        "unchanged C2 state, class 2 over the judged state including the pending item)":
            ["test_episode_end_during_duplicate_and_delayed_outcomes",
             "test_judgment_attention_survives_episode_end_and_suppresses_recovery"],
        "FX-C / SF-REQ-053-AC-04: attention survives; duplicate observation/restart keeps one identity":
            ["test_judgment_attention_survives_episode_end_and_suppresses_recovery"],
        "FX-C: completed judgment suppresses recovery; valid resolution permits reinspection only":
            ["test_judgment_attention_survives_episode_end_and_suppresses_recovery"],
        "FX-C: one authorized effect/readback identity under duplicate/delayed outcomes":
            ["test_episode_end_during_duplicate_and_delayed_outcomes"],
        "FX-C / SF-REQ-053-AC-04: stopped scans surface DEGRADED/STALE; monitor continues after the episode ends":
            ["test_stopped_scans_surface_stale_or_degraded_never_healthy"],
        "composition boundary: constructing starts nothing; missing policy blocks startup":
            ["test_constructing_the_composition_starts_nothing"],
        "negative controls (one per material failure class)": ["proven-red.json: " + ", ".join(c[0] for c in CONTROLS)],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"),
        "composed_readback": observed,
        "boundaries": "local/composed fixture only; host unassigned (R1-GAP-MONITOR-HOST); no supervised-host "
                      "deployment, bootstrap replacement, live G+I, live transport, cutover, sovereignty or retirement",
        "proof_level": report["proof_level"], "live_proof": report["live_proof"], "exit_status": report["exit_status"]},
        indent=2, default=str) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-C", "exit_status": report["exit_status"], "holds": report["holds"],
                      "baseline_conditions": len(report["baseline_conditions"]), "controls": len(mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
