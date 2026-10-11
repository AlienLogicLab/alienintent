"""publish_refs against a local bare remote (acceptance check 10, the publishing operation itself).

Exactly the given refs are pushed by explicit refspec, force only when asked, the remote is read back, any failure is
PublicationFailed naming the refs, and a retry pushes only what the remote lacks.
"""
from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from alienintent.invocation_runtime.adapters import git_source_control as module
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable, CandidateUnreadable
from alienintent.invocation_runtime.ports.source_control import PublicationFailed, PublishRef

IDENTITY = ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    remote, clone = tmp_path / "remote.git", tmp_path / "clone"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    git(tmp_path, "init", "-q", "-b", "main", str(clone))
    commits = []
    for n in range(3):
        (clone / "f").write_text(str(n))
        git(clone, "add", "f")
        git(clone, *IDENTITY, "commit", "-qm", f"c{n}")
        commits.append(git(clone, "rev-parse", "HEAD"))
    git(clone, "remote", "add", "origin", str(remote))
    git(clone, "tag", "unrelated-local-tag", commits[0])
    return clone, remote, commits


def remote_refs(clone: Path) -> dict[str, str]:
    lines = git(clone, "ls-remote", "origin").splitlines()
    return {name: commit for commit, name in (line.split("\t") for line in lines)}


@pytest.fixture
def recorded(monkeypatch):
    calls = []
    original = subprocess.run

    def run(args, *rest, **options):
        calls.append(list(args))
        return original(args, *rest, **options)

    monkeypatch.setattr(module.subprocess, "run", run)
    return calls


def test_pushes_exactly_the_given_refs_by_explicit_refspec(repo, recorded):
    clone, _, commits = repo
    refs = (PublishRef("refs/heads/packets", commits[1]), PublishRef("refs/tags/work/abc", commits[0], force=True))
    GitSourceControl().publish_refs(clone, "origin", refs)
    assert remote_refs(clone) == {"refs/heads/packets": commits[1], "refs/tags/work/abc": commits[0]}
    pushes = [c for c in recorded if c[1] == "push"]
    assert [c[-1] for c in pushes] == [f"{commits[1]}:refs/heads/packets", f"+{commits[0]}:refs/tags/work/abc"]
    assert not any(a in ("--tags", "--mirror", "--all") or "*" in a for c in pushes for a in c)


def test_retry_pushes_only_what_is_missing_and_a_complete_retry_changes_nothing(repo, recorded):
    clone, _, commits = repo
    branch, tag = PublishRef("refs/heads/packets", commits[2]), PublishRef("refs/tags/work/x", commits[1], force=True)
    GitSourceControl().publish_refs(clone, "origin", (branch,))  # A fault after the branch push, before the tag.
    recorded.clear()
    GitSourceControl().publish_refs(clone, "origin", (branch, tag))
    assert [c[-1] for c in recorded if c[1] == "push"] == [f"+{commits[1]}:refs/tags/work/x"]
    before = remote_refs(clone)
    recorded.clear()
    GitSourceControl().publish_refs(clone, "origin", (branch, tag))
    assert [c for c in recorded if c[1] == "push"] == [] and remote_refs(clone) == before


def test_a_moved_tag_moves_on_the_remote_only_with_force(repo):
    clone, _, commits = repo
    GitSourceControl().publish_refs(clone, "origin", (PublishRef("refs/tags/work/x", commits[0], force=True),))
    with pytest.raises(PublicationFailed, match="rejected") as error:
        GitSourceControl().publish_refs(clone, "origin", (PublishRef("refs/tags/work/x", commits[1]),))
    assert error.value.refs == ("refs/tags/work/x",) and remote_refs(clone)["refs/tags/work/x"] == commits[0]
    GitSourceControl().publish_refs(clone, "origin", (PublishRef("refs/tags/work/x", commits[1], force=True),))
    assert remote_refs(clone)["refs/tags/work/x"] == commits[1]


def test_rejected_push_is_publication_failed_naming_the_refs(repo, tmp_path):
    clone, remote, commits = repo
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    refs = (PublishRef("refs/heads/packets", commits[0]), PublishRef("refs/tags/work/y", commits[0], force=True))
    with pytest.raises(PublicationFailed, match="push of refs/heads/packets rejected") as error:
        GitSourceControl().publish_refs(clone, "origin", refs)
    assert error.value.refs == ("refs/heads/packets", "refs/tags/work/y") and remote_refs(clone) == {}


def test_read_back_that_differs_is_publication_failed(repo, monkeypatch):
    clone, _, commits = repo
    original = GitSourceControl._remote_refs
    reads = []

    def stale(self, clone_path, remote, refs):
        reads.append(1)
        found = original(self, clone_path, remote, refs)
        return found if len(reads) == 1 else {k: commits[2] for k in found}

    monkeypatch.setattr(GitSourceControl, "_remote_refs", stale)
    with pytest.raises(PublicationFailed, match="read-back differs"):
        GitSourceControl().publish_refs(clone, "origin", (PublishRef("refs/heads/packets", commits[0]),))


def test_unknown_remote_and_invalid_refs_are_refused(repo):
    clone, _, commits = repo
    with pytest.raises(PublicationFailed):
        GitSourceControl().publish_refs(clone, "nowhere", (PublishRef("refs/heads/packets", commits[0]),))
    for ref, commit in (("refs/tags/*", commits[0]), ("packets", commits[0]), ("refs/heads/x", "abc")):
        with pytest.raises(ValueError):
            PublishRef(ref, commit)
    assert "unrelated-local-tag" not in "".join(remote_refs(clone))


def test_remote_revision_reads_only_the_exact_branch_and_creates_or_pushes_nothing(repo, tmp_path):
    """RESTART-CONTINUATION check 3: the read-only remote answer `work decide` reconciles a publication with."""
    from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable
    clone, remote, commits = repo
    git(clone, "push", "-q", "origin", f"{commits[1]}:refs/heads/candidate/exact",
        f"{commits[2]}:refs/heads/x/refs/heads/candidate/absent", f"{commits[2]}:refs/heads/candidate/absent-longer")
    before, listing = remote_refs(clone), sorted(tmp_path.iterdir())
    control = GitSourceControl()
    assert control.remote_revision(clone, "origin", "candidate/exact") == commits[1]
    assert control.remote_revision(clone, "origin", "candidate/absent") is None  # only longer refs share its tail
    assert remote_refs(clone) == before and sorted(tmp_path.iterdir()) == listing
    git(clone, "remote", "set-url", "origin", str(tmp_path / "missing.git"))
    with pytest.raises(CandidateUnavailable):
        control.remote_revision(clone, "origin", "candidate/exact")
    with pytest.raises(CandidateUnavailable):
        control.remote_revision(tmp_path / "no-worktree", "origin", "candidate/exact")


# --- WORKER-CREDENTIAL-BOUNDARY: candidate hand-over by exact object identity (acceptance checks 1, 3 and 6b) -------
import getpass  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import signal  # noqa: E402
import stat  # noqa: E402
import sys  # noqa: E402

from alienintent.execution_coordination.domain.custody import CandidateRef  # noqa: E402
from alienintent.invocation_runtime.adapters.git_source_control import IntakeSourceControl  # noqa: E402
from alienintent.invocation_runtime.adapters.git_worktree import WorkerCloneAdapter  # noqa: E402
from alienintent.invocation_runtime.application.real_worker import read_verdict  # noqa: E402
from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable  # noqa: E402

USER = getpass.getuser()
FAKE_SUDO = r'''#!{python}
"""FAKE SUDO (test data): records its arguments and working directory, then runs the command as the test's own user.
It accepts only `-n -u <user> -- env -i ...` and `-n -u <user> kill ...`; a kill of a single pid is recorded only."""
import json, os, sys
argv = sys.argv[1:]
with open({log!r}, "a") as sink:
    sink.write(json.dumps({{"argv": argv, "cwd": os.getcwd()}}) + "\n")
if argv[:3] != ["-n", "-u", {user!r}]:
    sys.exit(97)
rest = argv[3:]
if rest[:1] == ["kill"]:
    if not rest[-1].startswith("-"):
        sys.exit(0)
elif rest[:3] != ["--", "env", "-i"]:
    sys.exit(98)
else:
    rest = rest[1:]
os.execvp(rest[0], rest)
'''


def install_fake_sudo(bin_dir: Path, monkeypatch, user: str = USER) -> Path:
    """A fake `sudo` first on PATH; answers the path of its JSON-lines log."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    log = bin_dir / "sudo.log"
    sudo = bin_dir / "sudo"
    sudo.write_text(FAKE_SUDO.format(python=sys.executable, log=str(log), user=user))
    sudo.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return log


def sudo_calls(log: Path) -> list[dict]:
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def record_git(monkeypatch) -> list[dict]:
    """Every git process this (control-plane) process starts: argv, working directory and GIT_DIR."""
    calls: list[dict] = []
    popen = subprocess.Popen

    class Recording(popen):
        def __init__(self, args, *rest, **kwargs):
            argv = [str(a) for a in args] if isinstance(args, (list, tuple)) else [str(args)]
            if Path(argv[0]).name == "git":
                env = kwargs.get("env")
                calls.append({"argv": argv, "cwd": str(kwargs.get("cwd") or os.getcwd()),
                              "git_dir": (os.environ if env is None else env).get("GIT_DIR")})
            super().__init__(args, *rest, **kwargs)
    monkeypatch.setattr(subprocess, "Popen", Recording)
    return calls


def outside(calls: list[dict], *roots: Path) -> None:
    """Acceptance check 1: no control-plane git runs in, names GIT_DIR in, or has an argument under a worker root."""
    for call in calls:
        for value in (call["cwd"], call["git_dir"], *call["argv"]):
            if value is None:
                continue
            for root in roots:
                assert not str(value).startswith(str(root)), call


class Handover:
    """A packets clone of a bare remote, a launch folder and the hand-over over a fake sudo (the worker is the test's
    own user, so ownership by uid is checked against that uid)."""

    def __init__(self, tmp_path: Path, monkeypatch) -> None:
        self.tmp = tmp_path
        self.remote, self.packets, self.launch = tmp_path / "remote.git", tmp_path / "packets", tmp_path / "launch"
        git(tmp_path, "init", "-q", "--bare", "-b", "main", str(self.remote))
        git(tmp_path, "init", "-q", "-b", "main", str(self.packets))
        (self.packets / "f").write_text("base\n")
        git(self.packets, "add", "f")
        git(self.packets, *IDENTITY, "commit", "-qm", "base")
        git(self.packets, "remote", "add", "origin", str(self.remote))
        git(self.packets, "push", "-q", "origin", "main")
        self.base = git(self.packets, "rev-parse", "HEAD")
        for name in ("worker", "results", "handoff"):
            (self.launch / name).mkdir(parents=True, mode=0o711)
        self.log = install_fake_sudo(tmp_path / "bin", monkeypatch)
        self.env = {"HOME": str(tmp_path / "worker-home"), "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x.invalid",
                    "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x.invalid"}
        self.workspaces = WorkerCloneAdapter(self.packets, self.launch / "worker", self.launch / "results", USER,
                                             self.env)
        self.source = IntakeSourceControl(self.packets, "origin", self.launch, USER, os.getuid(), self.env,
                                          dict(os.environ), self.workspaces)

    def produce(self, correlation: str = "c1") -> tuple[Path, str]:
        workspace = self.workspaces.allocate(correlation, "owner", self.base).path
        (workspace / "f").write_text("candidate\n")
        git(workspace, "add", "f")
        git(workspace, *IDENTITY, "commit", "-qm", "candidate")
        return workspace, git(workspace, "rev-parse", "HEAD")

    def bundle(self, workspace: Path, name: str, *refs: str) -> Path:
        path = self.tmp / name
        git(workspace, "bundle", "create", "-q", str(path), *refs)
        return path


@pytest.fixture
def handover(tmp_path, monkeypatch) -> Handover:
    return Handover(tmp_path, monkeypatch)


def test_the_candidate_is_imported_by_exact_identity_and_planted_worker_metadata_changes_nothing(handover, monkeypatch):
    """Checks 1 and 3: planted refs, replace refs, alternates, config, config.worktree, commondir and .git file do not
    change the imported candidate, the publication or the diff; no control-plane git touches a worker path."""
    workspace, claimed = handover.produce()
    dot_git = workspace / ".git"
    other = handover.tmp / "other"
    git(handover.tmp, "init", "-q", str(other))
    (dot_git / "refs/heads/main").write_text(handover.base + "\n")
    (dot_git / "refs/replace").mkdir(parents=True)
    (dot_git / "refs/replace" / handover.base).write_text(claimed + "\n")
    (dot_git / "objects/info/alternates").write_text(str(other / ".git/objects") + "\n")
    evil = handover.tmp / "evil.git"
    git(workspace, "config", "remote.origin.url", str(evil))
    git(workspace, "config", f"url.{evil}.insteadOf", str(handover.remote))
    git(workspace, "config", "core.hooksPath", str(handover.tmp / "hooks"))
    (dot_git / "config.worktree").write_text(f"[remote \"origin\"]\n\turl = {evil}\n")
    calls = record_git(monkeypatch)
    assert handover.source.revision(workspace) == claimed
    ref = handover.source.hand_over("c1", workspace, claimed, handover.base)
    # After the bundle: a commondir and a .git file pointing elsewhere are planted too.
    (dot_git / "commondir").write_text(str(other / ".git") + "\n")
    (workspace / "sub").mkdir()
    (workspace / "sub/.git").write_text(f"gitdir: {other / '.git'}\n")
    intake = handover.launch / "intake.git"
    assert ref == "refs/intake/c1" and git(intake, "rev-parse", ref) == claimed
    assert git(intake, "for-each-ref", "--format=%(refname)").splitlines() == ["refs/intake/c1"]
    assert not (intake / "objects/info/alternates").exists()
    assert git(intake, "rev-parse", f"{handover.base}^{{tree}}") == git(handover.packets, "rev-parse", "HEAD^{tree}")
    candidate = handover.source.publish_intake("c1", "candidate/c1", claimed, handover.launch / "verifier" / "p-c1")
    assert git(handover.remote, "rev-parse", "refs/heads/candidate/c1") == claimed and not evil.exists()
    assert candidate.locator.endswith(f"candidate/c1@{claimed}")
    clone = handover.source.candidate_clone("verifier", "v1", "owner", candidate).path
    outside(calls, handover.launch / "worker", handover.launch / "handoff", handover.launch / "results")
    assert clone == handover.launch / "worker" / "verifier-v1" and git(clone, "rev-parse", "HEAD") == claimed
    for call in calls:
        if call["git_dir"] == str(intake):
            assert call["argv"][1:5] == ["-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false"], call
    # Every worker-side step went through the one rule.
    for call in sudo_calls(handover.log):
        assert call["argv"][:7] == ["-n", "-u", USER, "--", "env", "-i", "PATH=/usr/bin:/bin"], call


_ORIGINAL_COPY = IntakeSourceControl._copy_bundle


def _swap_bundle(monkeypatch, replace):
    """Replace the worker's hand-over file just before the control plane copies it."""
    copy = _ORIGINAL_COPY

    def swapped(self, source, target):
        replace(source)
        return copy(self, source, target)
    monkeypatch.setattr(IntakeSourceControl, "_copy_bundle", swapped)


def test_a_bundle_that_lacks_the_claim_or_its_prerequisite_is_refused_and_its_ref_names_are_ignored(handover, monkeypatch):
    """Check 3: only the claimed SHA is fetched; another commit, a failing prerequisite, or bundle ref names that
    point elsewhere never become the candidate."""
    workspace, claimed = handover.produce()
    git(workspace, "tag", "base-tag", handover.base)
    base_only = handover.bundle(workspace, "base.bundle", "base-tag")
    thin = handover.bundle(workspace, "thin.bundle", f"{handover.base}..HEAD")
    _swap_bundle(monkeypatch, lambda source: source.write_bytes(thin.read_bytes()))
    with pytest.raises(CandidateUnavailable, match="verification"):  # its prerequisite is not in the intake
        handover.source.hand_over("c1", workspace, claimed, handover.base)
    _swap_bundle(monkeypatch, lambda source: source.write_bytes(base_only.read_bytes()))
    with pytest.raises(CandidateUnavailable, match="does not hold the claimed commit"):
        handover.source.hand_over("c2", workspace, claimed, handover.base)
    intake = handover.launch / "intake.git"
    assert git(intake, "for-each-ref", "--format=%(refname)") == ""
    git(workspace, "branch", "-f", "main", handover.base)
    named = handover.bundle(workspace, "named.bundle", "main", "HEAD")
    _swap_bundle(monkeypatch, lambda source: source.write_bytes(named.read_bytes()))
    assert handover.source.hand_over("c3", workspace, claimed, handover.base) == "refs/intake/c3"
    assert git(intake, "for-each-ref", "--format=%(refname) %(objectname)") == f"refs/intake/c3 {claimed}"


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo"])
def test_a_hand_over_path_that_is_not_a_regular_worker_file_is_refused_without_blocking(handover, monkeypatch, kind):
    """Check 3: a symlink (to a valid Founder-owned bundle), a directory or a FIFO at the hand-over path is refused
    by `fstat` on the descriptor; nothing is imported and the open never blocks."""
    workspace, claimed = handover.produce()
    valid = handover.bundle(workspace, "founder.bundle", "HEAD")

    def replace(source: Path) -> None:
        source.unlink()
        if kind == "symlink":
            source.symlink_to(valid)
        elif kind == "directory":
            source.mkdir()
        else:
            os.mkfifo(source)
    _swap_bundle(monkeypatch, replace)
    signal.alarm(10)
    try:
        with pytest.raises(CandidateUnavailable, match="regular worker-owned file"):
            handover.source.hand_over("c1", workspace, claimed, handover.base)
    finally:
        signal.alarm(0)
    assert git(handover.launch / "intake.git", "for-each-ref", "--format=%(refname)") == ""


def test_the_bundle_is_copied_into_the_founder_only_folder_and_only_that_copy_is_verified_and_fetched(handover, monkeypatch):
    """Check 3: `bundle verify` and `fetch` name only the intake-bundles copy (mode 0700 folder), by absolute path,
    with the working directory and GIT_DIR the intake repository."""
    workspace, claimed = handover.produce()
    calls = record_git(monkeypatch)
    handover.source.hand_over("c1", workspace, claimed, handover.base)
    bundles = handover.launch / "intake-bundles"
    assert oct(bundles.stat().st_mode & 0o777) == "0o700"
    used = [call for call in calls if "bundle" in call["argv"] or "fetch" in call["argv"]]
    assert len(used) == 2 and all(call["cwd"] == call["git_dir"] == str(handover.launch / "intake.git")
                                  for call in used)
    assert all(str(bundles / "c1.bundle") in call["argv"] for call in used)
    outside(calls, handover.launch / "worker", handover.launch / "handoff")


def _candidate(revision: str) -> CandidateRef:
    from hashlib import sha256
    digest = f"sha256:{sha256(revision.encode()).hexdigest()}"
    return CandidateRef.source_revision(digest, f"git:/remote#candidate/c1@{revision}")


@pytest.mark.parametrize("kind", ["symlink", "fifo", "folder-symlink", "regular"])
def test_results_are_read_only_through_a_checked_descriptor_never_a_worker_chosen_path(handover, kind):
    """Check 6b: a symlinked verdict is refused and its target never read; a FIFO, or the `<c>` folder swapped for a
    symlink to a Founder-owned folder, is refused without blocking; a regular worker file is read."""
    revision = "a" * 40
    founder = handover.tmp / "founder"
    founder.mkdir()
    (founder / "verdict.json").write_text(json.dumps({"revision": revision, "verdict": "accept", "findings": []}))
    results = handover.launch / "results"
    folder = results / "v1"
    if kind == "folder-symlink":
        folder.symlink_to(founder)
    else:
        folder.mkdir()
        if kind == "symlink":
            (folder / "verdict.json").symlink_to(founder / "verdict.json")
        elif kind == "fifo":
            os.mkfifo(folder / "verdict.json")
        else:
            (folder / "verdict.json").write_text("{}")
    signal.alarm(10)
    try:
        if kind == "regular":
            assert handover.source.read_result("v1", "verdict.json") == b"{}"
            return
        with pytest.raises(OSError):
            handover.source.read_result("v1", "verdict.json")
        outcome = read_verdict(folder / "verdict.json", _candidate(revision),
                               lambda path: handover.source.read_result(path.parent.name, path.name))
        assert outcome.kind == "verdict-missing"
    finally:
        signal.alarm(0)


def _regular_files_owned_by_another_user(monkeypatch) -> None:
    """`fstat` answers a uid other than the configured worker uid for every regular file (folders are unchanged)."""
    real = os.fstat

    def fstat(descriptor):
        status = real(descriptor)
        if not stat.S_ISREG(status.st_mode):
            return status
        fields = list(status[:10])
        fields[4] = status.st_uid + 1  # st_uid
        return os.stat_result(fields)
    monkeypatch.setattr(module.os, "fstat", fstat)


def test_a_candidate_that_does_not_descend_from_the_starting_revision_is_refused_at_import(handover):
    """Check 3: a claimed commit whose ancestry lacks the starting revision is refused, even when both commits are
    in the intake; no intake ref names it."""
    workspace, first = handover.produce("c1")
    assert handover.source.hand_over("c1", workspace, first, handover.base) == "refs/intake/c1"
    git(workspace, "checkout", "-q", "--detach", handover.base)
    (workspace / "f").write_text("sibling\n")
    git(workspace, *IDENTITY, "commit", "-qam", "sibling")
    sibling = git(workspace, "rev-parse", "HEAD")
    with pytest.raises(CandidateUnavailable, match="does not descend from the starting revision"):
        handover.source.hand_over("c2", workspace, sibling, first)


@pytest.mark.parametrize("kind", ["same-sha", "empty-commit", "commit-then-revert"])
def test_hand_over_refuses_a_candidate_with_the_starting_tree(handover, kind):
    workspace = handover.workspaces.allocate("c1", "owner", handover.base).path
    if kind == "empty-commit":
        git(workspace, *IDENTITY, "commit", "-qm", "empty", "--allow-empty")
    elif kind == "commit-then-revert":
        (workspace / "new.txt").write_text("change")
        git(workspace, "add", "new.txt")
        git(workspace, *IDENTITY, "commit", "-qm", "change")
        git(workspace, *IDENTITY, "revert", "--no-edit", "HEAD")
    claimed = git(workspace, "rev-parse", "HEAD")
    with pytest.raises(CandidateUnavailable, match="candidate tree equals the starting revision's tree"):
        handover.source.hand_over("c1", workspace, claimed, handover.base)


def test_a_hand_over_file_not_owned_by_the_worker_is_refused(handover, monkeypatch):
    """Check 3: a regular hand-over file whose `fstat` owner is not the worker uid is refused; nothing is imported."""
    workspace, claimed = handover.produce()
    _regular_files_owned_by_another_user(monkeypatch)
    with pytest.raises(CandidateUnavailable, match="regular worker-owned file"):
        handover.source.hand_over("c1", workspace, claimed, handover.base)
    intake = handover.launch / "intake.git"
    assert not intake.exists() or git(intake, "for-each-ref", "--format=%(refname)") == ""


def test_a_result_file_not_owned_by_the_worker_is_refused_and_its_bytes_are_never_used(handover, monkeypatch):
    """Check 6b: a regular result file in the worker's folder whose `fstat` owner is not the worker uid is refused;
    its descriptor is never read and the verdict counts as missing."""
    revision = "a" * 40
    folder = handover.launch / "results" / "v1"
    folder.mkdir()
    (folder / "verdict.json").write_text(json.dumps({"revision": revision, "verdict": "accept", "findings": []}))
    reads: list[int] = []
    real_read = module.read_descriptor
    monkeypatch.setattr(module, "read_descriptor", lambda descriptor, limit: reads.append(descriptor)
                        or real_read(descriptor, limit))
    _regular_files_owned_by_another_user(monkeypatch)
    with pytest.raises(OSError):
        handover.source.read_result("v1", "verdict.json")
    outcome = read_verdict(folder / "verdict.json", _candidate(revision),
                           lambda path: handover.source.read_result(path.parent.name, path.name))
    assert outcome.kind == "verdict-missing" and reads == []


def test_the_worker_clone_and_fetch_give_the_ownership_exception_to_upload_pack_itself(handover):
    """Live finding (check 8(e)): `git -c safe.directory=...` on the worker's command line never reaches git's
    ownership check for a Founder-owned source (the local clone checks in-process, and the spawned upload-pack does
    not inherit it), so the worker's clone refused the packets clone as dubious. The PRODUCER clone uses the
    transport (`--no-local`) and the VERIFIER/CLOSURE fetch names the intake repository, each with the exception
    given to upload-pack itself."""
    workspace, claimed = handover.produce()
    ref = handover.source.hand_over("c1", workspace, claimed, handover.base)
    handover.workspaces.candidate_clone("verifier", "c2", "owner", handover.launch / "intake.git", ref, claimed)
    calls = [json.loads(line)["argv"] for line in handover.log.read_text().splitlines()]
    gits = [argv[argv.index("git"):] for argv in calls if "git" in argv]
    clone = next(argv for argv in gits if "clone" in argv)
    fetch = next(argv for argv in gits if "fetch" in argv)
    assert "--no-local" in clone and "--no-hardlinks" not in clone
    assert f"--upload-pack=git -c safe.directory={handover.packets / '.git'} upload-pack" in clone
    assert f"--upload-pack=git -c safe.directory={handover.launch / 'intake.git'} upload-pack" in fetch
    assert not [word for argv in (clone, fetch) for word in argv if word.startswith("safe.directory=")]


# --- CUSTODY-READ-INFRASTRUCTURE-RETRY (Founder decision 48): "cannot read the candidate right now" is not "custody is
# invalid". Only a remote that cannot be read is CandidateUnreadable; a remote that answers without the exact candidate
# stays the custody refusal CandidateUnavailable.

def _published(repo, tmp_path):
    from hashlib import sha256
    from alienintent.execution_coordination.domain.custody import CandidateRef
    clone, remote, commits = repo
    git(clone, "push", "-q", "origin", f"{commits[2]}:refs/heads/candidate/c1")
    return lambda locator_remote=remote, branch="candidate/c1": CandidateRef.source_revision(
        "sha256:" + sha256(commits[2].encode()).hexdigest(), f"git:{locator_remote}#{branch}@{commits[2]}")


def test_retrieval_from_a_remote_that_cannot_be_read_is_unreadable_never_a_custody_judgment(repo, tmp_path):
    candidate = _published(repo, tmp_path)
    with pytest.raises(CandidateUnreadable):
        GitSourceControl().retrieve_for_verification(candidate(tmp_path / "unreachable.git"), tmp_path / "v1")
    assert not (tmp_path / "v1").exists()
    retrieved = GitSourceControl().retrieve_for_verification(candidate(), tmp_path / "v2")
    assert retrieved.verify_admissible


@pytest.mark.parametrize("case", ["branch-missing", "branch-elsewhere"])
def test_retrieval_from_a_remote_that_answers_without_the_exact_candidate_is_a_custody_refusal(repo, tmp_path, case):
    clone, remote, commits = repo
    candidate = _published(repo, tmp_path)
    if case == "branch-elsewhere":
        git(clone, "push", "-q", "-f", "origin", f"{commits[1]}:refs/heads/candidate/c1")
    with pytest.raises(CandidateUnavailable) as refused:
        GitSourceControl().retrieve_for_verification(
            candidate(branch="candidate/gone") if case == "branch-missing" else candidate(), tmp_path / "v1")
    assert not isinstance(refused.value, CandidateUnreadable)


def test_a_worker_clone_of_a_candidate_whose_remote_cannot_be_read_is_unreadable_and_a_missing_one_a_refusal(
        handover, monkeypatch):
    """The worker path reads the remote once (`ls-remote` of the packets remote); everything after reads the local
    intake. That one read failing is CandidateUnreadable; a remote answering without the candidate branch, or an
    intake not holding the exact candidate, stays the custody refusal."""
    from dataclasses import replace
    workspace, claimed = handover.produce()
    handover.source.hand_over("c1", workspace, claimed, handover.base)
    candidate = handover.source.publish_intake("c1", "candidate/c1", claimed, handover.launch / "verifier" / "p-c1")
    real = handover.source.remote_url
    monkeypatch.setattr(handover.source, "remote_url", lambda: str(handover.tmp / "unreachable.git"))
    with pytest.raises(CandidateUnreadable):
        handover.source.candidate_clone("verifier", "v1", "owner", candidate)
    monkeypatch.setattr(handover.source, "remote_url", real)
    gone = replace(candidate, locator=candidate.locator.replace("#candidate/c1@", "#candidate/gone@"))
    with pytest.raises(CandidateUnavailable) as refused:
        handover.source.candidate_clone("verifier", "v2", "owner", gone)
    assert not isinstance(refused.value, CandidateUnreadable)
    clone = handover.source.candidate_clone("verifier", "v3", "owner", candidate).path
    assert git(clone, "rev-parse", "HEAD") == claimed


def test_a_clone_that_fails_after_the_remote_answered_is_unreadable(repo, tmp_path, monkeypatch):
    candidate = _published(repo, tmp_path)
    real = GitSourceControl._git

    def failing_clone(self, *args, cwd=None):
        if args[0] == "clone":
            raise CandidateUnavailable("git operation failed")
        return real(self, *args, cwd=cwd)
    monkeypatch.setattr(GitSourceControl, "_git", failing_clone)
    with pytest.raises(CandidateUnreadable):
        GitSourceControl().retrieve_for_verification(candidate(), tmp_path / "v1")


def test_a_worker_clone_from_an_intake_that_is_gone_fails_closed_never_retried_as_unreadable(handover):
    """No intake repository means it does not hold the candidate: a custody refusal, decided locally before the
    remote is asked, never an infrastructure retry."""
    import shutil
    workspace, claimed = handover.produce()
    handover.source.hand_over("c1", workspace, claimed, handover.base)
    candidate = handover.source.publish_intake("c1", "candidate/c1", claimed, handover.launch / "verifier" / "p-c1")
    shutil.rmtree(handover.launch / "intake.git")
    with pytest.raises(CandidateUnavailable) as refused:
        handover.source.candidate_clone("verifier", "v1", "owner", candidate)
    assert not isinstance(refused.value, CandidateUnreadable)
