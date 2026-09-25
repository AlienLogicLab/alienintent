"""FX-K2 (WO-220402): canonical multi-role orchestration through the production composition.

Every probe runs ``k2_fixture``: the unchanged coordinator over the production
``RealWorkerProvider`` with its durable journal, and the Deterministic Test
Worker behind the same Worker Port. Faults are injected only at the journal or
process boundary, or by killing the composing process.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.invocation_runtime.adapters.scripted_worker import ScriptedWorkerProcess
from alienintent.invocation_runtime.application.real_worker import RealWorkerProvider
from alienintent.invocation_runtime.domain.runtime import VERDICT_PATH

from tests.execution_coordination.k2_fixture import CRASH_EXIT, ROOT, WORK, compose

PRODUCER, VERIFIER, CLOSURE = "PRODUCER", "VERIFIER", "CLOSURE"


def _held(fixture, stage: LifecycleStage) -> None:
    state = fixture.state()
    assert state.stage is stage and state.outcome == "authority-block"
    assert "DONE" not in fixture.projections()
    _, inbox = fixture.store.read_state(fixture.profile.name, "decision-inbox")
    assert WORK in inbox["open"]


# --- Class 1: producer success advances only to VERIFY ---------------------------


def test_producer_success_advances_only_to_verify(tmp_path: Path) -> None:
    """A published, custodied candidate and a successful producer exit reach VERIFY and no further."""
    fixture = compose(tmp_path, ("success", "no-verdict"))

    summary = fixture.coordinator.start()

    state = fixture.state()
    assert summary.dispatched == (WORK,)
    assert state.stage is LifecycleStage.VERIFY and not state.accepted and state.completed_closure_actions == frozenset()
    assert state.candidate is not None and state.candidate.independent_read_back_proven
    assert fixture.projections() == ["VERIFY", "VERIFY"]
    assert [(role, kind) for role, _, kind in fixture.invocations()] == [(PRODUCER, "success"), (VERIFIER, "verdict-missing")]
    _held(fixture, LifecycleStage.VERIFY)


def test_the_full_lifecycle_is_three_distinct_role_invocations_with_exact_custody(tmp_path: Path) -> None:
    fixture = compose(tmp_path)

    summary = fixture.coordinator.start()

    state = fixture.state()
    assert summary.dispatched == (WORK,) and summary.stop_reason.value == "eligible-backlog-exhausted"
    assert state.stage is LifecycleStage.DONE and state.accepted and state.outcome == "closed"
    assert fixture.projections() == ["VERIFY", "ACCEPT", "DONE"]
    roles = fixture.invocations()
    assert [(role, kind) for role, _, kind in roles] == [(PRODUCER, "success"), (VERIFIER, "accept"), (CLOSURE, "closed")]
    correlations = [correlation for _, correlation, _ in roles]
    assert len(set(correlations)) == 3
    record = state.record
    assert record["producer_correlation"] == correlations[0]
    assert record["verdict"]["verifier_correlation"] == correlations[1] != correlations[0]
    # Every role outcome names the same exact candidate.
    identities = {json.dumps(r["candidate"], sort_keys=True) for r in fixture.journal.records() if r.get("event") == "invocation-outcome"}
    assert len(identities) == 1 and state.candidate.identity == json.loads(identities.pop())["identity"]
    # The verifier evaluated the exact revision in its own fresh checkout.
    revision = state.candidate.locator.rsplit("@", 1)[1]
    verifier_workspace = Path(fixture.worker.verifier_provenance[correlations[1]])
    assert json.loads((verifier_workspace / VERDICT_PATH).read_text())["revision"] == revision
    assert subprocess.run(["git", "rev-parse", "HEAD"], cwd=verifier_workspace, capture_output=True, text=True).stdout.strip() == revision


# --- Class 2: independent verifier rejection returns to IMPLEMENT under budget -----


def test_verifier_rejection_records_findings_and_repairs_through_implement(tmp_path: Path) -> None:
    fixture = compose(tmp_path, ("success", "reject", "success", "accept"))

    summary = fixture.coordinator.start()

    state = fixture.state()
    assert state.stage is LifecycleStage.DONE and state.record["rejections"] == 1
    assert summary.dispatched == (WORK, WORK)
    roles = fixture.invocations()
    assert [(role, kind) for role, _, kind in roles] == [(PRODUCER, "success"), (VERIFIER, "reject"), (PRODUCER, "success"), (VERIFIER, "accept"), (CLOSURE, "closed")]
    [finding] = state.record["findings"]
    rejected = json.loads(json.dumps(next(r["candidate"] for r in fixture.journal.records() if r.get("kind") == "reject")))
    assert finding["source"] == "verifier" and finding["correlation"] == roles[1][1] and finding["candidate"] == rejected["identity"]
    assert finding["findings"] == [f"{WORK}: scripted rejection under {roles[1][1]}"]
    # The repair is a new candidate on its own branch; the rejected one is not what was accepted.
    assert state.candidate.identity != rejected["identity"]
    assert fixture.projections() == ["VERIFY", "IMPLEMENT", "VERIFY", "ACCEPT", "DONE"]


def test_rejection_beyond_the_attempt_budget_is_terminal_failure(tmp_path: Path) -> None:
    """The script could produce and accept again; only the budget stops it."""
    fixture = compose(tmp_path, ("success", "reject", "success", "reject", "success", "accept"))

    summary = fixture.coordinator.start()

    state = fixture.state()
    assert state.outcome == "failure" and state.record["hold_reason"] == "attempt-budget-exhausted"
    assert state.stage is LifecycleStage.IMPLEMENT and not state.accepted and state.candidate is None
    assert summary.dispatched == (WORK, WORK) and summary.failed == (WORK,)
    assert [role for role, _, _ in fixture.invocations()] == [PRODUCER, VERIFIER, PRODUCER, VERIFIER]
    assert len(state.record["findings"]) == 2


def test_a_candidate_that_carries_its_own_verdict_is_not_self_approved(tmp_path: Path) -> None:
    """A producer committing a verdict file cannot stand in for the independent verifier."""
    fixture = compose(tmp_path, ("success", "accept"), note=VERDICT_PATH)

    fixture.coordinator.start()

    assert [(role, kind) for role, _, kind in fixture.invocations()] == [(PRODUCER, "success"), (VERIFIER, "verdict-preexisting")]
    assert [run["role"] for run in fixture.process_runs()] == [PRODUCER]
    _held(fixture, LifecycleStage.VERIFY)


# --- Class 3: acceptance proceeds through REVIEW/ACCEPT; closure records only receipts --


def test_closure_records_only_actions_actually_read_back(tmp_path: Path) -> None:
    """A required action no adapter performed holds at ACCEPT; it is never inferred from success."""
    fixture = compose(tmp_path, closure_actions=("candidate-published", "merged-to-baseline"))

    fixture.coordinator.start()

    state = fixture.state()
    assert state.accepted and state.completed_closure_actions == frozenset()
    assert state.record["hold_reason"] == "closure-receipts-incomplete" and state.record["receipts"] == ["candidate-published"]
    assert fixture.projections() == ["VERIFY", "ACCEPT", "ACCEPT"]
    _held(fixture, LifecycleStage.ACCEPT)


def test_accepted_closure_carries_the_read_back_receipts(tmp_path: Path) -> None:
    fixture = compose(tmp_path)

    fixture.coordinator.start()

    state = fixture.state()
    assert state.stage is LifecycleStage.DONE and state.completed_closure_actions == frozenset({"candidate-published"})
    assert state.record["verdict"]["kind"] == "accept" and state.record["receipts"] == ["candidate-published"]


# --- Class 4: missing, duplicate, stale or miscorrelated evidence holds -----------


class JournalFault:
    """Rewrites the durable outcome record of one role; the process itself succeeds."""

    def __init__(self, role: str, fault: str) -> None:
        self.role, self.fault = role, fault

    def __call__(self, inner):
        role, fault = self.role, self.fault

        class Journal:
            def append(self, record):
                if record.get("event") != "invocation-outcome" or record.get("role") != role:
                    return inner.append(record)
                if fault == "missing":
                    return dict(record)
                if fault == "duplicate":
                    inner.append(record)
                    return inner.append(record)
                if fault == "stale":
                    candidate = dict(record["candidate"])
                    candidate["identity"] = candidate["identity"].replace("launch-K2-PROBE-0", "launch-K2-PROBE-9")
                    return inner.append(record | {"candidate": candidate})
                if fault == "role":
                    return inner.append(record | {"role": PRODUCER})
                if fault == "receipts":
                    return inner.append(record | {"receipts": [*record["receipts"], "merged-to-baseline"]})
                raise AssertionError(fault)

            def records(self):
                return inner.records()

        return Journal()


class StaleVerdict:
    """The verifier process succeeds but leaves a verdict for another revision."""

    def __init__(self, inner: ScriptedWorkerProcess) -> None:
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def run(self, invocation_id, role, workspace, wall_clock_seconds):
        result = self._inner.run(invocation_id, role, workspace, wall_clock_seconds)
        verdict = workspace / VERDICT_PATH
        if verdict.exists():
            verdict.write_text(json.dumps(json.loads(verdict.read_text()) | {"revision": "0" * 40}))
        return result


@pytest.mark.parametrize("fault", ["missing", "duplicate", "stale", "role", "no-verdict", "stale-verdict", "closure-receipts"])
def test_missing_duplicate_stale_or_miscorrelated_role_evidence_holds(tmp_path: Path, fault: str) -> None:
    script, journal, process, stage = ("success", "accept"), None, None, LifecycleStage.VERIFY
    if fault in {"missing", "duplicate", "stale", "role"}:
        journal = JournalFault(VERIFIER, fault)
    elif fault == "no-verdict":
        script = ("success", "no-verdict")
    elif fault == "stale-verdict":
        process = StaleVerdict
    else:
        journal, stage = JournalFault(CLOSURE, "receipts"), LifecycleStage.ACCEPT
    fixture = compose(tmp_path, script, journal=journal, process=process)

    summary = fixture.coordinator.start()

    assert summary.stop_reason.value == "dependencies-or-authority-blocked"
    state = fixture.state()
    assert state.stage is stage and state.completed_closure_actions == frozenset()
    assert all(run["result"] == "success" for run in fixture.process_runs())
    _held(fixture, stage)


def test_restart_after_the_verifier_outcome_recovers_its_role_without_re_running_it(tmp_path: Path) -> None:
    environment = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
    crashed = subprocess.run([sys.executable, "-m", "tests.execution_coordination.k2_fixture", "crash-after-verifier-outcome", "--root", str(tmp_path)],
                             cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
    assert crashed.returncode == CRASH_EXIT, crashed.stderr

    fixture = compose(tmp_path)
    assert fixture.state().stage is LifecycleStage.VERIFY
    [(role, correlation, _)] = [entry for entry in fixture.invocations() if entry[0] == VERIFIER]

    summary = fixture.coordinator.start()

    state = fixture.state()
    assert summary.dispatched == () and state.stage is LifecycleStage.DONE
    assert state.record["verdict"]["verifier_correlation"] == correlation
    assert [r["role"] for r in fixture.process_runs()] == [PRODUCER, VERIFIER]
    assert [role for role, _, _ in fixture.invocations()] == [PRODUCER, VERIFIER, CLOSURE]
    assert fixture.store.recovery_reservations(fixture.profile.name) == () and fixture.store.unresolved_effects(fixture.profile.name) == ()


# --- Class 5: one WorkerProvider boundary, no test shortcut or sidecar owner --------


def test_deterministic_and_real_workers_share_the_production_boundary(tmp_path: Path) -> None:
    fixture = compose(tmp_path)

    fixture.coordinator.start()

    assert type(fixture.worker) is RealWorkerProvider and isinstance(fixture.process, ScriptedWorkerProcess)
    assert fixture.state().stage is LifecycleStage.DONE
    # The scripted process holds no store and writes no lifecycle state.
    assert not hasattr(fixture.process, "_store") and not hasattr(fixture.worker, "_store")
    journals = [*fixture.journal.records(), *fixture.process_runs()]
    assert journals and not any("stage" in entry or "lifecycle" in entry or "accepted" in entry for entry in journals)
    # Execution truth has one owner: the coordinator's execution aggregates.
    aggregates = sorted(identity for identity, _, _ in fixture.store.list_states(fixture.profile.name, ""))
    assert aggregates == ["decision-inbox", f"factory:{WORK}"] or aggregates == [f"factory:{WORK}"]


def test_no_parallel_role_outcome_state_owner_exists_in_source() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "src").rglob("*.py"))
    assert not re.search(r"\bRoleOutcomeRecord\b", source)


def test_restart_after_a_recorded_rejection_recovers_without_wedging_the_profile(tmp_path: Path) -> None:
    """The rework clears the candidate; recovery must still correlate the verifier invocation it made."""
    fixture = compose(tmp_path, ("success", "reject"))
    release = fixture.store.release

    def crash_on_verifier_release(profile, scope, key, owner, fence):
        if owner != "launch:K2-PROBE:0":
            raise RuntimeError("simulated crash before the verifier reservation is released")
        return release(profile, scope, key, owner, fence)

    fixture.store.release = crash_on_verifier_release  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="simulated crash"):
        fixture.coordinator.start()
    assert fixture.state().stage is LifecycleStage.IMPLEMENT and fixture.store.recovery_reservations(fixture.profile.name) != ()

    reopened = compose(tmp_path, ("success", "accept"))
    summary = reopened.coordinator.start()

    assert summary.stop_reason.value == "eligible-backlog-exhausted" and summary.dispatched == (WORK,)
    state = reopened.state()
    assert state.stage is LifecycleStage.DONE and state.record["rejections"] == 1
    assert reopened.store.recovery_reservations(reopened.profile.name) == ()
