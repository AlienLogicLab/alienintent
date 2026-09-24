"""Release admission preconditions (SWF-21).

Evidence: PY-07 was moved READY -> IMPLEMENT with no release record naming a baseline,
while its Issue body still said implementation was not authorized. Two producers refused
correctly; work proceeded only once an explicit release record with a resolvable baseline
existed. These checks make that mechanical.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from release_admission import admit  # noqa: E402

GOOD = dict(
    issue=55,
    status="READY",
    agent_ready="READY",
    body="**BIU:** PY-07\n> **RELEASED** IMPLEMENT authorized against baseline `6c3f843`.",
    release_record={"baseline": "6c3f8432129892f11d182e713102e63cf0aa9b56", "authorizes_implement": True},
    baseline_resolves=True,
    baseline_ancestral=True,
    open_dependencies=[],
    active_invocations=[],
    held=False,
)


def _fail_codes(**overrides):
    return [f["check"] for f in admit({**GOOD, **overrides})]


def test_a_complete_release_record_is_admitted():
    assert admit(GOOD) == []


def test_release_without_a_record_authorizing_implementation_is_refused():
    assert "implementation_authorized" in _fail_codes(release_record=None)


def test_release_record_must_name_a_baseline():
    assert "baseline_named" in _fail_codes(release_record={"baseline": None, "authorizes_implement": True})


def test_a_baseline_that_does_not_resolve_is_refused():
    """The coordinator once published a baseline SHA that did not exist."""
    assert "baseline_resolves" in _fail_codes(baseline_resolves=False)


def test_a_baseline_outside_the_release_point_ancestry_is_refused():
    assert "baseline_ancestral" in _fail_codes(baseline_ancestral=False)


def test_stale_unauthorized_wording_without_a_superseding_record_is_refused():
    assert "authority_wording_consistent" in _fail_codes(
        body="> Implementation is **not** authorized by this Issue. Release remains an explicit authority step.")


def test_unauthorized_wording_is_accepted_when_explicitly_superseded():
    assert admit({**GOOD, "body": "> Implementation is **not** authorized by this Issue.\n"
                                  "> **RELEASED 2026-09-20 under SWF-21.** IMPLEMENT is authorized against "
                                  "baseline `6c3f843`, superseding the line above."}) == []


def test_a_biu_not_in_ready_is_refused():
    assert "status_ready" in _fail_codes(status="TASKS")


def test_a_biu_without_an_agent_ready_disposition_is_refused():
    assert "agent_ready" in _fail_codes(agent_ready="NEEDS_CLARIFICATION")


def test_an_open_dependency_is_refused():
    assert "dependencies_satisfied" in _fail_codes(open_dependencies=[52])


def test_an_existing_active_invocation_is_refused():
    assert "no_active_invocation" in _fail_codes(active_invocations=["AlienLogicLab/alienintent#55:PRODUCER"])


def test_an_explicitly_held_biu_is_refused():
    assert "not_held" in _fail_codes(held=True)


def test_every_failure_explains_itself():
    for failure in admit({**GOOD, "release_record": None, "baseline_resolves": False}):
        assert failure["why"], failure
        assert failure["check"]


def test_all_failures_are_reported_not_just_the_first():
    codes = _fail_codes(status="TASKS", release_record=None, held=True)
    assert {"status_ready", "implementation_authorized", "not_held"} <= set(codes)


# --- inserted BIU identifiers ---------------------------------------------------
# SWF-33 introduced PY-09B, following the repository's existing suffix convention.
# The disposition lookup keyed on PY-\d\d and silently returned None for it, which the
# gate then reported as "Agent-Ready disposition is None" — a missing-assessment refusal
# for a BIU whose assessment existed and said READY.


def test_a_suffixed_biu_identifier_is_recognised():
    from release_admission import biu_from_body
    assert biu_from_body("see [`PY-09B.assessment.json`](.../PY-09B.assessment.json)") == "PY-09B"


def test_a_plain_biu_identifier_is_still_recognised():
    from release_admission import biu_from_body
    assert biu_from_body("see [`PY-10.assessment.json`](.../PY-10.assessment.json)") == "PY-10"


def test_a_body_without_an_assessment_pointer_yields_none():
    from release_admission import biu_from_body
    assert biu_from_body("no pointer here") is None


# --- Wave 2 (2026-09-22): native Agent Ready records live beside the Wave 2 evidence ---------
# WO-NNNNNN BIUs are assessed by the Agent Ready product; the retained record is a
# ReadinessAssessment envelope under docs/evidence/wave2-readiness-assessments/, not a bare
# PY-NN.assessment.json under docs/work-units/python/. The gate must read the disposition from
# that record and only when the record says it was ASSESSED by Agent Ready.

from release_admission import biu_from_body, assessment_record_path, disposition_from_record  # noqa: E402

WAVE2_BODY = ("**Contract:** docs/work-units/wave2/WO-220101.md · readiness record "
              "docs/evidence/wave2-readiness-assessments/WO-220101.2026-09-22T110109.877043Z.assessment.json")


def test_a_wave2_biu_identifier_is_recognised():
    assert biu_from_body(WAVE2_BODY) == "WO-220101"


def test_a_wave2_readiness_record_path_is_taken_from_the_body():
    assert assessment_record_path(WAVE2_BODY).name == "WO-220101.2026-09-22T110109.877043Z.assessment.json"


def test_disposition_comes_only_from_an_assessed_agent_ready_record():
    rec = {"record_kind": "ReadinessAssessment", "outcome": "ASSESSED", "disposition": "READY",
           "provenance": {"producer": "agent-ready-cli", "native_agent_ready": True}}
    assert disposition_from_record(rec) == "READY"
    assert disposition_from_record({**rec, "outcome": "EXECUTION_FAILURE"}) is None
    assert disposition_from_record({**rec, "provenance": {"producer": "surrogate-bootstrap-assessor"}}) is None


def test_a_legacy_python_record_is_still_read_as_before():
    assert disposition_from_record({"disposition": "READY"}) == "READY"


def test_issue_project_readback_is_authoritative_when_list_transport_omits_the_new_item():
    from release_admission import project_status_from_issue
    issue = {"projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
    assert project_status_from_issue(issue) == "READY"


def test_native_issue_comment_receipt_requires_agent_ready_provenance_and_input_digest():
    from release_admission import disposition_from_native_comment
    valid = ("<!-- AGENT_READY_ASSESSMENT: {\"record_kind\":\"ReadinessAssessment\","
             "\"outcome\":\"ASSESSED\",\"disposition\":\"READY\","
             "\"provenance\":{\"producer\":\"agent-ready-cli\","
             "\"input_sha256\":\"abc\"}} -->")
    assert disposition_from_native_comment(valid) == "READY"
    assert disposition_from_native_comment(valid.replace("agent-ready-cli", "surrogate")) is None
    assert disposition_from_native_comment(valid.replace("input_sha256\":\"abc", "input_sha256\":\"")) is None


# --- Issue #83 (BRD-83): any BIU identifier, and nothing outside the record directory ----------
# ARP-01 and FDH-01 had native READY records on main, yet only WO-NNNNNN paths were recognised,
# so their release fell back to the native-receipt comment. The identifier widening must not
# widen the directory: the path is read from the release point, and a pattern that followed
# `..` or a `/` could be steered at a file that is not a readiness record.

import pytest  # noqa: E402

RECORDS = {
    "ARP-01": "docs/evidence/wave2-readiness-assessments/ARP-01.2026-09-24T030043.921727Z.assessment.json",
    "FDH-01": "docs/evidence/wave2-readiness-assessments/FDH-01.2026-09-24T055203.941687Z.assessment.json",
    "WO-220202": "docs/evidence/wave2-readiness-assessments/WO-220202.2026-09-23T161839.955776Z.assessment.json",
}


@pytest.mark.parametrize("biu", sorted(RECORDS))
def test_a_readiness_record_for_any_biu_identifier_is_recognised(biu):
    for text in (f"readiness record `{RECORDS[biu]}`", f"record ({RECORDS[biu]}).", RECORDS[biu]):
        assert str(assessment_record_path(text)) == RECORDS[biu]


def test_the_release_record_carries_its_text_so_a_path_cited_there_is_found():
    from release_admission import release_record_from
    comment = f"RELEASED. IMPLEMENT is authorized at baseline `474343a`. Record `{RECORDS['FDH-01']}`."
    record = release_record_from("no pointer", [{"body": comment}])
    assert str(assessment_record_path(record["text"])) == RECORDS["FDH-01"]


def test_a_path_that_climbs_out_of_the_record_directory_is_rejected():
    assert assessment_record_path(
        "`docs/evidence/wave2-readiness-assessments/../../../etc/ARP-01.s.assessment.json`") is None
    assert assessment_record_path(
        "`docs/evidence/wave2-readiness-assessments/ARP-01..assessment.json`") is None


def test_a_record_path_reached_through_a_parent_prefix_is_rejected():
    assert assessment_record_path(
        "`../docs/evidence/wave2-readiness-assessments/ARP-01.2026-09-24T030043.921727Z.assessment.json`") is None


def test_an_identifier_containing_a_slash_is_rejected():
    assert assessment_record_path(
        "`docs/evidence/wave2-readiness-assessments/ARP/01.2026-09-24T030043.921727Z.assessment.json`") is None


def test_a_record_in_another_directory_is_rejected():
    assert assessment_record_path(
        "`docs/evidence/elsewhere/ARP-01.2026-09-24T030043.921727Z.assessment.json`") is None
    assert assessment_record_path(
        "`docs/evidence/wave2-readiness-assessments/sub/FDH-01.2026-09-24T055203.941687Z.assessment.json`") is None


def test_a_record_path_continued_past_the_file_is_rejected():
    assert assessment_record_path(
        "`docs/evidence/wave2-readiness-assessments/ARP-01.2026-09-24T030043.921727Z.assessment.json/../x`") is None


def test_the_wave1_python_record_path_is_unchanged():
    assert str(assessment_record_path("see `PY-09B.assessment.json`")) == \
        "docs/work-units/python/PY-09B.assessment.json"
