"""Registering hand-written packets, importing earlier work and reading a record (acceptance checks 1-4).

Every case uses a temporary project database, a local clone and a local bare remote through the composed
WorkRegistry. Labels such as PY-SELF-00 and issue numbers below are TEST DATA, never historical records.
"""
from __future__ import annotations

import multiprocessing
from pathlib import Path
import sqlite3
import subprocess

import pytest

from alienintent.composition.work_registry import WorkRegistry
from alienintent.context_assembly.adapters import work_item_repository as adapter_module
from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
from alienintent.context_assembly.domain.work_identity import (
    CommitNotRetained, GitReadFailed, ParentNotRegistered, PointerMismatch, StoredPointer)
from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from tests.context_assembly.test_initial_compilation import PROJECT, REPO, Project, all_rows, git
from tests.context_assembly.test_work_identity_service import commit_file, remote_refs

A = "fx-a"
PATH = "docs/work-units/python/packet.md"
PACKET = b"# Work unit: fixture packet\n\n**Label:** `FROM-TEXT`\n**Parent:** `FROM-TEXT-PARENT`\n\nDo this.\n"
REQUEST = f"packet:{REPO}/{PATH}"


class Fixture:
    def __init__(self, root: Path):
        root.mkdir(mode=0o700, exist_ok=True)
        from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
        SQLiteOperationalStore(root / "a.sqlite")
        self.project = Project(root / "project", {A: root / "a.sqlite"})
        self.clone = self.project.clone
        self.registry = WorkRegistry(self.project.configuration)
        self.records, self.items = self.registry.records, self.registry.items
        self.evidence = LocalEvidenceRepository(root / "evidence", PROJECT, A)

    def rows(self) -> list[dict]:
        return all_rows(self.project.database)

    def commit(self, data: bytes = PACKET, branch: str = "main", path: str = PATH) -> str:
        return commit_file(self.clone, branch, path, data)

    def register(self, commit: str, data: bytes = PACKET, path: str = PATH, label: str = "PACKET-ONE",
                 parent_id: str | None = None):
        return self.records.register(data, REPO, path, commit, label, parent_id=parent_id)

    def evidence_count(self) -> int:
        return len(list((self.evidence.root / "objects").iterdir()))

    def database_text(self) -> str:
        connection = sqlite3.connect(self.project.database)
        try:
            return "\n".join(connection.iterdump())
        finally:
            connection.close()


@pytest.fixture
def fx(tmp_path) -> Fixture:
    return Fixture(tmp_path / "fx")


def assessment(name: str = "A") -> dict:
    """A reference document in the evidence repository's own form (TEST DATA)."""
    return {"project": PROJECT, "profile": A, "logical_id": "assessment-" + name,
            "revision_digest": "sha256:" + "a" * 64, "locator": "evidence:assessment-" + name}


# --- check 1: register a packet -------------------------------------------------------------------------------------


def test_register_creates_one_pointer_row_and_a_repeat_changes_nothing(fx):
    before = fx.evidence_count()
    commit = fx.commit()
    item = fx.register(commit)
    assert (item.request_ref, item.label, item.state, item.parent_id, item.kind) == (
        REQUEST, "PACKET-ONE", "CAPTURE", None, "BIU")
    assert item.pointer == StoredPointer(REPO, PATH, commit)
    assert remote_refs(fx.clone)["refs/tags/work/" + item.id] == commit
    rows = fx.rows()
    # A repeat returns the row unchanged, even with another label or a newer commit of the same path.
    newer = fx.commit(PACKET + b"edited\n")
    assert fx.register(commit) == item
    assert fx.records.register(PACKET + b"edited\n", REPO, PATH, newer, "OTHER-LABEL") == item
    assert fx.rows() == rows and len(rows) == 1
    # The database holds no packet text; no evidence record is written.
    assert b"Do this" not in fx.database_text().encode() and "FROM-TEXT" not in fx.database_text()
    assert fx.evidence_count() == before


@pytest.mark.parametrize("case", ["one-byte", "baseline", "deleted-branch"])
def test_wrong_commit_or_bytes_is_refused_and_nothing_is_written(fx, case):
    if case == "one-byte":  # An uncommitted edit of the packet file.
        commit, data, error = fx.commit(), PACKET[:-1] + b"!", PointerMismatch
    elif case == "baseline":  # The implementation baseline given as the packet commit.
        baseline = git(fx.clone, "rev-parse", "main").decode().strip()
        fx.commit()
        commit, data, error = baseline, PACKET, PointerMismatch
    else:
        commit, data, error = fx.commit(branch="draft"), PACKET, CommitNotRetained
        git(fx.clone, "branch", "-q", "-D", "draft")
    with pytest.raises(error):
        fx.register(commit, data)
    assert fx.rows() == [] and "refs/tags/work/" not in git(fx.clone, "show-ref").decode()


def test_fault_before_commit_leaves_no_row_and_a_rerun_creates_it(fx, monkeypatch):
    commit = fx.commit()
    original = SQLiteWorkItemRepository._created

    def fault(self, request_ref):
        original(self, request_ref)  # The insert happened inside the open transaction...
        raise RuntimeError("process died before COMMIT")  # ...and the process dies before COMMIT.

    monkeypatch.setattr(SQLiteWorkItemRepository, "_created", fault)
    with pytest.raises(RuntimeError):
        fx.register(commit)
    assert fx.rows() == []
    monkeypatch.setattr(SQLiteWorkItemRepository, "_created", original)
    item = fx.register(commit)
    assert [row["id"] for row in fx.rows()] == [item.id]


def _register_worker(configuration, commit, barrier, results):
    records = WorkRegistry(configuration).records
    barrier.wait()
    try:
        results.put(("ok", records.register(PACKET, REPO, PATH, commit, "PACKET-ONE").id))
    except Exception as error:  # Reported to the parent: a concurrent tag push may fail and is repaired by a repeat.
        results.put((type(error).__name__, str(error)))


def test_two_processes_registering_at_once_end_with_one_row(fx):
    commit = fx.commit()
    context = multiprocessing.get_context("spawn")
    barrier, results = context.Barrier(2), context.Queue()
    processes = [context.Process(target=_register_worker,
                                 args=(fx.project.configuration, commit, barrier, results)) for _ in range(2)]
    for process in processes:
        process.start()
    outcomes = [results.get(timeout=60) for _ in processes]
    for process in processes:
        process.join(timeout=60)
        assert process.exitcode == 0
    [row] = fx.rows()
    assert all(value == row["id"] for kind, value in outcomes if kind == "ok"), outcomes
    assert all(kind in ("ok", "PublicationFailed", "TagWriteFailed") for kind, _ in outcomes), outcomes
    item = fx.register(commit)
    assert item.id == row["id"] and remote_refs(fx.clone)["refs/tags/work/" + item.id] == commit


# --- check 2: optional parent -----------------------------------------------------------------------------------------


def test_parent_is_the_argument_never_the_packet_text(fx):
    parent = fx.register(fx.commit(path="docs/parent.md"), path="docs/parent.md", label="PARENT")
    child = fx.register(fx.commit(path="docs/child.md"), path="docs/child.md", label="CHILD", parent_id=parent.id)
    assert child.parent_id == parent.id and [c.id for c in fx.registry.identities.children(parent.id)] == [child.id]
    assert fx.records.show(parent.id).children == (child,)
    # Without --parent the parent stays empty and the label is the argument, whatever the packet text says.
    solo = fx.register(fx.commit(), label="SOLO")
    assert (solo.parent_id, solo.label) == (None, "SOLO")
    retired = fx.registry.identities.retire(child.id)
    assert retired.retired and retired.parent_id == parent.id
    assert [c.id for c in fx.records.show(parent.id).children] == [child.id]


def test_parent_naming_no_row_is_refused(fx):
    with pytest.raises(ParentNotRegistered):
        fx.register(fx.commit(), parent_id="00000000-0000-4000-8000-00000000dead")
    assert fx.rows() == []


# --- check 3: import of earlier work ----------------------------------------------------------------------------------


def test_import_records_done_without_a_transition_or_invented_evidence(fx, monkeypatch):
    calls = []
    monkeypatch.setattr(fx.items, "set_state", lambda *a: calls.append(a))
    before = fx.evidence_count()
    commit = fx.commit()
    item = fx.records.import_completed(PACKET, REPO, PATH, commit, "PY-SELF-00", "153", {})
    assert (item.request_ref, item.label, item.state, item.pointer) == (
        "issue:153", "PY-SELF-00", "DONE", StoredPointer(REPO, PATH, commit))
    assert (item.assessment_ref, item.approval_ref, item.verification_ref) == (None, None, None)
    rows = fx.rows()
    again = fx.records.import_completed(PACKET, REPO, PATH, commit, "OTHER", "153",
                                        {"assessment": assessment()})
    assert again == item and fx.rows() == rows
    # A fixture item imported with one assessment reference stores exactly that reference and no other.
    other = fx.commit(b"fixture item\n", path="docs/fixture.md")
    given = fx.records.import_completed(b"fixture item\n", REPO, "docs/fixture.md", other, "FIXTURE", "900",
                                        {"assessment": assessment(), "approval": None, "verification": None})
    assert given.state == "DONE" and given.assessment_ref is not None
    assert vars(given.assessment_ref) == assessment()
    assert (given.approval_ref, given.verification_ref) == (None, None)
    assert calls == [] and fx.evidence_count() == before
    assert remote_refs(fx.clone)["refs/tags/work/" + item.id] == commit


# --- check 4: show ----------------------------------------------------------------------------------------------------


def test_show_returns_row_parent_children_and_the_pinned_packet(fx):
    parent = fx.register(fx.commit(b"parent\n", path="docs/parent.md"), b"parent\n", "docs/parent.md", "PARENT")
    commit = fx.commit()
    item = fx.register(commit, parent_id=parent.id)
    grandchild = fx.register(fx.commit(b"grandchild\n", path="docs/g.md"), b"grandchild\n", "docs/g.md", "G",
                             parent_id=item.id)
    record = fx.records.show(item.id)
    assert (record.item, record.parent, record.children) == (item, parent, (grandchild,))
    assert record.packet == git(fx.clone, "show", f"{commit}:{PATH}") == PACKET
    assert fx.records.show("PACKET-ONE") == record and fx.records.show("missing") is None
    # A new commit of the path changes neither the row nor the text show returns.
    fx.commit(b"a newer revision\n")
    assert fx.records.show(item.id) == record


class _Counting:
    """A real connection that records every statement it runs."""

    def __init__(self, connection, statements):
        self._connection, self._statements = connection, statements

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def execute(self, sql, *args):
        self._statements.append(sql)
        return self._connection.execute(sql, *args)


@pytest.mark.parametrize("revisions", [0, 12])
def test_show_is_three_statements_and_one_git_call(fx, monkeypatch, revisions):
    parent = fx.register(fx.commit(b"parent\n", path="docs/parent.md"), b"parent\n", "docs/parent.md", "PARENT")
    item = fx.register(fx.commit(), parent_id=parent.id)
    for n in range(revisions):
        fx.commit(PACKET + b"revision %d\n" % n)
    statements, calls = [], []
    connect, run = SQLiteWorkItemRepository._connect, subprocess.run
    monkeypatch.setattr(SQLiteWorkItemRepository, "_connect", lambda self: _Counting(connect(self), statements))

    def recording(args, *rest, **options):
        calls.append(list(args))
        return run(args, *rest, **options)

    monkeypatch.setattr(adapter_module.subprocess, "run", recording)
    record = fx.records.show(item.id)
    assert record.packet == PACKET and record.parent == parent
    assert (statements[0], statements[-1], len(statements)) == ("BEGIN IMMEDIATE", "COMMIT", 5)
    assert all(s.startswith("SELECT") for s in statements[1:-1])  # Row, parent, children.
    assert [c[1] for c in calls] == ["show"]


def test_failed_git_show_is_git_read_failed_naming_the_path(fx, monkeypatch):
    item = fx.register(fx.commit())
    original = adapter_module.SQLiteWorkItemRepository._git

    def broken(self, location, *args, **options):
        if args[0] == "show":
            return subprocess.CompletedProcess(["git", *args], 128, b"", b"fatal: corrupt object")
        return original(self, location, *args, **options)

    monkeypatch.setattr(adapter_module.SQLiteWorkItemRepository, "_git", broken)
    with pytest.raises(GitReadFailed) as error:
        fx.records.show(item.id)
    assert error.value.values[0] == "git show" and PATH in error.value.values[1]
    assert error.value.code == "GIT_READ_FAILED"
