"""FX-K1 composition: the non-scripted WorkerProvider path over one disposable root.

The production ``OfflineProfile`` composes the unchanged coordinator, a real
SQLite store and a local Work Management transport with ``RealWorkerProvider``
over ``CliWorkerProvider`` (a real child process that commits into its
allocated worktree), ``GitSourceControl`` publishing to a local bare remote,
``GitWorktreeAdapter`` and the durable ``JsonlInvocationJournal``. No model,
provider, network or credential is involved. Reopening the same root is a
restart: every object is rebuilt and only the store, journal, remote and
worktrees persist.

Run as ``python -m tests.invocation_runtime.k1_fixture crash-after-outcome --root <root>``
to compose in a child process that dies right after the worker outcome is
durably journaled and before the coordinator confirms it.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, Mapping

from alienintent.composition.offline_profile import OfflineProfile
from alienintent.composition.sandbox_run_profile import contract_from_document
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook
from alienintent.invocation_runtime.ports.invocation_journal import InvocationJournal
from tests.support.feature_regressions import seed_verification_runner

ROOT = Path(__file__).resolve().parents[2]
S0_MANIFEST = ROOT / "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json"
WORK = "K1-PROBE"
PROFILE = "fx-k1"
REPOSITORY = "local:fx-k1"
EPOCH = 1758542400
CRASH_EXIT = 17
IDENTITY = ("FX-K1 worker", "k1-worker@alienintent.invalid")

# The worker is a real child process. As producer it records each run outside
# its workspace (so a re-run is observable) and commits one note. As verifier
# (K2) it accepts the exact revision checked out in its fresh workspace.
WORKER_SCRIPT = """
import json, os, pathlib, subprocess
invocation = os.environ["ALIENINTENT_INVOCATION_ID"]
if os.environ.get("ALIENINTENT_ROLE") == "VERIFIER":
    revision = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    verdict = pathlib.Path(".alienintent/verdict.json")
    verdict.parent.mkdir(parents=True, exist_ok=True)
    verdict.write_text(json.dumps({"verdict": "accept", "revision": revision, "findings": []}), encoding="utf-8")
    raise SystemExit(0)
with open(os.environ["K1_RUN_LOG"], "a", encoding="utf-8") as log:
    log.write(invocation + "\\n")
note = pathlib.Path("docs/K1-PROBE.md")
note.parent.mkdir(parents=True, exist_ok=True)
note.write_text("K1-PROBE produced under " + invocation + "\\n", encoding="utf-8")
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-q", "-m", "K1-PROBE: candidate"], check=True)
"""


def contract_document() -> dict[str, object]:
    """The S0 probe contract re-pinned to the K1 probe, with a CLI-enforceable budget."""
    manifest = json.loads(S0_MANIFEST.read_text(encoding="utf-8"))
    document = dict(manifest["work_items"][0]["contract"])
    document.update({
        "identity": WORK, "authority_issuer": "FX-K1 proof fixture", "authority_references": ["WO-220401"],
        "authorized_scope": ["docs/K1-PROBE.md"], "completion_criteria": ["docs/K1-PROBE.md records the invocation"],
        "intent": "prove the real WorkerProvider path durably correlates and reads back its outcome",
        "fixed_decisions": ["K1 real outcome/readback seam only"],
        "budget_policy": {"cancellation_limit": 1, "hard_wall_clock_seconds": 60, "maximum_attempts": 1, "retry_limit": 0},
    })
    return document


@dataclass
class K1Fixture:
    root: Path
    profile: OfflineProfile
    worker: RealWorkerProvider
    journal: JsonlInvocationJournal
    item: ReadyWorkItem

    @property
    def coordinator(self):
        return self.profile.coordinator

    @property
    def store(self):
        return self.profile.store

    def runs(self) -> list[str]:
        log = self.root / "runs.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def outcome_records(self, role: str | None = "PRODUCER") -> list[dict[str, object]]:
        return [record for record in self.journal.records() if record.get("event") == "invocation-outcome" and role in (None, record.get("role"))]

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
    (root / "checkout" / "README.md").write_text("FX-K1 disposable baseline\n", encoding="utf-8")
    seed_verification_runner(root / "checkout")
    _git("add", "-A", cwd=root / "checkout", environment=environment)
    _git("commit", "-q", "-m", "FX-K1 baseline", cwd=root / "checkout", environment=environment)
    _git("remote", "add", "origin", str(root / "remote.git"), cwd=root / "checkout", environment=environment)
    _git("push", "-q", "origin", "main", cwd=root / "checkout", environment=environment)


def candidate_branch(invocation: WorkerInvocation) -> str:
    return f"candidate/{ref_safe(invocation.correlation_id)}"


def compose(root: Path, *, journal: Callable[[JsonlInvocationJournal], InvocationJournal] | None = None) -> K1Fixture:
    """Compose over ``root``; an existing root is reopened, which is a restart."""
    root = Path(root).resolve()
    if not (root / "remote.git").exists():
        _seed(root)
    clock = lambda: float(EPOCH)  # noqa: E731
    durable = JsonlInvocationJournal(root / "invocation-journal.jsonl", clock)
    contract = contract_from_document(contract_document())
    item = ReadyWorkItem(WORK, 0, REPOSITORY, PROFILE, None, (), contract, contract.content_digest, "seeded by FX-K1", True)
    grant = lambda invocation: CapabilityGrant(  # noqa: E731
        f"FX-K1-{invocation.work_identity}", "1", invocation.correlation_id, InvocationRole.PRODUCER, PROFILE, REPOSITORY,
        frozenset({"process-control", "git-write"}), EPOCH + 3600,
    )
    process = CliWorkerProvider(
        "local-python", sys.executable, ("-c", WORKER_SCRIPT), "explicit", frozenset({"wall-clock", "cancellation"}),
        git_environment(root) | {"K1_RUN_LOG": str(root / "runs.log")},
    )
    worker = RealWorkerProvider(
        process, GitSourceControl(), root / "checkout", "origin", candidate_branch, root / "producer-read-back", grant, REPOSITORY,
        GitWorktreeAdapter(root / "checkout", root / "workspaces"), ReservationBook(1, 2), now=clock, sleep=lambda _: None,
        journal=durable if journal is None else journal(durable),
    )
    work = LocalWorkManagement(root / "work-management", PROFILE, REPOSITORY, (item,), clock)
    profile = OfflineProfile(root / "state.sqlite", work, worker, root / "artifacts", root / "verifier-evidence", name=PROFILE)
    return K1Fixture(root, profile, worker, durable, item)


class CrashAfterOutcome:
    """Dies immediately after the worker outcome is durably journaled."""

    def __init__(self, inner: JsonlInvocationJournal) -> None:
        self._inner = inner

    def append(self, record):
        entry = self._inner.append(record)
        if record.get("event") == "invocation-outcome":
            os._exit(CRASH_EXIT)
        return entry

    def records(self):
        return self._inner.records()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("crash-after-outcome",))
    parser.add_argument("--root", required=True, type=Path)
    arguments = parser.parse_args()
    compose(arguments.root, journal=CrashAfterOutcome).coordinator.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
