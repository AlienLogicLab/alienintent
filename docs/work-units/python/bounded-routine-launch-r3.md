# Work unit: bounded routine launch (R3)

**Label:** `BOUNDED-ROUTINE-LAUNCH-R3` (a document label; permanent id `236f54bf-071f-48d8-b735-97c39a2e570b`; parent `034b92ca`,
R2, cancelled as a packet defect: its VERIFIER's regression gate found three regressions outside its targeted set).
**Status:** Revision 6, 2026-10-10. Registered (CAPTURE).
**Authority:** derived from the approved canonical plan revision `28df5c3` (`sha256:415231dcd846671f40bbf24fd6429515592d2d920d4d159d599c9aed9a468dff`), obligation
`BOUNDED-ROUTINE-LAUNCH` (P0); released by the control plane (`work release`), no per-item Founder release.
**Starting revision:** main `8440338`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "236f54bf-071f-48d8-b735-97c39a2e570b",
 "version": "revision-6",
 "intent": "One `work run` starts the factory and keeps advancing READY work through PRODUCER, VERIFIER and CLOSURE to DONE and the next eligible item with no launch per role, reusing the existing `FactoryCoordinator.start()` loop under the existing exclusive launch reservation; retries resume without a human (`--wait` service mode); a crash resumes from durable reservations; routine operation reads open work and one work item's journal records only, never the whole history.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-10 (decisions section 26): do not redesign BOUNDED-ROUTINE-LAUNCH; the existing canonical plan and current `start()` implementation are the design; implement only the missing connection.",
  "Founder 2026-10-10: acceptance requires one `work run` starts the loop; roles advance without manual invocation; retry/backoff resumes without Founder/Claude intervention; crash/restart resumes from durable state; routine execution does not scan total historical Work state/journal.",
  "Founder 2026-10-10: the journal remains canonical; the index is disposable, rebuildable acceleration state; an index crash, omission, corruption or absence must never cause a valid journal record to disappear from reads.",
  "Founder 2026-10-10: the runner advancing into the next Work Item and running its roles is proven here; two sequential items both reaching DONE needs the starting-revision fix assigned to WORK-PREPARATION-REFILL.",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-09 (decisions section 24): plan revision 28df5c3 is the approved authority root recorded by the control plane; this item inherits release from obligation BOUNDED-ROUTINE-LAUNCH.",
  "Founder 2026-10-10 (plan 8440338): the canonical plan at the tip of main is the live authority root; the tip's obligation BOUNDED-ROUTINE-LAUNCH and its paths are unchanged from 28df5c3."
 ],
 "authorized_scope": [
  "src/alienintent/composition/role_binding.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/ports/invocation_journal.py",
  "tests/composition/test_bounded_routine_launch.py",
  "tests/composition/test_role_binding.py",
  "tests/composition/test_worker_launch.py",
  "tests/control_plane/test_cli.py",
  "tests/execution_coordination/k2_fixture.py",
  "tests/execution_coordination/test_role_orchestration.py",
  "tests/invocation_runtime/k1_fixture.py",
  "tests/invocation_runtime/test_invocation_journal_index.py",
  "tests/invocation_runtime/test_real_worker_outcome.py",
  "tests/invocation_runtime/test_workspace_folder.py"
 ],
 "excluded_scope": [
  "release, WIP, eligibility, role and lifecycle semantics",
  "context_assembly/ (the starting revision: WORK-PREPARATION-REFILL)",
  "the READY board read",
  "tools/fitness/",
  "src/alienintent/composition/landing_authority.py"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-3 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/bounded-routine-launch-r3.diff (sha256 da4ef836feaea7401d01477e7e863a9f4d287860da2ebf9b1737dad9b2272808), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a new workflow engine or scheduler",
  "landing two items released together (base-moved; WORK-PREPARATION-REFILL)",
  "detecting a hand-deleted single index file"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "automatic-on",
 "authority_issuer": "plan-authority:sha256:415231dcd846671f40bbf24fd6429515592d2d920d4d159d599c9aed9a468dff",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md obligation:BOUNDED-ROUTINE-LAUNCH",
  "docs/work-units/python/bounded-routine-launch-r3.diff"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "the `design_rules.authority_references` entry with path docs/work-units/python/bounded-routine-launch-r3.diff is absent from the context package, its text's sha256 is not da4ef836feaea7401d01477e7e863a9f4d287860da2ebf9b1737dad9b2272808, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

The pieces that take one work item to DONE already work (VERIFICATION-OUTCOME-INTEGRITY went from release to DONE with
no Founder step), but each role still needs someone to type `work launch`. `FactoryCoordinator.start()` already runs
READY -> PRODUCER -> VERIFIER -> CLOSURE -> DONE -> next with WIP 1 and every retry and hold rule; nothing in the registry
drives it. And the routine path still reads the whole history: every `factory:` row (`_with_started`, `_project_done`)
and the whole invocation journal (16 readers, and twice per append).

## 2. The change: exactly the referenced prototype diff at `8440338`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/bounded-routine-launch-r3.diff`; that entry's
  `text` field holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `da4ef836feaea7401d01477e7e863a9f4d287860da2ebf9b1737dad9b2272808` (89,710 bytes, 18 files, unified diff, `git apply` format).
- **Baseline:** main `8440338`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 18 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `da4ef836feaea7401d01477e7e863a9f4d287860da2ebf9b1737dad9b2272808`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. **`work run [--wait SECONDS]`** (`control_plane/adapters/cli.py`, `control_plane/application/operator.py`):
   `FactoryCoordinator.run(pause)` repeats the existing `start()` until a pass runs no role, inside the existing
   exclusive registry launch reservation (shared with `work launch` through one `_exclusively`) and the card projector.
   A work item a pass could not admit (WIP slot taken) is tried by the next pass; the run stops only when a pass runs
   nothing. Before a pass that retries an item (VERIFIER retry, CLOSURE retry, missing terminal result) it pauses
   `RETRY_PAUSE_SECONDS` (120). `--wait` (`watch_work`) runs again after each idle run and never returns: run as a
   service it picks up retries, decisions and new READY work with no one invoking it; a run that raises (the board
   unreadable, a store or git error) is reported as `error` and waited out, so one transient failure never ends it.
2. **Open work, not history** (`execution_coordination/application/factory_coordinator.py`): `_with_started` finds
   started items by their WIP slot instead of listing every `factory:` row. The all-rows `_project_done` scan is
   removed: a DONE keeps its WIP slot until the registry row is projected (cleanup before DONE settles), recovery
   projects a held DONE, and a permanent refusal (`ProjectionRefused`: every completion answer except
   LANDING_UNVERIFIED, and an unknown work item) settles it with the refusal named in the run output.
3. **The journal stays canonical; a disposable per-work-item index** (`invocation_runtime/adapters/invocation_journal.py`):
   `<journal>.by-work/` (format 2) holds a copy of each record under its `work_identity` and under its `correlation_id`
   (so a record naming this correlation under another work item still reaches the correlation checks) and `covered` (offset, the journal's size,
   modification time and inode, SHA-256 of the last covered line). Every append and work read holds one exclusive lock
   (`<journal>.lock`). A read first copies the lines past `covered`; the index is rebuilt from position 0 whenever it
   cannot prove it still describes the journal; `covered` is removed first on a rebuild; only byte-identical lines are
   read once; an index in another format is rebuilt. Every routine reader (`real_worker.py`, `role_binding.py`,
   `work_registry.py`) reads `records(work=<its work item>, correlation=<its correlation>)` (or the one it has); an
   append reads only the journal's last line.

Release, WIP, eligibility, role and lifecycle semantics are unchanged; explicit-human items still need a human release.

## 3. Acceptance checks

1. **The runner and the bounded reads**: `tests/composition/test_bounded_routine_launch.py` (one run takes the first
   item to DONE and runs every role of the next; pause before a retry; a crash mid-VERIFY resumes on the next run;
   DONE settles only once projected, permanent and transient refusals; 10, 100 and 1,000 recorded and journaled earlier
   work items: no `factory:` listing, none of their rows read, the whole journal never read; no overlap with a live
   launch) and `tests/control_plane/test_cli.py` (`work run`, `work run --wait`).
2. **The journal invariant**: `tests/invocation_runtime/test_invocation_journal_index.py` (old journal with no index;
   a crash after the journal line and before the index; eight kinds of damaged or stale index, each read next and
   after an append, rebuilt from position 0; doubled copy; two records with one sequence; two processes appending at
   once; an index failure after a durable append; an interrupted rebuild; the lock outside the index; a record naming
   this correlation under another work item). Every test file that exercises the journal port or its readers passes
   (the targeted set is part of this item's proof contract, decisions section 28):
   `tests/composition/test_worker_launch.py`, `tests/invocation_runtime/test_real_worker_outcome.py`, `tests/invocation_runtime/test_runtime.py`, `tests/invocation_runtime/test_scripted_worker.py`, `tests/composition/test_role_binding.py`, `tests/execution_coordination/test_role_orchestration.py`, `tests/execution_coordination/test_factory_coordinator.py`, `tests/composition/test_lifecycle_capstone.py`, `tests/invocation_runtime/test_workspace_folder.py`, `tests/composition/test_offline_proof.py`, `tests/composition/test_sandbox_profile.py`, `tests/composition/test_sandbox_run_profile.py`, `tests/context_assembly/test_work_context.py`, `tests/control_plane/test_attention.py`, `tests/execution_coordination/test_containment_wiring.py`, `tests/invocation_runtime/test_no_change_candidate.py`, `tests/invocation_runtime/test_owned_work.py`, `tests/invocation_runtime/test_regression_gate.py`, `tests/invocation_runtime/test_verification_outcome.py`.
3. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-mutations
[
 {
  "name": "the run stops after one pass",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if not summary.ran:\n",
    "new": "            if True:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_run_that_crashed_mid_verify_resumes_from_recorded_state_on_the_next_run",
   "tests/composition/test_bounded_routine_launch.py::test_one_run_takes_the_first_item_to_done_then_runs_the_next_with_no_launch_per_role"
  ]
 },
 {
  "name": "a WIP skip ends the run",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if not summary.ran:\n",
    "new": "            if not summary.ran or summary.stop_reason is StopReason.CAPACITY_UNAVAILABLE:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_run_that_crashed_mid_verify_resumes_from_recorded_state_on_the_next_run",
   "tests/composition/test_bounded_routine_launch.py::test_one_run_takes_the_first_item_to_done_then_runs_the_next_with_no_launch_per_role"
  ]
 },
 {
  "name": "no pause before a retry",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "                pause()\n",
    "new": "                pass\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_one_run_takes_the_first_item_to_done_then_runs_the_next_with_no_launch_per_role"
  ]
 },
 {
  "name": "a started item is not found by its slot",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if item is not None:\n                started.append(item)",
    "new": "            if False:\n                started.append(item)"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_run_that_crashed_mid_verify_resumes_from_recorded_state_on_the_next_run"
  ]
 },
 {
  "name": "a DONE is settled before its projection",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "        if done and self._completed is not None and not projected:\n",
    "new": "        if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_done_is_settled_only_once_its_row_is_projected_and_the_next_run_repairs_it",
   "tests/composition/test_bounded_routine_launch.py::test_a_permanent_projection_refusal_settles_the_done_and_a_transient_one_keeps_its_slot[LANDING_UNVERIFIED-False]"
  ]
 },
 {
  "name": "recovery does not project a held DONE",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "                if self._is_done(reservation.key) and self._completed is not None:\n",
    "new": "                if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_done_is_settled_only_once_its_row_is_projected_and_the_next_run_repairs_it"
  ]
 },
 {
  "name": "a routine reader reads the whole journal",
  "path": "src/alienintent/composition/role_binding.py",
  "edits": [
   {
    "old": "        try:\n            records = self._journal.records(work=invocation.work_identity, correlation=invocation.correlation_id)\n        except JournalUnreadable:\n            return \"durable-outcome-binding-unreadable\"",
    "new": "        try:\n            records = self._journal.records()\n        except JournalUnreadable:\n            return \"durable-outcome-binding-unreadable\""
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_run_reads_open_work_only_whatever_the_history[1000]",
   "tests/composition/test_bounded_routine_launch.py::test_a_run_reads_open_work_only_whatever_the_history[100]",
   "tests/composition/test_bounded_routine_launch.py::test_a_run_reads_open_work_only_whatever_the_history[10]"
  ]
 },
 {
  "name": "a doubled copy is read twice",
  "path": "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "edits": [
   {
    "old": "    records = [json.loads(line) for line in dict.fromkeys(lines)]",
    "new": "    records = [json.loads(line) for line in lines]"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_line_whose_copy_was_lost_or_doubled_by_a_crash_is_read_exactly_once",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_record_naming_this_correlation_under_another_work_item_is_still_read"
  ]
 },
 {
  "name": "the rebuild removes covered last",
  "path": "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "edits": [
   {
    "old": "    (index / \"covered\").unlink(missing_ok=True)\n    for stale in index.glob(\"*.jsonl\"):\n        stale.unlink()",
    "new": "    for stale in index.glob(\"*.jsonl\"):\n        stale.unlink()\n    (index / \"covered\").unlink(missing_ok=True)"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_rebuild_interrupted_after_removing_copies_is_finished_by_the_next_read"
  ]
 },
 {
  "name": "a permanent refusal keeps the slot",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "        except ProjectionRefused as refusal:\n            self.projection_diagnostics[identity] = f\"{identity}: refused: {refusal}\"\n",
    "new": "        except ProjectionRefused as refusal:\n            self.projection_diagnostics[identity] = f\"{identity}: refused: {refusal}\"\n            return\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_done_whose_work_item_is_unknown_is_settled_with_the_refusal_named",
   "tests/composition/test_bounded_routine_launch.py::test_a_permanent_projection_refusal_settles_the_done_and_a_transient_one_keeps_its_slot[NOT_RECORDABLE-True]"
  ]
 },
 {
  "name": "a changed journal is trusted",
  "path": "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "edits": [
   {
    "old": "        if rebuild or state is None or not _describes(journal, seen, state):",
    "new": "        if rebuild or state is None:"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[covered past the end-append then read]",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[covered past the end-read next]",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[replaced-append then read]",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[replaced-read next]"
  ]
 },
 {
  "name": "a read skips the catch-up",
  "path": "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "edits": [
   {
    "old": "    with _locked(path):\n        _sync_index(path)\n        try:\n            lines = [line for key in keys",
    "new": "    with _locked(path):\n        try:\n            lines = [line for key in keys"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_crash_after_the_journal_line_and_before_the_index_loses_nothing",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[index removed-read next]",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[replaced-read next]",
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[rewritten at the same size-read next]"
  ]
 },
 {
  "name": "the append does not sync first",
  "path": "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "edits": [
   {
    "old": "        try:  # first notice any change made since the last sync, before this line moves the journal's size\n            _sync_index(path)\n        except (OSError, ValueError):\n            pass  # the index is caught up by the next read\n",
    "new": ""
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_damaged_or_stale_index_is_rebuilt_from_the_journal_start[rewritten at the same size-append then read]"
  ]
 },
 {
  "name": "a record is not copied under its correlation",
  "path": "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "edits": [
   {
    "old": "            for key in {_key(\"work\", record.get(\"work_identity\")), _key(\"correlation\", record.get(\"correlation_id\"))}:",
    "new": "            for key in {_key(\"work\", record.get(\"work_identity\"))}:"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_invocation_journal_index.py::test_a_record_naming_this_correlation_under_another_work_item_is_still_read"
  ]
 },
 {
  "name": "custody does not read the producer correlation",
  "path": "src/alienintent/composition/role_binding.py",
  "edits": [
   {
    "old": "            records = (*records, *self._journal.records(work=invocation.work_identity, correlation=producer))",
    "new": "            records = records"
   }
  ],
  "tests": [
   "tests/composition/test_role_binding.py::test_a_second_producer_outcome_under_another_work_item_makes_custody_unattributable"
  ]
 },
 {
  "name": "work run outside the launch reservation",
  "path": "src/alienintent/control_plane/application/operator.py",
  "edits": [
   {
    "old": "    return _exclusively(store, ownership, profile, {}, run)",
    "new": "    return run()"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_run_never_overlaps_a_live_launch",
   "tests/control_plane/test_cli.py::test_work_run_renders_the_run_summary_inside_the_card_projector",
   "tests/control_plane/test_cli.py::test_work_run_wait_runs_again_after_each_idle_run_with_no_one_invoking_it"
  ]
 },
 {
  "name": "a failed run ends the service",
  "path": "src/alienintent/control_plane/application/operator.py",
  "edits": [
   {
    "old": "        try:\n            value = exclusive_run_work(launcher, store, ownership, profile, lambda: sleep(RETRY_PAUSE_SECONDS))\n        except Exception as error:  # noqa: BLE001 - the reservation is released; the next run recovers\n            value = {\"error\": type(error).__name__, \"detail\": str(error)}",
    "new": "        value = exclusive_run_work(launcher, store, ownership, profile, lambda: sleep(RETRY_PAUSE_SECONDS))"
   }
  ],
  "tests": [
   "tests/control_plane/test_cli.py::test_work_run_wait_survives_a_failed_run_and_runs_again"
  ]
 },
 {
  "name": "--wait sleeps after a run that ran",
  "path": "src/alienintent/control_plane/application/operator.py",
  "edits": [
   {
    "old": "        if not value.get(\"ran\"):\n            sleep(wait)",
    "new": "        sleep(wait)"
   }
  ],
  "tests": [
   "tests/control_plane/test_cli.py::test_work_run_wait_runs_again_after_each_idle_run_with_no_one_invoking_it"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (can defer)
- Two items released before the first lands: the second's CLOSURE answers base-moved, because a PRODUCER starts from
  its release baseline (`work_context.py`). Fixed by WORK-PREPARATION-REFILL (its allowed paths include
  context_assembly/); this item proves only that the runner runs every role of the next item.
- An item parked at `ready-to-land` while landing is off holds no WIP slot, so `work run` does not resume it
  (`work launch` does). Landing is on in the autonomous operating profile, so this does not occur on the normal path.
- The index trusts that only this module writes the journal and the index. Not detected, because detecting them would
  need a read that grows with history: a single per-work index file deleted by hand while `covered` survives; a
  journal line before `covered` changed in place by a writer that bypasses this module, when that writer also
  appends, or keeps the size within the same modification-time tick. No such writer exists in src.
- The READY snapshot still reads the board's READY column (TERMINAL-BOARD-STATUSES).

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `8440338` (byte copy:
`~/.local/state/alienintent/manual/path-to-done/bounded-routine-launch/prototype-on-8440338.diff`). Built
test-first; the targeted tests of section 3 pass; fitness passes; the 18 mutations of check 3 each fail
their named tests and pass when restored (`mutations.log`). Reviews: fresh adversarial reviews; the first found five
defects (rebuild ordering, reads outside the lock, a WIP slot wedged by a permanent refusal, dedupe by sequence,
unlocked sequence), the second three (a same-size rewrite before an append, the lock inside the disposable index, an
unknown work item wedging WIP), the third one (`--wait` ending on one failed run) and confirmed every earlier fix;
each fixed test-first at its source. R2's regression gate then found three regressions outside R2's targeted set
(a per-work-only index hid a record naming this correlation under another work item; one test fake): fixed by keying
the index by correlation too, and every test file using the journal port is now in the targeted set.
