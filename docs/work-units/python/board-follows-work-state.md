# Work unit: the board shows each work item's real state; launch never depends on the card

**Label:** `BOARD-FOLLOWS-WORK-STATE` (a document label; permanent id `PENDING`).
**Status:** Draft revision 1 (at CAPTURE) for independent review, 2026-10-06. Not approved, not assessed, not released.
**Position on the path:** the work item after the first factory DONE (`a41075ab`). Founder 2026-10-05: the GitHub
Project board is a display of AlienIntent's work item state; at every state change the card's Status must match after
read-back, and changing the card must never decide which role runs next.
**Roles:** launched by the factory: PRODUCER, fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING",
 "version": "revision-1",
 "intent": "Make the GitHub Project card show each registry work item's recorded stage (IMPLEMENT, VERIFY, ACCEPT, DONE) from the moment its role starts, retry the card until it matches, and make work launch find a started work item from the work registry rather than from the card staying in READY; READY on the board means only the Founder's release to start.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-05: at every work item state change, the GitHub Project Status matches the work item's state after read-back, and changing the card never decides which role runs next.",
  "Founder 2026-10-05: a failed card update does not change the work item's state; it is recorded and retried until the card matches.",
  "Founder 2026-10-05: no new architecture; a state-machine correction using the existing board write and the existing started-item lookup."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/composition/work_registry.py",
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
  "each acceptance check fails for its named wrong implementation"
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

1. **Find a started work item from the work registry** (`factory_coordinator.py`). In `launch`, for a work item that has
   a coordinator record, the item is the READY row if there is one, else `self._resolve(identity, items,
   projected.record)`, at every stage, not only ACCEPT (the ACCEPT branch's `closure-not-automated` and `ready-to-land`
   answers stay as they are). `guard_account` resolves the same way. A work item with no coordinator record is found only
   in the READY snapshot, as today.
2. **One card-sync step in the registry** (`work_registry.py`): `WorkRegistry.show_stage(identity)`. It reads the
   coordinator record; if the record has a `correlation` and `self._started_item(identity, correlation)` is not None
   (so the journal holds that correlation's `invocation-started`), and the record's `stage` is one of `IMPLEMENT`,
   `VERIFY`, `ACCEPT` or `DONE`, it reads the card's Status (`links.board.read_status(card_id)`); if it differs, it
   writes the stage name (`links.board.write_status(card_id, <stage>, 0)`) and reads it back. Every exception and every
   read-back mismatch is kept in a diagnostics map (like `projection_diagnostics`) and is never raised. Nothing else is
   written.
3. **When it runs:**
   - in `LaunchPreparation.prepare`, right after a successful preparation for the PRODUCER, VERIFIER or CLOSURE (the
     journal already holds `invocation-started`, `real_worker.py` about line 269), so the card shows the role's stage
     while the session runs;
   - after each recorded result: the coordinator takes an optional `stage_shown: Callable[[str], None] | None = None`
     and calls it with the identity after `_record_result` reads back; the registry passes `show_stage`;
   - at the start of every `launch`, for every recorded work item that is not DONE plus the named one, in the same
     place as `_project_done`, so a failed card write is retried on the next launch until the card matches.
4. A release-time hold (a record with no `correlation`) leaves the card in READY, so the next launch still finds the
   work item. CLOSURE's own `board-updated` write of DONE is unchanged.

## 3. Acceptance checks

1. **Full sequence** (`test_worker_launch.py`, with the existing fake board): release (card READY) → PRODUCER prepared
   (card IMPLEMENT) → PRODUCER result (card VERIFY) → VERIFIER prepared (VERIFY) → accept (card ACCEPT) → CLOSURE
   → DONE (card DONE). After each step `read_status` equals the recorded stage. Catches a missing write.
2. **Launch ignores the card** (`test_factory_coordinator.py`): with a work item at VERIFY and at ACCEPT whose card is
   no longer READY, `launch` runs the next role; with the card set back to READY by hand, nothing changes. Catches a
   remaining READY dependency.
3. **Board failure** (`test_worker_launch.py`): a board that raises on `write_status` leaves the coordinator record,
   the outcome and the next role unchanged, records a diagnostic, and the next launch writes the card. Catches a board
   error changing the work item's state, or no retry.
4. **No early move** (`test_worker_launch.py`): a release-time authority-block (no correlation) leaves the card in READY,
   and `launch` after `work decide authorize` still finds the work item. Catches a card moved before the work item can be
   found from the work registry.
5. **Rework** (`test_worker_launch.py`): a VERIFIER rejection moves the card back to IMPLEMENT.
6. **Fitness**: `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py
   tests/composition/test_worker_launch.py tests/composition/test_lifecycle_capstone.py` passes (no full suite), and
   `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Review record

**Revision 1 (2026-10-06).** First draft, from the Founder's decisions of 2026-10-05.
