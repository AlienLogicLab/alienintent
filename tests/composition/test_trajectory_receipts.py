"""FX-B1 mechanical probes (LOCAL): the trajectory-receipts attention producer over the B1P journal.

The capture runs under the unchanged C5 supervisor with its in-memory manager, as in
`test_trajectory_capture_host.py`. Every consumer is a fresh object over the same root, as a
fresh consumer process would be. The operational run on the real manager is `tools/live/fx_b1_operational.py`.
"""
import pytest

from tests.composition.test_trajectory_capture_host import World, send
from tests.control_plane.test_monitor_host import SECOND, T0

KINDS = ["CAPTURE_STALL", "DUPLICATE_IDENTITY", "OUT_OF_ORDER", "SEQUENCE_GAP", "TIMESTAMP_REGRESSION"]


def event(seq, observed=None, source="agent-1"):
    return {"source": source, "source_seq": seq, "observed_at": T0 + (observed or seq) * SECOND,
            "event": {"schema_version": "1.0", "event_id": f"{source}-{seq:03d}", "event_type": "TOOL_CALL"}}


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def consumer(world, name="consumer"):
    from alienintent.composition.trajectory_receipts import open_receipts
    return open_receipts(world.config, name, clock=world.clock)


def seed(world, hosted):
    """In order, gap, late, duplicate, source clock regression, then a stall."""
    acks = [send(hosted, event(s)) for s in (1, 2, 3)]
    acks += [send(hosted, event(6)), send(hosted, event(4, observed=6)), send(hosted, event(2)),
             send(hosted, event(7, observed=1))]
    world.clock.now += 31 * SECOND
    hosted.capture.check_stall()
    return acks


def journal_events(world):
    return {e["event"]["capture_seq"]: e["event"] for e in world.journal()["entries"] if e["kind"] == "EVENT"}


def test_receipts_observe_every_captured_event_with_its_journal_identity(world):  # B1-01
    world.supervisor.launch(world.grant())
    seed(world, world.host())
    result = consumer(world).consume()
    assert result["status"] == "RECEIPTED" and result["from_entry"] == 1
    assert result["to_entry"] == len(world.journal()["entries"])
    (receipt,) = consumer(world, "reader").chain()
    observed = {e["event"]["capture_seq"]: e["event"] for e in receipt["entries"] if e["event"]}
    journal = journal_events(world)
    assert sorted(observed) == sorted(journal) == [1, 2, 3, 4, 5, 6]
    for seq, seen in observed.items():
        assert all(seen[k] == journal[seq][k] for k in ("event_id", "identity", "captured_at", "source_seq"))
    assert [e["entry_seq"] for e in receipt["entries"]] == list(range(1, result["to_entry"] + 1))


def test_each_anomaly_kind_yields_exactly_one_pending_judgment_item(world):  # B1-02
    world.supervisor.launch(world.grant())
    seed(world, world.host())
    receipts = consumer(world)
    receipts.consume()
    items = consumer(world, "reader").items()
    assert sorted(i["lane"].removeprefix("trajectory-anomaly:") for i in items) == KINDS
    assert {i["status"] for i in items} == {"PENDING"}
    anomalies = {a["anomaly_id"]: (e, a) for e in world.journal()["entries"] for a in e["anomalies"]}
    assert sorted(i["event_identity"] for i in items) == sorted(anomalies)
    for item in items:
        entry, anomaly = anomalies[item["event_identity"]]
        shown = receipts.attention.show(item["identity"])
        assert shown.origin == receipts.origin(entry, anomaly)
        assert (shown.origin.kind, shown.origin.producer, shown.origin.required_authority) == (
            "JUDGMENT", "trajectory-receipts", "founder-judgment")
    report = consumer(world, "reader").reconcile()
    assert report["reconciled"], report
    assert report["anomaly_kinds"] == KINDS and report["pending_items"] == len(KINDS)


def test_a_pass_with_nothing_new_writes_nothing(world):  # B1-03
    world.supervisor.launch(world.grant())
    seed(world, world.host())
    consumer(world).consume()
    before = (consumer(world, "reader").chain(), consumer(world, "reader").items())
    assert consumer(world, "again").consume()["status"] == "UP_TO_DATE"
    assert (consumer(world, "reader").chain(), consumer(world, "reader").items()) == before


def test_passes_across_a_kill_and_granted_restart_reconcile_old_and_new_entries(world):  # B1-04, B1-05
    world.supervisor.launch(world.grant())
    first = world.host()
    acks = seed(world, first)
    one = consumer(world, "pass-1").consume()
    before_chain, before_items = consumer(world, "reader").chain(), consumer(world, "reader").items()

    world.manager.terminate(world.config.binding().unit)
    detection, alerted = world.supervisor.observe()
    assert detection.reason == "UNIT_FAILED_FAILED_SIGNAL"
    down = consumer(world, "pass-2").consume()                    # the capture is down; the queue is not
    assert down["status"] == "UP_TO_DATE"
    assert (consumer(world, "reader").chain(), consumer(world, "reader").items()) == (before_chain, before_items)

    world.supervisor.restart(world.grant(replaces=alerted.launch_id, alert=alerted.alert))
    second = world.host()
    assert send(second, event(7, observed=1))["status"] == "DUPLICATE"
    assert send(second, event(9))["anomalies"] == ["SEQUENCE_GAP"]
    three = consumer(world, "pass-3").consume()
    assert three["from_entry"] == one["to_entry"] + 1 and three["to_entry"] == len(world.journal()["entries"])
    assert consumer(world, "pass-4").consume()["status"] == "UP_TO_DATE"

    chain, items = consumer(world, "reader").chain(), consumer(world, "reader").items()
    assert chain[:1] == before_chain, "pre-restart receipts are an unchanged prefix"
    new = sorted(i["lane"] for i in items if i not in before_items)
    assert new == ["trajectory-anomaly:DUPLICATE_IDENTITY", "trajectory-anomaly:SEQUENCE_GAP"], new
    assert all(i in items for i in before_items), "items produced before the restart are unchanged"
    kinds = [e["kind"] for r in chain for e in r["entries"]]
    assert kinds.count("SESSION") == 2
    observed = [e["event"] for r in chain for e in r["entries"] if e["event"]]
    captured = {a["capture_seq"]: a for a in acks if a["status"] == "CAPTURED"}
    assert all(o["identity"] == captured[o["capture_seq"]]["identity"] for o in observed if o["capture_seq"] in captured)
    report = consumer(world, "reader").reconcile()
    assert report["reconciled"], report
    assert report["receipts"] == 2 and report["observed_events"] == report["journal_events"] == 7


def test_a_pass_that_dies_before_its_receipt_leaves_no_second_item(world):  # B1-06
    from alienintent.composition.trajectory_receipts import ReceiptHold
    world.supervisor.launch(world.grant())
    seed(world, world.host())
    dying = consumer(world, "dying")

    def crash(version, receipt):
        raise ReceiptHold("CRASH_INJECTED")
    dying._append = crash
    with pytest.raises(ReceiptHold):
        dying.consume()
    ensured = consumer(world, "reader").items()
    assert len(ensured) == len(KINDS) and consumer(world, "reader").chain() == ()
    rerun = consumer(world, "rerun").consume()
    assert rerun["from_entry"] == 1 and rerun["status"] == "RECEIPTED"
    assert consumer(world, "reader").items() == ensured
    assert consumer(world, "reader").reconcile()["reconciled"]


def test_a_rewritten_or_overtaken_prefix_holds_and_writes_nothing(world):  # B1-07
    from alienintent.composition.trajectory_receipts import ReceiptHold
    world.supervisor.launch(world.grant())
    seed(world, world.host())
    consumer(world).consume()
    chain, items = consumer(world, "reader").chain(), consumer(world, "reader").items()
    real = consumer(world, "reader").read_entries

    for label, doctored in (
        ("RECEIPTS_PREFIX_MISMATCH", lambda: tuple(e | {"recorded_at": e["recorded_at"] + 1} if e["entry_seq"] == 2
                                                   else e for e in real())),
        ("RECEIPTS_AHEAD_OF_JOURNAL", lambda: real()[:-1]),
    ):
        receipts = consumer(world, "doctored")
        receipts.read_entries = doctored
        with pytest.raises(ReceiptHold) as held:
            receipts.consume()
        assert held.value.reason == label
    assert (consumer(world, "reader").chain(), consumer(world, "reader").items()) == (chain, items)


def test_a_lost_receipt_compare_and_set_holds(world):  # B1-08
    from alienintent.composition.trajectory_receipts import ReceiptHold
    world.supervisor.launch(world.grant())
    hosted = world.host()
    send(hosted, event(1))
    slow, fast = consumer(world, "slow"), consumer(world, "fast")
    version, consumed = slow._receipted(slow._journal())
    fast.consume()
    with pytest.raises(ReceiptHold) as held:
        slow._append(version, {"schema_version": 1, "receipt_seq": version + 1, "consumer": "slow",
                               "stream": slow.stream, "from_entry": consumed + 1, "to_entry": 2,
                               "prefix_digest": "sha256:" + "0" * 64, "entries": []})
    assert held.value.reason == "RECEIPTS_VERSION_CONFLICT"
    assert len(consumer(world, "reader").chain()) == 1
