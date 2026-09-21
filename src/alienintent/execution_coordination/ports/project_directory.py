"""Projects v2 read and fenced projection-write boundary for one exact Project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


class ProjectUnavailable(RuntimeError):
    """The Project could not be reached or answered incompletely."""


class ProjectRejected(ValueError):
    """The Project answer cannot safely become a read or the target of a write."""


@dataclass(frozen=True)
class ProjectSchema:
    project_id: str
    project_number: int
    title: str
    status_field_id: str
    status_options: Mapping[str, str]
    priority_field_id: str
    priority_options: Mapping[str, str]


@dataclass(frozen=True)
class ProjectItemState:
    item_id: str
    status: str | None
    priority: str | None
    content_id: str | None
    # PY-10 needs three further observed facts to schedule live work. The
    # title and body carry the upstream BIU descriptor — its identity, the
    # contract document it was made READY against, that contract's digest at
    # that moment, and its dependency edges. The moment the Status value
    # itself last changed is the upstream READY-entry time the plan fixes as
    # the FIFO key. All default to absent, so a recorded fixture built from
    # the four PY-09B fields stays valid.
    title: str | None = None
    body: str | None = None
    status_updated_at: str | None = None


class ProjectDirectory(Protocol):
    def schema(self) -> ProjectSchema: ...
    def items(self) -> tuple[ProjectItemState, ...]: ...
    def read_status(self, item_id: str) -> ProjectItemState: ...
    def write_status(self, item_id: str, status: str, expected_revision: int) -> int: ...
