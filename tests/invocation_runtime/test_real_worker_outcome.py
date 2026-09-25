"""FX-K1 (WO-220401): durable, correlated outcome read-back on the real WorkerProvider path.

Every probe runs the production composition in ``k1_fixture``: the unchanged
coordinator over ``RealWorkerProvider`` with a real child process, a local
bare remote and the durable invocation journal. Faults are injected only at
the journal boundary or by killing the composing process.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation, WorkerOutcome
from alienintent.invocation_runtime.application.real_worker import decode_candidate

from tests.invocation_runtime.k1_fixture import CRASH_EXIT, ROOT, WORK, compose

CORRELATION = f"launch:{WORK}:0"
BRANCH = "candidate/launch-K1-PROBE-0"


def test_real_path_durably_retains_attributable_outcome_and_reads_it_back_after_restart(tmp_path: Path) -> None:
    """Class 1: role, invocation, attempt, contract and exact candidate survive a rebuild of every object."""
    fixture = compose(tmp_path)

    summary = fixture.coordinator.start()

    assert summary.dispatched == (WORK,)
    state = fixture.coordinator.state(WORK)
    assert state.stage is LifecycleStage.DONE and state.outcome == "closed"
    [record] = fixture.outcome_records()
    revision = fixture.remote_advertises(BRANCH)
    assert revision is not None and fixture.runs() == [CORRELATION]
    assert {key: record[key] for key in ("correlation_id", "work_identity", "role", "attempt", "contract_digest", "kind")} == {
        "correlation_id": CORRELATION, "work_identity": WORK, "role": "PRODUCER", "attempt": 1,
        "contract_digest": fixture.item.contract.content_digest, "kind": "success",
    }
    candidate = decode_candidate(record["candidate"])
    assert candidate.locator.endswith(f"#{BRANCH}@{revision}")
    assert state.candidate.identity == candidate.identity

    reopened = compose(tmp_path)
    invocation = WorkerInvocation(WORK, CORRELATION, fixture.item.contract.content_digest)
    assert reopened.worker.read_back(invocation) == WorkerOutcome.success(candidate)


class DropOutcome:
    """The process succeeds, but its outcome never becomes durable."""

    def __init__(self, inner) -> None:
        self._inner = inner

    def append(self, record):
        if record.get("event") == "invocation-outcome":
            return dict(record)
        return self._inner.append(record)

    def records(self):
        return self._inner.records()


def _assert_held(fixture) -> None:
    state = fixture.coordinator.state(WORK)
    assert state.stage is LifecycleStage.IMPLEMENT and state.candidate is None
    assert state.outcome == "authority-block"
    assert [effect.identity for effect in fixture.store.unresolved_effects(fixture.profile.name)] == [CORRELATION]
    _, inbox = fixture.store.read_state(fixture.profile.name, "decision-inbox")
    assert WORK in inbox["open"]


def test_process_success_without_a_durable_result_holds_the_transition(tmp_path: Path) -> None:
    """Class 2: a successful exit and a published candidate do not advance the lifecycle on their own."""
    fixture = compose(tmp_path, journal=DropOutcome)

    summary = fixture.coordinator.start()

    assert summary.dispatched == () and summary.stop_reason.value == "dependencies-or-authority-blocked"
    assert fixture.runs() == [CORRELATION] and fixture.remote_advertises(BRANCH) is not None
    assert fixture.outcome_records() == []
    _assert_held(fixture)


def _rewrite(record: dict[str, object], field: str) -> dict[str, object]:
    if field == "candidate":
        candidate = dict(record["candidate"])
        candidate["locator"] = candidate["locator"].replace(f"#{BRANCH}@", "#candidate/elsewhere@")
        return record | {"candidate": candidate}
    return record | {field: {"role": "VERIFIER", "work_identity": "OTHER-WORK", "contract_digest": "sha256:" + "0" * 64}[field]}


class Miscorrelate:
    def __init__(self, field: str):
        self.field = field

    def __call__(self, inner):
        field = self.field

        class Journal:
            def append(self, record):
                if record.get("event") != "invocation-outcome":
                    return inner.append(record)
                if field == "duplicate":
                    inner.append(record)
                    return inner.append(record)
                return inner.append(_rewrite(dict(record), field))

            def records(self):
                return inner.records()

        return Journal()


@pytest.mark.parametrize("field", ["role", "work_identity", "contract_digest", "candidate", "duplicate"])
def test_miscorrelated_durable_result_holds_rather_than_being_accepted(tmp_path: Path, field: str) -> None:
    """Class 3: a durable record naming another role, work item, contract or candidate branch, or two records, is not this result."""
    fixture = compose(tmp_path, journal=Miscorrelate(field))

    summary = fixture.coordinator.start()

    assert summary.dispatched == ()
    # Every outcome record, whatever role it (mis)names: the lifecycle held, so no other role ran.
    assert fixture.runs() == [CORRELATION] and len(fixture.outcome_records(None)) == (2 if field == "duplicate" else 1)
    _assert_held(fixture)


def test_restart_after_crash_reads_back_the_original_identity_without_duplicating_the_result(tmp_path: Path) -> None:
    """Class 4: a composing process killed after the durable outcome recovers it once, under its original correlation."""
    environment = os.environ | {"PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
    crashed = subprocess.run([sys.executable, "-m", "tests.invocation_runtime.k1_fixture", "crash-after-outcome", "--root", str(tmp_path)],
                             cwd=ROOT, env=environment, capture_output=True, text=True, check=False)
    assert crashed.returncode == CRASH_EXIT, crashed.stderr

    fixture = compose(tmp_path)
    [record] = fixture.outcome_records()
    assert fixture.runs() == [CORRELATION]
    assert fixture.coordinator.state(WORK).stage is LifecycleStage.IMPLEMENT
    assert [effect.identity for effect in fixture.store.unresolved_effects(fixture.profile.name)] == [CORRELATION]

    summary = fixture.coordinator.start()

    assert summary.dispatched == ()
    state = fixture.coordinator.state(WORK)
    assert state.stage is LifecycleStage.DONE and state.outcome == "closed"
    assert state.candidate.identity == decode_candidate(record["candidate"]).identity
    _, raw = fixture.store.read_state(fixture.profile.name, f"factory:{WORK}")
    assert raw["producer_correlation"] == CORRELATION
    assert fixture.runs() == [CORRELATION] and len(fixture.outcome_records()) == 1
    assert fixture.store.unresolved_effects(fixture.profile.name) == ()
    assert fixture.store.recovery_reservations(fixture.profile.name) == ()

    version, _ = fixture.store.read_state(fixture.profile.name, f"factory:{WORK}")
    again = compose(tmp_path)
    assert again.coordinator.start().dispatched == ()
    assert again.store.read_state(again.profile.name, f"factory:{WORK}")[0] == version
    assert again.runs() == [CORRELATION] and len(again.outcome_records()) == 1


@pytest.mark.parametrize("field", ["role", "candidate"])
def test_restart_read_back_holds_on_a_miscorrelated_record(tmp_path: Path, field: str) -> None:
    """Class 3 on the restart path: with no in-memory outcome to compare, the durable record alone must correlate."""
    import json

    fixture = compose(tmp_path)
    assert fixture.coordinator.start().dispatched == (WORK,)
    path = fixture.journal.path
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    path.write_text("".join(json.dumps(_rewrite(line, field) if line.get("event") == "invocation-outcome" and line.get("role") == "PRODUCER" else line) + "\n" for line in lines), encoding="utf-8")

    reopened = compose(tmp_path)

    assert reopened.worker.read_back(WorkerInvocation(WORK, CORRELATION, fixture.item.contract.content_digest)) is None


def test_ineligible_outcome_reads_back_without_a_journal(tmp_path: Path) -> None:
    """An in-memory provider must read back every outcome it returned, or the coordinator parks a plain refusal."""
    from alienintent.execution_coordination.domain.contract import BudgetPolicy

    fixture = compose(tmp_path, journal=lambda _: None)
    invocation = WorkerInvocation(WORK, CORRELATION)

    outcome = fixture.worker.start(invocation, None, frozenset(), BudgetPolicy())

    assert outcome.kind == "ineligible" and fixture.worker.read_back(invocation) == outcome
