"""Execute FX-S1 intact/fault/restored probes; retain raw immutable observations.

All fixtures use disposable external roots. Mutations run in separate source
copies and must cause an acceptance assertion failure, not an import/tool error.
No network, provider, lifecycle or live installation is used by this runner.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PLAN = Path("docs/evidence/wave2-proof-fixtures/FX-S1/fixture-plan.json")
TESTS = ["tests/evidence_learning", "tests/execution_coordination/test_evidence_verdict_bridge.py", "tests/composition/test_evidence_profile.py"]
MUTATIONS = (
    ("kind", "if kind_of(record) != kind:", "test_kind_gate_refuses_an_observation_used_as_definition"),
    ("definition-authority", "if grant not in authority.definitions:", "test_authority_rejects_observation_promotion"),
    ("revision", "if actual != expected:", "test_revision_gate_refuses_stale_evidence"),
    ("evaluator-authority", "if EvaluatorGrant(evaluator, authority_ref, policy_ref) not in authority.evaluators:", "test_missing_evaluator_policy_or_observation_ref_cannot_mint_verdict"),
)


def digest(body: bytes) -> str:
    return "sha256:" + sha256(body).hexdigest()


def execute(cwd: Path, args: list[str]) -> dict:
    env = {**os.environ, "PYTHONPATH": str(cwd / "src") + os.pathsep + str(cwd), "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    return {"argv": args, "cwd": str(cwd), "exit_status": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr}


def retain(output: Path, record: dict) -> dict:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    name = sha256(body).hexdigest()
    target = output / "observations" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(body)
    return {"revision_digest": "sha256:" + name, "locator": "observations/" + name}


def run(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=False)
    report = {"record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-S1",
              "invocation": json.loads((ROOT / PLAN).read_text())["invocation"],
              "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "fixture_plan_sha256": digest((ROOT / PLAN).read_bytes()),
              "source_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
              "independent_verdict": "PENDING", "live_proof": "NOT_ESTABLISHED", "provider_calls_observed": 0,
              "scope": "local synthetic evidence/SQLite proof; not an invocation/provider accounting report",
              "commands": [], "mutations": [], "holds": []}
    paths = [p for base in ("src/alienintent/evidence_learning", "tests/evidence_learning") for p in (ROOT / base).rglob("*.py")]
    paths += [ROOT / p for p in ("src/alienintent/composition/evidence_profile.py", "src/alienintent/composition/offline_profile.py",
                               "src/alienintent/execution_coordination/adapters/evidence_verdict_bridge.py",
                               "src/alienintent/execution_coordination/ports/evidence_verdict.py",
                               "src/alienintent/execution_coordination/domain/verdict.py", "tests/composition/test_evidence_profile.py",
                               "tests/execution_coordination/test_evidence_verdict_bridge.py", "tools/evidence/fx_s1_evidence.py")]
    report["input_digests"] = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(paths)}
    intact = execute(ROOT, [sys.executable, "-B", "-m", "pytest", "-q", *TESTS])
    report["commands"].append({"id": "intact", "expected_exit": 0, "observed_exit": intact["exit_status"], "observation_ref": retain(output, intact)})
    if intact["exit_status"] != 0:
        report["holds"].append("intact focused suite failed")
    with tempfile.TemporaryDirectory(prefix="fx-s1-mutations-") as temp:
        copy = Path(temp)
        shutil.copytree(ROOT / "src/alienintent", copy / "src/alienintent", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(ROOT / "tests", copy / "tests", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(ROOT / "pyproject.toml", copy / "pyproject.toml")
        path = copy / "src/alienintent/evidence_learning/domain/admission.py"
        original = path.read_text()
        for name, needle, test in MUTATIONS:
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f"{name}: mutation must match once, observed {count}")
            command = [sys.executable, "-B", "-m", "pytest", "-q", "tests/evidence_learning/test_admission.py::" + test]
            path.write_text(original.replace(needle, "if False:", 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            discriminates = fault["exit_status"] == 1 and "DID NOT RAISE" in fault["stdout"] and restored["exit_status"] == 0
            report["mutations"].append({"control": name, "application_count": count,
                                        "expected_fault_exit": 1, "observed_fault_exit": fault["exit_status"],
                                        "expected_restored_exit": 0, "observed_restored_exit": restored["exit_status"],
                                        "fault_ref": retain(output, fault), "restored_ref": retain(output, restored),
                                        "discriminates": discriminates})
            if not discriminates:
                report["holds"].append(name + " did not discriminate")
    # Retain actual synthetic typed objects and operational readback, not just test prose.
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from tests.evidence_learning.support import authority, definition, header, observation, seeded
    from tests.execution_coordination.test_evidence_verdict_bridge import evaluate
    from dataclasses import replace
    with tempfile.TemporaryDirectory(prefix="fx-s1-records-") as temp:
        fixture_root = Path(temp)
        profile, dref, oref = seeded(fixture_root)
        verdict = evaluate(profile, dref, (oref,))
        vref = profile.service.admit(verdict, 2).ref
        unknown = replace(observation(value=None, uncertainty="not measured"), header=header("unknown-measurement"), evidence_id="duration")
        uref = profile.service.admit(unknown, 3).ref
        conflict = replace(observation(value=False), header=header("conflicting-observation"))
        cref = profile.service.admit(conflict, 4).ref
        state = profile.service.read()
        shutil.copytree(fixture_root / "evidence/objects", output / "objects")
        report["typed_refs"] = [asdict(r) for r in (dref, oref, vref, uref, cref)]
        snapshot = {"profile": "fx-s1", "project": "AlienLogicLab/alienintent", "authority": asdict(authority()),
                    "access_scope": sorted(profile.access_scope), "max_bytes": profile.repository.max_bytes}
        # Sets/tuples are encoded deterministically for the immutable fixture input.
        snapshot["authority"]["external_refs"] = [asdict(r) for r in sorted(authority().external_refs, key=lambda r: r.logical_id)]
        report["profile_ref"] = retain(output, snapshot)
        report["readback_ref"] = retain(output, {"version": state.version, "refs": [asdict(r) for r in state.refs],
                                                "held_definitions": [asdict(r) for r in state.held_definitions]})
        if state.held_definitions != (dref,):
            report["holds"].append("competing observation did not hold applicability")
    report["exit_status"] = 0 if not report["holds"] else 1
    (output / "execution-record.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"fixture_id": "FX-S1", "exit_status": report["exit_status"], "holds": report["holds"], "report": str(output / "execution-record.json")}))
    return report["exit_status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().output))
