"""FX-O (WO-220404): the offline multi-role lifecycle capstone.

Each probe runs one pinned scenario of ``alienintent.composition.lifecycle_capstone``
over its own disposable root, through the production composition only: S0's
substrate with the K1 journal, K2 role routing, K3 binding guard, C1 judgment
attention and the AC-08 ownership attestation bound. The command probes run the
whole proof as pinned - inside an unprivileged user+network namespace with the
environment stated in full - and read its report back. A hold is never a pass.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.composition.lifecycle_capstone import EXIT_HOLD, EXIT_PASS, SCENARIOS, CapstoneSubstrate, compose, load_document, run_scenario
from alienintent.composition.offline_proof import network_denial_probe
from alienintent.composition.role_binding import RoleBindingGuard
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/evidence/wave2-proof-fixtures/FX-O/manifest.json"


def environment(tmp_path: Path) -> dict[str, str]:
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    return {"PATH": os.environ["PATH"], "HOME": str(home), "LANG": "C.UTF-8"}


def proved(name: str, tmp_path: Path, *identifiers: str) -> dict[str, object]:
    checks, facts = run_scenario(name, tmp_path / name, MANIFEST, environment(tmp_path))
    failed = [f"{c['id']} {c['name']}: {json.dumps(c['observed'], default=str)[:1200]}" for c in checks if c["status"] != "PASS"]
    assert not failed, "\n".join(failed)
    assert [c["id"] for c in checks] == list(identifiers)
    return facts


# --- class 1: denied-network lifecycle, publication, retrieval, wrong candidate ----


def test_the_lifecycle_rejects_reworks_and_closes_through_distinct_roles_and_actual_git_custody(tmp_path: Path) -> None:
    proved("lifecycle", tmp_path, *(f"L{n}" for n in range(1, 11)))


def test_a_candidate_the_producer_never_published_is_refused_before_the_verifier_launches(tmp_path: Path) -> None:
    proved("wrong-candidate", tmp_path, "W1")


def test_an_unpublished_candidate_cannot_be_retrieved_for_verification(tmp_path: Path) -> None:
    proved("unpublished-candidate", tmp_path, "U1")


# --- class 3 / AC-07: durable outcome evidence ----------------------------------------


@pytest.mark.parametrize(("name", "identifier"), [("miscorrelated-outcome", "M1"), ("duplicate-outcome", "N1"), ("malformed-outcome", "F1")])
def test_a_miscorrelated_duplicate_or_malformed_outcome_holds_despite_process_success(tmp_path: Path, name: str, identifier: str) -> None:
    proved(name, tmp_path, identifier)


def test_a_delayed_durable_outcome_is_read_back_once_after_the_owner_died(tmp_path: Path) -> None:
    proved("delayed-readback", tmp_path, "D1")


# --- class 4: judgment hold and exactly one authorized effect -------------------------


def test_a_judgment_required_outcome_holds_until_one_attributable_decision(tmp_path: Path) -> None:
    proved("judgment-hold", tmp_path, "J1", "J2", "J3", "J4")


def test_an_escaped_effect_holds_until_one_decision_authorizes_exactly_one_effect(tmp_path: Path) -> None:
    proved("unknown-effect", tmp_path, "E1", "E2")


# --- AC-08: invocation ownership and deterministic recovery ---------------------------


@pytest.mark.parametrize(("name", "prefix"), [("crash-before-output", "C"), ("progress-then-crash", "P")])
def test_conclusive_owner_death_with_a_missing_result_recovers_deterministically(tmp_path: Path, name: str, prefix: str) -> None:
    proved(name, tmp_path, f"{prefix}1", f"{prefix}2")


@pytest.mark.parametrize(("name", "identifier"), [("owner-alive", "A1"), ("owned-work-active", "B1")])
def test_unknown_ownership_blocks_replacement(tmp_path: Path, name: str, identifier: str) -> None:
    proved(name, tmp_path, identifier)


# --- class 5: binding ------------------------------------------------------------------


class AnotherRolesGrant(CapstoneSubstrate):
    """A fault at the grant issuer: every dispatch is granted as PRODUCER, whatever role it plays."""

    def grant(self, invocation: WorkerInvocation) -> CapabilityGrant:
        return CapabilityGrant("fx-o-producer-only", "1", invocation.correlation_id, InvocationRole.PRODUCER, self.manifest.profile,
                               self.manifest.repository, frozenset({"process-control", "git-write"}), int(self.clock()) + 3600)


def test_the_capstone_reaches_its_worker_only_through_the_binding_guard(tmp_path: Path) -> None:
    from alienintent.composition.lifecycle_capstone import scenario_manifest

    composed = AnotherRolesGrant(tmp_path / "root", scenario_manifest(load_document(MANIFEST), ["success", "accept"]), environment(tmp_path))
    composed.coordinator.start()

    state = composed.coordinator.state("O-LIFE")
    verifiers = [r for r in composed.journal.records() if r.get("event") == "invocation-started" and r.get("role") == "VERIFIER"]
    assert verifiers == [], "a verifier launched under a grant for another role"
    assert state.stage is LifecycleStage.VERIFY and state.outcome == "authority-block"
    assert list(composed.worker.refusals.values()) == ["role-authority-miscorrelated"]
    assert isinstance(composed.worker, RoleBindingGuard) and composed.worker.provider is composed.real_worker
    assert composed.real_worker.journal is composed.journal


def test_no_sidecar_state_owner_and_no_scenario_written_lifecycle(tmp_path: Path) -> None:
    composed = compose(tmp_path / "root", load_document(MANIFEST), ["success", "accept"], environment(tmp_path))
    composed.coordinator.start()

    aggregates = {identity for identity, _, _ in composed.store.list_states(composed.manifest.profile)}
    assert all(identity.startswith(("factory:", "release:", "scheduler:", "decision-inbox")) for identity in aggregates), aggregates
    assert not any("stage" in record or "lifecycle" in record for record in composed.journal.records())
    source = (ROOT / "src/alienintent/composition/lifecycle_capstone.py").read_text()
    for forbidden in ("RoleOutcomeRecord", "OutcomeEvidencePort", "CREATE TABLE", "commit_with_effect", "transition(", "mark_done", "sqlite3"):
        assert forbidden not in source, forbidden
    # The one store write is the forged-custody fault the guard must refuse; it never touches the stage.
    [write] = [line for line in source.splitlines() if ".commit(" in line]
    assert '"candidate": candidate' in write and "stage" not in write


# --- the proof command, as pinned ------------------------------------------------------


def unshare_available() -> bool:
    try:
        return subprocess.run(["unshare", "-rn", "true"], capture_output=True, timeout=10, check=False).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def proof_command(root: Path, *, namespace: bool, extra_environment: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], dict]:
    stated = environment(root) | {"PYTHONPATH": str(ROOT / "src")} | (extra_environment or {})
    command = [sys.executable, "-m", "alienintent.composition.lifecycle_capstone", "--root", str(root / "run"), "--manifest", str(MANIFEST), "--network-timeout", "1"]
    if namespace:
        command = ["unshare", "-rn", *command]
    completed = subprocess.run(command, cwd=ROOT, env=stated, capture_output=True, text=True, timeout=900, check=False)
    report_path = root / "run" / "run-report.json"
    return completed, json.loads(report_path.read_text()) if report_path.exists() else {}


@pytest.mark.skipif(not unshare_available(), reason="platform cannot create an unprivileged user+network namespace; network-denial evidence is NOT_ESTABLISHED here")
def test_the_proof_command_passes_inside_an_enforced_network_namespace(tmp_path: Path) -> None:
    completed, report = proof_command(tmp_path, namespace=True)

    assert completed.returncode == EXIT_PASS, completed.stdout + completed.stderr
    assert report["verdict"] == "PASS" and report["hold_reasons"] == []
    assert report["network_denial"]["status"] == "ENFORCED" and report["credentials_present"] == []
    assert report["network_denial"]["net_namespace_inode"] != os.stat("/proc/self/ns/net").st_ino
    assert sorted(report["scenarios"]) == sorted(SCENARIOS)
    assert report["live_proof"] == "NOT_ESTABLISHED" and report["token_usage"] == "UNKNOWN" and report["substituted_boundaries"]


def test_the_proof_command_holds_when_network_denial_is_not_enforced(tmp_path: Path) -> None:
    if network_denial_probe(1.0, os.environ)["status"] == "ENFORCED":
        pytest.skip("this host already denies outbound network; the negative control needs a reachable route")

    completed, report = proof_command(tmp_path, namespace=False)

    assert completed.returncode == EXIT_HOLD
    assert report["verdict"] == "HOLD" and report["scenarios"] == {}
    assert any(reason.startswith("outbound network denial not established") for reason in report["hold_reasons"])


def test_the_proof_command_holds_on_a_present_credential(tmp_path: Path) -> None:
    completed, report = proof_command(tmp_path, namespace=unshare_available(), extra_environment={"GITHUB_TOKEN": "fx-o-sentinel"})

    assert completed.returncode == EXIT_HOLD
    assert report["verdict"] == "HOLD" and report["credentials_present"] == ["GITHUB_TOKEN"]
    assert "fx-o-sentinel" not in json.dumps(report)
