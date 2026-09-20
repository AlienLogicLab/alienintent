"""SWF-22 local candidate custody: verifier-side copy and digest read-back."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import sys

from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable


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
    if candidate.kind is CandidateKind.SOURCE_REVISION:
        return _verify_source_revision_in_fresh_clone(candidate, verifier_root)
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


def _verify_source_revision_in_fresh_clone(candidate: CandidateRef, verifier_root: Path) -> CandidateRef:
    """Control-plane custody check; a producer's read-back flag is never trusted."""
    try:
        prefix, reference = candidate.locator.rsplit("#", 1)
        remote = prefix.removeprefix("git:")
        branch, revision = reference.rsplit("@", 1)
        if not remote or prefix == remote or not branch or len(revision) != 40:
            raise ValueError
    except ValueError:
        raise ValueError("independent candidate read-back did not prove identity") from None
    destination = verifier_root / revision
    if destination.exists():
        raise ValueError("independent candidate read-back requires a fresh clone")
    advertised = subprocess.run(["git", "ls-remote", remote, f"refs/heads/{branch}"], check=False, capture_output=True, text=True)
    if advertised.returncode or advertised.stdout.split()[:1] != [revision]:
        raise CandidateUnavailable("candidate revision is not published at the requested branch")
    result = subprocess.run(["git", "clone", "--no-checkout", remote, str(destination)], check=False, capture_output=True, text=True)
    resolved = subprocess.run(["git", "rev-parse", f"{revision}^{{commit}}"], cwd=destination, check=False, capture_output=True, text=True) if result.returncode == 0 else result
    expected_digest = f"sha256:{sha256(revision.encode()).hexdigest()}"
    if resolved.returncode or resolved.stdout.strip() != revision or candidate.content_digest != expected_digest:
        raise ValueError("independent candidate read-back did not prove identity")
    return CandidateRef(candidate.kind, candidate.identity, candidate.content_digest, candidate.locator, candidate.provenance, True)
