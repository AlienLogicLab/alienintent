"""FX-E2 LOCAL proof (WO-220503). Uses disposable rehearsal roots and a disposable copy of committed source.
It never reads or writes the live Node writer, the live Python sandbox, a provider or a live host.

Local results are labelled LOCAL and never satisfy operational acceptance, live cutover or release. The
output must be a new directory. The execution record is rewritten after every stage, so an interrupted
run reads as INCOMPLETE (a HOLD, never a PASS).
"""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fx_c_evidence import checkpoint, digest, discriminates, execute, failed_ids, git, pytest, retain  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-E2/FX-E2.md"
ADMISSION_BASELINE = "b07be02db62bdbc1c39753de4da32697b6dbd4e0"
TEST = "tests/execution_coordination/test_one_writer_cutover.py"
DOMAIN = "src/alienintent/execution_coordination/domain/cutover.py"
APPLICATION = "src/alienintent/execution_coordination/application/cutover.py"
ADAPTER = "src/alienintent/execution_coordination/adapters/cutover_files.py"
SOURCES = (DOMAIN, "src/alienintent/execution_coordination/ports/cutover.py", APPLICATION, ADAPTER,
           "src/alienintent/execution_coordination/adapters/sqlite_store.py",
           "src/alienintent/composition/cutover_rehearsal.py", TEST, CONTRACT)
ADJACENT = ("tests/execution_coordination/test_operational_store.py", "tests/execution_coordination/test_fenced_store.py",
            "tests/execution_coordination/test_factory_coordinator.py")
PROBES = {
    "E2-01": ("test_isolation_refuses_live_paths_before_writing",),
    "E2-02": ("test_absent_canonical_control_keeps_node",),
    "E2-03": ("test_each_quiescence_blocker_holds_without_writer_change",),
    "E2-04": ("test_checkpoint_binds_both_stores_and_tamper_holds",),
    "E2-05": ("test_reconciliation_maps_every_record_once_and_is_durable",),
    "E2-06": ("test_pending_reservations_retained_through_cutover_and_rollback",),
    "E2-07": ("test_one_writer_admission_race_and_node_writer_detection",),
    "E2-08": ("test_rollback_never_redispatches_python_completed_work",),
    "E2-09": ("test_rollback_stops_python_first_and_holds_on_unreconciled_effects",),
    "E2-10": ("test_fresh_controller_reads_identical_durable_state",),
}
# (control, failure class, file, needle, replacement, test names, pinned assertions)
CONTROLS = (
    ("quiescence_ignores_pending_intent", "quiescence asserted with an unresolved external intent", DOMAIN,
     "            if claim.get(intent):\n", "            if False:\n",
     ("test_each_quiescence_blocker_holds_without_writer_change",), ("a pending intent must block quiescence",)),
    ("checkpoint_unverified", "checkpoint integrity not verified", ADAPTER,
     '        if bad or set(members) != {"node-state.json", "python-store.sqlite"}:\n', "        if False:\n",
     ("test_checkpoint_binds_both_stores_and_tamper_holds",), ("a tampered checkpoint must hold",)),
    ("admission_unchecked", "simultaneous Node/Python writer not rejected", DOMAIN,
     '    if writer != authority.writer:\n        raise WriterRejected("NOT_APPROVED_WRITER")\n', "",
     ("test_one_writer_admission_race_and_node_writer_detection",), ("the non-approved writer must be refused",)),
    ("rollback_replays_python_effect", "rollback duplicates an effect Python already confirmed", APPLICATION,
     '                completed[identity.split(":", 2)[2]] = identity\n', "                pass\n",
     ("test_rollback_never_redispatches_python_completed_work",),
     ("a lane Python completed must not be re-dispatchable after rollback",)),
    ("reservation_dropped", "pending reservation lost in migration", DOMAIN,
     "            elif not any(effect[1] == lane for effect in effects):\n                reservations[lane] = invocation\n",
     "            elif False:\n                pass\n",
     ("test_pending_reservations_retained_through_cutover_and_rollback",), ("every pending reservation must be retained",)),
    ("keep_node_bypassed", "canonical control absent but migration proceeds anyway", APPLICATION,
     "        if not self.canonical_control:\n", "        if False:\n",
     ("test_absent_canonical_control_keeps_node",), ("absent canonical control must keep Node",)),
    ("rollback_before_python_stopped", "old writer enabled before the new writer is stopped and reconciled", APPLICATION,
     '        if unresolved:\n            raise CutoverHold("PYTHON_EFFECTS_UNRECONCILED", unresolved)\n', "",
     ("test_rollback_stops_python_first_and_holds_on_unreconciled_effects",),
     ("Node must stay disabled while Python effects are unreconciled",)),
)
CRITERIA = {
    "isolated rehearsal before live use (no shared state with the live writer)": ("E2-01",),
    "canonical control absent keeps Node and returns to existing authority": ("E2-02",),
    "quiescence": ("E2-03",),
    "backup/checkpoint integrity": ("E2-04",),
    "durable active-work/effect reconciliation": ("E2-05", "E2-10"),
    "retained pending reservations": ("E2-06",),
    "reject simultaneous Node/Python writers for the same work": ("E2-07",),
    "nonduplicating rollback": ("E2-08", "E2-09"),
}


def disposable_copy(target):
    archive = subprocess.run(["git", "archive", "HEAD"], cwd=ROOT, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)


def node(test, name):
    return f"{test}::{name}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    output = arguments.output
    output.mkdir(parents=True, exist_ok=False)
    dirty = git("status", "--porcelain", "--", *SOURCES)
    report = {"fixture": "FX-E2", "biu": "WO-220503", "issue": 123, "label": "LOCAL",
              "invocation": arguments.invocation, "contract": CONTRACT, "admission_baseline": ADMISSION_BASELINE,
              "source_candidate": {"commit": git("rev-parse", "HEAD"),
                                   "files": {s: digest((ROOT / s).read_bytes()) for s in SOURCES}},
              "commands": [], "probes": {}, "holds": [] if not dirty else ["SOURCE_UNCOMMITTED"],
              "non_claims": ["LOCAL proof only; not operational acceptance, release or live cutover",
                             "the Node writer is represented by its dispatcher.mjs state file; no Node process ran",
                             "no live Node or Python writer state was read or written"]}
    mutations = []

    def run(label, cwd, argv):
        observation = execute(cwd, argv)
        report["commands"].append({"label": label, "argv": argv, "exit_status": observation["exit_status"],
                                   "observation": retain(output, observation)})
        checkpoint(output, report, mutations, label)
        return observation

    focused = run("focused", ROOT, pytest("-rfEs", TEST))
    failed = failed_ids(focused["stdout"])
    for probe, tests in PROBES.items():
        broken = any(f.split("::")[-1].split("[")[0] in tests for f in failed)
        report["probes"][probe] = "PASS" if focused["exit_status"] == 0 or (
            focused["exit_status"] == 1 and not broken) else "FAIL"
    adjacent = run("adjacent", ROOT, pytest(*ADJACENT))
    architecture = run("architecture", ROOT, [sys.executable, "-B", "tools/fitness/check_architecture.py",
                                              "--root", "src/alienintent", "--check", "all"])
    registry = run("feature-regression-registry", ROOT, pytest("tools/verification/test_feature_regressions.py"))
    for label, observation in (("adjacent", adjacent),
                               ("architecture", architecture), ("feature-regression-registry", registry)):
        if observation["exit_status"] != 0:
            report["holds"].append("COMMAND_FAILED:" + label)
    with tempfile.TemporaryDirectory(prefix="fx-e2-controls-") as temporary:
        tree = Path(temporary)
        disposable_copy(tree)
        for name, failure, path, needle, replacement, tests, assertions in CONTROLS:
            target = tree / path
            original = target.read_text()
            count = original.count(needle)
            nodes = [node(TEST, t) for t in tests]
            intact = execute(tree, pytest(*nodes))
            if count == 1:
                target.write_text(original.replace(needle, replacement))
            fault = execute(tree, pytest(*nodes))
            target.write_text(original)
            restored = execute(tree, pytest(*nodes))
            ok = count == 1 and discriminates(assertions, intact, fault, restored)
            mutations.append({"control": name, "failure_class": failure, "file": path, "application_count": count,
                              "tests": nodes, "assertions": list(assertions), "discriminating": ok,
                              "intact": retain(output, intact), "fault": retain(output, fault),
                              "restored": retain(output, restored),
                              "exit_status": [intact["exit_status"], fault["exit_status"], restored["exit_status"]]})
            if not ok:
                report["holds"].append("CONTROL_NOT_DISCRIMINATING:" + name)
            checkpoint(output, report, mutations, "control:" + name)
    if any(v != "PASS" for v in report["probes"].values()) or focused["exit_status"] != 0:
        report["holds"].append("PROBE_FAILED")
    report |= {"run_state": "COMPLETE", "stage": "done", "exit_status": 1 if report["holds"] else 0}
    run_report = {"fixture": "FX-E2", "label": "LOCAL", "criteria": {
        c: {"probes": list(p), "result": "PASS" if all(report["probes"][x] == "PASS" for x in p) else "FAIL"}
        for c, p in CRITERIA.items()},
        "operational_acceptance": "NOT CLAIMED: isolated rehearsal only; a live cutover needs its own separate "
                                  "grant, the live writers' own readback and the B6 capstone"}
    for name, body in (("execution-record.json", report),
                       ("proven-red.json", {"controls": mutations, "holds": report["holds"]}),
                       ("run-report.json", run_report)):
        (output / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    for stale in output.glob("*.partial"):
        stale.unlink()
    manifest = {str(p.relative_to(output)): "sha256:" + sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_state": report["run_state"], "exit_status": report["exit_status"],
                      "holds": report["holds"], "probes": report["probes"],
                      "controls": {m["control"]: m["discriminating"] for m in mutations}}, indent=2))
    return report["exit_status"]


if __name__ == "__main__":
    sys.exit(main())
