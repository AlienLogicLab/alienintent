"""The work identity service over its real SQLite/Git adapter (acceptance checks 1, 2, 4, 6, 9, 10 outside a compile,
and the set_state rules of check 3).

Every case uses a temporary project database, a local clone and a local bare remote. Names such as PY-10 and the
requirement keys below are TEST DATA, never historical records.
"""
from __future__ import annotations

import multiprocessing
from pathlib import Path
import re
import sqlite3
import subprocess

import pytest

from alienintent.composition.work_registry import WorkRegistry
from alienintent.context_assembly.adapters import work_item_repository as adapter_module
from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository
from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.domain.work_identity import (
    RESERVATIONS, CommitNotRetained, RequestRef, GitReadFailed, IllegalTransition, InvalidRequestRef, LabelInUse,
    MigrationConflict, ParentNotRegistered, Pointer, PointerMismatch, PointerPresent, TagWriteFailed,
    TransactionHeld, is_uuid)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.invocation_runtime.adapters import git_source_control as publisher_module
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl
from alienintent.invocation_runtime.ports.source_control import PublicationFailed
from tests.context_assembly.test_initial_compilation import PACKETS_BRANCH, PROJECT, REPO, Project, all_rows, git

ROOT = Path(__file__).resolve().parents[2]
A, B = "fx-a", "fx-b"
INSTRUCTIONS = b"# Packet\n\nDo exactly this.\n"
COMMITTER = ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


def commit_file(clone: Path, branch: str, path: str, data: bytes) -> str:
    """Commit one file on `branch` (created from main when absent) and return to main."""
    exists = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=clone,
                            capture_output=True).returncode == 0
    if branch != "main":
        git(clone, "checkout", "-q", *(() if exists else ("-b",)), branch)
    target = clone / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    git(clone, "add", path)
    git(clone, *COMMITTER, "commit", "-qm", f"fixture {path}")
    commit = git(clone, "rev-parse", "HEAD").decode().strip()
    if branch != "main":
        git(clone, "checkout", "-q", "main")
    return commit


def tag_commit(clone: Path, identity: str) -> str | None:
    result = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/tags/work/{identity}"], cwd=clone,
                            capture_output=True, text=True)
    return result.stdout.strip() or None


def remote_refs(clone: Path) -> dict[str, str]:
    lines = git(clone, "ls-remote", "origin").decode().splitlines()
    return {name: commit for commit, name in (line.split("\t") for line in lines)}


class Fixture:
    def __init__(self, root: Path):
        root.mkdir(mode=0o700, exist_ok=True)
        self.profiles = {A: root / "a.sqlite", B: root / "b.sqlite"}
        self.stores = {name: SQLiteOperationalStore(path) for name, path in self.profiles.items()}
        self.project = Project(root / "project", self.profiles)
        self.clone = self.project.clone
        self.registry = WorkRegistry(self.project.configuration)
        self.service, self.items = self.registry.identities, self.registry.items

    def rows(self) -> list[dict]:
        return all_rows(self.project.database)

    def packet(self, branch: str = "main", path: str = "docs/p.md", data: bytes = INSTRUCTIONS) -> Pointer:
        return Pointer(REPO, path, commit_file(self.clone, branch, path, data), data)

    def record(self, profile: str, reservations: dict[str, str]) -> None:
        """TEST DATA in the shape of the old per-profile reservation record."""
        store = self.stores[profile]
        version, _ = store.read_state(profile, RESERVATIONS)
        store.commit(profile, RESERVATIONS, version, {"schema_version": 1, "reservations": reservations,
                                                      "history": []})


@pytest.fixture
def fx(tmp_path) -> Fixture:
    return Fixture(tmp_path / "fx")


def evidence(name: str) -> Ref:
    return Ref(PROJECT, A, name, "sha256:" + "a" * 64, "evidence:" + name)


# --- separate processes ----------------------------------------------------------------------------------------


def _service(database: str, clone: str) -> WorkIdentityService:
    from alienintent.context_assembly.ports.work_item_repository import RepositoryLocation
    locations = {REPO: RepositoryLocation(Path(clone), "origin", "main", PACKETS_BRANCH)}
    items = SQLiteWorkItemRepository(Path(database), locations)
    return WorkIdentityService(items, GitSourceControl(), locations, {})


def _register_worker(database, clone, barrier, results, operation):
    service = _service(database, clone)
    barrier.wait()
    try:
        if operation == "register":
            item = service.register("requirement:SF-REQ-1", "concurrent", "BIU")
        elif operation == "import":
            item = service.import_completed("issue:153", "PY-SELF-00", "BIU", None, {})
        else:
            item = service.set_state(operation, "SPECIFY")
        results.put(("ok", item.id))
    except Exception as error:  # Reported to the parent, which asserts the exact type.
        results.put((type(error).__name__, str(error)))


def run_concurrently(fx: Fixture, operation: str) -> list[tuple[str, str]]:
    context = multiprocessing.get_context("spawn")
    barrier, results = context.Barrier(2), context.Queue()
    processes = [context.Process(target=_register_worker,
                                 args=(str(fx.project.database), str(fx.clone), barrier, results, operation))
                 for _ in range(2)]
    for process in processes:
        process.start()
    outcomes = [results.get(timeout=60) for _ in processes]
    for process in processes:
        process.join(timeout=60)
        assert process.exitcode == 0
    return sorted(outcomes)


# --- check 1: repeat, crash, concurrency, separate fields ------------------------------------------------------


def test_repeat_returns_the_same_row_and_fields_stay_separate(fx):
    first = fx.service.register("requirement:SF-REQ-1", "Label one", "BIU")
    again = fx.service.register("requirement:SF-REQ-1", "Label one", "BIU")
    assert first == again and is_uuid(first.id) and len(fx.rows()) == 1
    assert (first.request_ref, first.label, first.parent_id, first.state) == (
        "requirement:SF-REQ-1", "Label one", None, "CAPTURE")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", first.created_at)
    # A repeat with a different label, parent or pointer returns the existing row unchanged.
    parent = fx.service.register("requirement:SF-REQ-2", "Parent", "BIU")
    changed = fx.service.register("requirement:SF-REQ-1", "Another label", "BIU", parent.id, fx.packet())
    assert changed == first and len(fx.rows()) == 2
    with pytest.raises(LabelInUse):
        fx.service.register("requirement:SF-REQ-3", "Label one", "BIU")
    assert len(fx.rows()) == 2


@pytest.mark.parametrize("request_ref", [
    "label:PY-10", "PY-10", "packet:docs/p.md", "packet:unknown/docs/p.md", "packet:alienintent/",
    "issue:abc", "issue:0", "legacy:not a name", "legacy:00000000-0000-4000-8000-000000000000", "requirement:",
    "requirement:a/b"])
def test_request_reference_kind_and_value_are_checked(fx, request_ref):
    with pytest.raises(InvalidRequestRef):
        fx.service.register(request_ref, "L", "BIU")
    assert fx.rows() == []


def test_crash_before_commit_leaves_no_row_and_rerun_creates_it(fx, monkeypatch):
    original = SQLiteWorkItemRepository._created

    def fault(self, request_ref):
        original(self, request_ref)  # The insert happened inside the open transaction...
        raise RuntimeError("process died before COMMIT")  # ...and the process dies before COMMIT.

    monkeypatch.setattr(SQLiteWorkItemRepository, "_created", fault)
    with pytest.raises(RuntimeError):
        fx.service.register("requirement:SF-REQ-1", "L", "BIU")
    assert fx.rows() == []
    monkeypatch.setattr(SQLiteWorkItemRepository, "_created", original)
    item = fx.service.register("requirement:SF-REQ-1", "L", "BIU")
    assert [row["id"] for row in fx.rows()] == [item.id]


def test_two_processes_register_one_row(fx):
    outcomes = run_concurrently(fx, "register")
    assert [o[0] for o in outcomes] == ["ok", "ok"] and outcomes[0][1] == outcomes[1][1]
    assert [row["id"] for row in fx.rows()] == [outcomes[0][1]]


def test_uuid_and_timestamp_come_only_from_the_adapter():
    production = ROOT / "src" / "alienintent"
    users = {p.relative_to(production).as_posix() for p in production.rglob("*.py")
             if re.search(r"\buuid4\b|strftime\(", p.read_text()) and "context_assembly" in p.as_posix()}
    assert users == {"context_assembly/adapters/work_item_repository.py"}
    service = (production / "context_assembly/application/work_identity_service.py").read_text()
    assert not re.search(r"^\s*(?:import|from)\s+(?:uuid|datetime|time|subprocess|sqlite3)\b", service, re.M)


# --- check 2: migration preserves names and owners -------------------------------------------------------------

SNAPSHOT = {"active": [f"PY-0{n}" for n in range(1, 9)], "retired": ["PY-09"], "reserved": ["PY-09B", "PY-10"]}


def test_migration_preserves_names_owners_and_retirement(fx):
    fx.record(A, {"requirement:R": "PY-10"})
    fx.record(B, {"requirement:Q": "PY-09"})
    report = fx.service.migrate(SNAPSHOT, [A, B])
    rows = {row["id"]: row for row in fx.rows()}
    assert set(rows) == {*SNAPSHOT["active"], "PY-09", "PY-09B", "PY-10"} and set(report.created) == set(rows)
    assert all(r["label"] == i and r["kind"] == "BIU" and r["commit"] is None and r["state"] == "CAPTURE"
               for i, r in rows.items())
    assert rows["PY-10"]["request_ref"] == "requirement:R"
    assert (rows["PY-09"]["request_ref"], rows["PY-09"]["retired_at"] is not None) == ("requirement:Q", True)
    assert all(rows[n]["request_ref"] == "legacy:" + n and rows[n]["retired_at"] is None
               for n in [*SNAPSHOT["active"], "PY-09B"])
    again = fx.service.migrate(SNAPSHOT, [A, B])
    assert (again.created, again.rekeyed) == ((), ()) and {r["id"]: r for r in fx.rows()} == rows
    # Existing names are returned, never recreated or renumbered.
    assert fx.service.register("requirement:R", "anything", "BIU").id == "PY-10"
    retired = fx.service.register("requirement:Q", "anything", "BIU")
    assert (retired.id, retired.retired) == ("PY-09", True) and len(fx.rows()) == len(rows)


def test_omitted_profile_is_rekeyed_and_reported(fx):
    fx.record(A, {"requirement:R": "PY-10"})
    fx.record(B, {"requirement:Q": "PY-09"})
    first = fx.service.migrate(SNAPSHOT, [A])
    assert fx.items.find("PY-09").request_ref == "legacy:PY-09"
    second = fx.service.migrate(SNAPSHOT, [A, B])
    assert second.created == () and second.rekeyed == (("PY-09", "requirement:Q"),)
    assert fx.items.find("PY-09").request_ref == "requirement:Q" and len(fx.rows()) == len(first.created)


@pytest.mark.parametrize("records", [
    {A: {"requirement:R": "PY-10"}, B: {"requirement:S": "PY-10"}},   # one name under two keys
    {A: {"requirement:R": "PY-10"}, B: {"requirement:R": "PY-08"}},   # one key with two names
])
def test_conflicting_records_roll_back(fx, records):
    for profile, reservations in records.items():
        fx.record(profile, reservations)
    with pytest.raises(MigrationConflict) as error:
        fx.service.migrate(SNAPSHOT, [A, B])
    assert any("profile:" + A in v for v in error.value.values) and any("profile:" + B in v for v in error.value.values)
    assert fx.rows() == []


def test_record_from_another_project_and_registry_difference_roll_back(fx):
    with pytest.raises(MigrationConflict):
        fx.service.migrate(SNAPSHOT, [A, "other-project-profile"])
    fx.service.migrate(SNAPSHOT, [A])
    fx.record(A, {"requirement:R": "PY-10"})
    other = fx.service.register("requirement:R2", "PY-01-other", "BIU")
    fx.record(B, {"requirement:R2": "PY-01"})  # requirement:R2 already names another row.
    before = fx.rows()
    with pytest.raises(MigrationConflict):
        fx.service.migrate(SNAPSHOT, [A, B])
    assert fx.rows() == before and fx.items.find("PY-10").request_ref == "legacy:PY-10"
    assert fx.items.find(other.id).request_ref == "requirement:R2"


def test_empty_migration_is_a_no_op(fx):
    """Check 7: no saved assignments -> success, no row, and a rerun changes nothing."""
    empty = {"active": [], "retired": [], "reserved": []}
    for _ in range(2):
        report = fx.service.migrate(empty, [A, B])
        assert (report.created, report.rekeyed, report.unchanged) == ((), (), ())
        assert fx.rows() == []


# --- check 4: optional parent and retirement by identifier -----------------------------------------------------


def test_optional_parent_children_and_retirement(fx):
    independent = fx.service.register("requirement:SOLO", "Independent", "BIU")
    assert independent.parent_id is None
    parent = fx.service.register("requirement:PARENT", "Parent", "BIU")
    children = [fx.service.register(f"requirement:CHILD-{n}", f"Child {n}", "BIU", parent.id) for n in range(4)]
    assert {c.id for c in fx.service.children(parent.id)} == {c.id for c in children}
    with pytest.raises(ParentNotRegistered):
        fx.service.register("requirement:ORPHAN", "Orphan", "BIU", "00000000-0000-4000-8000-00000000dead")
    retired = fx.service.retire(children[0].id)
    assert retired.retired and {k: v for k, v in vars(retired).items() if k not in ("retired_at", "updated_at")} == {
        k: v for k, v in vars(children[0]).items() if k not in ("retired_at", "updated_at")}
    assert children[0].id in {c.id for c in fx.service.children(parent.id)}
    assert fx.service.find(children[0].id) == retired == fx.service.retire(children[0].id)  # Set once.
    assert fx.service.register("requirement:CHILD-0", "x", "BIU") == retired and len(fx.rows()) == 6


def test_own_id_as_parent_is_refused_by_the_check(fx):
    item = fx.service.register("requirement:SELF", "Self", "BIU")
    connection = sqlite3.connect(fx.project.database)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute("UPDATE work_item SET parent_id = id WHERE id = ?", (item.id,))
    finally:
        connection.close()


# --- check 3 (state): legal transitions only --------------------------------------------------------------------


def test_set_state_accepts_only_legal_transitions(fx):
    item = fx.service.register("requirement:STATE", "State", "BIU")
    with pytest.raises(IllegalTransition):
        fx.service.set_state(item.id, "DONE")
    assert fx.service.find(item.id).state == "CAPTURE"
    assert fx.service.set_state(item.id, "SPECIFY").state == "SPECIFY"
    with pytest.raises(IllegalTransition):
        fx.service.set_state(item.id, "SPECIFY")


def test_two_processes_set_state_one_succeeds(fx):
    item = fx.service.register("requirement:STATE", "State", "BIU")
    outcomes = run_concurrently(fx, item.id)
    assert [o[0] for o in outcomes] == ["IllegalTransition", "ok"]
    assert fx.service.find(item.id).state == "SPECIFY"


# --- check 6: the pointer holds exactly the registered instructions ----------------------------------------------


def test_pointer_is_verified_retained_tagged_and_published(fx):
    pointer = fx.packet()
    item = fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    assert (item.pointer.repo, item.pointer.path, item.pointer.commit) == (REPO, "docs/p.md", pointer.commit)
    assert fx.service.find(item.id).pointer == item.pointer
    assert tag_commit(fx.clone, item.id) == pointer.commit
    assert remote_refs(fx.clone)["refs/tags/work/" + item.id] == pointer.commit
    # A new commit to the same path changes nothing in the row.
    commit_file(fx.clone, "main", "docs/p.md", b"edited\n")
    assert fx.service.find(item.id) == item


@pytest.mark.parametrize("case", ["one-byte", "no-path", "baseline", "deleted-branch", "other-tag", "no-branch"])
def test_wrong_pointer_is_refused_and_nothing_is_written(fx, case):
    if case == "one-byte":
        good = fx.packet()
        pointer, error = Pointer(REPO, good.path, good.commit, INSTRUCTIONS[:-1] + b"!"), PointerMismatch
    elif case == "no-path":  # A retained commit that does not contain the path.
        other = commit_file(fx.clone, "main", "docs/other.md", INSTRUCTIONS)
        pointer, error = Pointer(REPO, "docs/p.md", other, INSTRUCTIONS), PointerMismatch
    elif case == "baseline":  # The contract baseline is where implementation starts, not the packet's commit.
        baseline = git(fx.clone, "rev-parse", "main").decode().strip()
        fx.packet()
        pointer, error = Pointer(REPO, "docs/p.md", baseline, INSTRUCTIONS), PointerMismatch
    elif case == "deleted-branch":
        pointer = fx.packet("draft")
        git(fx.clone, "branch", "-q", "-D", "draft")
        error = CommitNotRetained
    elif case == "other-tag":
        pointer = fx.packet("draft")
        git(fx.clone, "tag", "unrelated", pointer.commit)
        git(fx.clone, "branch", "-q", "-D", "draft")
        error = CommitNotRetained
    else:  # No packets branch and no work tag exist yet: a plain miss, never GIT_READ_FAILED.
        pointer = fx.packet("loose")
        git(fx.clone, "branch", "-q", "-D", "loose")
        error = CommitNotRetained
    with pytest.raises(error) as raised:
        fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    if error is PointerMismatch:
        assert "bytes differ" in str(raised.value) and "docs/p.md" in str(raised.value)
    assert fx.rows() == [] and "refs/tags/work/" not in git(fx.clone, "show-ref").decode()


def test_retained_check_is_three_direct_lookups_whatever_the_tags(fx, monkeypatch):
    for n in range(40):
        git(fx.clone, "tag", f"noise-{n}")
    pointer = fx.packet(PACKETS_BRANCH)
    calls = []
    original = subprocess.run

    def recording(args, *rest, **options):
        calls.append(list(args))
        return original(args, *rest, **options)

    monkeypatch.setattr(adapter_module.subprocess, "run", recording)
    item = fx.items.register(RequestRef("packet", "alienintent/docs/p.md"), "P", "BIU", None, pointer)
    calls.clear()
    fx.items.set_pointer(item.id, pointer)
    assert sum(1 for c in calls if c[1:3] == ["merge-base", "--is-ancestor"]) <= 3
    assert not any(c[1] in ("for-each-ref", "show-ref", "log", "rev-list") or c[1:3] in (["tag", "-l"],
                   ["tag", "--list"]) or (c[1] == "tag" and len(c) == 2) for c in calls)


def test_deleted_branch_still_retrieved_through_the_work_tag(fx):
    pointer = fx.packet(PACKETS_BRANCH)
    item = fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    git(fx.clone, "branch", "-q", "-D", PACKETS_BRANCH)
    assert fx.items.set_pointer(item.id, pointer) == item  # Equal bytes, retained only by work/<id>.
    git(fx.clone, "tag", "-d", "work/" + item.id)
    with pytest.raises(CommitNotRetained):
        fx.items.set_pointer(item.id, pointer)


def test_failed_tag_write_after_commit_is_typed_and_repaired_by_a_repeat(fx, monkeypatch):
    pointer = fx.packet()
    original = adapter_module.SQLiteWorkItemRepository._git

    def no_tag(self, location, *args, **options):
        if args[0] == "tag":
            return subprocess.CompletedProcess(["git", *args], 1, b"", b"disk full")
        return original(self, location, *args, **options)

    monkeypatch.setattr(adapter_module.SQLiteWorkItemRepository, "_git", no_tag)
    with pytest.raises(TagWriteFailed, match="database committed"):
        fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    [row] = fx.rows()
    assert row["commit"] == pointer.commit and tag_commit(fx.clone, row["id"]) is None
    monkeypatch.setattr(adapter_module.SQLiteWorkItemRepository, "_git", original)
    item = fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    assert item.id == row["id"] and tag_commit(fx.clone, item.id) == pointer.commit


def test_rolled_back_caller_transaction_tags_nothing(fx):
    pointer = fx.packet()
    with pytest.raises(RuntimeError):
        with fx.items.transaction():
            item = fx.items.register(RequestRef("packet", "alienintent/docs/p.md"), "P", "BIU", None,
                                     pointer)
            raise RuntimeError("caller rolls back")
    assert fx.rows() == [] and tag_commit(fx.clone, item.id) is None
    with fx.items.transaction():
        with pytest.raises(TransactionHeld):
            fx.service.register("packet:alienintent/docs/p.md", "P", "BIU", pointer=pointer)


def test_set_pointer_moves_only_at_capture(fx):
    pointer = fx.packet()
    item = fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    assert fx.items.set_pointer(item.id, pointer).pointer == item.pointer
    revised = fx.packet(data=b"revised instructions\n")
    moved = fx.items.set_pointer(item.id, revised)
    assert (moved.pointer.commit, moved.state) == (revised.commit, "CAPTURE")
    assert tag_commit(fx.clone, item.id) == revised.commit
    fx.service.set_state(item.id, "SPECIFY")
    third = fx.packet(data=b"third\n")
    with pytest.raises(PointerPresent):
        fx.items.set_pointer(item.id, third)
    assert fx.service.find(item.id).pointer == moved.pointer


def test_database_holds_no_packet_text_and_no_evidence_is_written(fx, tmp_path):
    from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
    repository = LocalEvidenceRepository(tmp_path / "evidence", PROJECT, A)
    before = sorted((repository.root / "objects").iterdir())
    fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=fx.packet())
    connection = sqlite3.connect(fx.project.database)
    try:
        dump = "\n".join(connection.iterdump())
    finally:
        connection.close()
    assert "Do exactly this" not in dump and sorted((repository.root / "objects").iterdir()) == before


@pytest.mark.parametrize("command", ["merge-base", "cat-file"])
def test_unexpected_git_failure_is_typed_and_rolled_back(fx, monkeypatch, command):
    pointer = fx.packet()
    original = adapter_module.SQLiteWorkItemRepository._git

    def broken(self, location, *args, **options):
        if args[0] == command:
            return subprocess.CompletedProcess(["git", *args], 128, b"", b"fatal: corrupt object")
        return original(self, location, *args, **options)

    monkeypatch.setattr(adapter_module.SQLiteWorkItemRepository, "_git", broken)
    with pytest.raises(GitReadFailed) as error:
        fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    assert error.value.values[0] == "git " + command and "docs/p.md" in error.value.values[1]
    assert fx.rows() == []


# --- check 9: import of completed work through the same service --------------------------------------------------


def test_import_records_completed_work_once_with_exact_evidence(fx, monkeypatch):
    calls = []
    monkeypatch.setattr(fx.items, "set_state", lambda *a: calls.append(a))
    pointer = fx.packet()
    item = fx.service.import_completed("issue:153", "PY-SELF-00", "BIU", pointer, {"assessment": evidence("A")})
    assert (item.state, item.assessment_ref, item.approval_ref, item.verification_ref) == (
        "DONE", evidence("A"), None, None)
    assert calls == [] and remote_refs(fx.clone)["refs/tags/work/" + item.id] == pointer.commit
    again = fx.service.import_completed("issue:153", "Other", "BIU", fx.packet(data=b"other\n"),
                                        {"approval": evidence("B")})
    assert again == item and len(fx.rows()) == 1
    bare = fx.service.import_completed("issue:154", "PY-SELF-01", "BIU", None, {})
    assert (bare.assessment_ref, bare.approval_ref, bare.verification_ref, bare.state) == (None, None, None, "DONE")


def test_import_checks_kind_and_pointer_and_never_promotes(fx):
    for request_ref in ("requirement:X", "packet:alienintent/docs/p.md", "legacy:PY-01"):
        with pytest.raises(InvalidRequestRef):
            fx.service.import_completed(request_ref, "L", "BIU", None, {})
    good = fx.packet()
    with pytest.raises(PointerMismatch):
        fx.service.import_completed("issue:153", "L", "BIU", Pointer(REPO, good.path, good.commit, b"x"), {})
    loose = fx.packet("loose", path="docs/q.md")
    git(fx.clone, "branch", "-q", "-D", "loose")
    with pytest.raises(CommitNotRetained):
        fx.service.import_completed("issue:153", "L", "BIU", loose, {})
    assert fx.rows() == []
    # An issue:<n> already registered (any state) is returned unchanged and never promoted to DONE.
    fx.items.register(RequestRef("issue", "155"), "Open work", "BIU", None, None)
    existing = fx.service.import_completed("issue:155", "Open work", "BIU", None, {"assessment": evidence("A")})
    assert (existing.state, existing.assessment_ref) == ("CAPTURE", None) and len(fx.rows()) == 1


def test_import_crash_and_concurrency_end_with_one_row(fx, monkeypatch):
    original = SQLiteWorkItemRepository._created

    def fault(self, request_ref):
        original(self, request_ref)
        raise RuntimeError("process died before COMMIT")

    monkeypatch.setattr(SQLiteWorkItemRepository, "_created", fault)
    with pytest.raises(RuntimeError):
        fx.service.import_completed("issue:153", "PY-SELF-00", "BIU", None, {})
    assert fx.rows() == []
    monkeypatch.setattr(SQLiteWorkItemRepository, "_created", original)
    outcomes = run_concurrently(fx, "import")
    assert [o[0] for o in outcomes] == ["ok", "ok"] and outcomes[0][1] == outcomes[1][1]
    assert [row["id"] for row in fx.rows()] == [outcomes[0][1]]


# --- check 10 outside a compile: register and import publish their tag -------------------------------------------


def test_registered_packet_survives_on_the_remote_without_its_branch(fx, tmp_path):
    pointer = fx.packet(PACKETS_BRANCH)
    git(fx.clone, "push", "-q", "origin", PACKETS_BRANCH)
    item = fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)
    git(fx.clone, "push", "-q", "origin", ":refs/heads/" + PACKETS_BRANCH)  # The source branch deleted there.
    fresh = tmp_path / "fresh"
    git(tmp_path, "clone", "-q", str(fx.project.remote), str(fresh))
    assert git(fresh, "show", f"{item.pointer.commit}:{item.pointer.path}") == INSTRUCTIONS
    assert remote_refs(fx.clone)["refs/tags/work/" + item.id] == pointer.commit


@pytest.mark.parametrize("operation", ["register", "import"])
def test_failed_push_leaves_the_row_and_a_repeat_publishes(fx, operation):
    pointer = fx.packet()
    remote = git(fx.clone, "remote", "get-url", "origin").decode().strip()
    git(fx.clone, "remote", "set-url", "origin", str(fx.project.root / "missing.git"))
    call = (lambda: fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=pointer)) \
        if operation == "register" else (lambda: fx.service.import_completed("issue:153", "P", "BIU", pointer, {}))
    with pytest.raises(PublicationFailed) as error:
        call()
    [row] = fx.rows()
    assert error.value.refs == ("refs/tags/work/" + row["id"],)
    git(fx.clone, "remote", "set-url", "origin", remote)
    item = call()
    assert item.id == row["id"] and remote_refs(fx.clone)["refs/tags/work/" + item.id] == pointer.commit


def test_every_push_goes_through_publish_refs(fx, monkeypatch):
    inside, pushes = [], []
    original_publish, original_run = GitSourceControl.publish_refs, subprocess.run

    def publish(self, clone, remote, refs):
        inside.append(True)
        try:
            return original_publish(self, clone, remote, refs)
        finally:
            inside.pop()

    def recording(args, *rest, **options):
        if list(args[:2]) == ["git", "push"]:
            pushes.append((bool(inside), list(args)))
        return original_run(args, *rest, **options)

    monkeypatch.setattr(GitSourceControl, "publish_refs", publish)
    monkeypatch.setattr(publisher_module.subprocess, "run", recording)
    monkeypatch.setattr(adapter_module.subprocess, "run", recording)
    fx.service.register("packet:alienintent/docs/p.md", "Packet", "BIU", pointer=fx.packet())
    fx.service.import_completed("issue:153", "Done", "BIU", fx.packet(path="docs/q.md", data=b"q\n"), {})
    assert pushes and all(through for through, _ in pushes)
    assert all(not any(a in ("--tags", "--mirror", "--all") or "*" in a for a in args) for _, args in pushes)
