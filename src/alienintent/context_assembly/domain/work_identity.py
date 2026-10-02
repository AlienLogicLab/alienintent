"""Work identity rules (formal design 6.1, 6.1A): one row per piece of work, four separate fields, typed refusals.

A work item keeps, separately, its permanent identifier (`id`: an existing name kept exactly, or a version-4 UUID
issued by the repository adapter), its creation-request reference (`request_ref`: `<kind>:<value>` with a closed set
of kinds, never a label or a parent), its unique human label and an optional parent identifier. The packet pointer
names a repository, a path and the exact 40-hex commit that holds the registered instructions; the database never
holds the instructions themselves. Everything here is pure: no clock, no identifier generation, no storage.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping

from alienintent.context_assembly.domain.compilation import IDENTITY_GRAMMAR, UUID_GRAMMAR
from alienintent.evidence_learning.domain.refs import Ref

# Formal design 6.1 kinds and the 7.1 lifecycle states.
KINDS = ("REQUIREMENT", "BIU", "MAINTENANCE", "DECISION", "MIGRATION")
CAPTURE, DONE = "CAPTURE", "DONE"
STATES = (CAPTURE, "SPECIFY", "PLAN", "TASKS", "READY", "IMPLEMENT", "VERIFY", "ACCEPT", DONE)
# Formal design 7.3: no other normal transition is legal.
TRANSITIONS = frozenset({(CAPTURE, "SPECIFY"), ("SPECIFY", "PLAN"), ("PLAN", "TASKS"), ("TASKS", "READY"),
                         ("READY", "IMPLEMENT"), ("IMPLEMENT", "VERIFY"), ("VERIFY", "IMPLEMENT"),
                         ("VERIFY", "ACCEPT"), ("ACCEPT", DONE)})
REQUIREMENT, PACKET, ISSUE, LEGACY = "requirement", "packet", "issue", "legacy"
REQUEST_KINDS = (REQUIREMENT, PACKET, ISSUE, LEGACY)
EVIDENCE = ("assessment", "approval", "verification")
# The per-profile reservation aggregate the earlier compiler wrote; read only by migration and the compiler's check.
RESERVATIONS = "upstream:identity-reservations"
TAG_PREFIX = "refs/tags/work/"
_COMMIT = re.compile(r"\A[0-9a-f]{40}\Z")


class WorkIdentityRefused(Exception):
    """A typed refusal; `code` is the stable reason and `values` name what was refused."""
    code = "WORK_IDENTITY_REFUSED"

    def __init__(self, *values: str) -> None:
        self.values = tuple(str(v) for v in values)
        super().__init__(f"{self.code}: {', '.join(self.values)}")


class LabelInUse(WorkIdentityRefused):
    code = "LABEL_IN_USE"


class ParentNotRegistered(WorkIdentityRefused):
    code = "PARENT_NOT_REGISTERED"


class PointerMismatch(WorkIdentityRefused):
    code = "POINTER_MISMATCH"


class CommitNotRetained(WorkIdentityRefused):
    code = "COMMIT_NOT_RETAINED"


class MigrationConflict(WorkIdentityRefused):
    code = "MIGRATION_CONFLICT"


class IllegalTransition(WorkIdentityRefused):
    code = "ILLEGAL_TRANSITION"


class InvalidRequestRef(WorkIdentityRefused):
    code = "INVALID_REQUEST_REF"


class InvalidWorkItem(WorkIdentityRefused):
    """A label, kind, state, evidence name or pointer value that the row rules do not admit."""
    code = "INVALID_WORK_ITEM"


class UnknownWorkItem(WorkIdentityRefused):
    code = "UNKNOWN_WORK_ITEM"


class PointerPresent(WorkIdentityRefused):
    code = "POINTER_PRESENT"


class GitReadFailed(WorkIdentityRefused):
    code = "GIT_READ_FAILED"


class CloneUnavailable(WorkIdentityRefused):
    code = "CLONE_UNAVAILABLE"


class MigrationIncomplete(WorkIdentityRefused):
    """An old per-profile record assigns a requirement a name the table does not hold under that requirement."""
    code = "MIGRATION_INCOMPLETE"


class IdentityRetired(WorkIdentityRefused):
    code = "IDENTITY_RETIRED"


class RegistryBusy(WorkIdentityRefused):
    """The project database stayed locked beyond the busy timeout; nothing was written, rerun the request."""
    code = "WORK_REGISTRY_BUSY"


class TransactionHeld(WorkIdentityRefused):
    """A call that publishes after its own commit was made inside a caller-held transaction."""
    code = "TRANSACTION_HELD"


class TagWriteFailed(Exception):
    """The database transaction COMMITTED; afterwards setting `work/<id>` in the clone failed.

    The rows are stored and are not rolled back. The commit is still retained by the branch that passed the check;
    repeating the same request re-applies the tag. This is deliberately not a WorkIdentityRefused: nothing refused.
    """
    code = "TAG_WRITE_FAILED"

    def __init__(self, tags: Iterable[str], detail: str) -> None:
        self.tags = tuple(tags)
        super().__init__(f"{self.code}: database committed; tag(s) {', '.join(self.tags)} not set ({detail}); "
                         "repeat the request to set them")


@dataclass(frozen=True)
class RequestRef:
    kind: str
    value: str

    def __str__(self) -> str:
        return f"{self.kind}:{self.value}"


def parse_request_ref(text: object, repositories: Iterable[str]) -> RequestRef:
    """`<kind>:<value>`, kind in the closed set and value in its kind's own format; INVALID_REQUEST_REF otherwise."""
    if not isinstance(text, str) or ":" not in text:
        raise InvalidRequestRef(repr(text))
    kind, value = text.split(":", 1)
    valid = {REQUIREMENT: _requirement_value, PACKET: lambda v: _packet_value(v, repositories),
             ISSUE: lambda v: re.fullmatch(r"[1-9][0-9]*", v) is not None,
             LEGACY: lambda v: re.match(IDENTITY_GRAMMAR, v) is not None and not is_uuid(v)}.get(kind)
    if valid is None or not value.isascii() or not valid(value):
        raise InvalidRequestRef(kind, value)
    return RequestRef(kind, value)


def _requirement_value(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value) is not None


def _packet_value(value: str, repositories: Iterable[str]) -> bool:
    """`<repo>/<path>`: repo a configured repository name, path non-empty and relative without `..` parts."""
    for name in sorted(set(repositories), key=len, reverse=True):
        if value.startswith(name + "/"):
            return valid_path(value[len(name) + 1:])
    return False


def valid_path(path: str) -> bool:
    parts = path.split("/")
    return bool(path) and path.isascii() and all(p and p not in (".", "..") for p in parts) \
        and not any(c in path for c in "\0\n\r:")


def is_uuid(identity: object) -> bool:
    return isinstance(identity, str) and re.fullmatch(UUID_GRAMMAR, identity) is not None


def valid_identity(identity: object) -> bool:
    """An existing name matching the grammar, or a version-4 UUID; never a number parsed out of either."""
    return isinstance(identity, str) and re.match(IDENTITY_GRAMMAR, identity) is not None


def check_label(label: object) -> str:
    if not isinstance(label, str) or not label.strip():
        raise InvalidWorkItem("label", repr(label))
    return label


def check_kind(kind: object) -> str:
    if kind not in KINDS:
        raise InvalidWorkItem("kind", repr(kind))
    return str(kind)


def check_transition(current: str, new: str) -> None:
    """Only a row of the formal design 7.3 table is a legal change of state."""
    if (current, new) not in TRANSITIONS:
        raise IllegalTransition(current, new)


def check_evidence(which: object) -> str:
    if which not in EVIDENCE:
        raise InvalidWorkItem("evidence", repr(which))
    return str(which)


@dataclass(frozen=True)
class Pointer:
    """Where the registered instructions live: repository name, path and the exact commit holding them.

    `instructions` are the bytes being registered; they are compared with `git show <commit>:<path>` and never
    stored in the database."""
    repo: str
    path: str
    commit: str
    instructions: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.repo, str) or not self.repo or not isinstance(self.path, str) \
                or not valid_path(self.path) or not isinstance(self.commit, str) or not _COMMIT.match(self.commit) \
                or not isinstance(self.instructions, bytes):
            raise InvalidWorkItem("pointer", f"{self.repo!r}:{self.path!r}@{self.commit!r}")


@dataclass(frozen=True)
class StoredPointer:
    """A row's pointer as stored: the instructions stay in Git."""
    repo: str
    path: str
    commit: str

    def with_instructions(self, instructions: bytes) -> Pointer:
        return Pointer(self.repo, self.path, self.commit, instructions)


@dataclass(frozen=True)
class WorkItem:
    id: str
    request_ref: str
    label: str
    parent_id: str | None
    kind: str
    state: str
    retired_at: str | None
    pointer: StoredPointer | None
    assessment_ref: Ref | None
    approval_ref: Ref | None
    verification_ref: Ref | None
    created_at: str
    updated_at: str

    @property
    def retired(self) -> bool:
        return self.retired_at is not None

    @property
    def tag(self) -> str:
        return TAG_PREFIX + self.id


def check_pointer_change(item: WorkItem) -> None:
    """Different instructions may replace a row's pointer only while the row is at CAPTURE (registered, not yet
    assessed or approved); past CAPTURE changing authorized instructions is a later controlled operation."""
    if item.state != CAPTURE:
        raise PointerPresent(item.id, item.state)


# --- migration of existing names (work migrate) -----------------------------------------------------------------


@dataclass(frozen=True)
class MigrationEntry:
    """One existing name: id = label = name, kind BIU, state CAPTURE, no pointer; `sources` name its inputs."""
    id: str
    request_ref: str
    retired: bool
    sources: tuple[str, ...]


SKIP, INSERT, REKEY = "SKIP", "INSERT", "REKEY"


def plan_migration(snapshot: Mapping[str, object], records: Mapping[str, Mapping[str, object]]) -> tuple[
        MigrationEntry, ...]:
    """Every snapshot name and every record's name, keyed `requirement:<id>` when a record maps it, else
    `legacy:<name>`. One name under two keys, or one key with two names, is MIGRATION_CONFLICT naming both sources."""
    if not isinstance(snapshot, Mapping):
        raise MigrationConflict("snapshot", "not an identity snapshot")
    named: dict[str, set[str]] = {}
    for group in ("active", "retired", "reserved"):
        values = snapshot.get(group, [])
        if not isinstance(values, list):
            raise MigrationConflict("snapshot:" + group, "not a list")
        for name in values:
            _migrated_name(name, "snapshot:" + group)
            named.setdefault(name, set()).add("snapshot:" + group)
    keyed: dict[str, tuple[str, str]] = {}  # name -> (key, source)
    by_key: dict[str, tuple[str, str]] = {}  # key -> (name, source)
    for profile in sorted(records):
        source = "profile:" + profile
        mapping = records[profile]
        if not isinstance(mapping, Mapping):
            raise MigrationConflict(source, "reservations not a mapping")
        for key in sorted(mapping):
            name = mapping[key]
            _migrated_name(name, source)
            try:
                ref = parse_request_ref(key, ())
            except InvalidRequestRef:
                raise MigrationConflict(source, f"{key!r} is not a requirement key") from None
            if ref.kind != REQUIREMENT:
                raise MigrationConflict(source, f"{key} is not a requirement key")
            if name in keyed and keyed[name][0] != key:
                raise MigrationConflict(f"{keyed[name][1]}:{keyed[name][0]}->{name}", f"{source}:{key}->{name}")
            if key in by_key and by_key[key][0] != name:
                raise MigrationConflict(f"{by_key[key][1]}:{key}->{by_key[key][0]}", f"{source}:{key}->{name}")
            keyed.setdefault(name, (key, source))
            by_key.setdefault(key, (name, source))
            named.setdefault(name, set()).add(source)
    retired = set(snapshot.get("retired", []))
    return tuple(MigrationEntry(name, keyed[name][0] if name in keyed else f"{LEGACY}:{name}", name in retired,
                                tuple(sorted(sources)))
                 for name, sources in sorted(named.items()))


def _migrated_name(name: object, source: str) -> None:
    if not isinstance(name, str) or is_uuid(name) or re.match(IDENTITY_GRAMMAR, name) is None:
        raise MigrationConflict(source, f"{name!r} is not an existing name")


def migration_action(entry: MigrationEntry, row: WorkItem | None, holder: WorkItem | None) -> str:
    """Insert an absent name, skip an identical row, re-key `legacy:` to the mapped `requirement:`; any other
    difference is MIGRATION_CONFLICT. `holder` is the row already holding `entry.request_ref`, if any."""
    if holder is not None and holder.id != entry.id:
        raise MigrationConflict(f"{','.join(entry.sources)}:{entry.request_ref}->{entry.id}",
                                f"registry:{entry.request_ref}->{holder.id}")
    if row is None:
        return INSERT
    if row.label != entry.id or row.kind != "BIU" or row.retired != entry.retired:
        raise MigrationConflict(f"{','.join(entry.sources)}:{entry.id}",
                                f"registry:{row.id}:label={row.label}:kind={row.kind}:retired={row.retired}")
    if row.request_ref == entry.request_ref:
        return SKIP
    if row.request_ref.startswith(LEGACY + ":") and entry.request_ref.startswith(REQUIREMENT + ":"):
        return REKEY
    raise MigrationConflict(f"{','.join(entry.sources)}:{entry.request_ref}->{entry.id}",
                            f"registry:{row.request_ref}->{row.id}")
