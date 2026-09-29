#!/usr/bin/env python3
"""BRD-83 proven-red matrix — make each guard permissive and observe its test fail.

SWF-24: a check that cannot fail is not evidence. For every rejection or refusal this BIU
adds to the release-admission gate (Issue #83), in the structural form of the SF-REQ-002
2026-09-29 amendment, this harness copies the gate and its tests,
applies exactly one deliberately permissive variant, and requires the test that names the
guard to go red, after first requiring it to pass on the intact copy. A test that still
passes against its permissive variant is reported as a failure of this harness.

    python3 tools/live/brd83_proven_red.py           # human readable
    python3 tools/live/brd83_proven_red.py --json    # retained evidence

Nothing here touches the working tree: every variant is applied to a temporary copy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
COPIED = ("release_admission.py", "test_release_admission.py", "test_release_admission_release_point.py")
UNIT = "test_release_admission.py"
FIXTURE = "test_release_admission_release_point.py"

# variant name -> (exact source in release_admission.py, permissive replacement, test that must go red)
# The Issue #83 guards in their SF-REQ-002 2026-09-29 form: the work unit and execution packet a
# receipt binds to are read at the release point, and the identifier is one plain segment.
VARIANTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "reads_the_working_tree",
        '    shown = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True)\n'
        "    return shown.stdout if shown.returncode == 0 else None\n",
        "    target = Path(root) / path\n"
        "    return target.read_bytes() if target.exists() else None\n",
        f"{FIXTURE}::test_a_work_unit_present_only_in_the_working_tree_is_not_used",
    ),
    (
        "reads_the_local_head",
        'f"{commit}:{path}"',
        'f"HEAD:{path}"',
        f"{FIXTURE}::test_a_work_unit_committed_only_in_the_local_checkout_is_not_used",
    ),
    (
        "trusts_a_stale_remote_ref",
        '    return _git(root, "fetch", "--quiet", remote, branch).returncode == 0\n',
        "    return True\n",
        f"{FIXTURE}::test_a_work_unit_landed_at_the_release_point_but_absent_from_the_checkout_is_found",
    ),
    (
        "fetch_takes_an_option_shaped_branch",
        '    if not branch or remote.startswith("-") or branch.startswith("-"):\n',
        "    if not branch:\n",
        f"{FIXTURE}::test_a_release_point_shaped_like_an_option_is_never_passed_to_fetch",
    ),
    (
        "ignores_the_explicit_release_point",
        'f"{release_point}^{{commit}}"',
        'f"origin/main^{{commit}}"',
        f"{FIXTURE}::test_an_explicit_release_point_is_read_instead_of_origin_main",
    ),
    (
        "identifier_admits_dots_and_slashes",
        'WORK_UNIT_ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+")',
        'WORK_UNIT_ID = re.compile(r"[A-Za-z0-9./-]+")',
        f"{FIXTURE}::test_a_receipt_naming_a_path_instead_of_an_identifier_binds_nothing",
    ),
    (
        "identifier_admits_dots_and_slashes_unit",
        'WORK_UNIT_ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+")',
        'WORK_UNIT_ID = re.compile(r"[A-Za-z0-9./-]+")',
        f"{UNIT}::test_an_identifier_that_is_not_one_plain_segment_names_no_file",
    ),
    (
        "document_identifier_unchecked",
        "    if not unit or not WORK_UNIT_ID.fullmatch(unit):\n        return None, None\n",
        "    if not unit:\n        return None, None\n",
        f"{UNIT}::test_an_identifier_that_is_not_one_plain_segment_names_no_file",
    ),
    (
        "packet_identifier_unchecked",
        "    if not unit or not WORK_UNIT_ID.fullmatch(unit):\n        return None\n    raw = read(",
        "    if not unit:\n        return None\n    raw = read(",
        f"{UNIT}::test_an_identifier_that_is_not_one_plain_segment_names_no_file",
    ),
    (
        "work_units_only_in_wave2",
        'WORK_UNIT_DIRS = ("docs/work-units/wave2", "docs/work-units/python", "docs/work-units")',
        'WORK_UNIT_DIRS = ("docs/work-units/wave2",)',
        f"{FIXTURE}::test_a_bound_receipt_for_any_biu_is_admitted",
    ),
    # SF-REQ-002 2026-09-29: each structural precondition can refuse.
    (
        "receipt_not_bound_to_the_packet",
        '    elif facts["work_unit_sha256"] != receipt.get("input_sha256"):\n',
        "    elif False:\n",
        f"{FIXTURE}::test_a_task_packet_edited_after_its_ready_assessment_is_refused_until_reassessed",
    ),
    (
        "receipt_without_an_input_digest",
        'if not isinstance(provenance, dict) or not isinstance(provenance.get("input_sha256"), str) \\\n'
        '            or not provenance["input_sha256"]:\n        return None\n',
        'if not isinstance(provenance, dict):\n        return None\n',
        f"{UNIT}::test_a_native_receipt_needs_agent_ready_provenance_and_an_input_digest",
    ),
    (
        "baseline_not_required",
        '    if not baseline:\n        fail("baseline_named"',
        '    if False:\n        fail("baseline_named"',
        f"{FIXTURE}::test_no_baseline_is_named_without_a_packet_or_a_work_unit",
    ),
    (
        "unbound_work_unit_names_a_baseline",
        '            and work_unit_sha256 == (receipt or {}).get("input_sha256"):\n',
        "            :\n",
        f"{FIXTURE}::test_without_a_packet_an_unbound_receipt_names_no_baseline",
    ),
    (
        "work_unit_commit_is_the_oldest",
        '    log = _git(root, "log", "-1", "--format=%H", release_commit, "--", str(path))\n'
        '    value = log.stdout.strip() if log.returncode == 0 else ""\n',
        '    log = _git(root, "log", "--format=%H", release_commit, "--", str(path))\n'
        '    value = log.stdout.split()[-1] if log.returncode == 0 and log.stdout.split() else ""\n',
        f"{FIXTURE}::test_without_a_packet_the_newest_commit_of_the_assessed_spec_is_the_baseline",
    ),
    (
        "work_unit_commit_before_packet",
        '    baseline = packet_baseline(unit, read)\n',
        "    baseline = None\n",
        f"{FIXTURE}::test_a_packet_baseline_wins_over_the_work_unit_commit",
    ),
    (
        "baseline_not_resolved",
        '    elif not facts.get("baseline_resolves"):\n',
        "    elif False:\n",
        f"{FIXTURE}::test_a_packet_baseline_that_does_not_resolve_is_refused",
    ),
    (
        "baseline_not_reachable",
        '    elif not facts.get("baseline_ancestral"):\n',
        "    elif False:\n",
        f"{FIXTURE}::test_a_packet_baseline_outside_the_release_point_ancestry_is_refused",
    ),
    (
        "contract_baseline_preferred",
        'for key in ("admission_baseline_sha", "baseline_sha"):',
        'for key in ("candidate_contract_baseline_sha", "admission_baseline_sha", "baseline_sha"):',
        f"{UNIT}::test_the_packet_admission_baseline_wins_over_its_contract_baseline",
    ),
    (
        "stale_wording_ignored",
        "    if UNAUTHORIZED_WORDING.search(body) and not SUPERSEDING_WORDING.search(body):\n",
        "    if False:\n",
        f"{UNIT}::test_stale_unauthorized_wording_without_a_superseding_statement_is_refused",
    ),
    # The one reader: only the newest operator receipt from Agent Ready counts.
    (
        "accepts_any_assessment_outcome",
        'record.get("outcome") != "ASSESSED" or ',
        "",
        f"{FIXTURE}::test_a_marker_that_is_not_an_agent_ready_assessment_yields_no_disposition",
    ),
    (
        "counts_any_author",
        "        if not isinstance(author, str) or author.lower() not in operators:\n",
        "        if not isinstance(author, str):\n",
        f"{FIXTURE}::test_a_receipt_from_a_non_operator_is_not_counted",
    ),
    (
        "oldest_receipt_wins",
        "            if receipt is not None:\n                latest = receipt\n",
        "            if receipt is not None and latest is None:\n                latest = receipt\n",
        f"{FIXTURE}::test_a_task_packet_edited_after_its_ready_assessment_is_refused_until_reassessed",
    ),
    (
        "writes_through_gh",
        '_gh_json(root, "issue", "view", str(issue)',
        '_gh_json(root, "issue", "edit", str(issue)',
        f"{FIXTURE}::test_the_gate_only_reads_from_github",
    ),
    # Preserved behaviour, proven the same way: each positive test can fail.
    (
        "repository_not_derived_from_the_gate",
        "[str(Path(__file__).resolve().parent), os.getcwd()]",
        "[os.getcwd()]",
        f"{FIXTURE}::test_the_repository_is_derived_from_the_gate_location_without_an_override",
    ),
)


def _pytest(where: Path, test: str) -> dict:
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test],
                         cwd=where, capture_output=True, text=True)
    tail = [line for line in run.stdout.strip().splitlines() if line][-1:] or [""]
    return {"exit": run.returncode, "summary": tail[0]}


def prove(name: str, source: str, permissive: str, test: str) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"brd83-{name}-") as tmp:
        where = Path(tmp)
        for f in COPIED:
            shutil.copy(HERE / f, where / f)
        intact = _pytest(where, test)
        gate = where / "release_admission.py"
        text = gate.read_text()
        occurrences = text.count(source)
        if occurrences != 1:
            return {"variant": name, "test": test, "intact": intact, "occurrences": occurrences,
                    "proven_red": False, "why": "guard source not found exactly once"}
        gate.write_text(text.replace(source, permissive))
        fault = _pytest(where, test)
        gate.write_text(text)
        restored = _pytest(where, test)
    proven = intact["exit"] == 0 and fault["exit"] == 1 and restored["exit"] == 0
    return {"variant": name, "test": test, "intact": intact, "fault": fault, "restored": restored,
            "proven_red": proven}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    results = [prove(*variant) for variant in VARIANTS]
    ok = all(r["proven_red"] for r in results)
    if args.json:
        print(json.dumps({"proven_red": ok, "variants": results}, indent=2))
    else:
        for r in results:
            mark = "RED as required" if r["proven_red"] else "NOT PROVEN"
            print(f"{r['variant']:38} {mark:16} {r['test']}")
            for phase in ("intact", "fault", "restored"):
                if phase in r:
                    print(f"    {phase:9} exit {r[phase]['exit']}  {r[phase]['summary']}")
        print(f"{sum(r['proven_red'] for r in results)}/{len(results)} variants proven red")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
