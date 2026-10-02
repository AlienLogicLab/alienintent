"""`work link` and `work display` over the real work registry, adapters and credential, with GitHub replaced by a
recorded transport that keeps Issues and board cards (acceptance checks 1-6).

The work database, clone and bare remote are temporary; the repository, board, App and every identity are the
synthetic fixtures of tests/support/live_github.py. Faults are injected deterministically at named GitHub steps.
"""
from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import sqlite3

import pytest

from alienintent.composition.work_registry import WorkRegistry, project_configuration
from alienintent.context_assembly.domain.work_identity import RegistryBusy
from alienintent.context_assembly.domain.work_link import duplicate, duplicate_line, marker, render
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.project_directory import ProjectUnavailable
from alienintent.execution_coordination.ports.repository_directory import RepositoryUnavailable
from alienintent.installation.ports.github_transport import TransportResponse
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, project_clone
from tests.context_assembly.test_work_identity_service import commit_file
from tests.support.disposable_rsa import disposable_private_key
from tests.support.live_github import (
    LEAST_PRIVILEGE, PRIORITY_FIELD, SANDBOX_PROJECT, SANDBOX_REPOSITORY, STATUS_FIELD, RecordedTransport,
    rest_answers)

APP = "recorded-app[bot]"  # rest_answers' App slug `recorded-app`
GRANTED = LEAST_PRIVILEGE | {"issues": "write", "organization_projects": "write"}
ISSUES = f"/repos/{SANDBOX_REPOSITORY}/issues"
PACKET = b"# Work unit: fixture\n\nDo exactly this.\n"
WRITES = {"create", "update", "close", "add", "delete"}


class RecordedGitHub(RecordedTransport):
    """The recorded App and installation answers, plus Issues and board cards that remember what was written.

    `faults[label]` answers that step once with a failure; `hooks[label]` runs once just before that step (to
    interleave a second run deterministically). Every Issue or board operation is logged in `log` by label."""

    def __init__(self, permissions: dict[str, str] | None = None) -> None:
        super().__init__(rest_answers(installation_permissions=GRANTED if permissions is None else permissions,
                                      expires_at="2099-01-01T00:00:00Z"), self._board)
        self.issues: dict[int, dict] = {}
        self.cards: dict[str, str] = {}  # card id -> Issue node id
        self.log: list[str] = []
        self.faults: dict[str, int] = {}
        self.hooks: dict[str, Callable[[], object]] = {}
        self.ignore_updates = False
        self._next_card = 0

    # --- seeding and inspection --------------------------------------------------------------------------------

    def seed(self, body: str, *, login: str = APP, state: str = "open", title: str = "seeded",
             pull_request: bool = False) -> int:
        number = len(self.issues) + 1
        self.issues[number] = {"number": number, "node_id": f"I_fixture_{number}", "title": title, "body": body,
                               "state": state, "state_reason": None, "user": {"login": login},
                               **({"pull_request": {"url": "x"}} if pull_request else {})}
        return number

    def card_for(self, number: int) -> str | None:
        node = self.issues[number]["node_id"]
        return next((card for card, content in self.cards.items() if content == node), None)

    def writes(self) -> list[str]:
        return [label for label in self.log if label in WRITES]

    # --- transport ---------------------------------------------------------------------------------------------

    def _step(self, label: str) -> bool:
        """Log the step, run its hook, and answer True when a fault is injected here."""
        if label in self.hooks:
            self.hooks.pop(label)()
        self.log.append(label)
        if self.faults.get(label):
            self.faults[label] -= 1
            return True
        return False

    def request(self, method: str, url: str, headers, body: bytes | None = None) -> TransportResponse:
        if ISSUES not in url:
            return super().request(method, url, headers, body)
        self.calls.append((method, url))
        rest = url.split(ISSUES, 1)[1]
        payload = json.loads(body) if body else {}
        if method == "GET" and rest.startswith("?"):
            assert rest == "?state=all&sort=created&direction=desc&per_page=100"
            self.log.append("list")
            return _answer(200, [dict(i) for _, i in sorted(self.issues.items(), reverse=True)][:100])
        if method == "POST" and rest == "":
            if self._step("create"):
                return _answer(500, {"message": "fault"})
            number = self.seed(payload["body"], title=payload["title"])
            return _answer(201, self.issues[number])
        number = int(rest.lstrip("/"))
        if number not in self.issues:
            self.log.append("get-missing")
            return _answer(404, {"message": "Not Found"})
        issue = self.issues[number]
        if method == "GET":
            self.log.append("get")
            return _answer(200, issue)
        assert method == "PATCH"
        if "state" in payload:
            if self._step("close"):
                return _answer(500, {"message": "fault"})
            issue.update(state=payload["state"], state_reason=payload["state_reason"], body=payload["body"])
        else:
            if self._step("update"):
                return _answer(500, {"message": "fault"})
            if not self.ignore_updates:
                issue.update(title=payload["title"], body=payload["body"])
        return _answer(200, issue)

    def _board(self, query: str, variables: dict) -> object:
        project = {"id": SANDBOX_PROJECT, "number": 2}
        if "addProjectV2ItemById" in query:
            if self._step("add"):
                return {"errors": [{"message": "fault"}]}
            assert variables["project"] == SANDBOX_PROJECT
            content = variables["content"]
            card = next((c for c, held in self.cards.items() if held == content), None)
            if card is None:
                self._next_card += 1
                card = f"PVTI_fixture_{self._next_card}"
                self.cards[card] = content
            return {"data": {"addProjectV2ItemById": {"item": {"id": card, "project": project}}}}
        if "deleteProjectV2Item" in query:
            if self._step("delete"):
                return {"errors": [{"message": "fault"}]}
            self.cards.pop(variables["item"], None)
            return {"data": {"deleteProjectV2Item": {"deletedItemId": variables["item"]}}}
        if "ProjectV2Item { id project" in query:
            if self._step("read-card"):
                return {"errors": [{"message": "fault"}]}
            content = self.cards.get(variables["item"])
            return {"data": {"node": {"id": variables["item"], "project": project,
                                      "content": {"id": content} if content else None, "fieldValues": {"nodes": []}}}}
        self.log.append("other-graphql")
        return {"data": {}}


def _answer(status: int, document: object) -> TransportResponse:
    return TransportResponse(status, json.dumps(document).encode())


class Linked:
    """A fixture project with the `github` entry, its registry over the recorded GitHub, and registered items."""

    def __init__(self, root: Path, permissions: dict[str, str] | None = None) -> None:
        root.mkdir()
        SQLiteOperationalStore(root / "fx.sqlite")
        self.clone, _ = project_clone(root)
        (root / "key.pem").write_bytes(disposable_private_key())
        self.document = {"schema_version": 1, "projects": {PROJECT: {
            "database": str(root / "work.sqlite"),
            "repositories": {REPO: {"clone": str(self.clone), "remote": "origin", "default_branch": "main",
                                    "packets_branch": "alienintent/work-packets"}},
            "packets": {"repository": REPO, "directory": "work-packets"},
            "profiles": {"fx": str(root / "fx.sqlite")},
            "github": {"repository": SANDBOX_REPOSITORY, "application_id": 1000001, "installation_id": 2000002,
                       "private_key_path": str(root / "key.pem"),
                       "project": {"project_id": SANDBOX_PROJECT, "project_number": 2,
                                   "organization": "AlienLogicLab", "status_field_id": STATUS_FIELD,
                                   "priority_field_id": PRIORITY_FIELD}}}}}
        self.github = RecordedGitHub(permissions)
        self.registry = WorkRegistry(project_configuration(self.document, PROJECT), transport=self.github)
        self.links, self.database = self.registry.links, root / "work.sqlite"

    def item(self, label: str):
        path = f"docs/{label}.md"
        packet = PACKET + label.encode()
        return self.registry.records.register(packet, REPO, path, commit_file(self.clone, "main", path, packet), label)

    def stored(self, label: str):
        return self.registry.records.show(label).item


@pytest.fixture
def fx(tmp_path) -> Linked:
    return Linked(tmp_path / "fx")


def issue_count(fx: Linked) -> int:
    return sum(1 for issue in fx.github.issues.values() if "pull_request" not in issue)


# --- check 1: create and link -------------------------------------------------------------------------------------


def test_an_unlinked_item_gets_one_rendered_issue_and_one_card_and_a_repeat_changes_nothing(fx):
    item = fx.item("X")
    result = fx.links.link("X")
    assert result.answer is None and result.closed == () and result.display == "unchanged"
    [number] = fx.github.issues
    issue = fx.github.issues[number]
    assert (issue["title"], issue["body"]) == (render(item).title, render(item).body) == ("X", "\n".join((
        marker(item.id), f"Work item `X` (`{item.id}`)",
        f"Instructions: `{REPO}/docs/X.md` at `{item.pointer.commit}`",
        "This text is a display only. The instructions are that file at that commit.")))
    assert fx.github.cards == {result.card_id: issue["node_id"]}
    stored = fx.stored("X")
    assert (stored.issue_number, stored.issue_node_id, stored.card_id) == (
        number, issue["node_id"], result.card_id) == (result.issue_number, result.issue_node_id, result.card_id)
    # Every write was read back: the Issue after creating it, the card after adding it.
    assert fx.github.log[fx.github.log.index("create") + 1] == "get"
    assert fx.github.log[fx.github.log.index("add") + 1] == "read-card"
    rows = sqlite3.connect(fx.database).execute("SELECT * FROM work_item").fetchall()
    fx.github.log.clear()
    again = fx.links.link(item.id)
    assert again == result and fx.github.writes() == [] and issue_count(fx) == 1
    assert sqlite3.connect(fx.database).execute("SELECT * FROM work_item").fetchall() == rows


def test_an_item_without_a_pointer_renders_without_the_instructions_line(fx):
    from dataclasses import replace
    item = replace(fx.item("X"), pointer=None)
    assert "Instructions:" not in render(item).body and render(item).body.startswith(marker(item.id) + "\n")


def test_an_unknown_or_retired_item_is_answered_without_any_github_request(fx):
    item = fx.item("X")
    fx.registry.identities.retire(item.id)
    assert fx.links.link("missing").answer == "UNKNOWN_IDENTITY"
    assert fx.links.link("X").answer == "IDENTITY_RETIRED"
    assert fx.links.display("missing").answer == "UNKNOWN_IDENTITY"
    assert fx.github.calls == []


# --- check 2: one-to-one, and the cleanup of duplicates ----------------------------------------------------------


def test_an_issue_linked_to_another_item_or_a_second_issue_for_a_linked_item_is_refused(fx):
    fx.item("X"), fx.item("Y")
    linked = fx.links.link("X")
    refused = fx.links.link("Y", linked.issue_number)
    assert (refused.answer, refused.issue_number) == ("ISSUE_ALREADY_LINKED", None)
    assert fx.stored("Y").issue_number is None and issue_count(fx) == 1
    other = fx.github.seed("a human issue", login="founder")
    fx.github.log.clear()
    second = fx.links.link("X", other)
    assert (second.answer, second.issue_number) == ("ITEM_ALREADY_LINKED", linked.issue_number)
    assert fx.github.log == [] and fx.stored("X").issue_number == linked.issue_number


def test_two_runs_for_two_items_naming_the_same_issue_end_with_one_link(fx):
    fx.item("X"), fx.item("Y")
    shared = fx.github.seed("shared", login="founder")
    answers = {}
    fx.github.hooks["add"] = lambda: answers.setdefault("Y", fx.links.link("Y", shared))
    answers["X"] = fx.links.link("X", shared)
    assert answers["Y"].answer is None and answers["X"].answer == "ISSUE_ALREADY_LINKED"
    assert fx.stored("Y").issue_number == shared and fx.stored("X").issue_number is None
    assert issue_count(fx) == 1 and len(fx.github.cards) == 1


def test_two_runs_for_one_item_end_with_one_link_and_the_loser_closes_its_own_issue(fx):
    item = fx.item("X")
    answers = {}
    fx.github.hooks["create"] = lambda: answers.setdefault("winner", fx.links.link("X"))
    loser = fx.links.link("X")
    winner = answers["winner"]
    assert winner.answer is None and loser.answer == "ITEM_ALREADY_LINKED"
    assert loser.issue_number == winner.issue_number == fx.stored("X").issue_number
    [duplicate] = [n for n in fx.github.issues if n != winner.issue_number]
    assert loser.closed == (duplicate,)
    closed = fx.github.issues[duplicate]
    assert (closed["state"], closed["state_reason"]) == ("closed", "not_planned")
    assert closed["body"] == f"{render(item).body}\n\n{duplicate_line(winner.issue_number)}"
    assert fx.github.card_for(duplicate) is None and fx.github.card_for(winner.issue_number) == winner.card_id
    assert fx.github.issues[winner.issue_number]["state"] == "open"


UNSAFE = {
    "not created by the App": lambda fx, item: fx.github.seed(marker(item.id) + "\nbody", login="someone"),
    "the linked Issue": lambda fx, item: fx.stored("X").issue_number,
    "linked to another item": lambda fx, item: _linked_elsewhere(fx, item),
    "a second, conflicting marker": lambda fx, item: fx.github.seed(
        marker(item.id) + "\n" + "<!-- alienintent-work-item: other -->"),
    "a marker not on the first line": lambda fx, item: fx.github.seed("text\n" + marker(item.id)),
    "another item's marker": lambda fx, item: fx.github.seed(marker("someone-else") + "\nbody"),
    "already closed": lambda fx, item: fx.github.seed(marker(item.id) + "\nbody", state="closed"),
    "a pull request": lambda fx, item: fx.github.seed(marker(item.id) + "\nbody", pull_request=True),
}


def _linked_elsewhere(fx: Linked, item) -> int:
    """An App Issue carrying X's marker that the database links to Y (as `work link Y --issue n` stores it)."""
    number = fx.github.seed(marker(item.id) + "\nbody")
    fx.registry.items.set_link(fx.item("Y").id, number, f"I_fixture_{number}", "PVTI_elsewhere")
    return number


@pytest.mark.parametrize("case", sorted(UNSAFE))
def test_cleanup_never_touches_an_issue_failing_a_safe_check(fx, case):
    """Step 7's safe checks: each Issue here carries this item's marker (or is the linked one) yet must be left
    exactly as it is: no card added or removed, no close, no body change."""
    item = fx.item("X")
    fx.links.link("X")
    number = UNSAFE[case](fx, item)
    before = json.dumps(fx.github.issues, sort_keys=True)
    fx.github.log.clear()
    result = fx.links.link("X")
    assert result.answer is None and result.closed == ()
    assert fx.github.writes() == [] and json.dumps(fx.github.issues, sort_keys=True) == before
    assert number not in result.closed


SAFE = {"number": 4, "node_id": "I_4", "state": "open", "user": {"login": APP}, "body": marker("x") + "\nbody"}


@pytest.mark.parametrize("change", [{}, {"number": 1}, {"state": "closed"}, {"user": {"login": "someone"}},
                                    {"body": "text\n" + marker("x")}, {"body": marker("y") + "\nbody"},
                                    {"body": marker("x") + "\n" + marker("y")}, {"node_id": None}])
def test_each_github_side_safe_check_alone_refuses_a_duplicate(change):
    """Each condition of step 7 on its own: the unchanged Issue is a duplicate of x linked to #1; any one change
    (the linked number, closed, another creator, marker not first, another item's, a second marker) is not."""
    assert duplicate(SAFE | change, "x", APP, 1) is (change == {})


def test_a_safe_duplicate_is_closed_after_its_card_is_removed(fx):
    item = fx.item("X")
    linked = fx.links.link("X")
    number = fx.github.seed(marker(item.id) + "\nleft by a crashed run")
    fx.github.log.clear()
    result = fx.links.link("X")
    assert result.closed == (number,) and fx.github.writes() == ["add", "delete", "close"]
    assert fx.github.issues[number]["body"].endswith("\n" + duplicate_line(linked.issue_number))
    assert fx.github.card_for(number) is None


def test_an_interrupted_cleanup_is_finished_by_the_rerun_and_then_nothing_is_written(fx):
    item = fx.item("X")
    linked = fx.links.link("X")
    number = fx.github.seed(marker(item.id) + "\nleft by a crashed run")
    fx.github.faults["close"] = 1  # The card is removed, then closing fails.
    with pytest.raises(RepositoryUnavailable) as failed:
        fx.links.link("X")
    assert "work link step: cleanup" in failed.value.__notes__
    assert fx.github.issues[number]["state"] == "open" and fx.github.card_for(number) is None
    rerun = fx.links.link("X")
    assert rerun.closed == (number,) and fx.github.issues[number]["state"] == "closed"
    assert fx.github.issues[number]["body"].endswith(duplicate_line(linked.issue_number))
    fx.github.log.clear()
    assert fx.links.link("X").closed == () and fx.github.writes() == []


# --- check 3: crash recovery -------------------------------------------------------------------------------------


def test_a_fault_after_the_issue_is_created_is_recovered_by_adopting_it(fx):
    fx.item("X")
    fx.github.faults["add"] = 1
    with pytest.raises(ProjectUnavailable) as failed:
        fx.links.link("X")
    assert "work link step: card" in failed.value.__notes__
    assert fx.stored("X").issue_number is None and issue_count(fx) == 1
    [created] = fx.github.issues
    result = fx.links.link("X")
    assert result.issue_number == created and issue_count(fx) == 1 and fx.github.log.count("create") == 1


def test_a_fault_after_the_card_is_added_reuses_the_card(fx, monkeypatch):
    fx.item("X")
    original = fx.registry.items.set_link

    def busy_once(*args):
        monkeypatch.setattr(fx.registry.items, "set_link", original)
        raise RegistryBusy("work_item", "fault injected")
    monkeypatch.setattr(fx.registry.items, "set_link", busy_once)
    with pytest.raises(RegistryBusy):
        fx.links.link("X")
    [card] = fx.github.cards
    result = fx.links.link("X")
    assert result.card_id == card and list(fx.github.cards) == [card] and issue_count(fx) == 1
    assert fx.github.log.count("create") == 1


# --- check 4: an existing Issue ----------------------------------------------------------------------------------


def test_an_existing_issue_on_the_board_reuses_its_card_and_one_off_the_board_gets_one(fx):
    fx.item("X"), fx.item("Y")
    on_board, off_board = fx.github.seed("human", login="founder"), fx.github.seed("human", login="founder")
    fx.github.cards["PVTI_existing"] = fx.github.issues[on_board]["node_id"]
    assert fx.links.link("X", on_board).card_id == "PVTI_existing"
    added = fx.links.link("Y", off_board)
    assert added.card_id != "PVTI_existing" and fx.github.cards[added.card_id] == f"I_fixture_{off_board}"
    assert len(fx.github.cards) == 2 and issue_count(fx) == 2 and "create" not in fx.github.log


def test_a_missing_issue_or_a_pull_request_is_issue_not_found(fx):
    fx.item("X")
    pull = fx.github.seed("a pull request", pull_request=True)
    for number in (pull, 999):
        result = fx.links.link("X", number)
        assert (result.answer, result.detail) == ("ISSUE_NOT_FOUND", f"#{number}")
    assert fx.github.writes() == [] and fx.stored("X").issue_number is None


def test_an_issue_with_the_marker_not_created_by_the_app_is_not_adopted(fx):
    item = fx.item("X")
    foreign = fx.github.seed(marker(item.id) + "\nlooks like ours", login="someone")
    result = fx.links.link("X")
    assert result.issue_number != foreign and fx.github.log.count("create") == 1
    assert fx.github.issues[foreign]["state"] == "open" and fx.github.card_for(foreign) is None


def test_adoption_takes_the_newest_open_app_issue_and_closes_the_older_one(fx):
    item = fx.item("X")
    older = fx.github.seed(render(item).body, title="X")
    newer = fx.github.seed(render(item).body, title="X")
    result = fx.links.link("X")
    assert result.issue_number == newer and result.closed == (older,) and "create" not in fx.github.log


# --- check 5: display and repair ---------------------------------------------------------------------------------


def test_display_restores_an_edited_issue_with_one_write_and_otherwise_writes_nothing(fx):
    item = fx.item("X")
    linked = fx.links.link("X")
    packet = fx.registry.records.show("X").packet
    fx.github.issues[linked.issue_number].update(title="edited", body="edited on GitHub")
    fx.github.log.clear()
    shown = fx.links.display("X")
    assert (shown.answer, shown.display) == (None, "updated") and fx.github.writes() == ["update"]
    assert fx.github.log[fx.github.log.index("update") + 1] == "get"
    issue = fx.github.issues[linked.issue_number]
    assert (issue["title"], issue["body"]) == (render(item).title, render(item).body)
    fx.github.log.clear()
    assert fx.links.display("X").display == "unchanged" and fx.github.writes() == []
    record = fx.registry.records.show("X")
    assert record.item.pointer == item.pointer and record.packet == packet


def test_a_display_that_does_not_read_back_is_not_confirmed(fx):
    fx.item("X")
    linked = fx.links.link("X")
    fx.github.issues[linked.issue_number]["body"] = "edited"
    fx.github.ignore_updates = True
    fx.github.log.clear()
    shown = fx.links.display("X")
    assert (shown.answer, shown.detail, shown.display) == ("DISPLAY_NOT_CONFIRMED", "body", None)
    assert fx.github.writes() == ["update"]


def test_display_of_an_unlinked_item_is_not_linked(fx):
    fx.item("X")
    assert fx.links.display("X").answer == "NOT_LINKED" and fx.github.calls == []


# --- check 6: permissions and scope ------------------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["issues", "organization_projects"])
def test_a_missing_permission_is_answered_after_only_the_permission_read(tmp_path, missing):
    fx = Linked(tmp_path / "fx", GRANTED | {missing: "read"})
    fx.item("X")
    result = fx.links.link("X")
    assert (result.answer, result.detail) == ("PERMISSION_MISSING", f"{missing}: write")
    assert fx.github.calls == [("GET", "https://api.github.com/app/installations/2000002")]
    assert fx.stored("X").issue_number is None


def test_only_the_permitted_requests_are_sent(fx):
    item = fx.item("X")
    fx.links.link("X")
    fx.github.seed(marker(item.id) + "\nduplicate")
    fx.links.link("X")
    fx.links.display("X")
    permitted = {("GET", "https://api.github.com/app/installations/2000002"),
                 ("POST", "https://api.github.com/app/installations/2000002/access_tokens"),
                 ("GET", "https://api.github.com/app"), ("POST", "https://api.github.com/graphql"),
                 ("GET", f"https://api.github.com{ISSUES}?state=all&sort=created&direction=desc&per_page=100"),
                 ("POST", f"https://api.github.com{ISSUES}"),
                 *((method, f"https://api.github.com{ISSUES}/{n}") for method in ("GET", "PATCH") for n in (1, 2))}
    assert set(fx.github.calls) <= permitted
    # Board: only the card add, its read-back and the duplicate's removal; never a scan or a field write.
    assert set(fx.github.log) <= {"list", "create", "get", "add", "read-card", "delete", "close"}
    assert "other-graphql" not in fx.github.log
