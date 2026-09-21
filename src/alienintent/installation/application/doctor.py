"""Read-only, fail-closed pre-autonomy installation validation."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
import os
from pathlib import Path
from typing import Literal

from alienintent.execution_coordination.domain.webhook_authenticity import signature_valid
from alienintent.installation.domain.github_profile import GitHubProfile
from alienintent.installation.ports.secret_provider import SecretProvider


Outcome = Literal["PASS", "FAIL", "UNAVAILABLE", "WARNING"]

REQUIRED_CHECKS = (
    "configuration", "secrets", "work_management", "source_control",
    "provider", "transport", "persistence", "execution",
)

_ACTIONS = {
    "configuration": "correct the configured profile and isolated namespaces",
    "secrets": "correct the configured secret reference and provider access",
    "work_management": "restore authenticated Project access and complete lifecycle mapping",
    "source_control": "restore repository, baseline, and candidate publication access",
    "provider": "restore authenticated provider readiness and enforceable budgets",
    "transport": "correct webhook route and verify its configured signature",
    "persistence": "restore compatible persistent storage and settle migrations",
    "execution": "restore workspace, worktree, and process-control capability",
}


class DoctorFailure(RuntimeError):
    """A required prerequisite was positively shown to be broken."""


class DoctorUnavailable(RuntimeError):
    """A required prerequisite could not be positively evidenced."""


@dataclass(frozen=True)
class CheckEvidence:
    outcome: Outcome

    @classmethod
    def passed(cls) -> "CheckEvidence":
        return cls("PASS")

    @classmethod
    def warning(cls) -> "CheckEvidence":
        return cls("WARNING")

    @classmethod
    def unavailable(cls) -> "CheckEvidence":
        return cls("UNAVAILABLE")


@dataclass(frozen=True)
class CheckResult:
    name: str
    outcome: Outcome
    suggested_action: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[CheckResult, ...]
    disposition: Outcome
    exit_code: int

    @property
    def ready(self) -> bool:
        return self.disposition in {"PASS", "WARNING"}

    def as_dict(self) -> dict[str, object]:
        return {"checks": [asdict(check) for check in self.checks], "disposition": self.disposition, "exit_code": self.exit_code, "ready": self.ready}


@dataclass(frozen=True)
class DoctorDependencies:
    """Read-only probes supplied by the installed profile's adapters.

    Each probe must provide authenticated or recorded-fixture evidence and must
    not create, project, publish, or otherwise mutate a product resource.
    """

    profile: object
    secrets: SecretProvider
    work_management: Callable[[], object]
    source_control: Callable[[], object]
    provider: Callable[[], object]
    transport: Callable[[], object]
    persistence: Callable[[], object]
    execution: Callable[[], object]


class InstallationDoctor:
    """Own the eight Wave-1 prerequisites; adapters provide only read evidence."""

    def __init__(self, dependencies: DoctorDependencies) -> None:
        self._dependencies = dependencies

    def run(self) -> DoctorReport:
        checks = {
            "configuration": self._configuration,
            "secrets": self._secrets,
            "work_management": self._work_management,
            "source_control": self._source_control,
            "provider": self._provider,
            "transport": self._transport,
            "persistence": self._persistence,
            "execution": self._execution,
        }
        return DoctorService(checks).run()

    def _configuration(self) -> CheckEvidence:
        profile = self._dependencies.profile
        # GitHubProfile rejects blank identity, an unmapped READY status, an
        # authority-inverting status and unknown fields at construction, so a
        # typed profile in hand *is* the positive evidence. Re-checking those
        # rules here would be unreachable code that no test could turn red.
        if not isinstance(profile, GitHubProfile):
            raise DoctorFailure("profile is not typed-valid")
        return CheckEvidence.passed()

    def _secrets(self) -> CheckEvidence:
        reference = self._dependencies.profile.webhook_secret_reference
        material = self._dependencies.secrets.resolve(reference)
        if not isinstance(material, bytes) or not material:
            raise DoctorFailure("secret provider returned an unusable handle")
        # Positive evidence is the provider naming the reference it holds; the
        # same diagnostic must never carry the material it resolved.
        diagnostic = self._dependencies.secrets.diagnostic()
        if not isinstance(diagnostic, str) or reference not in diagnostic:
            raise DoctorFailure("secret provider does not report the configured reference")
        if material and material.decode("latin-1") in diagnostic:
            raise DoctorFailure("secret provider diagnostic reveals resolved material")
        return CheckEvidence.passed()

    def _work_management(self) -> CheckEvidence:
        value = self._dependencies.work_management()
        if isinstance(value, Mapping):
            rows, statuses = value.get("rows"), value.get("lifecycle_statuses")
            if not isinstance(rows, tuple) or not isinstance(statuses, Mapping):
                raise DoctorFailure("recorded Project evidence is incomplete")
            mapped = tuple(statuses.values())
            if not mapped or mapped.count("READY") != 1 or len(set(mapped)) != len(mapped):
                raise DoctorFailure("lifecycle Status mapping is incomplete or ambiguous")
            permissions = value.get("projection_permissions")
            if not isinstance(permissions, tuple) or "VERIFY" not in permissions:
                raise DoctorFailure("projection write capability cannot be read back")
            for row in rows:
                if not isinstance(row, Mapping) or row.get("repository") != self._dependencies.profile.repository or row.get("status") not in statuses:
                    raise DoctorFailure("recorded Project is unreachable or unmapped")
                if "priority" not in row or not isinstance(row.get("dependencies"), (list, tuple)):
                    raise DoctorFailure("Priority or dependency evidence is missing")
            return CheckEvidence.passed()
        raise DoctorFailure("recorded Project evidence is unavailable")

    def _source_control(self) -> CheckEvidence:
        value = self._dependencies.source_control()
        if isinstance(value, Mapping):
            permissions = value.get("publication_permissions")
            if value.get("repository") != self._dependencies.profile.repository or not isinstance(value.get("baseline"), str) or len(value["baseline"]) != 40 or not isinstance(permissions, tuple) or "contents:write" not in permissions:
                raise DoctorFailure("repository, baseline, or publication permission cannot be read back")
            return CheckEvidence.passed()
        raise DoctorFailure("source-control evidence is unavailable")

    def _provider(self) -> CheckEvidence:
        value = self._dependencies.provider()
        if isinstance(value, Mapping):
            capabilities = value.get("capabilities")
            required = {"wall-clock", "attempts", "retries", "concurrency", "cancellation"}
            if not isinstance(value.get("name"), str) or not value["name"] or not isinstance(value.get("version"), str) or not value["version"] or not isinstance(capabilities, tuple) or not required.issubset(capabilities) or value.get("authenticated") is not True:
                raise DoctorFailure("provider readiness or enforceable budget evidence is incomplete")
            return CheckEvidence.passed()
        raise DoctorFailure("provider evidence is unavailable")

    def _transport(self) -> CheckEvidence:
        value = self._dependencies.transport()
        if isinstance(value, Mapping):
            body, signature, route = value.get("body"), value.get("signature"), value.get("route")
            secret = self._dependencies.secrets.resolve(self._dependencies.profile.webhook_secret_reference)
            if not isinstance(route, str) or not route or not isinstance(body, bytes) or not isinstance(signature, str) or not signature_valid(secret, body, signature):
                raise DoctorFailure("webhook route or signature evidence is invalid")
            return CheckEvidence.passed()
        raise DoctorFailure("transport evidence is unavailable")

    def _persistence(self) -> CheckEvidence:
        value = self._dependencies.persistence()
        if isinstance(value, Mapping):
            preflight = value.get("preflight")
            if not callable(preflight):
                raise DoctorFailure("persistence location is unavailable")
            observed = preflight()
            current_version, migration = getattr(observed, "current_version", None), getattr(observed, "migration", None)
            if current_version != 2 or migration is not None:
                raise DoctorFailure("persistence schema is incompatible or unsettled")
            return CheckEvidence.passed()
        raise DoctorFailure("persistence evidence is unavailable")

    def _execution(self) -> CheckEvidence:
        """Derive execution capability from the filesystem and negotiated capability.

        Nothing here creates a worktree or starts a process: the workspace root
        is stat-ed, the worktree inventory is read back, and process control is
        established by the provider advertising the dimensions it can enforce.
        """
        value = self._dependencies.execution()
        if not isinstance(value, Mapping):
            raise DoctorFailure("execution evidence is unavailable")
        root = value.get("workspace_root")
        if not isinstance(root, Path) or not root.is_dir():
            raise DoctorFailure("workspace root is absent or is not a directory")
        if not os.access(root, os.W_OK | os.X_OK):
            raise DoctorFailure("workspace root is not writable")
        manager = value.get("workspace_manager")
        if not callable(getattr(manager, "allocate", None)) or not callable(getattr(manager, "cleanup", None)):
            raise DoctorFailure("no workspace manager can create a Git worktree")
        inventory = value.get("git_worktrees")
        if not isinstance(inventory, tuple) or not inventory or not all(isinstance(entry, Path) and entry.is_dir() for entry in inventory):
            raise DoctorFailure("Git worktree inventory could not be read back")
        dimensions = getattr(value.get("worker_capabilities"), "enforceable_dimensions", None)
        if not isinstance(dimensions, frozenset) or not {"wall-clock", "cancellation"} <= dimensions:
            raise DoctorFailure("worker provider does not negotiate process control")
        executable = value.get("worker_executable")
        if not isinstance(executable, Path) or not executable.is_file() or not os.access(executable, os.X_OK):
            raise DoctorFailure("worker executable is absent or not executable")
        return CheckEvidence.passed()


class DoctorService:
    """Aggregate only positive, non-mutating readiness evidence from profile checks."""

    def __init__(self, checks: Mapping[str, Callable[[], CheckEvidence]], *, advisory_checks: Mapping[str, Callable[[], CheckEvidence]] | None = None) -> None:
        if set(checks) != set(REQUIRED_CHECKS):
            raise ValueError("all required checks must be configured exactly once")
        if advisory_checks is not None and (set(advisory_checks) & set(REQUIRED_CHECKS) or any(not name for name in advisory_checks)):
            raise ValueError("advisory checks cannot replace required checks")
        self._checks = dict(checks)
        self._advisory_checks = dict(advisory_checks or {})

    def run(self) -> DoctorReport:
        results = tuple(self._run_check(name, self._checks[name], required=True) for name in REQUIRED_CHECKS)
        results += tuple(self._run_check(name, check, required=False) for name, check in self._advisory_checks.items())
        outcomes = {result.outcome for result in results}
        if "FAIL" in outcomes:
            disposition, exit_code = "FAIL", 1
        elif "UNAVAILABLE" in outcomes:
            disposition, exit_code = "UNAVAILABLE", 2
        elif "WARNING" in outcomes:
            disposition, exit_code = "WARNING", 3
        else:
            disposition, exit_code = "PASS", 0
        return DoctorReport(results, disposition, exit_code)

    @staticmethod
    def _run_check(name: str, check: Callable[[], CheckEvidence], *, required: bool) -> CheckResult:
        try:
            evidence = check()
        except DoctorUnavailable:
            return CheckResult(name, "UNAVAILABLE", _ACTIONS.get(name, "inspect the unavailable prerequisite"))
        except Exception:
            return CheckResult(name, "FAIL", _ACTIONS.get(name, "correct the reported prerequisite"))
        # Required Wave 1 checks have no advisory mode.  A profile cannot
        # relabel a missing prerequisite as a warning.
        if not isinstance(evidence, CheckEvidence):
            return CheckResult(name, "FAIL", _ACTIONS.get(name, "correct the reported prerequisite"))
        if evidence.outcome == "WARNING" and not required:
            return CheckResult(name, "WARNING", "inspect the advisory observation")
        if evidence.outcome == "UNAVAILABLE":
            return CheckResult(name, "UNAVAILABLE", _ACTIONS.get(name, "inspect the unavailable prerequisite"))
        if evidence.outcome != "PASS":
            return CheckResult(name, "FAIL", _ACTIONS.get(name, "correct the reported prerequisite"))
        return CheckResult(name, "PASS")
