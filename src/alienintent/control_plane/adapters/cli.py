"""Sanitized command-line presentation adapter for the operator control plane."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import importlib
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any

from alienintent.control_plane.application.operator import OperatorControlPlane, OperatorDenied


def _sanitize(value: object) -> str:
    """Map trusted operator failures to a closed, secret-safe vocabulary."""
    if isinstance(value, OperatorDenied):
        if str(value).startswith("readiness gate failed"):
            return "readiness-gate-failed"
        if str(value) == "stale expected version":
            return "stale-expected-version"
        return "authority-denied"
    if isinstance(value, KeyError):
        return "unknown-work-item"
    if isinstance(value, ValueError):
        return "invalid-command-arguments"
    return "internal-error"


def _argument_error(_: str) -> None:
    raise ValueError("invalid command arguments")


def _sanitized(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.error = _argument_error  # type: ignore[method-assign]
    return parser


def _factory(reference: str) -> Any:
    module, separator, name = reference.partition(":")
    if not separator:
        raise ValueError("profile factory must be module:callable")
    return getattr(importlib.import_module(module), name)()


def _parser() -> argparse.ArgumentParser:
    parser = _sanitized(argparse.ArgumentParser(prog="alienintent"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--profile-factory")
    sub = parser.add_subparsers(dest="command", required=True)
    _sanitized(sub.add_parser("version")); _sanitized(sub.add_parser("status")); _sanitized(sub.add_parser("health"))
    explain = _sanitized(sub.add_parser("explain")); explain.add_argument("target")
    for command in ("run", "resume", "stop", "cancel", "reconcile"):
        item = _sanitized(sub.add_parser(command)); item.add_argument("target", nargs="?", default="service")
        _mutation(item)
    decisions = _sanitized(sub.add_parser("decisions")).add_subparsers(dest="decision_command", required=True)
    _sanitized(decisions.add_parser("list"))
    show = _sanitized(decisions.add_parser("show")); show.add_argument("identity")
    decide = _sanitized(decisions.add_parser("decide")); decide.add_argument("identity"); decide.add_argument("--choice", required=True); decide.add_argument("--biu-version", type=int, required=True); _mutation(decide)
    return parser


def _mutation(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--actor", required=True); parser.add_argument("--authority", required=True)
    parser.add_argument("--intent", required=True); parser.add_argument("--expected-version", type=int, required=True); parser.add_argument("--reason", required=True); parser.add_argument("--idempotency-key", required=True)


def _render(value: object, machine: bool) -> None:
    if is_dataclass(value): value = asdict(value)
    print(json.dumps(value, default=str, sort_keys=True, indent=None if machine else 2))


def main(argv: list[str] | None = None) -> int:
    args = None
    try:
        raw = list(sys.argv[1:] if argv is None else argv)
        for flag in ("--json", "--profile-factory"):
            if flag in raw and raw.index(flag) > 0:
                index = raw.index(flag); values = raw[index:index + (2 if flag == "--profile-factory" else 1)]; del raw[index:index + len(values)]; raw[0:0] = values
        args = _parser().parse_args(raw)
        if args.command == "version": _render({"version": "0.0.0", "install": "python-package"}, args.json); return 0
        if not args.profile_factory: raise ValueError("--profile-factory is required")
        profile = _factory(args.profile_factory)
        service = OperatorControlPlane(profile.name, profile.store, profile.work, profile.coordinator, profile.readiness, lambda: datetime.now(UTC).isoformat())
        if args.command == "status": value = service.status()
        elif args.command == "health": value = {"live": True, "ready": bool(profile.readiness())}
        elif args.command == "explain": value = service.explain(args.target)
        elif args.command == "decisions":
            fields = {key: value for key, value in vars(args).items() if key not in {"identity", "command", "decision_command", "json", "profile_factory"}}
            value = service.decisions_list() if args.decision_command == "list" else service.decisions_show(args.identity) if args.decision_command == "show" else service.decisions_decide(args.identity, target=args.identity, **fields)
        else:
            value = getattr(service, args.command)(**vars(args))
        _render(value, args.json); return 0
    except Exception as error:
        _render({"error": _sanitize(error)}, bool(getattr(args, "json", False))); return 2
