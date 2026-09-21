"""Tests for the Program Director <-> Claude coordinator bridge.

The bridge transports requests and replies. It holds no decision logic, and it is
deliberately separate from the AlienIntent product attention queue: post-Wave-1
orchestration messages must not mix with product/runtime attention.

Identity is the stable `message_id`, never an observation timestamp — the Wave 1
attention queue was woken three times for one event by anchoring on a rewritable
timestamp, and this bridge must not repeat it.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from bridge import Bridge, REQUIRED_FIELDS  # noqa: E402


@pytest.fixture
def bridge(tmp_path):
    return Bridge(tmp_path / "orchestration")


# --- message schema -------------------------------------------------------------


def test_a_sent_request_carries_every_required_field(bridge):
    mid = bridge.send(to_role="claude-bootstrap-coordinator", message_type="REVIEW_REQUEST",
                      task_id="T-001", subject="synthetic", body="please confirm",
                      requires_reply=True)
    msg = bridge.get(mid)
    missing = [f for f in REQUIRED_FIELDS if f not in msg]
    assert missing == [], missing


def test_message_id_and_correlation_id_are_distinct_and_stable(bridge):
    mid = bridge.send(to_role="x", message_type="PING", task_id="T", subject="s", body="b")
    msg = bridge.get(mid)
    assert msg["message_id"] == mid
    assert msg["correlation_id"]
    assert bridge.get(mid)["message_id"] == mid, "identity must not change on re-read"


def test_a_reply_carries_the_request_correlation_id(bridge):
    mid = bridge.send(to_role="claude", message_type="REVIEW_REQUEST", task_id="T-002",
                      subject="s", body="b", requires_reply=True)
    rid = bridge.reply(mid, from_role="claude-bootstrap-coordinator", body="PASS")
    assert bridge.get(rid)["correlation_id"] == bridge.get(mid)["correlation_id"]
    assert bridge.get(rid)["reply_to"] == mid


# --- delivery and dedupe --------------------------------------------------------


def test_an_unhandled_request_is_pending_for_its_recipient(bridge):
    mid = bridge.send(to_role="claude-bootstrap-coordinator", message_type="REVIEW_REQUEST",
                      task_id="T", subject="s", body="b", requires_reply=True)
    assert [m["message_id"] for m in bridge.pending("claude-bootstrap-coordinator")] == [mid]


def test_an_acknowledged_request_is_no_longer_pending(bridge):
    mid = bridge.send(to_role="claude-bootstrap-coordinator", message_type="X",
                      task_id="T", subject="s", body="b")
    bridge.acknowledge(mid, by="claude-bootstrap-coordinator", note="handled")
    assert bridge.pending("claude-bootstrap-coordinator") == []


def test_acknowledgement_survives_a_fresh_bridge_instance(tmp_path):
    root = tmp_path / "orchestration"
    mid = Bridge(root).send(to_role="claude", message_type="X", task_id="T", subject="s", body="b")
    Bridge(root).acknowledge(mid, by="claude", note="handled")
    assert Bridge(root).pending("claude") == []


def test_the_same_message_is_never_delivered_twice(bridge):
    mid = bridge.send(to_role="claude", message_type="X", task_id="T", subject="s", body="b")
    bridge.acknowledge(mid, by="claude", note="first")
    bridge.acknowledge(mid, by="claude", note="second")
    assert bridge.pending("claude") == []
    assert bridge.get(mid)["status"] == "handled"


def test_messages_to_another_role_are_not_pending_for_this_one(bridge):
    bridge.send(to_role="program-director", message_type="X", task_id="T", subject="s", body="b")
    assert bridge.pending("claude-bootstrap-coordinator") == []


# --- correlated waiting ---------------------------------------------------------


def test_waiting_returns_the_reply_matching_the_correlation_id(bridge):
    mid = bridge.send(to_role="claude", message_type="REVIEW_REQUEST", task_id="T",
                      subject="s", body="b", requires_reply=True)
    bridge.reply(mid, from_role="claude", body="PASS_WITH_QUALIFICATIONS")
    got = bridge.wait_for_reply(mid, timeout_s=2, poll_s=0.01)
    assert got is not None and got["body"] == "PASS_WITH_QUALIFICATIONS"


def test_waiting_times_out_rather_than_blocking_forever(bridge):
    mid = bridge.send(to_role="claude", message_type="REVIEW_REQUEST", task_id="T",
                      subject="s", body="b", requires_reply=True)
    assert bridge.wait_for_reply(mid, timeout_s=0.3, poll_s=0.01) is None


def test_a_reply_to_a_different_request_does_not_satisfy_the_wait(bridge):
    first = bridge.send(to_role="claude", message_type="R", task_id="T1", subject="s", body="b",
                        requires_reply=True)
    second = bridge.send(to_role="claude", message_type="R", task_id="T2", subject="s", body="b",
                         requires_reply=True)
    bridge.reply(second, from_role="claude", body="other")
    assert bridge.wait_for_reply(first, timeout_s=0.3, poll_s=0.01) is None


# --- durability -----------------------------------------------------------------


def test_records_are_immutable_json_on_disk(bridge):
    mid = bridge.send(to_role="claude", message_type="X", task_id="T", subject="s", body="b")
    files = list((bridge.root / "inbox").glob("*.json"))
    assert len(files) == 1
    on_disk = json.loads(files[0].read_text())
    assert on_disk["message_id"] == mid


def test_a_partial_write_is_never_visible(bridge, monkeypatch):
    """Atomic publish: readers must never observe a half-written record."""
    seen = {}
    real = Path.replace

    def spy(self, target):
        seen["atomic"] = True
        return real(self, target)

    monkeypatch.setattr(Path, "replace", spy)
    bridge.send(to_role="claude", message_type="X", task_id="T", subject="s", body="b")
    assert seen.get("atomic"), "records must be published with an atomic rename"


def test_the_bridge_does_not_touch_the_product_attention_queue(bridge):
    bridge.send(to_role="claude", message_type="X", task_id="T", subject="s", body="b")
    assert "attention" not in str(bridge.root)
    assert not (bridge.root / "coordinator-attention.jsonl").exists()
