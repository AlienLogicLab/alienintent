"""Git implementation of immutable remote candidate custody and of exact-ref publication."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Mapping
from urllib.parse import urlsplit, urlunsplit

from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.invocation_runtime.adapters.cli_worker import run_as_worker
from alienintent.invocation_runtime.adapters.git_worktree import GitWorkspace, WorkerCloneAdapter, ref_safe
from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable, CandidateUnreadable
from alienintent.invocation_runtime.ports.source_control import PublicationFailed, PublishRef, SourceControl

PUBLISH_TIMEOUT_SECONDS = 300
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
# How one worker-written file is opened by the control plane: never through a final symbolic link, never blocking on
# a FIFO, and checked by `fstat` on this descriptor (never a path `stat`) before anything is read from it.
WORKER_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
# Environment a control-plane git call never inherits: every repository-discovery or object-store override.
_DISCOVERY = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
              "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_REPLACE_REF_BASE", "GIT_CEILING_DIRECTORIES",
              "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS")


# The one diff form actual-diff containment reads: every changed path with its mode, NUL-separated, no rename pairing.
RAW_DIFF = ("diff", "--raw", "-z", "--no-renames", "--no-ext-diff", "--no-textconv", "--abbrev=40")


def raw_changes(output: str) -> tuple[tuple[str, str], ...]:
    """`(mode, path)` of each entry of `git diff --raw -z --no-renames`: the new mode of an added or modified path,
    the old mode of a deleted one. Anything else is CandidateUnavailable."""
    fields = output.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    if len(fields) % 2:
        raise CandidateUnavailable("unreadable raw diff")
    changes = []
    for header, path in zip(fields[0::2], fields[1::2]):
        parts = header.lstrip(":").split()
        if not header.startswith(":") or len(parts) != 5 or not path:
            raise CandidateUnavailable("unreadable raw diff")
        changes.append((parts[0] if parts[4] == "D" else parts[1], path))
    return tuple(changes)


def open_worker_file(path: Path, owner_uid: int) -> int:
    """An open descriptor of `path`, a regular file owned by `owner_uid` (checked by `fstat` on the descriptor), or
    OSError. The caller reads only from this descriptor and closes it."""
    descriptor = os.open(path, WORKER_FILE_FLAGS)
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode) or status.st_uid != owner_uid:
            raise OSError("not a regular file owned by the worker")
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def read_descriptor(descriptor: int, limit: int) -> bytes:
    chunks, total = [], 0
    while True:
        chunk = os.read(descriptor, 1 << 16)
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > limit:
            raise OSError("worker file too large")
        chunks.append(chunk)


class GitSourceControl(SourceControl):
    @staticmethod
    def _evidence_remote(remote: str) -> str:
        """Keep candidate evidence usable without retaining URL userinfo."""
        parsed = urlsplit(remote)
        if not parsed.scheme:
            return remote
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
        if result.returncode:
            raise CandidateUnavailable("git operation failed")
        return result.stdout.strip()

    def revision(self, workspace: Path) -> str:
        revision = self._git("rev-parse", "HEAD", cwd=workspace)
        if len(revision) != 40:
            raise CandidateUnavailable("candidate revision is not immutable")
        return revision

    def tree(self, workspace: Path, revision: str) -> str:
        return self._git("rev-parse", "--verify", f"{revision}^{{tree}}", cwd=workspace)

    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]:
        """Every path the candidate changed from `starting`, with its mode (`raw_changes`), read in the workspace."""
        if not _FULL_SHA.fullmatch(starting) or not _FULL_SHA.fullmatch(revision):
            raise CandidateUnavailable("candidate or starting revision is not a full SHA")
        result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *RAW_DIFF, starting, revision, "--"],
                                cwd=workspace, capture_output=True, check=False)
        if result.returncode:
            raise CandidateUnavailable("git operation failed")
        return raw_changes(result.stdout.decode(errors="replace"))

    def read_back_candidate(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
        remote_url = self._git("remote", "get-url", remote, cwd=workspace)
        return self._read_back(remote_url, branch, revision, verifier_workspace, workspace)

    def _read_back(self, remote_url: str, branch: str, revision: str, verifier_workspace: Path,
                   workspace: Path) -> CandidateRef:
        advertised = self._git("ls-remote", remote_url, f"refs/heads/{branch}", cwd=workspace)
        if not advertised or advertised.split()[0] != revision:
            raise CandidateUnavailable("candidate revision is not published at the requested branch")
        if verifier_workspace.exists():
            raise CandidateUnavailable("fresh verifier workspace already exists")
        self._git("clone", "--no-checkout", remote_url, str(verifier_workspace))
        fetched = self._git("rev-parse", f"{revision}^{{commit}}", cwd=verifier_workspace)
        if fetched != revision:
            raise CandidateUnavailable("fresh clone cannot retrieve exact candidate revision")
        digest = f"sha256:{sha256(revision.encode()).hexdigest()}"
        evidence_remote = self._evidence_remote(remote_url)
        return CandidateRef.source_revision(digest, f"git:{evidence_remote}#{branch}@{revision}", identity=f"revision:{evidence_remote}@{branch}@{revision}@{digest}").with_independent_read_back()

    def remote_revision(self, workspace: Path, remote: str, branch: str) -> str | None:
        """Read-only: the revision the remote holds at exactly `refs/heads/<branch>`, or None when the remote was read
        and lists no such ref. The same `ls-remote` `read_back_candidate` runs, keeping only the exact ref name (as
        `_remote_refs` does); it clones and pushes nothing. An unreadable remote is CandidateUnavailable."""
        if not workspace.is_dir():
            raise CandidateUnavailable("workspace is missing; the remote cannot be read from it")
        remote_url = self._git("remote", "get-url", remote, cwd=workspace)
        wanted = f"refs/heads/{branch}"
        for line in self._git("ls-remote", remote_url, wanted, cwd=workspace).splitlines():
            commit, _, name = line.partition("\t")
            if name == wanted:
                return commit
        return None

    def publish_and_read_back(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
        if self.revision(workspace) != revision:
            raise CandidateUnavailable("workspace HEAD differs from requested candidate revision")
        self._git("push", remote, f"{revision}:refs/heads/{branch}", cwd=workspace)
        return self.read_back_candidate(workspace, remote, branch, revision, verifier_workspace)

    def publish_refs(self, clone: Path, remote: str, refs: tuple[PublishRef, ...]) -> None:
        """Push exactly the given refs from `clone` to the named `remote`, then read the remote back.

        One explicit refspec per ref (`+` only when `force`), never `--tags`, `--mirror` or a wildcard. Refs the remote
        already holds at their commit are not pushed again, so a retry after a partial failure pushes only the rest
        and a retry of a complete publication changes nothing. Returns only when the remote shows every ref at its
        commit; any push or read-back failure is PublicationFailed naming the refs."""
        refs = tuple(refs)
        names = tuple(r.ref for r in refs)
        if not refs or len(set(names)) != len(names) or not all(isinstance(r, PublishRef) for r in refs):
            raise PublicationFailed(names, "refs must be distinct PublishRef values")
        if not isinstance(remote, str) or not remote or remote.startswith("-") or any(c.isspace() for c in remote):
            raise PublicationFailed(names, "remote must be a configured remote name")
        current = self._remote_refs(clone, remote, refs)
        for ref in refs:
            if current.get(ref.ref) == ref.commit:
                continue
            spec = f"{'+' if ref.force else ''}{ref.commit}:{ref.ref}"
            result = self._publish_git(clone, refs, "push", "--porcelain", remote, spec)
            if result.returncode:
                raise PublicationFailed(names, f"push of {ref.ref} rejected")
        published = self._remote_refs(clone, remote, refs)
        differing = tuple(r.ref for r in refs if published.get(r.ref) != r.commit)
        if differing:
            raise PublicationFailed(differing, "remote read-back differs")

    def _remote_refs(self, clone: Path, remote: str, refs: tuple[PublishRef, ...]) -> dict[str, str]:
        """Exactly the named refs on the remote (ls-remote matches ref tails, so keep only exact names)."""
        result = self._publish_git(clone, refs, "ls-remote", remote, *(r.ref for r in refs))
        if result.returncode:
            raise PublicationFailed(tuple(r.ref for r in refs), "remote read-back failed")
        wanted = {r.ref for r in refs}
        advertised = {}
        for line in result.stdout.splitlines():
            commit, _, name = line.partition("\t")
            if name in wanted:
                advertised[name] = commit
        return advertised

    @staticmethod
    def _publish_git(clone: Path, refs: tuple[PublishRef, ...], *args: str) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(["git", *args], cwd=clone, text=True, capture_output=True, check=False,
                                  timeout=PUBLISH_TIMEOUT_SECONDS)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise PublicationFailed(tuple(r.ref for r in refs), f"git {args[0]}: {type(error).__name__}") from error

    def retrieve_for_verification(self, candidate: CandidateRef, verifier_workspace: Path) -> CandidateRef:
        """Independently assemble verifier inputs from the immutable source reference."""
        try:
            prefix, reference = candidate.locator.rsplit("#", 1)
            remote = prefix.removeprefix("git:")
            branch, revision = reference.rsplit("@", 1)
            if not remote or prefix == remote or not branch or len(revision) != 40 or verifier_workspace.exists():
                raise ValueError
        except ValueError:
            raise CandidateUnavailable("candidate cannot be independently retrieved") from None
        try:  # the two reads of the remote: failing to reach it is infrastructure, never a custody judgment
            advertised = self._git("ls-remote", remote, f"refs/heads/{branch}")
        except CandidateUnavailable:
            raise CandidateUnreadable("the remote holding the candidate cannot be read") from None
        if not advertised or advertised.split()[0] != revision:
            raise CandidateUnavailable("candidate revision is not retrievable for verifier")
        try:
            self._git("clone", "--no-checkout", remote, str(verifier_workspace))
        except CandidateUnavailable:
            raise CandidateUnreadable("the remote holding the candidate cannot be cloned") from None
        if self._git("rev-parse", f"{revision}^{{commit}}", cwd=verifier_workspace) != revision:
            raise CandidateUnavailable("verifier clone cannot retrieve exact candidate revision")
        expected_digest = f"sha256:{sha256(revision.encode()).hexdigest()}"
        if candidate.content_digest != expected_digest:
            raise CandidateUnavailable("candidate digest does not match immutable revision")
        # The verifier evaluates the exact revision's tree, not an empty clone.
        self._git("checkout", "-q", "--detach", revision, cwd=verifier_workspace)
        return candidate.with_independent_read_back()


class IntakeSourceControl(GitSourceControl, SourceControl):
    """Candidate hand-over by exact object identity into the control-plane-owned intake repository (unit
    WORKER-CREDENTIAL-BOUNDARY, packet 0.4 and 0.5).

    The worker, through the sudo rule, reports the commit its workspace holds and bundles exactly that commit; the
    control plane copies the bundle by an `fstat`-checked descriptor into its own folder, verifies and fetches only
    the claimed SHA from that copy into `<launch>/intake.git`, checks the identity and ancestry, and publishes from
    the intake repository to the packets remote's URL read from the Founder-owned packets clone. Every control-plane
    git call runs with an explicit GIT_DIR (never discovered), hooks and fsmonitor off and no replace objects, and
    none runs in, or names a path under, a worker workspace or the hand-over folder."""

    def __init__(self, packets: Path, remote: str, launch: Path, user: str, worker_uid: int,
                 environment: Mapping[str, str], control_environment: Mapping[str, str],
                 workspaces: WorkerCloneAdapter) -> None:
        self._packets, self._remote, launch = Path(packets), remote, Path(launch)
        self.intake, self.handoff, self.bundles = launch / "intake.git", launch / "handoff", launch / "intake-bundles"
        self.results = launch / "results"
        self.worker_uid, self._user, self._environment = worker_uid, user, dict(environment)
        self._control = {k: v for k, v in control_environment.items() if k not in _DISCOVERY}
        self._workspaces = workspaces

    # --- control-plane git, in the intake repository only ---------------------------------------------------------

    def _intake_git(self, *args: str, timeout: float = PUBLISH_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
        environment = self._control | {"GIT_DIR": str(self.intake), "GIT_NO_REPLACE_OBJECTS": "1",
                                       "GIT_TERMINAL_PROMPT": "0"}
        try:
            return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
                                  cwd=self.intake, env=environment, capture_output=True, check=False,
                                  timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CandidateUnavailable(f"intake git failed: {type(error).__name__}") from error

    def _intake_out(self, *args: str) -> str:
        result = self._intake_git(*args)
        if result.returncode:
            raise CandidateUnavailable("intake git operation failed")
        return result.stdout.decode(errors="replace").strip()

    def ensure_intake(self) -> None:
        """`git init --bare` the intake repository when it is missing (as the control plane)."""
        if not (self.intake / "HEAD").is_file():
            self.intake.mkdir(mode=0o700, parents=True, exist_ok=True)
            result = subprocess.run(["git", "init", "-q", "--bare", str(self.intake)], cwd=self.intake,
                                    env=self._control | {"GIT_TERMINAL_PROMPT": "0"}, capture_output=True,
                                    check=False, timeout=60)
            if result.returncode:
                raise CandidateUnavailable("intake repository cannot be created")

    def remote_url(self) -> str:
        """The packets remote's URL, read from the Founder-owned packets clone's own git directory."""
        environment = self._control | {"GIT_DIR": str(self._packets / ".git"), "GIT_NO_REPLACE_OBJECTS": "1"}
        result = subprocess.run(["git", "remote", "get-url", self._remote], cwd=self._packets, env=environment,
                                capture_output=True, text=True, check=False, timeout=60)
        if result.returncode or not result.stdout.strip():
            raise CandidateUnavailable("the packets remote cannot be read")
        return result.stdout.strip()

    # --- the hand-over ---------------------------------------------------------------------------------------------

    def _as_worker(self, workspace: Path, *argv: str) -> str:
        try:
            result = run_as_worker(self._user, self._environment, argv, cwd=workspace)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CandidateUnavailable(f"worker command failed: {type(error).__name__}") from error
        if result.returncode:
            raise CandidateUnavailable("worker command failed")
        return result.stdout.decode(errors="replace").strip()

    def revision(self, workspace: Path) -> str:
        """The candidate SHA the worker claims: `git rev-parse --verify HEAD^{commit}`, run as the worker in its own
        workspace. The output is data: it must be 40 hex characters, and it is trusted only once imported."""
        claimed = self._as_worker(workspace, "git", "rev-parse", "--verify", "HEAD^{commit}")
        if not _FULL_SHA.fullmatch(claimed):
            raise CandidateUnavailable("candidate revision is not immutable")
        return claimed

    def tree(self, workspace: Path, revision: str) -> str:
        tree = self._as_worker(workspace, "git", "rev-parse", "--verify", f"{revision}^{{tree}}")
        if not _FULL_SHA.fullmatch(tree):
            raise CandidateUnavailable("candidate tree is not immutable")
        return tree

    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]:
        """Every path the imported candidate changed from `starting` (`raw_changes`), read in the intake repository
        only, after `hand_over`; the worker's workspace is never read."""
        if not _FULL_SHA.fullmatch(starting) or not _FULL_SHA.fullmatch(revision):
            raise CandidateUnavailable("candidate or starting revision is not a full SHA")
        result = self._intake_git(*RAW_DIFF, starting, revision, "--")
        if result.returncode:
            raise CandidateUnavailable("intake git operation failed")
        return raw_changes(result.stdout.decode(errors="replace"))

    def intake_ref(self, correlation: str) -> str:
        return f"refs/intake/{ref_safe(correlation)}"

    def hand_over(self, correlation: str, workspace: Path, claimed: str, starting: str) -> str:
        """Steps 0-4 of packet 0.4: the worker bundles exactly `claimed`; the control plane copies, verifies and
        imports only that SHA into `refs/intake/<c>`, and checks identity and ancestry. Answers the intake ref."""
        if not _FULL_SHA.fullmatch(claimed) or not _FULL_SHA.fullmatch(starting):
            raise CandidateUnavailable("candidate or starting revision is not a full SHA")
        name = f"{ref_safe(correlation)}.bundle"
        handoff = self.handoff / name
        self._as_worker(workspace, "git", "update-ref", "refs/alienintent/handoff", claimed)
        self._as_worker(workspace, "git", "bundle", "create", "-q", str(handoff), "refs/alienintent/handoff")
        self.ensure_intake()
        copy = self._copy_bundle(handoff, self.bundles / name)
        ref = self.intake_ref(correlation)
        if self._intake_git("bundle", "verify", "-q", str(copy)).returncode:
            raise CandidateUnavailable("candidate bundle fails verification")
        if self._intake_git("-c", "transfer.fsckObjects=true", "-c", "protocol.allow=never",
                            "-c", "protocol.file.allow=always", "fetch", "-q", "--no-tags", "--no-write-fetch-head",
                            "--", str(copy), f"+{claimed}:{ref}").returncode:
            raise CandidateUnavailable("candidate bundle does not hold the claimed commit")
        if self._intake_out("rev-parse", "--verify", f"{ref}^{{commit}}") != claimed:
            raise CandidateUnavailable("imported candidate differs from the claim")
        if self._intake_git("merge-base", "--is-ancestor", starting, claimed).returncode:
            raise CandidateUnavailable("candidate does not descend from the starting revision")
        tree = self._intake_out("rev-parse", "--verify", f"{claimed}^{{tree}}")
        if tree == self._intake_out("rev-parse", "--verify", f"{starting}^{{tree}}"):
            raise CandidateUnavailable("candidate tree equals the starting revision's tree")
        return ref

    def _copy_bundle(self, source: Path, target: Path) -> Path:
        """Step 0: copy the worker's bundle, from a descriptor opened without following a link and checked by
        `fstat` to be a regular file owned by the worker, into the Founder-only intake-bundles folder."""
        self.bundles.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.bundles, 0o700)
        try:
            descriptor = open_worker_file(source, self.worker_uid)
        except OSError as error:
            raise CandidateUnavailable("candidate bundle is not a regular worker-owned file") from error
        try:
            target.unlink(missing_ok=True)
            out = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            try:
                while chunk := os.read(descriptor, 1 << 20):
                    os.write(out, chunk)
            finally:
                os.close(out)
        except OSError as error:
            raise CandidateUnavailable("candidate bundle cannot be copied") from error
        finally:
            os.close(descriptor)
        return target.resolve()

    # --- publication and the worker's candidate clones -------------------------------------------------------------

    def publish_intake(self, correlation: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
        """Step 5: push `refs/intake/<c>` from the intake repository to the candidate branch on the packets remote's
        URL, then the existing read-back (ls-remote and a fresh control-plane clone)."""
        ref = self.intake_ref(correlation)
        if self._intake_out("rev-parse", "--verify", f"{ref}^{{commit}}") != revision:
            raise CandidateUnavailable("intake ref differs from requested candidate revision")
        url = self.remote_url()
        self._intake_out("push", "-q", "--", url, f"{ref}:refs/heads/{branch}")
        return self._read_back(url, branch, revision, verifier_workspace, self.intake)

    def candidate_clone(self, prefix: str, invocation_id: str, owner: str, candidate: CandidateRef) -> GitWorkspace:
        """A VERIFIER or CLOSURE worker clone of the exact candidate, after the control plane's custody checks (the
        `ls-remote` equality of the candidate branch, the digest, and the intake ref at that SHA)."""
        try:
            prefix_part, reference = candidate.locator.rsplit("#", 1)
            remote = prefix_part.removeprefix("git:")
            branch, revision = reference.rsplit("@", 1)
            if not remote or prefix_part == remote or not branch.startswith("candidate/") \
                    or not _FULL_SHA.fullmatch(revision):
                raise ValueError
        except ValueError:
            raise CandidateUnavailable("candidate cannot be independently retrieved") from None
        if candidate.content_digest != f"sha256:{sha256(revision.encode()).hexdigest()}":
            raise CandidateUnavailable("candidate digest does not match immutable revision")
        if not (self.intake / "HEAD").is_file():  # no intake holds no candidate: a custody refusal, decided locally
            raise CandidateUnavailable("intake does not hold the exact candidate")
        try:  # the one read of the remote: failing to reach it is infrastructure, never a custody judgment
            advertised = self._intake_out("ls-remote", "--", self.remote_url(), f"refs/heads/{branch}")
        except CandidateUnavailable:
            raise CandidateUnreadable("the packets remote holding the candidate cannot be read") from None
        if not advertised or advertised.split()[0] != revision:
            raise CandidateUnavailable("candidate revision is not retrievable for verifier")
        ref = f"refs/intake/{branch.removeprefix('candidate/')}"
        if self._intake_out("rev-parse", "--verify", f"{ref}^{{commit}}") != revision:
            raise CandidateUnavailable("intake does not hold the exact candidate")
        return self._workspaces.candidate_clone(prefix, invocation_id, owner, self.intake, ref, revision)

    def read_result(self, invocation_id: str, name: str, limit: int = 1 << 20) -> bytes:
        """A worker-written result `<results>/<invocation>/<name>`: the folder opened without following a link and
        checked by `fstat` (a directory owned by the worker), then the file relative to that folder's descriptor,
        opened and checked the same way; only that descriptor is read. Any refusal is OSError."""
        if "/" in name or name in {"", ".", ".."} or "/" in invocation_id or invocation_id in {"", ".", ".."}:
            raise OSError("unsafe result name")
        folder = os.open(self.results / invocation_id, WORKER_FILE_FLAGS | os.O_DIRECTORY)
        try:
            status = os.fstat(folder)
            if not stat.S_ISDIR(status.st_mode) or status.st_uid != self.worker_uid:
                raise OSError("results folder is not the worker's")
            descriptor = os.open(name, WORKER_FILE_FLAGS, dir_fd=folder)
        finally:
            os.close(folder)
        try:
            status = os.fstat(descriptor)
            if not stat.S_ISREG(status.st_mode) or status.st_uid != self.worker_uid:
                raise OSError("not a regular file owned by the worker")
            return read_descriptor(descriptor, limit)
        finally:
            os.close(descriptor)
