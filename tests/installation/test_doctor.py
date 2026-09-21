"""Acceptance proof for the fail-closed installation doctor."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


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
