# Work unit: link a work item to its GitHub Issue and board card, and write its display text

**Status:** Draft for independent review, 2026-10-02 (revision 2). Not approved, not assessed, not released.
**Origin:** row 3 of [the shortest dependency path](python-execution-path-20260930.md). Builds on the landed units [`identity-service-and-compiler-connection.md`](identity-service-and-compiler-connection.md), [`work-registration-and-family-history.md`](work-registration-and-family-history.md) and [`assess-registered-work.md`](assess-registered-work.md) (`main` `39cc1e3`).
**Founder decisions (2026-10-02):** go ahead while the repository is public; this unit creates the Issue and board card when an item has none.
**Setup before real use (Founder):** the factory GitHub App (application `4990774`, installation `162769625`) must grant `issues: write` and `organization_projects: write`. If it does not, `work link` answers `PERMISSION_MISSING` naming them and writes nothing; the Founder then raises the permission on GitHub and accepts it on the installation. No account or credential is changed by this unit. Implementation and checks 1–7 do not depend on it.
**Roles:** one PRODUCER (reviews its own complete change before handing it over); one fresh VERIFIER checks the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

A registered work item has a permanent id and points at its instructions in Git, but nothing ties it to GitHub. This unit adds two commands. `work link <id or label> [--issue <n>]` gives the item exactly one Issue and one card on the configured board: it uses the Issue named, or creates one when the item has none, puts it on the board if it is not there, reads both back, and stores the link on the item; any duplicate Issue an interrupted or losing run created is closed and its card removed. One item has at most one Issue and one Issue at most one item; a second link either way is refused. `work display <id or label>` writes the item's display text — its title and a short body rendered only from the stored record — to the Issue and reads it back; run again it changes nothing, so it is also the repair operation unit 4 will call when the board drifts. The display text points at the instructions; editing it on GitHub never changes them, because the instructions are the Git file at the stored commit.

**Why it matters:** unit 4 must find READY work through these links, not by reading card text; without a link a hand-written item is invisible on the board, and without the uniqueness rule two items could claim one card.

## 1. Inputs, sources and outputs

| Input | Authoritative source |
| --- | --- |
| the item, its label, pointer and state | the `work_item` row through `WorkRecordService.show` |
| the GitHub repository, board and App installation | the project configuration's `github` entry (section 4) |
| an existing Issue (optional) | `--issue <n>` |

Outputs: on GitHub, at most one linked Issue and one board card per item; the Issue's title and body set to the rendered display text; duplicates created by a losing or crashed run closed as not planned and their cards removed (section 5 step 7). In the work database, the item's link: Issue number, Issue node id, card id. Nothing else is written; no board Status is set.

## 2. Display text (domain: `context_assembly/domain/work_link.py`)

Rendered only from the stored row, deterministically:
- **Title:** the item's label.
- **Body:**
  ```
  <!-- alienintent-work-item: <id> -->
  Work item `<label>` (`<id>`)
  Instructions: `<repo>/<path>` at `<commit>`
  This text is a display only. The instructions are that file at that commit.
  ```
  An item with no pointer renders without the `Instructions` line. The `Instructions` line names whichever repository the pointer names; an item whose instructions live in another repository is linked and displayed the same way.

The first line is the marker that lets a rerun find an Issue it created before a crash (section 6).

## 3. Reused, and what is missing

Reused unchanged: `WorkRecordService.show`; `InstallationCredentials` (`authorization`, `granted_permissions`, `application`) and `UrllibGitHubTransport`; the profile-document readers `compose_profile`, `compose_secrets`, `compose_identity` (`composition/sandbox_profile.py`); `GitHubRepositoryApi` and `GitHubProjectsV2Directory` and their existing read paths and error types.

Missing, added here:
- `GitHubRepositoryApi`: `issue(number)`, `create_issue(title, body)` (POST, expects 201), `update_issue(number, title, body)` (PATCH, expects 200), `close_issue(number, body)` (PATCH `state: closed`, `state_reason: not_planned`, expects 200) and `recent_issues(limit)` (`GET /repos/{repo}/issues?state=all&sort=created&direction=desc&per_page=<limit>`), through one small request helper beside the existing `_read` that takes the method and the expected status. Pull requests (entries with `pull_request`) are skipped by `recent_issues` and refused by `issue` (`ISSUE_NOT_FOUND`). Each write is read back with `issue(number)`.
- `GitHubProjectsV2Directory`: `add_issue_item(issue_node_id)` (`addProjectV2ItemById` on the configured Project; GitHub returns the existing card when the Issue is already on the board). The card is read back with the existing `read_status(card_id)`, whose `content_id` must be the Issue's node id.
- The work database: three nullable columns on `work_item` — `issue_number`, `issue_node_id`, `card_id` — added by the adapter at open with plain `ALTER TABLE work_item ADD COLUMN …` when missing (SQLite cannot add a UNIQUE column), then `CREATE UNIQUE INDEX IF NOT EXISTS work_item_issue ON work_item(issue_number)`; and `set_link(id, issue_number, issue_node_id, card_id)` on the repository port, which inside one transaction updates only `WHERE id = ? AND issue_number IS NULL`, returning `ITEM_ALREADY_LINKED` if the item gained a link first, and `ISSUE_ALREADY_LINKED` when the unique index refuses; and `find_by_issue(number)`, a read used only by the duplicate cleanup (section 5 step 7). The three new `WorkItem` fields default to `None`; existing rows keep null links.
- `WorkLink` (application, `context_assembly/application/work_link.py`) with `link(id_or_label, issue=None)` and `display(id_or_label)`, and the CLI commands.

## 4. Configuration

The project configuration entry gains one optional object, read by the existing `project_configuration` (missing → no link service, the CLI answers `github-not-configured`; malformed → `ConfigurationInvalid`):

```
"github": {
  "repository": "AlienLogicLab/alienintent",
  "application_id": 4990774, "installation_id": 162769625,
  "private_key_path": "<the factory App key file named by self-hosting.json githubApp.privateKeyPath>",
  "project": {"project_id": "PVT_…", "project_number": 1, "organization": "AlienLogicLab",
              "status_field_id": "…", "priority_field_id": "…"}
}
```

Composition builds `AppIdentity`, a `ProtectedLocalFileSecretProvider` with the key path, `InstallationCredentials`, `UrllibGitHubTransport`, `ProjectAddress(**project)`, `GitHubRepositoryApi` and `GitHubProjectsV2Directory` directly — the same constructors `SandboxProfileComposition` uses, without its profile document. Before real use the release owner fills `project` with board #1's node id and its Status and Priority field ids, read once with a read-only GraphQL query, and records that the board has both fields.

## 5. Sequences

**`work link <id or label> [--issue <n>]`:**
1. `show`. Unknown → `UNKNOWN_IDENTITY`; retired → `IDENTITY_RETIRED`.
2. Already linked: with no `--issue`, or `--issue` equal to the stored number, read the Issue and card back and return the link (repeat-safe); a different `--issue` → `ITEM_ALREADY_LINKED`, nothing changed.
3. Permissions: `granted_permissions()` must grant `issues: write` and `organization_projects: write`; otherwise `PERMISSION_MISSING` naming them, nothing written.
4. The Issue. With `--issue <n>`: read it (missing or a pull request → `ISSUE_NOT_FOUND`); an Issue already linked to another item is refused by the unique index in step 6. Without: among the repository's 100 newest Issues (`recent_issues(100)`), adopt the newest *open* one created by the App (`user.login` equal to `<app slug>[bot]`, the slug read from `InstallationCredentials.application()`) whose body's first line is this item's marker (any other such open Issue is closed in step 7); if none, `create_issue` with the rendered title and body, and read it back.
5. The card: `add_issue_item(node id)`; read it back with `read_status(card id)`, whose `content_id` must be this Issue's node id.
6. `set_link` (section 3). `ISSUE_ALREADY_LINKED` stops the run with that answer. `ITEM_ALREADY_LINKED` (another run linked the item first) goes to step 7 and then returns that answer.
7. **Cleanup of duplicates (owner: this `link` operation).** Whenever `link` ends with the item linked — including the run that lost in step 6, after re-reading the stored link — every *other open* Issue among the repository's 100 newest that was created by the App, whose first body line is this item's marker and whose body contains no other `alienintent-work-item` marker, is cleaned up in this order: first its card is removed (card id from `add_issue_item`, which returns the existing card, then the existing `delete_item`, read back by `deletedItemId` equal to the card id; a duplicate with no card is briefly given one and removed); then it is closed with `close_issue`, its body ending with the line `Duplicate of #<linked number>; closed by AlienIntent work link.`, read back with `issue(number)`. An interruption between the two leaves an open Issue without a card, which the next run finishes; a closed duplicate is finished and never touched again, so a repeat `link` after cleanup sends no write. Safe checks first: the Issue's number differs from the stored link, `find_by_issue(number)` returns nothing, its creator is the App, its first line is this item's marker and no other marker appears; anything else — including an Issue with conflicting markers — is left untouched. The closed Issue and its body line on GitHub are the durable evidence; the command's answer lists the numbers it closed. A failure leaves the duplicate open and the rerun repeats the cleanup.
8. Display as below.

**`work display <id or label>`:** the item must be linked (else `NOT_LINKED`). Read the Issue; if its title and body already equal the rendered text, return `unchanged`; otherwise `update_issue` and read back; a read-back that differs → `DISPLAY_NOT_CONFIRMED`, naming the field. One write per call; repeated attempts and their limits belong to unit 4.

All refusals are returned as answers, the way `work show` returns `UNKNOWN_IDENTITY`; GitHub transport failures keep the adapters' existing typed errors.

## 6. Repetition, interruption, failure

- **Repeat:** `link` on a linked item reads back and returns the link; `display` with nothing to change writes nothing.
- **Crash after the Issue is created, before the link is stored:** the rerun finds the Issue by the App's login and its marker among the repository's 100 newest Issues and adopts it, so no second Issue is created. Stated bound: if 100 or more other Issues or pull requests were created in between, the earlier one is not found and a second Issue is created; the first then carries the item's marker; any later `link` of the item that finds it among the 100 newest closes it under step 7.
- **Two runs link the same item at once:** both may create an Issue; only one `set_link` succeeds; the losing run then removes its own card and closes its Issue under step 7 before answering `ITEM_ALREADY_LINKED`. If it crashes first, the next `link` of the item closes it.
- **Crash after the card is added:** `addProjectV2ItemById` returns the existing card.
- **GitHub fails or read-back differs:** nothing is stored for that step; the error names the step; a rerun continues from what exists.
- **Display edited on GitHub:** instructions are unaffected; `work display` restores the rendered text. The Issue's edit history on GitHub keeps earlier bodies.

## 7. Temporary resources

None. The installation token is minted and held in memory by the existing `InstallationCredentials`.

## 8. Permissions and prohibited actions

Prohibited: setting board Status or any other field; closing Issues except a duplicate under section 5 step 7; deleting, labelling or assigning Issues; removing cards except a duplicate's; reading or parsing Issue or card text to decide anything except the marker and login match in section 5 step 4 and the display comparison; moving pointers or changing instructions; listing or scanning the whole board or all Issues; a second link store; GitHub writes other than create Issue, update Issue title/body, add a card, and the step-7 close and card removal; `subprocess`, `uuid`, `datetime` or `time` in domain or application code; storing tokens or secrets.

## 9. Exact permitted files

| Production file | Change |
| --- | --- |
| `src/alienintent/context_assembly/domain/work_link.py` (new) | display rendering, marker |
| `src/alienintent/context_assembly/application/work_link.py` (new) | `WorkLink` |
| `src/alienintent/context_assembly/adapters/work_item_repository.py`, `src/alienintent/context_assembly/ports/work_item_repository.py` | link columns and index, `set_link` |
| `src/alienintent/context_assembly/domain/work_identity.py` | the link fields on `WorkItem` |
| `src/alienintent/execution_coordination/adapters/github_repository_api.py`, `src/alienintent/execution_coordination/ports/repository_directory.py` | the four Issue methods |
| `src/alienintent/execution_coordination/adapters/github_projects_v2.py`, `src/alienintent/execution_coordination/ports/project_directory.py` | `add_issue_item` |
| `src/alienintent/composition/work_registry.py` | optional `github` entry and `WorkRegistry.links` |
| `src/alienintent/control_plane/adapters/cli.py`, `src/alienintent/control_plane/application/operator.py` | `work link`, `work display` |

Tests: `tests/context_assembly/test_work_link.py` (new); `tests/execution_coordination/test_github_repository_api.py` (new); `tests/execution_coordination/test_github_projects_v2.py`; `tests/composition/test_sandbox_run_profile.py` (existing repository-API use); `tests/context_assembly/test_work_identity_service.py`, `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`. GitHub is replaced by the recorded-transport fixtures the existing adapter tests use.

## 10. Acceptance checks (each names the wrong implementation it catches)

1. **Create and link.** An unlinked item gets one Issue with the rendered title and body and one card on the configured board; both are read back; the link is stored; a second `link` changes nothing on GitHub or in the database. Catches unchecked writes and duplicate Issues on repeat.
2. **One-to-one.** Linking an item to an Issue already linked to another item, or a linked item to a different Issue, is refused with no link stored and no Issue created; two concurrent `link` runs for two items naming the same Issue end with one link; two concurrent `link` runs for one unlinked item end with one link and the loser answering `ITEM_ALREADY_LINKED`. Catches double claims. The losing run's Issue ends closed as not planned with the duplicate line naming the linked Issue, and its card removed; an Issue with the marker that the App did not create, that is the linked one, that is linked to another item (e.g. via `work link Y --issue n`), or whose body carries a second, conflicting marker is never closed; with a fault after a duplicate's card is removed and before it is closed, the rerun closes it; a repeat `link` after cleanup sends no write to GitHub. Catches duplicates left behind.
3. **Crash recovery.** With a fault after the Issue is created and before the link is stored, the rerun adopts that Issue by its marker and creates none; with a fault after the card is added, the rerun reuses it. Catches duplicates after interruption.
4. **Existing Issue.** `--issue <n>` on an Issue already on the board reuses its card; on one not on the board adds it; a missing Issue or a pull request is `ISSUE_NOT_FOUND`; an Issue with the marker but not created by the App is not adopted. Catches a second card and links to nothing.
5. **Display and repair.** `display` after the Issue body was edited restores the rendered text with one write and reads it back; with nothing changed it writes nothing; a read-back that differs is `DISPLAY_NOT_CONFIRMED`; the item's pointer and Git instructions are unchanged throughout. Catches unconfirmed writes and display edits leaking into instructions.
6. **Permissions and scope.** Missing `issues: write` or `organization_projects: write` → `PERMISSION_MISSING` with no request sent beyond the permission read; a recording transport shows only the permitted requests, no board scan, no Status write. Catches over-broad access.
7. **Wiring.** `work link` / `work display` with and without the `github` entry; an existing database opened by the new code gains the three columns and the index with its rows unchanged; the test files in section 9 and `check_architecture.py --check all` pass.
8. **Real use, before acceptance (the Founder runs, the VERIFIER inspects).** With the setup above, a project configuration whose `github` entry holds the factory App and board #1, and a new work database, this packet registered from `main`, the Founder runs `work link` and then `work display` on it. The VERIFIER checks on GitHub: one new Issue on `AlienLogicLab/alienintent` with the rendered title and body, one card on board #1 for it, the stored link equal to both, a second `work link` and `work display` writing nothing. This is the first Python Issue write with the factory account.

## 11. Excluded

Setting board Status or any field (units 4–5); reading the READY column (unit 4); pagination; closing or labelling Issues; making the repository private (Founder: not now); links for items in other repositories or boards; the MCP or any other transport; the earlier units' follow-ups.

## 12. Review record

**Revision 2d (2026-10-02).** The Founder's advisor required that cleanup exclude Issues with conflicting markers and finish both steps after an interruption. Cleanup removes the card first and closes the Issue second, considering only open duplicates, so an interrupted cleanup is finished by the next run and a finished one is never touched again (a repeat `link` writes nothing); any Issue carrying another marker is skipped.

**Revision 2c (2026-10-02).** The reviewer's check of 2b failed on one gap: nothing could run the "not linked to another item" check. `find_by_issue` is restored for the cleanup step only. Also: removal read back by `deletedItemId`; adoption takes the newest open Issue only; sections 0–1 name the close and card removal.

**Revision 2b (2026-10-02).** The Founder's advisor required an owner for the duplicate Issue a losing or crashed run can leave. Section 5 step 7 makes the `link` operation that owner: it closes such duplicates as not planned with a line naming the linked Issue and removes their cards, after safe checks, with the closed Issue as durable evidence.

**Revision 2 (2026-10-02).** An independent review of `d286846` failed on four blocking findings, fixed: the `github` entry now lists its own fields (the Node `self-hosting.json` cannot be read by `compose_profile`); the permission-table change is removed (that table is the sandbox App's, and `granted_permissions()` is already the inspection); the link columns are plain columns plus a unique index; `set_link` refuses an item that gained a link first. Also: `issue_card` and `find_by_issue` removed (always `addProjectV2ItemById`, read back with `read_status`); pull requests skipped; the marker must come from the App's login; one write helper with expected status; the work-management adapters are extended while the service stays in Work Preparation, which owns `work_item`.

**Revision 1 (2026-10-02).** Own review found the App is deliberately limited to `issues: read`; the table change and the Founder's GitHub permission change are added. First draft, written against `main` `39cc1e3`, after the Founder's two decisions above.
