"""SQLite and Git adapter behind WorkItemRepository: the declared owner and only writer of the `work_item` table.

The table's unique indexes, foreign key and check give every identity rule; `BEGIN IMMEDIATE` serializes writers,
so a repeated or concurrent request returns the one existing row. UUIDs and timestamps are generated only here.
Packet pointers are verified against Git, never trusted: `<commit>:<path>` must hold exactly the registered bytes
and the commit must be reachable from one of three named refs. The adapter also owns the packets branch (written
with `git fast-import`, never touching a working tree) and the lightweight `work/<id>` tags, which it sets only after
the outermost COMMIT succeeds. Publishing those refs to the remote is the caller's job through `publish_refs`.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import subprocess
import threading
from uuid import uuid4

from alienintent.context_assembly.domain.work_identity import (
    CAPTURE, DONE, EVIDENCE, KINDS, STATES, CloneUnavailable, CommitNotRetained, GitReadFailed, InvalidWorkItem,
    LabelInUse, MigrationEntry, ParentNotRegistered, Pointer, PointerMismatch, RegistryBusy, RegistryUnavailable,
    RequestRef,
    StoredPointer, TagWriteFailed, UnknownWorkItem, WorkIdentityRefused, WorkItem, check_evidence, check_kind,
    check_label, check_pointer_change, check_transition, valid_path)
from alienintent.context_assembly.domain.work_link import IssueAlreadyLinked, ItemAlreadyLinked
from alienintent.context_assembly.ports.work_item_repository import RepositoryLocation, WorkItemRepository
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import Ref

_SQL_LIST = lambda values: ", ".join(f"'{v}'" for v in values)  # noqa: E731 - closed constant sets only
SCHEMA = f"""
CREATE TABLE IF NOT EXISTS work_item (
    id TEXT NOT NULL PRIMARY KEY CHECK (id <> ''),
    request_ref TEXT NOT NULL UNIQUE CHECK (request_ref <> ''),
    label TEXT NOT NULL UNIQUE CHECK (label <> ''),
    parent_id TEXT REFERENCES work_item(id) CHECK (parent_id IS NOT id),
    kind TEXT NOT NULL CHECK (kind IN ({_SQL_LIST(KINDS)})),
    state TEXT NOT NULL CHECK (state IN ({_SQL_LIST(STATES)})),
    retired_at TEXT,
    repo TEXT,
    path TEXT,
    "commit" TEXT,
    assessment_ref TEXT,
    approval_ref TEXT,
    verification_ref TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK ((repo IS NULL AND path IS NULL AND "commit" IS NULL)
           OR (repo IS NOT NULL AND path IS NOT NULL AND length("commit") = 40))
)"""
NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"
COLUMNS = ("id, request_ref, label, parent_id, kind, state, retired_at, repo, path, \"commit\", assessment_ref, "
           "approval_ref, verification_ref, created_at, updated_at")
# The link to the item's one GitHub Issue and card (`work link`): added at open to a table that lacks them (SQLite
# cannot add a UNIQUE column), with a unique index giving one item per Issue.
LINK_COLUMNS = (("issue_number", "INTEGER"), ("issue_node_id", "TEXT"), ("card_id", "TEXT"))
LINK_INDEX = "CREATE UNIQUE INDEX IF NOT EXISTS work_item_issue ON work_item(issue_number)"
# One card names at most one item (the READY view's card lookup); NULLs are allowed for unlinked items.
CARD_INDEX = "CREATE UNIQUE INDEX IF NOT EXISTS work_item_card ON work_item(card_id)"
READ_COLUMNS = COLUMNS + "".join(", " + name for name, _ in LINK_COLUMNS)
INSERT = (f"INSERT INTO work_item ({COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, CASE WHEN ? THEN {NOW} END, ?, ?, ?, ?, ?, ?, "
          f"{NOW}, {NOW}) ON CONFLICT(request_ref) DO NOTHING")
ZERO = "0" * 40
COMMITTER = "AlienIntent Work Preparation <work-preparation@alienintent.invalid>"


class SQLiteWorkItemRepository(WorkItemRepository):
    """One project database file and the configured clone of each repository name.

    The only state is per thread: the open transaction's connection and the tags it will write after COMMIT, created
    at the outermost `transaction()` and dropped when it ends, on every path. Between transactions nothing is held."""

    def __init__(self, path: Path, repositories: Mapping[str, RepositoryLocation], *, busy_timeout: float = 5.0,
                 git_timeout: float = 120.0) -> None:
        self._path, self._repositories = path, dict(repositories)
        self._busy_timeout, self._git_timeout = busy_timeout, git_timeout
        self._local = threading.local()
        with self._session() as connection:
            self._execute(connection, SCHEMA)
            missing = self._missing_link_columns(connection)
        if missing:
            with self.transaction():  # Re-read under the write lock: another process may have added them.
                for name, kind in self._missing_link_columns(self._write()):
                    self._execute(self._write(), f"ALTER TABLE work_item ADD COLUMN {name} {kind}")
        with self._session() as connection:
            self._execute(connection, LINK_INDEX)
            self._execute(connection, CARD_INDEX)

    def _missing_link_columns(self, connection: sqlite3.Connection) -> list[tuple[str, str]]:
        present = {row["name"] for row in self._execute(connection, "PRAGMA table_info(work_item)").fetchall()}
        return [(name, kind) for name, kind in LINK_COLUMNS if name not in present]

    # --- connection and transaction ------------------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self._path, isolation_level=None, timeout=self._busy_timeout)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as error:
            raise RegistryUnavailable(str(self._path), str(error)) from error
        return connection

    @property
    def _connection(self) -> sqlite3.Connection | None:
        return getattr(self._local, "connection", None)

    @property
    def _pending(self) -> dict[tuple[str, str], str]:
        return self._local.pending

    @contextmanager
    def _session(self) -> Iterator[sqlite3.Connection]:
        """The open transaction's connection, or a short-lived autocommit one for a single read."""
        if self._connection is not None:
            yield self._connection
            return
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def in_transaction(self) -> bool:
        return self._connection is not None

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """`BEGIN IMMEDIATE` ... `COMMIT` (or `ROLLBACK` on any exception); nested calls join the outer one.
        Tags recorded inside are written only after the outermost COMMIT succeeded."""
        if self._connection is not None:
            yield
            return
        connection = self._connect()
        self._local.connection, self._local.pending = connection, {}
        try:
            self._execute(connection, "BEGIN IMMEDIATE")
            try:
                yield
                self._execute(connection, "COMMIT")
            except BaseException as error:
                self._rollback(connection, error)
                raise
        finally:
            pending = self._local.pending
            self._local.connection, self._local.pending = None, {}
            connection.close()
        self._write_tags(pending)

    @staticmethod
    def _rollback(connection: sqlite3.Connection, error: BaseException) -> None:
        """Roll back after `error`; a failing ROLLBACK never replaces it (closing the connection, which always
        follows, discards the open transaction) and is recorded on it as a note."""
        if not connection.in_transaction:
            return
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error as failure:
            error.add_note(f"ROLLBACK failed ({type(failure).__name__}: {failure}); the connection is closed, "
                           "which discards the transaction")

    @staticmethod
    def _execute(connection: sqlite3.Connection, sql: str, parameters: tuple = (), *, label: str | None = None,
                 parent: str | None = None, issue: int | None = None) -> sqlite3.Cursor:
        """One statement; constraint failures become typed refusals. Callers that can hit the label, parent or Issue
        constraint name the refused value explicitly; any other constraint is INVALID_WORK_ITEM."""
        try:
            return connection.execute(sql, parameters)
        except sqlite3.IntegrityError as error:
            kind, message = getattr(error, "sqlite_errorname", ""), str(error)
            if label is not None and kind == "SQLITE_CONSTRAINT_UNIQUE" and message.endswith("work_item.label"):
                raise LabelInUse(label) from error
            if parent is not None and kind == "SQLITE_CONSTRAINT_FOREIGNKEY":
                raise ParentNotRegistered(parent) from error
            if issue is not None and kind == "SQLITE_CONSTRAINT_UNIQUE" \
                    and message.endswith(("work_item.issue_number", "work_item.card_id")):  # An Issue has one card.
                raise IssueAlreadyLinked(str(issue)) from error
            raise InvalidWorkItem("constraint", message) from error
        except sqlite3.OperationalError as error:
            if "locked" in str(error) or "busy" in str(error):
                raise RegistryBusy("work_item", str(error)) from error
            raise RegistryUnavailable("work_item", str(error)) from error  # e.g. database or disk is full

    def _write(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("work_item write outside transaction()")  # Every writer below opens one first.
        return self._connection

    # --- rows --------------------------------------------------------------------------------------------------

    def _rows(self, where: str, parameters: tuple) -> list[WorkItem]:
        with self._session() as connection:
            rows = self._execute(connection, f"SELECT {READ_COLUMNS} FROM work_item WHERE {where}", parameters).fetchall()
        return [_item(row) for row in rows]

    def find(self, id_or_label: str) -> WorkItem | None:
        rows = self._rows("id = ? OR label = ? ORDER BY id = ? DESC LIMIT 1", (id_or_label,) * 3)
        return rows[0] if rows else None

    def find_request(self, request_ref: str) -> WorkItem | None:
        rows = self._rows("request_ref = ?", (request_ref,))
        return rows[0] if rows else None

    def find_by_issue(self, number: int) -> WorkItem | None:
        rows = self._rows("issue_number = ?", (number,))
        return rows[0] if rows else None

    def find_by_card(self, card_id: str) -> WorkItem | None:
        rows = self._rows("card_id = ?", (card_id,))
        return rows[0] if rows else None

    def children(self, identity: str) -> tuple[WorkItem, ...]:
        """Explicit parent links only; a family grows by authorized splits, never by a loop."""
        return tuple(self._rows("parent_id = ? ORDER BY created_at, id", (identity,)))

    def _by_id(self, identity: str) -> WorkItem:
        rows = self._rows("id = ?", (identity,))
        if not rows:
            raise UnknownWorkItem(identity)
        return rows[0]

    def register(self, request_ref: RequestRef, label: str, kind: str, parent_id: str | None,
                 pointer: Pointer | None) -> WorkItem:
        return self._create(request_ref, label, kind, parent_id, pointer, CAPTURE, {})

    def import_completed(self, request_ref: RequestRef, label: str, kind: str, pointer: Pointer | None,
                         evidence: dict[str, Ref]) -> WorkItem:
        return self._create(request_ref, label, kind, None, pointer, DONE, evidence)

    def _create(self, request_ref: RequestRef, label: str, kind: str, parent_id: str | None, pointer: Pointer | None,
                state: str, evidence: dict[str, Ref]) -> WorkItem:
        check_label(label)
        check_kind(kind)
        refs = {check_evidence(k): v for k, v in evidence.items()}
        with self.transaction():
            existing = self.find_request(str(request_ref))
            if existing is None:
                if pointer is not None:
                    self._verify(pointer, None)
                self._execute(self._write(), INSERT, (
                    str(uuid4()), str(request_ref), label, parent_id, kind, state, False,
                    *((pointer.repo, pointer.path, pointer.commit) if pointer else (None, None, None)),
                    *(_ref_text(refs.get(name)) for name in EVIDENCE)), label=label, parent=parent_id or "")
            item = self._created(str(request_ref))
            self._tag_later(item)
            return item

    def _created(self, request_ref: str) -> WorkItem:
        item = self.find_request(request_ref)
        if item is None:  # The insert either happened or found the row; nothing else can remove it.
            raise RuntimeError(f"work_item {request_ref} not readable inside its own transaction")
        return item

    def retire(self, identity: str) -> WorkItem:
        """`retired_at` is set once; nothing else about the row, its parent or its children changes."""
        with self.transaction():
            self._by_id(identity)
            self._execute(self._write(), f"UPDATE work_item SET retired_at = {NOW}, updated_at = {NOW} "
                                         "WHERE id = ? AND retired_at IS NULL", (identity,))
            return self._by_id(identity)

    def set_evidence(self, identity: str, which: str, ref: Ref) -> WorkItem:
        column = check_evidence(which) + "_ref"  # A closed set of three column names.
        if not isinstance(ref, Ref):
            raise InvalidWorkItem("evidence", repr(ref))
        with self.transaction():
            self._by_id(identity)
            self._execute(self._write(), f"UPDATE work_item SET {column} = ?, updated_at = {NOW} WHERE id = ?",
                          (_ref_text(ref), identity))
            return self._by_id(identity)

    def set_state(self, identity: str, state: str) -> WorkItem:
        """Only a legal transition from the state read inside this same write transaction."""
        with self.transaction():
            current = self._by_id(identity).state
            check_transition(current, state)
            self._execute(self._write(), f"UPDATE work_item SET state = ?, updated_at = {NOW} "
                                         "WHERE id = ? AND state = ?", (state, identity, current))
            return self._by_id(identity)

    def set_pointer(self, identity: str, pointer: Pointer) -> WorkItem:
        """Equal bytes keep the row's pointer (re-checked and re-tagged); different bytes replace it at CAPTURE and
        are POINTER_PRESENT past CAPTURE."""
        with self.transaction():
            item = self._by_id(identity)
            same = item.pointer is not None and item.pointer.repo == pointer.repo and self.holds(
                item.pointer.with_instructions(pointer.instructions))
            if same:
                self._verify(item.pointer.with_instructions(pointer.instructions), identity)
            else:
                check_pointer_change(item)
                self._verify(pointer, identity)
                self._execute(self._write(), f'UPDATE work_item SET repo = ?, path = ?, "commit" = ?, '
                                             f"updated_at = {NOW} WHERE id = ? AND state = ?",
                              (pointer.repo, pointer.path, pointer.commit, identity, CAPTURE))
                item = self._by_id(identity)
            self._tag_later(item)
            return item

    def set_link(self, identity: str, issue_number: int, issue_node_id: str, card_id: str) -> WorkItem:
        """Store the item's one Issue and card, only while it has none: ITEM_ALREADY_LINKED when the item gained a
        link first, ISSUE_ALREADY_LINKED when another item holds the Issue."""
        if not isinstance(issue_number, int) or issue_number <= 0 or not issue_node_id or not card_id:
            raise InvalidWorkItem("link", f"{issue_number!r}:{issue_node_id!r}:{card_id!r}")
        with self.transaction():
            self._by_id(identity)
            cursor = self._execute(self._write(), f"UPDATE work_item SET issue_number = ?, issue_node_id = ?, "
                                                  f"card_id = ?, updated_at = {NOW} "
                                                  "WHERE id = ? AND issue_number IS NULL",
                                   (issue_number, issue_node_id, card_id, identity), issue=issue_number)
            if cursor.rowcount != 1:
                raise ItemAlreadyLinked(identity, str(self._by_id(identity).issue_number))
            return self._by_id(identity)

    def insert_migrated(self, entry: MigrationEntry) -> WorkItem:
        with self.transaction():
            self._execute(self._write(), INSERT, (entry.id, entry.request_ref, entry.id, None, "BIU", CAPTURE,
                                                  entry.retired, None, None, None, None, None, None), label=entry.id)
            return self._by_id(entry.id)

    def rekey(self, identity: str, request_ref: str) -> WorkItem:
        """The one rewrite of `request_ref`: `legacy:<name>` to the `requirement:<id>` a later record maps."""
        with self.transaction():
            cursor = self._execute(self._write(), f"UPDATE work_item SET request_ref = ?, updated_at = {NOW} "
                                                  "WHERE id = ? AND request_ref LIKE 'legacy:%'",
                                   (request_ref, identity))
            if cursor.rowcount != 1:
                raise UnknownWorkItem(identity, "legacy request reference")
            return self._by_id(identity)

    # --- Git: verification, packets branch and work tags ----------------------------------------------------------

    def _location(self, repo: str) -> RepositoryLocation:
        location = self._repositories.get(repo)
        if location is None:
            raise InvalidWorkItem("repository", repo)
        return location

    def _git(self, location: RepositoryLocation, *args: str, data: bytes | None = None,
             failure: type[WorkIdentityRefused] = GitReadFailed, path: str = "") -> subprocess.CompletedProcess:
        """One bounded git call in the configured clone; a missing binary, clone or timeout is the typed failure."""
        try:
            return subprocess.run(["git", *args], cwd=location.clone, input=data, capture_output=True, check=False,
                                  timeout=self._git_timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise failure("git " + args[0], path or str(location.clone), type(error).__name__) from error

    def _checked(self, location: RepositoryLocation, *args: str, data: bytes | None = None,
                 failure: type[WorkIdentityRefused] = GitReadFailed, path: str = "") -> bytes:
        result = self._git(location, *args, data=data, failure=failure, path=path)
        if result.returncode:
            raise failure("git " + args[0], path or str(location.clone),
                          result.stderr.decode(errors="replace").strip()[:200])
        return result.stdout

    def _lookup(self, location: RepositoryLocation, revision: str, path: str = "") -> str | None:
        """A plain miss (exit 1) is None; any other failure is GIT_READ_FAILED."""
        result = self._git(location, "rev-parse", "--verify", "--quiet", revision, path=path)
        if result.returncode == 1:
            return None
        if result.returncode:
            raise GitReadFailed("git rev-parse", path or revision, result.stderr.decode(errors="replace")[:200])
        return result.stdout.decode().strip()

    def holds(self, pointer: Pointer) -> bool:
        """`git show <commit>:<path>` is byte-equal to the instructions (never a digest comparison)."""
        location = self._location(pointer.repo)
        oid = self._lookup(location, f"{pointer.commit}:{pointer.path}", pointer.path)
        if oid is None or self._checked(location, "cat-file", "-t", oid, path=pointer.path).strip() != b"blob":
            return False
        return self._checked(location, "cat-file", "blob", oid, path=pointer.path) == pointer.instructions

    def read_packet(self, pointer: StoredPointer) -> bytes:
        """`git show <commit>:<path>`: the registered instructions at the row's pinned commit, in one git call and
        no history walk. Any failure of that call is GIT_READ_FAILED naming the path."""
        return self._checked(self._location(pointer.repo), "show", "--no-textconv",
                             f"{pointer.commit}:{pointer.path}", path=pointer.path)

    def _verify(self, pointer: Pointer, identity: str | None) -> None:
        if not self.holds(pointer):
            raise PointerMismatch(f"{pointer.repo}/{pointer.path}@{pointer.commit}", "bytes differ")
        location = self._location(pointer.repo)
        refs = ["refs/heads/" + location.default_branch, "refs/heads/" + location.packets_branch]
        if identity is not None:  # A row registered for the first time has no tag yet.
            refs.append("refs/tags/work/" + identity)
        for ref in refs:  # Three direct checks; tags are never listed or searched.
            if self._lookup(location, ref + "^{commit}") is None:
                continue
            result = self._git(location, "merge-base", "--is-ancestor", pointer.commit, ref, path=pointer.path)
            if result.returncode == 0:
                return
            if result.returncode != 1:
                raise GitReadFailed("git merge-base", pointer.path, result.stderr.decode(errors="replace")[:200])
        raise CommitNotRetained(f"{pointer.repo}/{pointer.path}@{pointer.commit}")

    def packets_head(self, repo: str) -> str | None:
        location = self._location(repo)
        return self._lookup(location, f"refs/heads/{location.packets_branch}^{{commit}}")

    def commit_packet(self, repo: str, path: str, data: bytes, existing: StoredPointer | None) -> str:
        """The row's own commit when it holds these bytes, else the packets branch head when it does, else one new
        commit on the packets branch. No history walk; at most one blob is read to confirm a match."""
        location = self._location(repo)
        if not valid_path(path):
            raise InvalidWorkItem("path", repr(path))
        oid = self._checked(location, "hash-object", "--stdin", data=data, path=path).decode().strip()
        candidates = []
        if existing is not None and existing.repo == repo and existing.path == path:
            candidates.append(existing.commit)
        head = self.packets_head(repo)
        if head is not None:
            candidates.append(head)
        for commit in candidates:
            if self._lookup(location, f"{commit}:{path}", path) == oid:
                if self._checked(location, "cat-file", "blob", oid, path=path) == data:
                    return commit
                break  # The object id matched but the bytes did not: never reuse it.
        parent = head or self._lookup(location, f"refs/heads/{location.default_branch}^{{commit}}")
        if parent is None:
            raise CloneUnavailable(str(location.clone), "default branch " + location.default_branch + " missing")
        # One commit, written without a working tree; fast-import refuses a non-fast-forward branch update.
        message = f"work packet {path}\n".encode()
        stream = b"".join((
            f"commit refs/heads/{location.packets_branch}\ncommitter {COMMITTER} now\n".encode(),
            b"data %d\n" % len(message), message, f"from {parent}\nM 100644 inline {path}\n".encode(),
            b"data %d\n" % len(data), data, b"\ndone\n"))
        self._checked(location, "fast-import", "--quiet", "--done", "--date-format=now", data=stream,
                      failure=CloneUnavailable, path=str(location.clone))
        commit = self.packets_head(repo)
        if commit is None or commit == parent:
            raise CloneUnavailable(str(location.clone), "packets branch not advanced")
        return commit

    def _tag_later(self, item: WorkItem) -> None:
        if item.pointer is not None:
            self._pending[(item.pointer.repo, item.id)] = item.pointer.commit

    def _write_tags(self, pending: dict[tuple[str, str], str]) -> None:
        """After COMMIT: `work/<id>` at the row's commit (a no-op when equal). A failure here is TagWriteFailed —
        the database stays committed and a repeat of the request writes the tag."""
        failed, detail = [], ""
        for (repo, identity), commit in sorted(pending.items()):
            try:
                result = self._git(self._location(repo), "tag", "-f", "work/" + identity, commit)
            except (GitReadFailed, InvalidWorkItem) as error:
                failed.append("work/" + identity)
                detail = str(error)
                continue
            if result.returncode:
                failed.append("work/" + identity)
                detail = result.stderr.decode(errors="replace").strip()[:200]
        if failed:
            raise TagWriteFailed(failed, detail)


def _ref_text(ref: Ref | None) -> str | None:
    return None if ref is None else json.dumps(asdict(ref), sort_keys=True, separators=(",", ":"))


def _item(row: sqlite3.Row) -> WorkItem:
    pointer = StoredPointer(row["repo"], row["path"], row["commit"]) if row["repo"] is not None else None
    refs = {name: ref_from_document(json.loads(row[name + "_ref"])) if row[name + "_ref"] else None
            for name in EVIDENCE}
    return WorkItem(row["id"], row["request_ref"], row["label"], row["parent_id"], row["kind"], row["state"],
                    row["retired_at"], pointer, refs["assessment"], refs["approval"], refs["verification"],
                    row["created_at"], row["updated_at"], row["issue_number"], row["issue_node_id"], row["card_id"])
