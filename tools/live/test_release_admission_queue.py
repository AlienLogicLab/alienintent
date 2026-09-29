"""The READY queue is ordered by the canonical scheduler, not by a Director's reading.

Chris (2026-09-29): the factory must move BIUs by priority and dependency order. Before this,
the gate checked only the Issue a Director episode named, and `select_admissible` had no caller
outside tests, so any releasable READY BIU could jump the queue.
"""
import json
import sys
from pathlib import Path, PurePosixPath

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from release_admission import (  # noqa: E402
    QUEUE_CHECKS, SCHEDULER, admit, canonical_scheduler, founder_holds, rank_ready)
from test_release_admission import GOOD  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def scheduler():
    return canonical_scheduler(lambda path: (ROOT / path).read_bytes())


def row(number, status="READY", priority="P0"):
    return {"content": {"number": number, "repository": "AlienLogicLab/alienintent"},
            "status": status, "priority": priority}


def first(issue, items, releasable=lambda _n: True):
    return rank_ready(issue, items, releasable, scheduler)


def test_a_higher_priority_releasable_item_ranks_ahead():
    assert first(147, [row(147, priority="P1"), row(160, priority="P0")]) == {"status": "RANKED", "first": 160}


def test_equal_priority_goes_to_the_lower_issue_number():
    assert first(147, [row(147), row(125)])["first"] == 125
    assert first(125, [row(147), row(125)])["first"] == 125


def test_a_lower_priority_or_unset_priority_item_never_ranks_ahead():
    assert first(147, [row(147, priority="P1"), row(100, priority="P2"), row(101, priority=None)])["first"] == 147


def test_an_item_that_cannot_be_released_never_blocks_the_one_behind_it():
    assert first(147, [row(147), row(125)], releasable=lambda n: n != 125)["first"] == 147


def test_only_ready_items_compete():
    assert first(147, [row(147), row(125, status="IMPLEMENT"), row(126, status="TASKS")])["first"] == 147


def test_the_issue_competes_even_when_list_transport_omits_it():
    ranked = rank_ready(147, [row(160, priority="P1")], lambda _n: True, scheduler, "P0")
    assert ranked["first"] == 147
    assert rank_ready(147, [row(125)], lambda _n: True, scheduler, "P0")["first"] == 125
    # With no Priority known for it at all, it waits behind every prioritized item.
    assert first(147, [row(160, priority="P5")])["first"] == 160


def test_a_queue_of_one_needs_no_scheduler():
    def unavailable():
        raise AssertionError("scheduler must not be read")
    assert rank_ready(147, [row(147), row(125, status="DONE")], lambda _n: True, unavailable) \
        == {"status": "RANKED", "first": 147}


def test_the_rule_is_read_from_the_release_point_and_fails_closed_when_absent():
    with pytest.raises(LookupError):
        canonical_scheduler(lambda _path: None)
    seen = []
    canonical_scheduler(lambda path: seen.append(path) or (ROOT / path).read_bytes())
    assert seen == [PurePosixPath("src/alienintent/execution_coordination/domain/scheduling.py")] == [SCHEDULER]


def test_a_biu_behind_another_releasable_biu_is_refused_and_names_it():
    failures = admit({**GOOD, "issue": 147, "priority_order": {"status": "RANKED", "first": 125}})
    assert [f["check"] for f in failures] == ["priority_order"]
    assert "#125" in failures[0]["why"]


def test_the_first_biu_in_the_queue_is_admitted():
    assert admit({**GOOD, "issue": 125, "priority_order": {"status": "RANKED", "first": 125}}) == []


def test_an_unrankable_queue_is_refused():
    failures = admit({**GOOD, "priority_order": {"status": "UNAVAILABLE", "reason": "gh failed"}})
    assert [f["check"] for f in failures] == ["priority_order_known"]


def test_queue_checks_are_the_only_ones_ignored_when_judging_another_item():
    assert QUEUE_CHECKS == {"wip_limit_known", "wip_capacity_known", "wip_capacity_available",
                            "priority_order", "priority_order_known"}


def test_founder_holds_come_from_the_directors_hold_record(tmp_path):
    assert founder_holds({}) == frozenset()
    record = tmp_path / "founder-holds.json"
    record.write_text(json.dumps({"schemaVersion": 1, "holds": [{"issue": 125, "kind": "FOUNDER_DECISION", "reason": "r"}]}))
    assert founder_holds({"founderHoldRecord": str(record)}) == {125}
    with pytest.raises(OSError):
        founder_holds({"founderHoldRecord": str(tmp_path / "missing.json")})


def test_another_item_is_judged_by_its_own_gate_minus_the_shared_queue_checks():
    from release_admission import queue_releasable
    facts = {125: {**GOOD, "issue": 125, "active_claims_total": 1, "wip_limit": 1,
                   "priority_order": {"status": "RANKED", "first": 99}},
             126: {**GOOD, "issue": 126, "open_dependencies": [149]},
             127: {**GOOD, "issue": 127, "work_unit_sha256": "f" * 64}}
    assert queue_releasable(125, frozenset(), facts.__getitem__) is True
    assert queue_releasable(125, frozenset({125}), facts.__getitem__) is False, "a Founder hold is honored"
    assert queue_releasable(126, frozenset(), facts.__getitem__) is False, "an open dependency waits"
    assert queue_releasable(127, frozenset(), facts.__getitem__) is False, "a stale receipt waits"


# --- the live wiring in gather(): a failed read refuses, it never admits -----------------------

import subprocess  # noqa: E402

import release_admission as gate  # noqa: E402


class World:
    """gh answers from `self.answers`; a verb listed in `self.failing` exits non-zero."""

    def __init__(self, monkeypatch, tmp_path):
        self.failing, self.issues = set(), {}
        self.items = []
        state, config = tmp_path / "state.json", tmp_path / "host.json"
        state.write_text(json.dumps({"active": {}}))
        config.write_text(json.dumps({"wipLimit": 1}))
        monkeypatch.setattr(gate, "STATE", state)
        monkeypatch.setattr(gate, "HOST_CONFIG", config)
        monkeypatch.setattr(gate, "repository_root", lambda: str(tmp_path))
        monkeypatch.setattr(gate, "refresh_release_point", lambda root, point: True)
        monkeypatch.setattr(gate, "_git", lambda root, *args: subprocess.CompletedProcess(args, 0 if args[0] == "rev-parse" else 1, "c" * 40 + "\n", ""))
        monkeypatch.setattr(gate, "read_at_release_point",
                            lambda root, commit, path: (ROOT / path).read_bytes() if path == SCHEDULER else None)
        monkeypatch.setattr(gate, "reconcile_inherited_priority",
                            lambda root, issue, items: {"status": "ALREADY_MATCHED", "priority": "P0"})
        monkeypatch.setattr(gate.subprocess, "run", self.run)

    def add(self, number, priority="P0"):
        self.items.append(row(number, priority=priority))
        self.issues[number] = {"body": "", "comments": [], "labels": [],
                               "projectItems": [{"status": {"name": "READY"}}]}

    def run(self, args, **_kwargs):
        verb = "blocked_by" if args[1] == "api" else " ".join(args[1:3])
        if verb in self.failing or (verb == "issue view" and int(args[3]) in self.failing):
            # gh can print a JSON error body and still exit non-zero.
            return subprocess.CompletedProcess(args, 1, '{"message": "Bad Gateway"}', "HTTP 502")
        if verb == "issue view":
            payload = self.issues[int(args[3])]
        elif verb == "project item-list":
            payload = {"items": self.items}
        else:
            payload = []
        return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")


@pytest.fixture
def world(monkeypatch, tmp_path):
    return World(monkeypatch, tmp_path)


def test_a_fully_read_queue_is_ranked(world):
    world.add(147)
    world.add(125)  # ranks ahead, but has no bound receipt, so it cannot be released now
    facts = gate.gather(147)
    assert facts["unread"] == []
    assert facts["priority_order"] == {"status": "RANKED", "first": 147}


@pytest.mark.parametrize("verb", ["issue view", "project item-list", "blocked_by"])
def test_a_failed_read_of_the_biu_itself_refuses(world, verb):
    world.add(147)
    world.failing.add(verb)
    failures = [f["check"] for f in gate.admit(gate.gather(147))]
    assert "live_facts_readable" in failures


def test_blocked_by_that_is_not_a_list_refuses(world, monkeypatch):
    world.add(147)
    original = world.run

    def run(args, **kwargs):
        if args[1] == "api":
            return subprocess.CompletedProcess(args, 0, json.dumps({"message": "Not Found"}), "")
        return original(args, **kwargs)
    monkeypatch.setattr(gate.subprocess, "run", run)
    assert "live_facts_readable" in [f["check"] for f in gate.admit(gate.gather(147))]


def test_an_item_ahead_that_cannot_be_read_refuses_the_one_behind(world):
    world.add(147)
    world.add(125)
    world.failing.add(125)  # only #125's Issue read fails
    facts = gate.gather(147)
    assert facts["unread"] == []
    assert facts["priority_order"]["status"] == "UNAVAILABLE"
    assert "#125" in facts["priority_order"]["reason"]
    assert "priority_order_known" in [f["check"] for f in gate.admit(facts)]


def test_an_empty_answer_is_a_failed_read_not_an_empty_result(world, monkeypatch):
    world.add(147)
    original = world.run
    monkeypatch.setattr(gate.subprocess, "run", lambda args, **kwargs: subprocess.CompletedProcess(args, 0, "", "")
                        if args[1] == "api" else original(args, **kwargs))
    assert "live_facts_readable" in [f["check"] for f in gate.admit(gate.gather(147))]
