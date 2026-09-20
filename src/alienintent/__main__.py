"""Command-line presentation adapter for the operator control plane."""
from __future__ import annotations
import argparse
import importlib
import json
import re
import sys
from dataclasses import asdict, is_dataclass
from typing import Any

from alienintent.control_plane.application.operator import OperatorControlPlane

def _sanitize(value: object) -> str:
    return re.sub(r"(?i)(token|secret|key)=[^\s]+", r"\1=[REDACTED]", str(value))

def _factory(reference: str) -> Any:
    module, separator, name = reference.partition(":")
    if not separator: raise ValueError("profile factory must be module:callable")
    return getattr(importlib.import_module(module), name)()

def _service(profile: Any) -> OperatorControlPlane:
    if isinstance(profile, OperatorControlPlane): return profile
    return OperatorControlPlane(profile.name, profile.store, profile.work, profile.coordinator, profile.readiness)

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="alienintent")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--profile-factory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version")
    sub.add_parser("status")
    explain = sub.add_parser("explain"); explain.add_argument("target")
    for command in ("run", "resume", "stop", "cancel", "reconcile"):
        item = sub.add_parser(command); item.add_argument("target", nargs="?", default="service")
        item.add_argument("--actor", required=True); item.add_argument("--authority", required=True); item.add_argument("--expected-version", type=int, required=True); item.add_argument("--reason", required=True); item.add_argument("--idempotency-key", required=True)
    return parser

def _render(value: object, machine: bool) -> None:
    if is_dataclass(value): value = asdict(value)
    if machine: print(json.dumps(value, default=str, sort_keys=True))
    else: print(value if isinstance(value, str) else json.dumps(value, default=str, indent=2, sort_keys=True))

def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        raw = list(sys.argv[1:] if argv is None else argv)
        # Permit the conventional `command --json` spelling as well as global flags.
        if "--json" in raw and raw.index("--json") > 0:
            raw.remove("--json"); raw.insert(0, "--json")
        if "--profile-factory" in raw and raw.index("--profile-factory") > 0:
            index = raw.index("--profile-factory")
            value = raw.pop(index + 1); raw.pop(index)
            raw[0:0] = ["--profile-factory", value]
        args = parser.parse_args(raw)
        if args.command == "version": _render({"version": "0.0.0", "install": "python-package"}, args.json); return 0
        if not args.profile_factory: raise ValueError("--profile-factory is required")
        service = _service(_factory(args.profile_factory))
        if args.command == "status": result = service.status()
        elif args.command == "explain": result = service.explain(args.target)
        else:
            fields = {"target": args.target, "actor": args.actor, "authority": args.authority, "expected_version": args.expected_version, "reason": args.reason, "idempotency_key": args.idempotency_key}
            method = getattr(service, args.command)
            result = method(args.target, **fields) if args.command == "cancel" else method(**fields)
        _render(result, args.json); return 0
    except (ValueError, KeyError, AttributeError, ImportError) as error:
        _render({"error": _sanitize(error)}, getattr(locals().get("args", None), "json", False)); return 2

if __name__ == "__main__": raise SystemExit(main())
