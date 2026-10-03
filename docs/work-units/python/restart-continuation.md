# Work unit: restart continuation for registry launches

**Label:** `RESTART-CONTINUATION` (a document label; permanent id `bb39a588-bf9a-4d30-b573-b8245b8979a0`).
**Status:** Draft revision 5 (work item `bb39a588-bf9a-4d30-b573-b8245b8979a0`, at CAPTURE) for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** path row 7, the first of the three connections still missing from the critical path. The other two, in order, are separate automated closure and cleanup (row 8), then automatic selection and launch of the next eligible item. Builds on `main` `893063e` (units 6b, 6c-1, 6c-2 and record-completed-work).
**Scope (Founder, 2026-10-03):** only these three:
- the two capacity leaks;
- resolving parked launches;
- ownership of abandoned worktrees.

Reuse the existing recovery and cleanup code.
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "bb39a588-bf9a-4d30-b573-b8245b8979a0",
 "version": "revision-5",
 "intent": "Make registry launches survive a restart without a profile-wide wedge: release a repository reservation whose launch was never saved, park a launch that was saved but never started through the existing unknown-effect path, let the Founder resolve a parked launch with the existing decision path through work decide without launching anything, and clean an abandoned launch's PRODUCER worktree by its correlation with the existing cleanup guards.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-03: the critical path is not finished; prepare deterministic restart continuation next, before closure automation and next-item selection.",
  "Founder 2026-10-03: limit restart continuation to the two capacity leaks, resolving parked launches and ownership of abandoned worktrees; reuse the existing recovery and cleanup code; no new discovery.",
  "Founder 2026-10-03: no new store, mechanism or configuration source; missing or conflicting facts stop, never guess; a held launch keeps its WIP slot.",
  "Founder 2026-10-03: recovery must not release another launch's reservation; one launch at a time is enforced in code with the existing store's atomic reservation while the configurable WIP limit is preserved.",
  "Founder 2026-10-03: if publication may have partially succeeded, reconcile the exact candidate and remote result before permitting another attempt; the Founder's authorization cannot establish whether an external action happened."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/composition/test_worker_launch.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/test_git_source_control.py",
  "tests/control_plane/test_cli.py"
 ],
 "excluded_scope": [
  "re-attaching to a running worker or continuing the same attempt",
  "recording an already published candidate as the PRODUCER result",
  "the READY-snapshot recovery failure, the binding-refused inbox reason, cancel() identity",
  "closure and cleanup of landed work",
  "automatic next-item selection",
  "a new store, record kind, state, outcome kind or configuration source",
  "changing earlier packets"
 ],
 "dependencies": [
  "621b0120-9fd2-41a0-b816-0b30ecf14281"
 ],
 "required_capabilities": [
  "python",
  "git",
  "sqlite",
  "process-control"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-6 pass",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "landing record on main"
 ],
 "non_goals": [
  "closure automation",
  "next-item selection"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-launch.md",
  "docs/work-units/python/record-completed-work.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "direct merge to main",
  "landing record in docs/evidence",
  "remove temporary PRODUCER and VERIFIER worktrees"
 ],
 "stop_escalation_conditions": [
  "a landed interface does not match the packet",
  "a required fact has no existing authoritative record",
  "scope outside the authorized files"
 ]
}
```

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
- **A parked launch is resolved by `work decide`.** This is the registry profile's way to submit the choices the open decision request already offers (`authorize` or `defer`) through the existing decision path. It never launches anything; the next step is always an explicit `work launch`.
- **Abandoned PRODUCER worktrees are owned by their correlation.** The existing `finalize(invocation, retain=False)` finds the worktree from its fixed path when it is not in memory, and cleans it with the existing guards. VERIFIER clones and PRODUCER read-back folders are owned by row 8's cleanup.

No new store, record kind, state, outcome kind, configuration source or recovery mechanism is added. No running worker is re-attached.

## 1. The changes

**0. One `work launch` at a time, enforced in code** (`composition/work_registry.py`, `control_plane/application/operator.py`, `execution_coordination/application/factory_coordinator.py`).
- Before `FactoryCoordinator.launch` runs, `work launch` takes one exclusive registry-wide reservation with the store's existing atomic `acquire`: scope `launch`, key `registry`, owner `launcher:<ProcOwnership.current() as canonical JSON>`. It releases that reservation with its owner and fence in a `finally`.
- If the reservation is held, `work launch` reads its owner and asks the existing `ProcOwnership.owner_state`:
  - while the holder is `alive`, or its state is `unknown`, the answer is `LAUNCH_IN_PROGRESS`, naming the owner state, and nothing is written. Nothing is guessed. A reboot makes an earlier owner `terminated`;
  - only when the holder is `terminated` is the stale reservation released with its owner and fence (the store's existing `release`). If that `release` raises `StaleFence`, another process took it over first, and the answer is `LAUNCH_IN_PROGRESS`. Otherwise `acquire` is tried once more, and a failure there is also `LAUNCH_IN_PROGRESS`.
  - If `ProcOwnership.current()` gives no owner, `work launch` answers `LAUNCH_OWNER_UNAVAILABLE` and writes nothing.
- `_recover` skips a reservation with scope `launch` and key `registry`, as it skips `WIP_SCOPE`. It never releases that reservation. Only `work launch` releases it.
- `_recover` therefore runs only while this process holds the reservation. In the registry profile, `FactoryCoordinator.start()` and `reconcile()` are not reachable: `work_registry_profile` exposes only `work_registry`, and `work_registry` calls only `launch`. `work decide` does not run recovery. So a reservation with no effect, or with a `pending` effect, can only belong to a launch whose process has ended.
- The configurable WIP limit is unchanged: several work items may hold WIP slots between their steps. Only the launch processes are serialized.

**1. The first capacity leak** (`execution_coordination/application/factory_coordinator.py`, `_recover`). This covers a `repository` reservation owned by `launch:<id>:<v>` with no effect row for that correlation in the store's existing read-only `effect_ledger`. If the coordinator record `factory:<id>` is at store version `v`, the reservation is released with its owner and fence, through the existing `release`. Nothing else is written, and recovery continues. In any other version, the existing path applies unchanged.

**2. The second capacity leak** (the same method). This covers a reservation whose correlation's effect is `pending`. The effect is claimed with the existing `claim_effect`, then parked with the existing `_park_unknown_effect`. The escalation names the correlation and the reason `launch saved but never started`. `_park_unknown_effect` gains an optional reason, which defaults to today's text, so other callers are unchanged. The WIP slot is kept, as for every authority block. The cycle counts are unchanged. Recovery continues for the other reservations, so the profile is no longer wedged.

**3. `work decide <id> --choice authorize|defer --quote "<the Founder's words>"`** (`control_plane/adapters/cli.py`, `control_plane/application/operator.py`, `composition/work_registry.py`). It submits a choice on the work item's open decision request through the same existing path as `decisions decide`: `DecisionInbox.submit`, then `FactoryCoordinator.validate_decision` and `record_decision`, on the registry coordinator. `biu_version` comes from the open request (`DecisionInbox.list_open`). The idempotency key is `work-decide:<id>:<biu_version>:<choice>`. `actor` and `authority` are the contract's `authority_issuer`, `intent` is the choice and `reason` is the quote. The approver is the contract's `authority_issuer`. It offers only the choices that request offers: for a parked unknown effect, that is `authorize` or `defer` (`cancel` is not offered, and its commit is refused while the effect is unknown).
- The registry composition (`composition/work_registry.py`) gives `DecisionInbox` an admission that forwards `validate_decision` and `record_decision` to the registry coordinator, and whose `resume_after_decision` does nothing. `DecisionInbox` itself is unchanged. So `work decide` never calls `start()` and never launches a worker.
- After `authorize`, the existing `authorize_unknown_effect` lifts the effect, and the next `work launch` is a fresh attempt with a new correlation. After `defer`, the launch stays parked.
- Two added refusals guard `authorize`. Each writes nothing.
  - **A live worker.** The registry composition holds the `RealWorkerProvider` it built in `launcher()` and calls its existing `attest_ownership` directly. `authorize` is refused with `OWNER_STILL_RUNNING` when the answer is `owner-alive` or `owned-work-active`.
  - **A possibly partial publication.** When the correlation's journal holds `publication-started` (its `revision`, written just before the PRODUCER's push, real_worker.py:343-345), `authorize` first reconciles the exact candidate against the remote. `GitSourceControl` gains one public read-only method, `remote_revision(workspace, remote, branch) -> str | None`. It runs the same `ls-remote <remote url> refs/heads/<branch>` that `read_back_candidate` runs, keeps only the exact ref name (as `_remote_refs` does), clones nothing and pushes nothing. It returns the revision when the exact ref exists, and None only when `ls-remote` succeeds and the exact ref is not listed. When the remote cannot be read, it raises the existing `CandidateUnavailable`, and `authorize` answers `REMOTE_UNVERIFIED`. The branch is the existing `RealWorkerProvider.candidate_branch(invocation)` for the parked correlation. The workspace is the retained PRODUCER worktree `<workspace root>/<correlation>`; if it is missing, the answer is `REMOTE_UNVERIFIED`. Another attempt is allowed only when the remote shows nothing was published:
    - the branch is absent on the remote and `attest_ownership` answers `effect-unknown` (the owner has ended and no owned work runs): nothing was published, and `authorize` may proceed. Absent with any other attestation is `REMOTE_UNVERIFIED`;
    - the branch is at the journaled revision: the candidate was published, so `authorize` is refused with `CANDIDATE_PUBLISHED`, naming the branch and revision;
    - the branch is at any other revision: `REMOTE_CONFLICT`;
    - the remote cannot be read: `REMOTE_UNVERIFIED`. Nothing is guessed.
- The Founder's authorization never stands in for that reconciliation. Recording an already published candidate as the PRODUCER's result is not part of this unit; such a work item stays parked and is reported.
- A work item with no open decision request answers `NO_OPEN_DECISION`. A repeat of the same decision is a repeat under the existing idempotency key.

**4. Abandoned PRODUCER worktrees** (`execution_coordination/application/factory_coordinator.py`, `invocation_runtime/application/real_worker.py`).
- `_recover` gains one call to the existing `_finalize_workspace(identity, correlation, retain=False)` after it records a PRODUCER result for that correlation. Today it has none. A recorded `missing-terminal-result` keeps its worktree (`retain=True`), so the existing FX-O P2 progress proof is unchanged.
- When the correlation is not in the in-memory map, `RealWorkerProvider.finalize(invocation, retain=False)` derives the worktree from its fixed path, `<workspace root>/<correlation>`. It first asks its own existing `attest_ownership`. Only when the answer is `owner-terminated` or `effect-unknown` (the owner has ended and no owned work runs) does it clean the worktree with the existing `GitWorktreeAdapter.cleanup`, passing the owner process id from the correlation's `invocation-started` journal record. Any other answer keeps the worktree and reports it in `cleanup_diagnostics`, as does a refusal by the cleanup itself (dirty tree).
- A parked, unresolved launch keeps its worktree (`retain=True`, as today), so it stays available for diagnosis.
- The `invocation/` branch and the pushed candidate branch are not touched. VERIFIER clones and PRODUCER read-back folders are left for row 8's cleanup.

**Why recovery cannot release a live launch.** Changes 1 and 2 act on another launch's reservation only inside the exclusive reservation of change 0. That launch's process has therefore ended. No operating rule is relied on.

## 2. What stays out

- re-attaching to a worker that is still running;
- continuing the same attempt (every relaunch has a new correlation, as today);
- the profile-wide failure when a reservation's work item is missing from the READY snapshot (a separate defect, recorded for later);
- the wrong decision-inbox reason after a `binding-refused` launch (recorded for later);
- `cancel()` passing the work identity where the provider expects the correlation (recorded for later);
- closure and the cleanup of landed work, and of VERIFIER clones, PRODUCER read-back folders and the CLOSURE clone `<verifier root>/closure-<correlation>` (row 8);
- automatic next-item selection;
- a new store, record kind, state, outcome kind or configuration source.

## 3. Exact permitted files

Production:
- `src/alienintent/execution_coordination/application/factory_coordinator.py`
- `src/alienintent/invocation_runtime/application/real_worker.py`
- `src/alienintent/composition/work_registry.py`
- `src/alienintent/control_plane/adapters/cli.py`
- `src/alienintent/control_plane/application/operator.py`
- `src/alienintent/invocation_runtime/adapters/git_source_control.py` (`remote_revision`)

Tests:
- `tests/execution_coordination/test_factory_coordinator.py`
- `tests/composition/test_worker_launch.py`
- `tests/invocation_runtime/test_runtime.py`
- `tests/invocation_runtime/test_git_source_control.py`
- `tests/control_plane/test_cli.py`

## 4. Acceptance checks (each names the wrong implementation it catches)

All offline. The fake worker executables come from a test routing file, as in unit 6c-2. Each crash is reproduced by writing the exact store state with the store's own calls (`acquire`, then `commit_with_effect` for the second leak) before `work launch` runs. Owner liveness comes from a test `ProcOwnership` double or the test's own pid.

0. **One launch at a time.**
   - A second `work launch` while the first holds the exclusive reservation answers `LAUNCH_IN_PROGRESS` and writes nothing, even with WIP limit 2 and two eligible work items.
   - A reservation left by an ended launcher is taken over.
   - Two processes taking over the same stale reservation: exactly one wins.
   - Releasing a reservation with no effect while its owner launcher is still alive cannot happen.
   - An owner state of `unknown` answers `LAUNCH_IN_PROGRESS`, and the loser of a takeover race gets `LAUNCH_IN_PROGRESS`.
   - `work launch` while holding the exclusive reservation does not answer `capacity-unavailable`.
   - No registry-profile command except `work launch` calls `_recover`.
   - When `ProcOwnership.current()` gives no owner, `work launch` answers `LAUNCH_OWNER_UNAVAILABLE`, takes no reservation and writes nothing.

   Catches an unenforced rule, a lock that wedges after a crash, and a release of a live launch's reservation.
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
   - in the same recovery pass, another launch's finished, journaled outcome is still recorded, and `_recover` does not return False. That other launch uses a second repository and comes after the parked reservation in `recovery_reservations` order (two reservations cannot share one repository key).

   Catches a wedged profile, an invented outcome and a changed count.
3. **Resolving a parked launch.**
   - `work decide <id> --choice authorize` lifts the effect, starts no worker, and the next `work launch` runs a new correlation.
   - `--choice defer` leaves the launch parked.
   - `cancel` is not offered.
   - `authorize` is refused (`OWNER_STILL_RUNNING`, nothing written) while the owner is alive or owned work is running.
   - After a publish began, `authorize` is accepted only when the remote has no candidate branch and `attest_ownership` answers `effect-unknown`. An absent branch with any other attestation, or a missing PRODUCER worktree, answers `REMOTE_UNVERIFIED` and writes nothing.
   - `remote_revision` returns the revision for an exact ref, returns None for an absent branch (including when only a longer ref with the same prefix exists), raises `CandidateUnavailable` for an unreadable remote, and creates no clone folder and pushes nothing.
   - It answers `CANDIDATE_PUBLISHED` when the branch is at the journaled revision, `REMOTE_CONFLICT` at another revision, and `REMOTE_UNVERIFIED` when the remote cannot be read. Each writes nothing.
   - A work item with no open request gives `NO_OPEN_DECISION`.
   - The same decision twice is a repeat.

   Catches a decision path that bypasses validation, an authorize over a live worker, a decision that launches by itself, and a new attempt after a publication that may have succeeded.
4. **Abandoned PRODUCER worktrees.** After a restart:
   - a recovered PRODUCER result removes its clean worktree;
   - a dirty worktree, one whose journaled owner is alive, or whose owned work (a worker carrying the correlation's marker) is still running after the owner died, or one with no journaled owner, is kept and reported;
   - a recorded `missing-terminal-result` keeps its worktree;
   - nothing outside the workspace root is touched;
   - a parked, unresolved launch keeps its worktree.

   Catches worktrees that are never cleaned, a clean that skips the live-owner check, and removal outside the root.
5. **Restart changes no count, and existing recovery is unchanged.** These existing tests pass unchanged:
   - the check6 and check8 recovery and cycle-count tests;
   - the missing-terminal-result replacement;
   - the read-back of a finished worker.

   Catches a regression in existing recovery.
6. **Fitness.** The changed test files pass when run together in one run (no full suite), and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 5. Excluded

See section 2. Also excluded: changing earlier packets.

## 6. Review record

**Revision 2-3 (2026-10-03).** The REVIEWER's review of `1ad2cb1` (FAIL):
- F1: `work decide` offers only the open request's own choices (`authorize`, `defer`).
- F2: the added refusal applies only to a live owner or running owned work.
- F3: no resume step, so `work decide` never launches.
- F4: one `_finalize_workspace` call added in `_recover`; PRODUCER worktrees only, with the journaled owner's process id; folders go to row 8.
- F5: the concurrent-release risk is stated, with the one-launch-at-a-time rule.
- F6 and F7: `attest_ownership` is called on the composition's own `RealWorkerProvider`; the idempotency key and version come from the open request.
- Revision 4, Founder 2026-10-03:
  - "one launch at a time" is enforced in code (change 0, the store's atomic reservation with owner liveness), not an operating rule;
  - after a publication that may have partly succeeded, `authorize` reconciles the exact candidate against the remote first.
  - Fresh REVIEWER of `9fde64e` (FAIL): `_recover` skips the launcher's own reservation; an `unknown` owner state and a lost takeover race answer `LAUNCH_IN_PROGRESS`; a read-only `remote_revision` method is added, because `read_back_candidate` cannot tell the four remote cases apart; "absent" allows another attempt only with `effect-unknown`; recovery is reachable only through `work launch`.
  - Fresh recheck of `0414092` (FAIL, text): G1-G4 (`remote_revision` raises on an unreadable remote; test 3 matches the rule; tests for `remote_revision` and `LAUNCH_OWNER_UNAVAILABLE`).
- REVIEWER recheck of `2830b28` (FAIL):
  - R1: a do-nothing `resume_after_decision` admission;
  - R2: worktree cleanup gated on `attest_ownership`, because the journaled pid is the coordinator's, not the worker's;
  - R3: the idempotency key is defined;
  - R4: the park reason is optional, and a `missing-terminal-result` keeps its worktree;
  - F10: the CLOSURE clone is named;
  - check 2 ordering and the crash test seam.

**Revision 1 (2026-10-03).** First draft, from the existing row 7 fact sheet (no new discovery), against `main` `893063e`, with the Founder's scope: the two capacity leaks, resolving parked launches and ownership of abandoned worktrees, reusing the existing recovery and cleanup code.
