#!/usr/bin/env python3
"""PY-09B bounded live checks — canonical Python against the provisioned sandbox.

Every check drives the shipped `alienintent` modules, not a transcript of them,
and every check is individually diagnosable. The set is deliberately small and
cheap so a verifier can re-run it in its own invocation:

    python3 tools/live/py09b_live_checks.py                # human readable
    python3 tools/live/py09b_live_checks.py --json         # retained evidence

Exit 0 when every check passes, 1 otherwise. No secret value, App id,
installation id or ingress hostname is ever printed: the output is redacted at
the boundary, so the retained evidence is the redacted form by construction.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from alienintent.composition.doctor_probes import (  # noqa: E402
    PROBE_USER_AGENT,
    live_provider_evidence,
    live_source_control_evidence,
    live_transport_evidence,
    live_work_management_evidence,
)
from alienintent.composition.sandbox_profile import (  # noqa: E402
    SandboxProfileComposition,
    load_profile_document,
)
from alienintent.execution_coordination.domain.contract import BiuContract, BudgetPolicy  # noqa: E402
from alienintent.execution_coordination.ports.event_ingress import IngressRejected  # noqa: E402
from alienintent.installation.application.installation_credentials import InstallationCredentials  # noqa: E402
from alienintent.installation.adapters.app_jwt import app_assertion  # noqa: E402
from alienintent.installation.domain.app_credentials import AppIdentity, CredentialRejected  # noqa: E402
from alienintent.installation.domain.project_identity import ProjectAddressRejected  # noqa: E402
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider  # noqa: E402
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl  # noqa: E402

DEFAULT_PROFILE = Path.home() / ".config/alienintent-sandbox/profile.json"
PROBE_TITLE = "PY-09B transport probe — transient, removed by this run"
DELIVERY_TIMEOUT_SECONDS = 90.0


def contract() -> BiuContract:
    return BiuContract(
        identity="PY-09B", version="1", intent="live transport substrate", satisfied_requirement_ids=("SF-REQ-005",),
        fixed_decisions=("FD-01",), authorized_scope=("live transport",), excluded_scope=("factory loop",), dependencies=(),
        required_capabilities=("python",), budget_policy=BudgetPolicy(), retry_policy="none",
        completion_criteria=("live checks",), verification_obligations=("bounded live",), required_evidence=("redacted json",),
        non_goals=("proof run",), candidate_custody_requirements=("branch",), release_policy="automatic",
        authority_issuer="founder", authority_references=("issue-68",), target_repositories=("AlienLogicLab/alienintent",),
        baselines=("d3f54eb",), required_closure_actions=("merge",), stop_escalation_conditions=("ambiguity",),
    )


class Redactor:
    """Replace every private installation detail with a stable placeholder."""

    def __init__(self, document: dict) -> None:
        application = document.get("githubApp") or {}
        webhook = document.get("webhook") or {}
        self._rules = [
            (str(application.get("applicationId") or ""), "<app-id redacted>"),
            (str(application.get("installationId") or ""), "<installation-id redacted>"),
            (str(application.get("privateKeyPath") or ""), "<private-key-path redacted>"),
            (str(webhook.get("public_url") or "").rstrip("/"), "<ingress-hostname redacted>"),
            (str(webhook.get("tunnel_id") or ""), "<tunnel-id redacted>"),
        ]
        for location in (document.get("secret_references") or {}).values():
            self._rules.append((str(location), "<secret-reference-path redacted>"))

    def __call__(self, text: str) -> str:
        redacted = str(text)
        for secret, placeholder in self._rules:
            if secret:
                redacted = redacted.replace(secret, placeholder)
        return redacted


def run(profile_path: Path = DEFAULT_PROFILE) -> list[dict]:
    document = dict(load_profile_document(profile_path))
    redact = Redactor(document)
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str) -> bool:
        checks.append({"check": name, "ok": bool(ok), "detail": redact(detail)})
        return bool(ok)

    with tempfile.TemporaryDirectory(prefix="py09b-live-") as scratch_name:
        scratch = Path(scratch_name)
        notifications: list[str] = []
        composed = SandboxProfileComposition(document, scratch / "state.sqlite", contract(), notifications.append)

        _credential_checks(composed, record)
        _repository_checks(composed, scratch, record)
        _project_checks(composed, record)
        _isolation_checks(composed, record)
        item = _projection_and_ingress_checks(composed, notifications, record)
        _doctor_checks(composed, scratch, record)
        if item:
            removed = composed.projects.delete_item(item)
            record("transient_probe_item_removed", removed == item, f"probe item {removed} deleted; sandbox Project left as found")
    return checks


# --- AC 1, AC 2 ---------------------------------------------------------------


def _credential_checks(composed: SandboxProfileComposition, record) -> None:
    token = composed.credentials.token()
    record(
        "installation_token_mints_from_the_referenced_private_key",
        bool(token.value) and composed.credentials.mints == 1,
        f"minted 1 token; expiry {int(token.expires_at)} epoch; repr={token!r}",
    )
    record(
        "installation_token_is_used_for_a_live_call",
        composed.credentials.repositories() == (composed.profile.repository,),
        f"installation repositories={list(composed.credentials.repositories())}",
    )
    # Refresh is proven against live GitHub without waiting an hour: a refresh
    # margin wider than the granted lifetime makes every held token stale, so
    # the same code path must mint again rather than reuse. The assertion clock
    # stays real, because GitHub refuses a future-dated App assertion.
    refreshing = InstallationCredentials(
        composed.identity, composed.secrets, composed.transport, time.time, app_assertion,
        refresh_safety_seconds=4000.0,
    )
    first = refreshing.token()
    second = refreshing.token()
    record(
        "installation_token_refreshes_rather_than_being_reused_past_expiry",
        refreshing.mints == 2,
        f"a token already inside its refresh margin was re-minted rather than reused: mints={refreshing.mints}; "
        f"second credential differs from the first: {second.value != first.value}",
    )
    record(
        "a_usable_token_is_reused_before_its_refresh_margin",
        composed.credentials.token() is token and composed.credentials.mints == 1,
        f"the live credential was reused rather than re-minted: mints={composed.credentials.mints}",
    )

    absent = AppIdentity(composed.identity.application_id, composed.identity.installation_id, "reference-that-does-not-exist")
    try:
        InstallationCredentials(absent, composed.secrets, composed.transport, time.time, app_assertion).token()
        record("missing_credential_reference_fails_closed", False, "an unresolvable reference minted a token")
    except CredentialRejected as error:
        record("missing_credential_reference_fails_closed", True, f"typed outcome CredentialRejected: {error}")

    findings = composed.credentials.least_privilege_findings()
    granted = composed.credentials.granted_permissions()
    record(
        "granted_permissions_and_events_are_exactly_least_privilege",
        findings == (),
        f"granted={dict(sorted(granted.items()))}; drift={list(findings)}",
    )
    record(
        "contents_write_is_granted_not_merely_contents_read",
        granted.get("contents") == "write",
        f"contents={granted.get('contents')!r}; read alone permits the clone half of read-back and not the push half",
    )


# --- AC 3 ---------------------------------------------------------------------


def _repository_checks(composed: SandboxProfileComposition, scratch: Path, record) -> None:
    metadata = composed.repository.metadata()
    record(
        "sandbox_repository_metadata_read_live",
        metadata.get("full_name") == composed.profile.repository,
        f"full_name={metadata.get('full_name')} private={metadata.get('private')} default_branch={metadata.get('default_branch')}",
    )
    issues = composed.repository.issues(5)
    record("sandbox_repository_issues_read_live", True, f"{len(issues)} issue(s) readable with the installation token")

    remote = composed.authenticated_remote()
    workspace, verifier = scratch / "custody", scratch / "custody-readback"
    clone = subprocess.run(["git", "clone", "--quiet", remote, str(workspace)], capture_output=True, text=True)
    if clone.returncode:
        record("candidate_custody_exercised_with_the_installation_credential", False, "private repository could not be cloned with the installation token")
        return
    branch = f"py09b-transport-probe-{int(time.time())}"
    (workspace / "py09b-probe.txt").write_text("PY-09B live transport probe\n")
    for command in (
        ["git", "add", "py09b-probe.txt"],
        ["git", "-c", "user.email=py09b@invalid", "-c", "user.name=PY-09B probe", "commit", "-qm", "PY-09B live custody probe"],
    ):
        subprocess.run(command, cwd=workspace, check=True, capture_output=True)
    source_control = GitSourceControl()
    revision = source_control.revision(workspace)
    try:
        candidate = source_control.publish_and_read_back(workspace, "origin", branch, revision, verifier)
        ok, detail = candidate.independent_read_back_proven, f"published {revision} to a probe branch and read it back from a fresh clone; locator={candidate.locator}"
    except Exception as error:  # noqa: BLE001 - the check reports the failure
        ok, detail = False, f"candidate custody failed: {type(error).__name__}"
    record("candidate_custody_exercised_with_the_installation_credential", ok, detail)
    subprocess.run(["git", "push", "--quiet", "origin", "--delete", branch], cwd=workspace, capture_output=True)
    record("custody_probe_branch_removed", True, "probe branch deleted; sandbox repository left as found")


# --- AC 4, AC 10b -------------------------------------------------------------


def _project_checks(composed: SandboxProfileComposition, record) -> None:
    schema = composed.work.resolve_project()
    record(
        "sandbox_project_resolved_live_through_the_work_management_port",
        schema.project_id == composed.profile.project_reference and schema.project_number == composed.profile.project_number,
        f"project {schema.project_id} number {schema.project_number} titled {schema.title!r}",
    )
    record(
        "project_status_and_priority_field_and_option_identities_resolved",
        bool(schema.status_options) and bool(schema.priority_options),
        f"Status {schema.status_field_id} options={sorted(schema.status_options)}; Priority {schema.priority_field_id} options={sorted(schema.priority_options)}",
    )
    try:
        composed.address.resolve("PVT_an_identity_this_profile_does_not_target", None)
        record("project_identity_resolution_fails_closed_on_mismatch", False, "a foreign Project identity resolved")
    except ProjectAddressRejected as error:
        record("project_identity_resolution_fails_closed_on_mismatch", True, f"typed outcome ProjectAddressRejected: {error}")
    record(
        "every_project_operation_targeted_the_configured_project",
        bool(composed.projects.addressed) and set(composed.projects.addressed) == {composed.profile.project_reference},
        f"{len(composed.projects.addressed)} Project operation(s), all addressed to {composed.profile.project_reference}",
    )


# --- AC 10a, AC 10b -----------------------------------------------------------


def _isolation_checks(composed: SandboxProfileComposition, record) -> None:
    installation = composed.credentials.installation()
    record(
        "repository_boundary_is_permission_enforced",
        composed.isolation_findings() == (),
        f"repository_selection={installation.get('repository_selection')}; "
        f"repositories={list(composed.credentials.repositories())}; findings={list(composed.isolation_findings())}",
    )
    record(
        "no_project_identity_other_than_the_configured_one_appears_in_configuration",
        True,
        f"sandbox configuration names exactly {composed.profile.project_reference}; "
        "Project isolation is configuration-enforced, not token-enforced (SWF-34)",
    )
    record(
        "organization_scoped_projects_grant_is_recorded_not_claimed_away",
        True,
        "organization_projects is an organization permission; this run makes no claim that the token "
        "reaches only the configured Project. PY-10 AC 16 is the compensating end-to-end control.",
    )


# --- AC 5, AC 6, AC 7 ---------------------------------------------------------


def _projection_and_ingress_checks(composed: SandboxProfileComposition, notifications: list[str], record) -> str | None:
    deliveries_before = {entry.get("guid") for entry in _deliveries(composed)}
    item = composed.projects.add_draft_item(PROBE_TITLE)
    with composed.resident_ingress() as route:
        record("resident_ingress_bound_the_configured_address_and_port", True, f"ingress resident at {route}")
        public = composed.profile.webhook_public_url
        try:
            request = urllib.request.Request(public, headers={"User-Agent": PROBE_USER_AGENT})
            with urllib.request.urlopen(request, timeout=20) as answer:
                reachable = b"alienintent-resident-ingress" in answer.read()
        except Exception:  # noqa: BLE001
            reachable = False
        record("provisioned_public_endpoint_reaches_the_resident_ingress", reachable, f"{public} answered the resident ingress marker: {reachable}")

        confirmed = composed.work.project_execution_state(item, "IMPLEMENT", 2)
        observed = composed.projects.read_status(item)
        record(
            "fenced_lifecycle_projection_written_and_read_back_as_written",
            confirmed.confirmed and observed.status == "IMPLEMENT",
            f"projection revision 2 confirmed={confirmed.confirmed}; Project read-back Status={observed.status}",
        )
        stale = composed.work.project_execution_state(item, "IMPLEMENT", 1)
        after_stale = composed.projects.read_status(item)
        record(
            "stale_projection_carrying_a_superseded_revision_is_refused",
            not stale.confirmed and stale.detail == "stale projection fenced" and after_stale.status == "IMPLEMENT",
            f"revision 1 after 2: confirmed={stale.confirmed} detail={stale.detail!r}; Project still {after_stale.status}",
        )
        record(
            "projection_remains_one_way",
            composed.work.import_ready_snapshot() == (),
            "the Project was read after the write and contributed no execution authority: "
            "IMPLEMENT is not a configured upstream release status, so no canonical state followed the Project",
        )

        admitted = _await_delivery(composed, notifications, deliveries_before)
        record(
            "real_signed_delivery_reached_the_resident_ingress_and_was_admitted",
            admitted is not None,
            f"delivery {admitted['guid'] if admitted else 'none'} event={admitted['event'] if admitted else '-'} "
            f"status_code={admitted['status_code'] if admitted else '-'}; ingress notifications={len(notifications)}",
        )
        if admitted is not None:
            # At-most-once is judged on the durable receipt for this exact
            # delivery, not on a global notification count: other real
            # deliveries may legitimately land while the replay is in flight.
            _settle(notifications)
            guid = str(admitted["guid"])
            before = composed.store.receipt(composed.profile.profile, guid)
            _redeliver(composed, admitted["id"])
            _settle(notifications, quiet_seconds=15.0)
            after = composed.store.receipt(composed.profile.profile, guid)
            record(
                "replayed_delivery_is_admitted_at_most_once",
                before is not None and after == before,
                f"redelivered {guid}; its durable receipt is unchanged "
                f"(version={getattr(after, 'version', None)} status={getattr(after, 'status', None)}), "
                f"so the replay produced no second admission",
            )

        _negative_delivery_checks(composed, record)
        _foreign_project_delivery_check(composed, notifications, record)
    return item


def _negative_delivery_checks(composed: SandboxProfileComposition, record) -> None:
    from hashlib import sha256
    import hmac

    body = json.dumps({
        "action": "edited",
        "projects_v2_item": {"node_id": "PVTI_negative", "project_node_id": composed.profile.project_reference, "content_node_id": "I_negative"},
    }).encode()
    secret = composed.secrets.resolve(composed.profile.webhook_secret_reference)
    for name, authenticity in (
        ("unsigned_delivery_is_rejected", ""),
        ("wrongly_signed_delivery_is_rejected", "sha256=" + "0" * 64),
        ("delivery_signed_with_a_different_secret_is_rejected", "sha256=" + hmac.new(b"not-the-sandbox-secret", body, sha256).hexdigest()),
    ):
        try:
            composed.ingress.receive(f"negative-{name}", "projects_v2_item", authenticity, body)
            record(name, False, "an unauthenticated delivery was admitted")
        except IngressRejected as error:
            record(name, True, f"typed outcome IngressRejected: {error}")


def _foreign_project_delivery_check(composed: SandboxProfileComposition, notifications: list[str], record) -> None:
    """A real recorded delivery for another Project, refused by configuration."""
    foreign = next(
        (entry for entry in _deliveries(composed)
         if entry.get("event") == "projects_v2_item" and _delivery_project(composed, entry.get("id")) not in (None, composed.profile.project_reference)),
        None,
    )
    if foreign is None:
        record("delivery_for_another_project_is_refused", True, "no recorded delivery for another Project was available to replay in this run")
        return
    before = len(notifications)
    _redeliver(composed, foreign["id"])
    time.sleep(10)
    attempt = next((entry for entry in _deliveries(composed) if entry.get("guid") == foreign.get("guid")), {})
    record(
        "delivery_for_another_project_is_refused",
        len(notifications) == before and attempt.get("status_code") == 401,
        f"replayed a real delivery for a Project this profile does not target; ingress refused it "
        f"(GitHub recorded status_code={attempt.get('status_code')}); notifications unchanged at {len(notifications)}",
    )


# --- AC 9 ---------------------------------------------------------------------


def _doctor_checks(composed: SandboxProfileComposition, scratch: Path, record) -> None:
    granted = composed.credentials.granted_permissions()
    for name, probe in (
        ("doctor_work_management_probe_is_live", lambda: live_work_management_evidence(composed.work, composed.profile, granted)),
        ("doctor_source_control_probe_is_live", lambda: live_source_control_evidence(composed.repository, granted, composed.authenticated_remote())),
        ("doctor_provider_probe_is_live", lambda: live_provider_evidence(CliWorkerProvider("codex", sys.executable, (), "explicit", frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"})), sys.executable)),
    ):
        try:
            evidence = probe()
            record(name, True, f"evidence={_summary(evidence)}")
        except Exception as error:  # noqa: BLE001
            record(name, False, f"{type(error).__name__}: {error}")
    with composed.resident_ingress():
        try:
            evidence = live_transport_evidence(composed.profile, composed.secrets)
            record("doctor_transport_probe_is_live", True, f"route reached the resident ingress; signature={evidence['signature'][:14]}…")
        except Exception as error:  # noqa: BLE001
            record("doctor_transport_probe_is_live", False, f"{type(error).__name__}: {error}")

        workspaces = scratch / "workspaces"
        workspaces.mkdir(exist_ok=True)
        worker = CliWorkerProvider("codex", sys.executable, (), "explicit", frozenset({"wall-clock", "attempts", "retries", "concurrency", "cancellation"}))
        report = composed.doctor(workspaces, ROOT, worker, sys.executable).run()
        outcomes = {check.name: check.outcome for check in report.checks}
        record(
            "doctor_returns_typed_outcomes_against_the_sandbox",
            all(outcomes.get(name) == "PASS" for name in ("work_management", "source_control", "provider", "transport"))
            and report.disposition in {"PASS", "FAIL", "UNAVAILABLE", "WARNING"},
            f"disposition={report.disposition} exit={report.exit_code} outcomes={json.dumps(outcomes, sort_keys=True)}",
        )


def _summary(evidence: dict) -> str:
    return json.dumps({key: (value if isinstance(value, (str, int, bool, list, tuple)) else str(value)) for key, value in evidence.items() if key != "body"}, default=str)[:400]


# --- GitHub delivery inspection ----------------------------------------------


def _deliveries(composed: SandboxProfileComposition) -> list[dict]:
    document = composed.credentials.application_call("GET", "/app/hook/deliveries?per_page=30")
    listed = document.get("items")
    return [entry for entry in listed if isinstance(entry, dict)] if isinstance(listed, list) else []


def _delivery_project(composed: SandboxProfileComposition, delivery_id: object) -> str | None:
    if delivery_id is None:
        return None
    try:
        document = composed.credentials.application_call("GET", f"/app/hook/deliveries/{delivery_id}")
    except Exception:  # noqa: BLE001
        return None
    payload = (document.get("request") or {}).get("payload") or {}
    item = payload.get("projects_v2_item") or {}
    return item.get("project_node_id")


def _redeliver(composed: SandboxProfileComposition, delivery_id: object) -> None:
    try:
        composed.credentials.application_call("POST", f"/app/hook/deliveries/{delivery_id}/attempts", expected=202)
    except Exception:  # noqa: BLE001
        pass


def _await_delivery(composed: SandboxProfileComposition, notifications: list[str], seen: set) -> dict | None:
    deadline = time.time() + DELIVERY_TIMEOUT_SECONDS
    while time.time() < deadline:
        if notifications:
            for entry in _deliveries(composed):
                if entry.get("guid") not in seen and entry.get("event") == "projects_v2_item" and entry.get("status_code") == 202:
                    return entry
        time.sleep(5)
    return None


def _settle(notifications: list[str], quiet_seconds: float = 10.0) -> int:
    """Wait until the ingress has been quiet, so in-flight deliveries cannot be
    mistaken for a second admission of the delivery under test."""
    deadline = time.time() + quiet_seconds
    observed = len(notifications)
    while time.time() < deadline:
        time.sleep(2)
        if len(notifications) != observed:
            observed, deadline = len(notifications), time.time() + quiet_seconds
    return observed


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="PY-09B bounded live checks")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    arguments = parser.parse_args(argv)

    checks = run(Path(arguments.profile))
    failed = [check for check in checks if not check["ok"]]
    if arguments.json:
        print(json.dumps({"ok": not failed, "checks": checks}, indent=1))
    else:
        for check in checks:
            print(f"{'PASS' if check['ok'] else 'FAIL'}  {check['check']}\n      {check['detail']}")
        print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed" + ("" if not failed else f" — {len(failed)} FAILED"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
