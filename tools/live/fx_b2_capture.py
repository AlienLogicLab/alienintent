#!/usr/bin/env python3
"""Read back one isolated FX-B2 profile into content-addressed evidence files.

This reader makes no acceptance verdict and does not touch the factory dispatcher or Project.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
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
    if not (root / "liveness.sqlite").is_file():
        raise ValueError("EVIDENCE_STORE_MISSING")
    store = SQLiteOperationalStore(root / "liveness.sqlite")
    _, authority = store.read_state(profile, authority_name)
    expiry = authority.get("expires_at")
    at = time.time() if now is None else now
    policy = config.get("policy", {})
    durations = [policy.get(key) for key in ("grace_seconds", "interval_seconds", "confirmation_seconds")]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value <= 0 for value in durations):
        raise ValueError("POLICY_INVALID")
    grace, interval, confirmation = durations
    # One gap window, two real suppression grace periods, then a confirmation window.
    minimum_expiry = at + 3 * grace + 2 * interval + confirmation
    if (authority.get("schema_version") != 1 or authority.get("active") is not True
            or type(authority.get("epoch")) is not int or authority["epoch"] < 1
            or authority.get("invocation") != config["host_invocation"]
            or type(expiry) not in (int, float) or not math.isfinite(expiry) or expiry <= minimum_expiry):
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


def launch(root: Path, *, now: float | None = None) -> dict[str, object]:
    """The fixture's only launch entrypoint: admission first, then the C5 CLI."""
    admitted = preflight(root, now=now)
    argv = [sys.executable, "-B", "-m", "alienintent.composition.monitor_host", "launch",
            "--config", str(admitted["config"]), "--actor", "factory-director",
            "--authority", "fx-b2-operational-authorization"]
    env = dict(os.environ)
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    result = subprocess.run(argv, capture_output=True, text=True, env=env, check=False)
    return {"argv": argv, "exit_status": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def capture(root: Path, output: Path, source_sha: str) -> dict[str, object]:
    root = root.resolve(strict=True)
    config_path = root.parent / "fx-b2-supervision.json"
    config = json.loads(config_path.read_text())
    if Path(config["root"]).resolve(strict=True) != root or config["profile"] != "fx-b2-liveness-operational":
        raise ValueError("FX-B2_PROFILE_MISMATCH")
    if (root / "state.json").exists():
        raise ValueError("FACTORY_STATE_IN_ISOLATED_ROOT")
    required = ("liveness.sqlite", "attention.sqlite", "monitor.sqlite", "monitor-host.sqlite")
    if any(not (root / name).is_file() for name in required):
        raise ValueError("EVIDENCE_STORE_MISSING")
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
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    if args.preflight and args.launch:
        parser.error("--preflight and --launch are mutually exclusive")
    if not (args.preflight or args.launch) and (args.output is None or args.source_sha is None):
        parser.error("--output and --source-sha are required for capture")
    result = (preflight(args.root) if args.preflight else launch(args.root) if args.launch else
              capture(args.root, args.output, args.source_sha))
    print(json.dumps(result, sort_keys=True))
    if args.launch:
        raise SystemExit(result["exit_status"])


if __name__ == "__main__":
    main()
