"""FX-C1: real durable store/evidence, disposable channels, no provider calls."""
from dataclasses import replace
from hashlib import sha256
import json

import pytest


def build(root, *, notifier=None, activation=None):
    from alienintent.composition.control_plane_profile import AttentionProfile
    from alienintent.control_plane.domain.attention import ResolverGrant
    return AttentionProfile(root, project="project", name="fixture", invocation="fx-c1",
        clock=lambda: "2026-09-23T00:00:00Z", next_id=lambda: "attempt-1",
        resolvers=(ResolverGrant("director", "authority-1", "issue:78", "rev-1", "product"),),
        notifier=notifier, activation=activation)


def origin(kind="DONE"):
    from alienintent.control_plane.domain.attention import AttentionOrigin
    from alienintent.evidence_learning.domain.refs import Ref
    return AttentionOrigin("issue:78", "invocation:outcome-1", kind, "rev-1", "product",
        "authority-1", "observer", Ref("project", "fixture", "outcome-1",
        "sha256:" + sha256(b"outcome-1").hexdigest(), "fixture:outcome-1"))


def resolution(item, **changes):
    from alienintent.control_plane.domain.attention import Resolution
    return replace(Resolution("director", "authority-1", "rev-1", "product",
        item.version, origin().source_ref), **changes)


def recorded_resolution(profile, item, **changes):
    from dataclasses import asdict
    from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes
    decision = resolution(item, **changes)
    body = {"item_identity": item.identity, "actor": decision.actor,
            "authority": decision.authority, "work_revision": decision.work_revision,
            "lane": decision.lane, "expected_version": decision.expected_version}
    record = Observation(Header("project", "fixture", "resolution:" + item.identity,
        str(item.version), (item.history_ref,)), item.history_ref, item.identity,
        "attention-resolution", (item.history_ref,), canonical_bytes(body).decode(), None,
        decision.actor, "authorized-consumer")
    return replace(decision, decision_ref=profile.evidence.put(record))


@pytest.mark.parametrize("kind", ["DONE", "JUDGMENT"])
def test_restart_dedupe_origin(tmp_path, kind):
    p = build(tmp_path)
    first = p.attention.ensure(origin(kind))
    seen = p.attention.seen(first.identity, "director", first.version)
    reopened = build(tmp_path)
    duplicate = reopened.attention.ensure(origin(kind))
    assert duplicate == seen, "origin dedupe lost history or minted a new version"
    assert len(reopened.attention.list_pending()) == 1
    assert len(reopened.attention.history(first.identity)) == 2
    assert duplicate.origin == origin(kind)


def test_origin_conflict(tmp_path):
    from alienintent.control_plane.domain.attention import AttentionHold
    p = build(tmp_path)
    p.attention.ensure(origin())
    with pytest.raises(AttentionHold, match="ORIGIN_CONFLICT"):
        p.attention.ensure(replace(origin(), required_authority="different"))


def test_delivery_failure_pending_fresh_consumer(tmp_path):
    class BrokenChannel:
        def notify(self, item, attempt_id):
            persisted = build(tmp_path).attention.show(item.identity)
            assert persisted.attempts[-1].status == "UNCONFIRMED"
            raise OSError("channel unavailable")
    p = build(tmp_path, notifier=BrokenChannel())
    item = p.attention.handle(origin())
    fresh = build(tmp_path)
    pending = fresh.attention.list_pending()
    assert len(pending) == 1, "durable attention creation must precede delivery"
    item = fresh.attention.show(item.identity)
    assert item.status == "PENDING"
    assert item.attempts[-1].status == "FAILED"
    assert "channel unavailable" in item.attempts[-1].diagnostic
    assert [h["action"] for h in fresh.attention.history(item.identity)] == ["CREATED", "NOTIFICATION_STARTED", "NOTIFICATION_FAILED"]
    resolved = fresh.attention.resolve(item.identity, recorded_resolution(fresh, item))
    assert resolved.status == "RESOLVED"
    assert resolved.handler == "director"
    assert not fresh.attention.list_pending()


def test_seen_is_not_resolved_and_decision_inbox_distinct(tmp_path):
    p = build(tmp_path)
    p.store.commit("fixture", "decision-inbox", 0, {"open": {"issue:78": {"untouched": True}}})
    before = p.store.read_state("fixture", "decision-inbox")
    item = p.attention.ensure(origin())
    seen = p.attention.seen(item.identity, "director", item.version)
    assert seen.status == "SEEN"
    assert seen in p.attention.list_pending()
    assert seen.resolution_ref is None
    p.attention.resolve(item.identity, recorded_resolution(p, seen))
    assert p.store.read_state("fixture", "decision-inbox") == before


@pytest.mark.parametrize("field,value", [("actor", "intruder"), ("work_revision", "stale"), ("lane", "mailbox"), ("authority", "wrong")])
def test_resolution_authority_refusal(tmp_path, field, value):
    from alienintent.control_plane.domain.attention import AttentionHold
    p = build(tmp_path)
    item = p.attention.ensure(origin())
    with pytest.raises(AttentionHold):
        p.attention.resolve(item.identity, recorded_resolution(p, item, **{field: value}))
    assert p.attention.show(item.identity) == item


def test_stale_resolution_and_competing_consumers(tmp_path):
    from alienintent.execution_coordination.ports.operational_store import VersionConflict
    p, other = build(tmp_path), build(tmp_path)
    item = p.attention.ensure(origin())
    p.attention.seen(item.identity, "reader", item.version)
    with pytest.raises(VersionConflict):
        other.attention.resolve(item.identity, resolution(item))


def test_unbound_activation_zero_launches(tmp_path):
    class Spy:
        count = 0
        def launch(self, item):
            self.count += 1
            return "unexpected"
    spy = Spy()
    p = build(tmp_path, activation=spy)
    item = p.attention.ensure(origin())
    result = p.attention.request_activation(item.identity, "director", item.version)
    assert spy.count == 0, "unbound activation launched a model"
    assert result.reason == "ACTIVATION_UNBOUND"
    assert p.attention.show(item.identity).status == "PENDING"


def test_correlated_consumer_receipt(tmp_path):
    from alienintent.control_plane.domain.attention import DeliveryReceipt
    class Channel:
        def notify(self, item, attempt_id):
            return DeliveryReceipt(item.identity, attempt_id, "desktop", "receipt-1")
    p = build(tmp_path, notifier=Channel())
    item = p.attention.handle(origin())
    reopened = build(tmp_path).attention.show(item.identity)
    assert reopened.attempts[0].receipt == DeliveryReceipt(item.identity, "attempt-1", "desktop", "receipt-1"), "consumer bridge lost durable correlated receipt"
    assert reopened.status == "PENDING"


def test_wrong_receipt_retains_pending(tmp_path):
    from alienintent.control_plane.domain.attention import DeliveryReceipt
    class Channel:
        def notify(self, item, attempt_id):
            return DeliveryReceipt("different-item", attempt_id, "desktop", "receipt-1")
    item = build(tmp_path, notifier=Channel()).attention.handle(origin())
    assert item.status == "PENDING"
    assert item.attempts[-1].status == "UNCONFIRMED"
    assert "correlation" in item.attempts[-1].diagnostic


def test_missing_history_blocks_mutation(tmp_path):
    from alienintent.evidence_learning.domain.refs import EvidenceHold
    p = build(tmp_path)
    item = p.attention.ensure(origin())
    (p.evidence.root / item.history_ref.locator).unlink()
    with pytest.raises(EvidenceHold):
        p.attention.seen(item.identity, "reader", item.version)


def test_schema_incompatible(tmp_path):
    from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible
    p = build(tmp_path)
    item = p.attention.ensure(origin())
    version, state = p.store.read_state("fixture", item.identity)
    p.store.commit("fixture", item.identity, version, {**state, "schema_version": 99})
    with pytest.raises(SchemaIncompatible):
        p.attention.show(item.identity)


def test_migration_stages_history_aliases_without_switching_writer(tmp_path):
    source = tmp_path / "source.jsonl"
    records = [
        {"kind": "item", "id": "att-1", "biu": 78, "outcome": "DONE_TO_DONE", "handled": False},
        {"kind": "notification", "id": "att-1", "delivered": False, "error": "offline"},
        {"kind": "item", "id": "att-2", "biu": 79, "outcome": "FOUNDER_EXCEPTION", "handled": False},
        {"kind": "ack", "id": "att-2", "by": "founder", "note": "disposition", "at": "then"},
    ]
    source.write_text("".join(json.dumps(r) + "\n" for r in records))
    original = source.read_bytes()
    p = build(tmp_path)
    stage = p.migration.stage(source, permitted_root=tmp_path, source_id="bootstrap-product")
    fresh = build(tmp_path)
    readback = fresh.migration.read(stage.identity)
    assert readback["raw_source"] == original.decode()
    assert readback["records"] == records
    assert readback["aliases"]["att-1"] != readback["aliases"]["att-2"]
    assert readback["states"]["att-1"]["status"] == "PENDING"
    assert readback["states"]["att-2"]["status"] == "RESOLVED"
    assert readback["states"]["att-2"]["handler"] == "founder"
    assert fresh.attention.list_pending() == ()
    assert source.read_bytes() == original
    compare = fresh.migration.compare(stage.identity, source, permitted_root=tmp_path)
    assert compare["source_unchanged"] is True
    assert compare["writer"] == "SOURCE"
    assert fresh.migration.rollback(stage.identity)["pending_origin_ids"] == ["att-1"]
    assert fresh.migration.read(stage.identity) == readback


def test_migration_rejects_unknown_or_conflicting_records(tmp_path):
    from alienintent.control_plane.domain.attention import AttentionHold
    source = tmp_path / "source.jsonl"
    source.write_text('{"kind":"mailbox","id":"x"}\n')
    p = build(tmp_path)
    with pytest.raises(AttentionHold):
        p.migration.stage(source, permitted_root=tmp_path, source_id="bootstrap-product")


def test_notification_crash_preserves_unconfirmed_attempt(tmp_path):
    import os
    from pathlib import Path
    import subprocess
    import sys
    script = '''
import os, sys
from pathlib import Path
from tests.control_plane.test_attention import build, origin
class CrashChannel:
    def notify(self, item, attempt_id):
        os._exit(77)
build(Path(sys.argv[1]), notifier=CrashChannel()).attention.handle(origin())
'''
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)],
        env={**os.environ, "PYTHONPATH": str(root / "src") + os.pathsep + str(root)})
    assert result.returncode == 77
    item, = build(tmp_path).attention.list_pending()
    assert item.status == "PENDING"
    assert item.attempts[0].status == "UNCONFIRMED"
    assert len(build(tmp_path).attention.history(item.identity)) == 2


def test_concurrent_origin_cas_no_duplicate_identity(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from alienintent.execution_coordination.ports.operational_store import VersionConflict
    # Independent connections share the real database and immutable object store.
    p, q = build(tmp_path), build(tmp_path)
    barrier = Barrier(2)
    def produce(profile):
        barrier.wait()
        try:
            return profile.attention.ensure(origin()).identity
        except VersionConflict:
            return "CAS_HOLD"
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(produce, (p, q)))
    item, = build(tmp_path).attention.list_pending()
    assert item.version == 1
    assert all(value in {item.identity, "CAS_HOLD"} for value in results)


def test_migration_append_and_rewrite_refusal(tmp_path):
    from alienintent.control_plane.domain.attention import AttentionHold
    source = tmp_path / "source.jsonl"
    first = '{"kind":"item","id":"att-1","handled":false}\n'
    source.write_text(first)
    p = build(tmp_path)
    staged = p.migration.stage(source, permitted_root=tmp_path, source_id="product")
    before = p.migration.read(staged.identity)
    source.write_text(first + '{"kind":"seen","id":"att-1","by":"reader"}\n')
    assert p.migration.compare(staged.identity, source, permitted_root=tmp_path)["source_unchanged"] is False
    second = p.migration.stage(source, permitted_root=tmp_path, source_id="product")
    assert second.version == staged.version + 1
    assert p.migration.read(second.identity)["states"]["att-1"]["status"] == "SEEN"
    assert p.migration.read(second.identity)["aliases"] == before["aliases"]
    assert p.repository.history(second.identity)[0] == before
    source.write_text('{"kind":"item","id":"att-other"}\n')
    with pytest.raises(AttentionHold, match="SOURCE_HISTORY_REWRITE"):
        p.migration.stage(source, permitted_root=tmp_path, source_id="product")


def test_bound_activation_policy_does_not_supply_episode_executor(tmp_path):
    from alienintent.control_plane.domain.attention import ActivationPolicy
    class Spy:
        count = 0
        def launch(self, item):
            self.count += 1
            return "unexpected"
    spy = Spy()
    p = build(tmp_path, activation=spy)
    item = p.attention.ensure(origin())
    policy = ActivationPolicy("fixture", item.identity, item.version, "director", "authority-1", "rev-1", "product")
    for key, value in [("profile", "wrong"), ("item_identity", "wrong"), ("item_version", 99),
                       ("actor", "wrong"), ("authority", "wrong"), ("work_revision", "wrong"), ("lane", "wrong")]:
        p.attention.activation_policy = replace(policy, **{key: value})
        assert p.attention.request_activation(item.identity, "director", item.version).reason == "ACTIVATION_NOT_APPLICABLE"
    p.attention.activation_policy = policy
    assert p.attention.request_activation(item.identity, "director", item.version).reason == "ACTIVATION_EXECUTOR_UNBOUND"
    assert spy.count == 0


@pytest.mark.parametrize("action", ["seen", "resolve"])
@pytest.mark.parametrize("fails", [True, False])
def test_concurrent_handling_preserves_delivery_result(tmp_path, action, fails):
    from alienintent.control_plane.domain.attention import DeliveryReceipt
    class Channel:
        def notify(self, item, attempt_id):
            fresh = build(tmp_path)
            if action == "seen":
                fresh.attention.seen(item.identity, "reader", item.version)
            else:
                fresh.attention.resolve(item.identity, recorded_resolution(fresh, item))
            if fails:
                raise OSError("known concurrent failure")
            return DeliveryReceipt(item.identity, attempt_id, "consumer", "correlated")
    item = build(tmp_path, notifier=Channel()).attention.handle(origin())
    fresh = build(tmp_path).attention.show(item.identity)
    assert fresh.status == ("SEEN" if action == "seen" else "RESOLVED")
    assert fresh.attempts[-1].status == ("FAILED" if fails else "DELIVERED")
    if fails:
        assert fresh.attempts[-1].diagnostic == "known concurrent failure"
    else:
        assert fresh.attempts[-1].receipt.receipt_id == "correlated"


@pytest.mark.parametrize("fault", ["missing", "corrupt", "unrelated", "actor", "item", "version"])
def test_resolution_requires_retrievable_correlated_disposition(tmp_path, fault):
    from alienintent.control_plane.domain.attention import AttentionHold
    from alienintent.evidence_learning.domain.records import canonical_bytes
    from alienintent.evidence_learning.domain.refs import EvidenceHold
    p = build(tmp_path)
    item = p.attention.ensure(origin())
    decision = recorded_resolution(p, item)
    if fault == "missing":
        (p.evidence.root / decision.decision_ref.locator).unlink()
    elif fault == "corrupt":
        (p.evidence.root / decision.decision_ref.locator).write_text("corrupt")
    elif fault == "unrelated":
        decision = replace(decision, decision_ref=item.history_ref)
    else:
        record = p.evidence.get(decision.decision_ref, frozenset({"private"}))
        body = json.loads(record.value)
        body[{"actor": "actor", "item": "item_identity", "version": "expected_version"}[fault]] = "wrong"
        decision = replace(decision, decision_ref=p.evidence.put(replace(record, value=canonical_bytes(body).decode())))
    with pytest.raises((AttentionHold, EvidenceHold)):
        p.attention.resolve(item.identity, decision)
    assert p.attention.show(item.identity) == item
