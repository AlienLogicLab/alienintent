"""Source-control boundary for immutable candidate publication and read-back, and for publishing exact refs."""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Protocol

from alienintent.execution_coordination.domain.custody import CandidateRef

_REF = re.compile(r"\Arefs/(?:heads|tags)/[A-Za-z0-9._/-]+\Z")
_COMMIT = re.compile(r"\A[0-9a-f]{40}\Z")


class PublicationFailed(RuntimeError):
    """PUBLICATION_FAILED: a push or the remote read-back failed; nothing is reported as published."""
    code = "PUBLICATION_FAILED"

    def __init__(self, refs: tuple[str, ...], detail: str) -> None:
        self.refs = tuple(refs)
        super().__init__(f"{self.code}: {', '.join(self.refs)} ({detail})")


@dataclass(frozen=True)
class PublishRef:
    """One exact ref to publish: a full branch or tag name, the commit it must name, and whether it may move."""
    ref: str
    commit: str
    force: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.ref, str) or not _REF.match(self.ref) or ".." in self.ref \
                or self.ref.endswith(("/", ".lock")):
            raise ValueError(f"not an explicit branch or tag ref: {self.ref!r}")
        if not isinstance(self.commit, str) or not _COMMIT.match(self.commit):
            raise ValueError(f"not a full commit id: {self.commit!r}")
        if not isinstance(self.force, bool):
            raise ValueError("force must be a bool")


class SourceControl(Protocol):
    def revision(self, workspace: Path) -> str: ...
    def tree(self, workspace: Path, revision: str) -> str: ...
    def changes(self, workspace: Path, starting: str, revision: str) -> tuple[tuple[str, str], ...]: ...
    def publish_and_read_back(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...
    def retrieve_for_verification(self, candidate: CandidateRef, verifier_workspace: Path) -> CandidateRef: ...
    def publish_refs(self, clone: Path, remote: str, refs: tuple[PublishRef, ...]) -> None: ...
