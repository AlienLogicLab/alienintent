"""FX-B5 (WO-220508) LOCAL probes: human receipt as an explicit acknowledgement on the C1 attention path.

Real durable store/evidence, disposable roots and channels. Nothing here is operational
acceptance, and an acknowledgement made by this module is never human receipt.
"""
from dataclasses import asdict
from hashlib import sha256
import json

import pytest

HUMAN = "founder"
AT = "2026-09-26T12:00:00Z"


def build(root, *, notifier=None, activation=None, acknowledgers=(HUMAN,)):
    from alienintent.composition.control_plane_profile import AttentionProfile
    from alienintent.control_plane.domain.attention import ResolverGrant
    return AttentionProfile(root, project="project", name="fixture", invocation="fx-b5",
        clock=lambda: AT, next_id=lambda: "attempt-1",
        resolvers=(ResolverGrant("director", "authority-1", "issue:128", "rev-1", "product"),),
        notifier=notifier, activation=activation, acknowledgers=acknowledgers)


def origin(kind="JUDGMENT", event="invocation:outcome-1"):
    from alienintent.control_plane.domain.attention import AttentionOrigin
    from alienintent.evidence_learning.domain.refs import Ref
    return AttentionOrigin("issue:128", event, kind, "rev-1", "product", "authority-1", "observer",
        Ref("project", "fixture", event, "sha256:" + sha256(event.encode()).hexdigest(), "fixture:" + event))


def recorded_resolution(profile, item):
    from alienintent.control_plane.domain.attention import Resolution
    from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes
    body = {"item_identity": item.identity, "actor": "director", "authority": "authority-1",
            "work_revision": "rev-1", "lane": "product", "expected_version": item.version}
    record = Observation(Header("project", "fixture", "resolution:" + item.identity, str(item.version),
        (item.history_ref,)), item.history_ref, item.identity, "attention-resolution", (item.history_ref,),
        canonical_bytes(body).decode(), None, "director", "authorized-consumer")
    return Resolution("director", "authority-1", "rev-1", "product", item.version, profile.evidence.put(record))


def refusal(call):
    from alienintent.control_plane.domain.attention import AttentionHold
    from alienintent.execution_coordination.ports.operational_store import VersionConflict
    try:
        call()
    except AttentionHold as hold:
        return hold.reason
    except VersionConflict:
        return "VERSION_CONFLICT"
    return None


def actions(profile, identity):
    return [h["action"] for h in profile.attention.history(identity)]


class Channel:
    """Disposable transport that confirms delivery with a correlated receipt."""

    def __init__(self):
        self.calls = 0

    def notify(self, item, attempt_id):
        from alienintent.control_plane.domain.attention import DeliveryReceipt
        self.calls += 1
        return DeliveryReceipt(item.identity, attempt_id, "desktop-consumer", "receipt-" + attempt_id)


class BrokenChannel:
    def notify(self, item, attempt_id):
        raise OSError("channel unavailable")


# B5-01 ---------------------------------------------------------------------------------------

def test_receipt_distinct_from_insertion_delivery_rendering_seen(tmp_path):
    p = build(tmp_path, notifier=Channel())
    inserted = p.attention.ensure(origin())
    assert inserted.acknowledgement is None, "queue insertion must not be human receipt"
    delivered = p.attention.handle(origin())
    assert delivered.attempts[-1].status == "DELIVERED"
    assert delivered.acknowledgement is None, "a delivered notification must not be human receipt"
    assert all(i.acknowledgement is None for i in p.attention.list_pending()), "rendering must not be human receipt"
    seen = p.attention.seen(inserted.identity, HUMAN, delivered.version)
    assert seen.acknowledgement is None, "SEEN must not be human receipt"
    assert "ACKNOWLEDGED" not in actions(p, inserted.identity)
    acknowledged = p.attention.acknowledge(inserted.identity, HUMAN, seen.version, "I have read this item")
    assert acknowledged.acknowledgement is not None


# B5-02 / B5-05 -------------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["JUDGMENT", "DONE"])
def test_acknowledgement_shape_and_transition(tmp_path, kind):
    p = build(tmp_path)
    item = p.attention.ensure(origin(kind))
    acknowledged = p.attention.acknowledge(item.identity, HUMAN, item.version, "Acknowledged: will judge")
    receipt = acknowledged.acknowledgement
    assert (receipt.item_identity, receipt.item_version, receipt.item_history_ref) == \
        (item.identity, item.version, item.history_ref), "receipt must bind the exact item version shown"
    assert (receipt.actor, receipt.at, receipt.statement) == (HUMAN, AT, "Acknowledged: will judge")
    assert acknowledged.version == item.version + 1
    assert acknowledged.status == "SEEN", "acknowledgement is receipt, never resolution"
    assert acknowledged.resolution_ref is None and acknowledged.handler is None
    assert acknowledged in p.attention.list_pending(), "an acknowledged unresolved item stays queued"
    last = p.attention.history(item.identity)[-1]
    assert (last["action"], last["actor"], last["status"]) == ("ACKNOWLEDGED", HUMAN, "SEEN")
    assert last["acknowledgement"] == json.loads(json.dumps(asdict(receipt)))


# B5-03 ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("actor", ["notifier", "observer", "director", "intruder", ""])
def test_unconfigured_actor_refused(tmp_path, actor):
    p = build(tmp_path)
    item = p.attention.ensure(origin())
    reason = refusal(lambda: p.attention.acknowledge(item.identity, actor, item.version, "ack"))
    assert reason == "WRONG_ACKNOWLEDGER", "an unconfigured actor must not acknowledge"
    assert p.attention.show(item.identity) == item


def test_statement_and_version_required(tmp_path):
    p = build(tmp_path)
    item = p.attention.ensure(origin())
    assert refusal(lambda: p.attention.acknowledge(item.identity, HUMAN, item.version, " ")) == "STATEMENT_REQUIRED"
    assert refusal(lambda: p.attention.acknowledge(item.identity, HUMAN, item.version + 1, "ack")) == "VERSION_CONFLICT"
    assert p.attention.show(item.identity) == item


# B5-04 ---------------------------------------------------------------------------------------

def test_zero_duplicate_handling(tmp_path):
    channel = Channel()
    p = build(tmp_path, notifier=channel)
    first = p.attention.handle(origin())
    again = build(tmp_path, notifier=channel).attention.handle(origin())
    assert again == first and channel.calls == 1, "a repeated origin must not create or notify twice"
    assert len(p.attention.list_pending()) == 1
    acknowledged = p.attention.acknowledge(first.identity, HUMAN, first.version, "ack")
    reason = refusal(lambda: p.attention.acknowledge(first.identity, HUMAN, acknowledged.version, "ack again"))
    assert reason == "ALREADY_ACKNOWLEDGED", "a second acknowledgement must be refused"
    assert actions(p, first.identity).count("ACKNOWLEDGED") == 1
    assert p.attention.show(first.identity) == acknowledged


# B5-06 ---------------------------------------------------------------------------------------

def test_pending_reconciliation_after_failed_delivery(tmp_path):
    build(tmp_path, notifier=BrokenChannel()).attention.handle(origin())
    fresh = build(tmp_path)
    [pending] = fresh.attention.list_pending()
    assert (pending.status, pending.attempts[-1].status) == ("PENDING", "FAILED")
    acknowledged = fresh.attention.acknowledge(pending.identity, HUMAN, pending.version, "picked up after failure")
    assert fresh.attention.list_pending() == (acknowledged,)
    resolved = fresh.attention.resolve(pending.identity, recorded_resolution(fresh, acknowledged))
    assert resolved.status == "RESOLVED" and not fresh.attention.list_pending()
    assert resolved.acknowledgement == acknowledged.acknowledgement, "receipt survives resolution"
    assert actions(fresh, pending.identity) == [
        "CREATED", "NOTIFICATION_STARTED", "ACKNOWLEDGED", "RESOLVED", "NOTIFICATION_FAILED"]
    assert refusal(lambda: fresh.attention.acknowledge(pending.identity, HUMAN, resolved.version, "late")) == \
        "ALREADY_RESOLVED"


# B5-07 ---------------------------------------------------------------------------------------

SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
G = 300 * SECOND
DIGEST = "sha256:" + "c" * 64
BIU = "WO-L1"


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


def liveness(root, clock):
    from alienintent.composition.control_plane_profile import AttentionProfile, MonitorProfile
    from alienintent.composition.liveness_profile import LivenessProfile
    from alienintent.control_plane.domain.attention import ResolverGrant
    from alienintent.control_plane.domain.monitor_health import MonitorPolicy
    from alienintent.execution_coordination.domain.liveness import KnownActive, LivenessPolicy
    attention = AttentionProfile(root, project="project", name="fixture", invocation="fx-b5",
        clock=lambda: AT, next_id=lambda: "attempt-1",
        resolvers=(ResolverGrant("director", "founder-judgment", BIU, DIGEST + ":generation:1", "producer"),),
        acknowledgers=(HUMAN,))
    ids = iter(f"monitor-{n}" for n in range(1, 100))
    health = MonitorProfile(root, project="project", name="fixture", invocation="fx-b5", policy=MonitorPolicy(60),
                            clock=clock, next_id=lambda: next(ids))
    p = LivenessProfile(root, project="project", name="fixture", policy=LivenessPolicy(), clock=clock,
                        attention=attention, monitor=health, required_authority="founder-judgment")
    version, _ = p.store.read_state("fixture", "authority:dispatch")
    p.store.commit("fixture", "authority:dispatch", version, {"schema_version": 1, "active": True, "epoch": 1,
                   "invocation": "dispatcher-1", "expires_at": T0 / SECOND + 10 ** 6})
    p.journal.enter(KnownActive(BIU, "repo:alienintent", DIGEST, "IMPLEMENT", 1, T0, "authority:dispatch", True, None))
    p.reconciler.progress.start()
    p.reconciler.start()
    return p


def scan(p, clock, now):
    clock.now = now
    p.reconciler.progress.tick()
    return [e.kind for e in p.reconciler.scan().events]


def test_acknowledgement_keeps_judgment_suppression(tmp_path):
    from alienintent.execution_coordination.domain.liveness import CorrelatedOutcome
    clock = Clock()
    p = liveness(tmp_path, clock)
    p.journal.record_outcome(CorrelatedOutcome("outcome-1", BIU, 1, "producer", "FOUNDER_EXCEPTION", 1))
    assert scan(p, clock, T0 + G) == ["liveness.suppressed"]
    service = p.judgment.attention
    [item] = service.list_pending()
    service.acknowledge(item.identity, HUMAN, item.version, "Founder has seen the exception")
    for n in (3, 10):
        assert scan(p, clock, T0 + n * G) == ["liveness.suppressed"], \
            "acknowledgement must not lift judgment suppression"
    assert [s for _, _, s in p.store.list_states("fixture", '__fenced__:["consumer",')] == []
    acknowledged = service.list_pending()[0]
    service.resolve(item.identity, recorded_resolution_for(p, acknowledged))
    assert scan(p, clock, T0 + 12 * G) == ["liveness.no_action"], "only a valid resolution lifts suppression"


def recorded_resolution_for(p, item):
    from alienintent.control_plane.domain.attention import Resolution
    from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes
    body = {"item_identity": item.identity, "actor": "director", "authority": "founder-judgment",
            "work_revision": item.origin.work_revision, "lane": item.origin.lane, "expected_version": item.version}
    record = Observation(Header("project", "fixture", "resolution:" + item.identity, str(item.version),
        (item.history_ref,)), item.history_ref, item.identity, "attention-resolution", (item.history_ref,),
        canonical_bytes(body).decode(), None, "director", "authorized-consumer")
    return Resolution("director", "founder-judgment", item.origin.work_revision, item.origin.lane, item.version,
                      p.judgment.attention.repository.evidence.put(record))


# B5-08 ---------------------------------------------------------------------------------------

def test_queue_persists_across_restart(tmp_path):
    first = build(tmp_path, notifier=BrokenChannel())
    judgment = first.attention.handle(origin("JUDGMENT"))
    done = first.attention.ensure(origin("DONE", "invocation:outcome-2"))
    first.attention.acknowledge(done.identity, HUMAN, done.version, "done noted")
    before = first.attention.list_pending()
    histories = {i.identity: first.attention.history(i.identity) for i in before}
    del first
    reopened = build(tmp_path)
    assert reopened.attention.list_pending() == before, "the queue must persist across restart"
    assert {i.identity: reopened.attention.history(i.identity) for i in before} == histories
    assert {i.identity for i in before} == {judgment.identity, done.identity}


# B5-09 ---------------------------------------------------------------------------------------

def inbox(capsys, *argv):
    from alienintent.composition.attention_inbox import main
    code = main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_operator_surface(tmp_path, capsys):
    root = tmp_path / "profile"
    root.mkdir()
    config = tmp_path / "attention-inbox.json"
    config.write_text(json.dumps({"root": str(root), "project": "project", "profile": "fixture",
                                  "invocation": "fx-b5", "acknowledgers": [HUMAN]}))
    assert inbox(capsys, "list", "--config", str(config)) == (2, {"hold": "ATTENTION_STORE_ABSENT"})
    item = build(root).attention.ensure(origin())
    code, listed = inbox(capsys, "list", "--config", str(config))
    assert code == 0 and [(i["identity"], i["acknowledged_by"]) for i in listed] == [(item.identity, None)]
    assert inbox(capsys, "acknowledge", item.identity, "--config", str(config), "--actor", "intruder",
                 "--expected-version", str(item.version), "--statement", "x") == (2, {"hold": "WRONG_ACKNOWLEDGER"})
    code, acknowledged = inbox(capsys, "acknowledge", item.identity, "--config", str(config), "--actor", HUMAN,
                               "--expected-version", str(item.version), "--statement", "received")
    assert code == 0 and acknowledged["status"] == "SEEN" and acknowledged["acknowledgement"]["actor"] == HUMAN
    code, listed = inbox(capsys, "list", "--config", str(config))
    assert [(i["identity"], i["acknowledged_by"], i["status"]) for i in listed] == [(item.identity, HUMAN, "SEEN")]
    code, history = inbox(capsys, "history", item.identity, "--config", str(config))
    assert [h["action"] for h in history] == ["CREATED", "ACKNOWLEDGED"]
    assert inbox(capsys, "list", "--config", str(tmp_path / "absent.json")) == \
        (2, {"hold": "INBOX_CONFIGURATION_MISSING"})


# B5-10 ---------------------------------------------------------------------------------------

def test_acknowledgement_never_activates(tmp_path):
    class Spy:
        count = 0

        def launch(self, item):
            Spy.count += 1
            return "launched"
    p = build(tmp_path, activation=Spy())
    item = p.attention.ensure(origin())
    acknowledged = p.attention.acknowledge(item.identity, HUMAN, item.version, "ack")
    hold = p.attention.request_activation(item.identity, HUMAN, acknowledged.version)
    assert hold.reason == "ACTIVATION_UNBOUND" and Spy.count == 0, "acknowledgement must not activate"
