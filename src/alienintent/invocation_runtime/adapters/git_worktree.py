"""Git worktree allocation with owner records and conservative cleanup.

With a worker user (unit WORKER-CREDENTIAL-BOUNDARY), `WorkerCloneAdapter` replaces the worktree: each role gets its
own clone created and removed by the worker user through the sudo rule, and the control plane runs no git inside it.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Mapping

from alienintent.invocation_runtime.adapters.cli_worker import run_as_worker
from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable, workspace_folder
from alienintent.invocation_runtime.ports.workspace import Workspace, WorkspaceManager

_REF_SAFE = re.compile(r"[^A-Za-z0-9._-]")
_FULL_SHA = re.compile(r"[0-9a-f]{40}")


def ref_safe(invocation_id: str) -> str:
    """A refname component Git will accept for this invocation identity.

    The coordinator correlates an invocation as `launch:<work>:<version>`, and
    Git refuses a refname containing `:`. Workspace folders use
    `workspace_folder`, the same rule; `allocate` and `_new` refuse a path that
    already exists, and a branch name that collides fails closed on
    `worktree add`, so a collision never quietly shares a folder or a branch.
    """
    return _REF_SAFE.sub("-", invocation_id).strip(".-") or "invocation"


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
            raise CandidateUnavailable("git worktree operation failed")

    def allocate(self, invocation_id: str, owner: str, baseline: str) -> GitWorkspace:
        if not invocation_id or not owner or any(part in invocation_id for part in ("/", "\\", "..", "\x00")):
            raise CandidateUnavailable("workspace identity is unsafe")
        path = self._root / workspace_folder(invocation_id)
        if path.exists():
            raise CandidateUnavailable("workspace is already allocated")
        self._root.mkdir(parents=True, exist_ok=True)
        branch = f"invocation/{ref_safe(invocation_id)}"
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

    def remove_branch(self, workspace: GitWorkspace) -> None:
        """`git branch -D` of a cleaned-up workspace's `invocation/...` branch in the repository."""
        if not workspace.branch.startswith("invocation/") or workspace.path.exists():
            raise CandidateUnavailable("workspace branch is not removable")
        self._git("branch", "-D", workspace.branch)


def _upload_pack(repository: Path) -> str:
    """The worker's upload-pack for a Founder-owned source `repository`, with git's ownership exception for that one
    repository given to upload-pack itself: `git -c safe.directory=...` on the worker's command line never reaches
    the check (live finding, check 8(e)). The worker only reads the source; nothing is trusted from the worker."""
    return f"--upload-pack=git -c safe.directory={shlex.quote(str(repository))} upload-pack"


def _safe_identity(invocation_id: str) -> bool:
    return bool(invocation_id) and not any(part in invocation_id for part in ("/", "\\", "..", "\x00")) \
        and not invocation_id.startswith("-")


class WorkerCloneAdapter(WorkspaceManager):
    """Worker-owned workspaces `<root>/<role>-<invocation>` (`root` is `<launch>/worker`), each created, filled and
    removed only by the worker user through the sudo rule; the control plane never runs git in one.

    The PRODUCER's clone is `git clone --no-local <packets clone>` (objects through the transport, as a pack) at the starting revision's full SHA; a VERIFIER
    or CLOSURE clone is `git init` and a fetch of one intake ref from the control-plane-owned intake repository, at
    the candidate's full SHA. Each allocation also creates the worker's `<results>/<invocation>/` folder (mode
    0755) for the files the session writes."""

    def __init__(self, packets: Path, root: Path, results: Path, user: str, environment: Mapping[str, str]) -> None:
        self._packets, self._root, self._results = Path(packets), Path(root).resolve(), Path(results)
        self._user, self._environment = user, dict(environment)

    def _worker(self, *argv: str) -> None:
        try:
            result = run_as_worker(self._user, self._environment, argv, cwd=self._root)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CandidateUnavailable(f"worker command failed: {type(error).__name__}") from error
        if result.returncode:
            raise CandidateUnavailable("worker workspace operation failed")

    def _new(self, prefix: str, invocation_id: str, owner: str, revision: str) -> Path:
        if not _safe_identity(invocation_id) or not owner or not _FULL_SHA.fullmatch(revision):
            raise CandidateUnavailable("workspace identity or revision is unsafe")
        path = self._root / f"{prefix}-{workspace_folder(invocation_id)}"
        if os.path.lexists(path):
            raise CandidateUnavailable("workspace is already allocated")
        self._worker("mkdir", "-m", "0755", "--", str(self._results / invocation_id))
        return path

    def allocate(self, invocation_id: str, owner: str, baseline: str) -> GitWorkspace:
        """The PRODUCER clone of the packets clone, checked out at `baseline` (a full SHA)."""
        path = self._new("producer", invocation_id, owner, baseline)
        self._worker("git", "clone", "-q", "--no-local", "--no-checkout", _upload_pack(self._packets / ".git"),
                     "--", str(self._packets), str(path))
        self._worker("git", "-C", str(path), "checkout", "-q", "--detach", baseline)
        return GitWorkspace(invocation_id, owner, path, baseline)

    def candidate_clone(self, prefix: str, invocation_id: str, owner: str, intake: Path, ref: str,
                        revision: str) -> GitWorkspace:
        """A fresh VERIFIER or CLOSURE clone: `git init`, a fetch of `ref` from the intake repository (read only),
        then the candidate's full SHA checked out detached."""
        if prefix not in {"verifier", "closure"} or not ref.startswith("refs/intake/"):
            raise CandidateUnavailable("workspace identity is unsafe")
        path = self._new(prefix, invocation_id, owner, revision)
        self._worker("git", "init", "-q", "--", str(path))
        self._worker("git", "-C", str(path), "fetch", "-q", "--no-tags", _upload_pack(intake), "--", str(intake), ref)
        self._worker("git", "-C", str(path), "checkout", "-q", "--detach", revision)
        return GitWorkspace(invocation_id, owner, path, revision)

    def cleanup(self, workspace: Workspace, process_id: int | None) -> None:
        """Removal as the worker (`rm -rf`), only after the ownership checks; no git runs in the workspace."""
        if not isinstance(workspace, GitWorkspace) or workspace.path.parent != self._root \
                or not _safe_identity(workspace.path.name):
            raise CandidateUnavailable("workspace ownership cannot be established")
        if process_id is not None and Path(f"/proc/{process_id}").exists():
            raise CandidateUnavailable("owned process is plausibly live; workspace retained")
        if not os.path.lexists(workspace.path):
            return
        self._worker("rm", "-rf", "--", str(workspace.path))
        if os.path.lexists(workspace.path):
            raise CandidateUnavailable("workspace is not removable; retained for diagnosis")
