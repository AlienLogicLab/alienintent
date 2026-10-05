# Work unit: the board shows each work item's real state; launch never depends on the card

**Label:** `BOARD-FOLLOWS-WORK-STATE-R3` (a document label; permanent id `PENDING`).
**Status:** Draft revision 3 (at CAPTURE) for independent review, 2026-10-06. Not approved, not assessed, not released.
**Position on the path:** the work item after the first factory DONE (`a41075ab`). Founder 2026-10-05: the GitHub
Project board is a display of AlienIntent's work item state; at every state change the card's Status must match after
read-back, and changing the card must never decide which role runs next.
**Roles:** launched by the factory: PRODUCER, fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING",
 "version": "revision-3",
 "intent": "Make the GitHub Project card show each registry work item's recorded stage (IMPLEMENT, VERIFY, ACCEPT, DONE) from the moment its role starts, retry the card until it matches, and make work launch find a started work item from the work registry rather than from the card staying in READY; READY on the board means only the Founder's release to start.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-05: at every work item state change, the GitHub Project Status matches the work item's state after read-back, and changing the card never decides which role runs next.",
  "Founder 2026-10-05: a failed card update does not change the work item's state; it is recorded and retried until the card matches.",
  "Founder 2026-10-05: no new architecture; a state-machine correction using the existing board write and the existing started-item lookup.",
  "Founder 2026-10-06: routine launch and sweep must not parse or replay the full invocation journal; lookup cost is bounded by current work, not total factory history, and the evidence demonstrates that property.",
  "Founder 2026-10-06: the retry proof must be discriminating: with the card write failing and the retry disabled, the retry test fails; restored, it passes; no other hook repairs the card in that test.",
  "Founder 2026-10-06: the pre-check and the independent VERIFIER execute the same discriminating acceptance mutations the packet names."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/execution_coordination/adapters/sqlite_store.py",
  "tests/execution_coordination/test_operational_store.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/composition/test_worker_launch.py"
 ],
 "excluded_scope": [
  "the READY view, its refusals and its release meaning",
  "automatic selection of the next work item, and any change to how many roles one launch runs",
  "retrying a failed work item",
  "the closure actions, the Landing Authority and the work registry row's own state",
  "any new board field, option or Status name"
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
  "acceptance checks 1-6 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1 and M2 of section 3 exactly and records that each makes its named test fail"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "showing outcomes such as failure or authority-block on the card"
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
  "a named function does not exist at the starting revision",
  "_started_item is None for a record whose correlation starts with launch: and the card would need to move",
  "a card write could move a work item to a state where neither the READY view nor started_item can find it",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

Today the card stays in READY until CLOSURE writes DONE (`work_registry.py`, `RegistryClosure._board`), because
`FactoryCoordinator.launch` finds a work item at IMPLEMENT or VERIFY only in the READY snapshot; only at ACCEPT does it
fall back to the work registry (`_resolve`, which uses `started_item`). So the board must show READY while the work item
is in IMPLEMENT, VERIFY or ACCEPT, and moving the card would stop the next role.

## 2. The change

1. **Find a started work item from the work registry** (`factory_coordinator.py`, `launch`). Keep the ACCEPT-only
   early checks (`closure-not-automated`, `ready-to-land`, about lines 166-171) as they are. After
   `self._project_done()` (about line 179), resolve the item from a fresh read:
   `item = next((r for r in items if r.identity == identity), None)`; if that is None and `self.state(identity)` does not raise `KeyError`, `item = self._resolve(identity, items, self.state(identity).record)`
   (the existing `accepted` fallback for ACCEPT stays covered by this). `guard_account` resolves the same way. A work
   item with no coordinator record is found only in the READY snapshot, as today.
2. **Keep the correlation through a decision** (`factory_coordinator.py`, `record_decision`, about line 925):
   `decision_state` also keeps `"correlation": raw["correlation"]` when `raw.get("correlation")` is a `str`, so a work
   item whose card has left READY can still be found after `work decide`.
3. **One card-sync step** (`work_registry.py`): `WorkRegistry.show_stage(identity: str, correlation: str | None = None,
   role: str | None = None)`.
   - The correlation is the given one, else the coordinator record's `correlation` only when it starts with `launch:`
     (a release-time hold records `"release"`, `factory_coordinator.py` about lines 369 and 374). With none, it does
     nothing and records no diagnostic.
   - If `self._started_item(identity, correlation)` is None, it writes nothing and records the diagnostic
     `not-started-item` (for example after a pointer change or retirement).
   - **Bounded started-item lookup.** `_started_item` no longer reads the invocation journal. The coordinator's
     `commit_with_effect` payload (`factory_coordinator.py`, `_run`, about line 413) also holds
     `"contract_digest": item.contract.content_digest`. `SQLiteOperationalStore` gains
     `read_effect(profile: str, identity: str) -> Effect | None`, one indexed `SELECT` by profile and identity.
     `_started_item(identity, correlation)` answers the item only when `read_effect("registry", correlation)` exists, its
     payload's `work` equals the identity and its payload's `contract_digest` equals the registry packet's contract digest
     (otherwise None, as today). An effect written before this change has no `contract_digest` and answers None.
   - The stage written is the given `role`'s stage when `role` is given (from `prepare`) (PRODUCER → `IMPLEMENT`, VERIFIER →
     `VERIFY`, CLOSURE → `ACCEPT`), else the coordinator record's `stage`, only when it is `IMPLEMENT`, `VERIFY`, `ACCEPT`
     or `DONE`. `REVIEW` is never written.
   - `card_id = self.records.show(identity).item.card_id`; with None it does nothing. It reads
     `links.board.read_status(card_id)`; if the status differs it calls `links.board.write_status(card_id, <stage>, 0)` and
     reads back. It never calls `links.display`.
   - Every exception and every read-back mismatch goes into `WorkRegistry.board_diagnostics: dict[str, str]` (created
     in `__init__`), keyed by identity, and is never raised; a later success removes the entry.
4. **Where it runs:**
   - `LaunchPreparation.__init__` takes `stage_shown: Callable[[str, str, str], None] | None = None` (identity,
     correlation, role); both `LaunchPreparation(...)` calls in `_launch_chain` pass
     `stage_shown=lambda identity, correlation, role: self.show_stage(identity, correlation, role)` (the two calls are
     at about lines 644 and 657). In `prepare`, after `self.starting[...] = ...` (about line 1163) and before the
     `return`, call it with `invocation.work_identity`, `invocation.correlation_id` and the role, inside
     `try/except Exception` whose result is ignored; the board transport's own request timeout bounds the delay. The
     journal already holds `invocation-started` at that point (`real_worker.py` about line 269).
   - `FactoryCoordinator.__init__` takes `stage_shown: Callable[[str], None] | None = None`, after `completed`; inside
     `_record_result`, after `if recorded:` (about line 587), it calls `self._stage_shown(item.identity)` inside
     `try/except Exception` that stores the error in `projection_diagnostics[identity]`. `coordinator()` (about line 470)
     passes `stage_shown=self.show_stage`.
   - At the start of every `launch`, next to `_project_done`, one sweep (`WorkRegistry._sweep_stages`) calls
     `show_stage` for the named work item and for every work item that holds a WIP slot
     (`store.recovery_reservations("registry")` with scope `wip`), which is bounded by the WIP limit. The sweep does not
     call `list_states` and reads no journal.
5. A release-time hold (a record whose `correlation` is `"release"`) leaves the card in READY. CLOSURE's own `board-updated` write of
   DONE is unchanged.

## 3. Acceptance checks

Board tests use the existing status-keeping board of the `Closing` fixture in `tests/composition/test_worker_launch.py`
(about line 602).

1. **Full sequence** (`test_worker_launch.py`, `Closing`): release (card READY) → PRODUCER prepared (card IMPLEMENT) →
   PRODUCER result (VERIFY) → VERIFIER prepared (VERIFY) → accept (ACCEPT) → CLOSURE → DONE (DONE). After each step
   `read_status` equals the expected stage. Catches a missing write.
2. **Launch ignores the card** (`test_factory_coordinator.py`): with a `started_item=` stub and a work management whose
   READY snapshot leaves the item out, `launch` runs the VERIFIER for a work item at VERIFY and CLOSURE for one at ACCEPT.
   Catches a remaining READY dependency.
3. **Board failure, and the retry proven by itself** (`test_worker_launch.py`, `Closing`): test
   `test_failed_card_write_is_repaired_only_by_the_launch_sweep`. With the `updateProjectV2ItemFieldValue` branch
   monkeypatched to raise, a role step leaves the coordinator record, the outcome and the next role unchanged and
   records a `board_diagnostics` entry. Then, with the board working again and both other card writes disabled for the
   rest of the test (the coordinator's `stage_shown` hook and `LaunchPreparation`'s `stage_shown` each monkeypatched to
   do nothing), `launch` is called for an identity that runs no role (an unregistered id, answer `not-eligible`). The
   card must now show the work item's stage and the diagnostic must be cleared. Only the launch-time sweep can do that.
4. **No early move, and decisions keep the work item findable** (`test_worker_launch.py`, `Closing`): a release-time
   authority-block (correlation `"release"`) leaves the card in READY and records no diagnostic, and `launch` after `work decide authorize` finds the work
   item; a worker authority-block at IMPLEMENT moves the card to IMPLEMENT, and after `work decide authorize` the next
   `launch` runs the PRODUCER. Catches a stranded work item.
5. **Rework** (`test_worker_launch.py`, `Closing`): a VERIFIER rejection moves the card back to IMPLEMENT.
6b. **Bounded lookup** (`test_worker_launch.py`): test `test_started_items_are_found_without_reading_the_journal`.
   With `JsonlInvocationJournal.records` monkeypatched to raise, a launch at VERIFY and a launch at ACCEPT each still find
   the work item through `_started_item` and run their role, and the sweep runs. And `_started_item` answers None for an
   effect whose `contract_digest` differs or is missing (`test_operational_store.py` covers `read_effect` for a present
   and a missing identity).
6c. **Mutations, run exactly by the pre-check and the VERIFIER**:
   - M1: in `src/alienintent/composition/work_registry.py`, insert `return` as the first statement of `_sweep_stages`;
     `python3 -m pytest -q tests/composition/test_worker_launch.py -k test_failed_card_write_is_repaired_only_by_the_launch_sweep`
     must FAIL; revert, and it must pass.
   - M2: in `_started_item`, replace the `read_effect` lookup with a call to `self._journal_records()` (the old journal
     replay); `python3 -m pytest -q tests/composition/test_worker_launch.py -k test_started_items_are_found_without_reading_the_journal`
     must FAIL; revert, and it must pass.
6. **Fitness**: `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py
   tests/execution_coordination/test_operational_store.py tests/composition/test_worker_launch.py
   tests/composition/test_lifecycle_capstone.py` passes (no full suite), and
   `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Review record

**Revision 3, replacement work item (2026-10-06).** Its predecessor `90187ba7-ce76-44c1-8c5c-9dcba402cf6b` (at `docs/work-units/python/board-follows-work-state-r2.md`) was stopped by the Founder before attempts 2-3 (`cancelled-by-operator`): the packet under-specified the bounded journal requirement (the VERIFIER found the sweep still parses the whole journal per launch), and its retry test still passed with the retry disabled (main-session mutation). This revision states both as exact checks (3, 6b, 6c), bounds the sweep to WIP-slot holders, and replaces the journal read with one indexed effect lookup.

**Revision 2, replacement work item (2026-10-06).** The packet is unchanged. Its predecessor `c6814e01-0099-436c-9c8a-e31124e217c2` (at `docs/work-units/python/board-follows-work-state.md`) ended FAILED after 3 attempts. Its genuine remaining defect, which this packet already rules out in section 2.4: the launch-time sweep must read the journal once, not once per work item. Its other two findings were outside the candidate and are fixed by WORKER-SESSION-IDENTITY (`e0cffbb5`, landed `1e66ab8`): worker sessions now carry `USER` and `LOGNAME` of the worker, and AGENTS.md states the factory's receipt rule. Its outcome is kept as recorded.

**Revision 1c (2026-10-06).** Second REVIEWER of `58708b1` (FAIL): a release-time hold records the correlation
`"release"`, so only a `launch:` correlation counts; `show_stage` takes `role`; the exact `prepare` callable, wrapped
so a board error cannot change the outcome.

**Revision 1b (2026-10-06).** REVIEWER of `32b9fb4` (FAIL): the record has no correlation while a role runs (pass it
from `prepare`); `prepare` reaches the registry through a `stage_shown` callable; `record_decision` keeps the
correlation; fresh record after recovery; exact `_record_result` call site; card id from the work record, not
`display`; REVIEW never written; a bounded sweep; `not-started-item`; the `Closing` fixture in the checks.

**Revision 1 (2026-10-06).** First draft, from the Founder's decisions of 2026-10-05.
