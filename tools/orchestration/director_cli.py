#!/usr/bin/env python3
"""Program Director CLI — the operator surface for the post-Wave-1 program.

    director_cli.py status                     program state, next task, Founder decisions
    director_cli.py route  <task_type> [--risk] show the routing decision and five answers
    director_cli.py ask    --task T --subject S --body-file F   request coordinator review
    director_cli.py await  --request <id> [--timeout N]          wait for the correlated reply
    director_cli.py codex  --prompt-file F [--sandbox read-only] run a bounded fresh session
    director_cli.py whoami                     coordinator identity via `claude agents --json`

Never releases a BIU, never changes Project lifecycle state.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from bridge import DEFAULT_ROOT, Bridge
from codex_session import CodexSession
from director import (DEFAULT_STATE, REPO, ProgramState, RiskClass, classify_risk,
                      resolved_codex_model, route)

COORDINATOR = "claude-bootstrap-coordinator"


def _git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


def coordinator_identity() -> dict:
    """Supported discovery: `claude agents --json`. No socket is touched."""
    try:
        out = subprocess.run(["claude", "agents", "--json"], capture_output=True, text=True,
                             timeout=60).stdout
        for s in json.loads(out):
            if s.get("kind") == "interactive" and s.get("cwd") == str(REPO):
                return {"name": s.get("name"), "session_id": s.get("sessionId"),
                        "pid": s.get("pid"), "status": s.get("status"), "cwd": s.get("cwd")}
    except Exception as exc:
        return {"error": str(exc)[:120]}
    return {"error": "no interactive coordinator session found for this repository"}


def cmd_status(args) -> int:
    state = ProgramState(args.state)
    print(f"program        : post-wave1-to-wave2")
    print(f"current phase  : {state.current_phase()}")
    print(f"completed      : {', '.join(state._data.get('completed_phases') or []) or '(none)'}")
    print(f"repo HEAD      : {_git('rev-parse', 'HEAD')[:8]}  origin/main: {_git('rev-parse', 'origin/main')[:8]}")
    print(f"codex model    : {resolved_codex_model()}")
    print("\ntasks:")
    for t in state.tasks():
        print(f"  {t['task_id']:20} ph{t['phase']:<4} {t['status']:26} {t['risk_class']:6} {t['assigned_actor']}")
    fd = state.founder_decisions_required()
    if fd:
        print("\nFOUNDER DECISIONS REQUIRED (program stops on these branches):")
        for t in fd:
            print(f"  {t['task_id']}: {t['title']}")
    nxt = state.next_task()
    print(f"\nnext task      : {nxt['task_id'] + ' — ' + nxt['title'] if nxt else '(none ready)'}")
    return 0


def cmd_route(args) -> int:
    risk = RiskClass(args.risk) if args.risk else classify_risk(args.task_type)
    d = route(task_type=args.task_type, risk=risk,
              deterministic_possible=args.deterministic, bounded_input=args.bounded)
    print(json.dumps(d.as_record(), indent=1))
    return 0


def cmd_ask(args) -> int:
    body = Path(args.body_file).read_text() if args.body_file else args.body
    bridge = Bridge(args.root)
    mid = bridge.send(to_role=COORDINATOR, message_type=args.type, task_id=args.task,
                      subject=args.subject, body=body, requires_reply=True)
    msg = bridge.get(mid)
    print(json.dumps({"message_id": mid, "correlation_id": msg["correlation_id"],
                      "to": COORDINATOR, "task_id": args.task,
                      "coordinator": coordinator_identity()}, indent=1))
    return 0


def cmd_await(args) -> int:
    reply = Bridge(args.root).wait_for_reply(args.request, timeout_s=args.timeout, poll_s=2.0)
    if reply is None:
        print(json.dumps({"request": args.request, "reply": None,
                          "note": "no correlated reply within the window"}, indent=1))
        return 1
    print(json.dumps({"request": args.request, "reply_id": reply["message_id"],
                      "correlation_id": reply["correlation_id"], "from": reply["from_role"],
                      "body": reply["body"]}, indent=1))
    return 0


def cmd_codex(args) -> int:
    prompt = Path(args.prompt_file).read_text()
    before = _git("rev-parse", "HEAD")
    session = CodexSession(workdir=REPO)
    res = session.run(prompt=prompt, sandbox=args.sandbox, prompt_path=args.prompt_file,
                      output_file=Path(args.output) if args.output else None,
                      sha_before=before, timeout_s=args.timeout)
    res.sha_after = _git("rev-parse", "HEAD")
    print(json.dumps(res.as_record(), indent=1))
    if res.terminal_message:
        print("\n--- terminal message ---")
        print(res.terminal_message[:2000])
    return 0 if res.ok else 1


def cmd_whoami(args) -> int:
    print(json.dumps(coordinator_identity(), indent=1))
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="AlienIntent local Program Director")
    ap.add_argument("--state", default=str(DEFAULT_STATE))
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("whoami").set_defaults(func=cmd_whoami)

    r = sub.add_parser("route"); r.set_defaults(func=cmd_route)
    r.add_argument("task_type")
    r.add_argument("--risk", choices=[x.value for x in RiskClass])
    r.add_argument("--deterministic", action="store_true")
    r.add_argument("--bounded", action="store_true")

    a = sub.add_parser("ask"); a.set_defaults(func=cmd_ask)
    a.add_argument("--task", required=True)
    a.add_argument("--subject", required=True)
    a.add_argument("--body-file")
    a.add_argument("--body", default="")
    a.add_argument("--type", default="REVIEW_REQUEST")

    w = sub.add_parser("await"); w.set_defaults(func=cmd_await)
    w.add_argument("--request", required=True)
    w.add_argument("--timeout", type=float, default=3600)

    c = sub.add_parser("codex"); c.set_defaults(func=cmd_codex)
    c.add_argument("--prompt-file", required=True)
    c.add_argument("--sandbox", default="read-only")
    c.add_argument("--output")
    c.add_argument("--timeout", type=int, default=1800)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
