"""Provider-neutral, immutable candidate custody references."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
import re


class CandidateValidationError(ValueError):
    """Raised when a candidate reference cannot establish immutable identity."""


class CandidateKind(StrEnum):
    LOCAL_ARTIFACT = "local-artifact"
    SOURCE_REVISION = "source-revision"
    ARCHIVE = "archive"


@dataclass(frozen=True)
class CandidateRef:
    kind: CandidateKind
    identity: str
    content_digest: str
    locator: str
    provenance: str
    independent_read_back_proven: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.content_digest):
            raise CandidateValidationError("content digest must use sha256")
        if not self.locator or not self.provenance or self.content_digest not in self.identity:
            raise CandidateValidationError("identity must resolve unambiguously to content digest")

    @property
    def verify_admissible(self) -> bool:
        return self.independent_read_back_proven

    def with_independent_read_back(self) -> CandidateRef:
        return replace(self, independent_read_back_proven=True)

    @classmethod
    def local_artifact(cls, digest: str, locator: str, *, identity: str | None = None) -> CandidateRef:
        return cls(CandidateKind.LOCAL_ARTIFACT, identity or f"artifact:{locator}@{digest}", digest, locator, "local durable artifact")

    @classmethod
    def source_revision(cls, digest: str, locator: str, *, identity: str | None = None) -> CandidateRef:
        return cls(CandidateKind.SOURCE_REVISION, identity or f"revision:{locator}@{digest}", digest, locator, "source-control revision")

    @classmethod
    def archive(cls, digest: str, locator: str, *, identity: str | None = None) -> CandidateRef:
        return cls(CandidateKind.ARCHIVE, identity or f"archive:{locator}@{digest}", digest, locator, "durable archive")
