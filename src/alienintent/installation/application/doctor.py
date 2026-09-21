"""Read-only, fail-closed pre-autonomy installation validation."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from typing import Literal


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
            return CheckResult(name, "UNAVAILABLE", _ACTIONS[name])
        except Exception:
            return CheckResult(name, "FAIL", _ACTIONS[name])
        # Required Wave 1 checks have no advisory mode.  A profile cannot
        # relabel a missing prerequisite as a warning.
        if not isinstance(evidence, CheckEvidence):
            return CheckResult(name, "FAIL", _ACTIONS.get(name, "correct the reported prerequisite"))
        if evidence.outcome == "WARNING" and not required:
            return CheckResult(name, "WARNING", "inspect the advisory observation")
        if evidence.outcome != "PASS":
            return CheckResult(name, "FAIL", _ACTIONS.get(name, "correct the reported prerequisite"))
        return CheckResult(name, "PASS")
