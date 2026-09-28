#!/usr/bin/env python3
"""Read back one isolated FX-B2 profile into content-addressed evidence files.

This reader makes no acceptance verdict and does not touch the factory dispatcher or Project.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def preflight(root: Path, *, now: float | None = None) -> dict[str, object]:
    """Refuse an incomplete isolated authority/entry before the caller launches C5."""
    root = root.resolve(strict=True)
    config = json.loads((root.parent / "fx-b2-supervision.json").read_text())
    profile = "fx-b2-liveness-operational"
    authority_name = "fx-b2-operational-authorization"
    if (Path(config["root"]).resolve(strict=True) != root or config["profile"] != profile
            or config["host_authority"] != authority_name or (root / "state.json").exists()):
        raise ValueError("FX_B2_PROFILE_MISMATCH")
    store = SQLiteOperationalStore(root / "liveness.sqlite")
    _, authority = store.read_state(profile, authority_name)
    expiry = authority.get("expires_at")
    at = time.time() if now is None else now
    if (authority.get("schema_version") != 1 or authority.get("active") is not True
            or type(authority.get("epoch")) is not int or authority["epoch"] < 1
            or authority.get("invocation") != config["host_invocation"]
            or type(expiry) not in (int, float) or not math.isfinite(expiry) or expiry <= at):
        raise ValueError("AUTHORITY_UNAVAILABLE")
    entries = store.list_states(profile, "liveness-active:")
    if len(entries) != 1:
        raise ValueError("KNOWN_ACTIVE_UNAVAILABLE")
    active = entries[0][2]
    if (active.get("schema_version") != 1 or active.get("biu") != "FX-B2-PROBE-" + config["host_invocation"]
            or active.get("stage") != "IMPLEMENT" or active.get("generation") != 1
            or active.get("authority") != authority_name or active.get("budget_admitted") is not True):
        raise ValueError("KNOWN_ACTIVE_INVALID")
    return {"config": str(root.parent / "fx-b2-supervision.json"), "authority": authority,
            "active": active, "profile": profile}


def capture(root: Path, output: Path, source_sha: str) -> dict[str, object]:
    root = root.resolve(strict=True)
    config_path = root.parent / "fx-b2-supervision.json"
    config = json.loads(config_path.read_text())
    if Path(config["root"]).resolve(strict=True) != root or config["profile"] != "fx-b2-liveness-operational":
        raise ValueError("FX-B2_PROFILE_MISMATCH")
    if (root / "state.json").exists():
        raise ValueError("FACTORY_STATE_IN_ISOLATED_ROOT")
    profile = config["profile"]
    store = SQLiteOperationalStore(root / "liveness.sqlite")
    raw = {
        "config": config,
        "liveness_states": store.list_states(profile, ""),
        "effect_ledger": store.effect_ledger(profile),
        "attention_states": SQLiteOperationalStore(root / "attention.sqlite").list_states(profile, ""),
        "monitor_states": SQLiteOperationalStore(root / "monitor.sqlite").list_states(profile, ""),
        "host_states": SQLiteOperationalStore(root / "monitor-host.sqlite").list_states(profile, ""),
        "host_log": (root / "monitor-host.log").read_text() if (root / "monitor-host.log").exists() else None,
        "observer_log": (root / "monitor-observer.log").read_text() if (root / "monitor-observer.log").exists() else None,
    }
    blob = canonical(raw)
    digest = sha256(blob).hexdigest()
    observations = output / "observations"
    observations.mkdir(parents=True, exist_ok=True)
    target = observations / digest
    if target.exists():
        if target.read_bytes() != blob:
            raise ValueError("OBSERVATION_COLLISION")
    else:
        with target.open("xb") as stream:
            stream.write(blob)
    return {"fixture": "FX-B2", "label": "ISOLATED_OPERATIONAL_MECHANICS",
            "source_sha": source_sha, "profile": profile, "root": str(root),
            "observation_ref": {"revision_digest": "sha256:" + digest, "locator": "observations/" + digest},
            "non_claims": ["No real #125 dispatcher or Project effect was exercised by this capture.",
                           "This capture makes no SF-REQ-056-AC-08 or SWF-29 retirement claim."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-sha")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if not args.preflight and (args.output is None or args.source_sha is None):
        parser.error("--output and --source-sha are required for capture")
    result = preflight(args.root) if args.preflight else capture(args.root, args.output, args.source_sha)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
