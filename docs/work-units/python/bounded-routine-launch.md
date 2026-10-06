# Work unit: a routine launch reads no history

**Label:** `BOUNDED-ROUTINE-LAUNCH` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 2, 2026-10-06, for independent review. Not registered, not approved, not assessed, not released.
**Position on the path:** this comes before BOARD-FOLLOWS-WORK-STATE R4 (work item `6140fb56-fe5c-47c1-91c4-5eb7fc626077`,
REVIEW FAILED). Founder 2026-10-06 decided on two work items. This one bounds every routine launch. R4 then builds the
board on top of it and keeps all R3 review fixes.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.
**Trace this packet is based on:** `manual/path-to-done/journal-reads-on-launch-path.md` (main `433b613`).
**Founder decisions:** `manual/path-to-done/founder-decisions-2026-10-06-bounded-launch.md`.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-2",
 "intent": "Make a routine PRODUCER, VERIFIER and CLOSURE launch read a constant amount of current state, whatever the total factory history. Every fact the launch path takes from the invocation journal today comes instead from one immutable attempt receipt, read directly by correlation. The effect ledger scan becomes a primary-key lookup. The all-states DONE repair scan becomes one set of outstanding DONE-board obligations. The global journal stays as append-only history and is never read on the routine path.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: routine PRODUCER, VERIFIER and CLOSURE launch must not reconstruct required operational facts by scanning or replaying historical event or journal records. A direct indexed lookup of one immutable attempt receipt is allowed.",
  "Founder 2026-10-06: the number of journal records read during a routine PRODUCER, VERIFIER or CLOSURE launch is zero, regardless of total historical invocation count.",
  "Founder 2026-10-06: RoleBindingGuard keeps its independent second source. Its full-journal dependency is replaced by a bounded immutable attempt receipt addressed directly by correlation. The canonical store never validates itself, and no other replayable journal is introduced.",
  "Founder 2026-10-06: the attempt receipt is written by the deterministic control plane, never by the worker, and holds only the facts the guard and the launch path need.",
  "Founder 2026-10-06: no general per-attempt journal abstraction.",
  "Founder 2026-10-06: _project_done's all-state scan is replaced by an indexed set of outstanding DONE-board obligations. The set holds only work items that are DONE whose card has not yet been written and read back, and an entry is removed once that succeeds.",
  "Founder 2026-10-06: historical and diagnostic journal access is explicitly separated from routine operational launch access.",
  "Founder 2026-10-06: a history-growth test seeds 10, 100 and 1,000 unrelated records and shows the same bounded operations."
 ],
 "authorized_scope": [
  "src/alienintent/invocation_runtime/ports/attempt_receipts.py",
  "src/alienintent/invocation_runtime/adapters/attempt_receipts.py",
  "src/alienintent/invocation_runtime/adapters/invocation_journal.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/composition/role_binding.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/composition/github_profile.py",
  "src/alienintent/composition/offline_profile.py",
  "src/alienintent/composition/sandbox_run_profile.py",
  "src/alienintent/composition/lifecycle_capstone.py",
  "src/alienintent/execution_coordination/ports/operational_store.py",
  "src/alienintent/execution_coordination/adapters/sqlite_store.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/context_assembly/application/work_context.py",
  "tests/invocation_runtime/test_attempt_receipts.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/test_scripted_worker.py",
  "tests/composition/test_role_binding.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_bounded_routine_launch.py",
  "tests/execution_coordination/test_operational_store.py",
  "tests/execution_coordination/test_factory_coordinator.py"
 ],
 "excluded_scope": [
  "the GitHub Project card writes, the board sweep and every BOARD-FOLLOWS-WORK-STATE change (work item 6140fb56)",
  "the READY view, its refusals and its release meaning",
  "pruning the effects table or the global journal",
  "any change to what RoleBindingGuard refuses or accepts, other than where its facts are read from",
  "the readers listed in section 2.6, which may keep reading the global journal"
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
  "acceptance checks 1-9 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1, M2 and M3 of section 3 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "making item-scoped reads (one work item's own attempts) independent of that item's own attempt count, which the attempt, rework and replacement limits already bound"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/automated-closure.md"
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
  "a named function or line does not exist at the starting revision",
  "src appends more than one invocation-started, publication-started or invocation-outcome record for one correlation, or more than one closure-ordered record for one correlation and order attempt, so a write-once attempt receipt slot cannot hold it",
  "the one-time copy of the global journal into attempt receipts reports a conflict",
  "a routine reader needs a fact that is not in the attempt receipt as defined in section 2.1",
  "RoleBindingGuard would refuse or accept a launch differently from the starting revision for the same facts",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

Today every routine launch reads the whole invocation journal many times: about 9 for PRODUCER, 7 for VERIFIER and 15
for CLOSURE. Each read gets slower as the factory's history grows. The trace names every reader. The largest are:
- `journal_append`, which reads the whole file twice for every append (`invocation_journal.py` lines 28 and 34);
- `RoleBindingGuard.refusal`, which checks freshness, custody and replacements (`role_binding.py` lines 147, 201 and 208);
- `RealWorkerProvider.read_back` (`real_worker.py` line 635);
- the CLOSURE order readers (`real_worker.py` line 408; `work_registry.py` lines 508, 699, 1359, 1366 and 1498);
- the ownership readers that a routine CLOSURE reaches through `_cleanup` → `finalize` → `_finalize_recovered`
  (`real_worker.py` lines 602, 612 and 658).

Three store scans also grow with history:
- `WorkContext._attempt` reads every effect row through `effect_ledger` (`work_context.py` line 253).
- `RoleBindingGuard._custody` reads every unresolved effect (`role_binding.py`, the `unresolved_effects` call).
  A parked effect stays `unknown` until it is authorized, so cancelled items' parked effects pile up there.
- `_project_done` reads every `factory:` row (`factory_coordinator.py` line 712).

## 2. The change

### 2.1 The attempt receipt

The term is always "attempt receipt" in full. "Receipt" alone already names the store's `Receipt` and the closure
action receipts.

- **Port** (`invocation_runtime/ports/attempt_receipts.py`): `AttemptReceipts(Protocol)` with exactly these methods:
  - `write(correlation: str, slot: str, record: Mapping[str, object]) -> dict[str, object]`
  - `read(correlation: str, slot: str) -> dict[str, object] | None`
  - `exists(correlation: str) -> bool`
  - `last_order(correlation: str) -> dict[str, object] | None`
  - `lost(phase: str) -> tuple[dict[str, object], ...]`
  - `closure_orders(work_identity: str, revision: str) -> tuple[dict[str, object], ...]`
  - `started_for(work_identity: str) -> tuple[dict[str, object], ...]`
- **Slots:** a slot is the event name for `invocation-started`, `publication-started` and `invocation-outcome`. For a
  `closure-ordered` record it is `closure-ordered-<order.attempt>` (one CLOSURE correlation orders up to `MAX_ORDERS`
  times, `work_registry.py` lines 1268, 1330 and 1401). Each slot is written once.
- **The record stored** is exactly the journal entry, including its `sequence` and `at`.
  - `journal_append` computes the entry first (section 2.3), writes the slot, then appends the same entry to the
    global journal.
  - Orders are sorted by `(sequence, at, correlation_id, order.attempt)`. This gives `orders[-1]` and
    `reversed(orders)` the same meaning as the journal order today (`work_registry.py` lines 510, 1336, 1373 and 1381).
- **File adapter** (`invocation_runtime/adapters/attempt_receipts.py`): `FileAttemptReceipts(root: Path)`.
  - **Slot file:** `root/<sha256(correlation)>/<slot>.json`. It is created with `O_CREAT | O_EXCL`, fsynced, its
    folder is fsynced, and it is read back identically before `write` returns.
  - **Writing the same slot again:** with an identical record, `write` returns the stored record. With a different
    record, it raises `AttemptReceiptConflict` and leaves the file unchanged.
  - **Reading:** `read` opens exactly one file and checks that its stored `correlation_id` equals the argument. If it
    does not match, `read` raises `JournalUnreadable`.
  - **`exists`** is one `stat` of `root/<sha256(correlation)>`.
  - **`last_order`** lists that one correlation's folder and returns the highest-attempt `closure-ordered-*` slot.
  - **Index entries:** each is a write-once file holding only the correlation and the slot name:
    - for a `missing-terminal-result` outcome: `root/phases/<sha256(phase)>/<sha256(correlation)>`;
    - for a `closure-ordered` slot: `root/closures/<sha256(work|revision)>/<sha256(correlation)>-<attempt>`;
    - for an `invocation-started` slot: `root/items/<sha256(work)>/<sha256(correlation)>`.
  - **The three index readers:** `lost`, `closure_orders` and `started_for` list one index folder, then read each
    listed slot.
  - **Listing:** every folder listing goes through one module function, `_listed(folder: Path)`. Nothing lists or
    reads `root` itself.
- **Who writes:** only the deterministic control plane, through the same code that appends to the journal today:
  - `RealWorkerProvider`, at lines 269, 272, 439 and 496;
  - `RoleBindingGuard._retain_missing`, at line 261;
  - `RegistryClosure._order`, at line 1358.

  The journal port's `append` does both steps: it writes the slot, then the journal line. So every appender keeps its
  one call. `JsonlInvocationJournal` takes the keyword `receipts: AttemptReceipts | None = None`. When it is None, it
  uses `FileAttemptReceipts(path.parent / "attempts")`, and it exposes it as `.receipts`.
- **A crash between the slot write and the journal append** leaves the slot present. `_recover` then reads the outcome
  from the slots (section 2.3), as it reads the journal today, and the correlation is never launched again
  (`factory_coordinator.py` lines 612-680).
- **Composition:**
  - The registry root is `launch_root(configuration) / "attempts"`.
  - Every src composition site gets its attempt receipts from its journal: `work_registry.py`, `github_profile.py`,
    `offline_profile.py`, `sandbox_run_profile.py` and `lifecycle_capstone.py`.
  - `RealWorkerProvider` and `RoleBindingGuard` read `journal.receipts`.

### 2.2 RoleBindingGuard reads the attempt receipt, never the journal

The guard keeps its second source: attempt receipts are files written beside the journal, never the operational
store. If the journal has no `receipts`, the refusal is `durable-outcome-binding-missing`.

| fact | starting revision | after |
|---|---|---|
| freshness | no journal record of any event has the correlation (line 150) | `not receipts.exists(correlation)` (covers all slots) |
| unreadable | `records()` raises `JournalUnreadable` | an attempt receipt read raises `JournalUnreadable` or `OSError`: same refusal text |
| exactly one unresolved effect (`_custody`) | `unresolved_effects(profile)` filtered by identity | `store.effect(profile, correlation)` is present with status `unknown` (the primary key makes it at most one) |
| custody (VERIFIER, CLOSURE) | `correlated_outcome(records, producer invocation, branch)` (line 201) | `correlated_outcome` on the producer correlation's `invocation-started` and `invocation-outcome` slots; the function is unchanged |
| replacements | count of lost outcomes for the phase across the whole journal (line 208) | `len(receipts.lost(phase_of(invocation)))` |
| `_retain_missing` (line 244) | own records except `publication-started` must be exactly `[invocation-started]` | own slots except `publication-started` must be exactly `invocation-started` (a `closure-ordered-*` slot still blocks) |

**One declared change, in `_retain_missing`:** today a failed journal append at line 270 retains nothing. After this
change, once the `missing-terminal-result` slot has been written, the retention counts as done even if the journal line
then fails, and the guard returns `read_back`. The guard's other store reads are unchanged.

### 2.3 Every other routine reader

| reader (starting revision) | after |
|---|---|
| `journal_append` sequence (`invocation_journal.py:28`) | the last line's `sequence + 1` (0 for an empty file), reading the file's end only |
| `journal_append` read-back (`:34`) | read back only the bytes just written, from the file's end |
| `RealWorkerProvider.read_back` (`real_worker.py:635`) | `correlated_outcome` on the correlation's own two slots |
| `_closure_orders` (`real_worker.py:408`) | `receipts.closure_orders(work, revision)` |
| `reconcile_closure` (`real_worker.py:425`) | the correlation's own slots, plus `closure_orders` |
| `_kept_reason`, `_owner_pid`, `attest_ownership` (`real_worker.py:602, 612, 658`) | the correlation's own slots |
| `_started_item` (`work_registry.py:486`) | `receipts.read(correlation, "invocation-started")` |
| `_project_completed` (`work_registry.py:508`) | `receipts.closure_orders(work, revision)` |
| LandingAuthority `ordered` (`work_registry.py:699`) | `receipts.last_order(correlation)` |
| `RegistryClosure._order` read-back (`work_registry.py:1359`) | `receipts.last_order(correlation)` after the append |
| `RegistryClosure` orders for `_settle` (`work_registry.py:1366`) | `receipts.closure_orders(work, revision)` |
| `RegistryClosure._cleanup` (`work_registry.py:1498`) | `receipts.started_for(work)` |
| `WorkContext._attempt` → `effect_ledger` (`work_context.py:253`) | new `OperationalStore.effect(profile, identity) -> Effect \| None`, with its status: one `SELECT` by `PRIMARY KEY(profile, identity)` in `SQLiteOperationalStore` |
| `_effect_status` → `effect_ledger` (`factory_coordinator.py:731`) | `store.effect(profile, correlation)` |

- **`AttemptReceiptConflict`** raised inside `read_back`, `reconcile_closure` or `_retain_missing` answers None (a
  hold). So `_recover` parks the work item and never aborts.
- `WorkRegistry._journal_records` remains for the history readers only (section 2.6).

### 2.4 Outstanding DONE-board obligations

- One aggregate, `board-owed`, in the coordinator's profile. Its state is `{"identities": [sorted work identities]}`,
  and it is read by `read_state`.
- **Adding an entry:**
  - Only when `self._completed is not None`.
  - In `FactoryCoordinator._record_result`, when `state.stage` is DONE, the identity is added with a version-checked
    `commit` *before* the work item's own commit (line 583).
  - On `VersionConflict`, it re-reads and retries, at most 3 times. Adding to a set is idempotent.
  - Any other store error propagates, exactly as a failed commit at line 583 does today.
- **Removing an entry:**
  - `completed(identity)` returning normally is the point where the card has been written and read back. R4 must keep
    that meaning.
  - `_project` (line 697) removes the identity with a version-checked `commit` after `self._completed(identity)`
    returns. On a `VersionConflict` it keeps the entry, which is retried at the next launch.
- **`_project_done`** reads only `board-owed`. For each identity it reads that work item's state:
  - at DONE, it calls `_project`;
  - otherwise, it removes the entry. That happens only after a crash between the add and the DONE commit. `_recover`
    runs before `_project_done` (lines 177-179) and goes through `_record_result` again, which adds the entry again
    first.
- `_project_done` never calls `list_states`. The set's size is the number of outstanding obligations, not the number
  of DONE work items.

### 2.5 History is not on the routine path

- **On the routine path:** a launch, its role (including CLOSURE's `_cleanup` of earlier worktrees), `_recover` when no
  reservation is held, and `_project_done`. These never call `journal_records`, `JsonlInvocationJournal.records`,
  `WorkRegistry._journal_records`, `effect_ledger`, `unresolved_effects` or `list_states`.
- **Not on the routine path:** the cutover, the proofs, `work show` and `work decide`.

### 2.6 History readers kept

These are the readers that may still read the global journal. Each must say so in its own docstring, with the exact
phrase "history reader; never on the routine launch path":
- `work_registry.py` line 588 (`work decide`);
- the proof readers in `lifecycle_capstone.py` and `offline_proof.py`;
- the one-time copy in section 2.7.

### 2.7 Upgrade

- **The copy:** `copy_journal_to_attempt_receipts(journal_path: Path, receipts: AttemptReceipts) -> int` lives in
  `invocation_runtime/adapters/attempt_receipts.py`.
  - It writes every record of the global journal into its slot and index entries, and returns the number written.
  - It is idempotent: identical records are returned as stored.
  - It raises on any `AttemptReceiptConflict`.
  - Only after a complete copy does it write `root/copied.json`, which holds the journal's line count.
- **The launch refuses without the copy:**
  - `WorkRegistry` refuses every launch with `attempt-receipts-not-copied` while `root/copied.json` is absent. This is
    one `stat`.
  - So the old history (lost outcomes, producer custody and old correlations) stays visible to the guard.
- **After this item lands:**
  1. Claude runs the copy once, from a registry script, before any other launch.
  2. Claude checks that this work item's own registry state and card are DONE.
  3. If either is not DONE, Claude adds its identity to `board-owed`. This item's own DONE was recorded by the old code,
     which never adds to the set.

## 3. Acceptance checks

1. **Attempt receipts** (`tests/invocation_runtime/test_attempt_receipts.py`):
   - write and read back;
   - an identical second write returns the stored record;
   - a different second write raises `AttemptReceiptConflict` and leaves the bytes unchanged;
   - a slot whose stored `correlation_id` differs raises `JournalUnreadable`;
   - `lost`, `closure_orders` and `started_for` return only their own index entries;
   - `closure_orders` is sorted by sequence across two correlations, each with attempts 1 and 2;
   - `last_order` returns the highest attempt;
   - with `_listed` wrapped and `os.scandir`, `os.listdir` and `Path.iterdir` patched to count, only the one named
     folder is listed.
2. **A routine launch reads no journal record** (`tests/composition/test_bounded_routine_launch.py`, test
   `test_routine_launch_reads_no_journal_record`).
   - **Set-up:** the `closing` fixture of `test_worker_launch.py`. The item is authorized with `fx.authorized(...,
     **FIXED)`, and the plan carries `ready-to-land:<revision>`, as `test_worker_launch.py` lines 707-712 do.
   - **The armed set**, patched on the classes so a store built per launch is covered (`test_worker_launch.py` lines
     171-172). Each of these raises when called:
     - the module global `alienintent.invocation_runtime.adapters.invocation_journal.journal_records`;
     - `JsonlInvocationJournal.records`;
     - `WorkRegistry._journal_records`;
     - `SQLiteOperationalStore.effect_ledger`, `.list_states` and `.unresolved_effects`.
   - **Order:**
     1. Arm, then `fx.launch(item.id)` (PRODUCER); disarm.
     2. Arm, then launch (VERIFIER); disarm.
     3. Arm, then `closing.close(item.id)` (CLOSURE that lands with the five exact receipts); disarm.
   - **Expected result:** each launch succeeds, and the final state is DONE. The journal still receives its appended
     records, checked after disarming.
   - **A second case** runs the same armed CLOSURE under the moving-main case of `test_worker_launch.py` lines 995-1004
     (two orders in one correlation).
   - Both cases fail at the starting revision.
3. **History growth** (`test_bounded_routine_launch.py`, test `test_launch_cost_is_constant_as_history_grows`,
   parametrized N = 10, 100, 1000). Before the first launch, it seeds:
   - N records of all four events for other work identities and correlations, through `JsonlInvocationJournal.append`
     (which writes their slots and index entries);
   - N confirmed effect rows on other aggregates, through `commit_with_effect`, `claim_effect` and `confirm_effect`;
   - N parked `unknown` effect rows for cancelled work items;
   - N DONE `factory:` rows, with an empty `board-owed`.

   Wrappers then count, for PRODUCER, VERIFIER and CLOSURE:
   - journal records read;
   - attempt receipt files opened and folders listed;
   - for every `SQLiteOperationalStore` read method, its calls **and the total rows it returns**.

   The test asserts:
   - journal records read is 0;
   - `effect_ledger`, `list_states` and `unresolved_effects` are called 0 times;
   - every other count and row total is identical for every N;
   - the final state and closure receipts are identical.
4. **Outstanding DONE-board obligations are exact** (`test_factory_coordinator.py`, test
   `test_done_board_obligations_are_bounded`):
   - With 1,000 DONE rows and an empty `board-owed`, `launch` of an unregistered identity calls `completed` zero times.
   - With exactly two identities added to `board-owed` (both DONE), it calls `completed` exactly for those two and
     empties the set.
   - An owed identity that is not DONE is removed without calling `completed`.
5. **The entry is added** (`test_factory_coordinator.py`, test `test_done_adds_the_board_obligation_first`):
   - A run to DONE with `completed` raising leaves the identity in `board-owed`; the next launch calls `completed` once
     and empties the set.
   - A store whose work item commit at DONE fails once, after the add, leaves the entry; the next launch removes it
     without calling `completed`, then recovery records DONE and adds it again.
   - A coordinator with `completed=None` never writes `board-owed`.
6. **Guard safety unchanged** (`tests/composition/test_role_binding.py`; every existing test keeps passing). New test
   `test_reused_correlation_is_refused_by_the_attempt_receipt`: the launch is refused with
   `durable-outcome-binding-not-fresh` when, for a correlation the store has just claimed (a store rewound to an
   earlier version), any one slot exists. The test is parametrized over all four slot kinds. Further guard checks:
   - a producer attempt receipt naming a different candidate is refused with `candidate-custody-unattributable`;
   - two `lost` entries in one phase are refused with `replacement-allowance-exhausted`;
   - a journal with no `receipts` is refused with `durable-outcome-binding-missing`;
   - a failed journal line after the `missing-terminal-result` slot write still counts as retained (the declared
     change in 2.2).
7. **Effect lookup and upgrade:**
   - In `test_operational_store.py`: `effect` returns the row and status for a present identity and None for a missing
     one, through exactly one `SELECT` with `identity=?` (checked with `sqlite3` `set_trace_callback`).
   - In `test_attempt_receipts.py`:
     - `copy_journal_to_attempt_receipts` copies a journal holding two closure orders in one correlation;
     - running it twice is idempotent;
     - a conflicting slot raises and writes no `copied.json`.
   - In `test_bounded_routine_launch.py`: a launch with no `copied.json` answers `attempt-receipts-not-copied`.
8. **Mutations, run exactly by the pre-check and the VERIFIER:**
   - **M1:** in `src/alienintent/composition/role_binding.py` `refusal`, replace the freshness condition with `False`.
     Then `python3 -m pytest -q tests/composition/test_role_binding.py -k test_reused_correlation_is_refused_by_the_attempt_receipt`
     must FAIL. Revert, and it must pass.
   - **M2:** in `src/alienintent/execution_coordination/application/factory_coordinator.py` `_project_done`, replace
     the `board-owed` read with the starting revision's loop over `self._store.list_states(self._profile, "factory:")`.
     Then `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py -k test_done_board_obligations_are_bounded`
     must FAIL. Revert, and it must pass.
   - **M3:** in `src/alienintent/invocation_runtime/adapters/invocation_journal.py` `journal_append`, compute
     `sequence` as `len(journal_records(path))`. Then `python3 -m pytest -q tests/composition/test_bounded_routine_launch.py -k test_routine_launch_reads_no_journal_record`
     must FAIL. Revert, and it must pass.
   - **M4:** in `_record_result`, remove the `board-owed` add. Then `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py -k test_done_adds_the_board_obligation_first`
     must FAIL. Revert, and it must pass.
9. **Fitness:** these all pass (no full suite):
   - `python3 -m pytest -q tests/invocation_runtime tests/composition/test_role_binding.py tests/composition/test_worker_launch.py tests/composition/test_bounded_routine_launch.py tests/composition/test_lifecycle_capstone.py tests/composition/test_sandbox_run_profile.py tests/execution_coordination/test_factory_coordinator.py tests/execution_coordination/test_operational_store.py`
   - `tools/fitness/check_architecture.py --root src/alienintent --check all`

## 4. Review record

**Revision 2 (2026-10-06).** REVIEWER of `bb47dfd` (FAIL, 13 findings), plus the main session's own pass.
- `closure-ordered` repeats within one correlation, so it is keyed by order attempt.
- Orders are sorted by journal `sequence`.
- The ownership readers that a routine CLOSURE reaches are moved onto slots.
- Freshness covers every slot.
- The `_retain_missing` change is declared.
- `AttemptReceiptConflict` is a hold.
- `_custody`'s `unresolved_effects` scan becomes one effect lookup (own pass: parked effects never leave `unknown`).
- The one-time copy, with a launch refusal until it is done, and this item's own DONE are handled.
- The `board-owed` add has its conflict rule and a check (5, M4).
- Check 3 counts returned rows and forbids the scans.
- Check 2 has its exact set-up and the moving-main case.
- Listing goes through one function.

**Revision 1 (2026-10-06).** First draft. It is based on the full trace of routine-launch journal and history reads,
and on the Founder's three decisions of 2026-10-06.
