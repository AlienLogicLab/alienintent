"""Git implementation of immutable remote candidate custody."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
from urllib.parse import urlsplit, urlunsplit

from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.invocation_runtime.domain.runtime import CandidateUnavailable
from alienintent.invocation_runtime.ports.source_control import SourceControl


class GitSourceControl(SourceControl):
    @staticmethod
    def _evidence_remote(remote: str) -> str:
        """Keep candidate evidence usable without retaining URL userinfo."""
        parsed = urlsplit(remote)
        if not parsed.scheme:
            return remote
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)
        if result.returncode:
            raise CandidateUnavailable("git operation failed")
        return result.stdout.strip()

    def revision(self, workspace: Path) -> str:
        revision = self._git("rev-parse", "HEAD", cwd=workspace)
        if len(revision) != 40:
            raise CandidateUnavailable("candidate revision is not immutable")
        return revision

    def read_back_candidate(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
        remote_url = self._git("remote", "get-url", remote, cwd=workspace)
        advertised = self._git("ls-remote", remote_url, f"refs/heads/{branch}", cwd=workspace)
        if not advertised or advertised.split()[0] != revision:
            raise CandidateUnavailable("candidate revision is not published at the requested branch")
        if verifier_workspace.exists():
            raise CandidateUnavailable("fresh verifier workspace already exists")
        self._git("clone", "--no-checkout", remote_url, str(verifier_workspace))
        fetched = self._git("rev-parse", f"{revision}^{{commit}}", cwd=verifier_workspace)
        if fetched != revision:
            raise CandidateUnavailable("fresh clone cannot retrieve exact candidate revision")
        digest = f"sha256:{sha256(revision.encode()).hexdigest()}"
        evidence_remote = self._evidence_remote(remote_url)
        return CandidateRef.source_revision(digest, f"git:{evidence_remote}#{branch}@{revision}", identity=f"revision:{evidence_remote}@{branch}@{revision}@{digest}").with_independent_read_back()

    def publish_and_read_back(self, workspace: Path, remote: str, branch: str, revision: str, verifier_workspace: Path) -> CandidateRef:
        if self.revision(workspace) != revision:
            raise CandidateUnavailable("workspace HEAD differs from requested candidate revision")
        self._git("push", remote, f"{revision}:refs/heads/{branch}", cwd=workspace)
        return self.read_back_candidate(workspace, remote, branch, revision, verifier_workspace)

    def retrieve_for_verification(self, candidate: CandidateRef, verifier_workspace: Path) -> CandidateRef:
        """Independently assemble verifier inputs from the immutable source reference."""
        try:
            prefix, reference = candidate.locator.rsplit("#", 1)
            remote = prefix.removeprefix("git:")
            branch, revision = reference.rsplit("@", 1)
            if not remote or prefix == remote or not branch or len(revision) != 40 or verifier_workspace.exists():
                raise ValueError
        except ValueError:
            raise CandidateUnavailable("candidate cannot be independently retrieved") from None
        advertised = self._git("ls-remote", remote, f"refs/heads/{branch}")
        if not advertised or advertised.split()[0] != revision:
            raise CandidateUnavailable("candidate revision is not retrievable for verifier")
        self._git("clone", "--no-checkout", remote, str(verifier_workspace))
        if self._git("rev-parse", f"{revision}^{{commit}}", cwd=verifier_workspace) != revision:
            raise CandidateUnavailable("verifier clone cannot retrieve exact candidate revision")
        expected_digest = f"sha256:{sha256(revision.encode()).hexdigest()}"
        if candidate.content_digest != expected_digest:
            raise CandidateUnavailable("candidate digest does not match immutable revision")
        # The verifier evaluates the exact revision's tree, not an empty clone.
        self._git("checkout", "-q", "--detach", revision, cwd=verifier_workspace)
        return candidate.with_independent_read_back()
