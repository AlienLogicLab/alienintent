"""Recorded-fixture contract tests for the PY-05 GitHub ACL and ingress."""

from __future__ import annotations

from hashlib import sha256
import hmac
import json
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.contract import BudgetPolicy, BiuContract


def contract() -> BiuContract:
    return BiuContract(
        identity="PY-05", version="1", intent="fixture", satisfied_requirement_ids=("SF-REQ-005",),
        fixed_decisions=("FD-01",), authorized_scope=("adapter",), excluded_scope=("live",), dependencies=(),
        required_capabilities=("python",), budget_policy=BudgetPolicy(), retry_policy="none",
        completion_criteria=("tests",), verification_obligations=("fixtures",), required_evidence=("evidence",),
        non_goals=("live",), candidate_custody_requirements=("branch",), release_policy="automatic",
        authority_issuer="founder", authority_references=("issue-53",), target_repositories=("AlienLogicLab/alienintent",),
        baselines=("3e57749",), required_closure_actions=("merge",), stop_escalation_conditions=("ambiguity",),
    )


def item(identity: str = "PY-05", *, priority: str | None = "P1", status: str = "READY", dependencies: tuple[str, ...] = (), complete: bool = True, membership: bool = True) -> dict[str, object]:
    return {
        "identity": identity, "repository": "AlienLogicLab/alienintent", "membership": membership, "complete": complete,
        "status": status, "priority": priority, "wave": "1", "dependencies": list(dependencies),
        "contract": "docs/work-units/python/PY-05.md", "contract_digest": "sha256:contract",
        "readiness": "READY", "source_version": "v1", "observed_at": "2026-09-20T00:00:00Z",
    }


def adapter(items: list[dict[str, object]], projection=lambda identity, field, state, revision: revision):
    from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
    return GitHubProjectsWorkManagement("alpha", "AlienLogicLab/alienintent", {"READY": "READY"}, {"IMPLEMENT": "Execution"}, lambda: tuple(items), contract(), projection)


def test_import_maps_priority_dependencies_and_keeps_wave_as_metadata() -> None:
    imported = adapter([item(dependencies=("PY-04",)), item("PY-06", priority=None)]).import_ready_snapshot()

    assert imported[0].priority == 1
    assert imported[0].dependencies == ("PY-04",)
    assert imported[0].metadata["wave"] == "1"
    assert imported[1].priority is None


@pytest.mark.parametrize("bad", [item(status="MYSTERY"), item(complete=False), item(membership=False)])
def test_ambiguous_status_missing_membership_and_incomplete_pages_fail_closed(bad: dict[str, object]) -> None:
    from alienintent.execution_coordination.ports.work_management import WorkRejected
    with pytest.raises(WorkRejected):
        adapter([bad]).import_ready_snapshot()


def test_complete_board_allows_many_to_one_non_ready_status_mappings() -> None:
    from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
    work = GitHubProjectsWorkManagement(
        "alpha",
        "AlienLogicLab/alienintent",
        {"READY": "READY", "In progress": "NOT_READY", "Backlog": "NOT_READY"},
        {"IMPLEMENT": "Execution"},
        lambda: (item(), item("PY-06", status="In progress"), item("PY-07", status="Backlog")),
        contract(),
    )

    assert [ready.identity for ready in work.import_ready_snapshot()] == ["PY-05"]


def test_stale_projection_never_overwrites_newer_revision_and_unavailable_is_visible() -> None:
    updates: list[tuple[str, str, int]] = []
    def write(identity: str, field: str, state: str, revision: int) -> int:
        updates.append((state, field, revision))
        return revision
    work = adapter([item()], write)

    assert work.project_execution_state("PY-05", "IMPLEMENT", 2).confirmed
    stale = work.project_execution_state("PY-05", "IMPLEMENT", 1)
    assert not stale.confirmed
    assert stale.detail == "stale projection fenced"
    assert updates == [("IMPLEMENT", "Execution", 2)]


def test_unavailable_projection_provider_preserves_the_unconfirmed_delivery_outcome() -> None:
    receipt = adapter([item()], None).project_execution_state("PY-05", "IMPLEMENT", 7)

    assert not receipt.confirmed
    assert receipt.revision == 7
    assert receipt.detail == "projection provider unavailable"


def test_projection_requires_provider_readback_of_the_requested_revision() -> None:
    work = adapter([item()], lambda identity, field, state, revision: revision - 1)
    receipt = work.project_execution_state("PY-05", "IMPLEMENT", 2)
    assert not receipt.confirmed
    assert receipt.detail == "projection read-back mismatch"


def test_webhook_verifies_raw_body_and_deduplicates_before_domain_notification(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    from alienintent.execution_coordination.ports.event_ingress import IngressRejected
    store = SQLiteOperationalStore(tmp_path / "inbox.sqlite")
    notifications: list[str] = []
    ingress = GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", b"sentinel-secret", store, notifications.append)
    body = json.dumps({"action": "edited", "project_item": {"id": "PY-05"}, "repository": {"full_name": "AlienLogicLab/alienintent"}}).encode()
    signature = "sha256=" + hmac.new(b"sentinel-secret", body, sha256).hexdigest()

    first = ingress.receive("delivery-1", "projects_v2_item", signature, body)
    duplicate = ingress.receive("delivery-1", "projects_v2_item", signature, body)
    assert first == duplicate
    assert notifications == ["upstream-product-change:PY-05"]
    with pytest.raises(IngressRejected):
        ingress.receive("delivery-2", "projects_v2_item", "sha256=forged", body)
    with pytest.raises(IngressRejected):
        ingress.receive("delivery-3", "projects_v2_item", signature, body + b" ")


def test_duplicate_returns_the_durably_recorded_prior_receipt_not_a_constant(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    store = SQLiteOperationalStore(tmp_path / "inbox.sqlite")
    ingress = GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", b"secret", store, lambda _: None)

    def signed(version: int) -> tuple[bytes, str]:
        body = json.dumps({"project_item": {"id": "PY-05", "version": version}, "repository": {"full_name": "AlienLogicLab/alienintent"}}).encode()
        return body, "sha256=" + hmac.new(b"secret", body, sha256).hexdigest()

    first_body, first_signature = signed(1)
    ingress.receive("delivery-1", "projects_v2_item", first_signature, first_body)
    second_body, second_signature = signed(2)
    ingress.receive("delivery-2", "projects_v2_item", second_signature, second_body)

    duplicate = ingress.receive("delivery-1", "projects_v2_item", first_signature, first_body)

    assert duplicate.detail == "applied:1"


def test_unknown_event_category_is_rejected_before_durable_admission(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    from alienintent.execution_coordination.ports.event_ingress import IngressRejected
    body = b'{"project_item":{"id":"PY-05"},"repository":{"full_name":"AlienLogicLab/alienintent"}}'
    signature = "sha256=" + hmac.new(b"secret", body, sha256).hexdigest()

    with pytest.raises(IngressRejected, match="unsupported event category"):
        GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", b"secret", SQLiteOperationalStore(tmp_path / "inbox.sqlite"), lambda _: None).receive("unknown-1", "pull_request", signature, body)


def test_foreign_repository_event_is_rejected_instead_of_being_routed_to_the_profile(tmp_path: Path) -> None:
    from alienintent.composition.github_profile import GitHubProfileComposition
    from alienintent.execution_coordination.ports.event_ingress import IngressRejected
    from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
    from alienintent.installation.domain.github_profile import GitHubProfile
    secret = tmp_path / "webhook"
    secret.write_text("sentinel-secret")
    profile = GitHubProfile("alpha", "AlienLogicLab/alienintent", "PVT_1", {"READY": "READY"}, {"IMPLEMENT": "Execution"}, "webhook", automatic_release=True)
    composed = GitHubProfileComposition(profile, ProtectedLocalFileSecretProvider({"webhook": secret}), tmp_path / "state.sqlite", lambda: (item(),), contract(), lambda _: None)
    body = b'{"project_item":{"id":"PY-05"},"repository":{"full_name":"foreign/repository"}}'
    signature = "sha256=" + hmac.new(b"sentinel-secret", body, sha256).hexdigest()

    with pytest.raises(IngressRejected, match="ambiguous profile"):
        composed.ingress.receive("foreign-1", "projects_v2_item", signature, body)


def test_redelivery_replays_a_receipted_notification_after_interruption(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    calls: list[str] = []
    def interrupted(notification: str) -> None:
        calls.append(notification)
        if len(calls) == 1:
            raise RuntimeError("simulated crash before internal delivery")
    ingress = GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", b"secret", SQLiteOperationalStore(tmp_path / "inbox.sqlite"), interrupted)
    body = b'{"project_item":{"id":"PY-05"},"repository":{"full_name":"AlienLogicLab/alienintent"}}'
    signature = "sha256=" + hmac.new(b"secret", body, sha256).hexdigest()
    with pytest.raises(RuntimeError):
        ingress.receive("delivery-1", "projects_v2_item", signature, body)
    ingress.receive("delivery-1", "projects_v2_item", signature, body)
    assert calls == ["upstream-product-change:PY-05", "upstream-product-change:PY-05"]


def test_reordered_event_is_held_without_a_second_domain_change(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    from alienintent.execution_coordination.ports.event_ingress import IngressRejected
    store = SQLiteOperationalStore(tmp_path / "inbox.sqlite")
    ingress = GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", b"secret", store, lambda _: None)
    def signed(event: str, version: int) -> tuple[bytes, str]:
        body = json.dumps({"project_item": {"id": "PY-05", "version": version}, "repository": {"full_name": "AlienLogicLab/alienintent"}}).encode()
        return body, "sha256=" + hmac.new(b"secret", body, sha256).hexdigest()
    body, signature = signed("new", 2)
    ingress.receive("new", "projects_v2_item", signature, body)
    body, signature = signed("old", 1)
    with pytest.raises(IngressRejected, match="stale"):
        ingress.receive("old", "projects_v2_item", signature, body)


def test_external_execution_display_edit_is_drift_not_a_lifecycle_command(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress
    observed: list[str] = []
    ingress = GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", b"secret", SQLiteOperationalStore(tmp_path / "inbox.sqlite"), observed.append)
    body = json.dumps({"project_item": {"id": "PY-05"}, "repository": {"full_name": "AlienLogicLab/alienintent"}, "execution_field_edit": True}).encode()
    signature = "sha256=" + hmac.new(b"secret", body, sha256).hexdigest()
    ingress.receive("drift-1", "projects_v2_item", signature, body)
    assert observed == ["downstream-drift:PY-05"]


def test_secret_config_redacts_sentinel_and_local_server_returns_real_hmac_status(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_webhook import GitHubWebhookIngress, serve_webhook
    from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
    secret_path = tmp_path / "secret"
    secret_path.write_text("sentinel-secret")
    provider = ProtectedLocalFileSecretProvider({"webhook": secret_path})
    assert "sentinel-secret" not in provider.diagnostic()
    ingress = GitHubWebhookIngress("alpha", "AlienLogicLab/alienintent", provider.resolve("webhook"), SQLiteOperationalStore(tmp_path / "inbox.sqlite"), lambda _: None)
    with serve_webhook(ingress) as url:
        body = b'{"project_item":{"id":"PY-05"},"repository":{"full_name":"AlienLogicLab/alienintent"}}'
        sig = "sha256=" + hmac.new(b"sentinel-secret", body, sha256).hexdigest()
        request = Request(url, data=body, method="POST", headers={"X-GitHub-Delivery": "http-1", "X-GitHub-Event": "projects_v2_item", "X-Hub-Signature-256": sig})
        assert urlopen(request).status == 202


def test_typed_github_profile_rejects_execution_display_as_a_release_mapping(tmp_path: Path) -> None:
    from alienintent.installation.domain.github_profile import GitHubProfile, ProfileRejected
    valid = GitHubProfile("alpha", "AlienLogicLab/alienintent", "PVT_1", {"READY": "READY"}, {"IMPLEMENT": "Execution"}, "webhook", automatic_release=True)
    assert valid.profile == "alpha"
    with pytest.raises(ProfileRejected):
        GitHubProfile("alpha", "AlienLogicLab/alienintent", "PVT_1", {"IMPLEMENT": "READY"}, {"IMPLEMENT": "Execution"}, "webhook", automatic_release=True)


def test_github_composition_wires_profile_secret_store_and_acl_without_live_api(tmp_path: Path) -> None:
    from alienintent.composition.github_profile import GitHubProfileComposition
    from alienintent.installation.domain.github_profile import GitHubProfile
    from alienintent.installation.adapters.protected_local_file_secret import ProtectedLocalFileSecretProvider
    secret = tmp_path / "webhook"
    secret.write_text("sentinel-secret")
    profile = GitHubProfile("alpha", "AlienLogicLab/alienintent", "PVT_1", {"READY": "READY"}, {"IMPLEMENT": "Execution"}, "webhook", automatic_release=True)
    composed = GitHubProfileComposition(profile, ProtectedLocalFileSecretProvider({"webhook": secret}), tmp_path / "state.sqlite", lambda: (item(),), contract(), lambda _: None)
    assert composed.work.import_ready_snapshot()[0].identity == "PY-05"


def test_github_imported_unsatisfied_dependency_is_ineligible_to_the_factory(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
    from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator, StopReason
    from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
    work = GitHubProjectsWorkManagement(
        "alpha", "AlienLogicLab/alienintent", {"READY": "READY"}, {"IMPLEMENT": "Execution"},
        lambda: (item(dependencies=("PY-04",)),), contract(),
    )

    summary = FactoryCoordinator(
        SQLiteOperationalStore(tmp_path / "state.sqlite"), work, object(),
        LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier"), "alpha",
    ).start()

    assert summary.stop_reason is StopReason.BLOCKED
    assert summary.dispatched == ()


def test_startup_reconcile_does_not_readmit_a_completed_github_snapshot_item(tmp_path: Path) -> None:
    from alienintent.execution_coordination.adapters.github_work_management import GitHubProjectsWorkManagement
    from alienintent.execution_coordination.application.factory_coordinator import FactoryCoordinator
    from alienintent.execution_coordination.application.local_artifact_custody import LocalArtifactStore
    from alienintent.execution_coordination.domain.lifecycle import ExecutionState, LifecycleStage
    work = GitHubProjectsWorkManagement(
        "alpha", "AlienLogicLab/alienintent", {"READY": "READY"}, {"IMPLEMENT": "Execution"},
        lambda: (item(),), contract(),
    )
    store = SQLiteOperationalStore(tmp_path / "state.sqlite")
    done = ExecutionState(LifecycleStage.DONE, 4, accepted=True, completed_closure_actions=frozenset({"merge"}), contract=contract())
    store.commit("alpha", "factory:PY-05", 0, FactoryCoordinator._encode(done) | {"outcome": "success"})

    class NoDuplicateWorker:
        def start(self, *args):
            raise AssertionError("completed item must not be admitted again")

        def read_back(self, *args):
            raise AssertionError("completed item has no recovery reservation")

    summary = FactoryCoordinator(store, work, NoDuplicateWorker(), LocalArtifactStore(tmp_path / "producer", tmp_path / "verifier"), "alpha").start()

    assert summary.dispatched == ()
