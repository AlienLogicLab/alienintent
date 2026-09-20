"""Git worktree allocation with owner records and conservative cleanup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable
from alienintent.invocation_runtime.ports.workspace import Workspace, WorkspaceManager


@dataclass(frozen=True)
class GitWorkspace(Workspace):
    invocation_id: str
    owner: str
    path: Path
    branch: str


class GitWorktreeAdapter(WorkspaceManager):
    def __init__(self, repository: Path, root: Path) -> None:
        self._repository, self._root = repository.resolve(), root.resolve()

    def _git(self, *args: str, cwd: Path | None = None) -> None:
        result = subprocess.run(["git", *args], cwd=cwd or self._repository, capture_output=True, text=True, check=False)
        if result.returncode:
            raise CandidateUnavailable(result.stderr.strip() or "git worktree operation failed")

    def allocate(self, invocation_id: str, owner: str, baseline: str) -> GitWorkspace:
        if not invocation_id or not owner or any(part in invocation_id for part in ("/", "\\", "..", "\x00")):
            raise CandidateUnavailable("workspace identity is unsafe")
        path = self._root / invocation_id
        if path.exists():
            raise CandidateUnavailable("workspace is already allocated")
        self._root.mkdir(parents=True, exist_ok=True)
        branch = f"invocation/{invocation_id}"
        self._git("worktree", "add", "-b", branch, str(path), baseline)
        return GitWorkspace(invocation_id, owner, path, branch)

    def cleanup(self, workspace: Workspace, process_id: int | None) -> None:
        if not isinstance(workspace, GitWorkspace) or not workspace.path.is_relative_to(self._root):
            raise CandidateUnavailable("workspace ownership cannot be established")
        if process_id is not None and Path(f"/proc/{process_id}").exists():
            raise CandidateUnavailable("owned process is plausibly live; workspace retained")
        if not workspace.path.exists():
            return
        status = subprocess.run(["git", "status", "--porcelain"], cwd=workspace.path, text=True, capture_output=True, check=False)
        if status.returncode or status.stdout:
            raise CandidateUnavailable("workspace is not quiescent; retained for diagnosis")
        self._git("worktree", "remove", str(workspace.path))
