#!/usr/bin/env python3
"""Run deterministic VERIFY regression packs selected by candidate changed paths."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("feature_regressions.json")


def changed_paths(base: str, candidate: str) -> tuple[str, ...]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{candidate}"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return tuple(line for line in out.splitlines() if line)


def matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    return fnmatch.fnmatch(path, pattern)
def selected_packs(document: dict, paths: tuple[str, ...]) -> list[dict]:
    return [
        pack for pack in document["packs"]
        if any(matches(path, pattern) for path in paths for pattern in pack["paths"])
    ]


def canonical_digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def run_pack(pack: dict) -> dict:
    command = list(pack["command"])
    done = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "id": pack["id"],
        "command": command,
        "exit_code": done.returncode,
        "stdout": done.stdout,
        "stderr": done.stderr,
        "passed": done.returncode == 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--receipt")
    args = parser.parse_args(argv)

    document = json.loads(MANIFEST.read_text())
    base_revision = subprocess.run(["git", "rev-parse", args.base], cwd=ROOT, check=True,
                                   capture_output=True, text=True).stdout.strip()
    candidate_revision = subprocess.run(["git", "rev-parse", args.candidate], cwd=ROOT, check=True,
                                        capture_output=True, text=True).stdout.strip()
    paths = tuple(args.changed_path) or changed_paths(base_revision, candidate_revision)
    packs = selected_packs(document, paths)
    results = [run_pack(pack) for pack in packs]
    receipt_body = {
        "schema_version": 1,
        "kind": "FeatureRegressionReceipt",
        "base": base_revision,
        "candidate": candidate_revision,
        "changed_paths": list(paths),
        "manifest_digest": canonical_digest(document),
        "packs": [{k: v for k, v in result.items() if k not in {"stdout", "stderr"}} for result in results],
        "passed": all(result["passed"] for result in results),
    }
    receipt = receipt_body | {"receipt_digest": canonical_digest(receipt_body)}
    if args.receipt:
        target = Path(args.receipt)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    for result in results:
        if result["stdout"]:
            print(result["stdout"], file=sys.stderr, end="")
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr, end="")
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
