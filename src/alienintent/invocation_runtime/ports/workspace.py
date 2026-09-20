"""Owner-scoped isolated workspace boundary."""

from pathlib import Path
from typing import Protocol


class Workspace(Protocol):
    invocation_id: str
    owner: str
    path: Path


class WorkspaceManager(Protocol):
    def allocate(self, invocation_id: str, owner: str, baseline: str) -> Workspace: ...
    def cleanup(self, workspace: Workspace, process_id: int | None) -> None: ...
