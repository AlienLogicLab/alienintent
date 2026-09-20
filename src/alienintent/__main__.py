"""First-class, dependency-free AlienIntent control-plane CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys

from alienintent.control_plane.application.operator import OperatorControlPlane, OperatorError


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alienintent")
    parser.add_argument("--json", action="store_true", dest="machine")
    parser.add_argument("--profile-factory", help="dotted callable returning a configured profile")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version")
    sub.add_parser("status")
    explain = sub.add_parser("explain"); explain.add_argument("biu")
    for name in ("run", "resume"):
        command = sub.add_parser(name); _mutation_arguments(command)
    decisions = sub.add_parser("decisions"); decision_sub = decisions.add_subparsers(dest="decision_command", required=True)
    decision_sub.add_parser("list")
    show = decision_sub.add_parser("show"); show.add_argument("id")
    decide = decision_sub.add_parser("decide"); decide.add_argument("id"); decide.add_argument("choice"); _mutation_arguments(decide)
    for name in ("stop", "cancel", "reconcile"):
        command = sub.add_parser(name); command.add_argument("target", nargs="?"); _mutation_arguments(command)
    return parser


def _mutation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--actor", required=True); parser.add_argument("--authority", required=True)
    parser.add_argument("--expected-version", required=True, type=int); parser.add_argument("--reason", required=True)
    parser.add_argument("--idempotency-key", required=True)


def _profile(factory: str | None) -> object:
    if not factory:
        raise OperatorError("profile is required")
    module_name, separator, attribute = factory.partition(":")
    if not separator or not module_name or not attribute:
        raise OperatorError("profile factory must be module:callable")
    return getattr(importlib.import_module(module_name), attribute)()


def _sanitize(value: object) -> object:
    text = str(value)
    return re.sub(r"(?i)(token|secret|key)=\S+", r"\1=[redacted]", text)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "version": result: object = {"version": "0.0.0", "diagnostics": "installed"}
        else:
            control = OperatorControlPlane(_profile(args.profile_factory))
            if args.command == "status": result = control.status()
            elif args.command == "explain": result = control.explain(args.biu)
            elif args.command in {"run", "resume"}: result = getattr(control, args.command)(actor=args.actor, authority=args.authority, expected_version=args.expected_version, reason=args.reason, idempotency_key=args.idempotency_key)
            elif args.command == "decisions":
                inbox = control.decisions()
                result = [vars(value) for value in inbox.list_open()] if args.decision_command == "list" else (vars(inbox.show(args.id)) if args.decision_command == "show" else control.decide(actor=args.actor, authority=args.authority, identity=args.id, expected_version=args.expected_version, reason=args.reason, idempotency_key=args.idempotency_key, choice=args.choice))
            else: result = control.invoke(args.command, args.target, actor=args.actor, authority=args.authority, expected_version=args.expected_version, reason=args.reason, idempotency_key=args.idempotency_key)
        print(json.dumps(result, default=str, sort_keys=True) if args.machine else result)
        return 0
    except (OperatorError, ValueError, KeyError) as error:
        payload = {"error": _sanitize(error)}
        print(json.dumps(payload, sort_keys=True) if args.machine else payload)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
