# BRD-83 / Issue #83 execution record (PRODUCER)

These are local proof receipts only. They are not an independent verdict, not a release, and
not operational success. The live gate is **not** switched to the repository copy; that remains
a Factory Director action after landing (BRD-83 non-goals).

## Identity and authority

- **Issue:** #83. The Factory Director's RELEASED comment (episode
  `factory-director-7e7fbb7bc9e043448674a2460f898ade`, 2026-09-24T09:08:15Z) authorizes
  IMPLEMENT for BRD-83's bounded extent only.
- **Invocation:** `AlienLogicLab/alienintent#83:PRODUCER:2c6a75f3-3ce6-4730-ba94-a7f1eb8e51ae`.
- **Worker:** Morty, Claude `claude-opus-5-5`.
- **Branch:** runtime-managed `b-disp/4cf01d9b-1a39-498c-a90f-3ab94e9d6881`.
- **Admission baseline:** `474343a4142316941340762a243e965ef44bb15c` (`origin/main` at release).
  `origin/main` has since advanced to `59db3c5` (FDH-01 live-proof evidence only; no path under
  `tools/live/`), so no rebase is needed.
- **Contract:** `docs/work-units/wave2/BRD-83.md`; native Agent Ready READY record
  `docs/evidence/wave2-readiness-assessments/BRD-83.2026-09-24T055035.450917Z.assessment.json`.

## Commits (in order)

1. `1439457`: verbatim import of `release_admission.py` and `test_release_admission.py` into
   `tools/live/` (AC1).
2. `7afec82`: release-point reading, identifier recognition, fixture tests and the proven-red
   harness `tools/live/brd83_proven_red.py`.
3. `3ed6d5c`: guard against an option-shaped release point reaching `git fetch`, found in
   self-review; fixture test plus an 11th proven-red variant. **This is the revision proven below.**
4. The evidence commit that adds this file.

`git diff 474343a 3ed6d5c --stat` touches only the four `tools/live/` files above. `admit()` is
byte-unchanged; `tools/orchestration/test_director.py` and `director.py` are unmodified.

## AC1: verbatim import custody

| File | Live source sha256 (re-checked before import) | `git show 1439457:tools/live/<file> \| sha256sum` |
|---|---|---|
| `release_admission.py` | `fb8758cecb4db13073be71e39f37c77250b018406d7c968e45d1fa57231b9b1b` | identical |
| `test_release_admission.py` | `e8000ad29d07d6a6064a7f4982b760ca957376e9d518991b8c8497a2954e5e4e` | identical |

At `1439457`, `python3 -m pytest -q tools/live/test_release_admission.py` → exit 0, **23 passed**.

## Design decisions (recorded as the assessment requested)

- **Repository root.** `ALIENINTENT_WORKDIR` if set (an explicit override wins outright);
  otherwise `git rev-parse --show-toplevel` from the gate's own directory; otherwise from the
  current directory. The repository copy therefore finds its own checkout, and the current live
  copy in `~/.local/share/alienintent-bootstrap/` works when run from inside a checkout. There
  is no hard-coded path. Both derivations are exercised by fixture tests.
- **Fetch / staleness.** When the release point has the form `<remote>/<branch>` and the remote
  exists, the gate runs `git fetch --quiet <remote> <branch>` first. A stale `origin/main`
  would reproduce the original invisibility, and the proven-red variant `trusts_a_stale_remote_ref`
  shows the fixture catches exactly that. A failed fetch is reported on stderr
  (`FETCH FAILED; local ref used`) but is not fatal and adds no admission condition. The release point
  is resolved once to a commit, and that commit is used for both the record read and the baseline
  ancestry check.
- **Reading.** `git show <release-commit>:<path>`. The working tree is never read. A record that
  exists only in the working tree, or only in an unpushed local commit, is not used.
- **Recognition.** `docs/evidence/wave2-readiness-assessments/<ID>.<stamp>.assessment.json` where
  `<ID>` is `[A-Za-z0-9-]+` and `<stamp>` is one or more dot-separated non-empty `[A-Za-z0-9-]+`
  segments. The path may not be preceded by `[\w./-]` or continued by `[\w/-]` (optionally after
  one `.`). This rejects `../docs/...`, `.../<dir>/<ID>...`, `...json/..` and empty segments.
  The Wave 1 `PY-NN[A-Z]?` path is unchanged (`biu_from_body` is byte-unchanged).
- **Precedence.** The Issue body's cited record comes first, as before. The release record's
  cited record (the comment `release_record_from` already selects) comes second. The native
  receipt comes last. A record found at the release point returns its disposition even when that
  is `None` (unchanged). An absent or unreadable record falls through, as before.
- **Output.** stdout and exit codes are unchanged. One diagnostic line goes to stderr:
  `release point <rp> -> <sha> (<fetch state>) in <repository>`.
- **Citation compatibility.** Across all Issue bodies (`gh issue list --state all`), the old and
  new matchers agree on every citation, except that `ARP-01` is newly recognised. No Issue cites a
  record through a URL.

## AC2–AC5: offline fixture

`tools/live/test_release_admission_release_point.py` runs the real CLI against a disposable
world:

- a bare `origin` repository;
- a clone standing in for the shared checkout, never pulled;
- a fake `gh` on `PATH` that answers from a JSON file and logs every call;
- `HOME` redirected so the live `state.json` is never read.

No test contacts GitHub, Project #1 or any Issue. `test_the_gate_only_reads_from_github` asserts
from the call log that only `issue view`, `project item-list` and a GET `api` call are made.

| AC | Tests |
|---|---|
| AC2 | `test_a_record_landed_at_the_release_point_but_absent_from_the_checkout_is_found` (the local `origin/main` is stale before the run and the file is absent from the working tree): ADMITTED, `agent_ready=READY`. `test_a_record_present_only_in_the_working_tree_is_not_used` and `test_a_record_committed_only_in_the_local_checkout_is_not_used`: exit 1, `agent_ready=None`. `test_an_explicit_release_point_is_read_instead_of_origin_main`. |
| AC3 | `test_a_record_for_any_biu_is_admitted_from_the_body_or_the_release_record`: `ARP-01`, `FDH-01` and `WO-220202`, each cited in the body and in the release record (6 cases). `test_a_readiness_record_for_any_biu_identifier_is_recognised` (3 cases). Rejections: `test_a_path_that_climbs_out_of_the_record_directory_is_rejected`, `test_a_record_path_reached_through_a_parent_prefix_is_rejected`, `test_an_identifier_containing_a_slash_is_rejected`, `test_a_record_in_another_directory_is_rejected`, `test_a_record_path_continued_past_the_file_is_rejected`. |
| AC4 | `test_the_native_receipt_fallback_is_unchanged_when_no_record_is_cited`, `test_the_native_receipt_fallback_is_unchanged_when_the_cited_record_is_absent`, `test_a_cited_record_that_is_not_an_agent_ready_assessment_still_yields_no_disposition`, and the 23 original tests unchanged. |
| AC5 | The whole fixture file, plus `test_the_gate_only_reads_from_github`, `test_the_repository_is_derived_from_the_gate_location_without_an_override` and `test_a_live_copy_outside_any_repository_uses_the_current_directory`. |

## AC6: proven red

`python3 tools/live/brd83_proven_red.py --json` → exit 0, `proven_red: true`, **11/11 variants**.
Each variant copies the gate and tests to a temporary directory and applies exactly one
permissive change. The named test must pass intact, fail under the variant, and pass again once
restored. Raw output: `brd-83/proven-red.json`.

| Variant | Test | Intact | Permissive variant | Restored |
|---|---|---|---|---|
| `reads_the_working_tree` | `test_a_record_present_only_in_the_working_tree_is_not_used` | 1 passed | 1 failed | 1 passed |
| `reads_the_local_head` | `test_a_record_committed_only_in_the_local_checkout_is_not_used` | 1 passed | 1 failed | 1 passed |
| `trusts_a_stale_remote_ref` | `test_a_record_landed_at_the_release_point_but_absent_from_the_checkout_is_found` | 1 passed | 1 failed | 1 passed |
| `fetch_takes_an_option_shaped_branch` | `test_a_release_point_shaped_like_an_option_is_never_passed_to_fetch` | 1 passed | 1 failed | 1 passed |
| `identifier_admits_dots_and_slashes` | `test_a_path_that_climbs_out_of_the_record_directory_is_rejected` | 1 passed | 1 failed | 1 passed |
| `identifier_admits_slashes` | `test_an_identifier_containing_a_slash_is_rejected` | 1 passed | 1 failed | 1 passed |
| `no_leading_path_boundary` | `test_a_record_path_reached_through_a_parent_prefix_is_rejected` | 1 passed | 1 failed | 1 passed |
| `no_trailing_path_boundary` | `test_a_record_path_continued_past_the_file_is_rejected` | 1 passed | 1 failed | 1 passed |
| `any_directory_under_docs_evidence` | `test_a_record_in_another_directory_is_rejected` | 1 passed | 1 failed | 1 passed |
| `wave2_identifier_is_wo_only` | `test_a_readiness_record_for_any_biu_identifier_is_recognised` | 3 passed | 2 failed, 1 passed | 3 passed |
| `release_record_not_consulted` | `test_a_record_for_any_biu_is_admitted_from_the_body_or_the_release_record` | 6 passed | 3 failed, 3 passed | 6 passed |

## AC7 and regression (at `3ed6d5c`)

| Command | Exit | Result | Log (sha256) |
|---|---|---|---|
| `python3 -m pytest -v -p no:cacheprovider tools/live/test_release_admission.py tools/live/test_release_admission_release_point.py` | 0 | 50 passed (23 original + 27 new) | `brd-83/release-admission-tests.log` (`a654fe42…69da`) |
| `python3 -m pytest -q tools` | 1 | 718 passed; 1 failed: the known non-hermetic baseline debt `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary` (out of scope, unmodified). The baseline at `1439457` was 691 passed with the same single failure. | `brd-83/python-tools.log` (`75ff2ce5…8dc4`) |
| `PYTHONPATH=src python3 -m pytest -q tests` | 0 | 551 passed (baseline 551) | `brd-83/python-tests.log` (`b5ffd043…a7a6de`) |
| `node scripts/check.mjs all` | 0 | 340 + 18 + 3 pass, 0 fail | `brd-83/check-all.log` (`6ca67a54…1d94`) |
| `python3 tools/live/brd83_proven_red.py --json` | 0 | 11/11 proven red | `brd-83/proven-red.json` (`2659e6da…b761e`) |

## #80 / #81 outcome (reported, scope not widened)

A read-only analysis of the live Issue text uses the candidate's pure functions
(`release_record_from`, `assessment_record_path`, `disposition_from_native_comment`):

| Issue | Body cites record | Release record cites record | Where the record is cited |
|---|---|---|---|
| #80 (WO-220202) | no | no | only the native-receipt comment (comment 0) |
| #81 (WO-220203) | no | no | only the native-receipt comment (comment 0) |
| #89 (FDH-01) | no | no | only the native-receipt comment (comment 0) |
| #83 (BRD-83) | no | yes: the RELEASED comment (comment 3) cites it | receipt (comment 2) and release record (comment 3) |

**#80 and #81 would still need the native-receipt fallback.** Neither their bodies nor their
release records cite the record path, and no directory discovery was added (per the assessment).
A future release without the manual receipt needs the Director's RELEASED comment, or the Issue
body, to cite the record path; the gate then finds it at `origin/main`.

For #83, the path cited in the RELEASED comment would have been found at admission time. Today
`release_record_from`'s existing newest-match selection (unchanged) picks the later state-record
comment (comment 4), because it also matches `RELEASED … authoriz`. Selection is out of scope and
is recorded here only as an observation.

**Credential observation.** Under the PRODUCER credential (`gh-morty`),
`gh issue view --json …,projectItems` fails with `Resource not accessible by personal access
token`, so a live CLI run from the worker reports `status=None` for every Issue. This is
pre-existing and credential-scoped: the Director runs the live gate under its own credential.
It is why the #80/#81 analysis above uses the pure functions rather than the live CLI.
