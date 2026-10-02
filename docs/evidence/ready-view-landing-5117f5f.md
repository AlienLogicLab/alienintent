# READY view landing record (5117f5f)

Unit: READY-VIEW-FROM-WORK-RECORD. Work item `989cb378-a47f-43cd-9056-8775782d1fd8`. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `5117f5fbb09536af47a56a88c7cab8d8441e2030` (branch `producer/ready-view-989cb378`).
- Merge base: `origin/main` `3a84129549f3db47983151f8393cf432b5326896`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/ready-view-from-work-record.md`. The file was already on `main` at `3a84129`, byte-for-byte equal to packets-branch commit `bc7fc00` (sha256 `458dd0dae0c56dae684fae8d08e0eae049bcb6894ed1ed09631b2b78181e3663`). The candidate does not change it.
- Scope: 12 files (6 production, 6 tests). Sandbox composition and sandbox tests unchanged. No timeout changed.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `989cb378-a47f-43cd-9056-8775782d1fd8` (`~/.local/state/alienintent/registry/`).
- Agent Ready: READY with `work assess`, attempt `f65570ef-28c2-455d-ad6d-9df599e46c9e` (provider limit 180 s).
- Founder approval: `~/.local/state/alienintent/registry/approvals/989cb378-a47f-43cd-9056-8775782d1fd8.json`.
- Design review: `~/.local/state/alienintent/registry/independent-review-463fa1b.md`.

## Real use (acceptance check 9)

Run read-only by the VERIFIER against real board #1. Records: `~/.local/state/alienintent/manual/ready-view-verification/round1-5117f5f/` (`check9-output.json`, `check9-stderr.txt`, `hashes-before.txt`, `hashes-after.txt`) and the evidence copy `~/.local/state/alienintent/manual/ready-view-check9/` (`run.sh`, `copy-20261002T143620Z/`).

- 138 of 138 board items read.
- READY column empty.
- Registry stores byte-identical before and after the run.

## Independent verification

| Round | Candidate | Verdict | Tests | Fitness | Wrong implementations caught | Record |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `5117f5f` | ACCEPT | 336 passed | PASS | 28 of 31 | `~/.local/state/alienintent/manual/ready-view-verification/round1-5117f5f/verdict-5117f5f.md` |

Tests run: the authorized test files, `tests/context_assembly/test_work_identity_service.py`, and every test importing `tests/support/live_github.py`.

Fitness command: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`

PRODUCER judgement accepted by the VERIFIER: rule refusals are isolated per row; a contract-resolver refusal still stops the sandbox import (sandbox semantics unchanged).

## Follow-ups (all non-blocking)

- N1: invalidated assessments are not checked.
- N2: a CRLF packet reads as no block (fails safe).
- N3: no test for a READY attempt of the current commit that is not the row's `assessment_ref`.
- N4: `items()` does not check page size.
- N5: `ready_refusals()` crashes without a READY view.
- N6: an unreadable work database is reported as `NO_LINK`.
- N7: the cleared listing is skipped silently if the attention store is unreadable.

## Landing checks

`origin/main` had not moved since `3a84129` when the candidate was merged. The merged tree is identical to the verified candidate tree (`git diff --quiet 5117f5f HEAD` before this record was added), so the verifier's round 1 results apply to it unchanged. No tests were run again.
