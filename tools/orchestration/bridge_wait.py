#!/usr/bin/env python3
"""Session-bound waiter: wakes the resident Claude coordinator on Program Director mail.

Same proven pattern as the Wave 1 attention waiter, and for the same reason: a
Claude-tracked background task's **exit** is what makes the harness deliver a completion
event into the resident session. systemd processes and file writes are invisible to it.

    python3 bridge_wait.py            # arm; exits 0 when new Director mail arrives

It decides nothing and mutates nothing — it does not even acknowledge the message, because
acknowledgement asserts the request was *handled*, which only the coordinator can say.

Exit 0 = new mail (printed). Exit 1 = the window closed quietly.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bridge import DEFAULT_ROOT, Bridge

ROLE = "claude-bootstrap-coordinator"
DEFAULT_TIMEOUT_S = 21600
POLL_S = 5.0


def _wait_for_change(path: Path, seconds: float) -> None:
    target = path if path.exists() else path.parent
    try:
        subprocess.run(["inotifywait", "-q", "-t", str(max(1, int(seconds))),
                        "-e", "modify,create,moved_to,close_write", str(target)],
                       capture_output=True, timeout=seconds + 5)
    except Exception:
        time.sleep(min(seconds, POLL_S))


def wait_for_mail(root: Path | str, surfaced: set[str], timeout_s: float, poll_s: float = POLL_S):
    bridge = Bridge(root)
    deadline = time.monotonic() + timeout_s
    while True:
        new = [m for m in bridge.pending(ROLE) if m["message_id"] not in surfaced]
        if new:
            return new
        if time.monotonic() >= deadline:
            return []
        if poll_s < 1:
            time.sleep(poll_s)
        else:
            _wait_for_change(Path(root) / "inbox", min(60, deadline - time.monotonic()))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Wake the resident coordinator on Director mail")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    ap.add_argument("--poll", type=float, default=POLL_S)
    args = ap.parse_args(argv)

    bridge = Bridge(args.root)
    # Anything already pending is already in front of the coordinator; do not re-report it.
    surfaced = {m["message_id"] for m in bridge.pending(ROLE)}
    if surfaced:
        print(f"armed; {len(surfaced)} message(s) already pending and not re-reported", flush=True)

    mail = wait_for_mail(args.root, surfaced, args.timeout, args.poll)
    if not mail:
        print("no Program Director mail in this window; re-arm to keep the bridge live")
        return 1

    print(f"{len(mail)} Program Director message(s) require the coordinator:")
    for m in mail:
        print(f"  - [{m['message_type']}] task={m['task_id']} correlation={m['correlation_id']}")
        print(f"    subject: {m['subject']}")
        print(f"    reply with: bridge.reply('{m['message_id']}', from_role='{ROLE}', body=...)")
    print(json.dumps({"woke_for": [m["message_id"] for m in mail],
                      "tasks": sorted({m["task_id"] for m in mail})}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
