"""Rules for linking a work item to its one GitHub Issue and board card, and for its display text (`work link`,
`work display`).

The display text is rendered only from the stored row: the title is the label; the body starts with the marker that
lets a rerun find an Issue it created before a crash, names the item and points at its instructions. The text is a
display only: the instructions are the Git file at the stored commit. Everything here is pure.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from alienintent.context_assembly.domain.work_identity import WorkIdentityRefused, WorkItem

MARKER_NAME = "alienintent-work-item"
# The GitHub App installation must grant both; anything less is PERMISSION_MISSING and nothing is written.
REQUIRED_PERMISSIONS = (("issues", "write"), ("organization_projects", "write"))
# Answers `work link` and `work display` return instead of linking or displaying.
UNKNOWN_IDENTITY, IDENTITY_RETIRED = "UNKNOWN_IDENTITY", "IDENTITY_RETIRED"
ITEM_ALREADY_LINKED, ISSUE_ALREADY_LINKED = "ITEM_ALREADY_LINKED", "ISSUE_ALREADY_LINKED"
ISSUE_NOT_FOUND, PERMISSION_MISSING = "ISSUE_NOT_FOUND", "PERMISSION_MISSING"
NOT_LINKED, DISPLAY_NOT_CONFIRMED = "NOT_LINKED", "DISPLAY_NOT_CONFIRMED"
UNCHANGED, UPDATED = "unchanged", "updated"


class ItemAlreadyLinked(WorkIdentityRefused):
    """The item gained a link before this one was stored."""
    code = ITEM_ALREADY_LINKED


class IssueAlreadyLinked(WorkIdentityRefused):
    """The Issue is already linked to another item (the unique index refused it)."""
    code = ISSUE_ALREADY_LINKED


@dataclass(frozen=True)
class Display:
    title: str
    body: str


@dataclass(frozen=True)
class LinkResult:
    """What `work link` and `work display` answer. `answer` is None when the item is linked (and, for `display`, its
    text confirmed); otherwise it is the refusal code. `closed` lists duplicate Issues this run closed."""
    identity: str
    answer: str | None = None
    issue_number: int | None = None
    issue_node_id: str | None = None
    card_id: str | None = None
    closed: tuple[int, ...] = ()
    display: str | None = None
    detail: str = ""


def marker(identity: str) -> str:
    return f"<!-- {MARKER_NAME}: {identity} -->"


def render(item: WorkItem, cycles: tuple[int | None, int | None] | None = None) -> Display:
    """Title and body from the stored row only; an item with no pointer has no `Instructions` line. `cycles` are the
    IMPLEMENT and VERIFY cycle counts of the coordinator's recorded state, given only when that state exists; a
    count that is None is shown as `unknown`."""
    lines = [marker(item.id), f"Work item `{item.label}` (`{item.id}`)"]
    if item.pointer is not None:
        lines.append(f"Instructions: `{item.pointer.repo}/{item.pointer.path}` at `{item.pointer.commit}`")
    lines.append("This text is a display only. The instructions are that file at that commit.")
    if cycles is not None:
        implement, verify = ("unknown" if count is None else count for count in cycles)
        lines.append(f"IMPLEMENT cycles: {implement} · VERIFY cycles: {verify}")
    return Display(item.label, "\n".join(lines))


def body_of(issue: Mapping[str, object]) -> str:
    body = issue.get("body")
    return body if isinstance(body, str) else ""


def first_line(body: str) -> str:
    lines = body.splitlines()
    return lines[0] if lines else ""


def creator(issue: Mapping[str, object]) -> str | None:
    user = issue.get("user")
    login = user.get("login") if isinstance(user, Mapping) else None
    return login if isinstance(login, str) else None


def app_login(application: Mapping[str, object]) -> str:
    """The App's own Issue author login: `<slug>[bot]`."""
    slug = application.get("slug")
    if not isinstance(slug, str) or not slug:
        raise ValueError("GitHub App answer names no slug")
    return f"{slug}[bot]"


def _named(issue: Mapping[str, object]) -> bool:
    return isinstance(issue.get("number"), int) and isinstance(issue.get("node_id"), str)


def adoptable(issue: Mapping[str, object], identity: str, login: str) -> bool:
    """An open Issue the App created whose first body line is this item's marker (section 5 step 4)."""
    return _named(issue) and issue.get("state") == "open" and creator(issue) == login \
        and first_line(body_of(issue)) == marker(identity)


def duplicate(issue: Mapping[str, object], identity: str, login: str, linked_number: int) -> bool:
    """Every safe check on the GitHub side for closing a duplicate (section 5 step 7): open, not the linked Issue,
    created by the App, first line is this item's marker and no other marker appears anywhere in the body. Whether
    another item links it is the caller's `find_by_issue` check."""
    body = body_of(issue)
    return _named(issue) and issue.get("state") == "open" and issue.get("number") != linked_number \
        and creator(issue) == login \
        and first_line(body) == marker(identity) and body.count(MARKER_NAME) == 1


def duplicate_line(linked_number: int) -> str:
    return f"Duplicate of #{linked_number}; closed by AlienIntent work link."


def closing_body(body: str, linked_number: int) -> str:
    """The duplicate's body ending with the line naming the linked Issue."""
    line = duplicate_line(linked_number)
    return body if body.endswith(line) else f"{body.rstrip()}\n\n{line}"


def missing_permissions(granted: Mapping[str, object]) -> tuple[str, ...]:
    """Each required grant GitHub does not report at `write` (or the higher `admin`)."""
    return tuple(f"{name}: {level}" for name, level in REQUIRED_PERMISSIONS
                 if granted.get(name) not in (level, "admin"))
