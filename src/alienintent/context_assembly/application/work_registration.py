"""The operator's three work-record operations over the one work identity service (formal design 6.1C).

`register` and `import_completed` hand the packet file's bytes to the identity service, whose adapter compares them
byte for byte with `git show <commit>:<path>` and checks the commit is retained, in one transaction; a repeat returns
the existing row unchanged. `show` reads the row, its parent and its children in one read transaction, then the packet
at the row's pinned commit with one `git show`. Nothing here moves a pointer, changes a state or writes evidence.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping

from alienintent.context_assembly.application.work_identity_service import WorkIdentityService
from alienintent.context_assembly.domain.work_identity import Pointer, StoredPointer, WorkItem
from alienintent.context_assembly.domain.work_registration import (
    DEFAULT_KIND, WorkRecord, given_evidence, issue_request_ref, packet_request_ref)
from alienintent.context_assembly.ports.work_item_repository import WorkItemRepository


class WorkRecordService:
    """Hand-written packet registration, import of earlier completed work and reading one record.

    `read_packet` is the repository adapter's `git show <commit>:<path>`; a failure of that call is GIT_READ_FAILED
    naming the path."""

    def __init__(self, identities: WorkIdentityService, items: WorkItemRepository,
                 read_packet: Callable[[StoredPointer], bytes]) -> None:
        self.identities, self.items, self.read_packet = identities, items, read_packet

    def register(self, packet: bytes, repo: str, path: str, commit: str, label: str, kind: str = DEFAULT_KIND,
                 parent_id: str | None = None) -> WorkItem:
        """One row at CAPTURE pointing at the commit that holds exactly `packet`; a repeat returns the existing row
        unchanged, whatever the arguments."""
        return self.identities.register(packet_request_ref(repo, path), label, kind, parent_id,
                                        Pointer(repo, path, commit, packet))

    def import_completed(self, packet: bytes, repo: str, path: str, commit: str, label: str, issue: str,
                         evidence: Mapping[str, object]) -> WorkItem:
        """Earlier completed work as a row at DONE with exactly the evidence references given; a repeat returns the
        existing row unchanged, whatever the arguments."""
        return self.identities.import_completed(issue_request_ref(issue), label, DEFAULT_KIND,
                                                Pointer(repo, path, commit, packet), given_evidence(evidence))

    def show(self, id_or_label: str) -> WorkRecord | None:
        """The row, its parent, its children and the packet at the pinned commit; None when no row holds the name."""
        with self.items.transaction():
            item = self.identities.find(id_or_label)
            if item is None:
                return None
            parent = self.identities.find(item.parent_id) if item.parent_id is not None else None
            children = self.identities.children(item.id)
        packet = self.read_packet(item.pointer) if item.pointer is not None else None
        return WorkRecord(item, parent, children, packet)
