"""Read-only, fail-closed pre-autonomy installation validation."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Literal

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


@dataclass(frozen=True)
class WorkManagementEvidence:
    project_reachable: bool; lifecycle_mapping_complete: bool; priority_readable: bool; dependencies_readable: bool; projection_capability: bool


@dataclass(frozen=True)
class SourceControlEvidence:
    repository_reachable: bool; baseline_resolvable: bool; candidate_publication_capable: bool


@dataclass(frozen=True)
class ProviderEvidence:
    present: bool; version_reported: bool; capabilities_advertised: bool; budget_enforceable: bool; authenticated: bool


@dataclass(frozen=True)
class TransportEvidence:
    route_configured: bool; secret_configured: bool; signature_verified: bool


@dataclass(frozen=True)
class PersistenceEvidence:
    reachable: bool; schema_compatible: bool; migrations_settled: bool


@dataclass(frozen=True)
class ExecutionEvidence:
    workspace_writable: bool; worktree_available: bool; process_control_available: bool


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
        if not isinstance(profile, GitHubProfile):
            raise DoctorFailure("profile is not typed-valid")
        # GitHubProfile validates required references and mappings at construction;
        # this additional guard makes an isolated profile name explicit evidence.
        if not profile.profile.strip() or not profile.repository.strip() or not profile.project_reference.strip():
            raise DoctorFailure("profile namespace is incomplete")
        return CheckEvidence.passed()

    def _secrets(self) -> CheckEvidence:
        reference = self._dependencies.profile.webhook_secret_reference
        material = self._dependencies.secrets.resolve(reference)
        if not isinstance(material, bytes) or not material:
            raise DoctorFailure("secret provider returned an unusable handle")
        return CheckEvidence.passed()

    @staticmethod
    def _require(evidence: object, kind: type[object], *facts: bool) -> CheckEvidence:
        if not isinstance(evidence, kind) or not all(facts):
            raise DoctorFailure("adapter did not provide complete positive readiness evidence")
        return CheckEvidence.passed()

    def _work_management(self) -> CheckEvidence:
        value = self._dependencies.work_management()
        return self._require(value, WorkManagementEvidence, value.project_reachable, value.lifecycle_mapping_complete, value.priority_readable, value.dependencies_readable, value.projection_capability) if isinstance(value, WorkManagementEvidence) else self._require(value, WorkManagementEvidence, False)

    def _source_control(self) -> CheckEvidence:
        value = self._dependencies.source_control()
        return self._require(value, SourceControlEvidence, value.repository_reachable, value.baseline_resolvable, value.candidate_publication_capable) if isinstance(value, SourceControlEvidence) else self._require(value, SourceControlEvidence, False)

    def _provider(self) -> CheckEvidence:
        value = self._dependencies.provider()
        return self._require(value, ProviderEvidence, value.present, value.version_reported, value.capabilities_advertised, value.budget_enforceable, value.authenticated) if isinstance(value, ProviderEvidence) else self._require(value, ProviderEvidence, False)

    def _transport(self) -> CheckEvidence:
        value = self._dependencies.transport()
        return self._require(value, TransportEvidence, value.route_configured, value.secret_configured, value.signature_verified) if isinstance(value, TransportEvidence) else self._require(value, TransportEvidence, False)

    def _persistence(self) -> CheckEvidence:
        value = self._dependencies.persistence()
        return self._require(value, PersistenceEvidence, value.reachable, value.schema_compatible, value.migrations_settled) if isinstance(value, PersistenceEvidence) else self._require(value, PersistenceEvidence, False)

    def _execution(self) -> CheckEvidence:
        value = self._dependencies.execution()
        return self._require(value, ExecutionEvidence, value.workspace_writable, value.worktree_available, value.process_control_available) if isinstance(value, ExecutionEvidence) else self._require(value, ExecutionEvidence, False)


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
