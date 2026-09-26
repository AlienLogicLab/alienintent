"""FX-U8 evidence runner: the intact FX-U8 probes, then one proven-red source mutation per control.

Runs against a committed candidate: `git archive <commit>` is extracted into a disposable directory, the intact probes
run there, and each control applies exactly one textual mutation to a fresh extraction and reruns only its named
probes. A control discriminates only when its mutation applied exactly once, pytest exits 1 and every named probe is
reported FAILED. Raw pytest output is retained as immutable observations/<sha256>. Tokens and cost are UNKNOWN.

    python3 -B tools/evidence/fx_u8_evidence.py --commit <sha> --output docs/evidence/wave2-proof-fixtures/FX-U8 \
        --invocation <invocation>
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROBES = "tests/context_assembly/test_initial_compilation.py"
DOMAIN = "src/alienintent/context_assembly/domain/initial_compilation.py"
SERVICE = "src/alienintent/context_assembly/application/initial_compilation_service.py"
BOUNDED = ["tests/context_assembly/test_compilation_validation.py", "tests/execution_coordination/domain/test_contract.py",
           PROBES]

# (id, failure class, file, original text, mutated text, probes that must fail)
CONTROLS = (
    ("K1", "1-derived-from-reviewed-design", SERVICE,
     "        if not decision.admitted:\n",
     "        if False:\n",
     ["test_unverified_design_holds_without_candidate"]),
    ("K2", "1-derived-from-pinned-requirements", DOMAIN,
     "        elif report.preparation != ELIGIBLE:\n",
     "        elif False:\n",
     ["test_unresolved_authority_holds"]),
    ("K3", "2-omission-holds", DOMAIN,
     '    unproven = [f"{a}:verification" for a in acceptance if a not in proven]\n',
     "    unproven = []\n",
     ["test_obligation_omission_holds"]),
    ("K4", "2-invention-holds", DOMAIN,
     '    invented = [o["obligation_id"] for o in proofs if o["predicate"]["acceptance_id"] not in acceptance]\n',
     "    invented = []\n",
     ["test_obligation_invention_holds"]),
    ("K5", "3-identity-not-sort-derived", DOMAIN,
     "        identity = reservations.get(key)\n",
     "        identity = None\n",
     ["test_reservation_is_stable_and_not_sort_derived"]),
    ("K6", "3-deterministic-under-permutation", DOMAIN,
     '    proofs = sorted(plan["obligations"], key=lambda o: o["obligation_id"])\n',
     '    proofs = list(plan["obligations"])\n',
     ["test_derivation_is_deterministic_under_permutation"]),
    ("K7", "3-identity-collision-fails-closed", DOMAIN,
     "            elif identity in occupied or list(reservations.values()).count(identity) > 1:\n",
     "            elif list(reservations.values()).count(identity) > 1:\n",
     ["test_identity_dependency_and_bound_violations_hold[collision]",
      "test_identity_dependency_and_bound_violations_hold[foreign_unit]",
      "test_identity_dependency_and_bound_violations_hold[foreign_unreserved]"]),
    ("K9", "1-exact-pinned-inputs", DOMAIN,
     "        or not _same(design.digest, plan[\"design_ref\"][\"revision_digest\"]):\n",
     "        or False:\n",
     ["test_unpinned_input_holds[design]"]),
    ("K8", "4-validator-only-cannot-complete", DOMAIN,
     "        and document.get(\"provenance\") == DERIVED and document.get(\"mode\") == INITIAL \\\n"
     "        and document.get(\"derivation_rule\") == DERIVATION_RULE\n",
     "        or document.get(\"mode\") == INITIAL\n",
     ["test_validator_only_supplied_mapping_cannot_complete"]),
)


def extract(commit: str, target: Path) -> None:
    data = subprocess.check_output(["git", "archive", "--format=tar", commit], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(target, filter="data")


def pytest(directory: Path, args: list[str]) -> tuple[int, str, list[str]]:
    # The U7 probes in the bounded command read pinned SWF-33 blobs; the extraction has no Git, so use the retained copies.
    env = {**os.environ, "PYTHONPATH": "src", "COLUMNS": "400", "PYTHONDONTWRITEBYTECODE": "1",
           "FX_U7_FIXTURE_INPUTS": str(directory / "docs/evidence/wave2-proof-fixtures/FX-U7/fixture-inputs")}
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-rf", "-p", "no:cacheprovider", *args]
    done = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True)
    output = done.stdout + done.stderr
    failed = [line.split(" ", 1)[1].split(" - ", 1)[0] for line in output.splitlines() if line.startswith("FAILED ")]
    return done.returncode, output, failed


def observe(output: Path, text: str) -> str:
    identity = sha256(text.encode()).hexdigest()
    path = output / "observations" / identity
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text)
    return identity


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", required=True)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "rev-parse", args.commit + "^{commit}"], cwd=ROOT, text=True).strip()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    report = {"schema_version": 1, "record_kind": "ProofRunReport", "fixture": "FX-U8", "biu_id": "WO-220208",
              "candidate_commit": commit, "invocation": args.invocation, "started_at": started,
              "runner": {"path": "tools/evidence/fx_u8_evidence.py",
                         "sha256": sha256((ROOT / "tools/evidence/fx_u8_evidence.py").read_bytes()).hexdigest()},
              "python": sys.version.split()[0], "proof_level": "LOCAL_COMPOSED_OR_MECHANICAL",
              "tokens": None, "cost": None, "tokens_cost_reason": "UNKNOWN: not exposed to the runner",
              "independent_verdict": "PENDING_FRESH_BIU_VERIFIER", "live_proof": "NOT_ESTABLISHED"}
    with tempfile.TemporaryDirectory(prefix="fx-u8-") as scratch:
        intact = Path(scratch) / "intact"
        extract(commit, intact)
        runs = []
        for name, probes in (("fx-u8-probes", [PROBES]), ("bounded-command", BOUNDED)):
            code, text, failed = pytest(intact, probes)
            runs.append({"name": name, "command": "PYTHONPATH=src python3 -B -m pytest -q " + " ".join(probes),
                         "exit_status": code, "expected": 0, "failed": failed, "observation": observe(output, text)})
        report["intact"] = runs
        controls = []
        for index, (identity, failure_class, path, original, mutated, targets) in enumerate(CONTROLS):
            copy = Path(scratch) / f"k{index}"
            extract(commit, copy)
            source = (copy / path).read_text()
            applied = source.count(original)
            if applied == 1:
                (copy / path).write_text(source.replace(original, mutated))
            nodes = [f"{PROBES}::{t}" for t in targets]
            code, text, failed = pytest(copy, nodes) if applied == 1 else (None, "", [])
            discriminated = applied == 1 and code == 1 and set(nodes) <= set(failed)
            controls.append({"id": identity, "failure_class": failure_class, "file": path, "applied_count": applied,
                             "mutation": {"original": original, "mutated": mutated}, "targets": nodes,
                             "exit_status": code, "failed": failed, "discriminated": discriminated,
                             "observation": observe(output, text) if text else None})
        report["controls"] = controls
    report["ended_at"] = datetime.now(timezone.utc).isoformat()
    intact_ok = all(r["exit_status"] == 0 for r in report["intact"])
    red_ok = all(c["discriminated"] for c in report["controls"])
    report["result"] = "PASS" if intact_ok and red_ok else "HOLD"
    (output / "run-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest = {p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest()
                for p in sorted(output.rglob("*")) if p.is_file() and p.name != "digest-manifest.json"}
    (output / "digest-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result": report["result"], "intact": [(r["name"], r["exit_status"]) for r in report["intact"]],
                      "controls": [(c["id"], c["applied_count"], c["exit_status"], c["discriminated"])
                                   for c in report["controls"]]}))
    return 0 if report["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
