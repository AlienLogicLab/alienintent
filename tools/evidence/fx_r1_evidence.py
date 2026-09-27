#!/usr/bin/env python3
"""FX-R1 citation integrity check (WO-220601, R1 coordinator-checkpoint replacement gate).

FX-R1 cites retained proof; it does not re-execute it. This script re-checks the integrity of
what the citation depends on and nothing else:
- the cited evidence is byte-unchanged in Git from the commit that retained it to the checked revision;
- the FDH-01 live-proof SHA256SUMS verifies;
- the landed/retained/merge commits are ancestors of the release baseline;
- the procedure was committed before the run started;
- the FX-C2/FX-C3 observations, controls and cited probes are intact.
It does not check Issue comments or the content of the step mapping; those are for the verifier.
It reads the repository and writes only under --output. Run from the repository root.
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
FDH_EVIDENCE_COMMIT = "59db3c532a004e10dee60eede7a477e8e17545f1"
PROCEDURE_AUTHORED = "a2bf163cce3d868dd38b4abf3dddf3740995bb22"
PROCEDURE_FOLLOWED = "06e7e0c1f384e29c304788b11e0e559d8bdacc73"  # README.md, 00-origin-main.sha, #89 authorization
FIXTURES = {
    "FX-C2": {"dir": "docs/evidence/wave2-proof-fixtures/FX-C2", "observations": 31, "controls": 13,
              "source": "459f825cd9d8a922837b9b20f053e3285eb47de4",
              "retained": "46920041299d4fac28c3bbd65eb25c5ac1823787",
              "merge": "7b6e19c4a17f1d797f61c99edafadd4857940dd6",
              "probe": "test_mismatch_is_failure", "probe_control": "mismatch_as_failure"},
    "FX-C3": {"dir": "docs/evidence/wave2-proof-fixtures/FX-C3", "observations": 73, "controls": 23,
              "source": "aaa16fb2d1c2bbc9adaeee78b50939bced2cffe7",
              "retained": "d69c00480c895da80d63eb185b534ca1befad0c7",
              "merge": "fc5c0a7fcbc0d70772c07cd35a4fe52a3e2641c7",
              "probe": "test_state_vector_mismatch", "probe_control": "vector_check_removed"},
}
INPUTS = ["docs/evidence/wave2-proof-fixtures/FX-R1.md", "docs/work-units/wave2/WO-220601.md",
          "docs/evidence/wave2-execution-packets/WO-220601.packet.json",
          "docs/evidence/wave2-execution-packets/WO-220601.allocation.json",
          "docs/evidence/wave2-dependency-dag.json", "tools/evidence/fx_r1_evidence.py",
          f"{FDH}/SHA256SUMS", f"{FDH}/README.md",
          "docs/evidence/wave2-proof-fixtures/FX-C2/execution-record.json",
          "docs/evidence/wave2-proof-fixtures/FX-C2/proven-red.json",
          "docs/evidence/wave2-proof-fixtures/FX-C3/execution-record.json",
          "docs/evidence/wave2-proof-fixtures/FX-C3/proven-red.json"]


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


def unchanged(checks, name, since, revision, path):
    # Retained evidence must be byte-identical in Git and in the working tree.
    for label, command in (("git", ["git", "diff", "--quiet", since, revision, "--", path]),
                           ("worktree", ["git", "diff", "--quiet", revision, "--", path])):
        result = run(command)
        check(checks, f"{name}_unchanged_{label}", 0, result["exit_status"], command=command)
    untracked = git("ls-files", "--others", "--exclude-standard", "--", path)
    check(checks, f"{name}_no_untracked_files", "", untracked, path=path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="release baseline commit")
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    baseline = git("rev-parse", "--verify", args.baseline + "^{commit}")
    revision = git("rev-parse", "HEAD")
    checks = []

    unchanged(checks, "fdh01_evidence", FDH_EVIDENCE_COMMIT, revision, FDH)
    # The packet's bounded command is `sha256sum -c <dir>/SHA256SUMS`; its entries are ./-relative,
    # so it is run from inside the directory. README.md and SHA256SUMS itself are not listed and are
    # covered by the Git immutability check above instead.
    sums = run(["sha256sum", "-c", "SHA256SUMS"], cwd=ROOT / FDH)
    listed = len((ROOT / FDH / "SHA256SUMS").read_text().splitlines())
    ok = sum(line.endswith(": OK") for line in sums["stdout"].splitlines())
    files = sorted(p.name for p in (ROOT / FDH).iterdir() if p.is_file())
    check(checks, "fdh01_sha256sums_verify", {"exit_status": 0, "ok": listed},
          {"exit_status": sums["exit_status"], "ok": ok}, command=sums["command"], cwd=FDH,
          stdout_sha256=sums["stdout_sha256"], files_in_directory=len(files))
    check(checks, "fdh01_run_head_is_procedure_followed", PROCEDURE_FOLLOWED,
          (ROOT / FDH / "00-origin-main.sha").read_text().strip())

    ancestors = [("fdh01_landed", FDH_LANDED), ("fdh01_evidence_commit", FDH_EVIDENCE_COMMIT),
                 ("procedure_authored", PROCEDURE_AUTHORED), ("procedure_followed", PROCEDURE_FOLLOWED)]
    ancestors += [(f"{f}_{label}", spec[label]) for f, spec in FIXTURES.items()
                  for label in ("source", "retained", "merge")]
    for name, commit in ancestors:
        result = run(["git", "merge-base", "--is-ancestor", commit, baseline])
        check(checks, f"{name}_is_ancestor_of_baseline", 0, result["exit_status"],
              command=result["command"], commit=commit)

    for name, commit in (("procedure_authored", PROCEDURE_AUTHORED),
                         ("procedure_followed", PROCEDURE_FOLLOWED)):
        committed = utc(commit)
        check(checks, f"{name}_committed_before_run", True, committed < RUN_STARTED_AT,
              commit=commit, committed_utc=committed, run_started_utc=RUN_STARTED_AT)
    last_change = git("log", "-1", "--format=%H", PROCEDURE_FOLLOWED, "--", PROCEDURE)
    check(checks, "procedure_followed_last_changed_before_run", True, utc(last_change) < RUN_STARTED_AT,
          blob=git("rev-parse", f"{PROCEDURE_FOLLOWED}:{PROCEDURE}"), last_change_commit=last_change,
          last_change_utc=utc(last_change),
          authored_blob=git("rev-parse", f"{PROCEDURE_AUTHORED}:{PROCEDURE}"))

    for fixture, spec in FIXTURES.items():
        base = ROOT / spec["dir"]
        unchanged(checks, fixture, spec["retained"], revision, spec["dir"])
        observations = sorted((base / "observations").iterdir())
        bad = [p.name for p in observations if sha256(p.read_bytes()).hexdigest() != p.name]
        check(checks, f"{fixture}_observations_self_digest", {"count": spec["observations"], "bad": []},
              {"count": len(observations), "bad": bad})
        controls = json.loads((base / "proven-red.json").read_text())["controls"]
        refs = [c[k]["locator"] for c in controls for k in c if k.endswith("_ref")]
        missing = [r for r in refs if not (base / r).is_file()]
        check(checks, f"{fixture}_control_refs_resolve", [], missing, refs=len(refs))
        check(checks, f"{fixture}_controls_all_discriminate_once",
              {"total": spec["controls"], "discriminating_once": spec["controls"]},
              {"total": len(controls),
               "discriminating_once": sum(c["discriminates"] is True and c["application_count"] == 1
                                          for c in controls)})
        probe = [c for c in controls if c["control"] == spec["probe_control"]]
        check(checks, f"{fixture}_probe_control_runs_probe", True,
              len(probe) == 1 and probe[0]["discriminates"] is True
              and any(spec["probe"] in part for part in probe[0]["command"]),
              probe=spec["probe"], control=spec["probe_control"])
        record = json.loads((base / "execution-record.json").read_text())
        check(checks, f"{fixture}_record", {"exit_status": 0, "holds": [], "source_revision": spec["source"]},
              {"exit_status": record["exit_status"], "holds": record["holds"],
               "source_revision": record["source_revision"]}, invocation=record["invocation"])

    failed = [c["check"] for c in checks if c["result"] != "PASS"]
    report = json.dumps({"record_kind": "CitationIntegrityChecks", "fixture_id": "FX-R1",
                         "checks": checks}, indent=2, sort_keys=True) + "\n"
    digest = sha256(report.encode()).hexdigest()
    status = git("status", "--porcelain", "--", *INPUTS)
    record = {
        "record_kind": "ProofFixtureExecution", "schema_version": 1, "fixture_id": "FX-R1",
        "biu_id": "WO-220601", "issue_number": 130, "invocation": args.invocation,
        "source_revision": revision, "source_status": status, "admission_baseline": baseline,
        "input_digests": {p: "sha256:" + sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS},
        "labels": ["CITATION_ONLY_NO_REEXECUTION", "FDH01_POSITIVE_PATH_ONLY",
                   "MISMATCH_ELEMENT_CAPABILITY_LEVEL_C2_C3"],
        "commands": [{"id": "citation_integrity",
                      "command": ["python3", "-B", "tools/evidence/fx_r1_evidence.py", "--baseline", baseline,
                                  "--invocation", args.invocation, "--output", "<output>"],
                      "exit_status": 1 if failed else 0,
                      "observation_ref": {"revision_digest": "sha256:" + digest,
                                          "locator": f"observations/{digest}"}}],
        "checks_total": len(checks), "checks_failed": failed, "holds": [],
        "residuals": ["R1-F1_DISPOSITION_EXACTLY_C2_C3_WORDING", "R1-F2_PROCEDURE_REVISION_PRECISION",
                      "C3_VERDICT_COMMENT_FIELDS_BLANK"],
        "independent_verdict": "PENDING_FRESH_BIU_VERIFIER",
        "proof_level": "OPERATIONAL_OR_EXTERNAL_AUTHORITY",
        "proof_level_by_element": {
            "reconstruction_without_prior_conversation": "OPERATIONAL_BY_CITATION (FDH-01, Issue #89)",
            "mismatch_blocks_tenure_change": "LOCAL_COMPOSED_OR_MECHANICAL_BY_CITATION (FX-C2, FX-C3)"},
        "live_proof": "CITED_NOT_REEXECUTED",
        "retirement": "NONE — KEEP_UNTIL_REPLACED",
        "exit_status": 1 if failed else 0,
    }
    (args.output / "observations").mkdir(parents=True, exist_ok=True)
    (args.output / "observations" / digest).write_text(report)
    (args.output / "execution-record.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"checks": len(checks), "failed": failed, "observation": digest}))
    return record["exit_status"]


if __name__ == "__main__":
    sys.exit(main())
