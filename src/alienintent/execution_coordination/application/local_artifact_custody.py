"""SWF-22 local candidate custody: verifier-side copy and digest read-back."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import sys

from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef


class LocalArtifactStore:
    def __init__(self, root: Path, verifier_root: Path) -> None:
        self.root = root
        self.verifier_root = verifier_root

    def write(self, contents: bytes) -> CandidateRef:
        digest = f"sha256:{sha256(contents).hexdigest()}"
        path = self.root / digest.removeprefix("sha256:")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != contents:
            raise ValueError("content-addressed artifact path is immutable")
        path.write_bytes(contents)
        return CandidateRef.local_artifact(digest, str(path))


def candidate_from_record(record: dict[str, object]) -> CandidateRef:
    return CandidateRef(CandidateKind(str(record["kind"])), str(record["identity"]), str(record["content_digest"]), str(record["locator"]), str(record["provenance"]))


def verify_in_fresh_process(candidate: CandidateRef, verifier_root: Path) -> CandidateRef:
    """Transfer bytes in a fresh verifier process and bind verification to its copy."""
    destination = verifier_root / candidate.content_digest.removeprefix("sha256:")
    code = (
        "from hashlib import sha256; from pathlib import Path; import shutil,sys; "
        "source,destination=map(Path,sys.argv[1:3]); destination.parent.mkdir(parents=True,exist_ok=True); "
        "(None if destination.exists() else shutil.copyfile(source,destination)); "
        "print('sha256:'+sha256(destination.read_bytes()).hexdigest())"
    )
    result = subprocess.run([sys.executable, "-c", code, candidate.locator, str(destination)], check=False, capture_output=True, text=True)
    if result.returncode or result.stdout.strip() != candidate.content_digest:
        raise ValueError("independent candidate read-back did not prove identity")
    return CandidateRef(candidate.kind, candidate.identity, candidate.content_digest, str(destination), candidate.provenance, True)

