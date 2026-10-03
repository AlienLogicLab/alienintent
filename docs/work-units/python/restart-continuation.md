# Work unit: restart continuation for registry launches

**Label:** `RESTART-CONTINUATION` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** path row 7, the first of the three connections still missing from the critical path. The other two, in order, are separate automated closure and cleanup (row 8), then automatic selection and launch of the next eligible item. Builds on `main` `893063e` (units 6b, 6c-1, 6c-2 and record-completed-work).
**Scope (Founder, 2026-10-03):** only these three:
- the two capacity leaks;
- resolving parked launches;
- ownership of abandoned worktrees.

Reuse the existing recovery and cleanup code.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

On restart, `FactoryCoordinator._recover` already does three things:
- it reads back a finished worker's journaled outcome and records it once;
- for a worker that died without a result, the existing missing-result rule allows one bounded replacement;
- it parks an effect it cannot prove as an authority block that needs a decision.

Three gaps remain for registry launches:
1. **Two capacity leaks.** In two crash points, `_recover` returns False, and every later `start()`, `launch()` and `reconcile()` answers `capacity-unavailable` for the whole profile, permanently:
   - after the repository reservation, before `commit_with_effect`, nothing is saved and no effect exists;
   - after `commit_with_effect`, before `claim_effect`, the effect is `pending` (`factory_coordinator.py` `_recover` and `_park_unknown_effect`; `park_unknown_effect` needs an `unknown` effect).

   Neither crash point started a worker: a worker starts only after `claim_effect`.
2. **No way to resolve a parked launch from the registry profile.** `decisions decide` exists, but the registry profile cannot reach it (`work_registry_profile` exposes only `work_registry`; `cli.py` builds `OperatorControlPlane` from attributes that profile does not have). So a parked work item keeps its WIP slot for ever.
3. **Abandoned worktrees.** The workspaces of a launch are known only in memory (`RealWorkerProvider._finished_workspaces`). After a restart, nothing cleans the PRODUCER worktree, the VERIFIER clone or the PRODUCER read-back folder of a launch whose outcome is recorded or decided.

This unit closes these three gaps and nothing else:
- **The first leak, automatically.** The reservation's owner `launch:<id>:<v>` has no effect, and the coordinator record is still at version `v`. That proves nothing was saved or started, so the reservation is released.
- **The second leak, by an existing park.** The `pending` effect is claimed (pending to unknown, the existing `claim_effect`) and parked through the existing `_park_unknown_effect`, with the reason "launch saved but never started". It is not resolved automatically. The saved launch already changed the coordinator record (role, and the first IMPLEMENT count), and only a decision may say what happens next.
- **A parked launch is resolved by `work decide`.** This is the registry profile's way to submit the existing decision (`authorize` or `cancel`) through the existing decision path.
- **Abandoned workspaces are owned by their correlation.** The existing `finalize(invocation, retain=False)` finds them from their fixed paths when they are not in memory, and cleans them with the existing guards.

No new store, record kind, state, outcome kind, configuration source or recovery mechanism is added. No running worker is re-attached.

## 1. The changes

**1. The first capacity leak** (`execution_coordination/application/factory_coordinator.py`, `_recover`). This covers a `repository` reservation owned by `launch:<id>:<v>` with no effect row for that correlation in the store's existing read-only `effect_ledger`. If the coordinator record `factory:<id>` is at store version `v`, the reservation is released with its owner and fence, through the existing `release`. Nothing else is written, and recovery continues. In any other version, the existing path applies unchanged.

**2. The second capacity leak** (the same method). This covers a reservation whose correlation's effect is `pending`. The effect is claimed with the existing `claim_effect`, then parked with the existing `_park_unknown_effect`. The escalation names the correlation and the reason `launch saved but never started`. The WIP slot is kept, as for every authority block. The cycle counts are unchanged. Recovery continues for the other reservations, so the profile is no longer wedged.

**3. `work decide <id> --choice authorize|cancel --quote "<the Founder's words>"`** (`control_plane/adapters/cli.py`, `control_plane/application/operator.py`, `composition/work_registry.py`). It submits the work item's open decision request through the same existing decision path as `decisions decide` (`DecisionInbox.submit`, leading to `FactoryCoordinator.validate_decision` and `record_decision`), on the registry coordinator. The approver is the contract's `authority_issuer`. The existing behaviour then applies:
- `cancel` records `cancelled-by-decision`, releases the WIP slot and cancels blocked dependents;
- `authorize` lifts the unknown effect with the existing `authorize_unknown_effect` and leaves the item eligible, so the next `work launch` is a fresh attempt with a new correlation.

One added refusal guards `authorize`. When the parked correlation has an `invocation-started` journal record, `authorize` is refused unless the existing `RealWorkerProvider.attest_ownership` answers `owner-terminated`. That means the owner is gone, no owned work is running and no publish had begun. Otherwise the answer is `OWNER_NOT_TERMINATED`, naming the attestation, and nothing is written. A correlation with no journal record was never started, so `authorize` is allowed. A work item with no open decision request answers `NO_OPEN_DECISION`. A repeat of the same decision is a repeat under the existing idempotency key.

**4. Abandoned workspaces** (`invocation_runtime/application/real_worker.py`, `finalize`). When the correlation is not in the in-memory map, `finalize(invocation, retain=False)` derives the launch's workspaces from their fixed paths:
- the PRODUCER worktree `<workspace root>/<correlation>`;
- the VERIFIER clone `<verifier root>/verifier-<correlation>`;
- the read-back folder `<verifier root>/producer-<correlation>`.

The worktree is cleaned with the existing `GitWorktreeAdapter.cleanup`, which refuses a live owner or a dirty tree; a refusal is kept and reported in the existing `cleanup_diagnostics`. The two folders are removed only when they lie inside their configured root and `attest_ownership` answers `owner-terminated`. Otherwise they are kept and reported. The `invocation/` branch and the pushed candidate branch are not touched.

The coordinator calls `finalize(retain=False)` on the same paths as today:
- after `_recover` records a result for that correlation (the existing call after `_record_result`);
- after `work decide` resolves its parked launch with `authorize` or `cancel`.

A parked, unresolved launch keeps its workspaces (`retain=True`, as today), so they stay available for diagnosis.

## 2. What stays out

- re-attaching to a worker that is still running;
- continuing the same attempt (every relaunch has a new correlation, as today);
- the profile-wide failure when a reservation's work item is missing from the READY snapshot (a separate defect, recorded for later);
- the wrong decision-inbox reason after a `binding-refused` launch (recorded for later);
- `cancel()` passing the work identity where the provider expects the correlation (recorded for later);
- two `work launch` runs at the same time (recorded for later);
- closure and the cleanup of landed work (row 8);
- automatic next-item selection;
- a new store, record kind, state, outcome kind or configuration source.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/application/factory_coordinator.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/control_plane/adapters/cli.py`
- `src/alienintent/control_plane/application/operator.py`

Tests:
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/composition/test_worker_launch.py`
- `tests/invocation_runtime/test_runtime.py`
- `tests/control_plane/test_cli.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The fake worker executables come from a test routing file, as in unit 6c-2, and each crash is injected at its exact point through the registry launcher.

1. **First leak.** A crash after the repository reservation and before `commit_with_effect` is followed by `work launch`:
   - the reservation is released;
   - the coordinator record is unchanged;
   - no decision is requested;
   - the launch proceeds.

   Catches a wedged profile, and a release that also writes a record.
2. **Second leak.** A crash after `commit_with_effect` and before `claim_effect` is followed by `work launch`:
   - the launch is parked as an authority block naming `launch saved but never started`;
   - its WIP slot is kept;
   - the cycle counts are unchanged;
   - no worker starts;
   - in the same recovery pass, another launch's finished, journaled outcome is still recorded, and `_recover` does not return False.

   Catches a wedged profile, an invented outcome and a changed count.
3. **Resolving a parked launch.**
   - `work decide <id> --choice cancel` records `cancelled-by-decision` and releases the WIP slot.
   - `--choice authorize` lifts the effect, and the next `work launch` runs a new correlation.
   - `authorize` is refused (`OWNER_NOT_TERMINATED`, nothing written) while the owner is alive, owned work is running or a publish had begun.
   - A work item with no open request gives `NO_OPEN_DECISION`.
   - The same decision twice is a repeat.

   Catches a decision path that bypasses validation, and an authorize over a live worker.
4. **Abandoned workspaces.** After a restart:
   - a recorded PRODUCER result removes its clean worktree and its read-back folder;
   - a recorded VERIFIER result removes its clone;
   - a dirty worktree, or one with a live owner, is kept and reported;
   - nothing outside the configured roots is touched;
   - a parked, unresolved launch keeps its workspaces until `work decide` resolves it.

   Catches workspaces that are never cleaned, a forced clean and removal outside the roots.
5. **Restart changes no count, and existing recovery is unchanged.** These existing tests pass unchanged:
   - the check6 and check8 recovery and cycle-count tests;
   - the missing-terminal-result replacement;
   - the read-back of a finished worker.

   Catches a regression in existing recovery.
6. **Fitness.** The changed test files pass when run together in one run (no full suite), and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 5. Excluded

See section 2. Also excluded: changing earlier packets.

## 6. Review record

**Revision 1 (2026-10-03).** First draft, from the existing row 7 fact sheet (no new discovery), against `main` `893063e`, with the Founder's scope: the two capacity leaks, resolving parked launches and ownership of abandoned worktrees, reusing the existing recovery and cleanup code.
