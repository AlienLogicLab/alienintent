# Work unit: a routine launch reads no history

**Label:** `BOUNDED-ROUTINE-LAUNCH` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-06, for independent review. Not registered, not approved, not assessed, not released.
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
 "version": "revision-1",
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
  "recovery-only and repair-only readers: they may keep reading the global journal and must be listed in section 2.6"
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
  "acceptance checks 1-8 pass"
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
  "src appends more than one record of the same event for one correlation (invocation-started, publication-started, closure-ordered or invocation-outcome), so a write-once attempt receipt slot cannot hold it",
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
- the CLOSURE order readers (`real_worker.py` line 408; `work_registry.py` lines 508, 699, 1359, 1366 and 1498).

Two store scans also grow with history: `WorkContext._attempt` reads every effect row through `effect_ledger`
(`work_context.py` line 253), and `_project_done` reads every `factory:` row (`factory_coordinator.py` line 712).

## 2. The change

### 2.1 The attempt receipt

The term is always "attempt receipt" in full. "Receipt" alone already names the store's `Receipt` and the closure
action receipts.

- **Port** (`invocation_runtime/ports/attempt_receipts.py`): `AttemptReceipts(Protocol)` with exactly these methods:
  - `write(correlation: str, event: str, record: Mapping[str, object]) -> dict[str, object]`
  - `read(correlation: str, event: str) -> dict[str, object] | None`
  - `lost(phase: str) -> tuple[dict[str, object], ...]`
  - `closure_orders(work_identity: str, revision: str) -> tuple[dict[str, object], ...]`
  - `started_for(work_identity: str) -> tuple[dict[str, object], ...]`
- **The four events:** `event` is one of the four events src appends today: `invocation-started`,
  `publication-started`, `closure-ordered` and `invocation-outcome`. Each event is a write-once slot. The record stored
  is exactly the record the journal append writes today, with no `sequence` or `at` field.
- **File adapter** (`invocation_runtime/adapters/attempt_receipts.py`): `FileAttemptReceipts(root: Path)`.
  - **Slot file:** `root/<sha256(correlation)>/<event>.json`. It is created with `O_CREAT | O_EXCL`, fsynced, its
    folder is fsynced, and it is read back identically before `write` returns.
  - **Writing the same slot again:** with an identical record, `write` returns the stored record. With a different
    record, it raises `AttemptReceiptConflict` and leaves the file unchanged.
  - **Reading:** `read` opens exactly one file and checks that its stored `correlation_id` equals the argument. If it
    does not match, `read` raises `JournalUnreadable`.
  - **Index entries:** each is a write-once file holding only the correlation:
    - for a `missing-terminal-result` outcome: `root/phases/<sha256(phase)>/<sha256(correlation)>`;
    - for a `closure-ordered` record: `root/closures/<sha256(work|revision)>/<sha256(correlation)>`;
    - for an `invocation-started` record: `root/items/<sha256(work)>/<sha256(correlation)>`.
  - **The three index readers:** `lost`, `closure_orders` and `started_for` list one index folder, then read each
    listed correlation's one slot.
  - **Nothing on this path lists or reads `root` itself.**
- **Who writes:** only the deterministic control plane, through the same code that appends to the journal today:
  - `RealWorkerProvider`, at lines 269, 272, 439 and 496;
  - `RoleBindingGuard._retain_missing`, at line 261;
  - `RegistryClosure._order`, at line 1358.

  At each of these points the attempt receipt slot is written first, then the existing journal append. A crash between
  the two leaves the slot present. The next launch of that correlation is then refused as not fresh, which holds the
  item safely.
- **Composition:**
  - `RealWorkerProvider` takes the keyword `receipts: AttemptReceipts | None = None` and exposes it as `.receipts`.
  - When `receipts` is None and the journal has a `path`, the provider uses `FileAttemptReceipts(journal.path.parent / "attempts")`.
  - Every src composition site passes `receipts` explicitly: `work_registry.py`, `github_profile.py`,
    `offline_profile.py`, `sandbox_run_profile.py` and `lifecycle_capstone.py`.
  - For the registry, the root is `launch_root(configuration) / "attempts"`.

### 2.2 RoleBindingGuard reads the attempt receipt, never the journal

The guard keeps its second source: attempt receipts are files written by the provider, never the operational store.
`_bound()` also requires `getattr(self.provider, "receipts", None)` to be present. If it is missing, the refusal is
`durable-outcome-binding-missing`.

| fact | starting revision | after |
|---|---|---|
| freshness | no journal record has the correlation (line 150) | `receipts.read(correlation, "invocation-started") is None` and `receipts.read(correlation, "invocation-outcome") is None` |
| unreadable | `records()` raises `JournalUnreadable` | `read` raises `JournalUnreadable` or `OSError`: same refusal text |
| custody (VERIFIER, CLOSURE) | `correlated_outcome(records, producer invocation, branch)` (line 201) | `correlated_outcome` called on exactly the producer correlation's `invocation-started` and `invocation-outcome` attempt receipts (a list of at most two records); the function itself is unchanged |
| replacements | count of lost outcomes for the phase across the whole journal (line 208) | `len(receipts.lost(phase_of(invocation)))` |
| `_retain_missing` | own records from the journal (line 244) | own four slots; the check "only `invocation-started`" is unchanged |

The `_custody` store reads (`read_state` and `unresolved_effects`) are unchanged.

### 2.3 Every other routine reader

| reader (starting revision) | after |
|---|---|
| `journal_append` sequence (`invocation_journal.py:28`) | `sequence` is the last line's `sequence + 1` (0 for an empty file), read from the file's end only |
| `journal_append` read-back (`:34`) | read back only the bytes just written, from the file's end |
| `RealWorkerProvider.read_back` (`real_worker.py:635`) | `correlated_outcome` on the correlation's own two slots |
| `_closure_orders` (`real_worker.py:408`) | `receipts.closure_orders(work, revision)` |
| `_started_item` (`work_registry.py:486`) | `receipts.read(correlation, "invocation-started")` |
| `_project_completed` (`work_registry.py:508`) | `receipts.closure_orders(work, revision)` |
| LandingAuthority `ordered` (`work_registry.py:699`) | `receipts.read(correlation, "closure-ordered")` |
| `RegistryClosure._order` read-back (`work_registry.py:1359`) | the record returned by `receipts.write` |
| `RegistryClosure` orders for `_settle` (`work_registry.py:1366`) | `receipts.closure_orders(work, revision)` |
| `RegistryClosure._cleanup` (`work_registry.py:1498`) | `receipts.started_for(work)` |
| `WorkContext._attempt` → `effect_ledger` (`work_context.py:253`) | new `OperationalStore.effect(profile, identity) -> Effect \| None`: one `SELECT` by `PRIMARY KEY(profile, identity)` in `SQLiteOperationalStore` |

`WorkRegistry._journal_records` remains for the history readers only (section 2.6).

### 2.4 Outstanding DONE-board obligations

- One aggregate, `board-owed`, in the coordinator's profile. Its state is `{"identities": [sorted work identities]}`,
  and it is read by `read_state`.
- **Adding an entry:** in `FactoryCoordinator._record_result`, when `state.stage` is DONE, the identity is added to
  `board-owed` with a version-checked `commit` *before* the work item's own commit at line 583.
- **Removing an entry:** `_project` (line 697) removes the identity from `board-owed` with a version-checked `commit`
  after `self._completed(identity)` returns. On a `VersionConflict` it keeps the entry, which is retried at the next
  launch.
- **`_project_done`** reads only `board-owed`. For each identity it reads that work item's state:
  - at DONE, it calls `_project`;
  - otherwise, it removes the entry. That happens only after a crash between the add and the DONE commit; when the item
    later reaches DONE, `_record_result` adds it again first.
- `_project_done` never calls `list_states`. The set's size is the number of outstanding obligations, not the number
  of DONE work items.

### 2.5 History is not on the routine path

- **On the routine path:** a launch, its role, its recovery pass when nothing needs recovering, and `_project_done`
  with no outstanding obligation. These never call `journal_records`, `JsonlInvocationJournal.records`,
  `WorkRegistry._journal_records`, `effect_ledger` or `list_states`.
- **Not on the routine path:** the cutover, the proofs, `work show`, and the recovery and repair readers.

### 2.6 History and recovery readers kept

These are the readers that may still read the global journal. The candidate must list each one in its module
docstring, with this exact phrase: "history or recovery reader; never on the routine launch path".
- `real_worker.py` lines 425, 602, 612 and 658, unless the candidate moves them onto attempt receipts;
- `work_registry.py` line 588 (`work decide`);
- `_effect_status` (`factory_coordinator.py` line 731);
- the proof readers in `lifecycle_capstone.py` and `offline_proof.py`.

Moving any of these onto attempt receipts is allowed.

### 2.7 Upgrade condition

At landing, no work item may be in flight, and every DONE work item's card must already be DONE. The CLOSURE of this
work item is the only exception. Attempts recorded before the upgrade have no attempt receipts. They are never read
again on the routine path, because their work items are finished.

## 3. Acceptance checks

1. **Attempt receipts** (`tests/invocation_runtime/test_attempt_receipts.py`):
   - write and read back;
   - an identical second write returns the stored record;
   - a different second write raises `AttemptReceiptConflict` and leaves the bytes unchanged;
   - a slot whose stored `correlation_id` differs raises `JournalUnreadable`;
   - `lost`, `closure_orders` and `started_for` return only their own index entries;
   - a monkeypatched `os.listdir`/`Path.iterdir` records that only the one named index folder is listed.
2. **A routine launch reads no journal record** (`tests/composition/test_bounded_routine_launch.py`, test
   `test_routine_launch_reads_no_journal_record`, using the `closing` fixture of `test_worker_launch.py`).
   - **The armed set** of functions that raise when called:
     - the module global `alienintent.invocation_runtime.adapters.invocation_journal.journal_records`;
     - `JsonlInvocationJournal.records`;
     - `WorkRegistry._journal_records`;
     - the store's `effect_ledger` and `list_states`.
   - **Order:**
     1. Arm, then `fx.launch(item.id)` (PRODUCER); disarm.
     2. Arm, then launch (VERIFIER); disarm.
     3. Arm, then `closing.close(item.id)` (CLOSURE that lands with the five exact receipts); disarm.
   - **Expected result:** each launch succeeds, and the final state is DONE.
   - The journal still receives its appended records, checked after disarming.
   - This test fails at the starting revision.
3. **History growth** (`test_bounded_routine_launch.py`, test `test_launch_cost_is_constant_as_history_grows`,
   parametrized N = 10, 100, 1000). Before the first launch, it seeds:
   - N journal records of all four events for other work identities and correlations;
   - N attempt receipt slots for those correlations;
   - N confirmed effect rows on other aggregates, through `commit_with_effect`, `claim_effect` and `confirm_effect`;
   - N DONE `factory:` rows with an empty `board-owed`.

   Counting wrappers then record, for PRODUCER, VERIFIER and CLOSURE:
   - journal records read (must be 0);
   - attempt receipt files opened and folders listed;
   - store method calls by name.

   The test asserts each count is identical for every N, and that the final state and closure receipts are identical.
4. **Outstanding DONE-board obligations are exact** (`test_factory_coordinator.py`, test
   `test_done_board_obligations_are_bounded`):
   - With 1,000 DONE rows and an empty `board-owed`, `launch` of an unregistered identity calls `completed` zero times.
   - With exactly two identities added to `board-owed` (both DONE), it calls `completed` exactly for those two and
     empties the set.
   - With `completed` raising, the entries stay, and the next launch retries them.
   - An owed identity that is not DONE is removed without calling `completed`.
5. **Guard safety unchanged** (`tests/composition/test_role_binding.py`; every existing test keeps passing). New test
   `test_reused_correlation_is_refused_by_the_attempt_receipt`: an `invocation-started` attempt receipt slot exists
   for a correlation the store has just claimed (a store rewound to an earlier version), and the launch is refused with
   `durable-outcome-binding-not-fresh`. Further guard checks:
   - a producer attempt receipt naming a different candidate is refused with `candidate-custody-unattributable`;
   - two `lost` entries in one phase are refused with `replacement-allowance-exhausted`;
   - a provider with no `receipts` is refused with `durable-outcome-binding-missing`.
6. **Effect lookup** (`test_operational_store.py`): `effect` returns the row for a present identity and None for a
   missing one, and it reads exactly one row (checked through `sqlite3` `set_trace_callback`: one `SELECT` with
   `identity=?`).
7. **Mutations, run exactly by the pre-check and the VERIFIER:**
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
8. **Fitness:** these all pass (no full suite):
   - `python3 -m pytest -q tests/invocation_runtime tests/composition/test_role_binding.py tests/composition/test_worker_launch.py tests/composition/test_bounded_routine_launch.py tests/composition/test_lifecycle_capstone.py tests/composition/test_sandbox_run_profile.py tests/execution_coordination/test_factory_coordinator.py tests/execution_coordination/test_operational_store.py`
   - `tools/fitness/check_architecture.py --root src/alienintent --check all`

## 4. Review record

**Revision 1 (2026-10-06).** First draft. It is based on the full trace of routine-launch journal and history reads,
and on the Founder's three decisions of 2026-10-06.
