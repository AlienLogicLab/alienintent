"""Acceptance proof for the fail-closed installation doctor."""

from __future__ import annotations

import hashlib
import hmac
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
        return "protected-local-file references=webhook-secret"


class _ReadOnlyFixture:
    """A recorded-fixture installation that also exposes the writes doctor must never make.

    `read` is the only non-mutating door. Every other door records the attempt
    and performs the real effect, so a doctor that creates, projects or
    publishes anything is caught rather than assumed absent.
    """

    def __init__(self, root: Path, **results: object) -> None:
        self.results = results
        self.root = root
        self.workspace_root = self.root / "workspaces"
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.effects: list[str] = []
        self.mutations: list[tuple[str, str]] = []

    def read(self, name: str) -> object:
        self.effects.append(name)
        result = self.results.get(name, self._defaults()[name])
        if isinstance(result, Exception):
            raise result
        return result

    def write(self, name: str, payload: str) -> None:
        self.mutations.append(("write", name))
        (self.root / name).write_text(payload, encoding="utf-8")

    def create(self, name: str) -> Path:
        self.mutations.append(("create", name))
        target = self.root / name
        target.mkdir(parents=True, exist_ok=True)
        return target

    def project(self, name: str, value: str) -> None:
        self.mutations.append(("project", name))
        self.write(f"{name}.projection", value)

    def publish(self, name: str) -> None:
        self.mutations.append(("publish", name))
        self.write(f"{name}.published", name)

    def _defaults(self) -> dict[str, object]:
        workspace_root = self.workspace_root
        return {
            "work_management": {"rows": ({"repository": "AlienLogicLab/alienintent", "status": "Ready", "priority": "P0", "dependencies": []},), "lifecycle_statuses": {"Ready": "READY"}, "projection_permissions": ("VERIFY",)},
            "source_control": {"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ("contents:write",)},
            "provider": {"name": "worker", "version": "1", "capabilities": ("wall-clock", "attempts", "retries", "concurrency", "cancellation"), "authenticated": True},
            "transport": {"route": "/webhook", "body": b"body", "signature": "sha256=" + hmac.new(b"usable", b"body", hashlib.sha256).hexdigest()},
            "persistence": {"preflight": lambda: type("Preflight", (), {"current_version": 2, "migration": None})()},
            "execution": {
                "workspace_root": workspace_root,
                "workspace_manager": _WorkspaceManagerDouble(),
                "git_worktrees": (workspace_root,),
                "worker_capabilities": _Capabilities(frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"})),
                "worker_executable": Path(sys.executable),
            },
        }


class _WorkspaceManagerDouble:
    def allocate(self, invocation_id: str, owner: str, baseline: str) -> object:
        raise AssertionError("doctor must never allocate a workspace")

    def cleanup(self, workspace: object, process_id: int | None) -> None:
        raise AssertionError("doctor must never remove a workspace")


class _Capabilities:
    def __init__(self, enforceable_dimensions: frozenset[str]) -> None:
        self.enforceable_dimensions = enforceable_dimensions


def _tree_digest(root: Path) -> dict[str, str]:
    """Every path under `root` with its content, so any write shows up as a diff."""
    digest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        key = str(path.relative_to(root))
        digest[key] = "dir" if path.is_dir() else hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def _profile():
    from alienintent.installation.domain.github_profile import GitHubProfile

    return GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook-secret", True)


def _installation_service(fixture: _ReadOnlyFixture, secrets: _Secrets | None = None):
    """A recorded fixture/local-double installation; each probe is read-only."""
    from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor

    return InstallationDoctor(DoctorDependencies(
        profile=_profile(), secrets=secrets or _Secrets(),
        work_management=lambda: fixture.read("work_management"),
        source_control=lambda: fixture.read("source_control"),
        provider=lambda: fixture.read("provider"),
        transport=lambda: fixture.read("transport"),
        persistence=lambda: fixture.read("persistence"),
        execution=lambda: fixture.read("execution"),
    )), fixture


def test_installation_doctor_runs_every_owned_read_only_check_without_write_effect(tmp_path: Path) -> None:
    """AC 4: no write-effect occurs — neither through the doubles nor onto disk."""
    fixture = _ReadOnlyFixture(tmp_path)
    service, _ = _installation_service(fixture)
    before = _tree_digest(tmp_path)

    report = service.run()

    assert report.ready
    assert fixture.effects == ["work_management", "source_control", "provider", "transport", "persistence", "execution"]
    assert fixture.mutations == []
    assert _tree_digest(tmp_path) == before


def test_read_only_assertion_detects_a_write_effect(tmp_path: Path) -> None:
    """The AC 4 harness must be able to go red; a check that writes is caught."""
    fixture = _ReadOnlyFixture(tmp_path)
    before = _tree_digest(tmp_path)

    fixture.write("repair-attempt", "doctor must never do this")

    assert fixture.mutations == [("write", "repair-attempt")]
    assert _tree_digest(tmp_path) != before


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
def test_installation_doctor_surfaces_distinct_sanitized_failure_for_each_required_check(check: str, evidence: Exception, tmp_path: Path) -> None:
    fixture = _ReadOnlyFixture(tmp_path, **({check: evidence} if check != "configuration" else {}))
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


def test_installation_doctor_covers_contract_negative_evidence_cases(tmp_path: Path) -> None:
    fixture = _ReadOnlyFixture(
        tmp_path,
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


_RUN_ARGUMENTS = ("run", "--actor", "morty", "--authority", "SWF-21", "--intent", "start", "--expected-version", "0", "--reason", "approved", "--idempotency-key", "run-1", "--json")


def _cli_profile(tmp_path: Path, disposition: str) -> dict[str, str]:
    """Write a real profile factory whose doctor reaches exactly one disposition."""
    broken = {
        "FAIL": "checks['persistence'] = lambda: (_ for _ in ()).throw(DoctorFailure('token=SENTINEL-CLI'))",
        "UNAVAILABLE": "checks['transport'] = lambda: (_ for _ in ()).throw(DoctorUnavailable('token=SENTINEL-CLI'))",
        "PASS": "pass",
    }[disposition]
    (tmp_path / "profile_factory.py").write_text(
        f"""
from pathlib import Path
from alienintent.composition.offline_profile import OfflineProfile
from alienintent.installation.application.doctor import CheckEvidence, DoctorFailure, DoctorService, DoctorUnavailable
class Work:
    def import_ready_snapshot(self): return ()
class Worker:
    def start(self, *_): raise AssertionError('no ready work exists to start')
def make():
    checks = {{name: CheckEvidence.passed for name in ('configuration', 'secrets', 'work_management', 'source_control', 'provider', 'transport', 'persistence', 'execution')}}
    {broken}
    return OfflineProfile(Path(__file__).with_name('state.db'), Work(), Worker(), Path(__file__).parent / 'artifacts', doctor=DoctorService(checks))
""",
        encoding="utf-8",
    )
    return os.environ | {"PYTHONPATH": f"src:{tmp_path}"}


def _alienintent(env: dict[str, str], *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alienintent", "--profile-factory", "profile_factory:make", *arguments],
        text=True, capture_output=True, env=env, check=False,
    )


def test_doctor_fail_disposition_refuses_a_real_run_attempt(tmp_path: Path) -> None:
    """AC 3 primary clause: a FAIL blocks autonomous start through the real CLI."""
    env = _cli_profile(tmp_path, "FAIL")

    doctor = _alienintent(env, "doctor", "--json")
    refused = _alienintent(env, *_RUN_ARGUMENTS)

    assert doctor.returncode == 1
    assert json.loads(doctor.stdout)["disposition"] == "FAIL"
    assert "SENTINEL-CLI" not in doctor.stdout + doctor.stderr + refused.stdout + refused.stderr
    assert refused.returncode == 2
    assert json.loads(refused.stdout) == {"error": "readiness-gate-failed"}


def test_doctor_pass_disposition_lets_a_real_run_attempt_proceed(tmp_path: Path) -> None:
    """The gate discriminates: without it, the FAIL and UNAVAILABLE refusals prove nothing."""
    env = _cli_profile(tmp_path, "PASS")

    doctor = _alienintent(env, "doctor", "--json")
    started = _alienintent(env, *_RUN_ARGUMENTS)

    assert doctor.returncode == 0
    assert json.loads(doctor.stdout)["disposition"] == "PASS"
    assert started.returncode == 0, started.stdout + started.stderr
    assert json.loads(started.stdout) != {"error": "readiness-gate-failed"}
