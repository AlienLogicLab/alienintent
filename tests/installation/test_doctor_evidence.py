"""Discriminating evidence tests for the PY-09 installation doctor."""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
import sqlite3


def test_doctor_rejects_ambiguous_status_mapping_from_recorded_project_evidence(tmp_path: Path) -> None:
    """Removing mapping validation must make this fail: two statuses cannot mean READY."""
    from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor
    from alienintent.installation.domain.github_profile import GitHubProfile

    profile = GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook", True)
    dependencies = _dependencies(
        profile=profile,
        secret=b"usable",
        work_rows=({"repository": "AlienLogicLab/alienintent", "status": "Ready", "priority": "P0", "dependencies": []},),
        lifecycle_statuses={"Ready": "READY", "Todo": "READY"},
        source_control={"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ("contents:write",)},
        provider={"name": "worker", "version": "1", "capabilities": ("wall-clock", "attempts", "retries", "concurrency", "cancellation"), "authenticated": True},
        webhook=_webhook_fixture(b"usable"),
        persistence_preflight=lambda: _preflight(tmp_path / "state.db"),
        workspace=tmp_path,
    )

    report = InstallationDoctor(dependencies).run()

    assert _outcome(report, "work_management") == "FAIL"


def test_doctor_rejects_incompatible_sqlite_schema_from_preflight(tmp_path: Path) -> None:
    """Replacing SQLite preflight with a claimed pass must make this fail."""
    from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor
    from alienintent.installation.domain.github_profile import GitHubProfile

    database = tmp_path / "future.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE operational_schema (version INTEGER NOT NULL)")
        connection.execute("INSERT INTO operational_schema VALUES (99)")
    profile = GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook", True)
    dependencies = _dependencies(
        profile=profile, secret=b"usable",
        work_rows=({"repository": "AlienLogicLab/alienintent", "status": "Ready", "priority": "P0", "dependencies": []},),
        lifecycle_statuses={"Ready": "READY"},
        source_control={"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ("contents:write",)},
        provider={"name": "worker", "version": "1", "capabilities": ("wall-clock", "attempts", "retries", "concurrency", "cancellation"), "authenticated": True},
        webhook=_webhook_fixture(b"usable"), persistence_preflight=lambda: _preflight(database), workspace=tmp_path,
    )

    report = InstallationDoctor(dependencies).run()

    assert _outcome(report, "persistence") == "FAIL"


def test_doctor_rejects_missing_priority_in_recorded_project_evidence(tmp_path: Path) -> None:
    """Removing Priority validation must make this fail."""
    report = _doctor(tmp_path, work_rows=({"repository": "AlienLogicLab/alienintent", "status": "Ready", "dependencies": []},))
    assert _outcome(report, "work_management") == "FAIL"


def test_doctor_rejects_resolved_secret_when_webhook_signature_rejects_material(tmp_path: Path) -> None:
    """An HTTP-shaped fixture is not ready unless the production HMAC rule accepts it."""
    fixture = _webhook_fixture(b"different-material")
    report = _doctor(tmp_path, webhook=fixture)
    assert _outcome(report, "transport") == "FAIL"


def test_doctor_rejects_missing_candidate_publication_permission(tmp_path: Path) -> None:
    """A reachable repository is insufficient without read-back write capability."""
    report = _doctor(tmp_path, source_control={"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ()})
    assert _outcome(report, "source_control") == "FAIL"


def test_doctor_rejects_provider_without_every_enforceable_budget_dimension(tmp_path: Path) -> None:
    """Removing the capability-set check must make this fail."""
    report = _doctor(tmp_path, provider={"name": "worker", "version": "1", "capabilities": ("wall-clock", "attempts"), "authenticated": True})
    assert _outcome(report, "provider") == "FAIL"


def _doctor(tmp_path: Path, *, work_rows: tuple[dict[str, object], ...] | None = None, source_control: dict[str, object] | None = None, provider: dict[str, object] | None = None, webhook: dict[str, object] | None = None) -> object:
    from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor
    from alienintent.installation.domain.github_profile import GitHubProfile
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    database = tmp_path / "state.db"
    SQLiteOperationalStore(database)
    profile = GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook", True)
    return InstallationDoctor(_dependencies(
        profile=profile, secret=b"usable",
        work_rows=work_rows or ({"repository": "AlienLogicLab/alienintent", "status": "Ready", "priority": "P0", "dependencies": []},),
        lifecycle_statuses={"Ready": "READY"},
        source_control=source_control or {"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ("contents:write",)},
        provider=provider or {"name": "worker", "version": "1", "capabilities": ("wall-clock", "attempts", "retries", "concurrency", "cancellation"), "authenticated": True},
        webhook=webhook or _webhook_fixture(b"usable"), persistence_preflight=lambda: _preflight(database), workspace=tmp_path,
    )).run()


def _webhook_fixture(secret: bytes) -> dict[str, object]:
    body = b'{"project_item":{"id":"PVT_x","version":1},"repository":{"full_name":"AlienLogicLab/alienintent"}}'
    return {"route": "/webhook", "body": body, "signature": "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()}


def _outcome(report: object, name: str) -> str:
    return next(item.outcome for item in report.checks if item.name == name)  # type: ignore[attr-defined]


def _preflight(database: Path) -> object:
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    return SQLiteOperationalStore.preflight(database)


def _dependencies(**values: object) -> object:
    from alienintent.installation.application.doctor import DoctorDependencies

    secret = values.pop("secret")
    class Secrets:
        def resolve(self, reference: str) -> bytes:
            assert isinstance(secret, bytes)
            return secret
    return DoctorDependencies(
        values["profile"], Secrets(),
        lambda: {"rows": values["work_rows"], "lifecycle_statuses": values["lifecycle_statuses"]},
        lambda: values["source_control"], lambda: values["provider"], lambda: values["webhook"],
        lambda: {"preflight": values["persistence_preflight"]}, lambda: {"workspace": values["workspace"]},
    )
