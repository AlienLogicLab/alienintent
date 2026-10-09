"""Actual-diff containment of a plan-derived candidate (Founder decision 6, 2026-10-08). Pure.

A plan-derived candidate may advance only when every path it actually changed is under its assessed
`authorized_scope` and none touches a protected path of the approved plan authority. `changes` are the
`(mode, path)` pairs of `git diff --raw --no-renames <start> <candidate>` as the control plane reads them (the new
mode of an added or modified path, the old mode of a deleted one); paths are compared with the same normalization as
`plan_authority`: exact case against the scope, case-folded against protected paths. One `scope-violation:` reason
per violation; an empty tuple means contained.
"""
from __future__ import annotations

from collections.abc import Iterable

from alienintent.execution_coordination.domain.plan_authority import normalized, under

SCOPE_VIOLATION = "scope-violation:"
# The refusal of an automatic-on candidate when no approved plan authority names its protected paths.
NO_PLAN_AUTHORITY = SCOPE_VIOLATION + "no-plan-authority"
# The refusal of an automatic-on candidate when the control plane holds no exact starting revision to diff from.
NO_TRUSTED_START = SCOPE_VIOLATION + "no-trusted-start"
# Modes a candidate may never introduce, keep or remove: a symbolic link and a submodule (gitlink).
FORBIDDEN_MODES = {"120000": "a symbolic link", "160000": "a submodule"}
# Interpreter start-up hooks the suite or a tool would execute wherever they sit, and pytest's per-folder hook file,
# which the regression gate's suite run would execute.
STARTUP_NAME, STARTUP_SUFFIX, CONFTEST = "sitecustomize.py", ".pth", "conftest.py"


def contained(changes: Iterable[tuple[str, str]], authorized_scope: Iterable[str],
              protected_paths: Iterable[str]) -> tuple[str, ...]:
    """One `scope-violation:` reason per violation of every changed path, in change order."""
    allowed = [path for path in (normalized(entry) for entry in authorized_scope) if path is not None]
    protected = [path for path in (normalized(entry, fold=True) for entry in protected_paths) if path is not None]
    reasons: list[str] = []
    for mode, path in changes:
        compared = normalized(path)
        if compared is None or not any(under(compared, entry) for entry in allowed):
            reasons.append(f"{SCOPE_VIOLATION} {path} is outside the authorized scope")
        if compared is not None and any(under(compared.casefold(), entry) for entry in protected):
            reasons.append(f"{SCOPE_VIOLATION} {path} is a protected path")
        if mode in FORBIDDEN_MODES:
            reasons.append(f"{SCOPE_VIOLATION} {path} is {FORBIDDEN_MODES[mode]} (mode {mode})")
        name = path.rpartition("/")[2].casefold()
        if name == STARTUP_NAME or name.endswith(STARTUP_SUFFIX):
            reasons.append(f"{SCOPE_VIOLATION} {path} is an interpreter start-up file")
        if name == CONFTEST:
            reasons.append(f"{SCOPE_VIOLATION} {path} is a pytest conftest file")
    return tuple(reasons)
