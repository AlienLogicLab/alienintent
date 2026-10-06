"""REGRESSION-GATE: the whole-suite comparison the control plane runs before a VERIFIER session.

The suite definition, the comparison and the baseline results are the installed control plane's own code and state,
never the candidate's: every test under `tests` and `tools` runs at the release baseline and at the candidate, and a
candidate is inadmissible when a test that passed at the baseline does not pass at the candidate, or a test that
exists only at the candidate fails or errors. A baseline test that already fails, errors or is skipped is known debt,
not a regression.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
import json
from hashlib import sha256
import os
from pathlib import Path
import re
from xml.etree import ElementTree

# The one suite command, run in a checkout's root; `{junit}` is the junit file it writes.
SUITE = ("python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--continue-on-collection-errors", "--junitxml",
         "{junit}", "tests", "tools")
# Each suite run's own wall clock, separate from the session's `hard_wall_clock_seconds`.
SUITE_WALL_CLOCK = 1800
# The junit file's name in its results folder, and the most of it the control plane reads.
SUITE_JUNIT = "suite-junit.xml"
SUITE_JUNIT_LIMIT = 64 << 20
OUTCOMES = frozenset({"passed", "failed", "error", "skipped"})
# A test case recorded more than once keeps its worst outcome.
_RANK = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
_FULL_SHA = re.compile(r"[0-9a-f]{40}")


class SuiteUnrunnable(Exception):
    """The suite gave no result: an exit code other than 0 or 1, junit that cannot be parsed, or a timeout."""


def suite(junit: Path) -> list[str]:
    """`SUITE` with its junit file named."""
    return [str(junit) if part == "{junit}" else part for part in SUITE]


def results(xml: bytes, exit_code: int) -> dict[str, str]:
    """Each junit test case's identity (`classname::name`, exactly as given) and its outcome.

    With `--continue-on-collection-errors` a module that cannot be collected is an `error` test case. Exit codes 0
    and 1 are results; any other (interrupted, internal error, usage error, no tests collected) is no result.
    """
    if exit_code not in (0, 1):
        raise SuiteUnrunnable(f"the suite exited {exit_code}")
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as error:
        raise SuiteUnrunnable("the suite's junit cannot be parsed") from error
    found: dict[str, str] = {}
    for case in root.iter("testcase"):
        tags = {child.tag for child in case}
        outcome = "error" if "error" in tags else "failed" if "failure" in tags else "skipped" if "skipped" in tags \
            else "passed"
        identity = f"{case.get('classname', '')}::{case.get('name', '')}"
        if _RANK[outcome] >= _RANK.get(found.get(identity, "passed"), 0):
            found[identity] = outcome
    return found


def compare(baseline: Mapping[str, str], candidate: Mapping[str, str]) -> tuple[str, ...]:
    """The sorted findings: each baseline `passed` test whose candidate outcome is not `passed` (or is missing), and
    each test absent at the baseline that fails or errors at the candidate."""
    findings = [f"regression:{identity}:passed->{candidate.get(identity, 'missing')}"
                for identity, outcome in baseline.items() if outcome == "passed" and candidate.get(identity) != "passed"]
    findings += [f"new-test-fails:{identity}:{outcome}" for identity, outcome in candidate.items()
                 if identity not in baseline and outcome in ("failed", "error")]
    return tuple(sorted(findings))


def receipt(baseline_sha: str, candidate_sha: str, baseline: Mapping[str, str], candidate: Mapping[str, str],
            findings: tuple[str, ...]) -> str:
    """`feature-regressions:sha256:` over the canonical JSON of the comparison's five values."""
    document = {"baseline_sha": baseline_sha, "candidate_sha": candidate_sha, "baseline": dict(baseline),
                "candidate": dict(candidate), "findings": list(findings)}
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return "feature-regressions:sha256:" + sha256(encoded).hexdigest()


class RegressionGate:
    """One whole-suite comparison of a candidate clone against its release baseline.

    `run(folder, junit)` runs `SUITE` in `folder`, writes `junit` and answers the exit code (`SuiteUnrunnable` on
    timeout); `read(junit)` reads those bytes (with a worker user through the hand-over's checked descriptor);
    `checkout(sha, identity)` is a fresh checkout at that full SHA under `identity`, checked and cleaned up when the
    block ends; `baselines` is the control plane's own cache folder, `<baselines>/<sha>.json`; `results` is the folder
    whose `<identity>/suite-junit.xml` each run writes. The decision is taken from the bytes read as soon as each run
    ends; a later rewrite of a junit file changes nothing.
    """

    def __init__(self, run: Callable[[Path, Path], int], read: Callable[[Path], bytes],
                 checkout: Callable[[str, str], AbstractContextManager[Path]], baselines: Path, results: Path) -> None:
        self._run, self._read, self._checkout = run, read, checkout
        self._baselines, self._results = Path(baselines), Path(results)

    def check(self, invocation_id: str, workspace: Path, baseline_sha: str,
              candidate_sha: str) -> tuple[tuple[str, ...], str]:
        """The findings and the receipt for the candidate clone `workspace` at `candidate_sha`."""
        if not _FULL_SHA.fullmatch(baseline_sha) or not _FULL_SHA.fullmatch(candidate_sha):
            raise SuiteUnrunnable("the baseline and the candidate must be full SHAs")
        baseline = self._baseline(invocation_id, baseline_sha)
        candidate = self._suite(workspace, self._results / invocation_id / SUITE_JUNIT)
        findings = compare(baseline, candidate)
        return findings, receipt(baseline_sha, candidate_sha, baseline, candidate, findings)

    def _suite(self, folder: Path, junit: Path) -> dict[str, str]:
        exit_code = self._run(folder, junit)
        try:
            xml = self._read(junit)
        except OSError as error:
            raise SuiteUnrunnable(f"the suite's junit cannot be read: {type(error).__name__}") from error
        return results(xml, exit_code)

    def _baseline(self, invocation_id: str, sha: str) -> dict[str, str]:
        """The cached baseline results, or a fresh run at `sha` under `baseline-<sha>-<invocation id>`, cached before
        the checkout is cleaned up."""
        folder = self._folder()
        cached = self._cached(folder / f"{sha}.json", sha)
        if cached is not None:
            return cached
        identity = f"baseline-{sha}-{invocation_id}"
        with self._checkout(sha, identity) as path:
            found = self._suite(path, self._results / identity / SUITE_JUNIT)
            self._write(folder, sha, found)
        return found

    def _folder(self) -> Path:
        """`<baselines>`, made with the control plane's uid and mode 0711 and checked as `_export` checks its
        folders: not a link, a folder, owned by this uid. The worker cannot write there."""
        folder = self._baselines
        folder.mkdir(mode=0o711, exist_ok=True)
        if folder.is_symlink() or not folder.is_dir() or folder.lstat().st_uid != os.getuid():
            raise OSError(f"the regression baselines folder is not the control plane's: {folder}")
        os.chmod(folder, 0o711)
        return folder

    @staticmethod
    def _cached(path: Path, sha: str) -> dict[str, str] | None:
        try:
            document = json.loads(path.read_bytes().decode("utf-8"))
        except FileNotFoundError:
            return None
        except ValueError:
            return None  # an unreadable cache is run again and replaced
        found = document.get("results") if isinstance(document, Mapping) and document.get("baseline") == sha else None
        if not isinstance(found, Mapping) or not all(isinstance(k, str) and v in OUTCOMES for k, v in found.items()):
            return None
        return dict(found)

    @staticmethod
    def _write(folder: Path, sha: str, found: Mapping[str, str]) -> None:
        """`{"baseline": sha, "results": ...}` to `<baselines>/<sha>.json`, through a temporary file and a rename."""
        temporary = folder / f".{sha}.{os.getpid()}.tmp"
        data = json.dumps({"baseline": sha, "results": dict(found)}, sort_keys=True).encode()
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, folder / f"{sha}.json")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
