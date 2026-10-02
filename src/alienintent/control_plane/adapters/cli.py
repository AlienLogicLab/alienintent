"""Sanitized command-line presentation adapter for the operator control plane."""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import importlib
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any

from alienintent.control_plane.application.operator import (
    OperatorControlPlane, OperatorDenied, assess_work, import_work, migrate_work, register_work, show_work)
from alienintent.execution_coordination.application.factory_coordinator import TerminalWork
from alienintent.execution_coordination.domain.escalation import SupersededDecision
from alienintent.execution_coordination.ports.operational_store import VersionConflict


# Typed work-registry refusals the operator may see by code; every other code stays internal.
_WORK_CODES = {"MIGRATION_CONFLICT": "migration-conflict", "INVALID_REQUEST_REF": "invalid-request-ref",
               "WORK_REGISTRY_BUSY": "work-registry-busy", "WORK_REGISTRY_UNAVAILABLE": "work-registry-unavailable",
               "POINTER_MISMATCH": "pointer-mismatch", "COMMIT_NOT_RETAINED": "commit-not-retained",
               "PARENT_NOT_REGISTERED": "parent-not-registered", "LABEL_IN_USE": "label-in-use",
               "INVALID_WORK_ITEM": "invalid-work-item", "GIT_READ_FAILED": "git-read-failed",
               "TAG_WRITE_FAILED": "tag-write-failed", "PUBLICATION_FAILED": "publication-failed"}


def _sanitize(value: object) -> str:
    """Map trusted operator failures to a closed, secret-safe vocabulary."""
    if getattr(value, "code", None) in _WORK_CODES:
        return _WORK_CODES[getattr(value, "code")]
    if isinstance(value, OperatorDenied):
        if str(value).startswith("readiness gate failed"):
            return "readiness-gate-failed"
        if str(value) == "stale expected version":
            return "stale-expected-version"
        return "authority-denied"
    if isinstance(value, VersionConflict):
        return "stale-expected-version"
    if isinstance(value, SupersededDecision):
        return "superseded-decision"
    if isinstance(value, TerminalWork):
        return "terminal-work"
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
    _sanitized(sub.add_parser("version")); _sanitized(sub.add_parser("status")); _sanitized(sub.add_parser("health")); _sanitized(sub.add_parser("doctor"))
    explain = _sanitized(sub.add_parser("explain")); explain.add_argument("target")
    for command in ("run", "resume", "stop", "cancel", "reconcile"):
        item = _sanitized(sub.add_parser(command)); item.add_argument("target", nargs="?", default="service")
        _mutation(item)
    decisions = _sanitized(sub.add_parser("decisions")).add_subparsers(dest="decision_command", required=True)
    _sanitized(decisions.add_parser("list"))
    show = _sanitized(decisions.add_parser("show")); show.add_argument("identity")
    decide = _sanitized(decisions.add_parser("decide")); decide.add_argument("identity"); decide.add_argument("--choice", required=True); decide.add_argument("--biu-version", type=int, required=True); _mutation(decide)
    work = _sanitized(sub.add_parser("work")).add_subparsers(dest="work_command", required=True)
    migrate = _sanitized(work.add_parser("migrate")); migrate.add_argument("--snapshot", required=True)
    migrate.add_argument("--profile", dest="profiles", action="append", required=True)
    register = _sanitized(work.add_parser("register")); _packet(register)
    register.add_argument("--parent"); register.add_argument("--kind", default="BIU")
    imported = _sanitized(work.add_parser("import")); _packet(imported); imported.add_argument("--issue", required=True)
    for name in ("assessment", "approval", "verification"):
        imported.add_argument("--" + name)
    show_work_item = _sanitized(work.add_parser("show")); show_work_item.add_argument("target")
    assess = _sanitized(work.add_parser("assess")); assess.add_argument("target")
    assess.add_argument("--file"); assess.add_argument("--commit"); assess.add_argument("--recover")
    return parser


def _packet(parser: argparse.ArgumentParser) -> None:
    for name in ("file", "repo", "path", "commit", "label"):
        parser.add_argument("--" + name, required=True)


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
        if args.command == "doctor":
            doctor = getattr(profile, "doctor", None)
            if doctor is None:
                _render({"error": "doctor-not-configured"}, args.json)
                return 1
            report = doctor.run()
            _render(report.as_dict(), args.json)
            return report.exit_code
        if args.command == "work":
            registry = getattr(profile, "work_registry", None)
            if registry is None:
                _render({"error": "work-registry-not-configured"}, args.json)
                return 1
            if args.work_command == "show":
                _render(show_work(registry.records, args.target), args.json)
                return 0
            if args.work_command == "assess":
                if (args.file is None) != (args.commit is None) or (args.file is not None and args.recover):
                    raise ValueError("--file and --commit only together, and never with --recover")
                if getattr(registry, "assessment", None) is None:
                    _render({"error": "readiness-not-configured"}, args.json)
                    return 1
                revision = None
                if args.file is not None:
                    with open(args.file, "rb") as handle:
                        revision = (handle.read(), args.commit)
                _render(assess_work(registry.assessment, args.target, revision, args.recover), args.json)
                return 0
            if args.work_command == "migrate":
                with open(args.snapshot, encoding="utf-8") as handle:
                    snapshot = json.load(handle)
                _render(migrate_work(registry.identities, snapshot, args.profiles), args.json)
                return 0
            with open(args.file, "rb") as handle:
                packet = handle.read()
            if args.work_command == "register":
                value = register_work(registry.records, packet, args.repo, args.path, args.commit, args.label,
                                      args.kind, args.parent)
            else:
                evidence = {name: None if getattr(args, name) is None else json.loads(getattr(args, name))
                            for name in ("assessment", "approval", "verification")}
                value = import_work(registry.records, packet, args.repo, args.path, args.commit, args.label,
                                    args.issue, evidence)
            _render(value, args.json)
            return 0
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
