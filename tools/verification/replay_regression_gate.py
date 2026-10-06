#!/usr/bin/env python3
"""Replay the REGRESSION-GATE comparison for two revisions of this repository (evidence tooling; no test calls it).

Each revision is checked out into its own temporary folder and the gate's `SUITE` runs there as the current user;
the findings of `compare` print as a JSON list, and both junit files are written to `--out` (default: the current
folder) as `<revision>.xml`.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from alienintent.invocation_runtime.application.regression_gate import (  # noqa: E402
    SUITE_WALL_CLOCK, SuiteUnrunnable, compare, results, suite)


def checkout(revision: str, folder: Path) -> None:
    subprocess.run(["git", "clone", "-q", "--no-checkout", str(ROOT), str(folder)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(folder), "checkout", "-q", "--detach", revision], check=True, capture_output=True)


def run(revision: str, temporary: Path, out: Path) -> dict[str, str]:
    folder, junit = temporary / revision, out / f"{revision}.xml"
    checkout(revision, folder)
    environment = os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}
    try:
        done = subprocess.run(suite(junit), cwd=folder, env=environment, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=SUITE_WALL_CLOCK, check=False)
    except subprocess.TimeoutExpired as error:
        raise SuiteUnrunnable(f"{revision}: the suite outran its wall clock") from error
    try:
        xml = junit.read_bytes()
    except OSError as error:
        raise SuiteUnrunnable(f"{revision}: no junit file: {type(error).__name__}") from error
    return results(xml, done.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("base")
    parser.add_argument("candidate")
    parser.add_argument("--out", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    out = arguments.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="replay-regression-gate-") as temporary:
        try:
            baseline = run(arguments.base, Path(temporary), out)
            candidate = run(arguments.candidate, Path(temporary), out)
        except (SuiteUnrunnable, subprocess.CalledProcessError) as error:
            print(f"unrunnable: {error}", file=sys.stderr)
            return 2
    print(json.dumps(list(compare(baseline, candidate)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
