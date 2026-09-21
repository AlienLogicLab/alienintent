"""Composition-root read-only probes supplying doctor with real adapter evidence.

Every probe here observes. None allocates a worktree, starts a worker, or
touches a product resource.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from hashlib import sha256
import hmac
from typing import Mapping
from urllib.error import URLError
from urllib.request import Request, urlopen

from alienintent.execution_coordination.adapters.github_webhook import RESIDENT_INGRESS_MARKER
from alienintent.installation.application.doctor import DoctorFailure, DoctorUnavailable
from alienintent.installation.domain.github_profile import GitHubProfile
from alienintent.installation.ports.secret_provider import SecretProvider
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter


def git_worktree_inventory(repository: Path) -> tuple[Path, ...]:
    """Read back the worktrees Git already knows about; `list` never allocates."""
    listing = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repository, capture_output=True, text=True, check=False,
    )
    if listing.returncode:
        return ()
    return tuple(
        Path(line.split(" ", 1)[1])
        for line in listing.stdout.splitlines()
        if line.startswith("worktree ")
    )


def execution_evidence(repository: Path, workspace_root: Path, worker: CliWorkerProvider, executable: str) -> dict[str, object]:
    """Evidence the doctor can adjudicate, not a verdict the adapter declared."""
    resolved = shutil.which(executable)
    return {
        "workspace_root": workspace_root,
        "workspace_manager": GitWorktreeAdapter(repository, workspace_root),
        "git_worktrees": git_worktree_inventory(repository),
        "worker_capabilities": worker.capabilities,
        "worker_executable": Path(resolved) if resolved else None,
    }


# --- live transport probes ---------------------------------------------------
#
# Each probe below observes a live answer and hands the doctor the evidence it
# adjudicates. None of them returns a verdict an adapter declared about itself,
# and none mutates a product resource: the Project is read, the repository is
# read, the ingress is asked only for its read-only liveness marker.


def live_work_management_evidence(work: object, profile: GitHubProfile, granted: Mapping[str, str]) -> dict[str, object]:
    """Resolve the live Project through the port, then describe what it answered.

    Projection capability is reported from the permission GitHub actually
    granted, so a profile whose installation cannot write Projects can never
    present itself as able to project.
    """
    schema = work.resolve_project()
    rows = work.import_ready_snapshot()
    projection = tuple(sorted(profile.projection_fields)) if granted.get("organization_projects") == "write" else ()
    return {
        "rows": tuple(
            {"repository": item.repository, "status": _upstream_status(profile, item), "priority": item.priority, "dependencies": list(item.dependencies)}
            for item in rows
        ),
        "lifecycle_statuses": profile.lifecycle_statuses,
        "projection_permissions": projection,
        "project": schema.project_id,
    }


def live_source_control_evidence(repository: object, granted: Mapping[str, str], remote: str) -> dict[str, object]:
    """Read the repository identity and its published baseline with the installation credential."""
    metadata = repository.metadata()
    advertised = subprocess.run(["git", "ls-remote", remote, "HEAD"], capture_output=True, text=True, check=False)
    if advertised.returncode:
        raise DoctorUnavailable("repository baseline could not be read with the installation credential")
    baseline = advertised.stdout.split()[0] if advertised.stdout.split() else ""
    permissions = tuple(f"contents:{granted['contents']}" for _ in (0,) if granted.get("contents"))
    return {"repository": str(metadata.get("full_name") or ""), "baseline": baseline, "publication_permissions": permissions}


def live_provider_evidence(worker: object, executable: str) -> dict[str, object]:
    """Establish the provider by running its own version probe, not by asking it."""
    resolved = shutil.which(executable)
    if resolved is None:
        raise DoctorFailure("worker executable is absent")
    probe = subprocess.run([resolved, "--version"], capture_output=True, text=True, check=False)
    capabilities = getattr(worker, "capabilities", None)
    dimensions = getattr(capabilities, "enforceable_dimensions", frozenset())
    return {
        "name": getattr(capabilities, "provider", ""),
        "version": (probe.stdout or probe.stderr).strip().splitlines()[0] if probe.returncode == 0 and (probe.stdout or probe.stderr).strip() else "",
        "capabilities": tuple(sorted(dimensions)),
        "authenticated": probe.returncode == 0,
    }


PROBE_USER_AGENT = "alienintent-doctor/1"


def live_transport_evidence(profile: GitHubProfile, secrets: SecretProvider) -> dict[str, object]:
    """Prove the configured public route reaches this resident ingress.

    The marker is served only by the shipped ingress, so a tunnel answering
    from any other origin — or answering nothing — cannot satisfy this probe.
    """
    route = profile.webhook_public_url
    if not route:
        raise DoctorFailure("profile records no public webhook route")
    try:
        # The probe identifies itself: an edge in front of the tunnel may refuse
        # an unidentified client, which would look like an unreachable origin.
        with urlopen(Request(route, headers={"User-Agent": PROBE_USER_AGENT}), timeout=20) as response:
            answered = response.read()
    except (URLError, TimeoutError, OSError) as error:
        raise DoctorUnavailable("configured webhook route is unreachable") from error
    if RESIDENT_INGRESS_MARKER not in answered:
        raise DoctorFailure("configured webhook route does not reach the resident ingress")
    secret = secrets.resolve(profile.webhook_secret_reference)
    body = b'{"probe":"resident-ingress-liveness"}'
    return {"route": route, "body": body, "signature": "sha256=" + hmac.new(secret, body, sha256).hexdigest()}


def _upstream_status(profile: GitHubProfile, item: object) -> str:
    """Report the upstream Status the row was imported from, not the neutral view."""
    neutral = (item.metadata or {}).get("upstream_status")
    for upstream, mapped in profile.lifecycle_statuses.items():
        if mapped == neutral:
            return upstream
    return str(neutral or "")
