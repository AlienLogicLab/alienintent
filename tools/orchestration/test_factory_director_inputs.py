"""Acceptance tests for the authoritative Factory Director predicate adapter (FDH-01).

Criterion 1: one test per predicate, each proving a true and a false case.
Criterion 2: every malformed or unavailable source fails closed, and each such check is
             shown failing against a deliberately broken adapter (a check that cannot fail
             is not evidence).
Criterion 3: Founder-hold and Director-inbox scenarios drive the real host.
"""
from pathlib import Path
import json
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import factory_director_inputs as adapter_module  # noqa: E402
from factory_director_host import (  # noqa: E402
    FactoryDirectorHost,
    HostState,
    InMemoryDirectorLauncher,
    JsonDirectorInputs,
)
from factory_director_inputs import (  # noqa: E402
    AuthoritativeDirectorInputs,
    SourceUnavailable,
    materialization,
)

REPO = "AlienLogicLab/alienintent"
OPERATOR = "sanookdu"
ASSESSMENT_BODY = ('**Native Agent Ready receipt.**\n<!-- AGENT_READY_ASSESSMENT: '
              '{"disposition":"READY","record_kind":"ReadinessAssessment","work_unit_id":"X"} -->')
ASSESSMENT = {"author": OPERATOR, "body": ASSESSMENT_BODY}


def comment(body, author="someone"):
    return {"author": author, "body": body}


class Sources:
    """Complete, consistent fixture sources: nothing requires control until a test adds it."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_file = root / "runtime" / "state.json"
        self.self_hosting = root / "config" / "self-hosting.json"
        self.holds_file = root / "director" / "founder-holds.json"
        self.pause_flag = root / "director" / "PAUSE"
        self.inbox = root / "director" / "inbox"
        self.config = root / "config" / "factory-director-host.json"
        self.projection = root / "host" / "inputs.json"
        self.board: list[dict] = []
        self.comments: dict[int, list[dict]] = {}
        self.state = {"deliveries": {}, "active": {}, "founderExceptions": {}}
        self.holds: list[dict] = []
        for directory in (self.state_file.parent, self.self_hosting.parent, self.inbox):
            directory.mkdir(parents=True, exist_ok=True)
        self.self_hosting.write_text(json.dumps({
            "repository": {"owner": "AlienLogicLab", "name": "alienintent"},
            "project": {"owner": "AlienLogicLab", "number": 1},
            "operator": {"authorizedGithubLogins": [OPERATOR]},
            "paths": {"stateFile": str(self.state_file)}}))
        self.config.write_text(json.dumps({
            "schemaVersion": 1, "selfHostingConfig": str(self.self_hosting), "wipLimit": 1,
            "founderHoldRecord": str(self.holds_file), "pauseFlag": str(self.pause_flag),
            "directorInbox": str(self.inbox),
            "launcher": {"provider": "claude", "executable": "/x/claude", "model": "m",
                         "permissionMode": "bypassPermissions"}}))
        self.flush()

    def flush(self) -> None:
        self.state_file.write_text(json.dumps(self.state))
        self.holds_file.write_text(json.dumps({"schemaVersion": 1, "holds": self.holds}))

    def issue(self, number: int, status: str) -> "Sources":
        self.board.append({"id": f"PVTI_{number}", "type": "ISSUE", "issue": number, "status": status,
                           "repository": REPO})
        return self

    def claim(self, number: int, role: str = "PRODUCER") -> "Sources":
        self.state["active"][f"{REPO}#{number}:{role}"] = {
            "invocationId": f"{REPO}#{number}:{role}:abc",
            "item": {"repository": REPO, "issue": number, "itemId": f"PVTI_{number}"}, "role": role}
        self.flush()
        return self

    def hold(self, number: int) -> "Sources":
        self.holds.append({"issue": number, "reason": "Founder decision on scope"})
        self.flush()
        return self

    def escalate(self, number: int, at: str = "2026-09-24T06:00:00.000Z") -> "Sources":
        self.state.setdefault("limitEscalations", {})[f"{REPO}#{number}"] = {
            "outcome": "EXECUTION_CYCLE_LIMIT", "biu": f"{REPO}#{number}", "at": at}
        self.flush()
        return self

    def inbox_entry(self, entry_id: str, receipt: bool = False) -> "Sources":
        (self.inbox / f"{entry_id}.json").write_text('{"from": "Founder"}')
        if receipt:
            (self.inbox / "processed").mkdir(exist_ok=True)
            (self.inbox / "processed" / f"{entry_id}.json").write_text('{"processedBy": "episode"}')
        return self

    def adapter(self, cls=AuthoritativeDirectorInputs):
        return cls(self.config, self.projection, board_reader=lambda: list(self.board),
                   comments_reader=lambda issue: list(self.comments.get(issue, [])))

    def inputs(self, cls=AuthoritativeDirectorInputs):
        return self.adapter(cls)()


@pytest.fixture
def sources(tmp_path):
    return Sources(tmp_path)


# --- criterion 1: one test per predicate, true and false ----------------------------------

def test_baseline_fixture_is_authoritative_and_requires_no_control(sources):
    values = sources.inputs()
    assert values.authoritative_state is True
    assert not values.control_required()


def test_authoritative_state(sources):
    assert sources.inputs().authoritative_state is True
    sources.state_file.unlink()
    assert sources.inputs().authoritative_state is False


def test_eligible_authorized_work(sources):
    assert sources.inputs().eligible_authorized_work is False
    sources.issue(1, "READY")
    assert sources.inputs().eligible_authorized_work is True


@pytest.mark.parametrize("state", ["IMPLEMENT", "VERIFY", "ACCEPT"])
def test_eligible_authorized_work_for_in_flight_issue_depends_on_its_claim(sources, state):
    sources.issue(2, state)
    assert sources.inputs().eligible_authorized_work is True
    sources.claim(2, "VERIFIER" if state == "VERIFY" else "PRODUCER")
    assert sources.inputs().eligible_authorized_work is False


@pytest.mark.parametrize("state", ["CAPTURE", "SPECIFY", "PLAN", "TASKS", "DONE"])
def test_inert_states_are_not_eligible_work(sources, state):
    sources.issue(3, state)
    values = sources.inputs()
    assert (values.eligible_authorized_work, values.lifecycle_requires_selection) == (False, False)


def test_lifecycle_requires_selection_for_review(sources):
    sources.issue(4, "DONE")
    assert sources.inputs().lifecycle_requires_selection is False
    sources.issue(5, "REVIEW")
    assert sources.inputs().lifecycle_requires_selection is True


def test_lifecycle_requires_selection_for_assessed_tasks(sources):
    sources.issue(6, "TASKS")
    sources.comments[6] = [comment("an ordinary comment")]
    assert sources.inputs().lifecycle_requires_selection is False
    sources.comments[6].append(ASSESSMENT)
    assert sources.inputs().lifecycle_requires_selection is True


def test_attention_required(sources):
    assert sources.inputs().attention_required is False
    sources.escalate(7)
    assert sources.inputs().attention_required is True


def test_pending_director_inbox(sources):
    assert sources.inputs().pending_director_inbox is False
    sources.inbox_entry("founder-note-1")
    assert sources.inputs().pending_director_inbox is True


def test_executable_capacity(sources):
    assert sources.inputs().executable_capacity is True
    sources.claim(8)
    assert sources.inputs().executable_capacity is False


def test_wip_intentionally_full(sources):
    assert sources.inputs().wip_intentionally_full is False
    sources.claim(9)
    assert sources.inputs().wip_intentionally_full is True
    sources.claim(10)  # over the limit is neither capacity nor "intentionally full"
    values = sources.inputs()
    assert (values.executable_capacity, values.wip_intentionally_full) == (False, False)


def test_founder_decision_pending(sources):
    sources.issue(11, "READY").hold(11)
    assert sources.inputs().founder_decision_pending is True
    sources.issue(12, "READY")
    assert sources.inputs().founder_decision_pending is False


def test_explicit_pause(sources):
    assert sources.inputs().explicit_pause is False
    sources.pause_flag.write_text("")
    assert sources.inputs().explicit_pause is True


# --- criterion 2: fail closed per source, each with a negative control --------------------

class SwallowBoardFailure(AuthoritativeDirectorInputs):
    def read_board(self):
        try:
            return super().read_board()
        except SourceUnavailable:
            return {1: "READY"}


class IgnoreNonIssueItems(AuthoritativeDirectorInputs):
    def read_board(self):
        rows = [row for row in self.board_reader() if row.get("type") == "ISSUE"]
        return adapter_module.validate_board(rows)


class DefaultMissingState(AuthoritativeDirectorInputs):
    def read_runtime(self, config):
        try:
            return super().read_runtime(config)
        except SourceUnavailable:
            return adapter_module.RuntimeView(0, frozenset(), (), 0)


class DefaultMissingHolds(AuthoritativeDirectorInputs):
    def read_holds(self, config):
        try:
            return super().read_holds(config)
        except SourceUnavailable:
            return {}


class DefaultMissingInbox(AuthoritativeDirectorInputs):
    def read_inbox(self, config):
        try:
            return super().read_inbox(config)
        except SourceUnavailable:
            return (), frozenset()


def board_incomplete(s):
    def reader():
        raise materialization.MaterializationFailed("Project reports 3 items but returned 2")
    s.board_reader_override = reader


def board_non_issue(s):
    s.board.append({"id": "PVTI_draft", "type": "DRAFT_ISSUE", "issue": None, "status": "READY"})


def state_missing(s):
    s.state_file.unlink()


def state_unparsable(s):
    s.state_file.write_text("{not json")


def hold_absent(s):
    s.holds_file.unlink()


def hold_unparsable(s):
    s.holds_file.write_text("[")


def inbox_absent(s):
    for path in s.inbox.iterdir():
        path.unlink()
    s.inbox.rmdir()


FAULTS = [
    ("board-incomplete", board_incomplete, SwallowBoardFailure),
    ("board-non-issue-item", board_non_issue, IgnoreNonIssueItems),
    ("state-file-missing", state_missing, DefaultMissingState),
    ("state-file-unparsable", state_unparsable, DefaultMissingState),
    ("hold-record-absent", hold_absent, DefaultMissingHolds),
    ("hold-record-unparsable", hold_unparsable, DefaultMissingHolds),
    ("inbox-directory-absent", inbox_absent, DefaultMissingInbox),
]


def fails_closed(tmp_path: Path, fault, cls) -> bool:
    """The criterion-2 check: not authoritative, host idles AUTHORITATIVE_STATE_UNAVAILABLE, no launch."""
    s = Sources(tmp_path)
    s.issue(1, "READY")  # control would otherwise be required, so a permissive adapter launches
    s.board_reader_override = None
    fault(s)
    adapter = s.adapter(cls)
    if s.board_reader_override is not None:
        adapter.board_reader = s.board_reader_override
    launcher = InMemoryDirectorLauncher()
    service = FactoryDirectorHost(tmp_path / "host", adapter, launcher)
    result = service.reconcile()
    projected = JsonDirectorInputs(s.projection)()
    return (result.reason == "AUTHORITATIVE_STATE_UNAVAILABLE" and launcher.launched == []
            and projected.authoritative_state is False and not projected.control_required())


@pytest.mark.parametrize("name,fault,broken", FAULTS, ids=[f[0] for f in FAULTS])
def test_malformed_or_unavailable_source_fails_closed(tmp_path, name, fault, broken):
    assert fails_closed(tmp_path / "real", fault, AuthoritativeDirectorInputs)


@pytest.mark.parametrize("name,fault,broken", FAULTS, ids=[f[0] for f in FAULTS])
def test_negative_control_the_same_check_fails_against_a_broken_adapter(tmp_path, name, fault, broken):
    assert not fails_closed(tmp_path / "broken", fault, broken)


@pytest.mark.parametrize("fault", [
    lambda s: s.board.append({"id": "dup", "type": "ISSUE", "issue": 1, "status": "READY"}),
    lambda s: s.board.append({"id": "nostatus", "type": "ISSUE", "issue": 20, "status": None}),
    lambda s: s.board.append({"id": "odd", "type": "ISSUE", "issue": 21, "status": "SHIPPED"}),
    lambda s: s.self_hosting.unlink(),
    lambda s: s.config.unlink(),
    lambda s: s.config.write_text(json.dumps({**json.loads(s.config.read_text()), "wipLimit": 0})),
    lambda s: s.config.write_text(json.dumps({**json.loads(s.config.read_text()), "directorInbox": "rel"})),
    lambda s: s.self_hosting.write_text(json.dumps({**json.loads(s.self_hosting.read_text()),
                                                    "project": {"owner": "AlienLogicLab", "number": 2}})),
    lambda s: s.state_file.write_text(json.dumps({"deliveries": {}})),
    lambda s: s.state_file.write_text(json.dumps({"active": {"x#1:PRODUCER": {"item": {"repository": "x"}}}})),
    lambda s: s.state_file.write_text(json.dumps({"active": {}, "limitEscalations": {"k": "v"}})),
    lambda s: s.holds_file.write_text(json.dumps({"schemaVersion": 1, "holds": [{"issue": 1}]})),
    lambda s: s.holds_file.write_text(json.dumps({"schemaVersion": 1, "holds": [
        {"issue": 1, "reason": "a"}, {"issue": 1, "reason": "b"}]})),
    lambda s: s.holds_file.write_text(json.dumps({"schemaVersion": 2, "holds": []})),
    lambda s: s.holds_file.write_text(json.dumps({"schemaVersion": 1, "holds": [], "note": "x"})),
    lambda s: (s.inbox / "processed").write_text("not a directory"),
    lambda s: (s.board.append({"id": "t", "type": "ISSUE", "issue": 22, "status": "TASKS"}),
               s.comments.__setitem__(22, [comment("<!-- AGENT_READY_ASSESSMENT: {broken -->", OPERATOR)])),
    lambda s: s.board.append({"id": "x", "type": "ISSUE", "issue": 24, "status": "READY",
                              "repository": "Other/repo"}),
    lambda s: s.board.append({"id": "y", "type": "ISSUE", "issue": 25, "status": "READY"}),
    lambda s: (s.inbox / "Founder note.json").write_text("{}"),
], ids=["duplicate-item", "item-without-status", "unknown-status", "self-hosting-missing",
        "host-config-missing", "wip-limit-invalid", "relative-source-path", "wrong-project",
        "state-without-active", "inconsistent-claim", "malformed-escalation", "hold-without-reason",
        "duplicate-hold", "hold-schema-version", "hold-unknown-key", "processed-not-directory",
        "unparsable-assessment", "foreign-repository-item", "item-without-repository",
        "unrecognised-inbox-json"])
def test_other_inconsistent_sources_also_fail_closed(tmp_path, fault):
    assert fails_closed(tmp_path, fault, AuthoritativeDirectorInputs)


def test_comment_reader_failure_fails_closed(sources):
    sources.issue(23, "TASKS")
    adapter = sources.adapter()

    def failing(issue):
        raise materialization.MaterializationFailed("gh api graphql failed")
    adapter.comments_reader = failing
    assert adapter().authoritative_state is False


# --- criterion 3: Founder holds and the Director inbox drive the host ---------------------

def reconcile(sources):
    launcher = InMemoryDirectorLauncher()
    result = FactoryDirectorHost(sources.root / "host", sources.adapter(), launcher).reconcile()
    return result, launcher


def test_hold_on_some_ready_items_does_not_idle_while_another_ready_item_is_unheld(sources):
    sources.issue(30, "READY").issue(31, "READY").issue(32, "READY").hold(30).hold(31)
    result, launcher = reconcile(sources)
    assert result.reason == "DIRECTOR_CONTINUITY_FAULT" and len(launcher.launched) == 1


def test_all_eligible_items_held_idles_founder_decision_pending(sources):
    sources.issue(30, "READY").issue(31, "READY").hold(30).hold(31)
    result, launcher = reconcile(sources)
    assert (result.reason, result.state) == ("FOUNDER_DECISION_PENDING", HostState.IDLE)
    assert launcher.launched == []


def test_held_unclaimed_implement_issue_does_not_make_control_required(sources):
    sources.issue(33, "IMPLEMENT").hold(33)
    values = sources.inputs()
    assert not values.control_required()
    result, launcher = reconcile(sources)
    assert result.reason == "FOUNDER_DECISION_PENDING" and launcher.launched == []


def test_pending_inbox_entry_launches_despite_holds_and_its_receipt_stops_it(sources):
    sources.issue(34, "READY").hold(34).inbox_entry("founder-2026-09-24")
    result, launcher = reconcile(sources)
    assert result.reason == "DIRECTOR_CONTINUITY_FAULT" and len(launcher.launched) == 1

    sources.inbox_entry("founder-2026-09-24", receipt=True)
    for path in (sources.root / "host").iterdir():
        path.unlink()
    result, launcher = reconcile(sources)
    assert result.reason == "FOUNDER_DECISION_PENDING" and launcher.launched == []


def test_escalation_is_never_suppressed_by_a_hold(sources):
    sources.issue(35, "READY").hold(35).escalate(35)
    values = sources.inputs()
    assert (values.attention_required, values.founder_decision_pending) == (True, False)


@pytest.mark.parametrize("state,claimed", [("TASKS", False), ("READY", False), ("IMPLEMENT", False),
                                           ("IMPLEMENT", True), ("VERIFY", False), ("REVIEW", False),
                                           ("ACCEPT", False), ("ACCEPT", True)])
def test_a_hold_covers_an_issue_in_every_lifecycle_state(sources, state, claimed):
    sources.issue(36, state).hold(36)
    sources.comments[36] = [ASSESSMENT]
    if claimed:
        sources.claim(36)
    values = sources.inputs()
    assert (values.eligible_authorized_work, values.lifecycle_requires_selection) == (False, False)


def test_hold_on_an_issue_that_needs_no_control_is_not_a_pending_founder_decision(sources):
    sources.issue(37, "IMPLEMENT").claim(37).hold(37)
    values = sources.inputs()
    assert (values.founder_decision_pending, values.control_required()) == (False, False)


def test_receipt_without_entry_is_ignored_and_partial_files_are_not_entries(sources):
    (sources.inbox / "processed").mkdir()
    (sources.inbox / "processed" / "orphan.json").write_text("{}")
    (sources.inbox / ".note.json.partial").write_text("{}")
    (sources.inbox / "note.json.partial").write_text("{}")
    (sources.inbox / "README.txt").write_text("")
    assert sources.inputs().pending_director_inbox is False


# --- publication and the read-only audit ---------------------------------------------------

def test_projection_is_published_atomically_and_reads_back_strictly(sources):
    sources.issue(40, "READY")
    values = sources.inputs()

    assert JsonDirectorInputs(sources.projection)() == values
    diagnostics = json.loads(sources.projection.with_name("inputs.diagnostics.json").read_text())
    assert diagnostics["failure"] is None
    assert diagnostics["observations"]["controlRequiredBy"] == {"40": "eligible:READY"}
    assert not list(sources.projection.parent.glob("*.partial"))


def test_failure_is_published_with_its_reason(sources):
    sources.holds_file.unlink()
    sources.inputs()
    diagnostics = json.loads(sources.projection.with_name("inputs.diagnostics.json").read_text())
    assert "Founder-hold record is absent" in diagnostics["failure"]


def snapshot(root: Path, exclude: Path) -> dict:
    return {str(path): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(root.rglob("*")) if path.is_file() and exclude not in path.parents}


def test_adapter_writes_nothing_but_its_own_projection(sources):
    sources.issue(41, "READY").issue(42, "TASKS").claim(43).hold(41).escalate(44).inbox_entry("e", receipt=True)
    sources.comments[42] = [ASSESSMENT]
    before = snapshot(sources.root, sources.projection.parent)

    sources.inputs()
    sources.inputs()

    assert snapshot(sources.root, sources.projection.parent) == before
    assert sorted(path.name for path in sources.projection.parent.iterdir()) == [
        "inputs.diagnostics.json", "inputs.json"]


def test_adapter_source_contains_no_github_write_or_issue_transition():
    source = Path(adapter_module.__file__).read_text()
    for forbidden in ("mutation", "item-edit", "item-add", "item-delete", '"create"', '"edit"', '"close"',
                      '"comment"', "--method", "-X", "materialize(", "set_status", "STATUS_OPTIONS["):
        assert forbidden not in source, forbidden
    assert source.count("_atomic_json(") == 3  # definition + projection + diagnostics


def test_default_board_reader_is_the_fail_closed_materialization_read_path():
    assert AuthoritativeDirectorInputs("/nonexistent").board_reader is materialization.read_board


def test_comment_reader_paginates_and_refuses_an_incomplete_answer(monkeypatch):
    def node(body, login="u"):
        return {"body": body, "author": {"login": login}, "editor": None}
    pages = [
        {"totalCount": 3, "pageInfo": {"hasNextPage": True, "endCursor": "c1"}, "nodes": [node("a"), node("b")]},
        {"totalCount": 3, "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": [node("c", None)]},
    ]
    calls = []

    def fake_gh(*args):
        calls.append(args)
        page = pages[len(calls) - 1]
        return json.dumps({"data": {"repository": {"issue": {"comments": page}}}})
    monkeypatch.setattr(materialization, "_gh", fake_gh)
    assert adapter_module.read_issue_comments(5) == [
        {"author": "u", "editor": None, "body": "a"}, {"author": "u", "editor": None, "body": "b"},
        {"author": None, "editor": None, "body": "c"}]
    assert all(call[:2] == ("api", "graphql") for call in calls)
    assert "cursor=c1" in calls[1]

    calls.clear()
    pages[1]["totalCount"] = pages[0]["totalCount"] = 4
    with pytest.raises(SourceUnavailable):
        adapter_module.read_issue_comments(5)


# --- repairs from independent review 1 ----------------------------------------------------

def acknowledge(sources, name):
    (sources.inbox / "escalations").mkdir(exist_ok=True)
    (sources.inbox / "escalations" / f"{name}.json").write_text("{}")


def test_escalation_is_resolved_by_a_director_receipt_for_that_exact_escalation(sources):
    sources.issue(50, "IMPLEMENT").claim(50).escalate(50)
    assert sources.inputs().attention_required is True
    entry = sources.state["limitEscalations"][f"{REPO}#50"]
    acknowledge(sources, adapter_module.escalation_receipt_id(f"{REPO}#50", entry))
    assert sources.inputs().attention_required is False
    # A newer escalation on the same BIU needs its own receipt.
    sources.escalate(50, at="2026-09-25T00:00:00.000Z")
    assert sources.inputs().attention_required is True


def test_escalation_for_an_issue_that_reached_done_is_resolved(sources):
    sources.issue(51, "DONE").escalate(51)
    assert sources.inputs().attention_required is False


def test_inbox_processed_receipt_does_not_acknowledge_an_escalation(sources):
    sources.escalate(55)
    entry = sources.state["limitEscalations"][f"{REPO}#55"]
    (sources.inbox / "processed").mkdir()
    (sources.inbox / "processed" / f"{adapter_module.escalation_receipt_id(f'{REPO}#55', entry)}.json").write_text("{}")
    assert sources.inputs().attention_required is True


def test_escalations_directory_that_is_not_a_directory_fails_closed(sources):
    (sources.inbox / "escalations").write_text("x")
    assert sources.inputs().authoritative_state is False


def test_escalation_receipt_is_not_an_unprocessed_inbox_entry(sources):
    sources.escalate(52)
    entry = sources.state["limitEscalations"][f"{REPO}#52"]
    acknowledge(sources, adapter_module.escalation_receipt_id(f"{REPO}#52", entry))
    values = sources.inputs()
    assert (values.attention_required, values.pending_director_inbox) == (False, False)


def test_assessment_marker_counts_only_from_an_authorized_operator(sources):
    sources.issue(53, "TASKS")
    sources.comments[53] = [comment(ASSESSMENT_BODY, author="drive-by")]
    assert sources.inputs().lifecycle_requires_selection is False
    sources.comments[53].append(ASSESSMENT)
    assert sources.inputs().lifecycle_requires_selection is True


def test_malformed_marker_from_an_unauthorized_author_is_ignored_not_fatal(sources):
    sources.issue(54, "TASKS")
    sources.comments[54] = [comment("quoting the format: <!-- AGENT_READY_ASSESSMENT: {json} -->")]
    values = sources.inputs()
    assert (values.authoritative_state, values.lifecycle_requires_selection) == (True, False)


def test_unreadable_pause_location_fails_closed_rather_than_unpaused(sources):
    locked = sources.root / "locked"
    locked.mkdir()
    config = json.loads(sources.config.read_text())
    config["pauseFlag"] = str(locked / "PAUSE")
    sources.config.write_text(json.dumps(config))
    locked.chmod(0)
    try:
        assert sources.inputs().authoritative_state is False
    finally:
        locked.chmod(0o755)


def test_board_rows_from_the_read_path_carry_the_issue_repository():
    rows = materialization.board_from_payload({
        "totalCount": 1, "pageInfo": {"hasNextPage": False},
        "nodes": [{"id": "PVTI_1", "type": "ISSUE", "fieldValueByName": {"name": "READY"},
                   "content": {"__typename": "Issue", "number": 7,
                               "repository": {"nameWithOwner": REPO}}}]})
    assert rows == [{"id": "PVTI_1", "type": "ISSUE", "issue": 7, "status": "READY", "repository": REPO}]
    assert "repository{nameWithOwner}" in Path(materialization.__file__).read_text()


def test_marker_in_an_operator_comment_edited_by_someone_else_is_ignored(sources):
    sources.issue(56, "TASKS")
    sources.comments[56] = [{**ASSESSMENT, "editor": "morty-worker"}]
    assert sources.inputs().lifecycle_requires_selection is False
    sources.comments[56] = [{**ASSESSMENT, "editor": OPERATOR}]
    assert sources.inputs().lifecycle_requires_selection is True
