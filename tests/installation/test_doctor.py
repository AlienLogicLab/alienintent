"""Acceptance proof for the fail-closed installation doctor."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


class _Secrets:
    def __init__(self, value: bytes = b"usable", *, reject: bool = False) -> None:
        self.value, self.reject, self.effects = value, reject, []

    def resolve(self, reference: str) -> bytes:
        self.effects.append(("resolve", reference))
        if self.reject:
            raise RuntimeError("token=SENTINEL-SECRET")
        return self.value

    def diagnostic(self) -> str:
        return "available"


class _ReadOnlyFixture:
    def __init__(self, **results: object) -> None:
        self.results = results
        self.effects: list[str] = []

    def read(self, name: str) -> object:
        self.effects.append(name)
        from alienintent.installation.application.doctor import ExecutionEvidence, PersistenceEvidence, ProviderEvidence, SourceControlEvidence, TransportEvidence, WorkManagementEvidence
        defaults = {
            "work_management": WorkManagementEvidence(True, True, True, True, True),
            "source_control": SourceControlEvidence(True, True, True),
            "provider": ProviderEvidence(True, True, True, True, True),
            "transport": TransportEvidence(True, True, True),
            "persistence": PersistenceEvidence(True, True, True),
            "execution": ExecutionEvidence(True, True, True),
        }
        result = self.results.get(name, defaults[name])
        if isinstance(result, Exception):
            raise result
        return result


def _profile():
    from alienintent.installation.domain.github_profile import GitHubProfile

    return GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook-secret", True)


def _installation_service(fixture: _ReadOnlyFixture | None = None, secrets: _Secrets | None = None):
    """A recorded fixture/local-double installation; each probe is read-only."""
    from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor

    fixture = fixture or _ReadOnlyFixture()
    return InstallationDoctor(DoctorDependencies(
        profile=_profile(), secrets=secrets or _Secrets(),
        work_management=lambda: fixture.read("work_management"),
        source_control=lambda: fixture.read("source_control"),
        provider=lambda: fixture.read("provider"),
        transport=lambda: fixture.read("transport"),
        persistence=lambda: fixture.read("persistence"),
        execution=lambda: fixture.read("execution"),
    )), fixture


def test_installation_doctor_runs_every_owned_read_only_check_without_write_effect() -> None:
    service, fixture = _installation_service()

    report = service.run()

    assert report.ready
    assert fixture.effects == ["work_management", "source_control", "provider", "transport", "persistence", "execution"]


@pytest.mark.parametrize(("check", "evidence"), (
    ("configuration", ValueError("unknown profile field")),
    ("secrets", RuntimeError("provider rejected material")),
    ("work_management", ValueError("ambiguous status mapping")),
    ("source_control", RuntimeError("baseline unavailable")),
    ("provider", RuntimeError("unauthenticated")),
    ("transport", ValueError("signature verification failed")),
    ("persistence", ValueError("incompatible schema")),
    ("execution", RuntimeError("worktree unavailable")),
))
def test_installation_doctor_surfaces_distinct_sanitized_failure_for_each_required_check(check: str, evidence: Exception) -> None:
    fixture = _ReadOnlyFixture(**({check: evidence} if check != "configuration" else {}))
    secrets = _Secrets(reject=check == "secrets")
    service, _ = _installation_service(fixture, secrets)
    if check == "configuration":
        from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor
        service = InstallationDoctor(DoctorDependencies(
            profile=object(), secrets=secrets, work_management=lambda: True, source_control=lambda: True,
            provider=lambda: True, transport=lambda: True, persistence=lambda: True, execution=lambda: True,
        ))

    result = next(item for item in service.run().checks if item.name == check)

    assert result.outcome == "FAIL"
    assert result.suggested_action
    assert "SENTINEL-SECRET" not in str(result)


def test_installation_doctor_covers_contract_negative_evidence_cases() -> None:
    fixture = _ReadOnlyFixture(
        work_management=ValueError("reachable project has incomplete lifecycle Status mapping and missing Priority"),
        transport=ValueError("endpoint responded but signature verification failed"),
        persistence=ValueError("incompatible persistence schema version"),
    )
    service, _ = _installation_service(fixture, _Secrets(reject=True))

    report = service.run()

    assert {item.name for item in report.checks if item.outcome == "FAIL"} == {"secrets", "work_management", "transport", "persistence"}


def _service(results: dict[str, object]):
    from alienintent.installation.application.doctor import CheckEvidence, DoctorService

    checks = {
        name: value if callable(value) else (lambda value=value: value)
        for name, value in results.items()
    }
    return DoctorService(checks)


def _passed() -> object:
    from alienintent.installation.application.doctor import CheckEvidence

    return CheckEvidence.passed()


def test_doctor_requires_positive_evidence_for_every_required_check() -> None:
    from alienintent.installation.application.doctor import DoctorService

    with pytest.raises(ValueError, match="required checks"):
        DoctorService({"configuration": _passed})


def test_doctor_reports_fail_and_unavailable_distinctly_without_secret_leakage() -> None:
    from alienintent.installation.application.doctor import CheckEvidence, DoctorFailure, DoctorUnavailable

    results = {name: _passed() for name in (
        "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution",
    )}
    results["secrets"] = lambda: (_ for _ in ()).throw(DoctorFailure("token=SENTINEL-SECRET"))
    results["provider"] = lambda: (_ for _ in ()).throw(DoctorUnavailable("stderr SENTINEL-SECRET"))

    report = _service(results).run()

    assert report.exit_code == 1
    assert report.disposition == "FAIL"
    payload = report.as_dict()
    assert {item["name"]: item["outcome"] for item in payload["checks"]} == {
        "configuration": "PASS", "secrets": "FAIL", "work_management": "PASS", "source_control": "PASS",
        "provider": "UNAVAILABLE", "transport": "PASS", "persistence": "PASS", "execution": "PASS",
    }
    assert "SENTINEL-SECRET" not in json.dumps(payload)
    assert all(item["suggested_action"] for item in payload["checks"] if item["outcome"] != "PASS")


def test_doctor_returns_unavailable_exit_when_no_check_failed() -> None:
    from alienintent.installation.application.doctor import DoctorUnavailable

    results = {name: _passed() for name in (
        "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution",
    )}
    results["transport"] = lambda: (_ for _ in ()).throw(DoctorUnavailable("offline"))

    report = _service(results).run()

    assert (report.disposition, report.exit_code, report.ready) == ("UNAVAILABLE", 2, False)


@pytest.mark.parametrize("broken", (
    "configuration", "secrets", "work_management", "source_control",
    "provider", "transport", "persistence", "execution",
))
def test_each_required_check_requires_positive_evidence(broken: str) -> None:
    """Returning a truthy non-evidence value for any prerequisite must not start work."""
    results = {name: _passed() for name in (
        "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution",
    )}
    results[broken] = True

    report = _service(results).run()

    assert report.disposition == "FAIL"
    assert next(item for item in report.as_dict()["checks"] if item["name"] == broken)["outcome"] == "FAIL"


def test_doctor_only_observes_the_configured_read_only_probes() -> None:
    """Adding a repair/write operation to doctor would change this observed effect."""
    observed: list[str] = []
    def probe(name: str):
        def read_only_probe():
            observed.append(name)
            return _passed()
        return read_only_probe
    report = _service({name: probe(name) for name in (
        "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution",
    )}).run()

    assert report.ready
    assert observed == ["configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution"]


def test_warning_is_reserved_and_cannot_downgrade_a_required_check() -> None:
    from alienintent.installation.application.doctor import CheckEvidence

    results = {name: _passed() for name in (
        "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution",
    )}
    results["configuration"] = CheckEvidence.warning

    report = _service(results).run()

    assert (report.disposition, report.exit_code, report.ready) == ("FAIL", 1, False)
    assert next(item for item in report.as_dict()["checks"] if item["name"] == "configuration")["outcome"] == "FAIL"


def test_test_only_advisory_warning_retains_the_reserved_warning_exit_code() -> None:
    """Removing the warning aggregation branch would make a warning block autonomy."""
    from alienintent.installation.application.doctor import CheckEvidence, DoctorService

    service = DoctorService(
        {name: _passed for name in (
            "configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution",
        )},
        advisory_checks={"test_observation": CheckEvidence.warning},
    )

    report = service.run()

    assert (report.disposition, report.exit_code, report.ready) == ("WARNING", 3, True)


def test_doctor_cli_emits_stable_json_and_run_refuses_when_unavailable(tmp_path: Path) -> None:
    factory = tmp_path / "profile_factory.py"
    factory.write_text(
        """
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
from alienintent.installation.application.doctor import CheckEvidence, DoctorService, DoctorUnavailable
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def start(self, *_): raise AssertionError('doctor must refuse start')
def make():
    checks = {name: CheckEvidence.passed for name in ('configuration', 'secrets', 'work_management', 'source_control', 'provider', 'transport', 'persistence', 'execution')}
    checks['transport'] = lambda: (_ for _ in ()).throw(DoctorUnavailable('token=SENTINEL-CLI'))
    return OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts', doctor=DoctorService(checks))
"""
    )
    env = os.environ | {"PYTHONPATH": f"src:{tmp_path}"}
    doctor = subprocess.run([sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "doctor", "--json"], text=True, capture_output=True, env=env, check=False)
    refused = subprocess.run([sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", "run", "--actor", "morty", "--authority", "SWF-21", "--intent", "start", "--expected-version", "0", "--reason", "approved", "--idempotency-key", "run-1", "--json"], text=True, capture_output=True, env=env, check=False)

    assert doctor.returncode == 2
    assert json.loads(doctor.stdout)["disposition"] == "UNAVAILABLE"
    assert "SENTINEL-CLI" not in doctor.stdout + doctor.stderr
    assert refused.returncode != 0
    assert json.loads(refused.stdout) == {"error": "readiness-gate-failed"}
