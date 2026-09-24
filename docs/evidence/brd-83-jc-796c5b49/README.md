# BRD-83 independent verification — JC — REJECT

Invocation: `AlienLogicLab/alienintent#83:VERIFIER:796c5b49-250b-4c61-8c32-10e968d3fef9`.
Date: 2026-09-24. Git identity: JC / jc-github@factorychecks.com; GitHub: jc-worker.

## Authority and custody

Authority is the [Director release](https://github.com/AlienLogicLab/alienintent/issues/83#issuecomment-5811219183)
and its bound `docs/work-units/wave2/BRD-83.md`, with admission baseline
`474343a4142316941340762a243e965ef44bb15c`. That release supersedes the older baseline
in the contract. The [producer result](https://github.com/AlienLogicLab/alienintent/issues/83#issuecomment-5811430832)
identifies candidate `c278f04b9b9da6d7824c57b65d9efb11c96c2b12` on
`b-disp/4cf01d9b-1a39-498c-a90f-3ab94e9d6881`; fetch and `git ls-remote` confirmed it.

The fresh runtime-managed verifier worktree initially contained clean `59db3c5`.
All candidate checks ran at exact `c278f04`, before these evidence-only additions.
The candidate has four commits relative to the admission baseline and changes only
the gate, its tests/harness, and evidence. The later main-only FDH evidence is not
a candidate deletion. No implementation changes, live gate switch, Project changes,
Issue-body edits, PR, or baseline push were performed.

## Blocking findings on candidate

**R1 — AC3 path rejection is bypassed by the legacy fallback (P1).**
`tools/live/release_admission.py:218-222` rejects a malformed Wave 2 path at the new
regex but immediately calls `biu_from_body` (`:198`). That unanchored matcher extracts
`WO-220202` from wrong-directory, traversal, and embedded-slash citations and returns
`docs/work-units/python/WO-220202.assessment.json`. The supplied rejection tests use
ARP/FDH identifiers, so they do not exercise this fallback.

Independent offline CLI proof: land a READY record at that legacy location in a
temporary origin, provide a fake READY Issue with a normal release record, no native
receipt, and cite each of:

- `docs/evidence/elsewhere/WO-220202.s.assessment.json`
- `docs/evidence/wave2-readiness-assessments/../../../WO-220202.s.assessment.json`
- `docs/evidence/wave2-readiness-assessments/ARP/WO-220202.s.assessment.json`

All three print `ADMITTED` and exit 0; the required refusal is exit 1. This is
misresolution to a different committed record, not filesystem traversal execution.
`probe.py` reproduces all three; its exit 1 records the failed discriminating probe.
See `independent-path-probe.json`. The legacy matcher predates the candidate, but
the candidate's newly required rejection guarantee is not met by its composition.

Repair obligation: reject invalid Wave 2 citations before legacy fallback can
reinterpret them, while preserving legitimate Wave 1 paths and native receipts.
Add whole-resolver/CLI rejection coverage including WO and PY-shaped identifiers
and prove those guards red. Do not weaken `admit()` or expand live scope.

**R2 — AC6 is incomplete (P2).**
`tools/live/test_release_admission_release_point.py` adds refusal checks
`test_an_explicit_release_point_is_read_instead_of_origin_main` and
`test_a_cited_record_that_is_not_an_agent_ready_assessment_still_yields_no_disposition`.
Neither is targeted in `tools/live/brd83_proven_red.py:30-109`. The local-HEAD mutant
does not demonstrate the explicit-release-point refusal, and no mutant demonstrates
the invalid-assessment refusal. Eleven listed variants passing is not proof for
every new rejection/refusal test. Add the missing discriminating controls and
retain intact/pass → permissive/fail → restored/pass evidence.

## Fresh validation

Commands below were prefixed with `rtk proxy`. Raw output and exact subprocess
commands/exits are retained alongside this report (`commands.json`).

| Check | Exit | Observation |
| --- | --- | --- |
| `git show 1439457:tools/live/release_admission.py` then SHA-256 | 0 | `fb8758cecb4db13073be71e39f37c77250b018406d7c968e45d1fa57231b9b1b` |
| `git show 1439457:tools/live/test_release_admission.py` then SHA-256 | 0 | `e8000ad29d07d6a6064a7f4982b760ca957376e9d518991b8c8497a2954e5e4e` |
| Import blobs extracted to a temporary directory; `python3 -m pytest -q <directory>` | 0 | 23 passed |
| `python3 -m pytest -q tools/live/test_release_admission.py tools/live/test_release_admission_release_point.py` | 0 | 50 passed |
| `python3 tools/live/brd83_proven_red.py --json` | 0 | 11/11 listed variants: intact 0, permissive 1, restored 0 |
| `python3 -m pytest -q tools` | 1 | 718 passed; only the declared `test_substantial_technical_analysis_routes_to_codex_primary` failed |
| `PYTHONPATH=src python3 -m pytest -q tests` | 0 | 551 passed |
| `node scripts/check.mjs all` | 0 | runtime 340/340; preflight PASS; RAI 18/18; policy 3/3 |
| `python3 -m pytest -q tools/live/test_project_materialization.py` | 0 | 12 passed |
| `python3 docs/evidence/brd-83-jc-796c5b49/probe.py` | 1 | Three invalid citations admitted; independent AC3 failure |

AST comparison with the verbatim import confirms `admit`, `biu_from_body`,
`disposition_from_record`, and `disposition_from_native_comment` are unchanged.
The known failing orchestration test and implementation have no candidate diff;
its observed model mismatch is the declared baseline debt, not a rejection reason.

AC1, AC2, AC4, AC5, and AC7 have positive evidence. AC3 fails on R1; AC6 is
incomplete on R2. Preserve all passing checks, import custody and existing
evidence through repair. The supplied positive stale-checkout fixture proves
fetch plus committed-source lookup; it does not prove freshness after fetch
failure. The gate explicitly reports and uses the local ref on fetch failure,
an acknowledged producer decision rather than a new admission condition.

Read-only Issue #80/#81 checks confirmed neither body nor selected release
record has a recognized pointer and each has one native receipt. They still
need the existing fallback (`issue-paths.json`). No directory discovery was added.

## Separate read-only review of landed 62b85e0 and aa2b263

Inspected both diffs and their code retained at candidate SHA (merged earlier via
`13cac4e`). No blocking finding in those changes against #83 AC2/AC4:

- `src/github/authority.mjs:3-28` separates attempted result classification
  from strict single-marker acceptance and preserves invocation/role checks.
  `src/runtime/dispatcher.mjs:172-185` retains author, repository, claim and time
  validation. Ordinary Director prose becomes `NON_RESULT_COMMENT`; malformed,
  duplicate, unknown-invocation and wrong-author markers remain invalid.
  `test/dispatcher.test.mjs:1216-1284` exercises these cases; the full runtime
  suite passed independently.
- `src/runtime/dispatcher.mjs:10-20` names SWF-19 merge landing and forbids PRs
  without changing lifecycle state vocabulary. This remains prompt enforcement;
  the operations document correctly discloses the worker-capability limitation.
- `tools/live/project_materialization.py:93-126` requires completeness metadata,
  equal node/total counts and no next page. Its twelve tests pass. Status options
  at `:37-41` retain the existing vocabulary. This is read-back verification, not
  a claim that GitHub's historic add-path transport fault is repaired.

This favorable landed-change review is separate from rejection of `c278f04`.

## Disposition

JC evidence branch: `b-disp/2a642ca4-c96f-4e7d-9dd5-38df7bfebbaf`, based on the reviewed
candidate, contains only this review packet beyond that candidate. It is published
for retrieval and retained under runtime-managed BIU custody, not merged. The
candidate remains unaccepted; the dependency is producer repair of R1/R2 followed
by fresh independent verification. Factory lifecycle ownership governs cleanup of
both runtime-managed resources; JC does not delete its active worker worktree.
