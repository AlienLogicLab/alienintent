"""Seed the SWF-21 release inputs an operational profile now requires (WO-220611, B3P).

``SandboxRunProfile`` and ``GitHubProfileComposition`` always compose the
canonical release gate and the attributable per-BIU allocation, so a fixture
that drains work through them supplies what a real operator supplies: a durable
release record naming an exact, reachable baseline, and a configured budget
allocation for every dimension its contracts require. Nothing is bypassed.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Iterable, Mapping

from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from alienintent.execution_coordination.ports.release_admission import ReleaseAuthorizationRecords

# Every dimension the fixture contracts require, with room for rework cycles.
ALLOCATION = {"attempts": 10, "retries": 10, "wall-clock": 10, "concurrency": 10, "cancellation": 10}


def biu_limits(identities: Iterable[str]) -> dict[str, dict[str, int]]:
    return {identity: dict(ALLOCATION) for identity in identities}


def release_admission_section(identities: Iterable[str]) -> Mapping[str, object]:
    """The ``release_admission`` section of a profile document."""
    return {"release_admission": {"biu_limits": biu_limits(identities)}}


def authorize_release(records: ReleaseAuthorizationRecords, checkout: Path, identities: Iterable[str]) -> str:
    """Record IMPLEMENT authorization for each BIU against the checkout's current baseline."""
    baseline = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    for identity in identities:
        if records.release_authorization(identity) is not None:
            continue  # a reopened root is a restart; the durable record already exists
        records.record(ReleaseAuthorization(identity, f"fixture-release-record:{identity}", True, baseline))  # type: ignore[attr-defined]
    return baseline
