"""FX-K2 composition: canonical multi-role orchestration over one disposable root.

The production ``OfflineProfile`` composes the unchanged ``FactoryCoordinator``,
a real SQLite store and a local Work Management transport with the production
``RealWorkerProvider`` and its durable ``JsonlInvocationJournal`` (the K1
seam). Behind that one Worker Port sits the Deterministic Test Worker:
``ScriptedWorkerProcess``, which commits real revisions as producer and writes
real verdict files as verifier. ``GitSourceControl`` publishes to a local bare
remote and retrieves each candidate into fresh clones. No model, provider,
network or credential is involved; the script drives worker outcomes only and
never touches the store or the lifecycle.

Reopening the same root is a restart. Run as
``python -m tests.execution_coordination.k2_fixture crash-after-verifier-outcome --root <root>``
to compose in a child process that dies right after the verifier outcome is
durably journaled and before the coordinator records it.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Callable, Mapping, Sequence

from alienintent.composition.offline_profile import OfflineProfile
from alienintent.composition.sandbox_run_profile import contract_from_document
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal, journal_records
from alienintent.invocation_runtime.adapters.scripted_worker import ScriptedWorkerProcess
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal
from alienintent.invocation_runtime.ports.worker_process import WorkerProcess

ROOT = Path(__file__).resolve().parents[2]
S0_MANIFEST = ROOT / "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json"
WORK = "K2-PROBE"
PROFILE = "fx-k2"
REPOSITORY = "local:fx-k2"
EPOCH = 1758542400
CRASH_EXIT = 17
IDENTITY = ("FX-K2 worker", "k2-worker@alienintent.invalid")
NOTE = "docs/K2-PROBE.md"


def contract_document(*, closure_actions: Sequence[str] = ("candidate-published",), maximum_attempts: int = 2) -> dict[str, object]:
    """The S0 probe contract re-pinned to the K2 probe with a two-attempt budget."""
    manifest = json.loads(S0_MANIFEST.read_text(encoding="utf-8"))
    document = dict(manifest["work_items"][0]["contract"])
    budget = dict(document["budget_policy"]) | {"maximum_attempts": maximum_attempts}
    document.update({
        "identity": WORK, "authority_issuer": "FX-K2 proof fixture", "authority_references": ["WO-220402"],
        "authorized_scope": [NOTE], "completion_criteria": [f"{NOTE} records the invocation"],
        "intent": "prove canonical producer, verifier and closure role routing over the shared WorkerProvider boundary",
        "fixed_decisions": ["K2 canonical_role_orchestration only"], "target_repositories": [REPOSITORY],
        "required_closure_actions": list(closure_actions), "budget_policy": budget,
    })
    return document


@dataclass
class K2Fixture:
    root: Path
    profile: OfflineProfile
    worker: RealWorkerProvider
    process: WorkerProcess
    journal: JsonlInvocationJournal
    item: ReadyWorkItem

    @property
    def coordinator(self):
        return self.profile.coordinator

    @property
    def store(self):
        return self.profile.store

    def state(self):
        return self.coordinator.state(WORK)

    def invocations(self) -> list[tuple[str, str, str | None]]:
        """(role, correlation, kind) of every durably journaled invocation outcome, in order."""
        return [(str(r["role"]), str(r["correlation_id"]), r.get("kind")) for r in self.journal.records() if r.get("event") == "invocation-outcome"]

    def process_runs(self) -> list[dict[str, object]]:
        return [r for r in journal_records(self.root / "process-journal.jsonl") if r.get("event") == "process-run"]

    def projections(self) -> list[str]:
        return [str(r.get("state")) for r in self.profile.work.receipts() if r.get("receipt") == "execution-state-projected"]

    def remote_advertises(self, branch: str) -> str | None:
        advertised = _git("ls-remote", str(self.root / "remote.git"), f"refs/heads/{branch}", cwd=self.root)
        return advertised.split()[0] if advertised else None


def git_environment(root: Path) -> dict[str, str]:
    name, email = IDENTITY
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(root / "home"), "LANG": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(root / "home" / ".gitconfig"), "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        "GIT_AUTHOR_DATE": f"{EPOCH} +0000", "GIT_COMMITTER_DATE": f"{EPOCH} +0000",
    }


def _git(*args: str, cwd: Path, environment: Mapping[str, str] | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, env=None if environment is None else dict(environment), capture_output=True, text=True, check=True).stdout.strip()


def _seed(root: Path) -> None:
    environment = git_environment(root)
    (root / "home").mkdir(parents=True, exist_ok=True)
    _git("init", "-q", "--bare", "--initial-branch=main", str(root / "remote.git"), cwd=root, environment=environment)
    _git("init", "-q", "--initial-branch=main", str(root / "checkout"), cwd=root, environment=environment)
    (root / "checkout" / "README.md").write_text("FX-K2 disposable baseline\n", encoding="utf-8")
    _git("add", "-A", cwd=root / "checkout", environment=environment)
    _git("commit", "-q", "-m", "FX-K2 baseline", cwd=root / "checkout", environment=environment)
    _git("remote", "add", "origin", str(root / "remote.git"), cwd=root / "checkout", environment=environment)
    _git("push", "-q", "origin", "main", cwd=root / "checkout", environment=environment)


def candidate_branch(invocation: WorkerInvocation) -> str:
    return f"candidate/{ref_safe(invocation.correlation_id)}"


def compose(
    root: Path, script: Sequence[str] = ("success", "accept"), *, note: str = NOTE,
    closure_actions: Sequence[str] = ("candidate-published",), maximum_attempts: int = 2,
    journal: Callable[[JsonlInvocationJournal], InvocationJournal] | None = None,
    process: Callable[[ScriptedWorkerProcess], WorkerProcess] | None = None,
) -> K2Fixture:
    """Compose over ``root``; an existing root is reopened, which is a restart."""
    root = Path(root).resolve()
    if not (root / "remote.git").exists():
        _seed(root)
    clock = lambda: float(EPOCH)  # noqa: E731
    durable = JsonlInvocationJournal(root / "invocation-journal.jsonl", clock)
    contract = contract_from_document(contract_document(closure_actions=closure_actions, maximum_attempts=maximum_attempts))
    item = ReadyWorkItem(WORK, 0, REPOSITORY, PROFILE, None, (), contract, contract.content_digest, "seeded by FX-K2", True)
    grant = lambda invocation: CapabilityGrant(  # noqa: E731
        f"FX-K2-{invocation.work_identity}", "1", invocation.correlation_id, InvocationRole.PRODUCER, PROFILE, REPOSITORY,
        frozenset({"process-control", "git-write"}), EPOCH + 3600,
    )
    scripted = ScriptedWorkerProcess({WORK: tuple(script)}, {WORK: note}, clock, root / "process-journal.jsonl", git_environment(root))
    behind_port = scripted if process is None else process(scripted)
    worker = RealWorkerProvider(
        behind_port, GitSourceControl(), root / "checkout", "origin", candidate_branch, root / "worker-read-back", grant, REPOSITORY,
        GitWorktreeAdapter(root / "checkout", root / "workspaces"), ReservationBook(1, 2), now=clock, sleep=lambda _: None,
        journal=durable if journal is None else journal(durable),
    )
    work = LocalWorkManagement(root / "work-management", PROFILE, REPOSITORY, (item,), clock)
    profile = OfflineProfile(root / "state.sqlite", work, worker, root / "artifacts", root / "verifier-evidence", name=PROFILE)
    return K2Fixture(root, profile, worker, behind_port, durable, item)


class CrashAfterVerifierOutcome:
    """Dies immediately after the verifier outcome is durably journaled."""

    def __init__(self, inner: JsonlInvocationJournal) -> None:
        self._inner = inner

    def append(self, record):
        entry = self._inner.append(record)
        if record.get("event") == "invocation-outcome" and record.get("role") == "VERIFIER":
            os._exit(CRASH_EXIT)
        return entry

    def records(self):
        return self._inner.records()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("crash-after-verifier-outcome",))
    parser.add_argument("--root", required=True, type=Path)
    arguments = parser.parse_args()
    compose(arguments.root, journal=CrashAfterVerifierOutcome).coordinator.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
