"""FX-K3 (WO-220403): shared-profile role binding and compatibility, proven offline.

Every probe composes an *actual* shared-profile constructor from
``k3_fixture`` - ``SandboxRunProfile`` or ``GitHubProfileComposition`` - over
local transports, a real child worker, real Git worktrees and a local bare
remote. Faults are injected only at the grant issuer, the durable journal,
the execution store, or by killing the composing process.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.composition.role_binding import BINDING_REFUSED, RoleBindingGuard
from alienintent.composition.sandbox_run_profile import SandboxRunProfile
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.worker_provider import MISSING_TERMINAL_RESULT, WorkerInvocation
from alienintent.invocation_runtime.application.real_worker import decode_candidate
from alienintent.invocation_runtime.domain.runtime import CapabilityGrant, InvocationRole

from tests.composition.k3_fixture import (
    CRASH_EXIT, GH_WORK, ROOT, SANDBOX_WORK, advertised, github, journaled, runs, sandbox,
)

PRODUCER_0 = f"launch:{SANDBOX_WORK}:0"


def outcomes(journal_path: Path) -> list[tuple[str, str, str]]:
    return [(str(r["role"]), str(r["correlation_id"]), str(r["kind"])) for r in journaled(journal_path)]


def _held_before_launch(state, refusals: dict[str, str], correlation: str, reason: str) -> None:
    assert state.outcome == "authority-block"
    assert refusals == {correlation: reason}


# --- class 1: refusal before launch -------------------------------------------


class ProducerOnlyGrants(SandboxRunProfile):
    """The pre-K3 issuer: every dispatch is granted as PRODUCER, whatever role it plays."""

    def grant(self, invocation: WorkerInvocation) -> CapabilityGrant:
        return CapabilityGrant(f"py10-{invocation.work_identity}", "1", invocation.correlation_id, InvocationRole.PRODUCER,
                               self.name, self.composition.profile.repository, frozenset({"process-control", "git-write"}), 9999999999)


def test_sandbox_profile_refuses_a_verifier_launch_whose_grant_names_another_role(tmp_path: Path) -> None:
    profile = sandbox(tmp_path, profile_class=ProducerOnlyGrants)

    profile.coordinator.start()

    state = profile.coordinator.state(SANDBOX_WORK)
    assert state.stage is LifecycleStage.VERIFY
    [verifier] = list(profile.worker.refusals)
    _held_before_launch(state, profile.worker.refusals, verifier, "role-authority-miscorrelated")
    # The producer ran under its own role; the verifier never launched or journaled.
    assert runs(tmp_path) == [("PRODUCER", PRODUCER_0)]
    assert [record["correlation_id"] for record in journaled(profile.journal.path, "invocation-started")] == [PRODUCER_0]


def test_sandbox_profile_refuses_a_verifier_given_a_candidate_the_producer_never_published(tmp_path: Path) -> None:
    profile = sandbox(tmp_path)
    project = profile.work.project_execution_state

    def forge_custody_at_verify(identity, stage, revision=0):
        # A custody record that no longer names what the producer durably published.
        if stage == LifecycleStage.VERIFY:
            version, raw = profile.store.read_state(profile.name, f"factory:{identity}")
            candidate = dict(raw["candidate"])
            forged = "sha256:" + "f" * 64
            candidate["identity"] = str(candidate["identity"]).replace(str(candidate["content_digest"]), forged)
            candidate["content_digest"] = forged
            profile.store.commit(profile.name, f"factory:{identity}", version, raw | {"candidate": candidate})
        return project(identity, stage, revision)

    profile.work.project_execution_state = forge_custody_at_verify  # type: ignore[method-assign]
    profile.coordinator.start()

    state = profile.coordinator.state(SANDBOX_WORK)
    [verifier] = list(profile.worker.refusals)
    assert state.stage is LifecycleStage.VERIFY
    _held_before_launch(state, profile.worker.refusals, verifier, "candidate-custody-unattributable")
    assert runs(tmp_path) == [("PRODUCER", PRODUCER_0)]


@pytest.mark.parametrize("binding", ["missing", "disconnected"])
def test_github_profile_refuses_an_unbound_or_disconnected_worker_before_launch(tmp_path: Path, binding: str) -> None:
    composed = github(tmp_path, binding=binding)

    summary = composed.coordinator.start()

    state = composed.coordinator.state(GH_WORK)
    assert summary.dispatched == () and state.stage is LifecycleStage.IMPLEMENT
    _held_before_launch(state, composed.worker.refusals, f"launch:{GH_WORK}:0", f"durable-outcome-binding-{binding}")
    # Nothing ran, nothing was published, nothing was journaled anywhere.
    assert runs(tmp_path) == [] and advertised(tmp_path) == []
    assert journaled(tmp_path / "invocation-journal.jsonl", "invocation-started") == []
    assert journaled(tmp_path / "elsewhere-journal.jsonl", "invocation-started") == []


# --- class 2: correlated success, rejection and restart read-back -------------


def _drained(coordinator, work: str, journal_path: Path) -> list[tuple[str, str, str]]:
    state = coordinator.state(work)
    assert state.stage is LifecycleStage.DONE and state.outcome == "closed"
    observed = outcomes(journal_path)
    producer = [record for record in journaled(journal_path) if record["role"] == "PRODUCER" and record["kind"] == "success"][-1]
    assert state.candidate.identity == decode_candidate(producer["candidate"]).identity
    return observed


@pytest.mark.parametrize("constructor", ["sandbox", "github"])
def test_bound_profiles_reach_correlated_success_through_every_role(tmp_path: Path, constructor: str) -> None:
    composed = sandbox(tmp_path) if constructor == "sandbox" else github(tmp_path)
    work = SANDBOX_WORK if constructor == "sandbox" else GH_WORK
    journal_path = tmp_path / ("state/invocation-journal.jsonl" if constructor == "sandbox" else "invocation-journal.jsonl")

    composed.coordinator.start()

    observed = _drained(composed.coordinator, work, journal_path)
    assert [(role, kind) for role, _, kind in observed] == [("PRODUCER", "success"), ("VERIFIER", "accept"), ("CLOSURE", "closed")]
    assert len({correlation for _, correlation, _ in observed}) == 3
    assert [role for role, _ in runs(tmp_path)] == ["PRODUCER", "VERIFIER"]
    assert composed.worker.refusals == {} and composed.worker.retained == {}


def test_bound_sandbox_profile_reads_back_a_rejection_and_repairs_through_implement(tmp_path: Path) -> None:
    profile = sandbox(tmp_path, maximum_attempts=2)
    (tmp_path / "worker-tmp" / "reject-once").touch()

    profile.coordinator.start()

    observed = _drained(profile.coordinator, SANDBOX_WORK, profile.journal.path)
    assert [(role, kind) for role, _, kind in observed] == [
        ("PRODUCER", "success"), ("VERIFIER", "reject"), ("PRODUCER", "success"), ("VERIFIER", "accept"), ("CLOSURE", "closed"),
    ]
    _, raw = profile.store.read_state(profile.name, f"factory:{SANDBOX_WORK}")
    [finding] = raw["findings"]
    assert finding["source"] == "verifier" and finding["correlation"] == observed[1][1]
    assert finding["findings"] == ["FX-K3: first candidate rejected"] and raw["rejections"] == 1


def _crash(root: Path, mode: str) -> None:
    environment = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
    crashed = subprocess.run([sys.executable, "-m", "tests.composition.k3_fixture", mode, "--root", str(root)],
                             cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
    assert crashed.returncode == CRASH_EXIT, crashed.stdout + crashed.stderr


def test_bound_sandbox_profile_recovers_the_verifier_outcome_after_a_crash_without_re_running_it(tmp_path: Path) -> None:
    _crash(tmp_path, "crash-after-verifier-outcome")
    assert [role for role, _ in runs(tmp_path)] == ["PRODUCER", "VERIFIER"]

    restarted = sandbox(tmp_path)
    restarted.coordinator.start()

    observed = _drained(restarted.coordinator, SANDBOX_WORK, restarted.journal.path)
    assert [(role, kind) for role, _, kind in observed] == [("PRODUCER", "success"), ("VERIFIER", "accept"), ("CLOSURE", "closed")]
    assert [role for role, _ in runs(tmp_path)] == ["PRODUCER", "VERIFIER"]
    assert restarted.store.unresolved_effects(restarted.name) == () and restarted.worker.refusals == {}


# --- class 3: the guard cannot be bypassed ------------------------------------


def test_every_shared_profile_coordinator_reaches_its_worker_only_through_the_binding_guard(tmp_path: Path) -> None:
    profile = sandbox(tmp_path / "sandbox")
    composed = github(tmp_path / "github")

    for guard, coordinator in ((profile.worker, profile.coordinator), (composed.worker, composed.coordinator)):
        assert isinstance(guard, RoleBindingGuard) and coordinator._worker is guard
    assert profile.worker.provider is profile.real_worker and profile.real_worker.journal is profile.journal


# --- class 4: no sidecar owner, no activation ---------------------------------


def test_the_binding_guard_owns_no_state_and_introduces_no_outcome_record(tmp_path: Path) -> None:
    source = (ROOT / "src/alienintent/composition/role_binding.py").read_text()
    for forbidden in (".commit(", "commit_with_effect", "sqlite", "CREATE TABLE", "RoleOutcomeRecord", "OutcomeEvidencePort", "open("):
        assert forbidden not in source, forbidden

    profile = sandbox(tmp_path)
    profile.coordinator.start()

    aggregates = {identity for identity, _, _ in profile.store.list_states(profile.name)}
    assert all(identity.startswith(("factory:", "release:", "scheduler:", "decision-inbox")) for identity in aggregates), aggregates
    assert {record["event"] for record in journaled(profile.journal.path, "invocation-started") + journaled(profile.journal.path)} == {
        "invocation-started", "invocation-outcome"}


# --- class 5: owned background work keeps the invocation ----------------------


def test_client_exit_with_owned_background_work_active_does_not_end_the_invocation(tmp_path: Path) -> None:
    profile = sandbox(tmp_path)
    (tmp_path / "worker-tmp" / "background").touch()

    profile.coordinator.start()

    observed = _drained(profile.coordinator, SANDBOX_WORK, profile.journal.path)
    assert [(role, kind) for role, _, kind in observed][0] == ("PRODUCER", "success")
    revision = profile.coordinator.state(SANDBOX_WORK).candidate.locator.rsplit("@", 1)[1]
    shown = subprocess.run(["git", "--git-dir", str(tmp_path / "remote.git"), "show", f"{revision}:docs/{SANDBOX_WORK}-background.md"],
                           capture_output=True, text=True, check=False)
    assert shown.returncode == 0 and PRODUCER_0 in shown.stdout, "the candidate was taken before owned background work finished"


# --- class 6: deterministic recovery and replacement --------------------------


def _drop_producer_outcomes(profile: SandboxRunProfile, *, times: int, limit: int) -> None:
    """The worker exits, but its own durable result never lands; retained outcomes still do."""
    append = profile.journal.append
    dropped: list[str] = []
    started: list[str] = []

    def lossy(record):
        if record.get("event") == "invocation-started" and record.get("role") == "PRODUCER":
            started.append(str(record["correlation_id"]))
            assert len(started) <= limit, "unbounded replacement launch"
        if record.get("event") == "invocation-outcome" and record.get("role") == "PRODUCER" and record.get("kind") != MISSING_TERMINAL_RESULT and len(dropped) < times:
            dropped.append(str(record["correlation_id"]))
            return dict(record)
        return append(record)

    profile.journal.append = lossy  # type: ignore[method-assign]


def test_conclusive_loss_without_a_durable_result_is_retained_and_replaced_exactly_once(tmp_path: Path) -> None:
    profile = sandbox(tmp_path)
    _drop_producer_outcomes(profile, times=1, limit=2)

    profile.coordinator.start()

    observed = _drained(profile.coordinator, SANDBOX_WORK, profile.journal.path)
    producers = [(correlation, kind) for role, correlation, kind in observed if role == "PRODUCER"]
    assert producers[0] == (PRODUCER_0, MISSING_TERMINAL_RESULT) and producers[1][1] == "success" and len(producers) == 2
    [retained] = [record for record in journaled(profile.journal.path) if record["kind"] == MISSING_TERMINAL_RESULT]
    assert retained["ownership"] == "already-finished" and retained["phase"] == f"{SANDBOX_WORK}|PRODUCER|"
    assert [correlation for role, correlation in runs(tmp_path) if role == "PRODUCER"] == [PRODUCER_0, producers[1][0]]
    assert profile.worker.retained == {PRODUCER_0: "already-finished"}
    _, inbox = profile.store.read_state(profile.name, "decision-inbox")
    assert not inbox.get("open")


def test_a_second_loss_in_the_same_phase_is_refused_at_launch_and_held(tmp_path: Path) -> None:
    profile = sandbox(tmp_path)
    _drop_producer_outcomes(profile, times=2, limit=2)

    profile.coordinator.start()

    state = profile.coordinator.state(SANDBOX_WORK)
    assert state.stage is LifecycleStage.IMPLEMENT
    assert [kind for role, _, kind in outcomes(profile.journal.path)] == [MISSING_TERMINAL_RESULT, MISSING_TERMINAL_RESULT]
    assert [role for role, _ in runs(tmp_path)] == ["PRODUCER", "PRODUCER"]
    [third] = list(profile.worker.refusals)
    _held_before_launch(state, profile.worker.refusals, third, "replacement-allowance-exhausted")


def test_no_replacement_launches_while_ownership_is_unknown_after_the_owner_died(tmp_path: Path) -> None:
    _crash(tmp_path, "crash-before-producer-outcome")
    assert runs(tmp_path) == [("PRODUCER", PRODUCER_0)]

    restarted = sandbox(tmp_path)
    restarted.coordinator.start()

    state = restarted.coordinator.state(SANDBOX_WORK)
    assert runs(tmp_path) == [("PRODUCER", PRODUCER_0)]
    assert state.stage is LifecycleStage.IMPLEMENT and state.outcome == "authority-block"
    assert journaled(restarted.journal.path) == [] and restarted.worker.retained == {}
    assert [effect.identity for effect in restarted.store.unresolved_effects(restarted.name)] == [PRODUCER_0]


def test_a_refused_launch_journals_nothing_and_reads_back_nothing(tmp_path: Path) -> None:
    composed = github(tmp_path, binding="disconnected")
    invocation = WorkerInvocation(GH_WORK, f"launch:{GH_WORK}:0", None)

    assert composed.worker.start(invocation, None, frozenset(), None).kind == BINDING_REFUSED  # type: ignore[arg-type]
    assert composed.worker.read_back(invocation) is None


def test_a_raising_owning_call_leaves_its_effects_unknown_and_is_never_replaced(tmp_path: Path) -> None:
    """The provider raised after its process exited: what it did afterwards (a push) is unknown, so nothing replaces it."""
    profile = sandbox(tmp_path)
    append = profile.journal.append

    def failing(record):
        if record.get("event") == "invocation-outcome" and record.get("role") == "PRODUCER":
            raise RuntimeError("durable outcome append failed after the process exited")
        return append(record)

    profile.journal.append = failing  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="durable outcome append failed"):
        profile.coordinator.start()
    profile.journal.append = append  # type: ignore[method-assign]
    profile.coordinator.start()

    state = profile.coordinator.state(SANDBOX_WORK)
    assert runs(tmp_path) == [("PRODUCER", PRODUCER_0)], "a replacement launched over an unknown effect"
    assert state.stage is LifecycleStage.IMPLEMENT and state.outcome == "authority-block"
    assert journaled(profile.journal.path) == [] and profile.worker.retained == {}


def test_a_conclusively_lost_verifier_result_re_dispatches_the_verifier_on_the_same_candidate(tmp_path: Path) -> None:
    profile = sandbox(tmp_path)
    append = profile.journal.append
    dropped: list[str] = []

    def lossy(record):
        if record.get("event") == "invocation-outcome" and record.get("role") == "VERIFIER" and record.get("kind") != MISSING_TERMINAL_RESULT and not dropped:
            dropped.append(str(record["correlation_id"]))
            return dict(record)
        return append(record)

    profile.journal.append = lossy  # type: ignore[method-assign]
    profile.coordinator.start()

    state = profile.coordinator.state(SANDBOX_WORK)
    assert state.stage is LifecycleStage.DONE, (state.stage, state.outcome)
    verifiers = [(correlation, kind) for role, correlation, kind in outcomes(profile.journal.path) if role == "VERIFIER"]
    assert [kind for _, kind in verifiers] == [MISSING_TERMINAL_RESULT, "accept"] and verifiers[0][0] == dropped[0]
    started = [r for r in journaled(profile.journal.path, "invocation-started") if r["role"] == "VERIFIER"]
    assert len(started) == 2 and [role for role, _ in runs(tmp_path)] == ["PRODUCER", "VERIFIER", "VERIFIER"]
