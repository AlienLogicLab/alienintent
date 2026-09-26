"""FX-B5 operational tool, exercised on disposable roots only (never the operational root)."""
import json
from pathlib import Path
import sys

sys.path[:0] = [str(Path(__file__).resolve().parent)]

import fx_b5_operational as fx  # noqa: E402


def test_readback_holds_until_named_human_acknowledges(tmp_path, capsys):
    from alienintent.composition.attention_inbox import main as inbox
    root = tmp_path / "attention"
    first = fx.prepare(root, "founder", "fx-b5-test", "WO-220508")
    again = fx.prepare(root, "founder", "fx-b5-test", "WO-220508")
    assert [i["identity"] for i in first["prepared"]] == [i["identity"] for i in again["prepared"]]
    held = fx.readback(root)
    assert held["result"] == "HOLD" and held["holds"] == ["HUMAN_ACKNOWLEDGEMENT_ABSENT"], \
        "no human acknowledgement must hold, never pass"
    assert all(b["in_pending_queue"] and b["acknowledgement"] is None for b in held["items"])
    judgment = next(i for i in first["prepared"] if i["kind"] == "JUDGMENT")
    config = str(root / "attention-inbox.json")
    assert inbox(["acknowledge", judgment["identity"], "--config", config, "--actor", "agent",
                  "--expected-version", str(judgment["version"]), "--statement", "x"]) == 2
    assert json.loads(capsys.readouterr().out) == {"hold": "WRONG_ACKNOWLEDGER"}
    assert fx.readback(root)["holds"] == ["HUMAN_ACKNOWLEDGEMENT_ABSENT"]
    assert inbox(["acknowledge", judgment["identity"], "--config", config, "--actor", "founder",
                  "--expected-version", str(judgment["version"]), "--statement", "received"]) == 0
    capsys.readouterr()
    complete = fx.readback(root)
    assert complete["result"] == "OPERATIONAL_READBACK_COMPLETE", complete["holds"]
    bound = next(b for b in complete["items"] if b["kind"] == "JUDGMENT")
    transition = bound["transition"]
    assert (transition["from"]["status"], transition["to"]["status"], transition["to"]["action"]) == \
        ("PENDING", "SEEN", "ACKNOWLEDGED")
    assert transition["item_bound"] and transition["receipt_equals_entry"] and transition["actor_is_configured_human"]
    assert transition["from"]["object"]["rehash_matches"] and bound["current_object"]["rehash_matches"]
    assert bound["in_pending_queue"] and bound["acknowledged_entries"] == 1
    assert complete["other_attention_identities"] == []
    output = tmp_path / "out"
    fx.retain(output, complete)
    assert json.loads((output / "readback.json").read_text())["result"] == "OPERATIONAL_READBACK_COMPLETE"


def test_prepare_refuses_a_different_configuration(tmp_path):
    import pytest
    root = tmp_path / "attention"
    fx.prepare(root, "founder", "fx-b5-test", "WO-220508")
    with pytest.raises(SystemExit):
        fx.prepare(root, "someone-else", "fx-b5-test", "WO-220508")
