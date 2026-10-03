"""WorkIdentityService: the one application service that creates work identities for a project (formal design 6.1A).

Manual registration, the compiler, import of completed work and migration all go through here; the injected
WorkItemRepository adapter is the only writer of `work_item`. The service holds no state and generates nothing:
identifiers and timestamps come from the adapter, repeat safety from the database's uniqueness and transactions.
Every operation that saves a packet reference publishes the row's `work/<id>` tag through the injected RefPublisher,
which composition binds to the one source-control `publish_refs` operation.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from alienintent.context_assembly.domain.work_identity import (
    CAPTURE, INSERT, ISSUE, REKEY, STATES, InvalidRequestRef, InvalidWorkItem, MigrationConflict, Pointer,
    RESERVATIONS, TransactionHeld, WorkItem, check_evidence, migration_action, parse_request_ref, plan_migration)
from alienintent.context_assembly.ports.work_item_repository import (
    PacketRef, RefPublisher, RepositoryLocation, WorkItemRepository)
from alienintent.evidence_learning.domain.refs import Ref
from alienintent.execution_coordination.ports.operational_store import OperationalStore


@dataclass(frozen=True)
class MigrationReport:
    created: tuple[str, ...]
    rekeyed: tuple[tuple[str, str], ...]
    unchanged: tuple[str, ...]


class WorkIdentityService:
    def __init__(self, items: WorkItemRepository, publisher: RefPublisher,
                 repositories: Mapping[str, RepositoryLocation], profile_stores: Mapping[str, OperationalStore]) -> None:
        self.items, self.publisher = items, publisher
        self.repositories, self.profile_stores = dict(repositories), dict(profile_stores)

    def register(self, request_ref: str, label: str, kind: str, parent_id: str | None = None,
                 pointer: Pointer | None = None) -> WorkItem:
        """Create the row at CAPTURE once; a repeat returns the existing row exactly as it is (and republishes its
        tag when it has a pointer). PUBLICATION_FAILED leaves the committed row; repeating the request retries.
        Inside a caller-held transaction (the compiler's registration step) nothing is published: nothing may push
        while the project lock is held, and that caller publishes its rows' refs itself after COMMIT."""
        ref = parse_request_ref(request_ref, self.repositories)
        self._outside_transaction(pointer)
        held = self.items.in_transaction()
        item = self.items.register(ref, label, kind, parent_id, pointer)
        if not held:
            self._publish(item)
        return item

    def import_completed(self, request_ref: str, label: str, kind: str, pointer: Pointer | None,
                         evidence: Mapping[str, Ref]) -> WorkItem:
        """An explicitly authorized historical record at DONE with exactly the evidence given; no transition, no
        invented workflow step. Only the operator's `work import` command calls this."""
        ref = parse_request_ref(request_ref, self.repositories)
        if ref.kind != ISSUE:
            raise InvalidRequestRef(ref.kind, ref.value)
        given = {check_evidence(name): value for name, value in evidence.items()}
        if not all(isinstance(value, Ref) for value in given.values()):
            raise InvalidWorkItem("evidence", "not an evidence Ref")
        self._outside_transaction(pointer)
        item = self.items.import_completed(ref, label, kind, pointer, given)
        self._publish(item)
        return item

    def record_completed(self, identity: str, pointer_commit: str, ref: Ref) -> tuple[WorkItem, bool]:
        """`import_completed`'s historical-record rule for an existing row: straight to DONE with exactly this
        verification reference, guarded by the checked pointer commit; no transition, no new row, no tag change.
        Only `work record-completed` (WorkCompletion) calls this."""
        if not isinstance(ref, Ref):
            raise InvalidWorkItem("evidence", "not an evidence Ref")
        return self.items.record_completed(identity, pointer_commit, ref)

    def retire(self, identity: str) -> WorkItem:
        return self.items.retire(identity)

    def find(self, id_or_label: str) -> WorkItem | None:
        return self.items.find(id_or_label)

    def children(self, identity: str) -> tuple[WorkItem, ...]:
        return self.items.children(identity)

    def set_evidence(self, identity: str, which: str, ref: Ref) -> WorkItem:
        return self.items.set_evidence(identity, check_evidence(which), ref)

    def set_pointer(self, identity: str, pointer: Pointer) -> WorkItem:
        """The repository's pointer rules (equal bytes keep it; different bytes replace it at CAPTURE; POINTER_PRESENT
        past CAPTURE), then the row's `work/<id>` tag is published exactly as `register` publishes it:
        PUBLICATION_FAILED leaves the committed row and repeating the request publishes again."""
        self._outside_transaction(pointer)
        item = self.items.set_pointer(identity, pointer)
        self._publish(item)
        return item

    def set_state(self, identity: str, state: str) -> WorkItem:
        """The only change of state after creation: a row of the 7.3 transition table, read and written in one
        write transaction; anything else is ILLEGAL_TRANSITION and changes nothing."""
        if state not in STATES:
            raise InvalidWorkItem("state", repr(state))
        return self.items.set_state(identity, state)

    def migrate(self, snapshot: Mapping[str, object], profiles: Sequence[str]) -> MigrationReport:
        """`work migrate`: every existing name becomes its own row with its owner's request reference, in one
        transaction; a repeat changes nothing; a later-mapped `legacy:` row is re-keyed and reported."""
        foreign = [p for p in profiles if p not in self.profile_stores]
        if foreign:
            raise MigrationConflict(*(f"profile:{p}" for p in foreign), "not a configured profile of this project")
        records = {}
        for profile in sorted(set(profiles)):  # Sequential reads, one per profile's own operational database.
            _, state = self.profile_stores[profile].read_state(profile, RESERVATIONS)
            records[profile] = state.get("reservations") or {}
        entries = plan_migration(snapshot, records)
        created, rekeyed, unchanged = [], [], []
        with self.items.transaction():
            for entry in entries:
                row = self.items.find(entry.id)
                if row is not None and row.id != entry.id:
                    raise MigrationConflict(f"{','.join(entry.sources)}:{entry.id}", f"registry:label of {row.id}")
                action = migration_action(entry, row, self.items.find_request(entry.request_ref))
                if action == INSERT:
                    self.items.insert_migrated(entry)
                    created.append(entry.id)
                elif action == REKEY:
                    self.items.rekey(entry.id, entry.request_ref)
                    rekeyed.append((entry.id, entry.request_ref))
                else:
                    unchanged.append(entry.id)
        return MigrationReport(tuple(created), tuple(rekeyed), tuple(unchanged))

    def _outside_transaction(self, pointer: Pointer | None) -> None:
        """A stored pointer is tagged after COMMIT and then published, so it cannot join a caller's transaction."""
        if pointer is not None and self.items.in_transaction():
            raise TransactionHeld("register with a pointer")

    def _publish(self, item: WorkItem) -> None:
        if item.pointer is None:
            return
        location = self.repositories[item.pointer.repo]
        self.publisher.publish(location.clone, location.remote,
                               (PacketRef(item.tag, item.pointer.commit, force=item.state == CAPTURE),))
