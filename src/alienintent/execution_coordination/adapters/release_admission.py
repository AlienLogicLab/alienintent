"""Adapters for the canonical release gate: git revisions and store-held release records."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Mapping

from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from alienintent.execution_coordination.ports.operational_store import OperationalStore
from alienintent.execution_coordination.ports.release_admission import ReleaseAuthorizationRecords, RevisionResolver


class GitRevisionResolver(RevisionResolver):
    """Resolve baselines in a local checkout of each target repository; unknown repositories never resolve."""

    def __init__(self, checkouts: Mapping[str, Path]) -> None:
        self._checkouts = dict(checkouts)

    def _git(self, repository: str, *args: str) -> bool:
        checkout = self._checkouts.get(repository)
        if checkout is None:
            return False
        try:
            return subprocess.run(["git", *args], cwd=checkout, capture_output=True, check=False).returncode == 0
        except OSError:
            # An unavailable git or checkout cannot establish a revision: refuse, never admit.
            return False

    def resolves(self, repository: str, revision: str) -> bool:
        return self._git(repository, "cat-file", "-e", f"{revision}^{{commit}}")

    def is_reachable(self, repository: str, revision: str, release_point: str) -> bool:
        return (self._git(repository, "rev-parse", "--verify", "--quiet", f"{release_point}^{{commit}}")
                and self._git(repository, "merge-base", "--is-ancestor", revision, release_point))


class StoredReleaseAuthorizations(ReleaseAuthorizationRecords):
    """Durable release records held in the operational store, one aggregate per BIU."""

    def __init__(self, store: OperationalStore, profile: str) -> None:
        self._store, self._profile = store, profile

    @staticmethod
    def _aggregate(identity: str) -> str:
        return f"release-authorization:{identity}"

    def record(self, authorization: ReleaseAuthorization) -> None:
        """Create-only: commits at expected version 0, so the store raises VersionConflict and overwrites nothing
        when any release record already exists for the identity."""
        self._store.commit(self._profile, self._aggregate(authorization.identity), 0, {
            "identity": authorization.identity, "record_ref": authorization.record_ref,
            "authorizes_implement": authorization.authorizes_implement, "baseline": authorization.baseline,
            "text": authorization.text, "superseding_record": authorization.superseding_record,
        })

    def release_authorization(self, identity: str) -> ReleaseAuthorization | None:
        _, raw = self._store.read_state(self._profile, self._aggregate(identity))
        if not raw:
            return None
        baseline, superseding = raw.get("baseline"), raw.get("superseding_record")
        return ReleaseAuthorization(
            str(raw.get("identity") or ""), str(raw.get("record_ref") or ""), raw.get("authorizes_implement") is True,
            baseline if isinstance(baseline, str) else None, str(raw.get("text") or ""),
            superseding if isinstance(superseding, str) else None,
        )
