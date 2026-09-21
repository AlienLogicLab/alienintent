"""The sandbox profile composition and the live doctor probes it supplies.

The composition under test is the one the live checks drive; only the GitHub
transport and the worker executable are recorded, so the wiring exercised here
is the wiring that runs against the sandbox.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.composition.doctor_probes import (
    live_provider_evidence,
    live_source_control_evidence,
    live_transport_evidence,
    live_work_management_evidence,
)
from alienintent.composition.sandbox_profile import (
    APP_KEY_REFERENCE,
    SandboxProfileComposition,
    compose_identity,
    compose_profile,
    compose_secrets,
    load_profile_document,
)
from alienintent.execution_coordination.adapters.github_webhook import RESIDENT_INGRESS_MARKER, serve_webhook
from alienintent.installation.application.doctor import DoctorFailure, DoctorUnavailable
from alienintent.installation.domain.app_credentials import CredentialRejected
from alienintent.installation.domain.github_profile import ProfileRejected
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from tests.execution_coordination.test_github_work_management import contract
from tests.support.disposable_rsa import disposable_private_key
from tests.support.live_github import (
    FOREIGN_PROJECT,
    LEAST_PRIVILEGE,
    PRIORITY_FIELD,
    SANDBOX_PROJECT,
    SANDBOX_REPOSITORY,
    STATUS_FIELD,
    RecordedTransport,
    project_graphql,
    rest_answers,
)

DIMENSIONS = frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"})


def document(tmp_path: Path, **overrides) -> dict:
    key, secret = tmp_path / "key.pem", tmp_path / "webhook"
    key.write_bytes(disposable_private_key())
    secret.write_text("sandbox-webhook-secret")
    base = {
        "profile": "py10-sandbox",
        "repository": SANDBOX_REPOSITORY,
        "project_reference": SANDBOX_PROJECT,
        "project_number": 2,
        "project_status_field": STATUS_FIELD,
        "project_priority_field": PRIORITY_FIELD,
        "lifecycle_statuses": {"READY": "READY"},
        "projection_fields": {"IMPLEMENT": "Status", "VERIFY": "Status", "REVIEW": "Status", "ACCEPT": "Status", "DONE": "Status"},
        "webhook_secret_reference": "py10-sandbox-webhook",
        "automatic_release": True,
        "webhook": {"listen_address": "127.0.0.1", "listen_port": 0, "public_url": "https://example.invalid/"},
        "secret_references": {"py10-sandbox-webhook": str(secret)},
        "githubApp": {"applicationId": 1000001, "installationId": 2000002, "privateKeyPath": str(key)},
    }
    base.update(overrides)
    return base


def composition(tmp_path: Path, *, transport: RecordedTransport | None = None, **overrides) -> SandboxProfileComposition:
    recorded = transport or RecordedTransport(rest_answers(), project_graphql())
    return SandboxProfileComposition(document(tmp_path, **overrides), tmp_path / "state.sqlite", contract(), lambda _: None, recorded, lambda: 1758445000.0)


# --- AC 8: the profile composition loads and binds every capability ----------


def test_the_composition_binds_every_capability_from_the_recorded_identities(tmp_path: Path) -> None:
    composed = composition(tmp_path)

    assert composed.profile.profile == "py10-sandbox"
    assert composed.identity == compose_identity(document(tmp_path))
    assert composed.address.project_id == SANDBOX_PROJECT
    assert composed.credentials.token().value
    assert composed.repository.metadata()["full_name"] == SANDBOX_REPOSITORY
    assert composed.work.resolve_project().status_options["VERIFY"] == "64fca347"
    assert composed.ingress is not None
    assert composed.store.path.exists()


def test_the_profile_carries_the_recorded_bind_address_port_and_secret_reference(tmp_path: Path) -> None:
    profile = compose_profile(document(tmp_path, webhook={"listen_address": "127.0.0.1", "listen_port": 8789, "public_url": "https://example.invalid/"}))

    assert (profile.webhook_listen_address, profile.webhook_listen_port) == ("127.0.0.1", 8789)
    assert profile.webhook_secret_reference == "py10-sandbox-webhook"
    assert profile.webhook_public_url == "https://example.invalid/"


def test_a_bind_port_outside_the_addressable_range_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ProfileRejected):
        compose_profile(document(tmp_path, webhook={"listen_address": "127.0.0.1", "listen_port": 70000, "public_url": ""}))


def test_the_app_private_key_resolves_through_the_secret_provider_by_reference(tmp_path: Path) -> None:
    """Binding rule 3: credentials are referenced, never embedded."""
    secrets = compose_secrets(document(tmp_path))

    assert secrets.resolve(APP_KEY_REFERENCE).startswith(b"-----BEGIN RSA PRIVATE KEY-----")
    assert "BEGIN RSA PRIVATE KEY" not in secrets.diagnostic()
    assert APP_KEY_REFERENCE in secrets.diagnostic()


def test_a_profile_recording_no_private_key_reference_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(CredentialRejected):
        compose_secrets(document(tmp_path, githubApp={"applicationId": 1, "installationId": 2}))


def test_a_profile_document_round_trips_from_disk(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(document(tmp_path)))

    assert compose_profile(load_profile_document(path)).project_reference == SANDBOX_PROJECT


def test_the_resident_ingress_serves_the_address_the_profile_records(tmp_path: Path) -> None:
    from urllib.request import urlopen

    with composition(tmp_path).resident_ingress() as route:
        assert route.startswith("http://127.0.0.1:")
        assert urlopen(route.removesuffix("/webhook")).read() == RESIDENT_INGRESS_MARKER


# --- AC 10: isolation evidence, at the layer each control operates -----------


def test_isolation_reports_nothing_when_scope_and_addressing_are_correct(tmp_path: Path) -> None:
    assert composition(tmp_path).isolation_findings() == ()


def test_a_configuration_naming_another_project_is_reported(tmp_path: Path) -> None:
    """AC 10b: no Project identity other than the configured one may appear."""
    composed = composition(tmp_path, notes={"seen_elsewhere": FOREIGN_PROJECT})

    assert f"configuration names project {FOREIGN_PROJECT}" in composed.isolation_findings()


def test_an_installation_scoped_beyond_the_sandbox_repository_is_reported(tmp_path: Path) -> None:
    """AC 10a: the repository boundary is judged on what GitHub grants."""
    transport = RecordedTransport(rest_answers(repositories=[SANDBOX_REPOSITORY, "AlienLogicLab/elsewhere"]), project_graphql())

    findings = composition(tmp_path, transport=transport).isolation_findings()
    assert "installation scope includes AlienLogicLab/elsewhere" in findings


def test_an_installation_granted_all_repositories_is_reported(tmp_path: Path) -> None:
    transport = RecordedTransport(rest_answers(repository_selection="all"), project_graphql())

    findings = composition(tmp_path, transport=transport).isolation_findings()
    assert "installation repository_selection is 'all', required 'selected'" in findings


# --- AC 9: each live probe has a passing and a failing case ------------------


def test_the_work_management_probe_reports_projection_capability_from_the_real_grant(tmp_path: Path) -> None:
    composed = composition(tmp_path)

    evidence = live_work_management_evidence(composed.work, composed.profile, LEAST_PRIVILEGE)
    assert "VERIFY" in evidence["projection_permissions"]
    assert evidence["project"] == SANDBOX_PROJECT


def test_the_work_management_probe_cannot_claim_projection_without_the_grant(tmp_path: Path) -> None:
    """No probe passes on an adapter-declared flag: the grant is GitHub's answer."""
    composed = composition(tmp_path)
    granted = {name: level for name, level in LEAST_PRIVILEGE.items() if name != "organization_projects"}

    assert live_work_management_evidence(composed.work, composed.profile, granted)["projection_permissions"] == ()


def test_the_source_control_probe_reads_the_baseline_and_the_publication_grant(tmp_path: Path) -> None:
    composed = composition(tmp_path)
    remote = _local_remote(tmp_path)

    evidence = live_source_control_evidence(composed.repository, LEAST_PRIVILEGE, remote)
    assert evidence["repository"] == SANDBOX_REPOSITORY
    assert len(evidence["baseline"]) == 40
    assert evidence["publication_permissions"] == ("contents:write",)


def test_the_source_control_probe_reports_a_read_only_contents_grant_as_such(tmp_path: Path) -> None:
    composed = composition(tmp_path)

    evidence = live_source_control_evidence(composed.repository, LEAST_PRIVILEGE | {"contents": "read"}, _local_remote(tmp_path))
    assert evidence["publication_permissions"] == ("contents:read",)


def test_the_source_control_probe_is_unavailable_when_the_baseline_cannot_be_read(tmp_path: Path) -> None:
    composed = composition(tmp_path)

    with pytest.raises(DoctorUnavailable):
        live_source_control_evidence(composed.repository, LEAST_PRIVILEGE, str(tmp_path / "absent.git"))


def test_the_provider_probe_establishes_the_provider_by_running_its_version_probe() -> None:
    worker = CliWorkerProvider("codex", sys.executable, (), "explicit", DIMENSIONS)

    evidence = live_provider_evidence(worker, sys.executable)
    assert evidence["authenticated"] is True
    assert evidence["version"]
    assert set(evidence["capabilities"]) == DIMENSIONS


def test_the_provider_probe_fails_when_the_executable_cannot_be_resolved() -> None:
    worker = CliWorkerProvider("codex", sys.executable, (), "explicit", DIMENSIONS)

    with pytest.raises(DoctorFailure):
        live_provider_evidence(worker, "alienintent-provider-that-does-not-exist")


def test_the_transport_probe_passes_only_when_the_route_reaches_this_ingress(tmp_path: Path) -> None:
    composed = composition(tmp_path)

    with serve_webhook(composed.ingress, "127.0.0.1", 0) as route:
        profile = compose_profile(document(tmp_path, webhook={
            "listen_address": "127.0.0.1", "listen_port": 0, "public_url": route.removesuffix("/webhook"),
        }))
        evidence = live_transport_evidence(profile, composed.secrets)

    assert evidence["route"].startswith("http://127.0.0.1:")
    assert evidence["signature"].startswith("sha256=")


def test_the_transport_probe_fails_when_the_route_answers_from_another_origin(tmp_path: Path) -> None:
    """Removing the resident marker check must make this fail: any origin would pass."""
    composed = composition(tmp_path)
    with _foreign_origin() as route:
        profile = compose_profile(document(tmp_path, webhook={"listen_address": "127.0.0.1", "listen_port": 0, "public_url": route}))
        with pytest.raises(DoctorFailure):
            live_transport_evidence(profile, composed.secrets)


def test_the_transport_probe_is_unavailable_when_the_route_cannot_be_reached(tmp_path: Path) -> None:
    composed = composition(tmp_path)
    profile = compose_profile(document(tmp_path, webhook={"listen_address": "127.0.0.1", "listen_port": 0, "public_url": "http://127.0.0.1:1/"}))

    with pytest.raises(DoctorUnavailable):
        live_transport_evidence(profile, composed.secrets)


def test_the_transport_probe_requires_a_recorded_public_route(tmp_path: Path) -> None:
    composed = composition(tmp_path)
    profile = compose_profile(document(tmp_path, webhook={"listen_address": "127.0.0.1", "listen_port": 0, "public_url": ""}))

    with pytest.raises(DoctorFailure):
        live_transport_evidence(profile, composed.secrets)


# --- AC 11: the credentialed remote never becomes evidence -------------------


def test_the_authenticated_remote_is_never_the_form_that_reaches_evidence(tmp_path: Path) -> None:
    from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl

    remote = composition(tmp_path).authenticated_remote()

    assert "x-access-token:" in remote
    assert "x-access-token" not in GitSourceControl._evidence_remote(remote)
    assert GitSourceControl._evidence_remote(remote).startswith("https://github.com/")


def _local_remote(tmp_path: Path) -> str:
    origin = tmp_path / "origin"
    origin.mkdir()
    subprocess.run(["git", "init", "-q", "--initial-branch=main"], cwd=origin, check=True)
    (origin / "README").write_text("baseline")
    subprocess.run(["git", "add", "README"], cwd=origin, check=True)
    subprocess.run(
        ["git", "-c", "user.email=probe@invalid", "-c", "user.name=probe", "commit", "-qm", "baseline"],
        cwd=origin, check=True,
    )
    return str(origin)


def _foreign_origin():
    from contextlib import contextmanager
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"some other origin")

        def log_message(self, format: str, *args: object) -> None:
            pass

    @contextmanager
    def serve():
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/"
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    return serve()
