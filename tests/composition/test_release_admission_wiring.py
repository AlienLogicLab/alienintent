"""WO-220611 (B3P): the operational profiles enforce the canonical release gate by construction.

``SandboxRunProfile`` (the ``alienintent --profile-factory`` live profile) and
``GitHubProfileComposition`` always compose the SWF-21 precondition gate and the
attributable per-BIU allocation. Each case drives the real profile constructor
and counts actual worker starts; nothing here injects a gate by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from alienintent.composition.release_admission import (
    DEFAULT_RELEASE_POINT,
    ReleaseAdmissionConfig,
    ReleaseAdmissionRejected,
    compose_release_admission,
    release_admission_config,
)
from alienintent.composition.sandbox_run_profile import SandboxBacklogComposition, SandboxRunProfile, worker_environment
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.domain.release import ReleaseAuthorization
from tests.composition import k3_fixture
from tests.composition.test_sandbox_profile import document
from tests.composition.test_sandbox_run_profile import _seeded_repository, contract_document, digest_of, project_item
from tests.support.live_github import RecordedTransport, project_graphql, rest_answers
from tests.support.release_admission import authorize_release, release_admission_section

EPOCH = 1758445000.0


def _sandbox(tmp_path: Path, *, limits: bool = True, record: bool = True, release_point: str | None = None) -> SandboxRunProfile:
    """The real run profile over one SB-01 item; release inputs are exactly what the flags say."""
    _, checkout = _seeded_repository(tmp_path)
    only = contract_document("SB-01")
    items = [project_item("PVTI_1", "SB-01", priority="P0", ready_at="2026-09-21T11:00:01Z", digest=digest_of(only))]
    transport = RecordedTransport(rest_answers(contents={"biu/SB-01.json": json.dumps(only).encode()}), project_graphql(items=items))
    profile_document = dict(document(tmp_path))
    if limits:
        profile_document |= release_admission_section(("SB-01",))
    if release_point is not None:
        section = dict(profile_document.get("release_admission") or {})
        profile_document["release_admission"] = section | {"release_point": release_point}
    composed = SandboxBacklogComposition(profile_document, tmp_path / "state.sqlite", lambda _: None, transport, lambda: EPOCH)
    profile = SandboxRunProfile(composed, tmp_path / "state", checkout, provider="claude", worker_command=("/bin/bash", "worker/run.sh"),
                                worker_environment=worker_environment(tmp_path), clock=lambda: EPOCH)
    if record:
        authorize_release(profile.release_records, checkout, ("SB-01",))
    return profile


def _producer_starts(profile) -> list[str]:
    started: list[str] = []
    original = profile.worker.start

    def counted(invocation, context, grants, budget):
        if invocation.role == "PRODUCER":
            started.append(invocation.work_identity)
        return original(invocation, context, grants, budget)

    profile.worker.start = counted  # type: ignore[method-assign]
    return started


def test_both_operational_profiles_compose_the_gate_and_the_allocation(tmp_path: Path) -> None:
    sandbox = _sandbox(tmp_path / "sandbox")
    github = k3_fixture.github(tmp_path / "github")

    for profile in (sandbox, github):
        assert profile.coordinator._release_gate is profile.release_admission.gate is not None
        assert profile.coordinator._allocation is profile.release_admission.allocation is not None


def test_the_live_profile_refuses_release_without_a_durable_record(tmp_path: Path) -> None:
    profile = _sandbox(tmp_path, record=False)
    started = _producer_starts(profile)

    summary = profile.coordinator.start()

    assert started == []
    assert summary.authority_blocked == ("SB-01",)
    assert profile.coordinator.state("SB-01").record["hold_reason"] == "release-precondition:implementation-authorized"


def test_the_live_profile_refuses_release_when_no_allocation_is_configured(tmp_path: Path) -> None:
    profile = _sandbox(tmp_path, limits=False)
    started = _producer_starts(profile)

    summary = profile.coordinator.start()

    assert started == []
    assert summary.authority_blocked == ("SB-01",)
    assert profile.coordinator.state("SB-01").outcome == "authority-block"


def test_the_live_profile_refuses_a_baseline_the_release_point_cannot_reach(tmp_path: Path) -> None:
    profile = _sandbox(tmp_path, record=False, release_point="refs/does-not-exist")
    authorize_release(profile.release_records, profile.checkout, ("SB-01",))
    started = _producer_starts(profile)

    profile.coordinator.start()

    assert started == []
    assert profile.coordinator.state("SB-01").record["hold_reason"] == "release-precondition:baseline-reachable"


def test_the_live_profile_releases_exactly_once_when_every_precondition_holds(tmp_path: Path) -> None:
    profile = _sandbox(tmp_path)
    started = _producer_starts(profile)

    profile.coordinator.start()

    assert started == ["SB-01"]
    assert profile.coordinator.state("SB-01").stage is LifecycleStage.DONE


def test_a_github_profile_without_a_checkout_resolves_no_baseline_and_launches_nothing(tmp_path: Path) -> None:
    composed = k3_fixture.github(tmp_path)
    # The same profile recomposed without its checkout: nothing can resolve.
    composed.release_admission = compose_release_admission(composed.store, k3_fixture.GH_PROFILE, k3_fixture.GH_REPOSITORY, None, ReleaseAdmissionConfig())
    composed.coordinator._release_gate = composed.release_admission.gate
    started = _producer_starts(composed)

    composed.coordinator.start()

    assert started == []
    assert composed.coordinator.state(k3_fixture.GH_WORK).record["hold_reason"] == "release-precondition:baseline-resolves"


def test_an_absent_release_admission_section_is_the_fail_closed_default() -> None:
    config = release_admission_config({})

    assert config.release_point == DEFAULT_RELEASE_POINT and dict(config.biu_limits) == {}


@pytest.mark.parametrize("section", [
    [], {"release_point": ""}, {"release_point": 7}, {"biu_limits": []}, {"biu_limits": {"SB-01": 3}},
    {"unknown": True}, {"biu_limits": {"SB-01": {"attempts": -1}}},
])
def test_a_malformed_release_admission_section_is_refused(tmp_path: Path, section) -> None:
    with pytest.raises(ReleaseAdmissionRejected):
        config = release_admission_config({"release_admission": section})
        compose_release_admission(SQLiteOperationalStore(tmp_path / "s.sqlite"), "p", "o/r", None, config)


def test_the_offline_double_profile_carries_a_supplied_gate(tmp_path: Path) -> None:
    from alienintent.composition.offline_profile import OfflineProfile
    from tests.execution_coordination.test_factory_coordinator import MemoryWorkManagement

    store = SQLiteOperationalStore(tmp_path / "offline.sqlite")
    admission = compose_release_admission(store, "offline", "o/r", None, ReleaseAdmissionConfig())
    profile = OfflineProfile(tmp_path / "offline.sqlite", MemoryWorkManagement([]), object(), tmp_path / "a", store=store, release_admission=admission)  # type: ignore[arg-type]

    assert profile.coordinator._release_gate is admission.gate and profile.coordinator._allocation is admission.allocation
    assert admission.records.release_authorization("none") is None
    admission.records.record(ReleaseAuthorization("B", "r", True, "a" * 40))
    assert admission.records.release_authorization("B") == ReleaseAuthorization("B", "r", True, "a" * 40)
