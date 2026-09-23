"""Neutral references and explicit evidence holds; no consumer application imports."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Ref:
    project: str
    profile: str
    logical_id: str
    revision_digest: str
    locator: str

    def __post_init__(self) -> None:
        if any(not isinstance(v, str) or not v.strip() for v in
               (self.project, self.profile, self.logical_id, self.locator)):
            raise EvidenceHold("INVALID_REF", required_action="supply nonempty reference identity")
        if not isinstance(self.revision_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", self.revision_digest):
            raise EvidenceHold("INVALID_DIGEST", required_action="supply exact sha256 digest")


@dataclass(frozen=True)
class EvidenceHold(Exception):
    reason_code: str
    affected_refs: tuple[Ref, ...] = ()
    evidence_refs: tuple[Ref, ...] = ()
    required_action: str = "supply valid evidence or obtain the named source authority"

    def __str__(self) -> str:
        return f"{self.reason_code}: {self.required_action}"
