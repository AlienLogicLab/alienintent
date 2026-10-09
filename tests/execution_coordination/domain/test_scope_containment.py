"""Actual-diff containment (PLAN-AUTHORITY-INHERITANCE revision 3, change 3): the pure rule.

Every changed path of a plan-derived candidate must be under its assessed scope and outside the protected paths;
symbolic links, submodules and interpreter start-up files are refused wherever they sit. Paths are TEST DATA.
"""
from __future__ import annotations

import pytest

from alienintent.execution_coordination.domain.scope_containment import contained

SCOPE = ("src/alienintent/composition/", "tests/composition/test_x.py")
PROTECTED = ("docs/decisions/", "src/alienintent/composition/landing_authority.py")


def test_changes_inside_the_scope_are_contained():
    assert contained((("100644", "src/alienintent/composition/a.py"), ("100755", "tests/composition/test_x.py")),
                     SCOPE, PROTECTED) == ()


@pytest.mark.parametrize(("change", "words"), [
    (("100644", "src/alienintent/composition_extra.py"), "outside the authorized scope"),
    (("100644", "docs/decisions/plan.md"), "outside the authorized scope"),
    (("100644", "src/alienintent/composition/landing_authority.py"), "is a protected path"),
    (("120000", "src/alienintent/composition/link.py"), "a symbolic link (mode 120000)"),
    (("160000", "src/alienintent/composition/vendor"), "a submodule (mode 160000)"),
    (("100644", "src/alienintent/composition/sitecustomize.py"), "interpreter start-up file"),
    (("100644", "src/alienintent/composition/hook.pth"), "interpreter start-up file"),
    (("100644", "SRC/alienintent/composition/b.py"), "outside the authorized scope"),
    (("100644", "src/alienintent/composition/Landing_Authority.py"), "is a protected path"),
    (("100644", "src/alienintent/composition/conftest.py"), "a pytest conftest file"),
], ids=["outside", "outside-and-protected-folder", "protected", "symlink", "submodule", "sitecustomize", "pth",
        "scope-is-exact-case", "protected-ignores-case", "conftest"])
def test_each_violation_is_named(change, words):
    reasons = contained((change,), SCOPE, PROTECTED)
    assert reasons and all(reason.startswith("scope-violation:") for reason in reasons)
    assert any(words in reason and change[1] in reason for reason in reasons)


def test_nothing_is_contained_without_a_scope():
    assert contained((("100644", "src/alienintent/composition/a.py"),), (), PROTECTED) != ()
