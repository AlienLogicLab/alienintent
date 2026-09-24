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

## Repair cycle 1 — JC REJECT of `c278f04` (R1, R2)

- **Invocation:** `AlienLogicLab/alienintent#83:PRODUCER:e2afdc0d-56fc-4617-9e1c-791bdfd86126`.
- **Branch:** runtime-managed `b-disp/a367e00e-a4d6-435c-801c-4d33d5c772ed`, built on the rejected
  candidate `c278f04` so that the import custody (`1439457`) and the earlier commits are kept.
- **Rejection:** JC, `AlienLogicLab/alienintent#83:VERIFIER:796c5b49-250b-4c61-8c32-10e968d3fef9`.
  Evidence is at `5edbfd1` on `b-disp/2a642ca4-c96f-4e7d-9dd5-38df7bfebbaf`
  (`docs/evidence/brd-83-jc-796c5b49/`).

### R1 (P1): a rejected citation fell through to the Wave 1 record

**Cause.** `assessment_record_path` gave any text that `WAVE2_RECORD` rejected to the Wave 1
fallback, `biu_from_body`. That fallback matches a PY/WO identifier anywhere before
`.assessment.json`. So `docs/evidence/elsewhere/WO-220202.s.assessment.json`, the `../../../` form
and the `ARP/` form each resolved to `docs/work-units/python/WO-220202.assessment.json`.

**Repair (`775084d`).** The Wave 1 fallback now takes only a Wave 1 citation (`WAVE1_RECORD`,
`_wave1_biu`):

- the file name is exactly `<BIU>.assessment.json`, never a stamped name;
- the path is either bare or ends in `docs/work-units/python/` (a repository path or a GitHub blob
  URL);
- the path has no `..` segment;
- the path is not preceded by `[\w./-]` and not continued past the file.

A rejected citation now resolves to nothing, so the native-receipt fallback decides, as for any
uncited Issue. The following are all AST-identical to the import `1439457`:

- `admit()`
- `biu_from_body`
- `disposition_from_record`
- `disposition_from_native_comment`
- `project_status_from_issue`

`biu_from_body` is kept for its existing tests; the resolver no longer calls it. `main` differs
from the import only by the stderr diagnostic line added in `7afec82`; this repair does not change it.

**Proof.**

- JC's `probe.py` re-run against the repair exits **0**. All three invalid citations now refuse
  with exit 1 and resolve to `None`.
- A new CLI fixture test, `test_a_rejected_citation_never_admits_through_the_wave1_record`,
  covers 6 cases: JC's three paths, each with a WO- and a PY-shaped identifier. In every case a
  READY Wave 1 record for the same identifier is committed at the release point, and there is no
  native receipt.
- New unit tests cover:
  - the same 6 citations;
  - stamped names;
  - another directory;
  - `..` segments;
  - an embedded identifier;
  - a path continued past the file.
- A positive CLI test shows a Wave 1 record cited by its repository path is still admitted.
- `test_every_wave1_citation_form_on_record_still_resolves` covers each Wave 1 citation form found
  in the Issue bodies (#2, #50–#58, #68).
- **Compatibility:** every one of the 84 live Issue bodies resolves identically under `c278f04`
  and under the repair (15 resolve a record, 0 differ). See
  `brd-83/repair-1/citation-compatibility.txt`, which was read-only.

### R2 (P2): incomplete proven-red coverage

**Repair (`247e139`).** `brd83_proven_red.py` now carries **23** variants, up from 11:

- **JC R2 refusal tests:**
  - `ignores_the_explicit_release_point` → `test_an_explicit_release_point_is_read_instead_of_origin_main`
  - `accepts_any_assessment_outcome` → `test_a_cited_record_that_is_not_an_agent_ready_assessment_still_yields_no_disposition`
- **Read-only `gh` test:** `writes_through_gh` → `test_the_gate_only_reads_from_github`.
- **R1 guards:**
  - `rejected_citation_falls_back_to_wave1`, the exact pre-repair composition
  - `wave1_any_directory`
  - `wave1_parent_segment_allowed`
  - `wave1_accepts_stamped_names`
  - `wave1_no_leading_boundary`
  - `wave1_no_trailing_boundary`
- **Preserved behaviour:**
  - `native_receipt_fallback_removed`
  - `repository_not_derived_from_the_gate`
  - `wave1_directory_path_not_recognised`

Every variant passes intact, fails under the permissive change, and passes again once restored.

### Results at `247e139` (the proven revision)

| Command | Exit | Result | Log (sha256) |
|---|---|---|---|
| `python3 -m pytest -v -p no:cacheprovider tools/live/test_release_admission.py tools/live/test_release_admission_release_point.py` | 0 | 72 passed (23 original + 49 new) | `brd-83/repair-1/release-admission-tests.log` (`34acc9d8…ca68`) |
| `python3 tools/live/brd83_proven_red.py --json` | 0 | 23/23 proven red | `brd-83/repair-1/proven-red.json` (`031dda1e…42b6`) |
| `python3 -m pytest -q -p no:cacheprovider tools` | 1 | 740 passed. 1 failed: only the known non-hermetic `test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`, which is unmodified. | `brd-83/repair-1/python-tools.log` (`6ffcdb80…4203`) |
| `PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests` | 0 | 551 passed | `brd-83/repair-1/python-tests.log` (`7c306ad8…98aa`) |
| `node scripts/check.mjs all` | 0 | 340 + 18 + 3 pass, 0 fail | `brd-83/repair-1/check-all.log` (`3c0026c1…4730`) |

`git diff c278f04 247e139 --stat` touches only the four `tools/live/` files. Every other finding
of the earlier record stands, including the #80/#81 report: they still need the native-receipt
fallback.

## Repair cycle 2 — JC REJECT of `9b42ad5` (R1, prefixed Wave 1 directory)

- **Invocation:** `AlienLogicLab/alienintent#83:PRODUCER:f552e39b-2477-4052-9d30-17112e3158a8`.
- **Branch:** runtime-managed `b-disp/3dac0d9e-88fc-45cf-a499-e6e298726ebd`, built on the rejected
  candidate `9b42ad5`. The import custody (`1439457`) and all earlier commits are kept.
- **Rejection:** JC, `AlienLogicLab/alienintent#83:VERIFIER:12961a6a-6f0c-41c3-b217-179f1ea0ba43`.
  Evidence is at `7878265` on `b-disp/a5106d95-091b-4c98-8141-c4b1492677e8`
  (`docs/evidence/brd-83-jc-12961a6a/`).

### Cause

`_wave1_biu` accepted any prefix that *ended* in `docs/work-units/python/` and then substituted
the canonical Wave 1 path. So `docs/evidence/elsewhere/docs/work-units/python/PY-05.assessment.json`
and `docs/evidence/wave2-readiness-assessments/ARP/docs/work-units/python/PY-05.assessment.json`
both resolved to `docs/work-units/python/PY-05.assessment.json` and admitted it, although neither
citation names that file.

### Repair (`5b98a61`)

`WAVE1_PREFIX` must match the **whole** prefix (`fullmatch`). Only two forms are accepted:

- exactly `docs/work-units/python/` (the repository path); or
- `https://github.com/AlienLogicLab/alienintent/blob/<ref>/docs/work-units/python/`, where `<ref>`
  is one segment, `[A-Za-z0-9][\w.-]*` (a branch name such as `main`, or a commit SHA).

A bare `<BIU>.assessment.json` is still accepted, as before. The separate `..` segment check is
removed because the exact prefix subsumes it: no accepted prefix can contain a `..` segment. Its
proven-red variant now targets the ref grammar. `_wave1_biu` is the only function changed since
`9b42ad5`. `admit`, `biu_from_body`, `disposition_from_record`, `disposition_from_native_comment` and
`project_status_from_issue` remain AST-identical to the import `1439457`. `main` is unchanged since
`9b42ad5`. See `brd-83/repair-2/ast-identity.txt`, produced by `ast-identity.py`.

Now rejected: any other leading path (`x/`, `/`, `./`, `docs/evidence/elsewhere/`, `…/ARP/`), a blob
URL with a multi-segment ref or a `..` segment, and a URL of another repository, host, scheme or
view (`/tree/`). Refs containing `/` are not accepted because they cannot be told apart from a
path. No Issue on record uses one.

### Proof

- JC's `prefix-probe.py` (from `7878265`) exits **0**: both citations refuse with exit 1 and resolve
  to `None`. JC's original three-path probe also still exits 0. Both are retained, with logs, as
  `brd-83/repair-2/jc-*-probe.{py,log}`.
- A new whole-CLI fixture test, `test_a_prefixed_wave1_directory_never_admits_through_the_wave1_record`,
  covers 6 cases: JC's two prefixes and a foreign-repository blob URL, each with a PY- and a
  WO-shaped identifier. In each case the canonical Wave 1 record is READY at the release point and
  no native receipt exists.
- A positive CLI test, `test_a_wave1_record_cited_by_its_blob_url_is_still_admitted`, and a unit
  test for a blob URL at a commit SHA cover the preserved form.
- New unit tests: `test_a_wave1_directory_under_another_prefix_is_rejected` (10 cases),
  `test_a_wave1_blob_url_with_a_multi_segment_ref_is_rejected`,
  `test_a_wave1_url_that_is_not_a_blob_of_this_repository_is_rejected` (4 cases), and a blob-URL
  `..` case added to `test_a_wave1_record_reached_through_a_parent_segment_is_rejected`.
- **Proven red (`aee90b8`): 30/30.** Three variants are retargeted because their guard source
  changed (`wave1_any_directory`, `wave1_parent_segment_allowed` and
  `wave1_directory_path_not_recognised`). Seven are new:
  - `wave1_directory_is_a_suffix`: the exact rejected cycle-1 composition, against the whole CLI;
  - `wave1_directory_is_a_suffix_unit`: the same composition, against the unit test;
  - `wave1_prefix_is_searched`;
  - `wave1_blob_ref_multi_segment`;
  - `wave1_any_blob_url`;
  - `wave1_blob_url_not_recognised`;
  - `wave1_blob_url_at_a_commit_not_recognised`.
- **Compatibility:** `citation-compatibility.py` read every Issue body **and every Issue comment**
  (84 bodies, 256 comments; read-only `gh api`) and compared `9b42ad5` with the repair. 39 texts
  resolve a record and **0 differ**. That includes every Wave 1 body (#2, #50–#58, #68). The #80/#81
  report is unchanged: they still need the native-receipt fallback.

### Results at `aee90b8` (the proven revision; the evidence commit touches only `docs/`)

| Command | Exit | Result | Log (sha256) |
|---|---|---|---|
| `python3 -m pytest -q -p no:cacheprovider tools/live/test_release_admission.py tools/live/test_release_admission_release_point.py` | 0 | 95 passed (72 before + 23 new) | `brd-83/repair-2/release-admission-tests.log` (`c48ce162…a4ce`) |
| `python3 tools/live/brd83_proven_red.py --json` | 0 | 30/30 proven red | `brd-83/repair-2/proven-red.json` (`984636f4…706a`) |
| `python3 docs/evidence/brd-83/repair-2/jc-prefix-probe.py` | 0 | both prefixed citations refuse, exit 1 | `brd-83/repair-2/jc-prefix-probe.log` (`a9ace551…14cb`) |
| `python3 -m pytest -q -p no:cacheprovider tools` | 1 | 763 passed. 1 failed: only the known non-hermetic `test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`, which is unmodified. | `brd-83/repair-2/python-tools.log` (`0e3d4931…5a87`) |
| `PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider tests` | 0 | 551 passed | `brd-83/repair-2/python-tests.log` (`d2a0796c…8671`) |
| `node scripts/check.mjs all` | 0 | 340 + 18 + 3 pass, 0 fail | `brd-83/repair-2/check-all.log` (`a0bf1599…a24`) |
| `python3 -m pytest -q -p no:cacheprovider tools/live/test_project_materialization.py` | 0 | 12 passed | `brd-83/repair-2/project-materialization.log` (`c9055288…b633`) |

`git diff 9b42ad5 aee90b8 --stat` touches only the four `tools/live/` files (127 insertions, 6
deletions). I opened no pull request, pushed nothing to `main`, made no Project or Issue mutation
and did not switch the live gate.
