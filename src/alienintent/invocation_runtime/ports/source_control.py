"""Source-control boundary for immutable candidate publication and read-back."""

from pathlib import Path
from typing import Protocol

from alienintent.execution_coordination.domain.custody import CandidateRef


class SourceControl(Protocol):
    def revision(self, workspace: Path) -> str: ...
    def publish_and_read_back(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef: ...
    def retrieve_for_verification(self, candidate: CandidateRef, verifier_workspace: Path) -> CandidateRef: ...
