"""Composition root for the PY-04 offline profile and the S0 isolated proof substrate.

``OfflineProfile`` is the PY-04 composition, with optional S1 evidence composition.
Its execution kernel remains unchanged. ``OfflineProofSubstrate``
(WO-220101, DAG node S0) composes it, at current interfaces only, over a
disposable local root: a real SQLite operational store, a local bare Git remote
with worktree allocation, publication and fresh-clone read-back through the
unchanged ``RealWorkerProvider`` / ``GitSourceControl`` / ``GitWorktreeAdapter``,
a local Work Management transport with durable receipts, a scripted worker
process with a durable journal, and one injected clock. The existing kernel
runs unchanged; the substrate does not route roles and performs no lifecycle
transition of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from typing import TYPE_CHECKING, Callable, Mapping

from alienintent.composition.sandbox_run_profile import contract_from_document
from alienintent.composition.evidence_profile import EvidenceProfile
from alienintent.evidence_learning.domain.admission import AuthoritySnapshot
from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.control_plane.adapters.decision_notifier import NoOpDecisionNotifier
from alienintent.control_plane.ports.decision_notifier import DecisionNotifier
from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkManagement
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerProvider
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter, ref_safe
from alienintent.invocation_runtime.adapters.scripted_worker import ScriptedWorkerProcess, ScriptedWorkerProvider
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole, ReservationBook

if TYPE_CHECKING:
    from alienintent.installation.application.doctor import DoctorService


class OfflineProfile:
    def __init__(self, database: Path, work: WorkManagement, worker: WorkerProvider, artifact_root: Path, verifier_root: Path | None = None, *, name: str = "offline", automatic_release: bool = True, doctor: "DoctorService | None" = None,
                 evidence_root: Path | None = None, evidence_permitted_root: Path | None = None,
                 evidence_project: str | None = None, evidence_authority: AuthoritySnapshot | None = None,
                 store: SQLiteOperationalStore | None = None, notifier: DecisionNotifier | None = None) -> None:
        self.name = name
        self.store = SQLiteOperationalStore(database) if store is None else store
        self.work = work
        self.coordinator = FactoryCoordinator(self.store, work, worker, LocalArtifactStore(artifact_root, verifier_root or artifact_root / "verifier-evidence"), name, automatic_release=automatic_release, notifier=NoOpDecisionNotifier() if notifier is None else notifier)
        self.doctor = doctor
        self.evidence = None
        evidence_arguments = (evidence_root, evidence_permitted_root, evidence_project, evidence_authority)
        if any(value is not None for value in evidence_arguments):
            if any(value is None for value in evidence_arguments):
                raise EvidenceHold("EVIDENCE_CONFIGURATION", required_action="supply root, permitted root, project and pinned authority together")
            self.evidence = EvidenceProfile(evidence_root, permitted_root=evidence_permitted_root, project=evidence_project,
                                            name=name, authority=evidence_authority, store=self.store)

    def readiness(self) -> bool:
        """PY-09 owns substantive doctor checks; PY-08 supplies this injected gate."""
        return self.doctor is not None and self.doctor.run().ready


# --- S0: credential absence -----------------------------------------------------

CREDENTIAL_PATTERN = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|CREDENTIAL|PRIVATE_KEY)", re.IGNORECASE)
CREDENTIAL_NAMES = frozenset({"GIT_CONFIG_COUNT", "GIT_ASKPASS", "SSH_AUTH_SOCK"})


def credential_findings(environment: Mapping[str, str]) -> tuple[str, ...]:
    """Environment variable names that carry, or could route, a credential."""
    return tuple(sorted(name for name in environment if name in CREDENTIAL_NAMES or CREDENTIAL_PATTERN.search(name)))


# --- S0: manifest ---------------------------------------------------------------

MANIFEST_KIND = "OfflineProofManifest"
MANIFEST_SCHEMA_VERSION = "1"
GRANT_OPERATIONS = frozenset({"process-control", "git-write"})
GRANT_SECONDS = 3600
WORKER_IDENTITY = ("FX scripted worker", "scripted-worker@alienintent.invalid")


class ManifestRejected(ValueError):
    """The proof manifest cannot safely seed a fixture."""


@dataclass(frozen=True)
class ProofWorkItem:
    identity: str
    priority: int | None
    dependencies: tuple[str, ...]
    note_path: str
    script: tuple[str, ...]
    contract_document: Mapping[str, object]


@dataclass(frozen=True)
class ProofManifest:
    fixture_id: str
    profile: str
    seed: str
    clock_epoch: int
    repository: str
    baseline_files: Mapping[str, str]
    work_items: tuple[ProofWorkItem, ...]
    kernel_baseline: str
    kernel_paths: tuple[str, ...]
    digest: str


def manifest_from_document(document: Mapping[str, object]) -> ProofManifest:
    if not isinstance(document, Mapping) or document.get("record_kind") != MANIFEST_KIND or str(document.get("schema_version")) != MANIFEST_SCHEMA_VERSION:
        raise ManifestRejected("document is not an OfflineProofManifest schema 1")
    clock = document.get("clock") or {}
    try:
        epoch = int(clock["epoch_seconds"])
        items = tuple(
            ProofWorkItem(
                str(entry["identity"]), None if entry.get("priority") is None else int(entry["priority"]),
                tuple(str(value) for value in entry.get("dependencies") or ()), str(entry.get("note_path") or f"docs/{entry['identity']}.md"),
                tuple(str(step) for step in entry["script"]), dict(entry["contract"]),
            )
            for entry in document["work_items"]
        )
        manifest = ProofManifest(
            str(document["fixture_id"]), str(document["profile"]), str(document["seed"]), epoch, str(document["repository"]),
            dict(document.get("baseline_files") or {}), items, str(document.get("kernel_baseline") or ""),
            tuple(str(path) for path in document.get("kernel_paths") or ()),
            "sha256:" + sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ManifestRejected(f"manifest is incomplete: {error}") from error
    if not manifest.work_items or not manifest.profile or not manifest.seed:
        raise ManifestRejected("manifest names no work, profile or seed")
    return manifest


def load_manifest(path: Path) -> ProofManifest:
    return manifest_from_document(json.loads(Path(path).read_text(encoding="utf-8")))


# --- S0: substrate ---------------------------------------------------------------


class OfflineProofSubstrate:
    """The S0 isolated proof substrate over one disposable root.

    Constructing it over a fresh root seeds the local remote and checkout;
    constructing it over an existing root reopens the same store, journal and
    receipts and refuses a seed that disagrees. Separate roots are isolated.
    """

    def __init__(self, root: Path, manifest: ProofManifest, environment: Mapping[str, str] | None = None) -> None:
        self.root, self.manifest = Path(root).resolve(), manifest
        self.environment = dict(os.environ if environment is None else environment)
        self.home, self.checkout, self.remote = self.root / "home", self.root / "checkout", self.root / "remote.git"
        self.workspaces, self.producer_read_back = self.root / "workspaces", self.root / "producer-read-back"
        self.verifier_root, self.artifacts = self.root / "verifier-evidence", self.root / "artifacts"
        self.journal_path, self.work_root = self.root / "worker-journal" / "journal.jsonl", self.root / "work-management"
        self.database, self.tmp = self.root / "state.sqlite", self.root / "tmp"
        for directory in (self.home, self.workspaces, self.producer_read_back, self.verifier_root, self.artifacts, self.work_root, self.tmp):
            directory.mkdir(parents=True, exist_ok=True)
        self.clock: Callable[[], float] = lambda: float(manifest.clock_epoch)
        self.git_environment = self._git_environment()
        self.reopened = self.remote.exists()
        if not self.reopened:
            self._seed_repository()
        self.baseline_revision = self._git("rev-parse", "HEAD", cwd=self.checkout)
        self.items = tuple(self._ready_item(fifo, entry) for fifo, entry in enumerate(manifest.work_items))
        self.work = LocalWorkManagement(self.work_root, manifest.profile, manifest.repository, self.items, self.clock)
        self.process = ScriptedWorkerProcess(
            {entry.identity: entry.script for entry in manifest.work_items},
            {entry.identity: entry.note_path for entry in manifest.work_items},
            self.clock, self.journal_path, self.git_environment,
        )
        self.store = SQLiteOperationalStore(self.database)
        self.worker = self._compose_worker()
        self.profile = OfflineProfile(self.database, self.work, self.worker, self.artifacts, self.verifier_root, name=manifest.profile,
                                      store=self.store, notifier=self._compose_notifier())
        self.coordinator = self.profile.coordinator

    # --- worker composition ---------------------------------------------------

    def _compose_worker(self) -> WorkerProvider:
        """S0: the unchanged ``RealWorkerProvider`` behind a scripted journaling wrapper."""
        self.real_worker = RealWorkerProvider(
            self.process, GitSourceControl(), self.checkout, "origin", self.candidate_branch, self.producer_read_back,
            self.grant, self.manifest.repository, GitWorktreeAdapter(self.checkout, self.workspaces), ReservationBook(1, 2),
            now=self.clock, sleep=lambda _: None,
        )
        return ScriptedWorkerProvider(self.real_worker, self.journal_path, self.clock)

    def _compose_notifier(self) -> DecisionNotifier | None:
        return None

    # --- per-invocation authority and custody --------------------------------

    @staticmethod
    def candidate_branch(invocation: WorkerInvocation) -> str:
        return f"candidate/{ref_safe(invocation.correlation_id)}"

    def grant(self, invocation: WorkerInvocation) -> CapabilityGrant:
        return CapabilityGrant(
            f"{self.manifest.fixture_id}-{invocation.work_identity}", "1", invocation.correlation_id, InvocationRole.PRODUCER,
            self.manifest.profile, self.manifest.repository, GRANT_OPERATIONS, int(self.clock()) + GRANT_SECONDS,
        )

    # --- disposable repository ----------------------------------------------

    def _git_environment(self) -> dict[str, str]:
        """The exact environment every fixture-side git and worker command runs in.

        Stated in full rather than inherited: the fixture home is empty, the
        system and global git configuration are not read, so no credential
        helper, URL rewrite or identity from the launching user reaches the
        substrate.
        """
        name, email = WORKER_IDENTITY
        return {
            "PATH": self.environment.get("PATH", "/usr/bin:/bin"), "HOME": str(self.home), "LANG": "C.UTF-8", "TMPDIR": str(self.tmp),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(self.home / ".gitconfig"), "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email,
        }

    def _git(self, *args: str, cwd: Path) -> str:
        epoch = int(self.clock())
        environment = self.git_environment | {"GIT_AUTHOR_DATE": f"{epoch} +0000", "GIT_COMMITTER_DATE": f"{epoch} +0000"}
        result = subprocess.run(["git", *args], cwd=cwd, env=environment, capture_output=True, text=True, check=False)
        if result.returncode:
            raise ManifestRejected(f"fixture git step failed: git {' '.join(args)}: {result.stderr.strip()[:200]}")
        return result.stdout.strip()

    def _seed_repository(self) -> None:
        self._git("init", "-q", "--bare", "--initial-branch=main", str(self.remote), cwd=self.root)
        self._git("init", "-q", "--initial-branch=main", str(self.checkout), cwd=self.root)
        for relative, content in self.manifest.baseline_files.items():
            target = self.checkout / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self._git("add", "-A", cwd=self.checkout)
        self._git("commit", "-q", "--allow-empty", "-m", f"{self.manifest.fixture_id} baseline (seed {self.manifest.seed})", cwd=self.checkout)
        self._git("remote", "add", "origin", str(self.remote), cwd=self.checkout)
        self._git("push", "-q", "origin", "main", cwd=self.checkout)

    def _ready_item(self, fifo: int, entry: ProofWorkItem) -> ReadyWorkItem:
        contract = contract_from_document(entry.contract_document)
        if contract.identity != entry.identity:
            raise ManifestRejected("work item contract does not name the seeded identity")
        return ReadyWorkItem(
            entry.identity, fifo, self.manifest.repository, self.manifest.profile, entry.priority, entry.dependencies,
            contract, contract.content_digest, f"seeded by manifest {self.manifest.digest}", True,
        )

    # --- read-only observations ----------------------------------------------

    def remote_advertises(self, branch: str) -> str | None:
        advertised = self._git("ls-remote", str(self.remote), f"refs/heads/{branch}", cwd=self.root)
        return advertised.split()[0] if advertised else None

    def commit_dates(self, revision: str) -> tuple[int, int]:
        author, committer = self._git("show", "-s", "--format=%at %ct", revision, cwd=self.checkout).split()
        return int(author), int(committer)
