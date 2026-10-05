"""Work item WORKSPACE-FOLDER-NAMES (6e06e5dc): workspace and clone folders named after a correlation id use one safe
form, so `PYTHONPATH=<workspace>/src:<workspace>` in a child process still imports from the workspace."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

from alienintent.composition.work_registry import RegistryClosure, _producer_worktree
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain import runtime

ROOT = Path(__file__).resolve().parents[2]
CORRELATION = "launch:dc49e880-0de2-46fd-89a7-bf827f35cccd:2"


def workspace_folder(correlation: str) -> str:
    return runtime.workspace_folder(correlation)  # an AttributeError on the starting revision is the failure


def test_one_rule_names_every_folder():
    """Check 1."""
    assert workspace_folder(CORRELATION) == "launch-dc49e880-0de2-46fd-89a7-bf827f35cccd-2"
    other = "launch:dc49e880-0de2-46fd-89a7-bf827f35cccd:3"
    assert workspace_folder(other) != workspace_folder(CORRELATION)
    for correlation in (CORRELATION, other, "a b\tc:d", ":", "..x..", "-x-", ""):
        name = workspace_folder(correlation)
        assert name and not re.search(r"[:/\s]", name) and name == ref_safe(correlation)
    assert workspace_folder(":") == "invocation"


def imported_from(workspace: Path, cwd: Path) -> subprocess.CompletedProcess:
    (workspace / "src" / "alienintent").mkdir(parents=True, exist_ok=True)
    (workspace / "src" / "alienintent" / "__init__.py").write_text("")
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    environment["PYTHONPATH"] = f"{workspace}/src:{workspace}"
    return subprocess.run([sys.executable, "-c", "import alienintent,sys; print(alienintent.__file__)"], cwd=cwd,
                          env=environment, capture_output=True, text=True, check=False)


def test_a_child_python_imports_from_a_worker_clone_named_after_a_correlation(tmp_path, monkeypatch):
    """Check 2: the real boundary, a ':'-separated PYTHONPATH built from the workspace path."""
    from tests.invocation_runtime.test_git_source_control import Handover
    handover = Handover(tmp_path, monkeypatch)
    workspace = handover.workspaces.allocate(CORRELATION, "owner", handover.base).path
    result = imported_from(workspace, tmp_path)
    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()).resolve().is_relative_to((workspace / "src").resolve())
    raw = tmp_path / "raw" / f"producer-{CORRELATION}"
    raw.mkdir(parents=True)
    result = imported_from(raw, tmp_path)
    assert not (result.returncode == 0 and Path(result.stdout.strip()).resolve().is_relative_to((raw / "src").resolve()))


def test_every_site_names_the_folder_without_a_colon(tmp_path, monkeypatch):
    """Check 3: the clones `WorkerCloneAdapter` makes, the paths the registry reads back for them, the registry
    cleanup that removes them, the landing clone, and the folders `RealWorkerProvider` reads back into."""
    from tests.invocation_runtime.test_git_source_control import Handover
    handover = Handover(tmp_path, monkeypatch)
    invocation = WorkerInvocation("WORK", CORRELATION)
    producer, claimed = handover.produce(CORRELATION)
    assert ":" not in producer.name
    assert _producer_worktree(handover.launch / "worker", invocation, "producer-").path == producer
    handover.source.hand_over(CORRELATION, producer, claimed, handover.base)
    branch = f"candidate/{ref_safe(CORRELATION)}"
    candidate = handover.source.publish_intake(CORRELATION, branch, claimed, tmp_path / "read-back")
    roles = {"verifier": CORRELATION.replace(":2", ":3"), "closure": CORRELATION.replace(":2", ":4")}
    clones = [handover.source.candidate_clone(prefix, correlation, "owner", candidate).path
              for prefix, correlation in roles.items()]
    assert [p.name for p in clones] == [f"{prefix}-{workspace_folder(c)}" for prefix, c in roles.items()]
    assert not any(":" in p.name for p in clones)

    plain = GitWorktreeAdapter(handover.packets, tmp_path / "workspaces").allocate(CORRELATION, "owner", handover.base)
    assert ":" not in plain.path.name and _producer_worktree(tmp_path / "workspaces", invocation).path == plain.path

    closure = RegistryClosure.__new__(RegistryClosure)
    ownership = SimpleNamespace(owner_state=lambda owner: "terminated", owned_work=lambda correlation, token: ())
    started = [{"event": "invocation-started", "work_identity": "WORK", "correlation_id": c, "role": role.upper(),
                "owner": {"pid": 1, "start": 1, "boot": "b", "pidns": "n"}}
               for role, c in (("producer", CORRELATION), *roles.items())]
    closure._registry, closure._root, closure.worker = SimpleNamespace(ownership=ownership), handover.launch, None
    closure._journal = SimpleNamespace(records=lambda: started)
    closure.worker_workspaces, closure.cleanup_diagnostics = handover.workspaces, {}
    closure._git = lambda *args: ""
    landing = closure._clone(roles["closure"])
    read_back = handover.launch / "verifier" / f"producer-{workspace_folder(CORRELATION)}"
    read_back.mkdir(parents=True)
    assert landing.name == f"landing-{workspace_folder(roles['closure'])}"
    assert closure._cleanup(WorkerInvocation("WORK", "launch:WORK:9")) is True, closure.cleanup_diagnostics
    assert not any(os.path.lexists(p) for p in (*clones, landing, read_back))

    provider = RealWorkerProvider.__new__(RealWorkerProvider)
    provider._verifier_root = tmp_path / "verifier"
    assert provider._producer_read_back(invocation).name == f"producer-{workspace_folder(CORRELATION)}"


SITES = ("src/alienintent/invocation_runtime/adapters/git_worktree.py",
         "src/alienintent/invocation_runtime/application/real_worker.py",
         "src/alienintent/composition/work_registry.py", "src/alienintent/composition/offline_proof.py",
         "src/alienintent/composition/lifecycle_capstone.py", "tools/live/py10_proven_red.py")
RAW = re.compile(r"-\{(?:invocation\.correlation_id|correlation|invocation_id|c|closures\[0\]\[0\])\}"
                 r"|\{prefix\}\{correlation\}|(?<!results )(?<!exports )/ (?:correlation|invocation_id|original)\b")


@pytest.mark.parametrize("site", SITES)
def test_no_site_names_a_folder_after_the_raw_correlation(site):
    """Check 3, for the sites a unit test does not reach (`verifier-`/`closure-` in `RealWorkerProvider`, the
    worktree `_authorize_refusal` reads, and the proofs that rebuild the same paths)."""
    lines = [line for line in (ROOT / site).read_text().splitlines() if RAW.search(line)]
    assert lines == []
