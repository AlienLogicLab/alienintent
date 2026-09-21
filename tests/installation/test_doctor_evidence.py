"""Discriminating evidence tests for the PY-09 installation doctor.

Every test here is written so that removing the guard it names turns it red.
The PASS path is driven by the real `GitWorktreeAdapter` and
`CliWorkerProvider` through the composition-root probe, so a green execution
check means those adapters really answered.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


REQUIRED = ("configuration", "secrets", "work_management", "source_control", "provider", "transport", "persistence", "execution")


def test_doctor_accepts_every_prerequisite_on_recorded_evidence(tmp_path: Path) -> None:
    """AC 1 passing case: all eight checks reach PASS on evidence, exit 0."""
    report = _doctor(tmp_path)

    assert {item.name: item.outcome for item in report.checks} == {name: "PASS" for name in REQUIRED}
    assert (report.disposition, report.exit_code, report.ready) == ("PASS", 0, True)


def test_doctor_rejects_ambiguous_status_mapping_from_recorded_project_evidence(tmp_path: Path) -> None:
    """Removing mapping validation must make this fail: two statuses cannot mean READY."""
    report = _doctor(tmp_path, lifecycle_statuses={"Ready": "READY", "Todo": "READY"})
    assert _outcome(report, "work_management") == "FAIL"


def test_doctor_rejects_incompatible_sqlite_schema_from_preflight(tmp_path: Path) -> None:
    """Replacing SQLite preflight with a claimed pass must make this fail."""
    database = tmp_path / "future.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE operational_schema (version INTEGER NOT NULL)")
        connection.execute("INSERT INTO operational_schema VALUES (99)")

    report = _doctor(tmp_path, persistence_database=database)

    assert _outcome(report, "persistence") == "FAIL"


def test_doctor_rejects_persistence_whose_migration_has_not_settled(tmp_path: Path) -> None:
    """Reaches the version/migration comparison: schema 1 returns an unsettled migration.

    The schema-99 case above raises out of `preflight()` before any doctor
    logic runs, so only this case can turn the comparison red.
    """
    database = tmp_path / "unsettled.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE operational_schema (version INTEGER NOT NULL)")
        connection.execute("INSERT INTO operational_schema VALUES (1)")
    observed = _preflight(database)
    assert (observed.current_version, observed.migration) == (1, (1, 2))

    report = _doctor(tmp_path, persistence_database=database)

    assert _outcome(report, "persistence") == "FAIL"


def test_doctor_rejects_missing_priority_in_recorded_project_evidence(tmp_path: Path) -> None:
    """Removing Priority validation must make this fail."""
    report = _doctor(tmp_path, work_rows=({"repository": "AlienLogicLab/alienintent", "status": "Ready", "dependencies": []},))
    assert _outcome(report, "work_management") == "FAIL"


def test_doctor_rejects_webhook_endpoint_whose_signature_verification_fails(tmp_path: Path) -> None:
    """AC 2 case 1: the endpoint responds, the production HMAC rule still refuses it."""
    report = _doctor(tmp_path, webhook=_webhook_fixture(b"different-material"))
    assert _outcome(report, "transport") == "FAIL"


def test_doctor_transport_check_is_bound_to_the_production_signature_rule(tmp_path: Path) -> None:
    """Doctor must exercise the shipped rule, not a copy that can drift from it."""
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    from alienintent.execution_coordination.domain import webhook_authenticity
    from alienintent.installation.application import doctor as doctor_module

    fixture = _webhook_fixture(b"usable")
    assert webhook_authenticity.signature_valid(b"usable", fixture["body"], fixture["signature"])
    assert GitHubWebhookIngress.signature_valid(b"usable", fixture["body"], fixture["signature"])

    def refuse_everything(secret: bytes, raw_body: bytes, authenticity: str) -> bool:
        return False

    original = webhook_authenticity.signature_valid
    webhook_authenticity.signature_valid = refuse_everything
    doctor_module.signature_valid = refuse_everything
    try:
        report = _doctor(tmp_path)
    finally:
        webhook_authenticity.signature_valid = original
        doctor_module.signature_valid = original

    assert _outcome(report, "transport") == "FAIL"


def test_doctor_rejects_missing_candidate_publication_permission(tmp_path: Path) -> None:
    """A reachable repository is insufficient without read-back write capability."""
    report = _doctor(tmp_path, source_control={"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ()})
    assert _outcome(report, "source_control") == "FAIL"


def test_doctor_rejects_provider_without_every_enforceable_budget_dimension(tmp_path: Path) -> None:
    """Removing the capability-set check must make this fail."""
    report = _doctor(tmp_path, provider=_provider_evidence(capabilities=("wall-clock", "attempts")))
    assert _outcome(report, "provider") == "FAIL"


def test_doctor_rejects_resolvable_secret_whose_material_the_provider_rejects(tmp_path: Path) -> None:
    """AC 2 case 2: the reference resolves; the worker provider rejects the material."""
    report = _doctor(tmp_path, provider=_provider_evidence(authenticated=False))

    assert _outcome(report, "secrets") == "PASS"
    assert _outcome(report, "provider") == "FAIL"


def test_doctor_rejects_unusable_resolved_secret_handle(tmp_path: Path) -> None:
    """Removing the usable-handle guard must make this fail: empty material is not a handle."""
    report = _doctor(tmp_path, secret=b"")
    assert _outcome(report, "secrets") == "FAIL"


def test_doctor_rejects_secret_provider_that_does_not_report_the_configured_reference(tmp_path: Path) -> None:
    """Resolving something is not evidence the provider holds the configured reference."""
    report = _doctor(tmp_path, secret_diagnostic="protected-local-file references=some-other-reference")
    assert _outcome(report, "secrets") == "FAIL"


def test_doctor_rejects_secret_provider_diagnostic_that_reveals_material(tmp_path: Path) -> None:
    """Binding rule 3: a provider that leaks its own material is not a usable path."""
    report = _doctor(tmp_path, secret=b"leaked-material", secret_diagnostic="references=webhook-secret value=leaked-material")
    assert _outcome(report, "secrets") == "FAIL"


def test_doctor_rejects_project_evidence_without_read_back_projection_capability(tmp_path: Path) -> None:
    """Configured projection fields alone are not authenticated capability evidence."""
    report = _doctor(tmp_path, projection_permissions=())
    assert _outcome(report, "work_management") == "FAIL"


def test_doctor_rejects_workspace_root_that_is_not_a_directory(tmp_path: Path) -> None:
    """Removing the is-a-directory guard must make this fail.

    The file is writable and executable on purpose: a merely absent path would
    also be caught by the writability probe, which would mask this guard.
    """
    not_a_directory = tmp_path / "workspace-root-file"
    not_a_directory.write_text("", encoding="utf-8")
    not_a_directory.chmod(0o777)
    assert os.access(not_a_directory, os.W_OK | os.X_OK)

    report = _doctor(tmp_path, execution_overrides={"workspace_root": not_a_directory})

    assert _outcome(report, "execution") == "FAIL"


@pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses filesystem write permission")
def test_doctor_rejects_workspace_root_that_is_not_writable(tmp_path: Path) -> None:
    """Removing the writability probe must make this fail."""
    unwritable = tmp_path / "read-only-root"
    unwritable.mkdir()
    unwritable.chmod(0o555)
    try:
        assert not os.access(unwritable, os.W_OK)
        report = _doctor(tmp_path, execution_overrides={"workspace_root": unwritable})
    finally:
        unwritable.chmod(0o755)

    assert _outcome(report, "execution") == "FAIL"


def test_doctor_rejects_execution_without_a_workspace_manager(tmp_path: Path) -> None:
    """Removing the workspace-manager guard must make this fail."""
    report = _doctor(tmp_path, execution_overrides={"workspace_manager": object()})
    assert _outcome(report, "execution") == "FAIL"


def test_doctor_rejects_unreadable_git_worktree_inventory(tmp_path: Path) -> None:
    """A directory Git does not manage yields no inventory, so worktree creation is unevidenced."""
    from alienintent.composition.doctor_probes import git_worktree_inventory

    not_a_repository = tmp_path / "plain-directory"
    not_a_repository.mkdir()
    assert git_worktree_inventory(not_a_repository) == ()

    report = _doctor(tmp_path, execution_overrides={"git_worktrees": git_worktree_inventory(not_a_repository)})

    assert _outcome(report, "execution") == "FAIL"


def test_doctor_rejects_worker_provider_that_cannot_enforce_cancellation(tmp_path: Path) -> None:
    """Process control is negotiated capability; removing that guard must make this fail."""
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider

    worker = CliWorkerProvider("codex", sys.executable, (), "explicit", frozenset({"wall-clock", "attempts"}))

    report = _doctor(tmp_path, execution_overrides={"worker_capabilities": worker.capabilities})

    assert _outcome(report, "execution") == "FAIL"


def test_doctor_rejects_absent_worker_executable(tmp_path: Path) -> None:
    """Removing the executable guard must make this fail: no binary, no process control."""
    report = _doctor(tmp_path, execution_overrides={"worker_executable": None})
    assert _outcome(report, "execution") == "FAIL"


def test_profile_rejects_a_blank_namespace_at_construction() -> None:
    """Where `_configuration`'s namespace rule actually lives.

    Doctor evidences typed validity; the type enforces the namespace rules, so
    an unreachable re-check inside doctor would be decoration no test can kill.
    """
    from alienintent.installation.domain.github_profile import GitHubProfile, ProfileRejected

    with pytest.raises(ProfileRejected):
        GitHubProfile("", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook-secret", True)
    with pytest.raises(ProfileRejected):
        GitHubProfile("isolated", "AlienLogicLab/alienintent", "", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook-secret", True)


def test_profile_rejects_an_unknown_field() -> None:
    """Scope 2: the profile rejects unknown/invalid fields."""
    from alienintent.installation.domain.github_profile import GitHubProfile

    with pytest.raises(TypeError):
        GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook-secret", True, unknown_field="x")  # type: ignore[call-arg]


def test_doctor_rejects_a_profile_that_is_not_typed_valid(tmp_path: Path) -> None:
    """Removing the typed-validity guard must make this fail."""
    from alienintent.installation.application.doctor import DoctorDependencies, InstallationDoctor

    dependencies = DoctorDependencies(
        object(), _NullSecrets(), lambda: True, lambda: True, lambda: True,
        lambda: True, lambda: True, lambda: True,
    )

    report = InstallationDoctor(dependencies).run()

    assert _outcome(report, "configuration") == "FAIL"


class _NullSecrets:
    def resolve(self, reference: str) -> bytes:
        raise RuntimeError("no secret provider is configured")

    def diagnostic(self) -> str:
        return "unconfigured"


def _doctor(
    tmp_path: Path,
    *,
    work_rows: tuple[dict[str, object], ...] | None = None,
    lifecycle_statuses: dict[str, str] | None = None,
    source_control: dict[str, object] | None = None,
    provider: dict[str, object] | None = None,
    webhook: dict[str, object] | None = None,
    secret: bytes = b"usable",
    secret_diagnostic: str | None = None,
    projection_permissions: tuple[str, ...] = ("VERIFY",),
    persistence_database: Path | None = None,
    execution_overrides: dict[str, object] | None = None,
) -> object:
    from alienintent.installation.application.doctor import InstallationDoctor
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore

    database = persistence_database
    if database is None:
        database = tmp_path / "state.db"
        SQLiteOperationalStore(database)
    profile = _profile()
    execution = _real_execution_evidence(tmp_path)
    execution.update(execution_overrides or {})
    return InstallationDoctor(_dependencies(
        profile=profile,
        secret=secret,
        secret_diagnostic=secret_diagnostic,
        work_rows=work_rows or ({"repository": "AlienLogicLab/alienintent", "status": "Ready", "priority": "P0", "dependencies": []},),
        lifecycle_statuses=lifecycle_statuses or {"Ready": "READY"},
        projection_permissions=projection_permissions,
        source_control=source_control or {"repository": "AlienLogicLab/alienintent", "baseline": "a" * 40, "publication_permissions": ("contents:write",)},
        provider=provider or _provider_evidence(),
        webhook=webhook or _webhook_fixture(b"usable"),
        persistence_preflight=lambda: _preflight(database),
        execution=execution,
    )).run()


def _profile():
    from alienintent.installation.domain.github_profile import GitHubProfile

    return GitHubProfile("isolated", "AlienLogicLab/alienintent", "PVT_x", {"Ready": "READY"}, {"VERIFY": "Status"}, "webhook-secret", True)


def _provider_evidence(*, capabilities: tuple[str, ...] = ("wall-clock", "attempts", "retries", "concurrency", "cancellation"), authenticated: bool = True) -> dict[str, object]:
    return {"name": "worker", "version": "1", "capabilities": capabilities, "authenticated": authenticated}


def _real_execution_evidence(tmp_path: Path) -> dict[str, object]:
    """Drive the shipped worktree and worker adapters; nothing here allocates or starts."""
    from alienintent.composition.doctor_probes import execution_evidence
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider

    repository = tmp_path / "repository"
    repository.mkdir(exist_ok=True)
    if not (repository / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=repository, check=True, capture_output=True)
    workspace_root = tmp_path / "workspaces"
    workspace_root.mkdir(exist_ok=True)
    worker = CliWorkerProvider("codex", sys.executable, (), "explicit", frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"}))
    return execution_evidence(repository, workspace_root, worker, sys.executable)


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

    secret = values["secret"]
    profile = values["profile"]
    diagnostic = values["secret_diagnostic"]
    if diagnostic is None:
        diagnostic = f"protected-local-file references={profile.webhook_secret_reference}"

    class Secrets:
        def resolve(self, reference: str) -> bytes:
            assert isinstance(secret, bytes)
            return secret

        def diagnostic(self) -> str:
            assert isinstance(diagnostic, str)
            return diagnostic

    return DoctorDependencies(
        profile, Secrets(),
        lambda: {"rows": values["work_rows"], "lifecycle_statuses": values["lifecycle_statuses"], "projection_permissions": values["projection_permissions"]},
        lambda: values["source_control"], lambda: values["provider"], lambda: values["webhook"],
        lambda: {"preflight": values["persistence_preflight"]}, lambda: values["execution"],
    )
