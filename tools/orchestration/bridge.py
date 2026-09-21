#!/usr/bin/env python3
"""Program Director <-> Claude bootstrap coordinator bridge — transport only.

Post-Wave-1 orchestration infrastructure. **Not** an AlienIntent product capability and
**not** execution authority for BIU lifecycle state.

Why a mailbox rather than a peer helper: `claude agents --json` is a supported way to
*discover* a running session (name, session id, pid, cwd, status), but the installed CLI
exposes no supported way for an external process to *send* a message into one. The Unix
socket under `/run/user/<uid>/cc-socks/` is an undocumented protocol and is deliberately
left alone. So this is the smallest explicit bridge, outside Git, per the bootstrap order
of preference.

Identity is the stable `message_id`. Never an observation timestamp — Wave 1's attention
queue woke a coordinator three times for one event by anchoring on a field the writer
rewrote, and that failure is not repeated here.

The bridge holds **no decision logic**. It transports requests and replies.

It is deliberately separate from the AlienIntent product attention queue
(`coordinator-attention.jsonl`): orchestration traffic must not mix with product runtime
attention.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".local/state/alienintent/orchestration"

REQUIRED_FIELDS = (
    "message_id", "correlation_id", "sent_at", "from_role", "to_role", "message_type",
    "task_id", "subject", "body", "requires_reply", "reply_to", "handled_at", "status",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Bridge:
    def __init__(self, root: Path | str = DEFAULT_ROOT) -> None:
        self.root = Path(root)
        for sub in ("inbox", "outbox", "acknowledgements"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)

    # --- writing ----------------------------------------------------------------

    def _publish(self, folder: str, record: dict) -> None:
        """Write atomically: a reader never observes a half-written record."""
        target = self.root / folder / f"{record['message_id']}.json"
        tmp = target.with_suffix(".json.partial")
        tmp.write_text(json.dumps(record, indent=1) + "\n")
        os.chmod(tmp, 0o600)
        Path.replace(tmp, target)

    def send(self, to_role: str, message_type: str, task_id: str, subject: str, body: str,
             *, from_role: str = "program-director", requires_reply: bool = False,
             correlation_id: str | None = None, reply_to: str | None = None,
             body_path: str | None = None) -> str:
        record = {
            "message_id": f"msg-{uuid.uuid4().hex[:12]}",
            "correlation_id": correlation_id or f"cor-{uuid.uuid4().hex[:12]}",
            "sent_at": _now(),
            "from_role": from_role,
            "to_role": to_role,
            "message_type": message_type,
            "task_id": task_id,
            "subject": subject,
            "body": body,
            "body_path": body_path,
            "requires_reply": bool(requires_reply),
            "reply_to": reply_to,
            "handled_at": None,
            "status": "sent",
        }
        folder = "outbox" if from_role != "program-director" else "inbox"
        self._publish(folder, record)
        return record["message_id"]

    def reply(self, request_id: str, from_role: str, body: str,
              message_type: str = "REVIEW_RESULT", body_path: str | None = None) -> str:
        request = self.get(request_id)
        if request is None:
            raise KeyError(request_id)
        return self.send(
            to_role=request["from_role"], message_type=message_type,
            task_id=request["task_id"], subject=f"RE: {request['subject']}",
            body=body, from_role=from_role, correlation_id=request["correlation_id"],
            reply_to=request_id, body_path=body_path)

    def acknowledge(self, message_id: str, by: str, note: str = "") -> None:
        """Idempotent: acknowledging twice records once and never re-delivers."""
        path = self.root / "acknowledgements" / f"{message_id}.json"
        if path.exists():
            return
        tmp = path.with_suffix(".json.partial")
        tmp.write_text(json.dumps(
            {"message_id": message_id, "by": by, "note": note, "handled_at": _now()}, indent=1) + "\n")
        Path.replace(tmp, path)

    # --- reading ----------------------------------------------------------------

    def _all(self) -> list[dict]:
        out = []
        for folder in ("inbox", "outbox"):
            for f in sorted((self.root / folder).glob("*.json")):
                try:
                    out.append(json.loads(f.read_text()))
                except Exception:
                    continue
        return out

    def _acks(self) -> dict:
        acks = {}
        for f in (self.root / "acknowledgements").glob("*.json"):
            try:
                a = json.loads(f.read_text())
                acks[a["message_id"]] = a
            except Exception:
                continue
        return acks

    def get(self, message_id: str) -> dict | None:
        acks = self._acks()
        for m in self._all():
            if m["message_id"] == message_id:
                if message_id in acks:
                    m = {**m, "status": "handled", "handled_at": acks[message_id]["handled_at"]}
                return m
        return None

    def pending(self, to_role: str) -> list[dict]:
        """Unacknowledged messages addressed to this role, oldest first."""
        acks = self._acks()
        return sorted(
            (m for m in self._all() if m["to_role"] == to_role and m["message_id"] not in acks),
            key=lambda m: m["sent_at"])

    def replies_to(self, request_id: str) -> list[dict]:
        return [m for m in self._all() if m.get("reply_to") == request_id]

    def wait_for_reply(self, request_id: str, timeout_s: float = 3600, poll_s: float = 5.0):
        """Block until a reply correlated to this request appears, or time out."""
        deadline = time.monotonic() + timeout_s
        while True:
            found = self.replies_to(request_id)
            if found:
                return found[0]
            if time.monotonic() >= deadline:
                return None
            time.sleep(min(poll_s, max(0.0, deadline - time.monotonic())))
