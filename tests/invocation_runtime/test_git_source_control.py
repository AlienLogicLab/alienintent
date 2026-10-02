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
