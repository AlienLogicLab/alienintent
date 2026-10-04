"""AUTOMATED-CLOSURE check 5 and check 6 (the Authority's half): the Landing Authority lands only the ordered landing.

A local bare remote, a landing clone with the exact merge and record commits, stand-ins for the coordinator reader,
the journal reader and the landing credentials. Every refusal leaves the remote unchanged. Texts are TEST DATA.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from alienintent.composition.landing_authority import LANDING_PERMISSIONS, LandingAuthority, LandingOrder
from alienintent.composition.work_registry import DISPLAY_PERMISSIONS

RECORD = "docs/evidence/unit-landing-0000000.md"
ID = ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *ID, *args], cwd=cwd, check=True, capture_output=True).stdout.decode().strip()


def commit(cwd: Path, path: str, text: str) -> str:
    (cwd / path).parent.mkdir(parents=True, exist_ok=True)
    (cwd / path).write_text(text)
    git(cwd, "add", path)
    git(cwd, "commit", "-qm", path)
    return git(cwd, "rev-parse", "HEAD")


class Fx:
    def __init__(self, root: Path) -> None:
        self.remote, self.clone = root / "remote.git", root / "landing"
        root.mkdir()
        git(root, "init", "-q", "--bare", "-b", "main", str(self.remote))
        git(root, "init", "-q", "-b", "main", str(self.clone))
        self.base = commit(self.clone, "README.md", "base\n")
        git(self.clone, "push", "-q", str(self.remote), "main")
        git(self.clone, "checkout", "-q", "-b", "candidate")
        self.candidate = commit(self.clone, "src/unit.py", "candidate\n")
        git(self.clone, "checkout", "-q", "--detach", self.base)
        git(self.clone, "merge", "-q", "--no-ff", "-m", "merge", self.candidate)
        self.merge = git(self.clone, "rev-parse", "HEAD")
        self.record = commit(self.clone, RECORD, "record\n")
        self.order = LandingOrder("item", self.candidate, "launch:item:3", self.base, self.merge, self.record, RECORD,
                                  self.clone, ("candidate-published", "merged-to-main", "landing-record"), 1)
        self.journaled: LandingOrder | None = None
        self.custodied: str | None = self.candidate
        self.permissions = dict(LANDING_PERMISSIONS)
        self.mints = 0

    def event(self, order: LandingOrder) -> dict:
        return {"event": "closure-ordered", "correlation_id": order.correlation, "work_identity": order.identity,
                "candidate": order.candidate, "order": {"base": order.base, "merge": order.merge,
                                                        "record": order.record, "record_path": order.record_path,
                                                        "attempt": order.attempt, "actions": list(order.actions)}}

    def land(self, order: LandingOrder) -> str:
        fx = self

        class Credentials:
            def token(self):
                fx.mints += 1
                return SimpleNamespace(value="ghs-marker-landing", permissions=dict(fx.permissions),
                                       repository_selection="selected")

        authority = LandingAuthority(Credentials(), "owner/repo", "main",
                                     lambda identity: fx.custodied if identity == "item" else None,
                                     lambda correlation: fx.event(fx.journaled or order), push_url=str(self.remote))
        return authority.land(order)

    def head(self) -> str:
        return git(self.remote, "rev-parse", "main")


@pytest.fixture
def fx(tmp_path) -> Fx:
    return Fx(tmp_path / "fx")


def test_a_valid_order_fast_forwards_the_default_branch_to_exactly_the_record(fx):
    assert fx.land(fx.order) == "pushed" and fx.head() == fx.record and fx.mints == 1


def _other_tree_merge(fx: Fx) -> LandingOrder:
    merge = git(fx.clone, "commit-tree", f"{fx.base}^{{tree}}", "-p", fx.base, "-p", fx.candidate, "-m", "m")
    record = git(fx.clone, "commit-tree", f"{fx.record}^{{tree}}", "-p", merge, "-m", "r")
    return replace(fx.order, merge=merge, record=record)


def _two_files(fx: Fx) -> LandingOrder:
    git(fx.clone, "checkout", "-q", "--detach", fx.merge)
    (fx.clone / RECORD).parent.mkdir(parents=True, exist_ok=True)
    (fx.clone / RECORD).write_text("record\n")
    git(fx.clone, "add", RECORD)
    return replace(fx.order, record=commit(fx.clone, "src/other.py", "more\n"))  # one commit, two files


@pytest.mark.parametrize(("case", "reason"), [
    ("not-accept", "not-accepted"), ("other-candidate", "not-accepted"), ("no-merge-action", "actions"),
    ("no-record-action", "actions"), ("merge-parents", "merge-parents"), ("merge-tree", "merge-tree"),
    ("record-parent", "record-parent"), ("record-changes", "record-changes"), ("head-moved", "base-moved"),
    ("not-journaled", "order-unjournaled"), ("display-token", "credential-scope")])
def test_every_other_order_is_refused_and_the_remote_is_unchanged(fx, case, reason):
    order = fx.order
    if case == "not-accept":
        fx.custodied = None
    if case == "other-candidate":
        fx.custodied = fx.base
    if case in ("no-merge-action", "no-record-action"):
        dropped = "merged-to-main" if case == "no-merge-action" else "landing-record"
        order = replace(order, actions=tuple(a for a in order.actions if a != dropped))
    if case == "merge-parents":
        order = replace(order, merge=fx.candidate)
    if case == "merge-tree":
        order = _other_tree_merge(fx)
    if case == "record-parent":
        order = replace(order, record=git(fx.clone, "commit-tree", f"{fx.record}^{{tree}}", "-p", fx.base, "-m", "r"))
    if case == "record-changes":
        order = _two_files(fx)
    if case == "head-moved":
        git(fx.clone, "checkout", "-q", "--detach", fx.base)
        moved = commit(fx.clone, "docs/other.md", "x\n")
        git(fx.clone, "push", "-q", str(fx.remote), f"{moved}:refs/heads/main")
    if case == "not-journaled":
        fx.journaled = replace(order, attempt=2)
    if case == "display-token":
        fx.permissions = dict(DISPLAY_PERMISSIONS)
    before = fx.head()
    assert fx.land(order) == f"refused:{reason}"
    assert fx.head() == before and fx.head() != order.record
    assert fx.mints == (1 if case == "display-token" else 0)  # a token is minted only for a fully checked order
