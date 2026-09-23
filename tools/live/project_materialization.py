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
import subprocess
import sys

REPO = "AlienLogicLab/alienintent"
PROJECT_OWNER = "AlienLogicLab"
PROJECT_NUMBER = 1
PROJECT_ID = "PVT_kwDOEcrpC84Bj5i_"
STATUS_FIELD = "PVTSSF_lADOEcrpC84Bj5i_zhisMnY"

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
    query = ('query($owner:String!,$number:Int!){organization(login:$owner){projectV2(number:$number)'
             '{items(first:100){totalCount nodes{id type content{__typename ... on Issue{number} '
             '... on PullRequest{number}} fieldValueByName(name:"Status")'
             '{... on ProjectV2ItemFieldSingleSelectValue{name}}}}}}}')
    payload = json.loads(_gh("api", "graphql", "-f", f"query={query}",
                            "-F", f"owner={PROJECT_OWNER}", "-F", f"number={PROJECT_NUMBER}"))
    items = payload["data"]["organization"]["projectV2"]["items"]
    if items["totalCount"] > len(items["nodes"]):
        raise MaterializationFailed("Project item collection is larger than one page; "
                                    "verification would be incomplete")
    return [{"id": node["id"], "type": node["type"],
             "issue": (node.get("content") or {}).get("number"),
             "status": (node.get("fieldValueByName") or {}).get("name")}
            for node in items["nodes"]]


def read_issue_side(issue: int):
    query = ('query($owner:String!,$name:String!,$issue:Int!){repository(owner:$owner,name:$name)'
             '{issue(number:$issue){projectItems(first:20){nodes{id project{number}}}}}}')
    owner, name = REPO.split("/")
    payload = json.loads(_gh("api", "graphql", "-f", f"query={query}", "-F", f"owner={owner}",
                            "-F", f"name={name}", "-F", f"issue={issue}"))
    nodes = payload["data"]["repository"]["issue"]["projectItems"]["nodes"]
    return [node["id"] for node in nodes if (node.get("project") or {}).get("number") == PROJECT_NUMBER]


def verify(issue: int, expected_status: str) -> None:
    verify_materialization(issue=issue, expected_status=expected_status, board=read_board(),
                           issue_side_items=read_issue_side(issue))
    print(f"MATERIALIZATION VERIFIED: issue #{issue} is on Project #{PROJECT_NUMBER} "
          f"at {expected_status.upper()}, exactly one item, no board pollution")


def materialize(title: str, body_file: str, status: str) -> None:
    if status.upper() not in STATUS_OPTIONS:
        raise MaterializationFailed(f"unknown lifecycle state {status!r}")
    url = _gh("issue", "create", "--repo", REPO, "--title", title, "--body-file", body_file).strip()
    issue = int(url.rstrip("/").rsplit("/", 1)[-1])
    print(f"created {url}")
    item = json.loads(_gh("project", "item-add", str(PROJECT_NUMBER), "--owner", PROJECT_OWNER,
                          "--url", url, "--format", "json"))["id"]
    print(f"added item {item}")
    _gh("project", "item-edit", "--project-id", PROJECT_ID, "--id", item,
        "--field-id", STATUS_FIELD, "--single-select-option-id", STATUS_OPTIONS[status.upper()])
    print(f"set status {status.upper()}")
    verify(issue, status)


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
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            verify(args.issue, args.expect_status)
        else:
            materialize(args.title, args.body_file, args.status)
    except MaterializationFailed as failure:
        print(failure, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
