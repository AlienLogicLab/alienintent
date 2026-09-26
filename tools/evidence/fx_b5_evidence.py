"""FX-B5 LOCAL proof (WO-220508). Uses disposable roots and a disposable copy of committed source.
It never touches the operational attention root, a provider or a live host.

Local results are labelled LOCAL and never satisfy operational acceptance. The operational
readback is `tools/live/fx_b5_operational.py`. The output must be a new directory. The execution
record is rewritten after every stage, so an interrupted run reads as INCOMPLETE (a HOLD, never a PASS).
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
CONTRACT = "docs/evidence/wave2-proof-fixtures/FX-B5/FX-B5.md"
ADMISSION_BASELINE = "62e693932dcbd6b6583a1d37b172f4b418af9256"
TEST = "tests/control_plane/test_attention_acknowledgement.py"
SERVICE = "src/alienintent/control_plane/application/attention.py"
SOURCES = (SERVICE, "src/alienintent/control_plane/domain/attention.py",
           "src/alienintent/control_plane/ports/attention.py",
           "src/alienintent/composition/attention_inbox.py",
           "src/alienintent/composition/control_plane_profile.py",
           "tools/live/fx_b5_operational.py", TEST, "tools/live/test_fx_b5_operational.py", CONTRACT)
ADJACENT = ("tests/control_plane/test_attention.py", "tests/execution_coordination/test_liveness_reconciliation.py",
            "tests/control_plane/test_monitor_host.py", "tests/composition/test_bounded_control_capstone.py")
PROBES = {
    "B5-01": ("test_receipt_distinct_from_insertion_delivery_rendering_seen",),
    "B5-02": ("test_acknowledgement_shape_and_transition",),
    "B5-03": ("test_unconfigured_actor_refused", "test_statement_and_version_required"),
    "B5-04": ("test_zero_duplicate_handling",),
    "B5-05": ("test_acknowledgement_shape_and_transition",),
    "B5-06": ("test_pending_reconciliation_after_failed_delivery",),
    "B5-07": ("test_acknowledgement_keeps_judgment_suppression",),
    "B5-08": ("test_queue_persists_across_restart",),
    "B5-09": ("test_operator_surface",),
    "B5-10": ("test_acknowledgement_never_activates",),
}
# (control, failure class, file, needle, replacement, test node ids, pinned assertions)
CONTROLS = (
    ("delivery_counts_as_receipt", "command delivery or transport mistaken for human receipt", SERVICE,
     '        raw_ack = body.get("acknowledgement")\n',
     '        raw_ack = body.get("acknowledgement") or next(({"item_identity": identity, "item_version": version,'
     ' "item_history_ref": asdict(ref), "actor": a.receipt.consumer, "at": "delivered", "statement": "delivered"}'
     ' for a in attempts if a.status == "DELIVERED"), None)\n',
     ("test_receipt_distinct_from_insertion_delivery_rendering_seen",),
     ("a delivered notification must not be human receipt",)),
    ("acknowledger_unchecked", "acknowledgement by a non-human or unconfigured actor", SERVICE,
     "        if actor not in self.acknowledgers:\n", "        if not isinstance(actor, str):\n",
     ("test_unconfigured_actor_refused",), ("an unconfigured actor must not acknowledge",)),
    ("duplicate_acknowledgement", "duplicate handling", SERVICE,
     '        if item.acknowledgement is not None:\n            raise AttentionHold("ALREADY_ACKNOWLEDGED")\n', "",
     ("test_zero_duplicate_handling",), ("a second acknowledgement must be refused",)),
    ("acknowledgement_resolves", "suppression broken or acknowledgement confused with resolution", SERVICE,
     '"ACKNOWLEDGED", actor, status="SEEN"', '"ACKNOWLEDGED", actor, status="RESOLVED"',
     ("test_acknowledgement_keeps_judgment_suppression",), ("acknowledgement must not lift judgment suppression",)),
)
CRITERIA = {
    "new and unresolved product attention, judgment outcomes": ("B5-02", "B5-05", "B5-08"),
    "pending reconciliation": ("B5-06",),
    "zero duplicate handling": ("B5-04",),
    "intact suppression": ("B5-07", "B5-10"),
    "queue persists": ("B5-08",),
    "command delivery is not human receipt; receipt is explicit, item-bound, timestamped": ("B5-01", "B5-02", "B5-03"),
    "human operator surface on the existing path": ("B5-09",),
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
    report = {"fixture": "FX-B5", "biu": "WO-220508", "issue": 128, "label": "LOCAL",
              "invocation": arguments.invocation, "contract": CONTRACT, "admission_baseline": ADMISSION_BASELINE,
              "source_candidate": {"commit": git("rev-parse", "HEAD"),
                                   "files": {s: digest((ROOT / s).read_bytes()) for s in SOURCES}},
              "commands": [], "probes": {}, "holds": [] if not dirty else ["SOURCE_UNCOMMITTED"],
              "non_claims": ["LOCAL proof only; not operational acceptance",
                             "no acknowledgement made here is human receipt"]}
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
    operational_tool = run("operational-tool", ROOT, pytest("tools/live/test_fx_b5_operational.py"))
    architecture = run("architecture", ROOT, [sys.executable, "-B", "tools/fitness/check_architecture.py",
                                              "--root", "src/alienintent", "--check", "all"])
    registry = run("feature-regression-registry", ROOT, pytest("tools/verification/test_feature_regressions.py"))
    for label, observation in (("adjacent", adjacent), ("operational-tool", operational_tool),
                               ("architecture", architecture), ("feature-regression-registry", registry)):
        if observation["exit_status"] != 0:
            report["holds"].append("COMMAND_FAILED:" + label)
    with tempfile.TemporaryDirectory(prefix="fx-b5-controls-") as temporary:
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
    run_report = {"fixture": "FX-B5", "label": "LOCAL", "criteria": {
        c: {"probes": list(p), "result": "PASS" if all(report["probes"][x] == "PASS" for x in p) else "FAIL"}
        for c, p in CRITERIA.items()},
        "operational_acceptance": "NOT CLAIMED: requires tools/live/fx_b5_operational.py readback of a named "
                                  "human acknowledgement on the authorized operational root"}
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
