"""Live GitHub delivery admission: authenticated, at most once, fail-closed.

The payload shapes here are the ones GitHub actually sends. A
`projects_v2_item` delivery names no repository, so the configured Project
identity is the only boundary it can be admitted against — which is exactly
the configuration-enforced control SWF-34 requires.
"""

from __future__ import annotations

from hashlib import sha256
import hmac
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from alienintent.execution_coordination.adapters.github_webhook import (
    RESIDENT_INGRESS_MARKER,
    GitHubWebhookIngress,
    serve_webhook,
)
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.github_delivery import DeliveryRejected, delivery_reference
from alienintent.execution_coordination.ports.event_ingress import IngressRejected
from tests.support.live_github import FOREIGN_PROJECT, SANDBOX_PROJECT, SANDBOX_REPOSITORY

SECRET = b"sandbox-webhook-secret"


def ingress(tmp_path: Path, notifications: list[str], project: str | None = SANDBOX_PROJECT) -> GitHubWebhookIngress:
    return GitHubWebhookIngress(
        "py10-sandbox", SANDBOX_REPOSITORY, SECRET,
        SQLiteOperationalStore(tmp_path / "inbox.sqlite"), notifications.append, project_reference=project,
    )


def signed(payload: dict) -> tuple[bytes, str]:
    body = json.dumps(payload).encode()
    return body, "sha256=" + hmac.new(SECRET, body, sha256).hexdigest()


def projects_v2_item(project: str = SANDBOX_PROJECT, content: str = "I_kwDOsandbox") -> dict:
    return {
        "action": "edited",
        "projects_v2_item": {
            "id": 251196014, "node_id": "PVTI_lADOsandbox", "project_node_id": project,
            "content_node_id": content, "content_type": "Issue",
        },
        "organization": {"login": "AlienLogicLab"},
        "installation": {"id": 2000002},
    }


def issue_comment(repository: str = SANDBOX_REPOSITORY) -> dict:
    return {
        "action": "created",
        "issue": {"number": 1, "node_id": "I_kwDOsandbox"},
        "comment": {"id": 1, "body": "sandbox probe"},
        "repository": {"full_name": repository},
        "installation": {"id": 2000002},
    }


# --- AC 7: a real delivery is admitted exactly once --------------------------


def test_a_live_projects_v2_item_delivery_is_admitted_exactly_once(tmp_path: Path) -> None:
    notifications: list[str] = []
    resident = ingress(tmp_path, notifications)
    body, signature = signed(projects_v2_item())

    first = resident.receive("delivery-1", "projects_v2_item", signature, body)
    replayed = resident.receive("delivery-1", "projects_v2_item", signature, body)

    assert first.accepted
    assert first == replayed
    assert notifications == ["upstream-product-change:I_kwDOsandbox"]


def test_a_live_issue_comment_delivery_is_admitted_against_the_repository(tmp_path: Path) -> None:
    notifications: list[str] = []
    body, signature = signed(issue_comment())

    receipt = ingress(tmp_path, notifications).receive("delivery-2", "issue_comment", signature, body)

    assert receipt.accepted
    assert notifications == ["upstream-product-change:I_kwDOsandbox"]


@pytest.mark.parametrize("authenticity", ["", "sha256=" + "0" * 64, "sha1=deadbeef"])
def test_an_unsigned_or_wrongly_signed_delivery_is_never_admitted(tmp_path: Path, authenticity: str) -> None:
    body, _ = signed(projects_v2_item())

    with pytest.raises(IngressRejected, match="invalid raw-body signature"):
        ingress(tmp_path, []).receive("delivery-3", "projects_v2_item", authenticity, body)


def test_a_delivery_signed_with_a_different_secret_is_rejected(tmp_path: Path) -> None:
    """AC 7 wrong-secret case, proven red: removing the check admits a forged delivery."""
    body = json.dumps(projects_v2_item()).encode()
    wrong = "sha256=" + hmac.new(b"some-other-secret", body, sha256).hexdigest()

    with pytest.raises(IngressRejected):
        ingress(tmp_path, []).receive("delivery-4", "projects_v2_item", wrong, body)


def test_a_body_altered_after_signing_is_rejected_on_the_raw_bytes(tmp_path: Path) -> None:
    body, signature = signed(projects_v2_item())

    with pytest.raises(IngressRejected):
        ingress(tmp_path, []).receive("delivery-5", "projects_v2_item", signature, body + b" ")


# --- AC 10b: fail-closed Project addressing at the ingress -------------------


def test_a_delivery_for_another_project_is_refused_even_though_the_token_could_reach_it(tmp_path: Path) -> None:
    """The organization-scoped grant makes this delivery reachable; configuration refuses it."""
    notifications: list[str] = []
    body, signature = signed(projects_v2_item(project=FOREIGN_PROJECT))

    with pytest.raises(IngressRejected, match="project outside this profile"):
        ingress(tmp_path, notifications).receive("foreign-1", "projects_v2_item", signature, body)
    assert notifications == []


def test_a_delivery_for_another_repository_is_refused(tmp_path: Path) -> None:
    body, signature = signed(issue_comment(repository="AlienLogicLab/elsewhere"))

    with pytest.raises(IngressRejected, match="ambiguous profile"):
        ingress(tmp_path, []).receive("foreign-2", "issue_comment", signature, body)


def test_a_project_delivery_reaching_a_profile_with_no_configured_project_is_ambiguous(tmp_path: Path) -> None:
    body, signature = signed(projects_v2_item())

    with pytest.raises(IngressRejected, match="ambiguous profile"):
        ingress(tmp_path, [], project=None).receive("unbound-1", "projects_v2_item", signature, body)


# --- delivery translation ----------------------------------------------------


def test_a_live_projects_v2_item_reference_carries_a_project_and_no_repository() -> None:
    reference = delivery_reference(projects_v2_item(), "projects_v2_item")

    assert (reference.work, reference.project, reference.repository) == ("I_kwDOsandbox", SANDBOX_PROJECT, None)


def test_a_recorded_fixture_reference_still_carries_a_repository_and_version() -> None:
    reference = delivery_reference(
        {"project_item": {"id": "PY-05", "version": 3}, "repository": {"full_name": SANDBOX_REPOSITORY}}, "projects_v2_item",
    )

    assert (reference.work, reference.version, reference.repository, reference.project) == ("PY-05", 3, SANDBOX_REPOSITORY, None)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"projects_v2_item": {"node_id": "PVTI_x"}},
        {"projects_v2_item": {"project_node_id": SANDBOX_PROJECT}},
        {"issue": {"number": 1}, "repository": {"full_name": SANDBOX_REPOSITORY}},
        {"issue": {"node_id": "I_x"}},
    ],
)
def test_a_delivery_that_identifies_nothing_is_rejected_rather_than_guessed(payload: dict) -> None:
    with pytest.raises(DeliveryRejected):
        delivery_reference(payload, "issue_comment")


# --- scope 5: the resident ingress binds the configured address --------------


def test_the_resident_ingress_binds_the_requested_address_and_admits_over_http(tmp_path: Path) -> None:
    notifications: list[str] = []
    resident = ingress(tmp_path, notifications)
    body, signature = signed(projects_v2_item())

    with serve_webhook(resident, "127.0.0.1", 0) as route:
        assert route.startswith("http://127.0.0.1:")
        request = Request(route, data=body, method="POST", headers={
            "X-GitHub-Delivery": "resident-1", "X-GitHub-Event": "projects_v2_item", "X-Hub-Signature-256": signature,
        })
        assert urlopen(request).status == 202
        assert urlopen(route.removesuffix("/webhook")).read() == RESIDENT_INGRESS_MARKER

    assert notifications == ["upstream-product-change:I_kwDOsandbox"]


def test_the_resident_ingress_refuses_a_forged_delivery_over_http(tmp_path: Path) -> None:
    resident = ingress(tmp_path, [])
    body = json.dumps(projects_v2_item()).encode()

    with serve_webhook(resident, "127.0.0.1", 0) as route:
        request = Request(route, data=body, method="POST", headers={
            "X-GitHub-Delivery": "resident-2", "X-GitHub-Event": "projects_v2_item", "X-Hub-Signature-256": "sha256=forged",
        })
        with pytest.raises(HTTPError) as refused:
            urlopen(request)

    assert refused.value.code == 401
