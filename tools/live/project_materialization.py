#!/usr/bin/env python3
"""Materialize a proposal onto AlienIntent Project #1, and fail closed if it did not land.

Procedure: docs/operations/alienintent-project-board-materialization.md

A returned ProjectV2Item id is not proof of materialization. On 2026-09-23 GitHub returned
valid item ids whose items were individually queryable with the correct project and
`isArchived: false`, yet never joined `ProjectV2.items`; the cards were invisible on the
board while the factory happily executed them. Wave 1 caught this class by reading the
Project back every time. Wave 2 dropped the habit and invisible cards accumulated.

So the read-back is the product here, not a nicety:

    create Issue -> add Project item -> set lifecycle state -> read the Project back
    -> verify exact expected state -> only then declare materialization successful

Usage:
    python3 tools/live/project_materialization.py verify <issue> [--expect-status CAPTURE]
    python3 tools/live/project_materialization.py materialize --title T --body-file F
                                                              [--status CAPTURE]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

REPO = "AlienLogicLab/alienintent"
PROJECT_OWNER = "AlienLogicLab"
PROJECT_NUMBER = 1
PROJECT_ID = "PVT_kwDOEcrpC84Bj5i_"
STATUS_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhisMnY"
PRIORITY_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhiy9vQ"
PRIORITY_OPTIONS = {"P0":"92998478","P1":"ae42b437","P2":"1da6e4a3","P3":"f10b964a","P4":"65e330b9","P5":"c29e1f42"}

# Lifecycle option ids. IMPLEMENT/VERIFY/ACCEPT launch workers; the rest are inert, which
# is not a licence to skip them.
STATUS_OPTIONS = {
    "CAPTURE": "0b45e6a1", "SPECIFY": "cd4f669d", "PLAN": "47939326", "TASKS": "162573f6",
    "READY": "70a61331", "IMPLEMENT": "1d0597c8", "VERIFY": "3d828d3e", "REVIEW": "c632da4e",
    "ACCEPT": "87ca6ed8", "DONE": "70d8419d",
}


class MaterializationFailed(RuntimeError):
    """The Project does not show the state we intended. Never proceed past this."""


def verify_materialization(*, issue: int, expected_status: str, board, issue_side_items) -> None:
    """Raise unless the Project itself shows exactly the intended state for `issue`.

    `board` is what `ProjectV2.items` reports; `issue_side_items` is what the Issue reports
    as its project memberships. The two disagreeing is the whole failure class: the Issue
    side is consistent while the board collection is missing the item.
    """
    failures: list[str] = []
    mine = [item for item in board if item.get("issue") == issue and item.get("type") == "ISSUE"]

    if not mine:
        failures.append(
            f"issue #{issue} is not present in the Project item collection"
            + (f" although the Issue side reports {len(issue_side_items)} membership(s) "
               f"({', '.join(issue_side_items)}) — a returned item id is not proof of "
               "materialization" if issue_side_items else ""))
    elif len(mine) > 1:
        failures.append(f"duplicate Project items for issue #{issue}: "
                        f"{', '.join(str(item.get('id')) for item in mine)}")
    else:
        observed = mine[0].get("status")
        if observed is None:
            failures.append(f"issue #{issue} is on the board with no Status")
        elif str(observed).upper() != expected_status.upper():
            failures.append(f"issue #{issue} has Status {observed!r}, expected "
                            f"{expected_status.upper()!r}")

    foreign = [item for item in board if item.get("type") != "ISSUE"]
    if foreign:
        failures.append("non-Issue items on the board (AlienIntent does not use them): "
                        + ", ".join(f"{item.get('type')} {item.get('id')}" for item in foreign))

    if failures:
        raise MaterializationFailed("MATERIALIZATION FAILED\n  - " + "\n  - ".join(failures))


# --- live GitHub reads -------------------------------------------------------------------

def _gh(*args) -> str:
    done = subprocess.run(["gh", *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise MaterializationFailed(f"gh {' '.join(args[:2])} failed: {done.stderr.strip()[:300]}")
    return done.stdout


def read_board():
    query = ('query($owner:String!,$number:Int!,$cursor:String){organization(login:$owner)'
             '{projectV2(number:$number){items(first:100,after:$cursor){totalCount '
             'pageInfo{hasNextPage endCursor} nodes{id type content{__typename '
             '... on Issue{number repository{nameWithOwner}} '
             '... on PullRequest{number}} '
             'status:fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}} '
             'priority:fieldValueByName(name:"Priority"){... on ProjectV2ItemFieldSingleSelectValue{name}}'
             '}}}}}')
    nodes = []
    expected_total = None
    cursor = None
    seen_cursors = set()
    while True:
        args = ["api", "graphql", "-f", f"query={query}",
                "-F", f"owner={PROJECT_OWNER}", "-F", f"number={PROJECT_NUMBER}"]
        if cursor:
            args += ["-f", f"cursor={cursor}"]
        payload = json.loads(_gh(*args))
        items = payload["data"]["organization"]["projectV2"]["items"]
        page_nodes = items.get("nodes")
        page_total = items.get("totalCount")
        page_info = items.get("pageInfo") or {}
        if not isinstance(page_nodes, list) or not isinstance(page_total, int) or page_total < 0:
            raise MaterializationFailed(
                "MATERIALIZATION FAILED\n  - Project item page is malformed or incomplete")
        if expected_total is None:
            expected_total = page_total
        elif page_total != expected_total:
            raise MaterializationFailed(
                "MATERIALIZATION FAILED\n  - Project item totalCount changed during pagination "
                f"({expected_total} -> {page_total})")
        nodes.extend(page_nodes)
        has_next = page_info.get("hasNextPage")
        if has_next is False:
            break
        next_cursor = page_info.get("endCursor")
        if has_next is not True or not isinstance(next_cursor, str) or not next_cursor:
            raise MaterializationFailed(
                "MATERIALIZATION FAILED\n  - Project item pagination metadata is inconsistent")
        if next_cursor in seen_cursors:
            raise MaterializationFailed(
                "MATERIALIZATION FAILED\n  - Project item pagination cursor repeated")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    return board_from_payload({"totalCount": expected_total, "pageInfo": {"hasNextPage": False},
                               "nodes": nodes})


def board_from_payload(items):
    """Map one Project item connection to board rows, refusing an incomplete answer.

    A fail-closed verifier cannot accept a connection whose own metadata contradicts its
    nodes: `totalCount` disagreeing in either direction, or another page waiting, means the
    board we would verify against was never the whole board.
    """
    nodes = items.get("nodes")
    total = items.get("totalCount")
    has_next = (items.get("pageInfo") or {}).get("hasNextPage")
    if not isinstance(nodes, list) or not isinstance(total, int) or total < 0 or has_next is not False:
        raise MaterializationFailed(
            "MATERIALIZATION FAILED\n  - Project item collection is incomplete or "
            f"inconsistent (totalCount={total!r}, hasNextPage={has_next!r})")
    if total != len(nodes):
        raise MaterializationFailed(
            "MATERIALIZATION FAILED\n  - Project reports "
            f"{total} items but returned {len(nodes)}; verification would be incomplete")
    return [{"id": node["id"], "type": node["type"],
             "issue": (node.get("content") or {}).get("number"),
             "status": (node.get("status") or node.get("fieldValueByName") or {}).get("name"),
             "priority": (node.get("priority") or {}).get("name"),
             "repository": ((node.get("content") or {}).get("repository") or {}).get("nameWithOwner")}
            for node in nodes]


def read_issue_side(issue: int):
    query = ('query($owner:String!,$name:String!,$issue:Int!){repository(owner:$owner,name:$name)'
             '{issue(number:$issue){projectItems(first:20){nodes{id project{number}}}}}}')
    owner, name = REPO.split("/")
    payload = json.loads(_gh("api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}",
                            "-F", f"name={name}", "-F", f"issue={issue}"))
    nodes = payload["data"]["repository"]["issue"]["projectItems"]["nodes"]
    return [node["id"] for node in nodes if (node.get("project") or {}).get("number") == PROJECT_NUMBER]


def requirement_priority(parent_issue: int) -> str:
    rows = [row for row in read_board() if row.get("issue") == parent_issue and row.get("type") == "ISSUE"]
    if len(rows) != 1:
        raise MaterializationFailed(f"parent requirement #{parent_issue} is not uniquely materialized")
    priority = rows[0].get("priority")
    if priority not in PRIORITY_OPTIONS:
        raise MaterializationFailed(f"parent requirement #{parent_issue} has no valid Priority")
    return str(priority)


def issue_database_id(issue: int) -> int:
    owner, name = REPO.split("/")
    value = json.loads(_gh("api", f"repos/{owner}/{name}/issues/{issue}")).get("id")
    if not isinstance(value, int):
        raise MaterializationFailed(f"issue #{issue} has no database id")
    return value


def attach_parent(parent_issue: int, child_issue: int) -> None:
    owner, name = REPO.split("/")
    existing = json.loads(_gh("api", f"repos/{owner}/{name}/issues/{parent_issue}/sub_issues"))
    if any(row.get("number") == child_issue for row in existing):
        return
    _gh("api", "--method", "POST", f"repos/{owner}/{name}/issues/{parent_issue}/sub_issues",
        "-F", f"sub_issue_id={issue_database_id(child_issue)}")


def verify_parent(parent_issue: int, child_issue: int) -> None:
    owner, name = REPO.split("/")
    children = json.loads(_gh("api", f"repos/{owner}/{name}/issues/{parent_issue}/sub_issues"))
    if not any(row.get("number") == child_issue for row in children):
        raise MaterializationFailed(f"issue #{child_issue} is not a sub-issue of parent requirement #{parent_issue}")


def verify_priority(issue: int, expected_priority: str) -> None:
    rows = [row for row in read_board() if row.get("issue") == issue and row.get("type") == "ISSUE"]
    if len(rows) != 1 or rows[0].get("priority") != expected_priority:
        observed = None if len(rows) != 1 else rows[0].get("priority")
        raise MaterializationFailed(f"issue #{issue} has Priority {observed!r}, expected {expected_priority!r}")


def verify(issue: int, expected_status: str) -> None:
    verify_materialization(issue=issue, expected_status=expected_status, board=read_board(),
                           issue_side_items=read_issue_side(issue))
    print(f"MATERIALIZATION VERIFIED: issue #{issue} is on Project #{PROJECT_NUMBER} "
          f"at {expected_status.upper()}, exactly one item, no board pollution")


def materialize(title: str, body_file: str, status: str, parent_issue: int | None = None) -> None:
    if status.upper() not in STATUS_OPTIONS:
        raise MaterializationFailed(f"unknown lifecycle state {status!r}")
    is_biu = re.match(r"^WO-\d+\b", title) is not None
    if is_biu and parent_issue is None:
        raise MaterializationFailed("BIU materialization requires --parent-issue")
    inherited_priority = requirement_priority(parent_issue) if parent_issue is not None else None
    url = _gh("issue", "create", "--repo", REPO, "--title", title, "--body-file", body_file).strip()
    issue = int(url.rstrip("/").rsplit("/", 1)[-1])
    print(f"created {url}")
    item = json.loads(_gh("project", "item-add", str(PROJECT_NUMBER), "--owner", PROJECT_OWNER,
                          "--url", url, "--format", "json"))["id"]
    print(f"added item {item}")
    _gh("project", "item-edit", "--project-id", PROJECT_ID, "--id", item,
        "--field-id", STATUS_FIELD, "--single-select-option-id", STATUS_OPTIONS[status.upper()])
    print(f"set status {status.upper()}")
    if inherited_priority is not None:
        _gh("project", "item-edit", "--project-id", PROJECT_ID, "--id", item,
            "--field-id", PRIORITY_FIELD, "--single-select-option-id", PRIORITY_OPTIONS[inherited_priority])
        attach_parent(parent_issue, issue)
        print(f"inherited {inherited_priority} from parent requirement #{parent_issue}")
    verify(issue, status)
    if inherited_priority is not None:
        verify_priority(issue, inherited_priority)
        verify_parent(parent_issue, issue)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("verify", help="read the Project back and verify one issue")
    check.add_argument("issue", type=int)
    check.add_argument("--expect-status", default="CAPTURE")
    make = sub.add_parser("materialize", help="create, add, set state, then verify")
    make.add_argument("--title", required=True)
    make.add_argument("--body-file", required=True)
    make.add_argument("--status", default="CAPTURE")
    make.add_argument("--parent-issue", type=int)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            verify(args.issue, args.expect_status)
        else:
            materialize(args.title, args.body_file, args.status, args.parent_issue)
    except MaterializationFailed as failure:
        print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
