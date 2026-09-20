"""Durable local-artifact custody used only by the PY-04 offline profile."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import sys

from alienintent.execution_coordination.domain.custody import CandidateRef


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def write(self, contents: bytes) -> CandidateRef:
        digest = f"sha256:{sha256(contents).hexdigest()}"
        path = self._root / digest.removeprefix("sha256:")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != contents:
            raise ValueError("content-addressed artifact path is immutable")
        path.write_bytes(contents)
        return CandidateRef.local_artifact(digest, str(path))


def verify_in_fresh_process(candidate: CandidateRef) -> CandidateRef:
    completed = subprocess.run(
        [sys.executable, "-c", "from hashlib import sha256; from pathlib import Path; import sys; print('sha256:' + sha256(Path(sys.argv[1]).read_bytes()).hexdigest())", candidate.locator],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 or completed.stdout.strip() != candidate.content_digest:
        raise ValueError("independent candidate read-back did not prove identity")
    return candidate.with_independent_read_back()
