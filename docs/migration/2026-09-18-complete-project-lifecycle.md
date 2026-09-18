# Complete Project lifecycle correction — 2026-09-18

## Authority and design

The operator requires CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT →
VERIFY → REVIEW → ACCEPT → DONE. The Project lifecycle is broader than the
execution engine. Merge/landing is a repository operation during closure after
ACCEPT on the path to DONE, never a lifecycle state.

The current Node bootstrap remains the implementation. Dispatch stays limited to
IMPLEMENT (producer), VERIFY (verifier), ACCEPT (producer closure). No automatic
promotion, new lane, Python implementation, or FactoryChecks change is authorized.

## Implementation plan

- [x] Pause live proof and preserve invocation state and existing worker evidence.
- [x] Snapshot and update the existing GitHub Status field in place; verify order,
  existing option identities, single-field identity and existing item values.
- [x] Add regression cases for complete profiles/App preflight, absent lifecycle
  options, ambiguous fields/options, and non-dispatch states on webhook/startup.
- [x] Share the full lifecycle vocabulary between configuration and App preflight;
  update examples, synthetic integration fixtures and active operator guidance.
- [x] Run full regression, independent review and any finding repairs.
- [ ] Commit and push correction; install validated profile and resume live proof.

## Verification evidence

Baseline b251979a8edd18e031840b0f08639938a6c141bb passed all required groups:
279 runtime tests, worker-preflight PASS, 18 RAI tests and 2 policy tests.
The existing Status field was updated without creating a competing field.
All five existing option IDs and the proof item's VERIFY value were preserved.
The five new states were inserted before IMPLEMENT in the required order.

The proof had begun before the correction request: producer artifact and its
VERIFY comment exist. It was paused before completion. These observations are
historical evidence, not a claim that the full live proof passed.

The final full regression command was `rtk proxy node scripts/check.mjs all`:
309 runtime tests, worker-preflight PASS, 18 RAI tests and 2 policy tests, all passing.
`git diff --check` passed. Before the implementation change, the new tests reproduced
rejection of a full profile and acceptance of incomplete Project lifecycles.

The production dispatcher and its role mapping are unchanged. Regression cases
exercise CAPTURE, SPECIFY, PLAN, TASKS, READY, REVIEW, DONE and MERGE on both webhook
and startup paths, confirming no launches, transitions, worker preflight or content
enrichment. Existing execution, authenticated-result, closure and recovery tests pass.

## Existing field and option identity readback

Project: AlienLogicLab / AlienIntent / 1. Existing Status field:
`PVTSSF_lADOEcrpC84Bj5i_zhisMnY`. Exactly one Status field remained after mutation.

| Order | State | Option ID | Disposition |
|---|---|---|---|
| 1 | CAPTURE | `0b45e6a1` | Added |
| 2 | SPECIFY | `cd4f669d` | Added |
| 3 | PLAN | `47939326` | Added |
| 4 | TASKS | `162573f6` | Added |
| 5 | READY | `70a61331` | Added |
| 6 | IMPLEMENT | `1d0597c8` | Preserved |
| 7 | VERIFY | `3d828d3e` | Preserved |
| 8 | REVIEW | `c632da4e` | Preserved |
| 9 | ACCEPT | `87ca6ed8` | Preserved |
| 10 | DONE | `70d8419d` | Preserved |

GitHub's live `ProjectV2SingleSelectFieldOptionInput` schema exposes an optional
`id`, which was supplied for each existing option. The field ID and all five IDs
were read back unchanged, and the existing proof item retained VERIFY.

Private installation profiles must migrate `project.statusNames` to all ten names
before starting this version. Startup deliberately fails closed for old incomplete
profiles; no automatic workflow-state migration or new dispatch behavior was added.
Historical proof observations are retained rather than rewritten.

## Independent review

Independent code review found no blocking implementation issue and returned PASS.
The reviewer independently ran 205 targeted tests with zero failures and checked
the live before/after snapshots. Its test-hardening suggestion was applied:
non-dispatch tests count preflight/enrichment calls explicitly so startup error
handling cannot swallow a failing assertion. Full regression was repeated afterward.
