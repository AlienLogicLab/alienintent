"""Fresh-invocation runner: reconstruct from a pinned manifest, or compare documents.

Inputs are the explicit arguments only. No stdin, environment value or transcript is read, so
conversation memory can be neither an input nor an authority.
Exit status: 0 RECONSTRUCTED/EQUAL, 1 MISMATCH, 2 HOLD, 3 ERROR (an unexpected failure is never
a mismatch, a hold or a pass).
"""
import argparse
import json
from pathlib import Path
import sys

from alienintent.composition.control_plane_profile import ContextProfile
from alienintent.context_assembly.domain.reconstruction import (
    DERIVATION_RULE, EPISODE_SUBSTITUTE, ContextHold, HoldReason, canonical, compare,
)
from alienintent.evidence_learning.domain.refs import EvidenceHold
from alienintent.execution_coordination.ports.operational_store import SchemaIncompatible, StoreUnavailable

HOLD_EXIT = 2
ERROR_EXIT = 3


def _emit(document: dict[str, object]) -> None:
    sys.stdout.write(canonical(document).decode() + "\n")


def reconstruct(arguments: argparse.Namespace) -> int:
    inputs = {"manifest_ref": arguments.manifest, "project": arguments.project, "profile": arguments.profile}
    try:
        profile = ContextProfile(arguments.root, project=arguments.project, name=arguments.profile,
                                 invocation=arguments.invocation)
    except (OSError, StoreUnavailable, SchemaIncompatible) as error:
        result: object = ContextHold(HoldReason.STORE_UNAVAILABLE, (str(arguments.root),), str(error))
    except EvidenceHold as error:
        result = ContextHold(HoldReason.EVIDENCE_UNAVAILABLE, (str(arguments.root),), str(error))
    else:
        result = profile.context.reconstruct(arguments.manifest)
    if isinstance(result, ContextHold):
        _emit(result.document() | {"inputs": inputs, "invocation": arguments.invocation})
        return HOLD_EXIT
    observation = profile.context.retain(result, arguments.observer)
    _emit({"status": "RECONSTRUCTED", "inputs": inputs, "invocation": arguments.invocation,
           "manifest_ref": result.manifest_ref, "manifest_digest": result.manifest_digest,
           "manifest_observation": dict(result.manifest_observation), "document": result.document,
           "digest": result.digest, "observation_ref": {"revision_digest": observation.revision_digest,
                                                        "locator": observation.locator},
           "labels": [DERIVATION_RULE, EPISODE_SUBSTITUTE]})
    return 0


def compare_outputs(arguments: argparse.Namespace) -> int:
    outputs = {}
    for path in arguments.outputs:
        try:
            outputs[path] = json.loads(Path(path).read_text())
        except (OSError, ValueError):
            outputs[path] = None
    holds = sorted(path for path, output in outputs.items()
                   if not isinstance(output, dict) or output.get("status") != "RECONSTRUCTED"
                   or not isinstance(output.get("document"), dict))
    if holds:
        _emit({"verdict": "HOLD", "holds": holds})
        return HOLD_EXIT
    verdict = compare({path: output["document"] for path, output in outputs.items()})
    _emit(verdict)
    return 0 if verdict["verdict"] == "EQUAL" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("reconstruct")
    run.add_argument("--root", required=True, type=Path)
    run.add_argument("--project", required=True)
    run.add_argument("--profile", required=True)
    run.add_argument("--manifest", required=True)
    run.add_argument("--invocation", required=True)
    run.add_argument("--observer", default="context-successor")
    check = commands.add_parser("compare")
    check.add_argument("outputs", nargs="+")
    arguments = parser.parse_args(argv)
    try:
        return reconstruct(arguments) if arguments.command == "reconstruct" else compare_outputs(arguments)
    except Exception as error:
        _emit({"status": "ERROR", "error": repr(error)})
        return ERROR_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
