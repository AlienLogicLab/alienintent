# BRD-83 independent JC verification — repair cycle 1

Verdict: **REJECT**. Candidate `9b42ad5452306e567d767f50fffeb716f0588e96` from
`b-disp/a367e00e-a4d6-435c-801c-4d33d5c772ed` was fetched and checked out exactly in the
fresh runtime worktree `b-disp/a5106d95-091b-4c98-8141-c4b1492677e8`.
Invocation: `AlienLogicLab/alienintent#83:VERIFIER:12961a6a-6f0c-41c3-b217-179f1ea0ba43`.
Git and GitHub identities: JC / jc-github@factorychecks.com and jc-worker.

## Authority and baseline

Authority is Issue #83's Director release https://github.com/AlienLogicLab/alienintent/issues/83#issuecomment-5811219183,
BRD-83 AC1–7, the prior rejection https://github.com/AlienLogicLab/alienintent/issues/83#issuecomment-5811522023,
and repair candidate receipt https://github.com/AlienLogicLab/alienintent/issues/83#issuecomment-5811683704.
Admission baseline remains `474343a4142316941340762a243e965ef44bb15c`; the initially clean verifier
worktree started at `59db3c532a004e10dee60eede7a477e8e17545f1` (later FDH evidence).
A fast-forward attempt correctly refused divergence without changing the tree; verification used a
detached exact candidate, then moved only this invocation's baseline-only local branch to that candidate
for evidence publication. No baseline branch was changed.

## Blocking finding R1-continuation / P1

At `tools/live/release_admission.py:225`, `_wave1_biu` checks only
`prefix.endswith(f"{WAVE1_DIR}/")`. Thus an arbitrary repository path ending in that directory
is treated as the canonical Wave 1 directory. `assessment_record_path` at lines 238–239
then substitutes a different record path.

The two paths in `prefix-probe.py` are in another directory and must be rejected under AC3.
With only `docs/work-units/python/PY-05.assessment.json` committed READY and no native receipt,
both instead resolve to that record and the real CLI returns ADMITTED / exit 0.
This is wrong-record resolution, not filesystem traversal execution. The whole CLI reproduction
fails (exit 1); see `prefix-probe.log`. The original three-path JC probe now passes (exit 0).

Required repair: distinguish exact allowed repository-relative Wave 1 paths from supported blob URLs;
do not use an arbitrary suffix as the directory authority. Preserve bare filenames and the existing
legitimate citation forms. Add whole-resolver/CLI negative coverage for prefixed wrong directories,
and prove the new guards red. Keep `admit()` and native fallback unchanged.

## Fresh verification

Commands below were launched with `rtk proxy`; the batch runner used subprocess argument arrays
and retained each exit status and full output. All behavioral suites ran on exact candidate code.

| Check / command | Exit | Observation |
|---|---:|---|
| Extract both import blobs at `1439457`; `python3 -m pytest -q <temporary directory>` | 0 | 23 passed; both pinned digests match (`import.json`) |
| `python3 -m pytest -q tools/live/test_release_admission.py tools/live/test_release_admission_release_point.py` | 0 | 72 passed |
| `python3 tools/live/brd83_proven_red.py --json` | 0 | 23/23 listed variants: intact 0, fault 1, restored 0 |
| `python3 -m pytest -q tools` | 1 | 740 passed; only declared non-hermetic director model-selection failure |
| `PYTHONPATH=src python3 -m pytest -q tests` | 0 | 551 passed |
| `node scripts/check.mjs all` | 0 | runtime 340, RAI 18, policy 3; preflight PASS |
| `python3 -m pytest -q tools/live/test_project_materialization.py` | 0 | 12 passed |
| `python3 docs/evidence/brd-83-jc-12961a6a/original-probe.py` | 0 | Three original invalid citations refuse |
| `python3 docs/evidence/brd-83-jc-12961a6a/prefix-probe.py` | 1 | Two prefixed wrong-directory citations wrongly admit |

AC1/2/4/5/7 retain positive evidence. R2's two missing controls are now present and proven red;
AC6's listed controls pass, but new coverage must accompany R1's remaining repair. AC3 fails.
The baseline debt is explicitly allowed and is not a rejection reason.

Import digests:
- release_admission.py: `fb8758cecb4db13073be71e39f37c77250b018406d7c968e45d1fa57231b9b1b`
- test_release_admission.py: `e8000ad29d07d6a6064a7f4982b760ca957376e9d518991b8c8497a2954e5e4e`

AST comparison with the import shows `admit`, `biu_from_body`, `disposition_from_record`,
`disposition_from_native_comment`, and `project_status_from_issue` unchanged (`ast-identity.json`).
Fresh read-only #80/#81 checks show no resolved record pointer in their body or selected release record;
each still has a READY native receipt and needs that fallback (`existing-issues.json`).
Fetch failure remains a disclosed nonfatal stale-ref policy; it adds no admission condition.

## Separate read-only review of landed changes

Inspected diffs of `62b85e0` and `aa2b263` (merged in `13cac4e`) against Issue #83 AC2/AC4.
No blocking finding in those bounded changes. `src/github/authority.mjs:3–28` keeps marker-attempt
classification separate from strict single-marker acceptance; `src/runtime/dispatcher.mjs:172–185`
retains invocation, timestamp and worker-identity checks while classifying ordinary prose.
`test/dispatcher.test.mjs:1216–1284` covers ordinary comments, wrong author, unknown invocation,
malformed/duplicate directives, and no-PR merge instructions; the Node suite passes.
`src/runtime/dispatcher.mjs:10–20` names merge closure and prohibits PRs without changing lifecycle values.
This is prompt enforcement, not credential-level prohibition.
`tools/live/project_materialization.py:93–126` refuses incomplete/inconsistent board responses;
status vocabulary at lines 37–41 is preserved. Its 12 tests pass. This is not a claim that the live
GitHub add-path fault has been repaired.

## Disposition

Evidence-only additions on the verifier's own runtime-managed branch; producer implementation is unchanged.
No PR, main push, Project mutation, live gate switch, or other-repository change.
Candidate and verifier resources remain under BIU runtime custody, retained for producer repair and fresh
independent verification. No Founder authority gap was found. Preserve all passing evidence and prior
review records; this finding continues R1 rather than superseding its original proof.
