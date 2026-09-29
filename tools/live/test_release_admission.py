"""Release admission preconditions (SWF-21, SWF-35, SF-REQ-002 amendment 2026-09-29).

Evidence: PY-07 was moved READY -> IMPLEMENT with no record naming a baseline, while its Issue
body still said implementation was not authorized. Two producers refused correctly; work
proceeded only once an exact, resolvable baseline was bound. These checks make that mechanical.
Since 2026-09-29 the authority is structural: a native READY receipt bound to the current task
packet by its input digest, and the baseline named by the BIU's execution packet.
"""
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from release_admission import admit  # noqa: E402

DOCUMENT = b"# PY-07\nThe task packet as assessed.\n"
DIGEST = hashlib.sha256(DOCUMENT).hexdigest()
GOOD = dict(
    issue=55,
    status="READY",
    agent_ready="READY",
    body="**BIU:** PY-07",
    receipt={"disposition": "READY", "work_unit_id": "PY-07", "input_sha256": DIGEST},
    work_unit_sha256=DIGEST,
    baseline="6c3f8432129892f11d182e713102e63cf0aa9b56",
    baseline_resolves=True,
    baseline_ancestral=True,
    open_dependencies=[],
    active_invocations=[],
    active_claims_total=0,
    wip_limit=1,
    held=False,
)


def _fail_codes(**overrides):
    return [f["check"] for f in admit({**GOOD, **overrides})]


def test_a_bound_receipt_and_a_packet_baseline_are_admitted():
    assert admit(GOOD) == []


def test_release_without_a_receipt_naming_its_work_unit_is_refused():
    assert "receipt_bound" in _fail_codes(receipt=None)
    assert "receipt_bound" in _fail_codes(receipt={**GOOD["receipt"], "work_unit_id": None})


def test_a_receipt_whose_work_unit_has_no_document_is_refused():
    assert "receipt_bound" in _fail_codes(work_unit_sha256=None)


def test_a_task_packet_edited_after_its_ready_assessment_is_refused():
    """SWF-35: the released text is the assessed text. An old READY receipt never admits an
    edited packet; the Director must assess the current packet again."""
    edited = hashlib.sha256(DOCUMENT + b"one more requirement\n").hexdigest()
    failures = admit({**GOOD, "work_unit_sha256": edited})
    assert [f["check"] for f in failures] == ["receipt_bound"]
    assert "fresh assessment" in failures[0]["why"]


def test_release_must_name_a_baseline():
    assert "baseline_named" in _fail_codes(baseline=None)


def test_a_baseline_that_does_not_resolve_is_refused():
    """The coordinator once published a baseline SHA that did not exist."""
    assert "baseline_resolves" in _fail_codes(baseline_resolves=False)


def test_a_baseline_outside_the_release_point_ancestry_is_refused():
    assert "baseline_ancestral" in _fail_codes(baseline_ancestral=False)


def test_stale_unauthorized_wording_without_a_superseding_statement_is_refused():
    assert "authority_wording_consistent" in _fail_codes(
        body="> Implementation is **not** authorized by this Issue. Release remains an explicit authority step.")


def test_unauthorized_wording_is_accepted_when_explicitly_superseded():
    assert admit({**GOOD, "body": "> Implementation is **not** authorized by this Issue.\n"
                                  "> **RELEASED 2026-09-20 under SWF-21.** IMPLEMENT is authorized against "
                                  "baseline `6c3f843`, superseding the line above."}) == []


def test_release_prose_never_stands_in_for_a_bound_receipt():
    """Authority is structural: a comment or body saying IMPLEMENT is authorized admits nothing."""
    codes = _fail_codes(receipt=None, body="> **RELEASED.** IMPLEMENT is authorized against baseline `6c3f843`.")
    assert "receipt_bound" in codes


def test_a_biu_not_in_ready_is_refused():
    assert "status_ready" in _fail_codes(status="TASKS")


def test_a_biu_without_an_agent_ready_disposition_is_refused():
    assert "agent_ready" in _fail_codes(agent_ready="NEEDS_CLARIFICATION")


@pytest.mark.parametrize("disposition", [None, "HOLD", "CLARIFY", "SPLIT"])
def test_a_biu_without_a_ready_disposition_is_refused(disposition):
    assert "agent_ready" in _fail_codes(agent_ready=disposition)


def test_an_unreadable_assessment_says_why():
    failures = admit({**GOOD, "agent_ready": None, "agent_ready_unreadable": "assessment unreadable: x"})
    assert any(f["check"] == "agent_ready" and "unreadable" in f["why"] for f in failures)


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
    for failure in admit({**GOOD, "receipt": None, "baseline_resolves": False}):
        assert failure["why"], failure
        assert failure["check"]


def test_all_failures_are_reported_not_just_the_first():
    codes = _fail_codes(status="TASKS", receipt=None, held=True)
    assert {"status_ready", "receipt_bound", "not_held"} <= set(codes)


def test_issue_project_readback_is_authoritative_when_list_transport_omits_the_new_item():
    from release_admission import project_status_from_issue
    issue = {"projectItems": [{"title": "AlienIntent", "status": {"name": "READY"}}]}
    assert project_status_from_issue(issue) == "READY"


# --- the one Agent Ready reader (shared with the Factory Director inputs adapter) -------------
# #125: HOLD and CLARIFY records were cited by path in the body while the later READY receipts
# cited none, and later comments mentioning "RELEASED" without a baseline were taken as the
# newest release record. The Director and the gate then disagreed about the same Issue.

from release_admission import (  # noqa: E402
    MalformedReceipt,
    agent_ready_disposition,
    agent_ready_receipt,
    comments_from_gh,
    packet_baseline,
    receipt_record,
    work_unit_document,
)

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
    assert receipt_record(record()) == {"disposition": "READY", "input_sha256": "0" * 64, "work_unit_id": "WO-220505"}
    assert receipt_record(record(outcome="EXECUTION_FAILURE")) is None
    assert receipt_record(record(provenance={"producer": "surrogate-bootstrap-assessor", "input_sha256": "0" * 64})) is None
    assert receipt_record(record(provenance={"producer": "agent-ready-cli", "input_sha256": ""})) is None
    assert receipt_record(record("MAYBE")) is None


def test_a_bare_legacy_disposition_is_not_a_receipt():
    """A compatible shape is not evidence: without Agent Ready provenance and an input digest a
    record cannot be bound to the packet it assessed."""
    assert receipt_record({"disposition": "READY"}) is None


def test_the_newest_receipt_is_the_current_disposition():
    comments = [receipt("HOLD"), receipt("CLARIFY"), {"author": OPERATOR, "body": "RELEASED, see above"},
                receipt("READY")]
    assert agent_ready_disposition(comments, OPERATORS) == "READY"
    assert agent_ready_disposition(comments + [receipt("CLARIFY")], OPERATORS) == "CLARIFY"


def test_the_receipt_carries_the_work_unit_and_digest_it_assessed():
    newest = agent_ready_receipt([receipt("HOLD"), receipt(work_unit_id="WO-220611",
        provenance={"producer": "agent-ready-cli", "input_sha256": "AB" * 32})], OPERATORS)
    assert newest == {"disposition": "READY", "work_unit_id": "WO-220611", "input_sha256": "ab" * 32}


def test_a_narrative_comment_about_a_different_issues_release_is_not_a_receipt():
    """Bug found live on Issue #124 (WO-220504): a comment describing a DIFFERENT, already landed
    Issue's release produced a false ADMITTED when authority was read from prose. Prose is not a
    receipt; only a native marker from an operator is."""
    comment = {"author": OPERATOR, "body": (
        "Bounded prerequisite dispatched. WO-220610 reached native Agent Ready READY and was released "
        "READY -> IMPLEMENT (`release_admission.py` ADMITTED, baseline "
        "`322baf4ae45776acb59d303370b12d48d76085ee`). This BIU's own hold is not authorized to lift.")}
    assert agent_ready_receipt([comment], OPERATORS) is None


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


# --- the work-unit document and packet baseline a receipt binds to ---------------------------
# Inserted identifiers (SWF-33: PY-09B) and any BIU family (Issue #83: ARP-01, FDH-01) resolve;
# the identifier is one plain segment, so nothing outside the work-unit and packet directories
# can be read (Issue #83, JC R1: `..`, `/` and prefixes never reach a file).

def reader(files: dict[str, bytes]):
    asked = []

    def read(path: PurePosixPath):
        asked.append(str(path))
        return files.get(str(path))
    return read, asked


@pytest.mark.parametrize("unit, path", [
    ("PY-09B", "docs/work-units/python/PY-09B.md"),
    ("PY-10", "docs/work-units/python/PY-10.md"),
    ("WO-220101", "docs/work-units/wave2/WO-220101.md"),
    ("ARP-01", "docs/work-units/wave2/ARP-01.md"),
    ("FDH-01", "docs/work-units/wave2/FDH-01.md"),
    ("SF-REQ-057", "docs/work-units/SF-REQ-057.md"),
])
def test_a_work_unit_document_for_any_biu_identifier_is_found(unit, path):
    read, _ = reader({path: b"packet"})
    assert work_unit_document(unit, read) == (PurePosixPath(path), b"packet")


def test_the_wave2_document_wins_over_another_directory():
    read, _ = reader({"docs/work-units/wave2/WO-220202.md": b"wave2", "docs/work-units/WO-220202.md": b"other"})
    assert work_unit_document("WO-220202", read)[1] == b"wave2"


@pytest.mark.parametrize("unit", [
    None, "", "../etc/passwd", "WO-220202/../../x", "docs/work-units/wave2/WO-220202", "WO-220202.md",
    "WO-220202.s", "ARP/01", "wo-220202", "PY05", "-PY-05", "PY-05/", "XPY-05 ", "PY-05\n",
])
def test_an_identifier_that_is_not_one_plain_segment_names_no_file(unit):
    read, asked = reader({})
    assert work_unit_document(unit, read) == (None, None)
    assert packet_baseline(unit, read) is None
    assert asked == []


def test_a_missing_document_is_none():
    read, asked = reader({})
    assert work_unit_document("WO-220202", read) == (None, None)
    assert asked == [f"{d}/WO-220202.md" for d in ("docs/work-units/wave2", "docs/work-units/python", "docs/work-units")]


def packet(**authority):
    return json.dumps({"biu_id": "WO-220202", "starting_authority": authority}).encode()


def test_the_packet_admission_baseline_wins_over_its_contract_baseline():
    read, asked = reader({"docs/evidence/wave2-execution-packets/WO-220102.packet.json": packet(
        admission_baseline_sha="a80a26bc1a9999ae1f082ad0a80c47c1c5baffec",
        candidate_contract_baseline_sha="2528e3acd773f53de116f6f28537244d1f1f8b2f")})
    assert packet_baseline("WO-220102", read) == "a80a26bc1a9999ae1f082ad0a80c47c1c5baffec"
    assert asked == ["docs/evidence/wave2-execution-packets/WO-220102.packet.json"]


def test_a_packet_baseline_sha_is_read():
    read, _ = reader({"docs/evidence/wave2-execution-packets/WO-220202.packet.json": packet(baseline_sha="6c3f843")})
    assert packet_baseline("WO-220202", read) == "6c3f843"


@pytest.mark.parametrize("raw", [None, b"not json", b"[]", packet(), packet(baseline_sha="main"),
                                 packet(baseline_sha="6c3f843 extra"), packet(baseline_sha=123)])
def test_a_missing_or_malformed_packet_names_no_baseline(raw):
    files = {} if raw is None else {"docs/evidence/wave2-execution-packets/WO-220202.packet.json": raw}
    read, _ = reader(files)
    assert packet_baseline("WO-220202", read) is None
