#!/usr/bin/env python3
"""FX-R1 citation integrity check (WO-220601, R1 coordinator-checkpoint replacement gate).

FX-R1 cites retained proof; it does not re-execute it. This script re-checks only what the
citation depends on: the FDH-01 live-proof SHA256SUMS, commit ancestry against the release
baseline, the pin-before-run order, and the self-digests and discrimination results of the
cited FX-C2/FX-C3 records. It reads the repository and never writes outside --output.
Run from the repository root.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FDH = "docs/evidence/fdh-01-live-proof/20260924T080401Z"
PROCEDURE = "docs/operations/factory-director-host-live-proof.md"
RUN_STARTED_AT = "2026-09-24T08:04:01Z"  # the $PROOF directory's own timestamp
FDH_LANDED = "a233e9e47fae053e0f789943f6423dbfeb2a8bbe"
PROCEDURE_AUTHORED = "a2bf163cce3d868dd38b4abf3dddf3740995bb22"
PROCEDURE_FOLLOWED = "06e7e0c1f384e29c304788b11e0e559d8bdacc73"  # README.md and Issue #89 authorization
FDH_EVIDENCE_COMMIT = "59db3c532a004e10dee60eede7a477e8e17545f1"
FIXTURES = {
    "FX-C2": {"dir": "docs/evidence/wave2-proof-fixtures/FX-C2", "controls": 13,
              "source": "459f825cd9d8a922837b9b20f053e3285eb47de4",
              "retained": "46920041299d4fac28c3bbd65eb25c5ac1823787",
              "merge": "7b6e19c4a17f1d797f61c99edafadd4857940dd6",
              "probe": "test_mismatch_is_failure", "probe_control": "mismatch_as_failure"},
    "FX-C3": {"dir": "docs/evidence/wave2-proof-fixtures/FX-C3", "controls": 23,
              "source": "aaa16fb2d1c2bbc9adaeee78b50939bced2cffe7",
              "retained": "d69c00480c895da80d63eb185b534ca1befad0c7",
              "merge": "fc5c0a7fcbc0d70772c07cd35a4fe52a3e2641c7",
              "probe": "test_state_vector_mismatch", "probe_control": "vector_check_removed"},
}


def run(command, cwd=ROOT):
    done = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return {"command": command, "exit_status": done.returncode,
            "stdout_sha256": "sha256:" + sha256(done.stdout.encode()).hexdigest(),
            "stdout": done.stdout.strip()}


def check(checks, name, expected, observed, **detail):
    checks.append({"check": name, "expected": expected, "observed": observed,
                   "result": "PASS" if expected == observed else "FAIL", **detail})


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


def utc(commit):
    seconds = int(git("show", "-s", "--format=%ct", commit))
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="release baseline commit")
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    baseline = git("rev-parse", "--verify", args.baseline + "^{commit}")
    checks = []

    sums = run(["sha256sum", "-c", "SHA256SUMS"], cwd=ROOT / FDH)
    listed = len((ROOT / FDH / "SHA256SUMS").read_text().splitlines())
    ok = sum(line.endswith(": OK") for line in sums["stdout"].splitlines())
    check(checks, "fdh01_sha256sums_verify", {"exit_status": 0, "ok": listed},
          {"exit_status": sums["exit_status"], "ok": ok}, command=sums["command"],
          cwd=FDH, stdout_sha256=sums["stdout_sha256"])

    for name, commit in (("fdh01_landed", FDH_LANDED), ("fdh01_evidence_commit", FDH_EVIDENCE_COMMIT),
                         ("procedure_authored", PROCEDURE_AUTHORED),
                         ("procedure_followed", PROCEDURE_FOLLOWED)):
        result = run(["git", "merge-base", "--is-ancestor", commit, baseline])
        check(checks, f"{name}_is_ancestor_of_baseline", 0, result["exit_status"],
              command=result["command"])

    for name, commit in (("procedure_authored", PROCEDURE_AUTHORED),
                         ("procedure_followed", PROCEDURE_FOLLOWED)):
        committed = utc(commit)
        check(checks, f"{name}_committed_before_run", True, committed < RUN_STARTED_AT,
              commit=commit, committed_utc=committed, run_started_utc=RUN_STARTED_AT)
    followed_blob = git("rev-parse", f"{PROCEDURE_FOLLOWED}:{PROCEDURE}")
    changes = git("log", "--format=%H", f"{PROCEDURE_FOLLOWED}", "--", PROCEDURE).splitlines()
    check(checks, "procedure_followed_last_changed_before_run", True, utc(changes[0]) < RUN_STARTED_AT,
          blob=followed_blob, last_change_commit=changes[0], last_change_utc=utc(changes[0]),
          authored_blob=git("rev-parse", f"{PROCEDURE_AUTHORED}:{PROCEDURE}"))

    for fixture, spec in FIXTURES.items():
        base = ROOT / spec["dir"]
        observations = sorted((base / "observations").iterdir())
        bad = [p.name for p in observations if sha256(p.read_bytes()).hexdigest() != p.name]
        check(checks, f"{fixture}_observations_self_digest", [], bad, count=len(observations))
        controls = json.loads((base / "proven-red.json").read_text())["controls"]
        discriminating = [c["control"] for c in controls
                          if c["discriminates"] and c["application_count"] == 1]
        check(checks, f"{fixture}_controls_discriminate", spec["controls"], len(discriminating),
              total=len(controls))
        check(checks, f"{fixture}_probe_control_discriminates", True,
              spec["probe_control"] in discriminating, probe=spec["probe"],
              control=spec["probe_control"])
        record = json.loads((base / "execution-record.json").read_text())
        check(checks, f"{fixture}_record_exit_and_holds", {"exit_status": 0, "holds": []},
              {"exit_status": record["exit_status"], "holds": record["holds"]},
              invocation=record["invocation"], source_revision=record["source_revision"])
        check(checks, f"{fixture}_record_source_revision", spec["source"], record["source_revision"])
        for label in ("source", "retained", "merge"):
            result = run(["git", "merge-base", "--is-ancestor", spec[label], baseline])
            check(checks, f"{fixture}_{label}_is_ancestor_of_baseline", 0, result["exit_status"],
                  command=result["command"], commit=spec[label])

    failed = [c["check"] for c in checks if c["result"] != "PASS"]
    report = {"record_kind": "CitationIntegrityCheck", "schema_version": "1", "fixture_id": "FX-R1",
              "invocation": args.invocation, "baseline": baseline,
              "script": "tools/evidence/fx_r1_evidence.py", "checks": checks, "failed": failed,
              "exit_status": 1 if failed else 0}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "citation-check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": len(checks), "failed": failed}))
    return report["exit_status"]


if __name__ == "__main__":
    sys.exit(main())
