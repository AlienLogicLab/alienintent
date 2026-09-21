"""Composition-root read-only probes supplying doctor with real adapter evidence.

Every probe here observes. None allocates a worktree, starts a worker, or
touches a product resource.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter


def git_worktree_inventory(repository: Path) -> tuple[Path, ...]:
    """Read back the worktrees Git already knows about; `list` never allocates."""
    listing = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repository, capture_output=True, text=True, check=False,
    )
    if listing.returncode:
        return ()
    return tuple(
        Path(line.split(" ", 1)[1])
        for line in listing.stdout.splitlines()
        if line.startswith("worktree ")
    )


def execution_evidence(repository: Path, workspace_root: Path, worker: CliWorkerProvider, executable: str) -> dict[str, object]:
    """Evidence the doctor can adjudicate, not a verdict the adapter declared."""
    resolved = shutil.which(executable)
    return {
        "workspace_root": workspace_root,
        "workspace_manager": GitWorktreeAdapter(repository, workspace_root),
        "git_worktrees": git_worktree_inventory(repository),
        "worker_capabilities": worker.capabilities,
        "worker_executable": Path(resolved) if resolved else None,
    }
