"""Human operator surface over an existing C1 attention profile (WO-220508, FX-B5).

- `list`, `show` and `history` only read. Rendering an item is never human receipt.
- `acknowledge` records the named human's explicit, item-bound, timestamped receipt of the exact
  version shown. It never resolves, notifies or activates anything.
- The profile store must already exist, and the acknowledgers come from the configuration file,
  never from the command line.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import uuid

from alienintent.composition.control_plane_profile import AttentionProfile
from alienintent.control_plane.domain.attention import AttentionHold, AttentionItem
from alienintent.execution_coordination.ports.operational_store import VersionConflict

MODULE = "alienintent.composition.attention_inbox"
EXIT_HOLD = 2
CONFIG_KEYS = ("root", "project", "profile", "invocation", "acknowledgers")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def load_config(path: Path | None) -> dict[str, object]:
    if path is None:
        raise AttentionHold("INBOX_CONFIGURATION_MISSING")
    try:
        document = json.loads(Path(path).read_text())
    except FileNotFoundError as error:
        raise AttentionHold("INBOX_CONFIGURATION_MISSING") from error
    except (OSError, ValueError) as error:
        raise AttentionHold("INBOX_CONFIGURATION_INVALID") from error
    if (not isinstance(document, dict) or any(k not in document for k in CONFIG_KEYS)
            or not all(isinstance(document[k], str) and document[k].strip() for k in CONFIG_KEYS[:4])
            or not isinstance(document["acknowledgers"], list)
            or not all(isinstance(a, str) and a.strip() for a in document["acknowledgers"])):
        raise AttentionHold("INBOX_CONFIGURATION_INVALID")
    if not (Path(document["root"]) / "attention.sqlite").is_file():
        raise AttentionHold("ATTENTION_STORE_ABSENT")
    return document


def open_profile(config: dict[str, object], clock=utc_now) -> AttentionProfile:
    return AttentionProfile(Path(config["root"]), project=config["project"], name=config["profile"],
        invocation=config["invocation"], clock=clock, next_id=lambda: "inbox:" + uuid.uuid4().hex,
        resolvers=(), acknowledgers=tuple(config["acknowledgers"]))


def summary(item: AttentionItem) -> dict[str, object]:
    return {"identity": item.identity, "version": item.version, "status": item.status,
            "kind": item.origin.kind, "work_ref": item.origin.work_ref,
            "event_identity": item.origin.event_identity, "lane": item.origin.lane,
            "attempts": [a.status for a in item.attempts],
            "acknowledged_by": None if item.acknowledgement is None else item.acknowledgement.actor}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=MODULE, description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("list", "show", "history", "acknowledge"))
    parser.add_argument("identity", nargs="?")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--actor")
    parser.add_argument("--expected-version", type=int)
    parser.add_argument("--statement")
    arguments = parser.parse_args(argv)
    try:
        attention = open_profile(load_config(arguments.config)).attention
        if arguments.command == "list":
            result: object = [summary(item) for item in attention.list_pending()]
        elif not arguments.identity:
            raise AttentionHold("ATTENTION_IDENTITY_REQUIRED")
        elif arguments.command == "show":
            result = asdict(attention.show(arguments.identity))
        elif arguments.command == "history":
            result = list(attention.history(arguments.identity))
        else:
            if arguments.expected_version is None:
                raise AttentionHold("EXPECTED_VERSION_REQUIRED")
            result = asdict(attention.acknowledge(arguments.identity, arguments.actor or "",
                                                  arguments.expected_version, arguments.statement or ""))
    except AttentionHold as hold:
        print(json.dumps({"hold": hold.reason}), flush=True)
        return EXIT_HOLD
    except VersionConflict:
        print(json.dumps({"hold": "VERSION_CONFLICT"}), flush=True)
        return EXIT_HOLD
    except KeyError:
        print(json.dumps({"hold": "ATTENTION_ITEM_UNKNOWN"}), flush=True)
        return EXIT_HOLD
    print(json.dumps(result, default=str, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
