#!/usr/bin/env python3
"""Sandbox feature-regression pack: every note a candidate changes has the seeded shape.

Installed into the sandbox repository by FX-E1 seeding as
`tools/verification/check_notes.py`, next to the shipped
`run_feature_regressions.py`, so the Python verifier gate has a real pack to run
there. A note must open with `# <BIU>` and carry exactly one bullet line, and a
candidate may change nothing but notes under `docs/`.
"""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def git(*arguments: str) -> str:
    return subprocess.run(["git", *arguments], capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    base = git("merge-base", "HEAD", "origin/main")
    changed = [path for path in git("diff", "--name-only", f"{base}...HEAD").splitlines() if path]
    problems = [f"{path}: outside docs/" for path in changed if not path.startswith("docs/")]
    for path in (Path(name) for name in changed if name.startswith("docs/") and name.endswith(".md")):
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        if not text.startswith(f"# {path.stem}\n"):
            problems.append(f"{path}: does not open with '# {path.stem}'")
        if sum(line.startswith("- ") for line in text.splitlines()) != 1:
            problems.append(f"{path}: does not carry exactly one bullet line")
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(changed)} changed path(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
