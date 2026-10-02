"""Rules for registering hand-written packets, importing earlier work and reading a work record (formal design 6.1C).

A registration is a pointer, never a copy: the row names the packet's repository, path and exact commit, and the
packet text and every later revision live in Git. The request reference of a hand-written packet is its stable
location, `packet:<repo>/<path>`, independent of its commit, label or parent; an import's is `issue:<n>`. The label
and the parent are what the operator's arguments say; nothing here reads the packet text. An import records exactly
the evidence references the operator gives, possibly none. Everything here is pure.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from alienintent.context_assembly.domain.work_identity import ISSUE, PACKET, WorkItem, check_evidence
from alienintent.evidence_learning.domain.records import ref_from_document
from alienintent.evidence_learning.domain.refs import Ref

# The sibling's kind for every registration it creates (the compiler and migration both register BIU).
DEFAULT_KIND = "BIU"


def packet_request_ref(repo: str, path: str) -> str:
    """The stable location of a hand-written packet; the identity service checks the repository and path."""
    return f"{PACKET}:{repo}/{path}"


def issue_request_ref(number: str) -> str:
    """The outside number of earlier completed work; the identity service checks its format."""
    return f"{ISSUE}:{number}"


def given_evidence(documents: Mapping[str, object]) -> dict[str, Ref]:
    """Exactly the evidence references the operator gave, as given; an absent one stays absent, none is invented."""
    return {check_evidence(name): ref_from_document(document) for name, document in documents.items()
            if document is not None}


@dataclass(frozen=True)
class WorkRecord:
    """What `work show` returns: the row, its parent row, its children and the packet bytes at the pinned commit
    (None for a row without a pointer)."""
    item: WorkItem
    parent: WorkItem | None
    children: tuple[WorkItem, ...]
    packet: bytes | None

