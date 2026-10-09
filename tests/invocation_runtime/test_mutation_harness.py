"""VERIFICATION-OUTCOME-INTEGRITY: the control plane's mutation harness and its reproduction of reject evidence.

Every run is in a fresh checkout of the exact candidate (here a copy of a tiny repository); the runner is a fake that
answers from the checkout's bytes, except in the one end-to-end test, which runs real pytest. Names are TEST DATA.
"""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from alienintent.execution_coordination.domain.custody import CandidateKind, CandidateRef
from alienintent.invocation_runtime.domain.mutation_spec import MutationSpec, parse_mutations
from alienintent.invocation_runtime.domain.verdict_admission import claims
from alienintent.invocation_runtime.application.mutation_harness import (
    KILLED, REVERTED_FAILS, SPEC_INVALID, SURVIVED, MutationHarness)
from alienintent.invocation_runtime.application.regression_gate import SuiteUnrunnable

SHA, OTHER, BASE = "c" * 40, "d" * 40, "a" * 40
INVOCATION = "launch:WORK:2"
RULE = "def admitted(ok):\n    if ok:\n        return True\n    return False\n"
TEST = ("from src.rule import admitted\n\n\ndef test_refuses():\n    assert admitted(False) is False\n\n\n"
        "def test_admits():\n    assert admitted(True) is True\n")
REFUSES, ADMITS = "tests/test_rule.py::test_refuses", "tests/test_rule.py::test_admits"
NEW = "tests/test_new.py::test_new"


def candidate(sha: str = SHA) -> CandidateRef:
    digest = "sha256:" + sha256(sha.encode()).hexdigest()
    return CandidateRef(CandidateKind.SOURCE_REVISION, digest, digest, f"git:origin#candidate/c@{sha}", "test")


def junit(*cases: tuple[str, str]) -> bytes:
    """A junit document with one test case per (identity, outcome)."""
    child = {"passed": "", "failed": "<failure message='assert 1 == 2'/>", "error": "<error message='x'/>",
             "skipped": "<skipped message='x'/>", "raised": "<failure message='NameError: name x is not defined'/>"}
    body = "".join(f'<testcase classname="{i.split("::")[0]}" name="{i.split("::")[1]}">{child[o]}</testcase>'
                   for i, o in cases)
    return f'<?xml version="1.0"?><testsuites><testsuite name="pytest">{body}</testsuite></testsuites>'.encode()


def mutation(old: str = "if ok:", new: str = "if True:", tests: tuple[str, ...] = (REFUSES,), path="src/rule.py"):
    return [{"name": "drop-check", "path": path, "edits": [{"old": old, "new": new}], "tests": list(tests)}]


def spec(*mutations: list) -> MutationSpec:
    return parse_mutations("```json alienintent-mutations\n" + json.dumps([m for ms in mutations for m in ms])
                           + "\n```\n")


def repository(root: Path) -> Path:
    source = root / "candidate"
    (source / "src").mkdir(parents=True)
    (source / "tests").mkdir()
    (source / "src" / "rule.py").write_text(RULE)
    (source / "tests" / "test_rule.py").write_text(TEST)
    return source


def harness(root: Path, run, candidate_files: dict | None = None,
            base_files: dict | None = None) -> tuple[MutationHarness, list[str]]:
    """A harness whose every checkout is a fresh copy of the candidate (or, by SHA, of the starting revision);
    `opened` names each checkout; whether a file exists at the starting revision is asked of that revision's files
    (git's answer); a `base_files` value of None removes the file there."""
    source, opened = repository(root), []
    base = root / "starting"
    shutil.copytree(source, base)
    for folder, files in ((source, candidate_files), (base, base_files)):
        for name, text in (files or {}).items():
            if text is None:
                (folder / name).unlink()
            else:
                (folder / name).write_text(text)

    def copy(origin: Path, identity: str):
        opened.append(identity)
        folder = root / "checkouts" / identity
        shutil.copytree(origin, folder)
        try:
            yield folder
        finally:
            shutil.rmtree(folder)
    return MutationHarness(run, Path.read_bytes, contextmanager(lambda given, identity: copy(source, identity)),
                           root / "results", revision_checkout=contextmanager(lambda sha, identity: copy(base, identity)),
                           exists_at=lambda sha, path: (base / path).is_file()), opened


def fake(always_fails: frozenset[str] = frozenset(), skipped: str | None = None):
    """The runner: compiles in process; `tests/test_rule.py::test_refuses` fails on an assertion when the check is
    gone; with `skipped` it is skipped instead, under the mutation only (`mutated`) or always (`always`); in a
    checkout holding a file BROKEN it fails on a ConnectionError instead (the environment, not the code), in one
    holding ASSERTS on an assertion; `tests/test_new.py::test_new` exists only where its file does, and fails on a
    ConnectionError when its file says so, else on an assertion."""
    def run(folder: Path, argv: list[str]) -> int:
        if argv[:2] == ["python3", "-c"]:
            try:
                compile((folder / argv[-1]).read_bytes(), argv[-1], "exec")
                return 0
            except SyntaxError:
                return 1
        path = Path(argv[argv.index("--junitxml") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        ids = argv[argv.index("--junitxml") + 2:]
        if (folder / "COLLECTION_ERROR").exists():  # a conftest that cannot be imported in this environment
            path.write_bytes(b'<?xml version="1.0"?><testsuites><testsuite name="pytest"><testcase classname="" '
                             b'name="tests.test_rule"><error message="collection failure"/></testcase>'
                             b'</testsuite></testsuites>')
            return 1
        def present(node: str) -> bool:
            file = folder / node.split("::")[0]
            return file.exists() and f"def {node.split('::')[1]}(" in file.read_text()
        if not all(map(present, ids)):  # as real pytest: a valid junit with no test case, and exit 4
            path.write_bytes(junit())
            return 4
        checked = "if ok:" in (folder / "src/rule.py").read_text()
        node_skips = skipped == "always" or (skipped == "mutated" and not checked)
        cases = [(f"{node.split('::')[0][:-3].replace('/', '.')}::{node.split('::')[1]}",
                  ("raised" if "ConnectionError" in (folder / "tests/test_new.py").read_text() else "failed")
                  if node == NEW else "failed" if node not in (REFUSES, ADMITS) else
                  "skipped" if node == REFUSES and node_skips else
                  "raised" if node == REFUSES and (folder / "BROKEN").exists() else
                  "failed" if node == REFUSES and (folder / "ASSERTS").exists() else
                  "failed" if node in always_fails or (node == REFUSES and not checked) else "passed") for node in ids]
        path.write_bytes(junit(*cases))
        return int(any(outcome != "passed" for _, outcome in cases))
    return run


def test_a_killing_mutation_is_applied_exactly_and_its_reverted_run_passes(tmp_path):
    checks, opened = harness(tmp_path, fake())
    results, receipt = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
    assert [(r.name, r.result) for r in results] == [("drop-check", KILLED)]
    assert opened[0] == f"mutation-0-{INVOCATION}" and opened[1].startswith(f"restored-mutation-0-{INVOCATION}")
    assert receipt.startswith("mutation-harness:sha256:")
    other, _ = harness(tmp_path / "other", fake())
    assert other.run(INVOCATION, candidate(OTHER), spec(mutation()), BASE)[1] != receipt  # the receipt binds the candidate


def test_a_surviving_mutation_and_a_failing_reverted_run_are_the_candidates(tmp_path):
    checks, _ = harness(tmp_path, fake())
    [survived], _ = checks.run(INVOCATION, candidate(), spec(mutation(tests=(ADMITS,))), BASE)
    assert survived.result == SURVIVED and ADMITS in survived.detail
    checks, _ = harness(tmp_path / "asserts", fake(), candidate_files={"ASSERTS": ""})
    [reverted], _ = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
    assert reverted.result == REVERTED_FAILS


@pytest.mark.parametrize("change", [
    {"old": "return"},                            # occurs more than once
    {"old": "if not ok:"},                        # does not occur
    {"new": "if True"},                           # the mutated file does not compile
    {"tests": ("tests/test_rule.py::test_unknown",)},
    {"path": "src/missing.py"},
])
def test_a_malformed_mutation_is_spec_invalid(tmp_path, change):
    checks, _ = harness(tmp_path, fake())
    [result], _ = checks.run(INVOCATION, candidate(), spec(mutation(**change)), BASE)
    assert result.result == SPEC_INVALID


def test_a_runner_failure_is_no_result(tmp_path):
    def unrunnable(folder, argv):
        if argv[:2] == ["python3", "-c"]:
            return 0
        raise SuiteUnrunnable("the run outran its wall clock")
    checks, _ = harness(tmp_path, unrunnable)
    with pytest.raises(SuiteUnrunnable):
        checks.run(INVOCATION, candidate(), spec(mutation()), BASE)


def finding(evidence: dict) -> dict:
    return {"finding": "a defect", "evidence": evidence}


@pytest.mark.parametrize("evidence, reproduced", [
    ({"type": "pytest", "node_ids": [REFUSES]}, False),
    ({"type": "pytest", "node_ids": ["tests/test_rule.py::test_unknown"]}, False),
    ({"type": "text", "path": "src/rule.py", "contains": "if ok:"}, True),
    ({"type": "text", "path": "src/rule.py", "absent": "if ok:"}, False),
    ({"type": "text", "path": "src/missing.py", "absent": "x"}, False),
])
def test_evidence_is_reproduced_only_when_it_holds_at_the_candidate(tmp_path, evidence, reproduced):
    checks, opened = harness(tmp_path, fake())
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding(evidence)]), BASE)
    assert result.reproduced is reproduced and opened[0].startswith(f"evidence-0-{INVOCATION}")


@pytest.mark.parametrize("code, output, reproduced", [
    (1, "invocation_runtime/application/x.py:3: unclassified cross-module domain import a.b.domain.c\n", True),
    (1, "Traceback (most recent call last):\n  File \"x.py\", line 1\nKeyError: 'domain_imports'\n", False),
    (1, "coupling register unavailable: missing\n", False),
    (0, "PASS: layers architecture fitness checks\n", False),
    (2, "usage: check_architecture.py: error: argument --check: invalid choice\n", False),
])
def test_a_fitness_finding_reproduces_only_on_the_checks_own_failure_report(tmp_path, code, output, reproduced):
    """A crash or a usage error of the fitness tool is not the candidate's failure (the starting revision passes)."""
    def run(folder, argv):
        Path(argv[-1]).parent.mkdir(parents=True, exist_ok=True)
        control = folder.name.startswith("control-")
        Path(argv[-1]).write_text("PASS: layers architecture fitness checks\n" if control else output)
        return 0 if control else code
    checks, _ = harness(tmp_path, run)
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "fitness", "check": "layers"})]), BASE)
    assert result.reproduced is reproduced


def test_end_to_end_a_real_mutation_and_real_reproducers_under_real_pytest(tmp_path):
    """One real run: the harness edits the file, real pytest kills the mutation, the restored file passes; a
    reproducer that asserts falsely reproduces and one that fails to import does not."""
    def run(folder: Path, argv: list[str]) -> int:
        if "--junitxml" in argv:
            Path(argv[argv.index("--junitxml") + 1]).parent.mkdir(parents=True, exist_ok=True)
        argv = [sys.executable, *argv[1:]] if argv[0] == "python3" else argv
        return subprocess.run(argv, cwd=folder, capture_output=True, timeout=120).returncode

    checks, _ = harness(tmp_path, run)
    [result], _ = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
    assert result.result == KILLED, result.detail
    asserting = {"type": "reproducer", "name": "test_refusal.py",
                 "source": "from src.rule import admitted\n\n\ndef test_admits_everything():\n"
                           "    assert admitted(False) is True\n"}
    importing = {"type": "reproducer", "name": "test_import.py",
                 "source": "import no_such_module\n\n\ndef test_x():\n    assert False\n"}
    first, second = checks.reproduce(INVOCATION, candidate(), claims([finding(asserting), finding(importing)]), BASE)
    assert (first.reproduced, second.reproduced) == (True, False), (first, second)
    assert not (tmp_path / "candidate" / "alienintent-evidence").exists()  # never written into the candidate


def test_a_pytest_finding_reproduces_when_a_named_test_fails_at_the_candidate(tmp_path):
    checks, _ = harness(tmp_path, fake(), candidate_files={"ASSERTS": ""})
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "pytest", "node_ids": [REFUSES, ADMITS]})]), BASE)
    assert result.reproduced and REFUSES in result.detail


@pytest.mark.parametrize("skipped", ["mutated", "always"])
def test_a_skipped_named_test_is_spec_invalid_never_the_candidates(tmp_path, skipped):
    """A skipped test is no evidence: skipped under the mutation it did not survive, skipped restored it did not
    fail; either way the evidence is unavailable."""
    checks, _ = harness(tmp_path, fake(skipped=skipped))
    [result], _ = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
    assert result.result == SPEC_INVALID


def test_each_evidence_item_has_its_own_fresh_checkout(tmp_path):
    """A reproducer that rewrites a candidate file changes nothing later evidence sees."""
    def run(folder: Path, argv: list[str]) -> int:
        (folder / "src/rule.py").write_text("changed by a reproducer\n")
        path = Path(argv[argv.index("--junitxml") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(junit(("alienintent-evidence.test_x::test_x", "failed")))
        return 1
    checks, opened = harness(tmp_path, run)
    reproducer = {"type": "reproducer", "name": "test_x.py", "source": "def test_x():\n    assert False\n"}
    text = {"type": "text", "path": "src/rule.py", "contains": "if ok:"}
    first, second = checks.reproduce(INVOCATION, candidate(), claims([finding(reproducer), finding(text)]), BASE)
    assert first.reproduced and second.reproduced
    assert len(opened) == 2 and opened[0].startswith(f"evidence-0-{INVOCATION}") \
        and opened[1].startswith(f"evidence-1-{INVOCATION}")


@pytest.mark.parametrize("outcome, reproduced", [("failed", True), ("raised", False), ("error", False)])
def test_a_reproducer_reproduces_only_with_an_assertion_failure(tmp_path, outcome, reproduced):
    def run(folder: Path, argv: list[str]) -> int:
        path = Path(argv[argv.index("--junitxml") + 1])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(junit(("alienintent-evidence.test_x::test_x", outcome)))
        return 1
    checks, _ = harness(tmp_path, run)
    reproducer = {"type": "reproducer", "name": "test_x.py", "source": "def test_x():\n    assert False\n"}
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding(reproducer)]), BASE)
    assert result.reproduced is reproduced



@pytest.mark.parametrize("base_files, result", [({"BROKEN": ""}, SPEC_INVALID), ({}, REVERTED_FAILS)])
def test_a_restored_run_that_is_not_an_assertion_counts_only_against_a_passing_starting_revision(
        tmp_path, base_files, result):
    """The restored test fails on a ConnectionError: when it also fails at the starting revision now, the
    environment decided (SPEC_INVALID); when the starting revision passes now, the candidate did."""
    checks, opened = harness(tmp_path, fake(), candidate_files={"BROKEN": ""}, base_files=base_files)
    [found], _ = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
    assert found.result == result and any(name.startswith(f"control-mutation-0-{INVOCATION}") for name in opened)
    assert ("environment" in found.detail) is (result == SPEC_INVALID)


@pytest.mark.parametrize("base_files, reproduced", [({"BROKEN": ""}, False), ({}, True)])
def test_a_pytest_finding_that_is_not_an_assertion_reproduces_only_against_a_passing_starting_revision(
        tmp_path, base_files, reproduced):
    checks, _ = harness(tmp_path, fake(), candidate_files={"BROKEN": ""}, base_files=base_files)
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "pytest", "node_ids": [REFUSES]})]),
                                BASE)
    assert result.reproduced is reproduced


@pytest.mark.parametrize("base_files, stands", [({"BROKEN": ""}, ()), ({}, ("tests.test_rule::test_refuses",))])
def test_a_gate_regression_stands_only_against_a_passing_starting_revision(tmp_path, base_files, stands):
    """The candidate errors on a ConnectionError now: with the environment failing at both revisions the regression
    does not stand; with the starting revision passing now it does."""
    checks, _ = harness(tmp_path, fake(), candidate_files={"BROKEN": ""}, base_files=base_files)
    assert checks.standing(INVOCATION, candidate(), BASE, ("tests.test_rule::test_refuses",)) == stands



@pytest.mark.parametrize("where", ["restored run", "pytest evidence", "gate regression"])
def test_an_assertion_failing_at_both_revisions_is_never_the_candidates(tmp_path, where):
    """The test fails on an assertion at the candidate and at the starting revision now: known debt or the
    environment, never the candidate."""
    checks, _ = harness(tmp_path, fake(), candidate_files={"ASSERTS": ""}, base_files={"ASSERTS": ""})
    if where == "restored run":
        [found], _ = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
        assert found.result == SPEC_INVALID and "environment" in found.detail
    elif where == "pytest evidence":
        [result] = checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "pytest", "node_ids": [REFUSES]})]),
                                    BASE)
        assert not result.reproduced
    else:
        assert checks.standing(INVOCATION, candidate(), BASE, ("tests.test_rule::test_refuses",)) == ()


@pytest.mark.parametrize("source, stands", [("def test_new():\n    raise ConnectionError\n", ()),
                                            ("def test_new():\n    assert False\n", ("tests.test_new::test_new",))])
def test_a_new_test_counts_only_when_it_fails_on_an_assertion(tmp_path, source, stands):
    """A test absent at the starting revision: an environment-style error keeps the candidate, an assertion
    failure stands."""
    checks, _ = harness(tmp_path, fake(), candidate_files={"tests/test_new.py": source})
    assert checks.standing(INVOCATION, candidate(), BASE, ("tests.test_new::test_new",)) == stands


@pytest.mark.parametrize("base_files, reproduced", [({"VIOLATES": ""}, False), ({}, True)])
def test_a_fitness_violation_reproduces_only_when_the_starting_revision_passes(tmp_path, base_files, reproduced):
    def run(folder, argv):
        Path(argv[-1]).parent.mkdir(parents=True, exist_ok=True)
        violates = (folder / "VIOLATES").exists()
        Path(argv[-1]).write_text("execution_coordination/x.py:3: a layer is crossed\n" if violates
                                  else "PASS: layers architecture fitness checks\n")
        return int(violates)
    checks, _ = harness(tmp_path, run, candidate_files={"VIOLATES": ""}, base_files=base_files)
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "fitness", "check": "layers"})]), BASE)
    assert result.reproduced is reproduced



@pytest.mark.parametrize("where", ["restored run", "pytest evidence", "gate regression"])
def test_a_collection_error_at_the_starting_revision_is_no_result_never_an_absent_test(tmp_path, where):
    """The test asserts at the candidate, and at the starting revision its module cannot be collected: absence there
    is not proven, so the run gives no result and the candidate is kept."""
    checks, _ = harness(tmp_path, fake(), candidate_files={"ASSERTS": ""}, base_files={"COLLECTION_ERROR": ""})
    with pytest.raises(SuiteUnrunnable):
        if where == "restored run":
            checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
        elif where == "pytest evidence":
            checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "pytest", "node_ids": [REFUSES]})]),
                             BASE)
        else:
            checks.standing(INVOCATION, candidate(), BASE, ("tests.test_rule::test_refuses",))


def test_a_gate_regression_whose_test_is_missing_at_the_starting_revision_is_no_result(tmp_path):
    """The gate proved the test passed at the baseline; not finding it there now is the machinery's failure."""
    checks, _ = harness(tmp_path, fake(), candidate_files={"ASSERTS": ""}, base_files={"tests/test_rule.py": None})
    with pytest.raises(SuiteUnrunnable):
        checks.standing(INVOCATION, candidate(), BASE, ("tests.test_rule::test_refuses",),
                        proven=frozenset({"tests.test_rule::test_refuses"}))



def test_a_test_absent_at_the_start_does_not_hide_one_that_exists(tmp_path):
    """Two named tests at the starting revision, one absent there: the existing one, asserting at both revisions,
    does not count against the candidate; the absent one is new and asserts at the candidate, so it does."""
    extra = "tests/test_rule.py::test_extra"
    checks, _ = harness(tmp_path, fake(), candidate_files={"ASSERTS": "", "tests/test_rule.py": TEST + (
        "\n\ndef test_extra():\n    assert False\n")}, base_files={"ASSERTS": ""})
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding({"type": "pytest", "node_ids": [REFUSES, extra]})]),
                                BASE)
    assert result.reproduced and extra in result.detail and REFUSES not in result.detail


def test_state_the_mutated_run_leaves_behind_never_reaches_the_restored_run(tmp_path):
    """The mutated code writes a file that makes the test fail on an assertion; the restored run is in its own fresh
    checkout of the candidate, so the mutation is simply killed, never REVERTED_FAILS."""
    inner = fake()

    def run(folder: Path, argv: list[str]) -> int:
        if "--junitxml" in argv and "if ok:" not in (folder / "src/rule.py").read_text():
            (folder / "ASSERTS").write_text("")  # state the mutated code left behind
        return inner(folder, argv)
    checks, _ = harness(tmp_path, run)
    [found], _ = checks.run(INVOCATION, candidate(), spec(mutation()), BASE)
    assert found.result == KILLED, found.detail


def test_an_absent_id_does_not_hide_an_existing_failing_test_at_the_candidate(tmp_path):
    """Real pytest runs nothing when one named test is not found: each named test runs on its own."""
    checks, _ = harness(tmp_path, fake(), candidate_files={"ASSERTS": ""})
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding(
        {"type": "pytest", "node_ids": [REFUSES, "tests/test_rule.py::test_gone"]})]), BASE)
    assert result.reproduced and REFUSES in result.detail



def test_a_test_whose_left_over_file_breaks_another_never_stands(tmp_path):
    """test_refuses leaves a file behind; test_admits fails on an assertion when it finds it. Alone each passes, so
    no finding stands: every judged test runs alone in its own fresh checkout."""
    inner = fake()

    def run(folder: Path, argv: list[str]) -> int:
        if "--junitxml" in argv and (folder / "state.flag").exists():
            (folder / "ASSERTS").write_text("")  # stand-in: test_admits asserts the flag is absent
        if "--junitxml" in argv and REFUSES in argv:
            (folder / "state.flag").write_text("")
        return inner(folder, argv)
    checks, _ = harness(tmp_path, run)
    assert checks.standing(INVOCATION, candidate(), BASE, ("tests.test_rule::test_refuses", "tests.test_rule::test_admits"),
                           proven=frozenset({"tests.test_rule::test_refuses", "tests.test_rule::test_admits"})) == ()
    [result] = checks.reproduce(INVOCATION, candidate(), claims([finding(
        {"type": "pytest", "node_ids": [REFUSES, ADMITS]})]), BASE)
    assert not result.reproduced


def test_every_judged_test_run_goes_through_observe():
    """Wiring: the named-tests command is used only by `observe` and by the mutated run; nothing else runs a test
    the control plane judges."""
    import ast
    import inspect
    from alienintent.invocation_runtime.application import mutation_harness

    tree = ast.parse(inspect.getsource(mutation_harness))
    users = {function.name for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
             for name in ast.walk(function) if isinstance(name, ast.Name) and name.id == "TESTS"}
    assert users == {"observe", "_mutation"}
    runners = {function.name for function in ast.walk(tree) if isinstance(function, ast.FunctionDef)
               for call in ast.walk(function) if isinstance(call, ast.Call)
               and isinstance(call.func, ast.Attribute) and call.func.attr == "_run"}
    assert runners == {"observe", "_mutation", "_fitness"}


def test_a_test_skipped_at_the_candidate_is_never_against_it(tmp_path):
    """Skipped at the candidate while passing at the starting revision: the environment decided."""
    inner = fake()

    def run(folder: Path, argv: list[str]) -> int:
        if "--junitxml" in argv and (folder / "SKIP").exists():
            path = Path(argv[argv.index("--junitxml") + 1])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(junit(("tests.test_rule::test_refuses", "skipped")))
            return 0
        return inner(folder, argv)
    checks, _ = harness(tmp_path, run, candidate_files={"SKIP": ""})
    assert checks.observe(BASE, REFUSES, "probe") == "passed"
    assert checks.standing(INVOCATION, candidate(), BASE, ("tests.test_rule::test_refuses",)) == ()
