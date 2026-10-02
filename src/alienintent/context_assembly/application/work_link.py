"""WorkLink: give a registered work item exactly one GitHub Issue and one board card, and write its display text
(`work link`, `work display`).

`link` uses the Issue named, adopts the Issue an interrupted run of this item created, or creates one; puts it on the
configured board; reads both back; stores the link once (one item per Issue, one Issue per item); closes any duplicate
a losing or crashed run left; and writes the display text. `display` writes the rendered title and body to the linked
Issue only when they differ, and reads them back. The display is never read to decide anything except the marker and
login match and the display comparison; the instructions are the Git file at the stored commit and never change here.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Protocol

from alienintent.context_assembly.application.work_registration import WorkRecordService
from alienintent.context_assembly.domain.work_identity import WorkItem
from alienintent.context_assembly.domain.work_link import (
    DISPLAY_NOT_CONFIRMED, IDENTITY_RETIRED, ISSUE_ALREADY_LINKED, ISSUE_NOT_FOUND, ITEM_ALREADY_LINKED, NOT_LINKED,
    PERMISSION_MISSING, UNCHANGED, UNKNOWN_IDENTITY, UPDATED, IssueAlreadyLinked, ItemAlreadyLinked, LinkResult,
    adoptable, app_login, body_of, closing_body, duplicate, missing_permissions, render)
from alienintent.context_assembly.ports.work_item_repository import WorkItemRepository
from alienintent.execution_coordination.ports.project_directory import ProjectDirectory, ProjectRejected
from alienintent.execution_coordination.ports.repository_directory import RepositoryDirectory, RepositoryRejected

# How many of the repository's newest Issues a rerun searches for this item's marker (no pagination).
RECENT_ISSUES = 100
# The note a failed step adds to the adapter's own typed error, naming the step.
STEP_NOTE = "work link step: "


class AppInstallation(Protocol):
    """The GitHub App installation credential as this service uses it (bound by composition)."""

    def granted_permissions(self) -> Mapping[str, str]: ...

    def application(self) -> Mapping[str, object]: ...


@contextmanager
def _step(name: str) -> Iterator[None]:
    """A failure keeps its own type and is marked with the step it stopped; nothing is stored for that step."""
    try:
        yield
    except Exception as error:
        error.add_note(STEP_NOTE + name)
        raise


class WorkLink:
    def __init__(self, records: WorkRecordService, items: WorkItemRepository, issues: RepositoryDirectory,
                 board: ProjectDirectory, app: AppInstallation) -> None:
        self.records, self.items, self.issues, self.board, self.app = records, items, issues, board, app

    def link(self, id_or_label: str, issue: int | None = None) -> LinkResult:
        record = self.records.show(id_or_label)
        if record is None:
            return LinkResult(id_or_label, UNKNOWN_IDENTITY)
        item = record.item
        if item.retired:
            return LinkResult(item.id, IDENTITY_RETIRED)
        if item.issue_number is not None:
            if issue is not None and issue != item.issue_number:
                return _linked(item, ITEM_ALREADY_LINKED, detail=f"linked to #{item.issue_number}")
            with _step("read back"):
                self._confirm(item)
            return self._finish(item)
        with _step("permissions"):
            missing = missing_permissions(self.app.granted_permissions())
        if missing:
            return LinkResult(item.id, PERMISSION_MISSING, detail=", ".join(missing))
        with _step("issue"):
            if issue is not None:
                try:
                    found = self.issues.issue(issue)
                except RepositoryRejected:
                    return LinkResult(item.id, ISSUE_NOT_FOUND, detail=f"#{issue}")
            else:
                found = self._adopt(item) or self._create(item)
        number, node_id = int(found["number"]), str(found["node_id"])
        with _step("card"):
            card = self._card(node_id)
        try:
            with _step("link"):
                linked = self.items.set_link(item.id, number, node_id, card)
        except IssueAlreadyLinked:
            return LinkResult(item.id, ISSUE_ALREADY_LINKED, detail=f"#{number}")
        except ItemAlreadyLinked:  # Another run linked the item first: clean up after it, then say so.
            current = self.records.show(item.id).item
            with _step("cleanup"):
                closed = self._cleanup(current)
            return _linked(current, ITEM_ALREADY_LINKED, closed=closed, detail=f"linked to #{current.issue_number}")
        return self._finish(linked)

    def display(self, id_or_label: str) -> LinkResult:
        record = self.records.show(id_or_label)
        if record is None:
            return LinkResult(id_or_label, UNKNOWN_IDENTITY)
        if record.item.issue_number is None:
            return LinkResult(record.item.id, NOT_LINKED)
        with _step("display"):
            return self._display(record.item)

    # --- steps -------------------------------------------------------------------------------------------------

    def _confirm(self, item: WorkItem) -> None:
        """A stored link is returned only after the Issue and the card read back as the ones stored."""
        if self.issues.issue(item.issue_number).get("node_id") != item.issue_node_id:
            raise RepositoryRejected(f"#{item.issue_number} is not the stored Issue")
        if self.board.read_status(item.card_id).content_id != item.issue_node_id:
            raise ProjectRejected("the stored card does not hold the stored Issue")

    def _adopt(self, item: WorkItem) -> Mapping[str, object] | None:
        """The newest open Issue the App created whose first body line is this item's marker (a crashed run's)."""
        login = app_login(self.app.application())
        return next((entry for entry in self.issues.recent_issues(RECENT_ISSUES) if adoptable(entry, item.id, login)),
                    None)

    def _create(self, item: WorkItem) -> Mapping[str, object]:
        rendered = render(item)
        number = int(self.issues.create_issue(rendered.title, rendered.body)["number"])
        created = self.issues.issue(number)
        if created.get("title") != rendered.title or body_of(created) != rendered.body:
            raise RepositoryRejected(f"#{number} did not read back with the rendered title and body")
        return created

    def _card(self, node_id: str) -> str:
        card = self.board.add_issue_item(node_id)
        if self.board.read_status(card).content_id != node_id:
            raise ProjectRejected("the card did not read back holding the Issue")
        return card

    def _finish(self, item: WorkItem) -> LinkResult:
        with _step("cleanup"):
            closed = self._cleanup(item)
        with _step("display"):
            shown = self._display(item)
        return LinkResult(item.id, shown.answer, item.issue_number, item.issue_node_id, item.card_id, closed,
                          shown.display, shown.detail)

    def _cleanup(self, item: WorkItem) -> tuple[int, ...]:
        """Close every other open duplicate of this item among the newest Issues (section 5 step 7): card removed
        first, then the Issue closed as not planned with a line naming the linked Issue. Anything that fails a
        safe check is left untouched; a closed duplicate is never touched again."""
        if item.issue_number is None:  # Without a stored link nothing can be a duplicate of it.
            return ()
        login, closed = app_login(self.app.application()), []
        for entry in self.issues.recent_issues(RECENT_ISSUES):
            if not duplicate(entry, item.id, login, item.issue_number):
                continue
            number = int(entry["number"])
            if self.items.find_by_issue(number) is not None:
                continue
            card = self.board.add_issue_item(str(entry["node_id"]))
            if self.board.delete_item(card) != card:
                raise ProjectRejected(f"the card of duplicate #{number} was not confirmed removed")
            body = closing_body(body_of(entry), item.issue_number)
            self.issues.close_issue(number, body)
            back = self.issues.issue(number)
            if back.get("state") != "closed" or body_of(back) != body:
                raise RepositoryRejected(f"duplicate #{number} did not read back closed")
            closed.append(number)
        return tuple(closed)

    def _display(self, item: WorkItem) -> LinkResult:
        """One write when the Issue's title or body differs from the rendered text, then read back."""
        rendered = render(item)
        current = self.issues.issue(item.issue_number)
        if current.get("title") == rendered.title and body_of(current) == rendered.body:
            return _linked(item, None, display=UNCHANGED)
        self.issues.update_issue(item.issue_number, rendered.title, rendered.body)
        back = self.issues.issue(item.issue_number)
        for field, value in (("title", back.get("title")), ("body", body_of(back))):
            if value != getattr(rendered, field):
                return _linked(item, DISPLAY_NOT_CONFIRMED, detail=field)
        return _linked(item, None, display=UPDATED)


def _linked(item: WorkItem, answer: str | None, closed: tuple[int, ...] = (), display: str | None = None,
            detail: str = "") -> LinkResult:
    return LinkResult(item.id, answer, item.issue_number, item.issue_node_id, item.card_id, closed, display, detail)
