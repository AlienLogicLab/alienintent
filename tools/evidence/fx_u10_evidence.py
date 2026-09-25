"""FX-U10 disposable local proof: the Agent Ready CLI/MCP transport boundary (WO-220210, SF-REQ-015).

Runs against a clean committed candidate into a new output directory; every observation is immutable and named by
its digest. Pinned inputs are recomputed at the RELEASED baseline and the candidate; a mismatch is a HOLD (exit 2)
before any probe runs. One discriminating control per material failure class is applied exactly once to a disposable
source copy: intact exit 0 -> fault exit 1 at the named assertion -> restored exit 0. Native probes launch the
configured Agent Ready product only when --agent-ready-bin names its environment; provider-backed assessments run
only with --native-assess. A local PASS is not operational acceptance and grants no release authority.
"""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fx_u9_evidence import ARCHITECTURE, COPIED, _ERROR, _FAILED, digest, execute, retain  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ADMISSION_BASELINE = "1163caf4c6844d2f41dbe3ad24ee6040e202de11"  # The RELEASED baseline (Issue #111).
CONTRACT_SHA256 = "c7b56d6f98a99527d1d7d4abc62a8447fb33c47f8bf4ad017c6c9c3292a98d4a"
TEST = "tests/context_assembly/test_readiness_transport.py"
PRODUCER = "src/alienintent/execution_coordination/adapters/agent_ready_producer.py"
EC_DOMAIN = "src/alienintent/execution_coordination/domain/readiness.py"
CONSUMER = "src/alienintent/execution_coordination/adapters/assessment_consumer.py"
BINDING = "src/alienintent/composition/readiness.py"
PROFILE_SOURCE = "src/alienintent/composition/upstream_profile.py"
CONFORMANCE = "docs/evidence/wave2-proof-fixtures/FX-U10/agent-ready-public-contract.json"
PLAN = "docs/evidence/wave2-proof-fixtures/FX-U10.md"
SOURCES = (PRODUCER, EC_DOMAIN, CONSUMER, BINDING, PROFILE_SOURCE, "tests/context_assembly/test_readiness_consumer.py")
# (label, path, sha256 at the RELEASED baseline); "contract" equals the native READY receipt's input_sha256.
PINNED = (("contract", "docs/work-units/wave2/WO-220210.md",
           "f545ad4b5de451793ce0e4b22d354d725934db7c81500930d3b620fab4a09cbc"),
          ("packet", "docs/evidence/wave2-execution-packets/WO-220210.packet.json",
           "445c68c9b0c12f644f903e914976ac3d232601197918e861822db23dde944dd6"),
          ("allocation", "docs/evidence/wave2-execution-packets/WO-220210.allocation.json",
           "17857144bd2c767d56299b18897cd00591ddfa0532ace7b2993af35ee975959c"),
          ("proof_packet", "docs/evidence/wave2-execution-packets/WO-220210.proof-packet.md",
           "75c19f03106cab9269d7be791bad21978f2af94b8f9e6821429a7cca05591d26"),
          ("C", "docs/evidence/wave2-design-contracts.json",
           "1cd1fe512e6d24cb7e90d813fd01eb0532e17564d95c99cdf63f63addbe05e80"),
          ("ready_receipt", "docs/evidence/wave2-readiness-assessments/WO-220210.2026-09-25T090303.988150Z.assessment.json",
           "2e0e078d9cfc7c4b73968f81aa93cf50d0f66760fb8ec3bdf4cc49666aa2e990"),
          ("U9_evidence", "docs/evidence/wave2-proof-fixtures/FX-U9.md",
           "373b2faf3543a401189744d093724153374470a741e8ccbc0b28ded7b1fce9b1"))
LABELS = ["FIXTURE_EXECUTABLE_NOT_AGENT_READY", "NATIVE_AGENT_READY_OPT_IN", "PUBLIC_CONTRACT_PINNED_BY_FIXTURE",
          "JSON_RPC_WRAPPER_PRESERVED", "SDK_VERSION_NOT_PRODUCT_VERSION"]
RESIDUALS = ["CONTRACT_VERSION_LIMITATION_AGENT_READY_1", "MODEL_PROVENANCE_UNKNOWN",
             "PROVIDER_EVIDENCE_CODEX_ONLY_UNTRUSTED", "INJECTED_FIXTURE_PRODUCER_PATH_RETAINED_FOR_U9",
             "UNKNOWN_INVOCATION_COMPLETION_HELD", "OPERATOR_SURFACE_NOT_BUILT"]


def node(name: str) -> str:
    return f"{TEST}::{name}"


# (control, material class, file, remove, replace_with, node ids) -- exactly one site each.
CONTROLS = (
    ("C1-mcp_wrapper_dropped", "raw response and invocation provenance reach the consumer", PRODUCER,
     "                raw, message = self._response(lines, deadline)\n",
     "                line, message = self._response(lines, deadline)\n"
     "                raw = json.dumps(message[\"result\"]).encode() if isinstance(message, dict) else line\n",
     (node("test_mcp_binding_reaches_consumer_with_raw_response_and_custody"),)),
    ("C2-mcp_correlation_trusted", "disconnected response refuses", PRODUCER,
     "                answered = identifier if isinstance(identifier, str) else \"\"\n",
     "                answered = unit.attempt_id\n",
     (node("test_disconnected_mcp_response_is_refused"),)),
    ("C3-json_rpc_error_beside_result_admitted", "provider error is an attempt failure, never READY", EC_DOMAIN,
     "        if \"error\" in document or \"result\" not in document:\n",
     "        if \"result\" not in document:\n",
     (node("test_failed_attempt_is_never_ready[mcp_json_rpc_error_beside_ready]"),)),
    ("C4-ready_released", "READY is eligibility only; the release gate is not bypassed", CONSUMER,
     '        status = "APPLICABLE" if isinstance(result, ReadinessEligibility) else "INAPPLICABLE"\n',
     '        status = "APPLICABLE" if isinstance(result, ReadinessEligibility) else "INAPPLICABLE"\n'
     '        if status == "APPLICABLE":\n'
     '            aggregate = "release:" + identity\n'
     '            self.store.commit(self.profile, aggregate, self.store.read_state(self.profile, aggregate)[0], '
     '{"released": identity})\n',
     (node("test_transport_ready_is_eligibility_only[cli]"), node("test_transport_ready_is_eligibility_only[mcp]"))),
)


def reconcile_baseline() -> dict:
    rows = []
    for label, path, pinned in PINNED:
        at_baseline = sha256(subprocess.check_output(["git", "show", f"{ADMISSION_BASELINE}:{path}"],
                                                     cwd=ROOT)).hexdigest()
        rows.append({"label": label, "path": path, "pinned_sha256": pinned, "at_admission_baseline": at_baseline,
                     "at_candidate": sha256((ROOT / path).read_bytes()).hexdigest()})
    base = subprocess.check_output(["git", "merge-base", "HEAD", ADMISSION_BASELINE], cwd=ROOT, text=True).strip()
    return {"admission_baseline": ADMISSION_BASELINE, "candidate_base": base, "inputs": rows,
            "reconciled": base == ADMISSION_BASELINE
            and all(r["pinned_sha256"] == r["at_admission_baseline"] == r["at_candidate"] for r in rows)}


def run_control(copy: Path, output: Path, control: tuple) -> dict:
    name, material, path, remove, replace_with, nodes = control
    original = (copy / path).read_text()
    count = original.count(remove)
    if count != 1:
        raise RuntimeError(f"{name}: mutation matches {count} sites, expected exactly one")
    argv = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *nodes]
    intact = execute(copy, argv, None)
    (copy / path).write_text(original.replace(remove, replace_with, 1))
    fault = execute(copy, argv, None)
    (copy / path).write_text(original)
    restored = execute(copy, argv, None)
    failed = {n for n, _ in _FAILED.findall(fault["stdout"])}
    named = set(nodes) <= failed and not _ERROR.findall(fault["stdout"])
    discriminates = (intact["exit_status"] == 0 and fault["exit_status"] == 1 and named
                     and restored["exit_status"] == 0 and (copy / path).read_text() == original)
    return {"control": name, "material_failure_class": material, "application_count": 1, "file": path,
            "source_digest": digest(original.encode()), "mutation": {"remove": remove, "replace_with": replace_with},
            "command": argv, "assertion": " ; ".join(f"FAILED {n} - AssertionError" for n in nodes),
            "intact_exit": intact["exit_status"], "fault_exit": fault["exit_status"],
            "restored_exit": restored["exit_status"], "intact_ref": retain(output, intact),
            "fault_ref": retain(output, fault), "restored_ref": retain(output, restored),
            "discriminates": discriminates}


def _failures(stdout: str) -> set[str]:
    return set(re.findall(r"^(?:FAILED|ERROR) (\S+)", stdout, re.MULTILINE))


def regression_against_baseline(output: Path, candidate: dict) -> dict:
    """Run the same full regression in a temporary detached worktree at the admission baseline and compare."""
    with tempfile.TemporaryDirectory(prefix="fx-u10-baseline-") as temporary:
        tree = Path(temporary) / "baseline"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), ADMISSION_BASELINE], cwd=ROOT, check=True,
                       capture_output=True)
        try:
            baseline = execute(tree, [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"], None)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=ROOT, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=ROOT, capture_output=True)
    before, after = _failures(baseline["stdout"]), _failures(candidate["stdout"])
    return {"admission_baseline": ADMISSION_BASELINE, "baseline_exit": baseline["exit_status"],
            "baseline_observation_ref": retain(output, baseline), "baseline_failures": sorted(before),
            "candidate_failures": sorted(after), "new_failures": sorted(after - before),
            "resolved_failures": sorted(before - after),
            "disposition": "PRE_EXISTING_BASELINE_FAILURES_ONLY" if after <= before else "NEW_FAILURES"}


def run(output: Path, invocation: str, agent_ready_bin: Path | None, native_assess: bool) -> int:
    output.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    holds: list[str] = ["source is not a clean committed candidate"] if status else []
    baseline = reconcile_baseline()
    if not baseline["reconciled"]:
        print(json.dumps({"fixture": "FX-U10", "exit_status": 2, "hold": "INPUT_DIGEST_MISMATCH"}))
        (output / "baseline-hold.json").write_text(json.dumps(baseline, indent=2) + "\n")
        return 2  # HOLD before any probe runs.
    paths = [PLAN, TEST, CONFORMANCE, str(Path(__file__).relative_to(ROOT)), *SOURCES]
    record = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-U10",
              "work_unit_id": "WO-220210", "issue": 111, "invocation": invocation, "source_revision": revision,
              "source_status": status, "admission_baseline": ADMISSION_BASELINE,
              "candidate_contract_sha256": CONTRACT_SHA256,
              "input_digests": {**{label: "sha256:" + pinned for label, _, pinned in PINNED},
                                **{p: digest((ROOT / p).read_bytes()) for p in paths}},
              "baseline_reconciliation_ref": retain(output, baseline), "commands": [], "holds": holds,
              "labels": LABELS, "residuals": RESIDUALS, "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
              "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL", "live_proof": "NOT_ESTABLISHED",
              "native_agent_ready": {"bin": str(agent_ready_bin) if agent_ready_bin else None,
                                     "provider_backed_assessments": native_assess},
              "measurements": {"agent_ready_invocations": None, "provider_calls": None, "tokens": None, "cost": None,
                               "reason": "UNKNOWN: Agent Ready v0.1 exposes no usage or cost; native invocations are "
                                         "counted in the retained command observations, never inferred zero"}}
    native_dir = Path(tempfile.mkdtemp(prefix="fx-u10-native-"))
    native_env = {"FX_U10_AGENT_READY_BIN": str(agent_ready_bin)} if agent_ready_bin else {}
    commands = [("focused", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", TEST], {})]
    if agent_ready_bin:
        commands.append(("native_credential_free", [sys.executable, "-B", "-m", "pytest", "-q", "-rs", "-p",
                                                    "no:cacheprovider", TEST, "-k", "native and not assessment"],
                         native_env))
        if native_assess:
            commands.append(("native_assessment", [sys.executable, "-B", "-m", "pytest", "-q", "-rs", "-p",
                                                   "no:cacheprovider", TEST, "-k", "native_assessment"],
                             {**native_env, "FX_U10_NATIVE_ASSESS": "1", "FX_U10_NATIVE_RECORD": str(native_dir)}))
    commands += [("u9_consumer", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                  "tests/context_assembly/test_readiness_consumer.py"], {}),
                 ("python_regression", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider"], {}),
                 ("architecture", [sys.executable, *ARCHITECTURE], {}),
                 ("architecture_fitness_tests", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                                 "tests/test_architecture_fitness.py"], {}),
                 ("node_regression", ["node", "scripts/check.mjs", "all"], {})]
    for label, argv, extra in commands:
        observation = _execute(ROOT, argv, extra)
        entry = {"id": label, "command": argv, "environment": extra, "exit_status": observation["exit_status"],
                 "observation_ref": retain(output, observation)}
        if label == "python_regression" and observation["exit_status"] != 0:
            # Failures already present at the RELEASED baseline are measured there and named, never called PASS.
            entry["baseline_comparison"] = regression_against_baseline(output, observation)
            if entry["baseline_comparison"]["new_failures"] or entry["baseline_comparison"]["baseline_exit"] is None:
                holds.append(label + " has failures absent at the admission baseline")
        elif observation["exit_status"] != 0:
            holds.append(label + " failed")
        record["commands"].append(entry)
        print(label, observation["exit_status"], flush=True)
    native = {}
    for path in sorted(native_dir.glob("native-*.json")):
        native[path.stem] = retain(output, json.loads(path.read_text()))
    shutil.rmtree(native_dir)
    if native_assess and set(native) != {"native-cli", "native-mcp"}:
        holds.append("native assessment observations missing")
    record["native_observation_refs"] = native

    controls = []
    with tempfile.TemporaryDirectory(prefix="fx-u10-controls-") as temporary:
        copy = Path(temporary)
        for name in ("src", "tests"):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for path in (*COPIED, CONFORMANCE):
            (copy / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, copy / path)
        for control in CONTROLS:
            result = run_control(copy, output, control)
            controls.append(result)
            print(result["control"], result["intact_exit"], result["fault_exit"], result["restored_exit"],
                  result["discriminates"], flush=True)
            if not result["discriminates"]:
                holds.append(result["control"] + " did not discriminate")
    record["exit_status"] = 1 if holds else 0
    (output / "execution-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (output / "proven-red.json").write_text(json.dumps({"controls": controls, "holds": holds}, indent=2) + "\n")
    manifest = {str(p.relative_to(output)): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"fixture": "FX-U10", "exit_status": record["exit_status"], "holds": holds,
                      "controls": len(controls), "discriminated": sum(c["discriminates"] for c in controls),
                      "native": sorted(native), "output": str(output)}))
    return record["exit_status"]


def _execute(cwd: Path, argv: list[str], extra: dict) -> dict:
    """fx_u9_evidence.execute with additional environment for the opt-in native probes."""
    import os
    saved = {k: os.environ.get(k) for k in extra}
    os.environ.update(extra)
    try:
        return execute(cwd, argv, None)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--agent-ready-bin", type=Path)
    parser.add_argument("--native-assess", action="store_true")
    arguments = parser.parse_args()
    if arguments.native_assess and arguments.agent_ready_bin is None:
        parser.error("--native-assess requires --agent-ready-bin")
    raise SystemExit(run(arguments.output, arguments.invocation, arguments.agent_ready_bin, arguments.native_assess))
