"""Executable proof for the S0 local Work Management transport."""

from __future__ import annotations

from pathlib import Path

import pytest

from alienintent.execution_coordination.adapters.local_work_management import LocalWorkManagement
from alienintent.execution_coordination.domain.escalation import HumanDecisionRequired
from alienintent.execution_coordination.domain.lifecycle import LifecycleStage
from alienintent.execution_coordination.ports.work_management import ReadyWorkItem, WorkRejected
from tests.execution_coordination.domain.test_contract import valid_contract

EPOCH = 1758542400.0
CLOCK = lambda: EPOCH  # noqa: E731


def item(identity: str, fifo: int = 0) -> ReadyWorkItem:
    contract = valid_contract(identity=identity)
    return ReadyWorkItem(identity, fifo, "local:test", "fx", 1, (), contract, contract.content_digest, "seeded")


def test_receipts_are_appended_read_back_and_stamped_with_the_injected_clock(tmp_path: Path) -> None:
    work = LocalWorkManagement(tmp_path / "wm", "fx", "local:test", [item("a")], CLOCK)

    work.propose_release(item("a"))
    receipt = work.project_execution_state("a", LifecycleStage.DONE, 5)

    assert (receipt.identity, receipt.revision, receipt.confirmed) == ("a", 5, True)
    receipts = work.receipts()
    assert [(entry["receipt"], entry.get("state")) for entry in receipts] == [("release-proposed", None), ("execution-state-projected", "DONE")]
    assert {entry["at"] for entry in receipts} == {EPOCH}
    assert [entry["sequence"] for entry in receipts] == [0, 1]
    assert work.seed_path.exists() and not work.reopened


def test_reopening_the_same_root_with_the_same_seed_keeps_receipts_and_refuses_a_different_seed(tmp_path: Path) -> None:
    first = LocalWorkManagement(tmp_path / "wm", "fx", "local:test", [item("a")], CLOCK)
    first.propose_release(item("a"))

    reopened = LocalWorkManagement(tmp_path / "wm", "fx", "local:test", [item("a")], CLOCK)
    assert reopened.reopened and len(reopened.receipts()) == 1
    assert reopened.import_ready_snapshot() == (item("a"),)

    with pytest.raises(WorkRejected, match="different work"):
        LocalWorkManagement(tmp_path / "wm", "fx", "local:test", [item("b")], CLOCK)


def test_the_local_project_names_every_lifecycle_stage_and_no_priority_options(tmp_path: Path) -> None:
    schema = LocalWorkManagement(tmp_path / "wm", "fx", "local:test", [item("a")], CLOCK).resolve_project()

    assert schema.project_id == "local:fx"
    assert set(schema.status_options) == {stage.value for stage in LifecycleStage}
    assert schema.priority_options == {}


def test_a_decision_request_is_recorded_as_a_confirmed_receipt(tmp_path: Path) -> None:
    work = LocalWorkManagement(tmp_path / "wm", "fx", "local:test", [item("a")], CLOCK)
    escalation = HumanDecisionRequired("fx", "local:test", "a", 2, "decide", "because", ("authorize", "defer"), ("t1", "t2"), "defer", ("SF-REQ-039",), ("FD-05",), "waiting", ("auth",))

    receipt = work.project_decision_request(escalation)

    assert (receipt.identity, receipt.revision, receipt.confirmed) == ("a", 2, True)
    assert work.receipts()[-1]["receipt"] == "decision-requested"
