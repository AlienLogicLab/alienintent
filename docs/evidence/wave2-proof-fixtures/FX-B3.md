# FX-B3 / FX-B4 — Canonical live release admission proof (WO-220506, Issue #126, SF-REQ-015/051)

This is the retained proof record for DAG node B3 (`external_proof_prerequisite`), executed by PRODUCER Morty
(invocation `AlienLogicLab/alienintent#126:PRODUCER:20b22537-6123-4278-aa13-f8d893951be0`) against the fixture pinned
in `docs/work-units/wave2/WO-220506.md` ("FX-B3 fixture", "Phase 2 target binding and fixture pin — 2026-09-28",
"FX-B3/FX-B4 canonical precondition re-pin — 2026-09-28"). Proof level: `OPERATIONAL_OR_EXTERNAL_AUTHORITY`.

**Completion predicate (B3):** all six existing release preconditions plus eligibility are verified at the actual
live-profile prelaunch boundary; meaningful invalid cases launch zero actors. Readiness is not release.

**Name collision.** WO-220506.md calls its phase-2 fixture "FX-B4". That id already belongs to DAG node B4
(WO-220507, `FX-B4.md`), which this record does not touch. Here "FX-B4" always means WO-220506 phase 2. Both phases are
retained under `FX-B3/`.

## Authority and inputs

- Release authority: SWF-35 via `docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md`. Phase 2
  target authority: Founder handoff `founder-authorize-125-126-operational-proof-20260927T230647Z`, bound in
  WO-220506.md. Canonical coverage prerequisite WO-220611 (#141) is DONE (`598ea0d`).
- Release record: IMPLEMENT is authorized (Issue #126 comment 2026-09-27T23:32:32Z). The fresh native Agent Ready
  assessment is READY (`WO-220506.2026-09-28T041646.663840Z`, input sha256 `502aecff…ab82`).
- Candidate baseline: `origin/main` @ `5149d4d5c76ccead8659a70a513e7a0c17a50840`.
- Fixture revision: `tools/live/fx_b3_release_admission_proof.py` committed at
  `e9f165426fecb350e4374904b1c2dcd8e6cfae38`, tool sha256 `e00b4112…6f22`. Both runs record `tool_uncommitted: false`.
- Prior proof preserved unchanged: the pre-execution coverage finding on `b-disp/760ff8cd-68a8-40b8-99cd-2d0a8b09cbf6`
  @ `a11e1dd716fef312698c32ba390ff10c722bf649`, and WO-220611's local FX-B3P record (`FX-B3P.md`).

## Commands and results

| Phase | Command | Exit | Launch id | Window (UTC) | `result.json` sha256 |
|---|---|---|---|---|---|
| 1 — FX-B3, sandbox `AlienLogicLab/alienintent-sandbox` / Project #2 | `PYTHONPATH=src python3 tools/live/fx_b3_release_admission_proof.py --target sandbox --out docs/evidence/wave2-proof-fixtures/FX-B3/phase1-sandbox` | 0 | `20260928T045326Z-973e` | 04:53:26–04:56:44 | `67d6e41b7b71d9cf5128e5963e17bb8d13edefeb00f7d0948adee2fe9b0e488d` |
| 2 — FX-B4, real `AlienLogicLab/alienintent` / Project #1 | `PYTHONPATH=src python3 tools/live/fx_b3_release_admission_proof.py --target production --out docs/evidence/wave2-proof-fixtures/FX-B3/phase2-project1` | 0 | `20260928T045705Z-24bd` | 04:57:05–05:03:57 | `e4b0837965c40657938b9c5388bbe4daaa2e3a121897071991640b78dd79e1bf` |

Each phase directory retains the following:
- `result.json`: every case's expected and observed outcomes, gate and `admit_release` answers, eligibility account,
  journal counts, binding refusals, withheld projection attempts, the probe items and their read-back, snapshot reads,
  the mutation log, cleanup and non-interference.
- `board-before.json` and `board-after.json`: full digests of every item.
- `ledger.json`: the created items and the cleanup receipt.
- `journals/`: the durable invocation and process journals of every case that launched.

Phase 1 also retains `production-board-before-after-diff.json`.

## Composition under proof

Both phases use the production composition root `GitHubProfileComposition`. Phase 1 builds its profile from
`~/.config/alienintent-sandbox/profile.json`. Phase 2 builds it from the running factory's own
`~/.config/alienintent/self-hosting.json` (repository, Project #1 and its App).

Each admission pass runs through `FactoryCoordinator._run`, in this order:

1. `ReleasePreconditionGate.check`, which uses the store-held release records and a fresh clone of the target
   repository with release point `origin/main`.
2. `admit_release`, with the configured per-BIU allocation.
3. The K3 `RoleBindingGuard`.
4. `RealWorkerProvider`, with a durable `JsonlInvocationJournal` and `GitWorktreeAdapter`.

**Only the worker process is doubled.** It is the S0 `ScriptedWorkerProcess`, scripted to `authority-block`, so no
candidate is committed or published and no provider runs. The clone's push URL is also set to a nonexistent path.

**Snapshots.** Every admission pass reads the Project fresh through a paginated Projects v2 reader.

**Observation.** `admit_release` and `gate.check` are wrapped observation-only. Each wrapper delegates unchanged and
records which check answered.

## Observed cases (identical in both phases)

| Case | Pinned | Seeding | Expected | Observed (P1 / P2) |
|---|---|---|---|---|
| 02-positive-control | step 2 | valid record, allocation, digest, capabilities | 1 launch | 1 / 1; journal `authority-block`, 0 binding refusals |
| 03-identity-replay | step 3 | re-run the step-2 composition | 0, `eligibility:authority-block` | 0 / 0 |
| 04-policy-source-mismatch | step 4 | automatic-on contract, explicit release, non-automatic profile | 0, `admit_release:automatic-on release requires attributable policy authorization` | match / match |
| 05-readiness-digest-mismatch | step 5 | Project digest is that of contract version 0 | 0, `admit_release:stale readiness reference` | match / match |
| 06-unsatisfied-dependency | step 6 | dependency on work that is not DONE | 0, `eligibility:dependencies-incomplete` | match / match |
| 07-missing-capability | step 7 | requires `fx-b3-absent-capability` | 0, `admit_release:missing required capability` | match / match |
| 08-missing-budget-dimension | step 8 (re-pinned) | allocation lacks `fx-b3-unallocated-dimension` | 0, `admit_release:absent hard-required budget dimension` | match / match |
| E1-eligibility-not-released | "plus eligibility" | non-automatic profile, never released | 0, `eligibility:not-released` | match / match |
| 09-no-release-record | step 9 | no record | 0, `gate:implementation-authorized` | match / match |
| 10-record-does-not-authorize | step 10 | `authorizes_implement=False` | 0, `gate:implementation-authorized` | match / match |
| 11-no-exact-baseline | step 11 | baseline `main` | 0, `gate:baseline-named` | match / match |
| 12a/12b | step 12 | null revision / absent `b…b` | 0, `gate:baseline-resolves` | match / match |
| 13-unreachable-baseline | step 13 | local-only `commit-tree` child of the release point, never pushed | 0, `gate:baseline-reachable` | match / match |
| 14-unsuperseded-denial | step 14 | denial wording in contract, record otherwise valid | 0, `gate:authority-wording-consistent` | match / match |
| C1 contrast (phase 1 only) | step 14 contrast | same wording plus superseding record | 1 launch | 1 / not run |

**Totals.**
- Phase 1: 2 launches (positive control and contrast), as expected. Phase 2: exactly 1 launch (the positive control),
  as expected.
- Both phases: 0 provider calls, 0 publications, 0 binding refusals.
- All 13 checks in each `result.json` are true.

## Blast radius, cleanup and non-interference (step 15–16)

**Step 15, fresh read-back.** Every probe item was still present at READY after all cases. The coordinator's lifecycle
projections were recorded locally and never written to the board.

**Mutation log.**

| Phase | Probe items | `addProjectV2DraftIssue` | `updateProjectV2ItemFieldValue` | `deleteProjectV2Item` |
|---|---|---|---|---|
| 1 | 15 | 15 | 30 | 15 |
| 2 | 14 | 14 | 28 | 14 |

- The updates are Priority P5 and Status READY on the run's own items.
- Every mutation names the target Project, and every update or delete names an item this run created
  (`mutations_only_on_own_items`).
- Phase 1 made zero writes to Project #1.

**Cleanup.** Every created item was deleted, the returned `deletedItemId` equals the created id, and a fresh read no
longer contains it (`cleanup.verified: true`, no failures).

**Non-interference.** Every other item's facts were digested before and after:
- Scope: Project item fields and timestamps, content title, body digest and state, labels, assignees, and the last
  100 comments by id, timestamp and body digest.
- Phase 2: Project #1's 126 items are byte-identical (`board-before.json` = `board-after.json`, sha256 `8d0f4aeb…9df0`).
- Phase 1: the sandbox's 17 items are identical (`8bdeb16f…ed8e`), and production Project #1's 126 items are
  identical (read-only).
- An independent App read-back after phase 2 shows 126 Issue items, no `FX-B` titled item, and #126 still at
  IMPLEMENT.

**Resident factory.** The running Node dispatcher lists only items whose content is an `Issue`
(`src/github/authority.mjs:73`), and it maps READY to no role (`src/runtime/dispatcher.mjs:22,160`). The READY draft
probes were therefore inert to it; no duplicate live work was possible.

## Deviations from the pinned text, and why

1. **Draft Project items, not Issues.**
   - The pinned credential is the existing App. The production App (and the sandbox App) grant `issues: read`,
     `organization_projects: write`, and neither can create or delete an Issue.
   - Draft items are pure Project-state writes, which is exactly what the Founder authorized ("minimum reversible
     Project-state writes").
   - `deleteProjectV2Item` removes them entirely, so "close and delete" is met with no residue.
   - The product reads them through the same descriptor path (`descriptor_from_body`).
   - A consequence: the Director's `project_materialization.py verify` would have flagged non-Issue items during the
     two runs' windows (about 7 minutes in total). Nothing remains.
2. **Worker double.** WO-220506.md names `ScriptedWorkerProvider`. Under `GitHubProfileComposition` every worker sits
   behind the K3 `RoleBindingGuard`, which requires the provider to expose its journal and grant issuer. The
   `ScriptedWorkerProvider` wrapper exposes neither, so the guard would refuse every launch and the positive control
   could not launch. The fixture therefore composes S0's `ScriptedWorkerProcess` behind the unchanged
   `RealWorkerProvider`, which is exactly what `ScriptedWorkerProvider` wraps. Only the process is substituted.
3. **Where steps 3 and 6 are refused.** The pinned text cites `release.py:59-61` for step 3 and `release.py:71-73` for
   step 6. At this call site the coordinator passes `admit_release` an empty ledger and treats the item's own
   dependencies as satisfied, so both are refused earlier, by `FactoryCoordinator` eligibility:
   - step 3 by the durable execution record (`authority-block`);
   - step 6 by `dependencies-incomplete`.

   Both are pre-launch refusals at the canonical boundary with zero launches. The fixture pins and asserts the check
   that actually refuses, as the prior coverage finding (#4) already disclosed. This is not missing coverage.
4. **Snapshot restricted to the run's own items.** Unrelated READY items are never admitted. This also matters
   because Project #1 carries 126 items: the product directory's `items()` reads only the first 50, and real BIU rows
   carry no fixture descriptor.
5. **Additions.**
   - Step 12 runs both variants the pin allows (12a, 12b).
   - E1 makes "plus eligibility" explicit.
   - The informative superseded-denial contrast runs only in phase 1, so phase 2 keeps exactly one positive launch.

## What this does not claim

- Phase 1 alone does not satisfy "actual live-profile"; phase 2 is the real Project #1 boundary.
- No real PRODUCER or VERIFIER was launched by the fixture, and nothing was released, merged or deployed. Admission
  proof is not release.
- Tokens and cost for this PRODUCER session are UNKNOWN. The fixture itself made zero provider calls.

## Verification guidance

- Re-run offline: `PYTHONPATH=src python3 -m pytest -q tools/live/test_fx_b3_release_admission_proof.py`. It drives the
  identical sequence over an in-memory board, shows a faulted gate failing the run, and shows the restored gate
  passing. This is registered as feature-regression pack `canonical-live-release-admission-proof`.
- Phase 1 may be re-run against the sandbox.
- Phase 2 should be judged from the retained evidence. Re-running it would add further production writes, which the
  bound authorization does not separately cover.
