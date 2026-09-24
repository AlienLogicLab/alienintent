"""FX-C2 disposable local proof. Never touches a live queue, provider, profile or bootstrap checkpoint.

Run against committed source; output must be a new directory. Every rerun keeps
its own immutable observations. Each control is applied once to a disposable copy.
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
TEST = "tests/context_assembly/test_context_reconstruction.py"
CONTRACT = "docs/work-units/wave2/WO-220302.md"
ADMISSION_BASELINE = "036c5fc2d2c7f1699b23ac171e9e019aa8d4fc98"
DOMAIN = "src/alienintent/context_assembly/domain/reconstruction.py"
SERVICE = "src/alienintent/context_assembly/application/reconstruction_service.py"
RUNNER = "src/alienintent/composition/context_reconstruction.py"
ARCHITECTURE = ["tools/fitness/check_architecture.py", "--root", "src/alienintent", "--check", "all"]
PINNED = {
    "docs/evidence/wave2-design-contracts.json": "sha256:56676dd97cd09031882ee01e61af2a15071f1b92f6c914fde2169b682f056242",
    "docs/evidence/wave2-dependency-dag.json": "sha256:f99c0a7a392f8dd1f7889bb99d926f0a5a9de0948cb09845686f9d7e6f2b1e8d",
    "docs/evidence/wave2-candidate-bius.json": "sha256:61f9324e7d1b7f0937bbc1aff7cbaba77c50192204e109cad5d78edb04f677f7",
    "docs/evidence/wave2-execution-packets/WO-220302.packet.json": "sha256:9ae65adb52efc2ddb38dced645cd826e294035fd4c5a685a9384594eae202944",
    "docs/evidence/wave2-execution-packets/WO-220302.allocation.json": "sha256:bbaac7bc38cea2c819eb7c7e2a2a22cc691e2ee35ae18fb8672d6680c05ca37e",
    CONTRACT: "sha256:ddfb512eb8e478ca69067f131f52f663edc5882ab4eccfef4239d9a350e80059",
    "docs/evidence/wave2-proof-fixtures/FX-C1/execution-record.json": "sha256:da3c79511fbbe571b1a9ae4bd4e6b245bfa99a04787b221bf59360f5ea34be55",
}
# (control, file, remove, replace_with, test or None for the architecture check, assertion)
CONTROLS = (
    ("manifest_digest_pin", SERVICE, '            if digest(state) != entry["digest"]:', "            if False:",
     "test_unavailable_state_holds[digest]", "expected typed hold DIGEST_MISMATCH"),
    ("missing_record_hold", SERVICE, '            if entry["version"] > 0 and version == 0 and not state:', "            if False:",
     "test_unavailable_state_holds[missing]", "expected typed hold MISSING_RECORD"),
    ("store_unavailable_hold", SERVICE, "            raise ContextHold(HoldReason.STORE_UNAVAILABLE, (aggregate,), str(error)) from error",
     "            return 0, {}", "test_unavailable_state_holds[store]", "expected typed hold STORE_UNAVAILABLE"),
    ("version_fence", SERVICE, '            if version != entry["version"]:', "            if False:",
     "test_unavailable_state_holds[drift]", "expected typed hold VERSION_DRIFT"),
    ("malformed_inbox_hold", DOMAIN, '        raise _hold(HoldReason.MALFORMED_DECISION_INBOX, "decision-inbox")',
     "        return ()", "test_unavailable_state_holds[malformed_inbox]", "expected typed hold MALFORMED_DECISION_INBOX"),
    ("canonical_order", DOMAIN, '    entries = sorted(entries, key=lambda entry: entry["aggregate"])', "    entries = list(entries)",
     "test_list_order_independent", "reversed list_states changed the pinned manifest"),
    ("conversation_isolation", RUNNER,
     '    inputs = {"manifest_ref": arguments.manifest, "project": arguments.project, "profile": arguments.profile}',
     '    inputs = {"manifest_ref": arguments.manifest, "project": arguments.project, "profile": arguments.profile, '
     '"conversation": __import__("os").environ.get("ALIENINTENT_CONVERSATION")}',
     "test_conversation_not_input", "conversation must be neither an input nor authority"),
    ("context_item_omitted", DOMAIN, '        "evidence_refs": list(manifest["evidence"]),\n', "",
     "test_fresh_invocations_equal", "context item omitted"),
    ("mismatch_as_failure", DOMAIN,
     "    differing = sorted(f for f in FIELDS if any(canonical(d.get(f)) != canonical(first.get(f)) for d in rest))",
     "    differing = []", "test_mismatch_is_failure", "mismatch must be a failure"),
    ("lifecycle_rule_bypassed", DOMAIN, "            if accepts(state, action):", "            if True:",
     "test_derivation_rule_uses_lifecycle", "lifecycle rejects authorized action"),
    ("seen_not_resolved", DOMAIN, 'a["status"] != "RESOLVED"', 'a["status"] not in {"RESOLVED", "SEEN"}',
     "test_seen_is_not_resolved", "SEEN attention must stay pending"),
    ("queue_distinct", DOMAIN, '        "unresolved_decisions": list(decisions),',
     '        "unresolved_decisions": list(decisions) + pending,', "test_seen_is_not_resolved",
     "attention must not enter the DecisionInbox queue"),
    ("adapter_import_added", DOMAIN, "from __future__ import annotations\n",
     "from __future__ import annotations\nfrom alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore\n",
     None, "domain imports adapters"),
)
LABELS = ["LABELLED_DERIVATION_RULE_v1", "LOCAL_PROCESS_BOUNDARY_SUBSTITUTE_FOR_EPISODE"]
RESIDUALS = [
    {"id": "M_CONTEXT_SHADOW_DEFERRED", "owner": "R5 (FX-R5) under POSTW1-DECIDE-006A",
     "note": "No comparison with the live bootstrap checkpoint, handoff or retirement; operational state needs a separately authorized target."},
    {"id": "DECISION_INBOX_LIST_OPEN_SILENT_EMPTY", "owner": "C1 (DecisionInbox owner)",
     "note": "DecisionInbox.list_open still returns () for a malformed aggregate; the context adapter validates the raw aggregate itself and holds instead. Not repaired here."},
]


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
    environment = {key: value for key, value in os.environ.items() if key != "ALIENINTENT_CONVERSATION"}
    environment |= {"PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd), "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        result = subprocess.run(argv, cwd=cwd, env=environment, text=True, capture_output=True, timeout=600,
                                stdin=subprocess.DEVNULL)
        return {"argv": argv, "cwd": str(cwd), "exit_status": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired as error:
        return {"argv": argv, "cwd": str(cwd), "exit_status": None, "error": str(error),
                "stdout": str(error.stdout), "stderr": str(error.stderr)}


def readback(output, invocation):
    """A fresh disposable profile: predecessor, two successors, comparator and every hold class."""
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tests.context_assembly import test_context_reconstruction as fixture
    with tempfile.TemporaryDirectory(prefix="fx-c2-readback-") as temporary:
        base = Path(temporary)
        root, cwd = base / "profile", base / "cwd"
        root.mkdir(), cwd.mkdir()
        fixture.seed(root)
        pred_status, pred = fixture.predecessor(root, cwd)
        runs = {"predecessor": {"exit_status": pred_status, "output": pred}}
        for label in ("a", "b"):
            status, result = fixture.successor(root, pred["manifest_ref"], cwd, label)
            runs["successor_" + label] = {"exit_status": status, "output": result}
        compare_status, verdict = fixture.compare(cwd, *(run["output"] for run in runs.values()))
        holds = {}
        for case, (reason, target, fault, before_pin) in fixture.HOLDS.items():
            case_root, case_cwd = base / ("hold-" + case), base / ("cwd-" + case)
            case_root.mkdir(), case_cwd.mkdir()
            profile = fixture.seed(case_root)
            target = fixture.attention_identity(profile) if target == "attention" else target
            if before_pin:
                version, _ = profile.store.read_state("fixture", target)
                profile.store.commit("fixture", target, version, {"open": ["not-an-escalation"]})
            pointer = profile.context.pin()
            if fault is not None:
                fault(profile, target)
            status, result = fixture.successor(case_root, pointer, case_cwd, "hold-" + case)
            holds[case] = {"expected_reason": reason, "exit_status": status, "output": result,
                           "observed_reason": result.get("reason") if isinstance(result, dict) else None}
        body = {"invocation": invocation, "runs": runs, "compare": {"exit_status": compare_status, "verdict": verdict},
                "holds": holds}
        return retain(output, body), body


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    paths = [Path(p) for p in PINNED] + [
        Path("docs/evidence/wave2-proof-fixtures/FX-C2/implementation-plan.md"), Path(TEST),
        Path("tests/context_assembly/context_episode.py"), Path(__file__).relative_to(ROOT), Path(DOMAIN), Path(SERVICE),
        Path(RUNNER), Path("src/alienintent/context_assembly/ports/context_assembler.py"),
        Path("src/alienintent/composition/control_plane_profile.py")]
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-C2",
        "invocation": invocation, "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "admission_baseline": ADMISSION_BASELINE,
        "input_digests": {str(p): digest((ROOT / p).read_bytes()) for p in paths},
        "commands": [], "holds": [], "labels": LABELS, "residuals": RESIDUALS,
        "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
        "measurements": {"tokens": None, "cost": None, "provider_calls": None,
                         "reason": "UNKNOWN: provider usage is unavailable to this local fixture"}}
    if report["source_status"]:
        report["holds"].append("source is not a clean committed candidate")
    for path, expected in PINNED.items():
        if report["input_digests"][path] != expected:
            report["holds"].append(f"pinned input digest mismatch: {path}")
    for label, command in (
        ("intact", [sys.executable, "-B", "-m", "pytest", "-q", TEST]),
        ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q"]),
        ("architecture", [sys.executable, "-B", *ARCHITECTURE]),
        ("node_regression", ["node", "scripts/check.mjs", "all"]),
    ):
        observation = execute(ROOT, command)
        report["commands"].append({"id": label, "command": command, "exit_status": observation["exit_status"],
                                   "observation_ref": retain(output, observation)})
        if observation["exit_status"] != 0:
            report["holds"].append(label + " failed")
    mutations = []
    with tempfile.TemporaryDirectory(prefix="fx-c2-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests", "tools"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        for name, relative, needle, replacement, test, assertion in CONTROLS:
            path = copy / relative
            original = path.read_text()
            count = original.count(needle)
            if count != 1:
                report["holds"].append(f"{name}: mutation application count {count}, expected exactly one")
                mutations.append({"control": name, "application_count": count, "discriminates": False})
                continue
            command = ([sys.executable, "-B", *ARCHITECTURE] if test is None
                       else [sys.executable, "-B", "-m", "pytest", "-q", TEST + "::" + test])
            path.write_text(original.replace(needle, replacement, 1))
            try:
                fault = execute(copy, command)
            finally:
                path.write_text(original)
            restored = execute(copy, command)
            if test is None:
                named = assertion in fault["stdout"]
            else:
                named = assertion in fault["stdout"] and "AssertionError" in fault["stdout"]
            discriminates = fault["exit_status"] == 1 and named and restored["exit_status"] == 0
            mutations.append({"control": name, "application_count": count, "file": relative,
                "source_digest": digest(original.encode()), "mutation": {"remove": needle, "replace_with": replacement},
                "command": command, "assertion": assertion, "fault_exit": fault["exit_status"],
                "restored_exit": restored["exit_status"], "fault_ref": retain(output, fault),
                "restored_ref": retain(output, restored), "discriminates": discriminates})
            if not discriminates:
                report["holds"].append(name + " did not discriminate")
    probe = {}
    try:
        report["readback_ref"], body = readback(output, invocation)
        runs = body["runs"]
        probe = {"predecessor_and_successor_digests": {k: v["output"].get("digest") for k, v in runs.items()},
                 "exit_statuses": {k: v["exit_status"] for k, v in runs.items()},
                 "field_equality": body["compare"]["verdict"], "compare_exit": body["compare"]["exit_status"],
                 "hold_reason_codes": {k: {"expected": v["expected_reason"], "observed": v["observed_reason"],
                                           "exit_status": v["exit_status"]} for k, v in body["holds"].items()}}
        if (any(v["exit_status"] != 0 for v in runs.values()) or body["compare"]["exit_status"] != 0
                or len(set(probe["predecessor_and_successor_digests"].values())) != 1):
            report["holds"].append("readback reconstruction was not equal")
        for case, value in probe["hold_reason_codes"].items():
            if value["exit_status"] != 2 or value["observed"] != value["expected"]:
                report["holds"].append(f"readback hold {case} did not produce its typed hold")
    except Exception as error:
        report["holds"].append("readback failed: " + repr(error))
    report["exit_status"] = 1 if report["holds"] else 0
    mapping = {"SF-REQ-053-AC-01": ["test_fresh_invocations_equal", "test_mismatch_is_failure",
        "test_conversation_not_input", "test_list_order_independent", "test_derivation_rule_uses_lifecycle",
        "test_seen_is_not_resolved", "test_unavailable_state_holds"]}
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "run-report.json").write_text(json.dumps({"acceptance_to_probes": mapping,
        "focused_command": report["commands"][0], "readback_ref": report.get("readback_ref"), **probe,
        "derivation_rule": "LABELLED_DERIVATION_RULE_v1", "episode_boundary": "LOCAL_PROCESS_BOUNDARY_SUBSTITUTE_FOR_EPISODE",
        "labels": LABELS, "residuals": [r["id"] for r in RESIDUALS],
        "proof_level": report["proof_level"], "live_proof": report["live_proof"],
        "exit_status": report["exit_status"]}, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": mutations, "holds": report["holds"]}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-C2", "exit_status": report["exit_status"], "holds": report["holds"],
                      "controls": len(mutations), "discriminating": sum(bool(m["discriminates"]) for m in mutations),
                      "output": str(output)}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--invocation", required=True)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.output, arguments.invocation))
