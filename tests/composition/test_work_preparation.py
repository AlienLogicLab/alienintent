"""Work Preparation's `prepare_next` (WORK-PREPARATION-REFILL R3a, spec 3.3-3.5; WPR-A2) on the composed registry over
a fixture project, with a fake PREPARER. Plans, packets and answers are TEST DATA."""
from __future__ import annotations

import json

import pytest

from alienintent.composition.work_preparation import (
    IN_PROGRESS, NOTHING, REFUSED, RELEASED, STOPPED, WorkPreparation)
from alienintent.context_assembly.domain.preparation import PENDING
from alienintent.execution_coordination.domain.plan_authority import PLAN_PATH
from tests.composition.test_work_registry import PlanBoard
from tests.context_assembly.test_initial_compilation import git
from tests.context_assembly.test_work_contract import satisfiable_payload

PACKETS = "alienintent/work-packets"


@pytest.fixture
def board(tmp_path) -> PlanBoard:
    board = PlanBoard(tmp_path / "fx")
    board.digest = board.approve()
    git(board.clone, "push", "-q", "origin", f"main:refs/heads/{PACKETS}")  # the packets branch, as in production
    return board


def packet(board, *, scope=("src/alienintent/composition/fixture.py",), satisfies=("FIXTURE-A1",)) -> str:
    payload = satisfiable_payload(PENDING, release_policy="automatic-on",
                                  authority_issuer="plan-authority:" + board.digest,
                                  authority_references=[f"{PLAN_PATH} obligation:FIXTURE"],
                                  authorized_scope=list(scope))
    proof = {"targeted_tests": ["tests/composition/test_fixture.py"]}
    return (f"# Work unit: prepared for FIXTURE\n\n```json alienintent-contract\n{json.dumps(payload, indent=1)}\n"
            f"```\n\n```json alienintent-acceptance\n{json.dumps({'satisfies': list(satisfies)})}\n```\n\n"
            f"```json alienintent-proof\n{json.dumps(proof)}\n```\n")


class Preparer:
    """A fake PREPARER answering from `answers` in order; it records each context package it was given."""

    def __init__(self, *answers) -> None:
        self.answers, self.contexts = list(answers), []

    def __call__(self, context: dict) -> dict:
        self.contexts.append(context)
        answer = self.answers.pop(0)
        return answer(context) if callable(answer) else answer


def service(board, preparer) -> WorkPreparation:
    return WorkPreparation(board.loaded(), preparer)


def test_a_valid_packet_is_committed_registered_bound_assessed_and_released_with_provenance(board):
    preparer = Preparer({"answer": "PACKET", "packet": packet(board)})
    result = service(board, preparer).prepare_next()
    assert (result.answer, result.obligation) == (RELEASED, "FIXTURE")
    registry = board.loaded()
    item = registry.identities.find(result.identity)
    assert item.label.startswith("FIXTURE-") and item.label.endswith("-1") and item.state == "CAPTURE"
    record = registry.records.show(item.id)
    assert f'"identity": "{item.id}"' in record.packet.decode() and PENDING not in record.packet.decode()
    assert git(board.root / "remote.git", "merge-base", "--is-ancestor", item.pointer.commit,
               f"refs/heads/{PACKETS}").decode() == ""
    release = registry.assessment.authorizations.release_authorization(item.id)
    assert release.text.startswith("inherited from plan authority " + board.digest)
    context = preparer.contexts[0]
    assert (context["plan"]["content_digest"], context["obligation"]["label"]) == (board.digest, "FIXTURE")
    assert context["identity"] == PENDING and context["budget"] == {"runs": 1, "limit": 3}


def test_a_refused_packet_writes_nothing_and_uses_one_run(board):
    before = board.loaded().identities.packet_items()
    preparer = Preparer({"answer": "PACKET", "packet": packet(board, scope=("outside/x.py",))})
    result = service(board, preparer).prepare_next()
    assert result.answer == REFUSED and "authorized_scope" in result.detail
    assert board.loaded().identities.packet_items() == before


def test_a_preparer_hold_stops_the_obligation_and_it_is_not_prepared_again(board):
    preparer = Preparer({"answer": "HOLD", "reason": "the obligation names no testable behaviour"})
    result = service(board, preparer).prepare_next()
    assert (result.answer, result.obligation) == (STOPPED, "FIXTURE") and "preparer-hold" in result.detail
    again = Preparer()
    assert service(board, again).prepare_next().answer == NOTHING and again.contexts == []


def test_an_agent_ready_clarify_gets_one_preparer_revision_of_the_same_item(board):
    def revise(context):
        assert context["findings"] and context["identity"] == PENDING and context["work_item"]  # the same item
        board.answer.write_text("READY")
        return {"answer": "PACKET", "packet": packet(board) + "\nRevised: the acceptance check names its test.\n"}
    board.answer.write_text("CLARIFY")
    preparer = Preparer({"answer": "PACKET", "packet": packet(board)}, revise)
    result = service(board, preparer).prepare_next()
    assert result.answer == RELEASED and len(preparer.contexts) == 2
    prepared = [i.label for i in board.loaded().identities.packet_items() if i.label.startswith("FIXTURE-")]
    assert len(prepared) == 1 and prepared[0].endswith("-1")


def test_three_refused_packets_exhaust_the_obligation_budget_and_stop_it(board):
    refused = {"answer": "PACKET", "packet": packet(board, satisfies=("OTHER-A1",))}
    for expected in (REFUSED, REFUSED, REFUSED):
        assert service(board, Preparer(refused)).prepare_next().answer == expected
    result = service(board, Preparer()).prepare_next()
    assert result.answer == STOPPED and "budget-exhausted" in result.detail


def test_while_a_derived_item_is_live_nothing_is_prepared(board):
    assert service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next().answer == RELEASED
    idle = Preparer()
    assert service(board, idle).prepare_next().answer == IN_PROGRESS and idle.contexts == []


def test_the_next_item_of_an_obligation_is_a_new_work_item_with_its_own_identity(board):
    """The first released item is retired unfinished, so the obligation is eligible again: its next item is a new
    Work Item, never a re-bind of the earlier one."""
    first = service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next()
    board.loaded().identities.retire(first.identity)
    second = service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next()
    assert second.answer == RELEASED and second.identity != first.identity
    assert board.loaded().identities.find(second.identity).label.endswith("-2")


def test_the_preparer_session_gets_its_instructions_on_stdin_and_its_result_is_read_back(board, tmp_path, monkeypatch):
    """The production runner (no worker user: a development profile): the PREPARER route's provider command runs in a
    detached clone of canonical main with the instructions on standard input; the one result file it names is read
    back, and the clone is removed."""
    import sys
    from alienintent.composition.work_preparation import WorkerPreparer
    fake = tmp_path / "fake-codex"
    fake.write_text(f"""#!{sys.executable}
import json, os, re, sys
text = sys.stdin.read()
result = re.search(r"Write exactly one JSON file to this path and nothing else:\\n(\\S+)", text).group(1)
label = json.loads(text.split("Context package:\\n", 1)[1])["obligation"]["label"]
reason = "cwd " + os.path.basename(os.getcwd()) + " obligation " + label
open(result, "w").write(json.dumps({{"answer": "HOLD", "reason": reason}}))
""")
    fake.chmod(0o755)
    routing = tmp_path / "routing.json"
    routing.write_text(json.dumps({"schemaVersion": 1, "default": {"provider": "codex", "model": "m"},
                                   "providers": {"codex": {"executable": str(fake), "permissionMode": "read-only"},
                                                 "claude": {"executable": str(fake), "permissionMode": "plan"}},
                                   "roles": {}}))
    monkeypatch.setenv("ALIENINTENT_MODEL_ROUTING", str(routing))
    answer = WorkerPreparer(board.loaded())({"obligation": {"label": "FIXTURE"}})
    assert answer["answer"] == "HOLD" and answer["reason"].startswith("cwd prepare-")
    assert answer["reason"].endswith("obligation FIXTURE")
    assert git(board.clone, "worktree", "list").decode().count("\n") == 1  # the session's clone is gone
    assert not list((board.root / "launch" / "preparation").glob("*.json"))  # nor its result file


def test_a_preparer_result_over_the_limit_is_never_read_whole_and_never_left_behind(board, tmp_path, monkeypatch):
    import sys
    from alienintent.composition import work_preparation
    from alienintent.composition.work_preparation import WorkerPreparer
    monkeypatch.setattr(work_preparation, "RESULT_LIMIT", 64)
    fake = tmp_path / "fake-codex"
    fake.write_text(f"""#!{sys.executable}
import re, sys
result = re.search(r"Write exactly one JSON file to this path and nothing else:\\n(\\S+)", sys.stdin.read()).group(1)
open(result, "w").write('{{"answer": "PACKET", "packet": "' + "x" * 200 + '"}}')
""")
    fake.chmod(0o755)
    routing = tmp_path / "routing.json"
    routing.write_text(json.dumps({"schemaVersion": 1, "default": {"provider": "codex", "model": "m"},
                                   "providers": {"codex": {"executable": str(fake), "permissionMode": "read-only"},
                                                 "claude": {"executable": str(fake), "permissionMode": "plan"}},
                                   "roles": {}}))
    monkeypatch.setenv("ALIENINTENT_MODEL_ROUTING", str(routing))
    answer = WorkerPreparer(board.loaded())({"obligation": {"label": "FIXTURE"}})
    assert answer["answer"] == "HOLD" and "limit" in answer["reason"]
    assert not list((board.root / "launch" / "preparation").glob("*.json"))


def _retired_and_stopped(board, result) -> None:
    registry = board.loaded()
    assert result.answer == STOPPED and registry.identities.find(result.identity).retired
    assert service(board, Preparer()).prepare_next().answer == NOTHING  # a stop, never a live item blocking preparation


def test_a_refused_revision_stops_the_obligation_and_retires_its_item(board):
    board.answer.write_text("CLARIFY")
    preparer = Preparer({"answer": "PACKET", "packet": packet(board)},
                        {"answer": "PACKET", "packet": packet(board, scope=("outside/x.py",))})
    _retired_and_stopped(board, service(board, preparer).prepare_next())


def test_an_assessment_hold_stops_the_obligation_and_retires_its_item(board):
    board.answer.write_text("HOLD")
    _retired_and_stopped(board, service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next())


def test_a_release_that_fails_stops_the_obligation_and_retires_its_item(board, monkeypatch):
    from alienintent.context_assembly.application.inherited_release import InheritedRelease

    def failing(self, identity):
        raise RuntimeError("board unreachable")
    monkeypatch.setattr(InheritedRelease, "release", failing)
    _retired_and_stopped(board, service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next())


def test_a_new_obligation_revision_prepares_a_new_item_never_the_old_one(board):
    """The plan entry changes after the first item: the new revision's first item is a new Work Item at its own path."""
    from tests.composition.test_work_registry import PLAN_SCOPE, plan_text
    first = service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next()
    board.loaded().identities.retire(first.identity)
    changed = dict(PLAN_SCOPE, obligations=[dict(PLAN_SCOPE["obligations"][0], intent="Fixture intent, revised.")])
    board.digest = board.approve(plan_text(changed))
    second = service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next()
    assert second.answer == RELEASED and second.identity != first.identity


def test_a_packet_publication_failure_is_a_typed_stop_never_an_exception(board, monkeypatch):
    from alienintent.composition.work_preparation import WorkPreparation
    from alienintent.context_assembly.ports.work_item_repository import PublicationFailed

    def unreachable(self, path, data, message):
        raise PublicationFailed(("refs/heads/alienintent/work-packets",), "remote unreachable")
    monkeypatch.setattr(WorkPreparation, "_commit", unreachable)
    result = service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next()
    assert result.answer == STOPPED and "publication-failed" in result.detail and result.identity is None


def test_a_bind_that_fails_after_registration_retires_the_registered_item(board, monkeypatch):
    from alienintent.composition.work_preparation import WorkPreparation
    from alienintent.context_assembly.ports.work_item_repository import PublicationFailed
    real, calls = WorkPreparation._commit, []

    def bind_fails(self, path, data, message):
        calls.append(message)
        if message.startswith("Bind"):
            raise PublicationFailed(("refs/heads/alienintent/work-packets",), "remote unreachable")
        return real(self, path, data, message)
    monkeypatch.setattr(WorkPreparation, "_commit", bind_fails)
    result = service(board, Preparer({"answer": "PACKET", "packet": packet(board)})).prepare_next()
    assert result.answer == STOPPED and "publication-failed" in result.detail and result.identity
    assert board.loaded().identities.find(result.identity).retired
