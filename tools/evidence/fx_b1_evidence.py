"""FX-B1 local mechanical proof (WO-220504): the trajectory-receipts attention producer.

Runs against committed source; output must be a new directory, and every rerun keeps its own
immutable observations. Results are labelled LOCAL and never satisfy operational acceptance: the
operational run on the bound target is `tools/live/fx_b1_operational.py run`. The execution
record is rewritten after every stage, so a stopped run leaves a durable INCOMPLETE record.
Nothing here touches the bound target, a live host, provider, bootstrap service or observer.
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
TEST = "tests/composition/test_trajectory_receipts.py"
DRIVER_TEST = "tools/live/test_fx_b1_operational.py"
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-B1/FX-B1.md"
ADMISSION_BASELINE = "01764fccf144a536023854dd533b05952131cb44"
ARCHITECTURE = ("tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all")
SOURCES = ("src/alienintent/composition/trajectory_receipts.py", "tools/live/fx_b1_operational.py",
           "tools/live/fx_b1_audit.py")
# Predecessor sources this node composes and must leave byte-identical to the admission baseline.
UNCHANGED = ("src/alienintent/composition/trajectory_capture.py",
             "src/alienintent/evidence_learning/domain/trajectory_capture.py",
             "src/alienintent/evidence_learning/ports/trajectory_journal.py",
             "src/alienintent/evidence_learning/adapters/trajectory_journal.py",
             "src/alienintent/evidence_learning/application/trajectory_capture_service.py",
             "src/alienintent/composition/monitor_host.py",
             "src/alienintent/composition/control_plane_profile.py",
             "src/alienintent/composition/attention_inbox.py",
             "src/alienintent/control_plane/domain/attention.py",
             "src/alienintent/control_plane/application/attention.py",
             "src/alienintent/control_plane/adapters/attention_repository.py",
             "src/alienintent/control_plane/application/monitor_supervision.py",
             "src/alienintent/control_plane/adapters/systemd_host_manager.py",
             "src/alienintent/evidence_learning/adapters/local_evidence_repository.py",
             "src/alienintent/execution_coordination/adapters/sqlite_store.py")
# (BIU, DAG node, issue, fixture, accepted candidate, landing merge).
PREDECESSORS = (
    ("WO-220610", "B1P", 140, "FX-B1P", "2d3d1f970e262e5f330cfb848784c74a0c991a0d",
     "5f5d8de97046840c4562799972d3c10a75dafda0"),
)
RECEIPTS = "src/alienintent/composition/trajectory_receipts.py"
DRIVER = "tools/live/fx_b1_operational.py"
T = TEST + "::"
D = DRIVER_TEST + "::"
# One discriminating control per material failure class, applied once each in a disposable copy:
# (control, failure class, file, needle, replacement, pytest node ids that must fail).
CONTROLS = (
    ("receipt_skips_events", "an attention-producer consumer does not observe the captured receipts", RECEIPTS,
     '            event = entry["event"] if entry["kind"] == EVENT else None\n', "            event = None\n",
     (T + "test_receipts_observe_every_captured_event_with_its_journal_identity",)),
    ("attention_not_produced", "an anomaly is not consumed into the attention queue", RECEIPTS,
     '            for anomaly in entry["anomalies"]:\n', "            for anomaly in ():\n",
     (T + "test_each_anomaly_kind_yields_exactly_one_pending_judgment_item",)),
    ("prefix_unchecked", "pre/post-restart observations do not reconcile", RECEIPTS,
     '        if chain and chain[-1]["prefix_digest"] != prefix_digest(entries[:consumed]):\n', "        if False:\n",
     (T + "test_a_rewritten_or_overtaken_prefix_holds_and_writes_nothing",)),
    ("receipt_before_attention", "a crash loses an anomaly's attention item", RECEIPTS,
     "        fresh = entries[consumed:]\n",
     "        fresh = entries[consumed:]\n"
     "        if fresh:\n"
     '            self._append(version, {"schema_version": 1, "receipt_seq": version + 1, "to_entry": len(entries),\n'
     '                                   "prefix_digest": prefix_digest(entries), "entries": []})\n'
     "            version += 1\n",
     (T + "test_a_pass_that_dies_before_its_receipt_leaves_no_second_item",)),
    ("cursor_ignored", "an entry is consumed twice across restart", RECEIPTS,
     "        fresh = entries[consumed:]\n", "        fresh = entries\n",
     (T + "test_a_pass_with_nothing_new_writes_nothing",
      T + "test_passes_across_a_kill_and_granted_restart_reconcile_old_and_new_entries")),
    ("audit_blind", "a read of observer or factory state goes undetected", DRIVER,
     "    return sorted({p for p in paths if inside(p, protected) and not any(inside(p, a) for a in allowed)})\n",
     "    return []\n",
     (D + "test_the_audit_names_a_protected_read_outside_the_allowed_root",
      D + "test_the_audit_records_sqlite_opens_and_survives_a_failing_module")),
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
    with tempfile.TemporaryDirectory(prefix="fx-b1-baseline-") as temporary:
        tree = Path(temporary) / "baseline"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), ADMISSION_BASELINE], cwd=ROOT,
                       check=True, capture_output=True)
        try:
            return execute(tree, pytest())
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(CONTRACT), Path("docs/work-units/wave2/WO-220504.md"),
             Path("docs/evidence/wave2-readiness-assessments/WO-220504.2026-09-27T131311.200780Z.assessment.json"),
             Path("docs/evidence/wave2-dependency-dag.json"), Path("docs/evidence/wave2-candidate-bius.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220504.packet.json"),
             Path("docs/evidence/wave2-execution-packets/WO-220504.allocation.json"),
             Path("docs/evidence/wave2-proof-fixtures/FX-B1P/FX-B1P.md"),
             Path(TEST), Path(DRIVER_TEST), Path(__file__).relative_to(ROOT),
             *(Path(s) for s in SOURCES), *(Path(s) for s in UNCHANGED),
             Path("tools/verification/feature_regressions.json")]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-B1",
        "work_unit": "WO-220504", "dag_node": "B1", "issue": 124, "invocation": invocation,
        "source_revision": git("rev-parse", "HEAD"),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE, "predecessors": predecessor_custody(),
        "unchanged_predecessor_sources": unchanged_sources(),
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths if (ROOT / p).exists()},
        "missing_inputs": [str(p) for p in paths if not (ROOT / p).exists()],
        "commands": [], "holds": [], "baseline_conditions": [], "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL", "operational_acceptance": "NOT_SATISFIED_BY_THIS_RUN",
        "labels": ["LOCAL_MECHANICAL", "C5_IN_MEMORY_MANAGER", "B1P_COMPOSITION_UNCHANGED",
                   "REAL_USER_SYSTEMD_MANAGER_FOR_B1P_REGRESSION_ONLY", "NO_BOUND_TARGET_TOUCHED"],
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
    mutations = []
    for label, command in (
        ("focused", pytest(TEST, DRIVER_TEST)),
        ("b1p_regression", pytest("tests/evidence_learning/test_trajectory_capture.py",
                                  "tests/composition/test_trajectory_capture_host.py",
                                  "tests/composition/test_trajectory_capture_systemd.py")),
        ("c1_regression", pytest("tests/control_plane/test_attention.py",
                                 "tests/control_plane/test_attention_acknowledgement.py")),
        ("feature_regressions", [sys.executable, "-B", "tools/verification/run_feature_regressions.py",
                                 "--base", ADMISSION_BASELINE, "--candidate", "HEAD"]),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("architecture_fitness_tests", pytest("tests/test_architecture_fitness.py")),
        ("python_regression", pytest()),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
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
        observation = execute(ROOT, command)
        entry = {"id": label, "command": command, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        if label == "b1p_regression" and (observation["exit_status"] != 0 or "skipped" in observation["stdout"]):
            report["holds"].append("b1p_regression failed or skipped its real-manager probe")
        elif label == "python_regression" and observation["exit_status"] != 0:
            failures = failed_ids(observation["stdout"])
            entry["failed"] = failures
            if failures and failures == baseline_failures:
                report["baseline_conditions"].append({
                    "condition": "PRE_EXISTING_BASELINE_FAILURE", "count": len(failures),
                    "baseline": ADMISSION_BASELINE, "baseline_ref": baseline_ref,
                    "note": "identical failing node ids at the admission baseline; no FX-B1 file is involved"})
            else:
                report["holds"].append(label + " failed beyond the recorded baseline condition")
        elif observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
        report["commands"].append(entry)
    with tempfile.TemporaryDirectory(prefix="fx-b1-controls-") as temporary:
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
        "B1-01 receipts observe every captured event": [T + "test_receipts_observe_every_captured_event_with_its_journal_identity"],
        "B1-02 one pending JUDGMENT item per anomaly kind": [T + "test_each_anomaly_kind_yields_exactly_one_pending_judgment_item"],
        "B1-03 idempotent pass": [T + "test_a_pass_with_nothing_new_writes_nothing"],
        "B1-04/B1-05 restart reconciles, queue retained": [T + "test_passes_across_a_kill_and_granted_restart_reconcile_old_and_new_entries"],
        "B1-06 crash between items and receipt": [T + "test_a_pass_that_dies_before_its_receipt_leaves_no_second_item"],
        "B1-07 rewritten or overtaken prefix holds": [T + "test_a_rewritten_or_overtaken_prefix_holds_and_writes_nothing"],
        "B1-08 second consumer refused": [T + "test_a_lost_receipt_compare_and_set_holds"],
        "B1-09 read audit": [D + "test_the_audit_names_a_protected_read_outside_the_allowed_root",
                             D + "test_the_audit_records_sqlite_opens_and_survives_a_failing_module"],
        "B1-10 root guard": [D + "test_the_root_guard_refuses_before_anything_is_written",
                             D + "test_the_default_target_is_the_bound_profile_root"],
        "B1P / C1 not regressed": ["unchanged_predecessor_sources", "b1p_regression", "c1_regression"],
        "negative controls": ["proven-red.json: " + ", ".join(c[0] for c in CONTROLS)],
    }
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0],
        "boundaries": "LOCAL mechanical proof only; the operational acceptance is the separate FX-B1 operational "
                      "run on the bound fx-b1-trajectory-operational target",
        "proof_level": report["proof_level"], "exit_status": report["exit_status"]}, indent=2, default=str) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-B1", "exit_status": report["exit_status"], "holds": report["holds"],
                      "baseline_conditions": len(report["baseline_conditions"]), "controls": len(mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
