"""Release admission preconditions (SWF-21).

Evidence: PY-07 was moved READY -> IMPLEMENT while its Agent Ready assessment did not permit
it; two producers refused correctly. Admission is now decided from structured state only:
Project status, the Agent Ready receipt, dependencies, holds, claims and priority. The gate
no longer reads authority from comment prose (#125: later comments that mentioned "RELEASED"
without a baseline were taken as the newest release record and refused a valid BIU).
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from release_admission import (  # noqa: E402
    MalformedReceipt,
    admit,
    agent_ready_disposition,
    comments_from_gh,
    project_status_from_issue,
    receipt_disposition,
)

GOOD = dict(
    issue=55,
    status="READY",
    agent_ready="READY",
    open_dependencies=[],
    active_invocations=[],
    active_claims_total=0,
    wip_limit=1,
    held=False,
)


def _fail_codes(**overrides):
    return [f["check"] for f in admit({**GOOD, **overrides})]


def test_structured_readiness_is_admitted():
    assert admit(GOOD) == []


def test_no_release_prose_is_required():
    """A READY BIU with a READY receipt needs no 'IMPLEMENT is authorized' comment or baseline."""
    assert admit({**GOOD, "body": "> Implementation is **not** authorized by this Issue."}) == []


def test_a_biu_not_in_ready_is_refused():
    assert "status_ready" in _fail_codes(status="TASKS")


@pytest.mark.parametrize("disposition", [None, "HOLD", "CLARIFY", "SPLIT"])
def test_a_biu_without_a_ready_disposition_is_refused(disposition):
    assert _fail_codes(agent_ready=disposition) == ["agent_ready"]


def test_an_unreadable_assessment_says_why():
    [failure] = admit({**GOOD, "agent_ready": None, "agent_ready_unreadable": "assessment unreadable: x"})
    assert failure["check"] == "agent_ready" and "assessment unreadable: x" in failure["why"]


def test_an_open_dependency_is_refused():
    assert "dependencies_satisfied" in _fail_codes(open_dependencies=[52])


def test_an_existing_active_invocation_is_refused():
    assert "no_active_invocation" in _fail_codes(active_invocations=["AlienLogicLab/alienintent#55:PRODUCER"])


def test_an_explicitly_held_biu_is_refused():
    assert "not_held" in _fail_codes(held=True)


def test_an_unreadable_wip_limit_is_refused():
    assert "wip_limit_known" in _fail_codes(wip_limit=None)


def test_an_unreadable_active_claim_total_is_refused():
    assert "wip_capacity_known" in _fail_codes(active_claims_total=None)


def test_active_claims_at_the_wip_limit_are_refused():
    # 2026-09-27 incident: releasing a second, graph-independent Issue while another
    # Issue's PRODUCER claim was still active produced two simultaneous claims against
    # wipLimit=1. This is the mechanical guard that incident recommended.
    assert "wip_capacity_available" in _fail_codes(active_claims_total=1, wip_limit=1)


def test_active_claims_above_the_wip_limit_are_refused():
    assert "wip_capacity_available" in _fail_codes(active_claims_total=2, wip_limit=1)


def test_active_claims_below_the_wip_limit_are_admitted():
    assert _fail_codes(active_claims_total=0, wip_limit=1) == []


def test_every_failure_explains_itself():
    for failure in admit({**GOOD, "agent_ready": None, "status": "TASKS", "held": True}):
        assert failure["why"], failure
        assert failure["check"]


def test_all_failures_are_reported_not_just_the_first():
    codes = _fail_codes(status="TASKS", agent_ready="HOLD", held=True)
    assert {"status_ready", "agent_ready", "not_held"} <= set(codes)


def test_issue_project_readback_is_authoritative_when_list_transport_omits_the_new_item():
    issue = {"projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
    assert project_status_from_issue(issue) == "READY"


# --- the one Agent Ready reader (shared with the Factory Director inputs adapter) -------------

OPERATOR = "sanookdu"
OPERATORS = frozenset({OPERATOR})


def record(disposition="READY", **overrides):
    """A native receipt in the shape tools/orchestration/readiness_assessment.py records."""
    value = {"record_kind": "ReadinessAssessment", "outcome": "ASSESSED", "disposition": disposition,
             "work_unit_id": "WO-220505",
             "provenance": {"producer": "agent-ready-cli", "input_sha256": "0" * 64}}
    value.update(overrides)
    return value


def receipt(disposition="READY", author=OPERATOR, **overrides):
    body = f"Native Agent Ready receipt.\n<!-- AGENT_READY_ASSESSMENT: {json.dumps(record(disposition, **overrides))} -->"
    return {"author": author, "body": body}


def test_a_native_receipt_needs_agent_ready_provenance_and_an_input_digest():
    assert receipt_disposition(record()) == "READY"
    assert receipt_disposition(record(outcome="EXECUTION_FAILURE")) is None
    assert receipt_disposition(record(provenance={"producer": "surrogate", "input_sha256": "0" * 64})) is None
    assert receipt_disposition(record(provenance={"producer": "agent-ready-cli", "input_sha256": ""})) is None
    assert receipt_disposition({"disposition": "READY"}) is None
    assert receipt_disposition(record("MAYBE")) is None


def test_the_newest_receipt_is_the_current_disposition():
    """#125: HOLD and CLARIFY records were cited by path; the later READY receipts cited none."""
    comments = [receipt("HOLD"), receipt("CLARIFY"), {"author": OPERATOR, "body": "RELEASED, see above"},
                receipt("READY")]
    assert agent_ready_disposition(comments, OPERATORS) == "READY"
    assert agent_ready_disposition(comments + [receipt("CLARIFY")], OPERATORS) == "CLARIFY"


def test_a_receipt_from_anyone_but_an_operator_is_ignored():
    assert agent_ready_disposition([receipt("READY", author="drive-by")], OPERATORS) is None
    assert agent_ready_disposition([receipt("HOLD"), receipt("READY", author="drive-by")], OPERATORS) == "HOLD"


def test_an_edited_receipt_counts_only_when_an_operator_edited_it():
    assert agent_ready_disposition([{**receipt(), "editor": "someone"}], OPERATORS) is None
    assert agent_ready_disposition([{**receipt(), "editor": OPERATOR}], OPERATORS) == "READY"
    assert agent_ready_disposition([{**receipt(), "lastEditedAt": "2026-09-29T00:00:00Z"}], OPERATORS) is None


def test_a_non_native_marker_does_not_override_an_older_native_receipt():
    comments = [receipt("READY"), receipt("HOLD", outcome="EXECUTION_FAILURE")]
    assert agent_ready_disposition(comments, OPERATORS) == "READY"


def test_an_unparsable_operator_marker_fails_closed():
    with pytest.raises(MalformedReceipt):
        agent_ready_disposition([{"author": OPERATOR, "body": "<!-- AGENT_READY_ASSESSMENT: {broken -->"}],
                                OPERATORS)
    assert agent_ready_disposition([{"author": "x", "body": "<!-- AGENT_READY_ASSESSMENT: {broken -->"}],
                                   OPERATORS) is None


def test_gh_comments_map_to_the_reader_shape():
    gh = [{"author": {"login": OPERATOR}, "body": receipt()["body"], "includesCreatedEdit": False},
          {"author": {"login": OPERATOR}, "body": receipt("HOLD")["body"], "includesCreatedEdit": True}]
    assert agent_ready_disposition(comments_from_gh(gh), OPERATORS) == "READY"
