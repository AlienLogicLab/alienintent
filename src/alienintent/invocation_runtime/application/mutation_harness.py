"""VERIFICATION-OUTCOME-INTEGRITY: the packet's mutations and a reject's evidence, run by the control plane.

Modelled on REGRESSION-GATE: every run is in a fresh checkout of the exact candidate SHA (never the VERIFIER's
clone), the runner and the junit read are injected, and the decision is taken from the bytes read as each run ends.

A mutation is applied exactly as the packet states it: every `old` must occur exactly once, all of its edits are
applied together, the mutated file must compile, and every named test must be present; otherwise the spec is invalid
(SPEC_INVALID). With the edits every named test must fail or error (else SURVIVED); without them, in its own fresh
checkout of the candidate, every one must pass (else REVERTED_FAILS, but only under the same-environment control
`against_candidate`; otherwise the environment decided and the spec's evidence is unavailable, SPEC_INVALID). A runner
that gives no result raises `SuiteUnrunnable`. The receipt binds the candidate SHA, the spec digest and every result.

Every judgment the control plane makes about one test goes through `MutationHarness.observe`: exactly that one node
id, run alone in its own fresh checkout of one exact revision, its junit read strictly, the checkout then torn down;
nothing one run leaves behind reaches another. The one exception is the mutated run, which runs the mutation's named
tests together in the mutated checkout (a collection failure there kills the mutation).

A reject's typed evidence (`verdict_admission`) is reproduced the same way, each item in its own fresh checkout of
the candidate; a reproducer is written into the untracked folder `EVIDENCE_FOLDER` of its checkout, never into the
candidate, and reproduces only when one of its tests fails on an assertion. A skipped test is never evidence.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from hashlib import sha256
from itertools import count
import json
from pathlib import Path
import re
from xml.etree import ElementTree

from alienintent.execution_coordination.domain.custody import CandidateRef
from alienintent.invocation_runtime.domain.mutation_spec import EVIDENCE_FOLDER, Mutation, MutationSpec
from alienintent.invocation_runtime.domain.verdict_admission import (
    Claim, Evidence, FitnessEvidence, PytestEvidence, ReproducerEvidence, Reproduction)
from alienintent.invocation_runtime.application.regression_gate import SuiteUnrunnable, results

Revision = CandidateRef | str  # the exact candidate, or a revision by full SHA (the starting revision)

# The named-tests command, run in a checkout's root; the junit file and the node ids follow it.
TESTS = ("python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--continue-on-collection-errors", "--junitxml")
# Compiles one file without writing bytecode; the path follows it.
COMPILE = ("python3", "-c", "import sys; compile(open(sys.argv[1], 'rb').read(), sys.argv[1], 'exec')")
# The fitness check, its output (both streams) written to the file named last; the check's name precedes it.
FITNESS = ("sh", "-c", 'python3 tools/fitness/check_architecture.py --root src/alienintent --check "$1" > "$2" 2>&1',
           "sh")
KILLED, SURVIVED, REVERTED_FAILS, SPEC_INVALID = "KILLED", "SURVIVED", "REVERTED_FAILS", "SPEC_INVALID"
# pytest's exit codes for "no such test" and "no tests collected": the named tests are not present.
_NOT_COLLECTED = (4, 5)
_FULL_SHA = re.compile(r"[0-9a-f]{40}")
# pytest's junit `<failure>` message for a failed assert: the rewritten `assert ...` or an explicit AssertionError.
_ASSERTION = re.compile(r"(?:AssertionError\b|assert\b)")
# One line of the fitness check's own failure report (`<path>:<line>: <message>`), and a Python crash.
_VIOLATION = re.compile(r"^\S+:\d+: \S", re.M)
_TRACEBACK = "Traceback (most recent call last)"
# A named test's outcome: `asserted` is a `<failure>` for an assertion, `failed` one raised by another exception.
_RANK = {"passed": 0, "skipped": 1, "missing": 2, "failed": 3, "error": 4, "asserted": 5}


@dataclass(frozen=True)
class MutationResult:
    name: str
    result: str
    detail: str


def receipt(candidate_sha: str, spec_digest: str, found: Sequence[MutationResult]) -> str:
    """`mutation-harness:sha256:` over the canonical JSON of the candidate, the spec digest and every result."""
    document = {"candidate_sha": candidate_sha, "spec_digest": spec_digest,
                "results": [{"name": r.name, "result": r.result, "detail": r.detail} for r in found]}
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return "mutation-harness:sha256:" + sha256(encoded).hexdigest()


def against_candidate(at_candidate: str, at_start: str | None) -> bool:
    """The same-environment control, the one rule for every test result the control plane holds against a candidate.
    A test that exists at the starting revision counts only when it does not pass at the candidate now and passes at
    the starting revision now (failing at both, even on an assertion, is the environment or known debt). A test
    absent at the starting revision (`missing` or None: new in the candidate) counts only when it fails on an
    assertion at the candidate now. A test skipped at the candidate never counts: the environment decided."""
    if at_candidate == "skipped":
        return False
    if at_start is None or at_start == "missing":
        return at_candidate == "asserted"
    return at_candidate != "passed" and at_start == "passed"


def cases(xml: bytes, exit_code: int) -> dict[str, str]:
    """Each junit test case's identity and its worst outcome, an assertion failure told apart (`asserted`); the exit
    code and the document are checked as REGRESSION-GATE checks them."""
    results(xml, exit_code)  # SuiteUnrunnable for no result
    found: dict[str, str] = {}
    for case in ElementTree.fromstring(xml).iter("testcase"):
        failures = case.findall("failure")
        outcome = "error" if case.find("error") is not None else "asserted" if any(
            failure.get("type", "AssertionError") == "AssertionError" and _ASSERTION.match(failure.get("message", ""))
            for failure in failures) else "failed" if failures else "skipped" if case.find("skipped") is not None \
            else "passed"
        identity = f"{case.get('classname', '')}::{case.get('name', '')}"
        if _RANK[outcome] >= _RANK[found.get(identity, "passed")]:
            found[identity] = outcome
    return found


def _outcome(node_id: str, found: Mapping[str, str]) -> str:
    """A node id's worst junit outcome (`missing` when no test case matches it). The junit identity is
    `<path as dotted module>[.<class>]::<name>`; a parametrized test matches each of its cases."""
    file, _, rest = node_id.partition("::")
    module, parts = file[:-3].replace("/", "."), rest.split("::") if rest else []
    matched = []
    for identity, outcome in found.items():
        cls, _, name = identity.rpartition("::")
        if not parts:
            hit = cls == module or cls.startswith(module + ".")
        else:
            hit = cls == ".".join([module, *parts[:-1]]) and (name == parts[-1] or name.startswith(parts[-1] + "["))
        if hit:
            matched.append(outcome)
    return max(matched, key=_RANK.__getitem__) if matched else "missing"


def _read_file(path: Path) -> bytes:
    return path.read_bytes()


def _write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


class MutationHarness:
    """The packet's mutations and a reject's evidence, each judged on fresh checkouts of exact revisions.

    `run(folder, argv)` runs one command in `folder` and answers its exit code (`SuiteUnrunnable` on timeout);
    `read(path)` reads a file a run wrote in `results` (with a worker user through the hand-over's checked
    descriptor); `checkout(candidate, identity)` is a fresh checkout of exactly that candidate under `identity`, and
    `revision_checkout(sha, identity)` one of a revision by SHA (the starting revision, for the same-environment
    control), each cleaned up when the block ends; `exists_at(sha, path)` answers, from the control plane's own git,
    whether a file exists at a revision (OSError when git cannot answer); `results` is the folder whose
    `<identity>/` each run writes to; `read_file` and `write_file` read and write one file of a checkout
    (`read_file` raises FileNotFoundError only for a file proven absent).
    """

    def __init__(self, run: Callable[[Path, Sequence[str]], int], read: Callable[[Path], bytes],
                 checkout: Callable[[CandidateRef, str], AbstractContextManager[Path]], results: Path, *,
                 revision_checkout: Callable[[str, str], AbstractContextManager[Path]],
                 exists_at: Callable[[str, str], bool],
                 read_file: Callable[[Path], bytes] = _read_file,
                 write_file: Callable[[Path, bytes], None] = _write_file) -> None:
        self._run, self._read, self._checkout, self._results = run, read, checkout, Path(results)
        self._revision_checkout, self._read_file, self._write_file = revision_checkout, read_file, write_file
        self._exists_at, self._observations = exists_at, count()

    def observe(self, revision: Revision, node: str, scope: str, *, write: tuple[str, bytes] | None = None) -> str:
        """The one test `node` at `revision` now, alone, in its own fresh checkout under `<scope>-<n>` (with `write`,
        one file written into that checkout first): passed, asserted, failed, error, skipped or missing.

        `missing` only when proven: the file is absent at the revision (asked of git for a SHA; of the checkout's own
        files for the candidate), or the run completed cleanly (exit 0, 1, 4 or 5, its junit written, no collection
        error) and does not name the node. Any other non-result is `SuiteUnrunnable`."""
        file, identity = node.split("::")[0], f"{scope}-{next(self._observations)}"
        if isinstance(revision, str) and not self._exists_at(revision, file):
            return "missing"
        opened = self._revision_checkout(revision, identity) if isinstance(revision, str) \
            else self._checkout(revision, identity)
        junit = self._results / identity / "junit.xml"
        with opened as folder:
            if write is not None:
                self._write_file(folder / write[0], write[1])
            if not _inside(folder, folder / file):
                return "missing"
            try:
                self._read_file(folder / file)
            except FileNotFoundError:
                return "missing"
            exit_code = self._run(folder, [*TESTS, str(junit), node])
            if exit_code not in (0, 1, *_NOT_COLLECTED):
                raise SuiteUnrunnable(f"the run of {node} exited {exit_code}")
            xml = self._junit(junit)
        ran = cases(xml, 1 if exit_code in _NOT_COLLECTED else exit_code)
        collection = [case for case in ElementTree.fromstring(xml).iter("testcase")
                      if case.get("classname", "") == "" or any("collection failure" in error.get("message", "")
                                                                for error in case.findall("error"))]
        if collection and write is not None and all(case.get("name", "") == write[0][:-3].replace("/", ".")
                                                    for case in collection):
            return "error"  # the written file itself (a VERIFIER's reproducer) cannot be collected: no evidence
        if collection:
            raise SuiteUnrunnable(f"a collection error in the run of {node}")
        return _outcome(node, ran)

    def _junit(self, junit: Path) -> bytes:
        """A junit file's bytes, read strictly: unreadable or unparsable is `SuiteUnrunnable`."""
        try:
            xml = self._read(junit)
            ElementTree.fromstring(xml)
        except (OSError, ElementTree.ParseError) as error:
            raise SuiteUnrunnable(f"the junit cannot be read: {type(error).__name__}") from error
        return xml

    def run(self, invocation_id: str, candidate: CandidateRef, spec: MutationSpec,
            base: str) -> tuple[tuple[MutationResult, ...], str]:
        """Each mutation's result, in spec order, and the receipt; `base` is the starting revision."""
        sha = _revision(candidate)
        found = tuple(self._mutation(f"mutation-{index}-{invocation_id}", candidate, mutation, base)
                      for index, mutation in enumerate(spec.mutations))
        return found, receipt(sha, spec.digest, found)

    def reproduce(self, invocation_id: str, candidate: CandidateRef, read: Sequence[Claim],
                  base: str) -> tuple[Reproduction | None, ...]:
        """Each claim's reproduction at the candidate (None for a claim without evidence), in order."""
        _revision(candidate)
        return tuple(None if claim.evidence is None else self._reproduce(f"evidence-{index}-{invocation_id}", candidate,
                                                                          claim.evidence, base)
                     for index, claim in enumerate(read))

    def standing(self, invocation_id: str, candidate: CandidateRef, base: str, identities: Sequence[str], *,
                 proven: frozenset[str] = frozenset()) -> tuple[str, ...]:
        """The REGRESSION-GATE findings' tests (junit identities) that stand under the same-environment control: each
        observed now at the starting revision and at the candidate. A test is new at the starting revision only when
        its absence is proven; one in `proven` (a regression: the gate proved it passed at the baseline) not found
        there now is no result, `SuiteUnrunnable`. One found at neither revision does not stand."""
        _revision(candidate)
        standing = []
        for index, name in enumerate(identities):
            scope = f"control-gate-{index}-{invocation_id}"
            node = self._node(name, lambda path: self._exists_at(base, path))
            start = None if node is None else self.observe(base, node, scope)
            if name in proven and start in (None, "missing"):
                raise SuiteUnrunnable(f"{name} passed at the baseline and is not found at the starting revision now")
            if node is None:
                with self._checkout(candidate, f"gate-probe-{index}-{invocation_id}") as folder:
                    node = self._node(name, lambda path: _present(self._read_file, folder, path))
            if node is not None and against_candidate(
                    self.observe(candidate, node, f"gate-{index}-{invocation_id}"), start):
                standing.append(name)
        return tuple(standing)

    @staticmethod
    def _node(identity: str, exists: Callable[[str], bool]) -> str | None:
        """The pytest node id of a junit identity: its longest dotted prefix that is a `.py` file, as `exists` says."""
        classname, _, name = identity.rpartition("::")
        parts = classname.split(".")
        for end in range(len(parts), 0, -1):
            path = "/".join(parts[:end]) + ".py"
            if all(parts[:end]) and exists(path):
                return "::".join([path, *parts[end:], name])
        return None

    def _held(self, candidate: CandidateRef, base: str, outcomes: Mapping[str, str], scope: str) -> list[str]:
        """The nodes whose candidate outcome counts against it, each observed again at the starting revision."""
        return [node for node, outcome in outcomes.items() if outcome != "passed"
                and against_candidate(outcome, self.observe(base, node, f"control-{scope}"))]

    def _reproduce(self, identity: str, candidate: CandidateRef, evidence: Evidence, base: str) -> Reproduction:
        """One evidence item at the candidate; tests through `observe`, a fitness check and a text predicate in their
        own fresh checkout, so nothing one item writes is seen by another."""
        if isinstance(evidence, PytestEvidence):
            outcomes = {node: self.observe(candidate, node, identity) for node in evidence.node_ids}
            if all(outcome == "missing" for outcome in outcomes.values()):
                return Reproduction(False, f"named tests not present: {', '.join(evidence.node_ids)}")
            failing = {node: outcome for node, outcome in outcomes.items()
                       if outcome in ("asserted", "failed", "error")}
            held = self._held(candidate, base, failing, identity)
            if held:
                return Reproduction(True, f"fails at the candidate, against the starting revision now: {', '.join(held)}")
            return Reproduction(False, "no named test fails against the starting revision now: "
                                + ", ".join(f"{node}:{outcome}" for node, outcome in outcomes.items()))
        if isinstance(evidence, ReproducerEvidence):
            relative = f"{EVIDENCE_FOLDER}/{evidence.name}"
            outcome = self.observe(candidate, relative, identity, write=(relative, evidence.source.encode()))
            if outcome == "missing":
                return Reproduction(False, f"the reproducer {evidence.digest} collected no test")
            if outcome != "asserted":
                return Reproduction(False, f"the reproducer {evidence.digest} has no test failing on an assertion "
                                           f"({outcome})")
            return Reproduction(True, f"the reproducer {evidence.digest} fails on an assertion")
        if isinstance(evidence, FitnessEvidence):
            with self._checkout(candidate, identity) as folder:
                exit_code, reported = self._fitness(folder, self._results / identity, evidence)
            if not reported:
                return Reproduction(False, f"the fitness check {evidence.check} exited {exit_code} without its own "
                                           "failure report")
            with self._revision_checkout(base, f"control-{identity}") as folder:
                started, _ = self._fitness(folder, self._results / f"control-{identity}", evidence)
            return Reproduction(started == 0, "the fitness check reports a violation at the candidate "
                                + ("and passes at the starting revision now" if started == 0
                                   else f"and exits {started} at the starting revision now (environment or debt)"))
        with self._checkout(candidate, identity) as folder:
            target = folder / evidence.path
            try:
                data = self._read_file(target) if _inside(folder, target) else None
            except FileNotFoundError:
                data = None
        if data is None:
            return Reproduction(False, f"{evidence.path} is not present at the candidate")
        holds = (evidence.text.encode() in data) is evidence.present
        verb = "contains" if evidence.present else "lacks"
        return Reproduction(holds, f"{evidence.path} {verb} the text" if holds else f"{evidence.path}: predicate false")

    def _mutation(self, identity: str, candidate: CandidateRef, mutation: Mutation, base: str) -> MutationResult:
        def result(kind: str, detail: str) -> MutationResult:
            return MutationResult(mutation.name, kind, detail)

        with self._checkout(candidate, identity) as folder:
            target = folder / mutation.path
            if not _inside(folder, target):
                return result(SPEC_INVALID, f"{mutation.path} is not inside the checkout")
            try:
                mutated = self._read_file(target)
            except FileNotFoundError:
                return result(SPEC_INVALID, f"{mutation.path} is not present at the candidate")
            for edit in mutation.edits:
                occurrences = mutated.count(edit.old.encode())
                if occurrences != 1:
                    return result(SPEC_INVALID, f"{edit.old!r} occurs {occurrences} times in {mutation.path}")
                mutated = mutated.replace(edit.old.encode(), edit.new.encode(), 1)
            self._write_file(target, mutated)
            if mutation.path.endswith(".py") and self._run(folder, [*COMPILE, mutation.path]) != 0:
                return result(SPEC_INVALID, f"the mutated {mutation.path} does not compile")
            # The mutated run: the named tests together in the mutated checkout (the one run outside `observe`).
            junit = self._results / identity / "mutated-junit.xml"
            exit_code = self._run(folder, [*TESTS, str(junit), *mutation.tests])
            under_mutation = {node: "error" for node in mutation.tests} if exit_code in (2, *_NOT_COLLECTED) \
                else {node: _outcome(node, cases(self._junit(junit), exit_code)) for node in mutation.tests}
        restored = {node: self.observe(candidate, node, f"restored-{identity}") for node in mutation.tests}
        absent = [node for node in mutation.tests if restored[node] == "missing"]
        if absent:
            return result(SPEC_INVALID, f"named tests not present: {', '.join(absent)}")
        failing = {node: outcome for node, outcome in restored.items() if outcome != "passed"}
        if failing:
            held = self._held(candidate, base, failing, identity)
            if held:
                return result(REVERTED_FAILS, "fail with the file restored: "
                              + ", ".join(f"{node}:{failing[node]}" for node in held))
            return result(SPEC_INVALID, "environment: with the file restored the named tests do not pass, and not at "
                                        f"the starting revision now either: {', '.join(failing)}")
        # A skipped test is no evidence either way: the environment, not the candidate, decided it.
        skipped = [node for node in mutation.tests if under_mutation[node] == "skipped"]
        if skipped:
            return result(SPEC_INVALID, f"named tests skipped: {', '.join(skipped)}")
        survived = [node for node in mutation.tests if under_mutation[node] == "passed"]
        if survived:
            return result(SURVIVED, f"pass with the mutation: {', '.join(survived)}")
        return result(KILLED, f"every named test fails with the mutation: {', '.join(mutation.tests)}")

    def _fitness(self, folder: Path, results: Path, evidence: FitnessEvidence) -> tuple[int, bool]:
        """The fitness check's exit code in `folder`, and whether it is the check's own violation report (exit 1, a
        violation line, no Python traceback)."""
        output = results / "fitness-output.txt"
        exit_code = self._run(folder, [*FITNESS, evidence.check, str(output)])
        try:
            text = self._read(output).decode("utf-8", "replace")
        except OSError as error:
            raise SuiteUnrunnable(f"the fitness output cannot be read: {type(error).__name__}") from error
        return exit_code, exit_code == 1 and _VIOLATION.search(text) is not None and _TRACEBACK not in text


def _present(read_file: Callable[[Path], bytes], folder: Path, path: str) -> bool:
    """Whether a checkout holds `path` (False only when the read proves it absent)."""
    if not _inside(folder, folder / path):
        return False
    try:
        read_file(folder / path)
    except FileNotFoundError:
        return False
    return True


def _revision(candidate: CandidateRef) -> str:
    """The candidate's full SHA, the last part of its locator; SuiteUnrunnable when it names none."""
    revision = candidate.locator.rpartition("@")[2]
    if not _FULL_SHA.fullmatch(revision):
        raise SuiteUnrunnable("the candidate names no full SHA")
    return revision


def _inside(folder: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(folder.resolve())
    except ValueError:
        return False
    return True
