# Materializing a proposal onto the AlienIntent GitHub Project

Status: **canonical operations procedure**. Authority: Founder direction 2026-09-23.
Scope: how a Product Issue becomes a visible, tracked card on AlienIntent Project #1.

This procedure existed during Wave 1 and produced a flawless board. It was never written
down, Wave 2 dropped its verification step, and invisible Project cards accumulated
unnoticed. That is why this document exists. **Do not let this process live only in chat
history again.**

## What the process is, in plain English

Creating a GitHub Issue does **not** put work on the board, and putting an item on the
board does **not** prove the board accepted it. Materialization is four steps, and the
fourth is the one that matters: after creating the Issue, adding it to the Project and
setting its lifecycle state, you **read the Project back from GitHub and verify the state
you intended is actually there**. If the read-back does not confirm it, materialization
has failed and the work does not proceed.

A returned Project item ID is **not** proof of materialization. GitHub can return a valid
item ID for an item that never joins the Project's item collection — that is precisely the
fault observed on 2026-09-23, and it is invisible to every step except the read-back.

## Stable identifiers

```bash
PROJECT_NUMBER=1
PROJECT_OWNER=AlienLogicLab
REPO=AlienLogicLab/alienintent
PROJECT_ID=PVT_kwDOEcrpC84Bj5i_
STATUS_FIELD=PVTSSF_lADOEcrpC84Bj5i_zhisMnY
```

Lifecycle option IDs for the `Status` single-select field:

| State | Option ID | Launches a worker? |
|---|---|---|
| `CAPTURE` | `0b45e6a1` | no |
| `SPECIFY` | `cd4f669d` | no |
| `PLAN` | `47939326` | no |
| `TASKS` | `162573f6` | no |
| `READY` | `70a61331` | no |
| `IMPLEMENT` | `1d0597c8` | **yes — PRODUCER** |
| `VERIFY` | `3d828d3e` | **yes — VERIFIER** |
| `REVIEW` | `c632da4e` | no |
| `ACCEPT` | `87ca6ed8` | **yes — PRODUCER (closure)** |
| `DONE` | `70d8419d` | no |

The worker-launching states come from the dispatcher role map
(`src/runtime/dispatcher.mjs`: `{ IMPLEMENT: PRODUCER, VERIFY: VERIFIER, ACCEPT: PRODUCER }`).
Every other state is a control/lifecycle state and is inert to the runtime. **Inert does not
mean skippable**: a proposal still starts at `CAPTURE` and walks the lifecycle honestly.

## The canonical sequence

### Step 1 — create the Product Issue

```bash
URL=$(gh issue create --repo "$REPO" --title "<title>" --body-file <file>)
```

### Step 2 — add it to Project #1

```bash
ITEM=$(gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" \
  --url "$URL" --format json --jq '.id')
```

### Step 3 — set the lifecycle state

Normally `CAPTURE`. Use `SPECIFY` only when the proposal is already sufficiently explicit.
Never jump straight to `READY`, and never skip stages because later ones happen to be
mechanically safe.

```bash
gh project item-edit --project-id "$PROJECT_ID" --id "$ITEM" \
  --field-id "$STATUS_FIELD" --single-select-option-id 0b45e6a1   # CAPTURE
```

### Step 4 — mandatory read-back verification (not optional)

```bash
python3 tools/live/project_materialization.py verify <issue-number> --expect-status CAPTURE
```

The read-back must confirm **all** of:

- the Issue is present in the Project's item collection;
- exactly one Project item exists for it — no duplicate;
- its `Status` is the intended lifecycle state;
- no unexpected non-Issue items are on the board (PRs and drafts do not belong);
- dependency relationships, where applicable, are correct.

If any check fails the tool exits non-zero and prints `MATERIALIZATION FAILED`. **Fail
closed**: do not enter a later lifecycle state, do not release, do not dispatch. An
invisible card must never proceed through factory execution.

The whole sequence, with the gate built in:

```bash
python3 tools/live/project_materialization.py materialize \
  --title "<title>" --body-file <file> --status CAPTURE
```

## Release path

Release is the same Step 3 applied twice, by the Factory Director, on an existing card:

```text
TASKS → READY → IMPLEMENT
```

The Director performs the Project status transition; the Node bootstrap runtime reacts to
the real Project webhook event and launches the worker. **The Director never launches a
worker directly.**

## Known platform fault (observed 2026-09-23)

`addProjectV2ItemById` and `addProjectV2DraftIssue` both return a valid item ID, and the
item is individually queryable with the correct `project { number }` and
`isArchived: false` — yet it never appears in `ProjectV2.items` and `items.totalCount` does
not increase. Reproduced on Project #1 and Project #2, through both the
`organization.projectV2(number:)` and `node(id:)` query paths. Deleting a pre-existing item
works correctly and does decrement `totalCount`.

While that fault persists, Step 4 will correctly report `MATERIALIZATION FAILED` for every
new proposal. That is the gate doing its job, not a defect in this procedure. Materialization
cannot succeed until GitHub restores the add path.

## Why this is enforced mechanically

Per the forward-only rule, a lesson must terminate in mechanical enforcement, deterministic
preflight, or explicit judgment — never in "remember this next time". The Wave 1 read-back
was a coordinator habit, so it was lost with the coordinator. `tools/live/project_materialization.py`
converts it into deterministic behaviour that cannot be forgotten.
