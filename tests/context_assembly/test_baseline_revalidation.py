"""Baseline revalidation (WORK-PREPARATION-REFILL R2, spec 3.8; Founder decisions sections 39 and 43): "Never silently
retarget an assessed Work Item onto changed code. Revalidate it first." Commits and paths are TEST DATA."""
from __future__ import annotations

import pytest

from alienintent.context_assembly.domain.baseline_revalidation import (
    ADVANCED, BEHIND, DIVERGED, PROCEED, REPREPARE, RETARGET, BaselineDecision, reference_paths, revalidate)

BASE, MAIN = "a" * 40, "b" * 40
GUARDED = ("src/pkg/module.py", "src/pkg/folder", "tests/pkg/test_module.py")


def decide(changed=("src/other.py",), guarded=GUARDED, reasons=(), proof=True, main=MAIN,
           relation=ADVANCED, errors=()) -> BaselineDecision:
    return revalidate(BASE, main, relation, changed, guarded, reasons, proof, errors)


def test_unchanged_main_proceeds_at_the_assessed_baseline_with_no_checks():
    assert decide(main=BASE) == BaselineDecision(PROCEED, BASE, ())


@pytest.mark.parametrize("relation", [BEHIND, DIVERGED])
def test_main_that_no_longer_contains_the_baseline_goes_back_to_preparation_and_never_runs_ahead_of_main(relation):
    """Main moved backward (an ancestor of the baseline) or was rewritten: the baseline holds commits canonical main no
    longer has, so it is never executed from (Founder, 2026-10-11)."""
    decision = decide(relation=relation, changed=())
    assert (decision.kind, decision.revision) == (REPREPARE, BASE)
    assert [(name, passed) for name, passed, _ in decision.checks] == [("baseline-on-main", False)]


def test_advanced_main_that_touches_nothing_guarded_is_retargeted_with_its_checks_recorded():
    decision = decide()
    assert (decision.kind, decision.revision) == (RETARGET, MAIN)
    assert [(name, passed) for name, passed, _ in decision.checks] == [
        ("plan-authority", True), ("proof-declared", True), ("packet-readable", True),
        ("scope-proof-references-untouched", True)]


@pytest.mark.parametrize("change", [
    pytest.param({"changed": ("src/pkg/module.py",)}, id="scope-file"),
    pytest.param({"changed": ("tests/pkg/test_module.py",)}, id="proof-file"),
    pytest.param({"changed": ("src/pkg/folder/inner.py",)}, id="under-a-directory-entry"),
    pytest.param({"changed": ("src/pkg",)}, id="over-a-guarded-entry"),
    pytest.param({"reasons": ("owner-decision-required: outside obligation FIXTURE",)}, id="outside-authority"),
    pytest.param({"proof": False}, id="no-proof-set"),
    pytest.param({"changed": ("src/pkg/folder/inner.py",), "guarded": ("src/pkg/folder/",)},
                 id="directory-entry-slash"),
    pytest.param({"changed": ("docs/x.md",), "guarded": ("./docs/x.md",)}, id="dotted-entry"),
    pytest.param({"guarded": ("the launch module",)}, id="entry-not-a-path"),
    pytest.param({"guarded": ("src/*.py",)}, id="entry-a-glob"),
    pytest.param({"errors": ("mutations: each mutation needs exactly edits, name, path, tests",)},
                 id="packet-unreadable"),
])
def test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline(change):
    decision = decide(**change)
    assert (decision.kind, decision.revision) == (REPREPARE, BASE)
    assert not all(passed for _, passed, _ in decision.checks)


def test_a_sibling_path_with_a_shared_prefix_is_not_guarded():
    assert decide(changed=("src/pkg/module.pyc", "src/pkg/folder2/x.py")).kind == RETARGET


def test_a_reference_guards_its_path_and_prose_is_kept_whole_so_it_holds():
    """`<path> obligation:<label>` guards the path; the canonical plan is judged by the authority check instead; prose
    is kept whole, is not a path and holds (never truncated to its first word)."""
    plan = "docs/plan.md"
    references = (f"{plan} obligation:FIXTURE", "docs/x.diff", "src/a.py obligation:OTHER",
                  "SF-REQ-013 amendment 2026-09-22")
    assert reference_paths(references, plan) == ("docs/x.diff", "src/a.py", "SF-REQ-013 amendment 2026-09-22")
    decision = decide(changed=(), guarded=reference_paths(references, plan))
    assert decision.kind == REPREPARE and "not a path: SF-REQ-013 amendment 2026-09-22" in decision.checks[-1][2]
