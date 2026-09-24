#!/usr/bin/env python3
"""BRD-83 proven-red matrix — make each guard permissive and observe its test fail.

SWF-24: a check that cannot fail is not evidence. For every rejection or refusal this BIU
adds to the release-admission gate (Issue #83), this harness copies the gate and its tests,
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
VARIANTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "reads_the_working_tree",
        '    shown = _git(root, "show", f"{commit}:{path}")\n'
        "    return shown.stdout if shown.returncode == 0 else None\n",
        "    target = Path(root) / path\n"
        "    return target.read_text() if target.exists() else None\n",
        f"{FIXTURE}::test_a_record_present_only_in_the_working_tree_is_not_used",
    ),
    (
        "reads_the_local_head",
        'f"{commit}:{path}"',
        'f"HEAD:{path}"',
        f"{FIXTURE}::test_a_record_committed_only_in_the_local_checkout_is_not_used",
    ),
    (
        "trusts_a_stale_remote_ref",
        '    return _git(root, "fetch", "--quiet", remote, branch).returncode == 0\n',
        "    return True\n",
        f"{FIXTURE}::test_a_record_landed_at_the_release_point_but_absent_from_the_checkout_is_found",
    ),
    (
        "fetch_takes_an_option_shaped_branch",
        '    if not branch or remote.startswith("-") or branch.startswith("-"):\n',
        "    if not branch:\n",
        f"{FIXTURE}::test_a_release_point_shaped_like_an_option_is_never_passed_to_fetch",
    ),
    (
        "identifier_admits_dots_and_slashes",
        'r"([A-Za-z0-9-]+\\.',
        'r"([A-Za-z0-9./-]+\\.',
        f"{UNIT}::test_a_path_that_climbs_out_of_the_record_directory_is_rejected",
    ),
    (
        "identifier_admits_slashes",
        'r"([A-Za-z0-9-]+\\.',
        'r"([A-Za-z0-9/-]+\\.',
        f"{UNIT}::test_an_identifier_containing_a_slash_is_rejected",
    ),
    (
        "no_leading_path_boundary",
        'r"(?<![\\w./-])" + ',
        "",
        f"{UNIT}::test_a_record_path_reached_through_a_parent_prefix_is_rejected",
    ),
    (
        "no_trailing_path_boundary",
        '\n    r"(?!\\.?[\\w/-])"',
        "",
        f"{UNIT}::test_a_record_path_continued_past_the_file_is_rejected",
    ),
    (
        "any_directory_under_docs_evidence",
        're.escape(WAVE2_DIR) + r"/"',
        'r"docs/evidence/(?:[\\w-]+/)*"',
        f"{UNIT}::test_a_record_in_another_directory_is_rejected",
    ),
    # JC R1: a rejected citation must not reach the Wave 1 record for the same identifier.
    (
        "rejected_citation_falls_back_to_wave1",
        "    biu = _wave1_biu(body)\n",
        "    biu = biu_from_body(body)\n",
        f"{FIXTURE}::test_a_rejected_citation_never_admits_through_the_wave1_record",
    ),
    (
        "wave1_any_directory",
        ' and (not prefix or prefix.endswith(f"{WAVE1_DIR}/"))',
        "",
        f"{UNIT}::test_a_wave1_record_in_another_directory_is_rejected",
    ),
    (
        "wave1_parent_segment_allowed",
        '".." not in prefix.split("/") and ',
        "",
        f"{UNIT}::test_a_wave1_record_reached_through_a_parent_segment_is_rejected",
    ),
    (
        "wave1_accepts_stamped_names",
        r"(PY-\d\d[A-Z]?|WO-\d{6})\.assessment",
        r"(PY-\d\d[A-Z]?|WO-\d{6})[\w.-]*\.assessment",
        f"{UNIT}::test_a_stamped_name_is_not_a_wave1_record",
    ),
    (
        "wave1_no_leading_boundary",
        'r"(?<![\\w./-])([^',
        'r"([^',
        f"{UNIT}::test_a_wave1_identifier_embedded_in_a_longer_name_is_rejected",
    ),
    (
        "wave1_no_trailing_boundary",
        r'\.assessment\.json(?!\.?[\w/-])")',
        r'\.assessment\.json")',
        f"{UNIT}::test_a_wave1_record_path_continued_past_the_file_is_rejected",
    ),
    # JC R2: the refusal tests the first matrix left unproven.
    (
        "ignores_the_explicit_release_point",
        'f"{release_point}^{{commit}}"',
        'f"origin/main^{{commit}}"',
        f"{FIXTURE}::test_an_explicit_release_point_is_read_instead_of_origin_main",
    ),
    (
        "accepts_any_assessment_outcome",
        'record.get("outcome") != "ASSESSED" or ',
        "",
        f"{FIXTURE}::test_a_cited_record_that_is_not_an_agent_ready_assessment_still_yields_no_disposition",
    ),
    (
        "writes_through_gh",
        '_gh_json(root, "issue", "view", str(issue)',
        '_gh_json(root, "issue", "edit", str(issue)',
        f"{FIXTURE}::test_the_gate_only_reads_from_github",
    ),
    # Preserved behaviour, proven the same way: each positive test can fail.
    (
        "native_receipt_fallback_removed",
        "    for comment in reversed(comments or []):\n",
        "    for comment in []:\n",
        f"{FIXTURE}::test_the_native_receipt_fallback_is_unchanged_when_the_cited_record_is_absent",
    ),
    (
        "repository_not_derived_from_the_gate",
        "[str(Path(__file__).resolve().parent), os.getcwd()]",
        "[os.getcwd()]",
        f"{FIXTURE}::test_the_repository_is_derived_from_the_gate_location_without_an_override",
    ),
    (
        "wave1_directory_path_not_recognised",
        ' or prefix.endswith(f"{WAVE1_DIR}/")',
        "",
        f"{FIXTURE}::test_a_wave1_record_cited_by_its_own_path_is_still_admitted",
    ),
    # The two recognition changes, proven the same way: without them the new cases refuse.
    (
        "wave2_identifier_is_wo_only",
        'r"([A-Za-z0-9-]+\\.',
        'r"(WO-\\d{6}\\.',
        f"{UNIT}::test_a_readiness_record_for_any_biu_identifier_is_recognised",
    ),
    (
        "release_record_not_consulted",
        "    for text in (body, release_text):\n",
        "    for text in (body,):\n",
        f"{FIXTURE}::test_a_record_for_any_biu_is_admitted_from_the_body_or_the_release_record",
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
