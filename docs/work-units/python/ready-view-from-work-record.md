# Work unit: the READY view read from the registered work record, with owned correction

**Label:** `READY-VIEW-FROM-WORK-RECORD` (a document label; the item's permanent id is allocated by the identity service when the packet is registered).
**Status:** Revision 7 draft for independent review, 2026-10-02. Not approved, not assessed, not released. Rewritten against what landed on `main` (`9b03dfd`): the identity service and registration (`work_item` row with a pointer to the packet at an exact commit), the retained assessment (`work assess`, the row's `assessment_ref`), and the GitHub link and display (`work link`, `work display`, the row's `issue_number`, `issue_node_id`, `card_id`). Revisions 1–6 assumed a stored definition object, a `work-association:` store and an identity line in card text; none of those exists, and none is built here.
**Founder decision (2026-10-02):** a hand-written packet carries its execution contract as **one clearly marked structured block inside the packet**, in the existing `BiuContract` format, at the same exact Git commit. Agent Ready assesses the whole file, block included. The READY reader refuses a missing, duplicate or invalid block and never infers a field from prose. Earlier, already assessed packets are not changed.
**Position on the path:** unit 4 of [the shortest dependency path](python-execution-path-20260930.md).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

The factory decides what it may build by reading the READY column of board #1. Today it reads only the first 50 cards, takes each item's identity and contract from the card's text and a branch, and stops the whole import on the first bad card. This unit makes the READY view read the **whole** board, and for every card in the READY column use only the registered work record: the card must be linked to a work item (`work link`), the item's contract is the one marked block inside its packet at the item's exact commit, and the item must have a retained Agent Ready READY assessment of exactly that commit. The card's own text is used for nothing except a display check: if the card's text differs from the item's rendered display, it is repaired with the landed `work display`. Every card that cannot be imported becomes one owned correction task naming why; the other cards still import.

**Why it matters:** an Issue edit must never change what gets built; a missed page must never hide approved work; one bad card must never stall the factory; and a defect must have an owner, not wait for the Founder to notice.

## 1. What is wrong today (verified at `main` `9b03dfd`)

- `GitHubProjectsV2Directory.items(limit=50)` (`execution_coordination/adapters/github_projects_v2.py` line 79; query line 29) reads one page of at most 50 items, with no `pageInfo` or `totalCount`; board #1 has more than 137 items.
- `SandboxBacklogComposition.project_snapshot` (`composition/sandbox_run_profile.py` line 160) builds each row from card text with `descriptor_from_body` (line 80), fetches the contract from a branch (`_contract_for_row`, line 196), and lets a second card overwrite the first (`item_ids[...]`, line 177).
- `GitHubProjectsWorkManagement.import_ready_snapshot` (`execution_coordination/adapters/github_work_management.py` line 49) translates every row in one expression, so one `WorkRejected` stops the whole import.

## 2. The contract block

The packet contains exactly one block, opened by a line that is exactly ```` ```json alienintent-contract ```` and closed by the next line that is exactly ```` ``` ````. Its content is one JSON object in the existing contract payload format, read with `json.loads` and validated by the existing `contract_from_payload` (`context_assembly/domain/compilation.py`). Its `identity` must equal the work item's permanent id. Anything else — no block, two blocks, an unclosed block, invalid JSON, a validator refusal, or a different `identity` — is `CONTRACT_INVALID`, naming which. No other text of the packet is read.

**Authoring order (landed commands only):** commit the packet without the block and `work register` it, which allocates the id; add the block with that id and commit; `work assess --file <packet> --commit <new commit>` moves the item's pointer at `CAPTURE` and assesses the whole file, block included.

## 3. Reused, and what is missing

Reused unchanged: `WorkRecordService.show` (row and packet bytes at the pointer); the row's link fields and `WorkLink.display` with its read-back (the display repair); `work_link`'s display rendering; the assessment store (`consumer.history(id)`) and the packet fingerprint rule (`context_assembly/domain/packet_assessment.py`); `contract_from_payload`; `GitHubProjectsWorkManagement._translate` (per-row rules, unchanged); `AttentionService.ensure` / `resolve` (`control_plane/application/attention.py`) for owned tasks; the release gate, unchanged.

Missing, added here:
- **Complete board read:** `items()` reads pages of 100 with `pageInfo { hasNextPage endCursor }` and `totalCount`, at most 10 pages and 3 attempts per page; it refuses (`ProjectUnavailable`) unless every page reports the same `totalCount`, cursors are non-empty and never repeat, `hasNextPage` is false only on the last page, item ids are unique, and the number read equals `totalCount`. The port's `items` signature drops `limit`.
- **One read on the work database:** `find_by_card(card_id)` on the repository port and adapter.
- **The READY snapshot from the record** in `SandboxBacklogComposition` (section 4), given the work registry by its caller; without one it answers `WorkUnavailable` ("work registry not configured") and never falls back to card text.
- **Per-row import:** `import_ready_snapshot` translates rows one at a time; a `WorkRejected` becomes a `ROW_REFUSED` task and the loop continues.

## 4. Sequence for one snapshot

1. `items()` reads the whole board (section 3), or the snapshot fails with no rows and no tasks.
2. For each card in the READY column, in board order:
   1. `find_by_card(card id)`: none → `NO_LINK` (owner Work Preparation: run `work link`).
   2. The item must not be retired and must have a pointer → else `NOT_ELIGIBLE`.
   3. Assessment: the attempt in `consumer.history(id)` whose `raw_ref` equals the row's `assessment_ref` must have the fingerprint of the row's current pointer and a READY outcome → else `ASSESSMENT_MISSING` (owner Work Preparation: `work assess`).
   4. Contract: the block of section 2 from the packet bytes at the pointer → else `CONTRACT_INVALID` (owner Work Preparation).
   5. Display: the card's title and body must equal the item's rendered display; if not, `WorkLink.display(id)` repairs it once, with read-back; a failed repair is `DISPLAY_DIFFERS` (owner Work Preparation, then Operator after 3 snapshots).
   6. The row: identity = item id; contract and dependencies from the block; `readiness_digest` = the contract's `content_digest`; `readiness_evidence` = the `assessment_ref` logical id; priority and status from the card's fields, as today.
3. `import_ready_snapshot` translates each row with the existing `_translate`; `WorkRejected` → `ROW_REFUSED`.
4. Each failing card gets one `AttentionService.ensure` task keyed `ready-view:<card id>` with its kind and reason (re-raised, never duplicated, attempts counted); tasks for cards no longer failing are resolved. The snapshot returns the imported rows and an in-memory list of the refusals (card id, kind, reason, whether the task was recorded).

Nothing else is written: no Project Status, no Issue text except through `WorkLink.display`.

## 5. Repetition, interruption, failure

No in-flight state: every snapshot is rebuilt from the board and the records. A crash leaves at most tasks already written, which the next snapshot re-raises or resolves. Board unreadable or pagination refused → no rows, no tasks. Work database or assessment store unreadable → the affected cards are refused with that reason and the others continue. Attention store unwritable → the refusal list says `recorded: false`; import continues.

## 6. Permissions and prohibited actions

Prohibited: taking identity, contract, dependencies or readiness from card text or a branch; reading any packet text outside the contract block; a second link, contract or report store; writing Project Status; changing `_translate`'s rules, the release gate or scheduling; changing any earlier packet.

## 7. Exact permitted files

| Production file | Change |
| --- | --- |
| `src/alienintent/execution_coordination/adapters/github_projects_v2.py`, `src/alienintent/execution_coordination/ports/project_directory.py` | complete `items()` |
| `src/alienintent/execution_coordination/adapters/github_work_management.py` | per-row translation with the refusal list |
| `src/alienintent/composition/sandbox_run_profile.py` | the snapshot of section 4; remove the card-text path from the READY import |
| `src/alienintent/context_assembly/adapters/work_item_repository.py`, `src/alienintent/context_assembly/ports/work_item_repository.py` | `find_by_card` |
| `src/alienintent/context_assembly/domain/work_contract.py` (new) | the section 2 block reader |

Tests: `tests/execution_coordination/test_github_projects_v2.py`, `tests/execution_coordination/test_github_work_management.py`, `tests/composition/test_sandbox_run_profile.py`, `tests/context_assembly/test_work_contract.py` (new), `tests/context_assembly/test_work_identity_service.py`. GitHub is the recorded-transport fixture the existing tests use.

## 8. Acceptance checks (each names the wrong implementation it catches)

1. **Complete board.** A board of 237 items over three pages is read whole; each pagination rule broken alone is refused; the page and attempt limits hold. Catches a partial or repeated board.
2. **Record, not card.** A linked, assessed card whose text names a different identity and contract imports the record's identity and contract and has its display repaired once with read-back. Catches any field taken from the card.
3. **Contract block.** Missing, duplicated, unclosed, invalid JSON, refused by the validator, or a different `identity` → `CONTRACT_INVALID` naming which; prose that looks like contract fields outside the block changes nothing. Catches inferred fields.
4. **Assessment of the exact commit.** No assessment, a non-READY outcome, or a READY assessment of an earlier commit → `ASSESSMENT_MISSING`. Catches importing stale or unassessed instructions.
5. **No link, no import.** A READY card with no link → `NO_LINK`; nothing else read for it. Catches trusting cards.
6. **Isolation.** One card of each failing kind plus two valid cards in one snapshot → the two valid rows import and each failure has its own task. Catches one card stalling all.
7. **Owned tasks.** Fifty snapshots with one persistent defect → one open task with its attempts counted; fixed → resolved on the next snapshot; display repair failing three snapshots → owner Operator. Catches task growth and unbounded repair.
8. **Wiring.** No work registry → `WorkUnavailable`, never card text; the test files of section 7 and `check_architecture.py --check all` pass.
9. **Real board, read-only (the VERIFIER).** With the factory board configuration and an isolated work database and attention store, one snapshot of board #1 reads exactly `totalCount` items and lists every READY-column card with its import or its exact refusal kind. No write to GitHub (no display repair is needed for unlinked cards).

## 9. Excluded

Writing board Status; release records and Founder approval (unit 5); worker launch (unit 6); operator status display changes; contract blocks for packets already assessed; proposing corrections (tasks route them, they do not make them).

## 10. Review record

**Revision 7 (2026-10-02).** Rewritten against the landed units and the Founder's decision on the contract block. Revisions 1–6 are superseded.
