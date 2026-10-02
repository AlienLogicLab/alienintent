# Work unit: the READY view read from the registered work record, with owned correction

**Label:** `READY-VIEW-FROM-WORK-RECORD` (a document label; the item's permanent id is allocated by the identity service when the packet is registered).
**Status:** Revision 8 draft (item `989cb378-a47f-43cd-9056-8775782d1fd8`, at CAPTURE) for independent review, 2026-10-02. Not approved, not assessed, not released. Rewritten against what landed on `main` (`9b03dfd`): the identity service and registration (`work_item` row with a pointer to the packet at an exact commit), the retained assessment (`work assess`, the row's `assessment_ref`), and the GitHub link and display (`work link`, `work display`, the row's `issue_number`, `issue_node_id`, `card_id`). Revisions 1–6 assumed a stored definition object, a `work-association:` store and an identity line in card text; none of those exists, and none is built here.
**Founder decision (2026-10-02):** a hand-written packet carries its execution contract as **one clearly marked structured block inside the packet**, in the existing `BiuContract` format, at the same exact Git commit. Agent Ready assesses the whole file, block included. The READY reader refuses a missing, duplicate or invalid block and never infers a field from prose. Earlier, already assessed packets are not changed.
**Position on the path:** unit 4 of [the shortest dependency path](python-execution-path-20260930.md).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "989cb378-a47f-43cd-9056-8775782d1fd8",
 "version": "revision-8",
 "intent": "The work registry gains a READY view of board #1 that reads the whole board and builds each READY row only from the card's registered work record: linked item, the contract block in its packet at the item's exact commit, and a retained READY assessment of that commit; rows are translated one at a time; every card that cannot be imported, and every card whose display differs from its record, gets one owned task reused across snapshots; display differences are repaired by an explicit operation reusing work display. The sandbox path is unchanged.",
 "satisfied_requirement_ids": [
  "SF-REQ-002",
  "SF-REQ-015"
 ],
 "fixed_decisions": [
  "Founder 2026-10-02: a hand-written packet's contract is one marked block inside the packet, in the existing BiuContract format, at the same commit; the reader refuses missing, duplicate or invalid blocks and never infers fields from prose; its identity equals the registered item's id.",
  "Founder 2026-10-02: priority inheritance from the source requirement is a separate assignment; this unit reads Priority from the card field as today.",
  "Identity, contract, dependencies and readiness come only from the work record; card title and body are read only to compare with the rendered display; the snapshot itself writes nothing to GitHub; display repair is a separate explicit operation reusing work display."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
  "src/alienintent/execution_coordination/adapters/github_work_management.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/adapters/work_item_repository.py",
  "src/alienintent/context_assembly/ports/work_item_repository.py",
  "src/alienintent/context_assembly/domain/work_contract.py",
  "tests/execution_coordination/test_github_projects_v2.py",
  "tests/execution_coordination/test_github_work_management.py",
  "tests/composition/test_work_registry.py",
  "tests/context_assembly/test_work_contract.py",
  "tests/context_assembly/test_work_identity_service.py",
  "tests/support/live_github.py",
  "tests/composition/test_sandbox_profile.py",
  "tests/composition/test_sandbox_run_profile.py"
 ],
 "excluded_scope": [
  "GitHub writes other than work display's Issue title/body update in repair_displays",
  "taking any executable field from card text",
  "writing board Status or fields",
  "changing _translate rules, the release gate, scheduling or row order",
  "changing the sandbox composition",
  "release records and approval",
  "worker launch",
  "changing earlier packets"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "git",
  "sqlite"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-8 pass with fixture GitHub",
  "check 9: one read-only snapshot of board #1 reads totalCount items and reports every READY card",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "read-only real-board snapshot before acceptance"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "real-board snapshot output",
  "landing record on main"
 ],
 "non_goals": [
  "operator status display changes",
  "proposing definition corrections",
  "priority inheritance",
  "contract blocks for already assessed packets"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/python-execution-path-20260930.md row 4",
  "Founder decision 2026-10-02: contract block in every new packet"
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
  "any GitHub write would be needed other than the work display Issue update in repair_displays()",
  "scope outside the authorized files"
 ]
}
```

## 0. The whole design (plain English)

The factory decides what it may build by reading the READY column of a board. Today the only Python reader is the sandbox's: it reads one page of 50 cards of the sandbox board, takes each item's identity and contract from card text and a branch, and stops on the first bad row. This unit adds a READY view to the **work registry**, for board #1 (the board `work link` already writes to), that reads the **whole** board and builds each READY row only from the registered work record: the card must be linked to a work item, the item's contract is the one marked block inside its packet at the item's exact commit, and the item must have a retained Agent Ready READY assessment of exactly that commit. Card text is never used for anything executable: the card's title and body are only compared with the item's rendered display, and a difference becomes a task that an explicit repair operation clears with the existing `work display`. Rows go through the existing translator one at a time, so one bad card never stops the others, and every card that cannot be imported gets one owned task naming why; a rerun reuses the same open task. The sandbox path is not changed.

**Why it matters:** an Issue edit must never change what gets built; a missed page must never hide approved work; one bad card must never stall the factory; a defect must have an owner.

## 1. What is wrong today (verified at `main` `9b03dfd`)

- `GitHubProjectsV2Directory.items(limit=50)` (`execution_coordination/adapters/github_projects_v2.py` line 79; query line 29) reads one page of at most 50 items, with no `pageInfo` or `totalCount`; board #1 has more than 137 items.
- The only READY reader, `SandboxBacklogComposition.project_snapshot` (`composition/sandbox_run_profile.py` line 160), reads the sandbox profile's board from card text (`descriptor_from_body`, line 80) and a branch (`_contract_for_row`, line 196). Nothing reads board #1 from the work registry.
- `GitHubProjectsWorkManagement.import_ready_snapshot` (`execution_coordination/adapters/github_work_management.py` line 49) translates every row in one expression, so one `WorkRejected` stops the whole import.

## 2. The contract block

The packet contains exactly one block, opened by a line that is exactly ```` ```json alienintent-contract ```` and closed by the next line that is exactly ```` ``` ````. Its content is one JSON object, read with `json.loads` and validated by the existing `contract_from_payload` (`context_assembly/domain/compilation.py`). Its `identity` must equal the work item's id. No block, two blocks, an unclosed block, invalid JSON, a validator refusal or a different `identity` is `CONTRACT_INVALID`, naming which. No other packet text is read.

**Authoring order (landed commands):** commit the draft on the packets branch and `work register` it (the id is allocated; registration needs no contract); add the block with that id and commit on the packets branch; `work assess <id> --file <packet> --commit <that commit>` moves the pointer at `CAPTURE` and assesses the whole file.

## 3. Reused, and what is missing

Reused unchanged: `WorkRecordService.show` (row and packet bytes at the pointer); the row's link fields; the assessment store (`consumer.history(id)`) and the packet fingerprint (`context_assembly/domain/packet_assessment.py`); `contract_from_payload`; `GitHubProjectsWorkManagement` and its `_translate` rules (row keys `complete`, `membership`, `repository`, `status`, `identity`, `contract_digest`, `readiness`, `priority`, `dependencies`; contract through its per-row resolver); `AttentionService.ensure` built the way `composition/control_plane_profile.py` builds it; `WorkLink.display` and `work_link`'s display rendering (the display repair of unit 3).

Missing, added here:
- **Complete board read:** `GitHubProjectsV2Directory.items()` reads pages of 100 with `pageInfo { hasNextPage endCursor }` and `totalCount`, at most 10 pages; it raises `ProjectUnavailable` unless every page reports the same `totalCount`, cursors are non-empty and never repeat, `hasNextPage` is false only on the last page, item ids are unique, and the number read equals `totalCount`. The port already takes no `limit`. The sandbox's reader gets the complete board too; its behaviour is otherwise unchanged.
- **Card lookup:** `find_by_card(card_id)` on the work repository port and adapter, with `CREATE UNIQUE INDEX IF NOT EXISTS work_item_card ON work_item(card_id)` at open, so one card names at most one item.
- **Per-row translation:** `import_ready_snapshot` translates rows one at a time; each `WorkRejected` is kept in `last_refusals` (card id, reason) and the loop continues.
- **The registry READY view** (`composition/work_registry.py`, when both the `github` and the `readiness` entries are present; its attention items are kept in the `readiness` entry's existing operational store and evidence folder, so no new configuration entry): `WorkRegistry.ready_view`, a `GitHubProjectsWorkManagement` for board #1 with profile `"registry"`, repository from the `github` entry, a status mapping of each formal workflow state name to itself, no projection fields and no projection writes, the snapshot of section 4 and a contract resolver returning the contract that snapshot read for that row. Each row carries its `card` id. `WorkRegistry.ready_refusals()`, called after `import_ready_snapshot()`, collects the snapshot's refusals and the translator's `last_refusals`, ensures their attention items (step 4), and returns them. `WorkRegistry.repair_displays()` calls the existing `WorkLink.display(id)` once for each item the last snapshot found with `DISPLAY_DIFFERS`, with its read-back, and returns each result; it is never called by the snapshot or by `import_ready_snapshot`.

## 4. Sequence for one snapshot

1. `items()` reads the whole board (section 3), or the snapshot fails with no rows and no tasks.
2. The cards in the READY column, ordered exactly as the sandbox reader orders them today (READY-entry time, then item id). For each:
   1. `find_by_card(card id)`: none → `NO_LINK` (owner Work Preparation: `work link`).
   2. The item must not be retired and must have a pointer → else `NOT_ELIGIBLE` (owner Work Preparation).
   3. Assessment: the entry in `consumer.history(id)` whose `raw_ref` equals the row's `assessment_ref` must have the fingerprint of the row's current pointer and a READY outcome → else `ASSESSMENT_MISSING` (owner Work Preparation: `work assess`).
   4. Contract: the block of section 2 from the packet bytes at the pointer → else `CONTRACT_INVALID` (owner Work Preparation).
   5. Display: the card's title and body are compared with the item's rendered display; a difference is recorded as `DISPLAY_DIFFERS` (owner Work Preparation: `repair_displays()` / `work display`) and the row is still built, since nothing in it comes from the card text.
   6. The row: `complete` and `membership` true, `repository` from the `github` entry, `status` and `priority` from the card's board fields as today, `identity` = item id, `contract_digest` = the contract's `content_digest`, `readiness` = the `assessment_ref` logical id, `dependencies` = the contract's `dependencies`, `card` = the card id.
3. `import_ready_snapshot` translates each row; a refusal (for example a missing or unsupported Priority) is `ROW_REFUSED` (owner Operator).
4. For each refusal and each `DISPLAY_DIFFERS`, `AttentionService.ensure` one `JUDGMENT` item whose origin is the same on every snapshot: `work_ref` = card id, `event_identity` = the kind, `work_revision` = `"ready-view"`, `lane` = `"ready-view"`, `required_authority` = the owner, `producer` = `"ready-view"`, `source_ref` = an evidence record whose every field is fixed — the content `{kind, card id}` and constant revision, definition, observer and invocation values, never a process id, time or reason — so the content-addressed repository returns the same `Ref` in every process. A rerun, in this or any later process, therefore finds the same open item instead of creating another; the current reason is reported in `ready_refusals()`, not in the item. This unit sets up no resolvers and resolves nothing: items stay open, a defect that returns finds its open item, and `ready_refusals()` lists open items whose defect is no longer observed as `cleared`. Resolution by the owner is later work.

The snapshot writes nothing to GitHub. Only `repair_displays()` writes, and only the Issue title and body through `work display`; never Status or fields.

**Release gate note:** for these rows `contract_digest` is the record's own contract digest, so the release gate's readiness-digest comparison is always equal; the binding of readiness to the exact instructions is step 2.3. Release records keyed by older labels do not match item ids; release from the registry view is unit 5's work.

## 5. Repetition, interruption, failure

No in-flight state: every snapshot is rebuilt from the board and the records. A crash leaves at most attention items already written, which the next snapshot finds again. Board unreadable or pagination refused → no rows, no items. Work database or assessment store unreadable → the affected cards are refused with that reason and the others continue. Attention store unwritable → `ready_refusals()` marks those refusals `recorded: false`; import continues.

## 6. Permissions and prohibited actions

Prohibited: any GitHub write except `repair_displays()` through `work display`; using card text for anything but the display comparison; taking identity, contract, dependencies or readiness from anywhere but the record and the contract block; reading packet text outside the block; writing board Status or fields; changing `_translate`'s rules, the release gate, scheduling or row order; changing the sandbox composition; a second link, contract or report store; changing any earlier packet.

## 7. Exact permitted files

The contract block's `authorized_scope` is the exact list. Production: `execution_coordination/adapters/github_projects_v2.py` (complete `items()`), `execution_coordination/adapters/github_work_management.py` (per-row translation, `last_refusals`), `composition/work_registry.py` (the READY view), `context_assembly/adapters/work_item_repository.py` and `context_assembly/ports/work_item_repository.py` (`find_by_card`, index), `context_assembly/domain/work_contract.py` (new; the block reader). Tests: the files in the block, including `tests/support/live_github.py` (the recorded fixture matches the query text) and the sandbox tests that use it, which change only to follow the new query.

## 8. Acceptance checks (each names the wrong implementation it catches)

1. **Complete board.** A board of 237 items over three pages is read whole; each pagination rule broken alone is refused; the page limit holds. Catches a partial or repeated board.
2. **Record, not card; display repaired separately.** A linked, assessed card whose body names a different identity and contract imports the record's identity, contract and dependencies, and records `DISPLAY_DIFFERS` with no GitHub request during the snapshot; `repair_displays()` then restores the card through `work display` with read-back, and the next snapshot records no difference. Catches any field taken from the card, a write inside the read, and a missing repair.
3. **Contract block.** Missing, duplicated, unclosed, invalid JSON, refused by the validator, or a different `identity` → `CONTRACT_INVALID` naming which; contract-like prose outside the block changes nothing. Catches inferred fields.
4. **Assessment of the exact commit.** No assessment, a non-READY outcome, or a READY assessment of an earlier commit → `ASSESSMENT_MISSING`. Catches importing stale or unassessed instructions.
5. **No link, no import.** A READY card with no link → `NO_LINK`. Catches trusting cards.
6. **Isolation and priority.** One card of each failing kind, one with no Priority, plus two valid cards → the two valid rows import in today's order and each failure has its own refusal and item; the missing Priority is `ROW_REFUSED` owned by the Operator. Catches one card stalling all and changed order.
7. **One open task per card and kind.** Fifty snapshots with one persistent refusal, taken by two separate registry instances (as two processes would) and with the reason text changing between them → one attention item, reused; a second kind for the same card → a second item; the defect removed → the item stays open and is listed `cleared`. Catches task accumulation and per-process origins.
8. **No regression.** The sandbox reader's existing ordering and status-write tests, and every test that uses `tests/support/live_github.py`, pass with the complete `items()`; the test files in the block and `check_architecture.py --check all` pass.
9. **Real board #1, read-only (the VERIFIER).** With a copy of the permanent registry's configuration pointing at a copy of `work.sqlite` and copies of its readiness database and evidence folder, one `WorkRegistry.ready_view.import_ready_snapshot()` and `ready_refusals()` against board #1 read exactly `totalCount` items and list every READY-column card with its import or its refusal kind, including any `DISPLAY_DIFFERS` on a linked card (which would show a difference between the board's and the Issue's text). No GitHub write.

## 9. Excluded

Any GitHub write other than `repair_displays()`; priority inheritance (first-ten slot 2); release records and approval (unit 5); worker launch (unit 6); operator status display; changing the sandbox composition; contract blocks for packets already assessed.

## 10. Review record

**Revision 8c (2026-10-02).** The reviewer's recheck of 8b (FAIL, text only): the stop condition allows `repair_displays()`; rows carry `card` and `ready_refusals()` creates the items after translation; attention items use the `readiness` store; every evidence field is fixed so all processes reuse one item; no resolvers are set up and cleared defects are listed, not resolved.

**Revision 8b (2026-10-02).** The Founder's advisor: changing the composition does not justify dropping display repair or correction ownership. The snapshot now detects display differences (comparison only, no write) and records them as owned tasks; `repair_displays()` repairs them with the existing `work display`, separately from the read. Task origins are fixed per card and kind so reruns reuse the same open task.

**Revision 8 (2026-10-02).** An independent review of revision 7 failed (two blocking, five high): the attention store cannot carry the specified keys, attempts or automatic resolution; display repair wrote to GitHub inside a read; the snapshot read the sandbox board, not board #1; "board order" changed scheduling; the row shape was unstated; refusals had no path to tasks; removing the card-text path broke files outside scope. The view now lives in the work registry for board #1, reads no card text and writes nothing to GitHub, keeps today's order, states the row keys, keeps refusals in the adapter, records one judgment item per card and kind, and leaves the sandbox path unchanged.

**Revision 7 (2026-10-02).** Rewritten against the landed units and the Founder's decision on the contract block. Revisions 1–6 are superseded.
