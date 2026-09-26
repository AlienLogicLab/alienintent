"""FX-K3 composition: the actual shared-profile constructors over local transports.

``sandbox`` builds the production ``SandboxRunProfile`` over recorded GitHub
answers; ``github`` builds the production ``GitHubProfileComposition`` over a
local snapshot, a local secret file and a supplied production
``RealWorkerProvider``. Both reach a real child worker (``worker/run.sh`` over
``CliWorkerProvider``), real Git worktrees and a local bare remote, and both
hand their coordinator nothing but the K3 ``RoleBindingGuard``. No model,
provider, network or credential is involved.

The worker is told how to behave by marker files in its stated ``TMPDIR``:
``reject-once`` makes the next verifier reject, ``background`` makes the
producer's client exit at once while owned background work commits later.
Every run is logged outside the workspace so a re-run is observable.

Reopening a root is a restart. Run as
``python -m tests.composition.k3_fixture <mode> --root <root>`` to compose the
sandbox profile in a child process that dies (``os._exit``) at the named
journal boundary: ``crash-before-producer-outcome`` or
``crash-after-verifier-outcome``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Callable

from alienintent.composition.github_profile import GitHubProfileComposition
from alienintent.composition.role_binding import ROLE_OPERATIONS
from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS, SandboxRunProfile, contract_from_document, worker_environment
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
from alienintent.installation.domain.github_profile import GitHubProfile
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.adapters.invocation_journal import JsonlInvocationJournal, journal_records
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook
from tests.composition.test_sandbox_run_profile import backlog, contract_document, digest_of, project_item
from tests.support.feature_regressions import seed_verification_runner

ROOT = Path(__file__).resolve().parents[2]
EPOCH = 1758445000.0
CRASH_EXIT = 17
SANDBOX_WORK = "SB-01"
GH_WORK, GH_PROFILE, GH_REPOSITORY = "GH-01", "alpha", "AlienLogicLab/alienintent"
WORKER_COMMAND = ("/bin/bash", "worker/run.sh")

WORKER = """#!/bin/bash
set -euo pipefail
invocation="${ALIENINTENT_INVOCATION_ID:?the worker is not told which invocation it is}"
role="${ALIENINTENT_ROLE:?the worker is not told which role it plays}"
biu="${invocation#launch:}"
biu="${biu%:*}"
test -z "${GIT_CONFIG_COUNT:-}" || { echo "worker inherited a publication credential" >&2; exit 3; }
printf '%s %s\\n' "$role" "$invocation" >> "$TMPDIR/runs.log"
if [ "$role" = VERIFIER ]; then
  mkdir -p .alienintent
  revision="$(git rev-parse HEAD)"
  if [ -e "$TMPDIR/reject-once" ]; then
    rm -f "$TMPDIR/reject-once"
    printf '{"verdict": "reject", "revision": "%s", "findings": ["FX-K3: first candidate rejected"]}\\n' "$revision" > .alienintent/verdict.json
  else
    printf '{"verdict": "accept", "revision": "%s", "findings": []}\\n' "$revision" > .alienintent/verdict.json
  fi
  exit 0
fi
if [ -e "$TMPDIR/background" ]; then
  # The client exits now; the work it started still holds its output and commits later.
  ( sleep 1; mkdir -p docs; printf '%s background work under %s\\n' "$biu" "$invocation" > "docs/${biu}-background.md"
    git add -A; git commit -qm "${biu}: background work" ) &
  exit 0
fi
mkdir -p docs
printf '%s completed by the factory under %s\\n' "$biu" "$invocation" >> "docs/${biu}.md"
git add -A
git commit -qm "${biu}: factory candidate"
"""


def _git_environment() -> dict[str, str]:
    return dict(os.environ) | {
        "GIT_AUTHOR_NAME": "FX-K3", "GIT_AUTHOR_EMAIL": "k3@alienintent.invalid",
        "GIT_COMMITTER_NAME": "FX-K3", "GIT_COMMITTER_EMAIL": "k3@alienintent.invalid",
    }


def seed(root: Path) -> Path:
    """A local bare remote and a checkout carrying the K3 worker; idempotent for a restart."""
    remote, checkout = root / "remote.git", root / "checkout"
    (root / "worker-tmp").mkdir(parents=True, exist_ok=True)
    if remote.exists():
        return checkout
    subprocess.run(["git", "init", "--bare", "--quiet", str(remote)], check=True)
    subprocess.run(["git", "clone", "--quiet", str(remote), str(checkout)], check=True, capture_output=True)
    (checkout / "worker").mkdir()
    (checkout / "worker" / "run.sh").write_text(WORKER)
    (checkout / "README.md").write_text("FX-K3 disposable baseline\n")
    seed_verification_runner(checkout)
    subprocess.run(["git", "-C", str(checkout), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(checkout), "commit", "--quiet", "-m", "baseline"], check=True, env=_git_environment())
    subprocess.run(["git", "-C", str(checkout), "push", "--quiet", "origin", "HEAD:refs/heads/main"], check=True, capture_output=True)
    return checkout


def document(identity: str, maximum_attempts: int) -> dict:
    budget = dict(contract_document(identity)["budget_policy"]) | {"maximum_attempts": maximum_attempts}
    return contract_document(identity, budget_policy=budget)


def sandbox(root: Path, *, maximum_attempts: int = 1, profile_class: type[SandboxRunProfile] = SandboxRunProfile) -> SandboxRunProfile:
    """The actual PY-10 run profile constructor; an existing root is reopened, which is a restart."""
    root = Path(root)
    checkout = seed(root)
    only = document(SANDBOX_WORK, maximum_attempts)
    items = [project_item("PVTI_1", SANDBOX_WORK, priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only))]
    return profile_class(
        backlog(root, items, {f"biu/{SANDBOX_WORK}.json": only}), root / "state", checkout,
        provider="claude", worker_command=WORKER_COMMAND, worker_environment=worker_environment(root), clock=lambda: EPOCH,
    )


def github_grant(invocation: WorkerInvocation) -> CapabilityGrant:
    role = InvocationRole(invocation.role)
    return CapabilityGrant(f"fx-k3-{invocation.work_identity}", "1", invocation.correlation_id, role, GH_PROFILE, GH_REPOSITORY,
                           ROLE_OPERATIONS[str(role)], int(EPOCH) + 3600)


def github(root: Path, *, binding: str = "bound", grant: Callable[[WorkerInvocation], CapabilityGrant] = github_grant) -> GitHubProfileComposition:
    """The actual GitHub profile constructor with a supplied real worker.

    ``binding`` is ``bound`` (the provider journals where the profile reads),
    ``missing`` (neither holds a journal) or ``disconnected`` (the provider
    journals somewhere the profile never reads).
    """
    root = Path(root)
    checkout = seed(root)
    clock = lambda: EPOCH  # noqa: E731
    contract = contract_from_document(document(GH_WORK, 1))
    row = {
        "identity": GH_WORK, "repository": GH_REPOSITORY, "membership": True, "complete": True, "status": "READY",
        "priority": "P0", "wave": "2", "dependencies": [], "contract": f"biu/{GH_WORK}.json",
        "contract_digest": contract.content_digest, "readiness": "READY", "source_version": "fx-k3",
    }
    secret = root / "webhook"
    secret.write_text("fx-k3-webhook-secret")
    journal = JsonlInvocationJournal(root / "invocation-journal.jsonl", clock)
    provider_journal = {"bound": journal, "missing": None, "disconnected": JsonlInvocationJournal(root / "elsewhere-journal.jsonl", clock)}[binding]
    worker = RealWorkerProvider(
        CliWorkerProvider("claude", *WORKER_COMMAND[:1], WORKER_COMMAND[1:], "bypassPermissions", PROVIDER_DIMENSIONS, environment=worker_environment(root)),
        GitSourceControl(), checkout, "origin", lambda invocation: f"candidate/{ref_safe(invocation.correlation_id)}",
        root / "producer-read-back", grant, GH_REPOSITORY, GitWorktreeAdapter(checkout, root / "workspaces"), ReservationBook(1, 2),
        now=clock, sleep=lambda _: None, journal=provider_journal,
    )
    profile = GitHubProfile(GH_PROFILE, GH_REPOSITORY, "PVT_1", {"READY": "READY"}, {"IMPLEMENT": "Execution"}, "webhook", automatic_release=True)
    return GitHubProfileComposition(
        profile, ProtectedLocalFileSecretProvider({"webhook": secret}), root / "state.sqlite", lambda: (row,), contract, lambda _: None,
        projection_write=lambda identity, field, state, revision: revision, worker=worker,
        journal=None if binding == "missing" else journal, clock=clock,
    )


# --- observation --------------------------------------------------------------


def runs(root: Path) -> list[tuple[str, str]]:
    """(role, correlation) of every worker process run, in order, read outside every workspace."""
    log = Path(root) / "worker-tmp" / "runs.log"
    return [tuple(line.split(" ", 1)) for line in log.read_text().splitlines()] if log.exists() else []  # type: ignore[misc]


def journaled(path: Path, event: str = "invocation-outcome") -> list[dict[str, object]]:
    return [record for record in journal_records(Path(path)) if record.get("event") == event]


def advertised(root: Path) -> list[str]:
    heads = subprocess.run(["git", "ls-remote", "--heads", str(Path(root) / "remote.git")], capture_output=True, text=True, check=True).stdout
    return sorted(line.split("refs/heads/", 1)[1] for line in heads.splitlines() if "refs/heads/candidate/" in line)


# --- crash harness ------------------------------------------------------------


def crash_at(profile: SandboxRunProfile, mode: str) -> None:
    """Kill this process at the named journal boundary; no Python cleanup runs."""
    append = profile.journal.append

    def dying(record):
        if mode == "crash-before-producer-outcome" and record.get("event") == "invocation-outcome" and record.get("role") == "PRODUCER":
            os._exit(CRASH_EXIT)
        entry = append(record)
        if mode == "crash-after-verifier-outcome" and record.get("event") == "invocation-outcome" and record.get("role") == "VERIFIER":
            os._exit(CRASH_EXIT)
        return entry

    profile.journal.append = dying  # type: ignore[method-assign]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("crash-before-producer-outcome", "crash-after-verifier-outcome"))
    parser.add_argument("--root", required=True, type=Path)
    arguments = parser.parse_args()
    profile = sandbox(arguments.root)
    crash_at(profile, arguments.mode)
    profile.coordinator.start()
    print(json.dumps({"crashed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
