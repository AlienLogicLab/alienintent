"""The per-role context package of one registered work item and attempt (docs/architecture/interface-contracts.md
sections 6-7; unit 6c-1): its fields, the VERIFIER's labelled self-review input and the self-review record names.

A package holds exactly the fields of its role and nothing else; a missing or conflicting required fact is a
`ContextHold` (context_assembly/domain/reconstruction.py) instead, so no package exists to launch with. Pure.
"""
from __future__ import annotations

from base64 import b64encode
from collections.abc import Mapping
from dataclasses import dataclass
import re

from alienintent.context_assembly.domain.reconstruction import canonical
from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.execution_coordination.ports.worker_provider import PRODUCER, VERIFIER

# Section 1: every role's fields, then what the PRODUCER alone and the VERIFIER alone receive.
COMMON_FIELDS = ("identity", "label", "role", "attempt", "goal", "instructions", "contract", "release_record",
                 "starting_revision", "allowed_scope", "required_evidence", "stop_condition", "escalation_condition",
                 "dependencies", "design_rules", "history", "resources", "context_command")
FIELDS = {PRODUCER: frozenset({*COMMON_FIELDS, "assessment"}),
          VERIFIER: frozenset({*COMMON_FIELDS, "candidate", "diff", "producer_self_review"})}
# Section 4: the self-review reaches the VERIFIER only under `producer_self_review`, with this fixed label.
SELF_REVIEW_LABEL = "input to check — not findings and not a verdict"
SELF_REVIEW = "self-review"
SELF_REVIEW_EXISTS = "SELF_REVIEW_EXISTS"
# The coordinator's source-revision locator: git:<remote>#<branch>@<revision>.
SOURCE_REVISION = re.compile(r"git:.+#.+@([0-9a-f]{40})")


@dataclass(frozen=True)
class ContextPackage:
    """One role's package: exactly that role's fields; `document()` is the JSON value printed and delivered."""
    role: str
    fields: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.role not in FIELDS or set(self.fields) != FIELDS[self.role]:
            raise ValueError(f"a {self.role} package holds exactly its section 1 fields")

    def document(self) -> dict[str, object]:
        return {"status": "PACKAGE", **self.fields}

    def canonical_bytes(self) -> bytes:
        return canonical(self.document())


def self_review_aggregate(identity: str, candidate: CandidateRef) -> str:
    """The create-only store record of the self-review for this candidate (keyed by its content digest)."""
    return f"{SELF_REVIEW}:{identity}:{candidate.content_digest}"


def candidate_document(candidate: CandidateRef) -> dict[str, object]:
    """The candidate exactly as the coordinator encodes it in its state."""
    return {"kind": str(candidate.kind), "identity": candidate.identity, "content_digest": candidate.content_digest,
            "locator": candidate.locator, "provenance": candidate.provenance,
            "independent_read_back_proven": candidate.independent_read_back_proven}


def candidate_revision(candidate: CandidateRef) -> str | None:
    """The commit named by a source-revision candidate's locator; None for any other candidate."""
    match = SOURCE_REVISION.fullmatch(candidate.locator) if candidate.kind is CandidateKind.SOURCE_REVISION else None
    return match.group(1) if match else None


def content(data: bytes) -> dict[str, str]:
    """Resolved bytes as JSON: the exact UTF-8 text, else the bytes in base64."""
    try:
        return {"text": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"base64": b64encode(data).decode("ascii")}
