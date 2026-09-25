"""FX-S0: the existing kernel runs unchanged over the S0 isolated proof substrate.

The in-process tests exercise the composed substrate directly. The command
tests launch `python -m alienintent.composition.offline_proof` as the pinned
plan does — inside an unprivileged user+network namespace with an environment
stated in full — and read its report back. Where the platform cannot create the
namespace, those tests skip with the reason recorded; a hold is never a pass.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.composition.offline_profile import ManifestRejected, OfflineProofSubstrate, credential_findings, load_manifest, manifest_from_document
from alienintent.composition.offline_proof import EXIT_FAIL, EXIT_HOLD, EXIT_PASS, network_denial_probe
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation
from alienintent.invocation_runtime.adapters.scripted_worker import journal_outcome, journal_provider_calls, journal_records

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/evidence/wave2-proof-fixtures/FX-S0/manifest.json"


def manifest_document(**overrides) -> dict:
    document = json.loads(MANIFEST.read_text())
    document.update(overrides)
    return document


def substrate(root: Path, *, script: tuple[str, ...] = ("success", "accept"), **overrides) -> OfflineProofSubstrate:
    """The S0 substrate over the current kernel.

    K2 (WO-220402) routes a distinct verifier invocation after producer
    success, so the in-process probes script the verifier's verdict too. The
    immutable S0 manifest scripts only the producer; over the current kernel
    it holds at VERIFY (see the frozen-kernel guard below).
    """
    document = manifest_document(**overrides)
    document["work_items"][0]["script"] = list(script)
    return OfflineProofSubstrate(root, manifest_from_document(document), os.environ)


def unshare_available() -> bool:
    try:
        return subprocess.run(["unshare", "-rn", "true"], capture_output=True, timeout=10, check=False).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def proof_command(root: Path, manifest: Path, *, namespace: bool, extra_environment: dict[str, str] | None = None, timeout: float = 1.0, source_root: Path = ROOT) -> tuple[subprocess.CompletedProcess[str], dict]:
    """The pinned C2 invocation: env stated in full, optionally inside `unshare -rn`."""
    home = root / "home"
    home.mkdir(parents=True, exist_ok=True)
    environment = {"PATH": os.environ["PATH"], "HOME": str(home), "LANG": "C.UTF-8", "PYTHONPATH": str(source_root / "src")} | (extra_environment or {})
    command = [sys.executable, "-m", "alienintent.composition.offline_proof", "--root", str(root), "--manifest", str(manifest), "--network-timeout", str(timeout)]
    if namespace:
        command = ["unshare", "-rn", *command]
    completed = subprocess.run(command, cwd=source_root, env=environment, capture_output=True, text=True, timeout=300, check=False)
    report = json.loads((root / "run-report.json").read_text()) if (root / "run-report.json").exists() else {}
    return completed, report


# --- manifest and credential observations --------------------------------------


def test_the_pinned_manifest_loads_and_names_the_single_probe_item() -> None:
    manifest = load_manifest(MANIFEST)

    assert (manifest.fixture_id, manifest.profile, manifest.clock_epoch) == ("FX-S0", "fx-s0", 1758542400)
    assert [item.identity for item in manifest.work_items] == ["S0-PROBE"]
    assert manifest.digest.startswith("sha256:")


@pytest.mark.parametrize("overrides", [{"record_kind": "Other"}, {"schema_version": "2"}, {"work_items": []}, {"clock": {}}])
def test_a_manifest_that_is_not_a_schema_1_proof_manifest_is_refused(overrides: dict) -> None:
    with pytest.raises(ManifestRejected):
        manifest_from_document(manifest_document(**overrides))


def test_a_contract_that_names_other_work_than_the_seeded_identity_is_refused(tmp_path: Path) -> None:
    document = manifest_document()
    document["work_items"][0]["contract"]["identity"] = "OTHER"
    with pytest.raises(ManifestRejected, match="does not name"):
        OfflineProofSubstrate(tmp_path, manifest_from_document(document), os.environ)


def test_credential_findings_name_every_variable_that_carries_or_routes_a_credential() -> None:
    environment = {"PATH": "/bin", "HOME": "/h", "GITHUB_TOKEN": "x", "ANTHROPIC_API_KEY": "y", "GIT_CONFIG_COUNT": "1", "SSH_AUTH_SOCK": "/s", "my_secret": "z"}

    assert credential_findings(environment) == ("ANTHROPIC_API_KEY", "GITHUB_TOKEN", "GIT_CONFIG_COUNT", "SSH_AUTH_SOCK", "my_secret")
    assert credential_findings({"PATH": "/bin", "HOME": "/h", "LANG": "C"}) == ()


# --- the composed substrate, in process -------------------------------------------


def test_the_existing_kernel_drains_the_seeded_item_through_the_local_substrate(tmp_path: Path) -> None:
    composed = substrate(tmp_path / "root")

    summary = composed.coordinator.start()

    state = composed.coordinator.state("S0-PROBE")
    assert summary.stop_reason.value == "eligible-backlog-exhausted" and summary.dispatched == ("S0-PROBE",)
    assert state.stage is LifecycleStage.DONE and state.candidate is not None and state.candidate.independent_read_back_proven
    branch, revision = state.candidate.locator.rsplit("#", 1)[1].rsplit("@", 1)
    assert branch == "candidate/launch-S0-PROBE-0" and len(revision) == 40
    assert subprocess.run(["git", "-C", str(composed.remote), "rev-parse", "--is-bare-repository"], capture_output=True, text=True).stdout.strip() == "true"
    assert composed.remote_advertises(branch) == revision
    assert composed.remote_advertises("main") == composed.baseline_revision
    assert (composed.producer_read_back / "producer-launch:S0-PROBE:0" / ".git").exists()
    assert (composed.verifier_root / revision / ".git").exists()
    assert composed.commit_dates(revision) == (1758542400, 1758542400)
    assert [(r["receipt"], r.get("state")) for r in composed.work.receipts()] == [
        ("release-proposed", None), ("execution-state-projected", "VERIFY"), ("execution-state-projected", "ACCEPT"), ("execution-state-projected", "DONE"),
    ]
    assert [(e["event"], e.get("role")) for e in journal_records(composed.journal_path)] == [
        ("invocation-started", "PRODUCER"), ("process-run", "PRODUCER"), ("invocation-outcome", "PRODUCER"), ("workspace-finalized", None),
        ("invocation-started", "VERIFIER"), ("process-run", "VERIFIER"), ("invocation-outcome", "VERIFIER"),
        ("invocation-started", "CLOSURE"), ("invocation-outcome", "CLOSURE"),
    ]
    assert journal_provider_calls(composed.journal_path) == 0
    assert not hasattr(composed.process, "_store") and not hasattr(composed.worker, "_store")
    assert not any("stage" in e or "lifecycle" in e for e in journal_records(composed.journal_path))
    assert not (composed.workspaces / "launch:S0-PROBE:0").exists()


def test_the_candidate_revision_is_determined_by_manifest_and_injected_clock(tmp_path: Path) -> None:
    """Same manifest, isolated roots: same revision. Different clock: different revision."""
    def revision_of(root: Path, epoch: int) -> str:
        composed = substrate(root, clock={"epoch_seconds": epoch})
        composed.coordinator.start()
        return composed.coordinator.state("S0-PROBE").candidate.locator.rsplit("@", 1)[1]

    same_a, same_b = revision_of(tmp_path / "a", 1758542400), revision_of(tmp_path / "b", 1758542400)
    other = revision_of(tmp_path / "c", 1758542401)

    assert same_a == same_b
    assert other != same_a


def test_reopening_the_same_root_reads_back_the_same_truth_and_dispatches_nothing(tmp_path: Path) -> None:
    first = substrate(tmp_path / "root")
    first.coordinator.start()
    done = first.coordinator.state("S0-PROBE")

    reopened = substrate(tmp_path / "root")
    summary = reopened.coordinator.start()

    assert reopened.reopened and reopened.work.reopened
    assert summary.dispatched == () and reopened.coordinator.state("S0-PROBE").candidate == done.candidate
    outcome = reopened.worker.read_back(WorkerInvocation("S0-PROBE", "launch:S0-PROBE:0"))
    assert outcome is not None and outcome.candidate is not None and outcome.candidate.locator == done.candidate.locator
    assert len(journal_records(reopened.journal_path)) == 9
    assert journal_outcome(substrate(tmp_path / "fresh").journal_path, "launch:S0-PROBE:0") is None


# --- the proof command, as pinned ---------------------------------------------------


@pytest.mark.skipif(not unshare_available(), reason="platform cannot create an unprivileged user+network namespace; network-denial evidence is NOT_ESTABLISHED here")
def test_the_proof_command_passes_inside_an_enforced_network_namespace(tmp_path: Path) -> None:
    """Retain S0's positive proof at the exact pre-S2 admission source.

    S2 authorizes extending sqlite_store.py; this does not retroactively change
    S0's immutable manifest or its requirement that its own kernel be unchanged.
    """
    baseline = "0515444b5c43c83f4a5e26c9ec2c5956f064e1d9"
    source = tmp_path / "historical-source"
    subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout", str(ROOT), str(source)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(source), "checkout", "--quiet", "--detach", baseline], check=True, capture_output=True)
    assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() == baseline
    historical_manifest = source / MANIFEST.relative_to(ROOT)
    assert historical_manifest.read_bytes() == MANIFEST.read_bytes()
    completed, report = proof_command(tmp_path / "root", historical_manifest, namespace=True, source_root=source)

    assert completed.returncode == EXIT_PASS, completed.stderr
    assert report["verdict"] == "PASS" and report["hold_reasons"] == []
    assert report["network_denial"]["status"] == "ENFORCED"
    assert report["network_denial"]["socket"]["name"] in {"ENETUNREACH", "EPERM", "EACCES"}
    assert report["network_denial"]["git_ls_remote"]["exit_status"] not in (0, None)
    assert report["network_denial"]["net_namespace_inode"] != os.stat("/proc/self/ns/net").st_ino
    assert report["credentials_present"] == []
    assert report["provider_calls_observed"]["value"] == 0
    assert report["lifecycle_terminal_stage"] == {"S0-PROBE": "DONE"}
    assert report["success_collapse_limitation"]["independent_verifier_invocation"] == "NOT_ESTABLISHED"
    assert report["live_proof"] == "NOT_ESTABLISHED" and report["token_usage"] == "NOT_APPLICABLE"
    assert {check["id"] for check in report["checks"]} == {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P10", "P11", "P12", "P13"}
    events = [json.loads(line) for line in (tmp_path / "root" / "trajectory.jsonl").read_text().splitlines()]
    assert [event["event_type"] for event in events] == ["ISOLATION_OBSERVED", "BIU_RELEASED", "INVOCATION_STARTED", "CANDIDATE_PUBLISHED", "SUCCESS_COLLAPSE_OBSERVED", "BIU_DONE"]
    required = {"schema_version", "event_id", "project", "biu_id", "event_type", "actor_role", "evidence_refs", "recorded_at"}
    assert all(required <= set(event) and event["evidence_refs"] for event in events)


@pytest.mark.skipif(not unshare_available(), reason="platform cannot create an unprivileged user+network namespace")
def test_s0_frozen_kernel_guard_rejects_authorized_s2_store_extension(tmp_path: Path) -> None:
    """Removing P11 must not turn a changed kernel into historical S0 proof."""
    completed, report = proof_command(tmp_path / "root", MANIFEST, namespace=True)
    assert completed.returncode == EXIT_FAIL
    assert report["verdict"] == "FAIL"
    assert report["kernel_unchanged"]["status"] == "CHANGED"
    kernel = report["kernel_unchanged"]
    changed = subprocess.check_output(["git", "diff", "--name-only", kernel["baseline"], "--", *kernel["paths"]], cwd=ROOT, text=True).splitlines()
    # S2 extends the store; K1 (WO-220401) adds the durable outcome correlation
    # gate and the real worker's journaled read-back; K2 (WO-220402) replaces
    # the success collapse with role-routed invocations and checks the exact
    # candidate out for the verifier.
    assert changed == [
        "src/alienintent/execution_coordination/adapters/sqlite_store.py",
        "src/alienintent/execution_coordination/application/factory_coordinator.py",
        "src/alienintent/invocation_runtime/adapters/git_source_control.py",
        "src/alienintent/invocation_runtime/application/real_worker.py",
    ]
    assert {c["id"] for c in report["checks"]} == {"P1", "P2", "P3", "P4", "P5", "P6", "P7", "P10", "P11", "P12", "P13"}
    # S0's manifest scripts no verifier verdict. Without the collapse the probe
    # holds at VERIFY, so every DONE-shaped S0 check and the collapse
    # observation itself (P12) no longer hold over the current kernel.
    assert [c["id"] for c in report["checks"] if c["status"] != "PASS"] == ["P1", "P3", "P4", "P7", "P11", "P12", "P13"]
    assert report["lifecycle_terminal_stage"] == {"S0-PROBE": "VERIFY"}
    assert report["success_collapse_limitation"]["observed"] is False


def test_the_proof_command_holds_when_network_denial_is_not_enforced(tmp_path: Path) -> None:
    """Negative control C3: silence, a timeout or a connection is never reported as denial."""
    if network_denial_probe(1.0, os.environ)["status"] == "ENFORCED":
        pytest.skip("this host already denies outbound network; the negative control needs a reachable route")

    completed, report = proof_command(tmp_path / "root", MANIFEST, namespace=False)

    assert completed.returncode == EXIT_HOLD
    assert report["verdict"] == "HOLD" and report["network_denial"]["status"] == "NOT_ESTABLISHED"
    assert any(reason.startswith("outbound network denial not established") for reason in report["hold_reasons"])
    assert "checks" in report and report["checks"] == []


def test_the_proof_command_refuses_a_present_credential(tmp_path: Path) -> None:
    """Negative control C4: a credential in the proof environment is a hold, whatever else holds."""
    completed, report = proof_command(tmp_path / "root", MANIFEST, namespace=unshare_available(), extra_environment={"GITHUB_TOKEN": "fx-s0-sentinel"})

    assert completed.returncode == EXIT_HOLD
    assert report["verdict"] == "HOLD" and report["credentials_present"] == ["GITHUB_TOKEN"]
    assert any(reason.startswith("credential variables present") for reason in report["hold_reasons"])
    assert "fx-s0-sentinel" not in json.dumps(report)


@pytest.mark.skipif(not unshare_available(), reason="platform cannot create an unprivileged user+network namespace")
def test_a_scripted_provider_call_is_counted_and_fails_the_proof(tmp_path: Path) -> None:
    """Negative control C5: the zero-provider-call predicate can go red."""
    document = manifest_document()
    document["work_items"][0]["script"] = ["provider-call"]
    manifest = tmp_path / "provider-call.json"
    manifest.write_text(json.dumps(document))

    completed, report = proof_command(tmp_path / "root", manifest, namespace=True)

    assert completed.returncode == EXIT_FAIL
    assert report["verdict"] == "FAIL" and report["provider_calls_observed"]["value"] == 1
    assert {check["id"]: check["status"] for check in report["checks"]}["P10"] == "FAIL"
    assert report["lifecycle_terminal_stage"] == {"S0-PROBE": "IMPLEMENT"}
