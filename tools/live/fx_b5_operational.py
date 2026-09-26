"""FX-B5 operational target (WO-220508): prepare items on, and read back from, the authorized
existing Python attention surface. The operational root lives outside the repository.

- `prepare` ensures one JUDGMENT and one DONE item for Issue #128 and writes the inbox
  configuration that names the human acknowledger. It is idempotent. It performs no
  notification, activation or external effect.
- `readback` reopens the durable profile and binds, for each item: the item, the named human's
  acknowledgement and the recorded state transition. Without a human acknowledgement of the
  JUDGMENT item the result is HOLD: HUMAN_ACKNOWLEDGEMENT_ABSENT. It is never PASS, and this tool
  never acknowledges anything.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src")]

from alienintent.composition.attention_inbox import CONFIG_KEYS, load_config, open_profile  # noqa: E402
from alienintent.composition.control_plane_profile import AttentionProfile  # noqa: E402
from alienintent.control_plane.domain.attention import AttentionOrigin  # noqa: E402
from alienintent.evidence_learning.domain.records import canonical_bytes  # noqa: E402
from alienintent.evidence_learning.domain.refs import Ref  # noqa: E402

DEFAULT_ROOT = Path.home() / ".local/state/alienintent/fx-b5/attention"
PROJECT, PROFILE, WORK_REF = "AlienLogicLab/alienintent", "fx-b5-operational", "issue:128"
EVENTS = (("JUDGMENT", "fx-b5:operational:judgment:1"), ("DONE", "fx-b5:operational:done:1"))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def origin(kind: str, event: str, work_revision: str) -> AttentionOrigin:
    body = canonical_bytes([PROJECT, PROFILE, WORK_REF, event, kind])
    source = Ref(PROJECT, PROFILE, event, "sha256:" + sha256(body).hexdigest(), "fx-b5-operational:" + event)
    return AttentionOrigin(WORK_REF, event, kind, work_revision, "human-attention", "founder-judgment",
                           "fx-b5-operational", source)


def prepare(root: Path, acknowledger: str, invocation: str, work_revision: str) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "attention-inbox.json"
    config = {"root": str(root.resolve()), "project": PROJECT, "profile": PROFILE,
              "invocation": "attention-inbox", "acknowledgers": [acknowledger],
              "work_revision": work_revision}
    if config_path.exists():
        existing = json.loads(config_path.read_text())
        if existing != config:
            raise SystemExit("refusing to rewrite a different operational configuration: " + str(config_path))
    else:
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
    profile = AttentionProfile(root, project=PROJECT, name=PROFILE, invocation=invocation, clock=utc_now,
                               next_id=lambda: "none", resolvers=(), acknowledgers=(acknowledger,))
    items = [profile.attention.ensure(origin(kind, event, work_revision)) for kind, event in EVENTS]
    return {"prepared": [{"identity": i.identity, "version": i.version, "kind": i.origin.kind,
                          "status": i.status, "history_ref": asdict(i.history_ref)} for i in items],
            "config": str(config_path), "acknowledger": acknowledger, "invocation": invocation}


def object_digest(root: Path, ref: dict[str, object]) -> dict[str, object]:
    """The immutable evidence object behind a history ref, re-hashed from disk."""
    name = str(ref["revision_digest"]).removeprefix("sha256:")
    path = root / "attention-evidence" / "objects" / name
    if not path.is_file():
        return {"ref": ref, "present": False}
    return {"ref": ref, "present": True, "rehash_matches": sha256(path.read_bytes()).hexdigest() == name}


def readback(root: Path) -> dict[str, object]:
    config = load_config(root / "attention-inbox.json")
    if any(k not in config for k in CONFIG_KEYS):
        raise SystemExit("invalid configuration")
    attention = open_profile(config).attention
    holds, bindings = [], []
    pending = {i.identity for i in attention.list_pending()}
    for kind, event in EVENTS:
        expected = origin(kind, event, config["work_revision"])
        identity = "attention:" + sha256(canonical_bytes([PROJECT, PROFILE, WORK_REF, event, kind])).hexdigest()
        try:
            item = attention.show(identity)
        except KeyError:
            holds.append("ITEM_ABSENT:" + event)
            continue
        history = list(attention.history(identity))
        acknowledged = [n for n, h in enumerate(history) if h.get("action") == "ACKNOWLEDGED"]
        receipt = None if item.acknowledgement is None else asdict(item.acknowledgement)
        binding: dict[str, object] = {
            "identity": identity, "kind": kind, "origin_matches": item.origin == expected,
            "version": item.version, "status": item.status, "in_pending_queue": identity in pending,
            "acknowledgement": receipt, "acknowledged_entries": len(acknowledged),
            "current_history_ref": asdict(item.history_ref),
            "current_object": object_digest(root, asdict(item.history_ref)),
            "history_actions": [h.get("action") for h in history]}
        if receipt is None:
            if kind == "JUDGMENT":
                holds.append("HUMAN_ACKNOWLEDGEMENT_ABSENT")
        else:
            index = acknowledged[0]
            prior, entry = history[index - 1], history[index]
            human = receipt["actor"] in config["acknowledgers"]
            binding["transition"] = {
                "from": {"version": receipt["item_version"], "status": prior.get("status"),
                         "action": prior.get("action"), "history_ref": receipt["item_history_ref"],
                         "object": object_digest(root, receipt["item_history_ref"])},
                "to": {"version": receipt["item_version"] + 1, "status": entry.get("status"),
                       "action": entry.get("action"), "actor": entry.get("actor"), "at": entry.get("at")},
                "receipt_equals_entry": entry.get("acknowledgement") == receipt,
                "item_bound": receipt["item_identity"] == identity,
                "actor_is_configured_human": human}
            if not (binding["transition"]["receipt_equals_entry"] and binding["transition"]["item_bound"] and human
                    and len(acknowledged) == 1 and entry.get("status") == "SEEN"):
                holds.append("ACKNOWLEDGEMENT_BINDING_INVALID:" + kind)
        if not binding["origin_matches"]:
            holds.append("ORIGIN_MISMATCH:" + kind)
        if item.status != "RESOLVED" and identity not in pending:
            holds.append("QUEUE_LOST:" + kind)
        bindings.append(binding)
    others = [i for i in attention.repository.identities("attention:")
                  if i not in {b["identity"] for b in bindings}]
    return {"result": "HOLD" if holds else "OPERATIONAL_READBACK_COMPLETE", "holds": holds,
            "read_at": utc_now(), "root": str(root), "profile": PROFILE, "items": bindings,
            "other_attention_identities": others, "acknowledgers": config["acknowledgers"],
            "source_candidate": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                               capture_output=True).stdout.strip()}


def retain(output: Path, record: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=False)
    body = json.dumps(record, indent=2, sort_keys=True, default=str) + "\n"
    (output / "readback.json").write_text(body)
    (output / "digest-manifest.json").write_text(json.dumps(
        {"readback.json": "sha256:" + sha256(body.encode()).hexdigest()}, indent=2) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("prepare", "readback"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--acknowledger")
    parser.add_argument("--invocation")
    parser.add_argument("--work-revision", default="WO-220508")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args(argv)
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    if arguments.command == "prepare":
        if not arguments.acknowledger or not arguments.invocation:
            parser.error("prepare needs --acknowledger and --invocation")
        result = prepare(arguments.root, arguments.acknowledger, arguments.invocation, arguments.work_revision)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = readback(arguments.root)
    if arguments.output is not None:
        retain(arguments.output, result)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["result"] == "OPERATIONAL_READBACK_COMPLETE" else 2


if __name__ == "__main__":
    sys.exit(main())
