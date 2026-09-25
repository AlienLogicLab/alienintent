"""Tests for mandatory Project read-back verification.

The failure class these exist for, observed live on 2026-09-23: GitHub returns a valid
ProjectV2Item id from `addProjectV2ItemById`, the item is individually queryable with the
correct project and `isArchived: false`, and yet it never joins `ProjectV2.items`. Every
step except a read-back reports success, so an invisible card walks into factory execution.

Wave 1 performed this read-back by coordinator habit and the board was flawless. Wave 2
dropped it. The rule therefore has to be mechanical, not remembered.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import project_materialization  # noqa: E402
from project_materialization import (MaterializationFailed, board_from_payload, read_board,  # noqa: E402
                                     verify_materialization)

ITEM = "PVTI_good"


def _board(status="CAPTURE", issue=90, item_id=ITEM, item_type="ISSUE"):
    """One healthy board item for `issue`, as the Project collection reports it."""
    return [{"id": item_id, "type": item_type, "issue": issue, "status": status}]


def test_a_materialized_issue_with_the_intended_status_verifies():
    verify_materialization(issue=90, expected_status="CAPTURE", board=_board(),
                           issue_side_items=[ITEM])


def test_an_item_id_that_never_joined_the_collection_fails_closed():
    """The exact 2026-09-23 fault: the add returned this id, the Issue side confirms the
    membership, and the Project collection does not contain it."""
    with pytest.raises(MaterializationFailed) as failure:
        verify_materialization(issue=90, expected_status="CAPTURE", board=[],
                               issue_side_items=[ITEM])
    assert "not present" in str(failure.value).lower()


def test_a_duplicate_project_item_for_one_issue_fails_closed():
    board = _board() + [{"id": "PVTI_dupe", "type": "ISSUE", "issue": 90, "status": "CAPTURE"}]
    with pytest.raises(MaterializationFailed) as failure:
        verify_materialization(issue=90, expected_status="CAPTURE", board=board,
                               issue_side_items=[ITEM, "PVTI_dupe"])
    assert "duplicate" in str(failure.value).lower()


def test_the_wrong_lifecycle_status_fails_closed():
    with pytest.raises(MaterializationFailed) as failure:
        verify_materialization(issue=90, expected_status="CAPTURE",
                               board=_board(status="READY"), issue_side_items=[ITEM])
    assert "status" in str(failure.value).lower()


def test_an_item_with_no_status_fails_closed():
    with pytest.raises(MaterializationFailed):
        verify_materialization(issue=90, expected_status="CAPTURE",
                               board=_board(status=None), issue_side_items=[ITEM])


def test_a_pull_request_on_the_board_fails_closed():
    """AlienIntent does not use PRs; a PR on the board is pollution, not a work item."""
    board = _board() + [{"id": "PVTI_pr", "type": "PULL_REQUEST", "issue": 91, "status": None}]
    with pytest.raises(MaterializationFailed) as failure:
        verify_materialization(issue=90, expected_status="CAPTURE", board=board,
                               issue_side_items=[ITEM])
    assert "pull_request" in str(failure.value).lower()


def test_success_is_never_inferred_from_a_returned_item_id_alone():
    """Guard against a future 'optimisation' that trusts the add response. The Issue side
    can report the membership while the board does not — that must still fail."""
    with pytest.raises(MaterializationFailed):
        verify_materialization(issue=90, expected_status="CAPTURE", board=[],
                               issue_side_items=[ITEM, "PVTI_second"])


# Adversarial review finding 3: a fail-closed verifier must not accept a connection whose
# own metadata contradicts its nodes. Rejecting only totalCount > len(nodes) let a partial
# or inconsistent response through, and the target item could then "verify" against a board
# that was never complete.

def _payload(nodes, total=None, has_next=False):
    return {"totalCount": len(nodes) if total is None else total,
            "pageInfo": {"hasNextPage": has_next},
            "nodes": [{"id": n, "type": "ISSUE", "content": {"__typename": "Issue", "number": 90},
                       "fieldValueByName": {"name": "CAPTURE"}} for n in nodes]}


def test_a_complete_board_payload_is_accepted():
    assert len(board_from_payload(_payload([ITEM]))) == 1


def test_a_count_greater_than_the_nodes_fails_closed():
    with pytest.raises(MaterializationFailed):
        board_from_payload(_payload([ITEM], total=5))


def test_a_count_smaller_than_the_nodes_fails_closed():
    with pytest.raises(MaterializationFailed):
        board_from_payload(_payload([ITEM, "PVTI_b"], total=0))


def test_another_page_fails_closed():
    with pytest.raises(MaterializationFailed):
        board_from_payload(_payload([ITEM], has_next=True))


def test_missing_completeness_metadata_fails_closed():
    with pytest.raises(MaterializationFailed):
        board_from_payload({"nodes": [], "pageInfo": {}})


def _graphql_page(nodes, total, has_next, end_cursor=None):
    return {
        "data": {
            "organization": {
                "projectV2": {
                    "items": {
                        "totalCount": total,
                        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
                        "nodes": nodes,
                    }
                }
            }
        }
    }


def _graphql_node(item_id, issue):
    return {
        "id": item_id,
        "type": "ISSUE",
        "content": {"__typename": "Issue", "number": issue,
                    "repository": {"nameWithOwner": "AlienLogicLab/alienintent"}},
        "fieldValueByName": {"name": "CAPTURE"},
    }


def test_read_board_paginates_complete_project(monkeypatch):
    pages = [
        _graphql_page([_graphql_node("PVTI_a", 90)], 2, True, "cursor-1"),
        _graphql_page([_graphql_node("PVTI_b", 91)], 2, False, None),
    ]
    calls = []

    def fake_gh(*args):
        calls.append(args)
        return __import__("json").dumps(pages[len(calls) - 1])

    monkeypatch.setattr(project_materialization, "_gh", fake_gh)
    board = read_board()
    assert [row["issue"] for row in board] == [90, 91]
    assert len(calls) == 2
    assert "cursor=cursor-1" in calls[1]


def test_read_board_rejects_total_count_change(monkeypatch):
    pages = [
        _graphql_page([_graphql_node("PVTI_a", 90)], 2, True, "cursor-1"),
        _graphql_page([_graphql_node("PVTI_b", 91)], 3, False, None),
    ]

    monkeypatch.setattr(project_materialization, "_gh",
                        lambda *args: __import__("json").dumps(pages.pop(0)))
    with pytest.raises(MaterializationFailed):
        read_board()


def test_read_board_rejects_missing_or_repeated_cursor(monkeypatch):
    missing = [_graphql_page([_graphql_node("PVTI_a", 90)], 2, True, None)]
    monkeypatch.setattr(project_materialization, "_gh",
                        lambda *args: __import__("json").dumps(missing[0]))
    with pytest.raises(MaterializationFailed):
        read_board()

    pages = [
        _graphql_page([_graphql_node("PVTI_a", 90)], 3, True, "cursor-1"),
        _graphql_page([_graphql_node("PVTI_b", 91)], 3, True, "cursor-1"),
    ]
    monkeypatch.setattr(project_materialization, "_gh",
                        lambda *args: __import__("json").dumps(pages.pop(0)))
    with pytest.raises(MaterializationFailed):
        read_board()


def test_biu_materialization_requires_parent_requirement(tmp_path, monkeypatch):
    body = tmp_path / "body.md"
    body.write_text("body")
    with pytest.raises(MaterializationFailed, match="parent-issue"):
        project_materialization.materialize("WO-999999 — child", str(body), "TASKS")


def test_biu_materialization_inherits_parent_priority_and_relationship(tmp_path, monkeypatch):
    body = tmp_path / "body.md"
    body.write_text("body")
    calls = []
    verified = []

    monkeypatch.setattr(project_materialization, "requirement_priority", lambda parent: "P0")

    def fake_gh(*args):
        calls.append(args)
        if args[:2] == ("issue", "create"):
            return "https://github.com/AlienLogicLab/alienintent/issues/999"
        if args[:2] == ("project", "item-add"):
            return '{"id":"PVTI_child"}'
        return "{}"

    monkeypatch.setattr(project_materialization, "_gh", fake_gh)
    monkeypatch.setattr(project_materialization, "attach_parent",
                        lambda parent, child: verified.append(("attach", parent, child)))
    monkeypatch.setattr(project_materialization, "verify",
                        lambda issue, status: verified.append(("status", issue, status)))
    monkeypatch.setattr(project_materialization, "verify_priority",
                        lambda issue, priority: verified.append(("priority", issue, priority)))
    monkeypatch.setattr(project_materialization, "verify_parent",
                        lambda parent, child: verified.append(("parent", parent, child)))

    project_materialization.materialize("WO-999999 — child", str(body), "TASKS", 23)

    edits = [args for args in calls if args[:2] == ("project", "item-edit")]
    assert any(project_materialization.PRIORITY_FIELD in args and
               project_materialization.PRIORITY_OPTIONS["P0"] in args for args in edits)
    assert ("attach", 23, 999) in verified
    assert ("priority", 999, "P0") in verified
    assert ("parent", 23, 999) in verified
