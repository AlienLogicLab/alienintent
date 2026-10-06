# Work unit: the regression gate runs the whole suite and the candidate never defines it

**Label:** `REGRESSION-GATE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 4, 2026-10-06, for independent review. Not registered, not approved, not assessed, not released.
**Position on the path:** this is the first of four in maintenance-required mode (Founder 2026-10-06). The order is:
1. REGRESSION-GATE;
2. MAIN-GREEN;
3. NO-CHANGE-CANDIDATE-REFUSED;
4. BOUNDED-ROUTINE-LAUNCH under a new id.

It is produced and verified by the hand-built maintenance path, because the factory's own gate is what is repaired.
**Founder decisions:** `manual/path-to-done/founder-decisions-2026-10-06-bounded-launch.md` (the later section).

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-4",
 "intent": "Before a VERIFIER session starts, the control plane runs one whole-suite comparison in place of the path-selected regression packs. It runs every test under tests/ and tools/ at the release baseline and at the candidate, as the worker, and reads the per-test results itself before any model session can touch them. A candidate is inadmissible if any test that passed at the baseline fails, errors, disappears or cannot run at the candidate, or if a test that exists only at the candidate fails. The suite definition, the comparison and the baseline results come from the control plane's installed code and its own state, never from the candidate.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: DONE is inadmissible if the candidate causes any previously passing applicable repository test or architecture check to fail.",
  "Founder 2026-10-06: whole suite, baseline vs candidate; per-test identity and result; baseline results cached by exact baseline SHA under control-plane ownership.",
  "Founder 2026-10-06: reject on baseline PASS -> candidate FAIL, baseline PASS -> candidate missing or not collected, baseline PASS -> candidate error before execution, and a required architecture check PASS -> FAIL. A baseline test that already fails and still fails is known debt, not a regression.",
  "Founder 2026-10-06: the candidate must not control the test-selection manifest or the comparison that decide whether it passes verification.",
  "Founder 2026-10-06: proven by replaying cd5314b -> 057fbc1. The gate must mechanically name the tests that passed at cd5314b and fail at 057fbc1. Do not claim the new gate verified itself.",
  "Founder 2026-10-06: produced and verified by the hand-built maintenance path, retired as soon as the gate is trusted."
 ],
 "authorized_scope": [
  "src/alienintent/invocation_runtime/application/regression_gate.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/adapters/cli_worker.py",
  "src/alienintent/invocation_runtime/adapters/git_worktree.py",
  "src/alienintent/composition/work_registry.py",
  "tests/invocation_runtime/test_regression_gate.py",
  "tests/invocation_runtime/fixtures/regression_gate/cd5314b.xml",
  "tests/invocation_runtime/fixtures/regression_gate/057fbc1.xml",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_work_registry.py",
  "tests/control_plane/test_cli.py",
  "tests/composition/test_upstream_integration_capstone.py",
  "tools/verification/replay_regression_gate.py",
  "tests/invocation_runtime/fixtures/regression_gate/findings.txt"
 ],
 "excluded_scope": [
  "repairing any currently failing test (that is MAIN-GREEN)",
  "selecting tests by dependency or by changed path",
  "the coordinator's accept rule: it keeps requiring one feature-regressions:sha256: receipt for the exact candidate",
  "deleting tools/verification/run_feature_regressions.py, its manifest or its tests (they stop deciding admission for the registry profile; their removal is separate)",
  "the offline, sandbox, lifecycle-capstone and scripted-worker paths, which do not land on main: they keep today's worker-written receipt",
  "the tools/evidence and tools/live scripts, including tools/live/worker_boundary_check.py, a live check that builds a LandingAuthority but lands no candidate",
  "docs/operations.md: its description of <launch>/results/<invocation>/feature-regressions.json becomes stale for the registry profile; the assertion of that text in test_worker_launch.py line 1487 stays unchanged and still holds, and the document is corrected separately"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem",
  "process-control"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-8 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs the replay of check 6 itself and records its output",
  "the VERIFIER runs mutations M1, M2 and M3 of section 3 exactly and records that each makes its named test fail and that reverting makes it pass",
  "the VERIFIER runs the whole suite at the starting revision and at the candidate and compares them per test, without using any gate code from the candidate"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "defending against candidate test code that deliberately forges its own results (for example a conftest.py hook); the gate stops accidental regressions and stops the candidate redefining the gate",
  "making the suite faster"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/automated-closure.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "a named function or line does not exist at the starting revision",
  "the replay of check 6 does not print exactly the 39 findings of findings.txt (section 1)",
  "a test outside authorized_scope runs a VERIFIER through the registry profile and needs the suite runner replaced",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

The first factory DONE, `057fbc1` (work item `a41075ab`), landed 27 regressions in `tests/context_assembly`. The main
session found them on 2026-10-06 and proved the cause:

- **Which tests broke.** The main session ran the whole suite (`tests` and `tools`) at `cd5314b` and at `057fbc1`, with
  junit output.
  - `cd5314b`: 2,853 test cases, 4 of them failing. These are the folder-name test in `test_sandbox_run_profile.py`,
    `test_ambiguity`, `test_readiness_consumer` and `tools/orchestration/test_director.py`.
  - `057fbc1`: 2,869 test cases.
  - Under this packet's rules there are **39 findings**: 27 in `tests/context_assembly` and 12 in
    `tests/control_plane`.
  - The recorded files are in `manual/path-to-done/regression-replay/`:
    - `cd5314b.xml` (sha256 `229913df3074a276…`);
    - `057fbc1.xml` (sha256 `7bd9aa84b97aaf80…`);
    - `findings.txt` (sha256 `5347c56c55daac14…`), which holds the exact 39 findings, one per line.

  The two junit files become the fixtures of check 3, committed unchanged, and `findings.txt` is the exact expected
  output of checks 3 and 6.
- **Why the gate missed them.** The VERIFIER's regression runner, `tools/verification/run_feature_regressions.py`,
  runs only the packs whose hand-written path patterns match the changed files. For `057fbc1` it selected 4 of 13
  packs (`requirement-priority-continuity`, `wave2a-upstream-integration-capstone`,
  `canonical-release-precondition-gate` and `canonical-live-release-admission-proof`). None of them runs
  `tests/context_assembly/test_work_context.py`.
- **The candidate defines its own gate.** The runner and its manifest are read from the candidate's workspace
  (`cli_worker.py` lines 117-118 and 139), so a candidate can change the gate that judges it.
- **The receipt proves nothing about who wrote it.** The worker user writes it, and `real_worker.py` lines 121-142 only
  check its fields and a digest that uses no secret.

## 2. The change

### 2.1 The comparison (control-plane code)

`src/alienintent/invocation_runtime/application/regression_gate.py` is new. It is imported from the installed
runtime, never from the candidate.

- **The suite command** is fixed:
  `SUITE = ("python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--continue-on-collection-errors", "--junitxml", <file>, "tests", "tools")`.
  `tools/test_architecture_fitness.py` is inside `tools`, so the architecture checks are part of the suite.
- **`SUITE_WALL_CLOCK = 1800`** seconds for each suite run. It is separate from the session's
  `hard_wall_clock_seconds`.
- **`results(xml: bytes, exit_code: int) -> dict[str, str]`** maps each test case's identity to one of `passed`,
  `failed`, `error` or `skipped`.
  - The identity is the junit `classname + "::" + name`, exactly as given.
  - With `--continue-on-collection-errors`, a module that cannot be collected appears as an `error` test case.
  - Exit codes 0 and 1 are results.
  - For any other exit code (interrupted, internal error, usage error or no tests collected), for XML that cannot be
    parsed, and for a timeout, it raises `SuiteUnrunnable`.
- **`compare(baseline, candidate) -> tuple[str, ...]`** returns the sorted findings:
  - `regression:<id>:passed-><outcome or missing>`, for every identity `passed` at the baseline whose candidate
    outcome is not `passed`;
  - `new-test-fails:<id>:<outcome>`, for every identity absent at the baseline whose candidate outcome is `failed` or
    `error`.

  Any identity that is `failed`, `error` or `skipped` at the baseline gives no finding.
- **`receipt(baseline_sha, candidate_sha, baseline, candidate, findings) -> str`** returns
  `"feature-regressions:sha256:" + sha256` over the canonical JSON of the five values.
- **`class RegressionGate`** takes these arguments:
  - `run: Callable[[Path, Path], int]`: runs `SUITE` in a folder, writes the junit file, returns the exit code, and
    raises `SuiteUnrunnable` on timeout;
  - `read: Callable[[Path], bytes]`;
  - `checkout: Callable[[str], Path]`: a fresh worker clone at a full SHA;
  - `baselines: Path`.

  `check(invocation_id, workspace, baseline_sha, candidate_sha) -> tuple[tuple[str, ...], str]` returns the findings
  and the receipt.

### 2.2 Where it runs: before the VERIFIER session, in the control plane

`real_worker.py`, `_evaluate` (lines 290-340). `RealWorkerProvider` takes two keywords:
`regression_gate: RegressionGate | None = None` and `regression_base: Callable[[str], str | None] | None = None`.

When a gate is given:
- **When it runs:** right after the candidate clone (line 312) and the preparation (line 319), and before the session
  (line 334), the provider calls `gate.check(...)`.
- **The baseline SHA** is `regression_base(invocation id)`. The registry passes `preparation.starting.get` in both the
  worker and the no-worker case; `LaunchPreparation.prepare` sets it for every role (`work_registry.py` line 1164) before
  this point. A missing value, or one that is not a full SHA, gives `WorkerOutcome("feature-regressions-missing")`.
- **The baseline:**
  - **Cached:** if `<baselines>/<baseline sha>.json` exists, its results are used.
  - **Not cached:**
    1. `checkout(baseline sha)` makes a fresh checkout at that SHA under the identity `baseline-<sha>-<invocation id>`,
       so two VERIFIERs never collide.
       - **With a worker user:** `WorkerCloneAdapter.allocate` (`git_worktree.py` lines 120-126), a fresh worker
         clone of the packets clone.
       - **Without one:** `GitWorktreeAdapter.allocate` (`git_worktree.py` line 54), a worktree.
    2. The checkout's revision is read with `handover.revision(path)`, which runs `rev-parse` as the worker and checks
       for 40 hex characters. The control plane runs no git in a worker clone. Without a worker user it is
       `source.revision(path)`. The result must equal the SHA.
    3. The suite runs there, with `PYTHONDONTWRITEBYTECODE=1`.
       - **With a worker user:** its junit goes to `<results>/baseline-<sha>-<invocation id>/suite-junit.xml`, the
         folder `allocate` already makes (`git_worktree.py` lines 111-118). The control plane reads it at once with
         `read_result("baseline-<sha>-<invocation id>", "suite-junit.xml", limit=64 << 20)`.
       - **Without one:** the junit goes to `<launch root>/regression-results/baseline-<sha>-<invocation id>/suite-junit.xml`,
         a folder the control plane creates itself, and is read directly.
    4. The checkout is cleaned up after the cache file of step 5 is written.
       - **With a worker user:** through the existing `WorkerCloneAdapter.cleanup`. The folder carries the `producer-`
         prefix that `allocate` always uses.
       - **Without one:** through the existing `GitWorktreeAdapter.cleanup`, followed by `git branch -D` of its
         `invocation/baseline-...` branch in the packets clone.
       - A cleanup refusal (for example files the tests left behind) is "workspace retained" and does not fail the gate.
       - Results folders are kept, as every invocation's results folder is kept today.
    5. The control plane writes `{"baseline": sha, "results": ...}` to `<baselines>/<sha>.json` atomically, through a
       temporary file in the same folder and a rename. This file is the only state shared between invocations.
  - Any `CandidateUnavailable` or `OSError` on this path gives `WorkerOutcome("feature-regressions-missing")`.
  - `<baselines>` is `<launch root>/regression-baselines`. The control plane makes it with its own uid, not as a
    symbolic link, with mode 0711. As `_export` does (`work_registry.py` lines 1189-1194), the folder's owner and that it
    is not a link are checked. The worker cannot write there.
- **The candidate:** the suite runs in the VERIFIER's own candidate clone, with `PYTHONDONTWRITEBYTECODE=1`.
  - **With a worker user:** its junit file goes to `<results>/<invocation id>/suite-junit.xml`, the invocation's
    existing results folder (made when the candidate clone is made). It is read with
    `read_result(<invocation id>, "suite-junit.xml", limit=64 << 20)`.
  - **Without one:** it goes to `<launch root>/regression-results/<invocation id>/suite-junit.xml`, a folder the control
    plane creates itself.
  - The control plane reads those bytes as soon as the suite ends, before the session starts. It decides from those bytes only and keeps the decision in memory. A later rewrite of the file
    changes nothing.
  - An `OSError` from that read is `SuiteUnrunnable`.
- **The verdict path stays clean.** After the suite and before the session:
  - With a worker user, `read_result(<invocation id>, "verdict.json")` must raise `FileNotFoundError`.
  - Without one, `workspace / VERDICT_PATH` must not exist; this is checked both before and after the suite.
  - Any other answer gives `WorkerOutcome("verdict-preexisting")`.
  - Files the tests leave in the candidate clone stay there. The session sees them, as it sees any working tree.
- **The decision:**
  - **With findings:** the session is not started. The outcome is `WorkerOutcome.reject(candidate, findings, (receipt,))`.
    The coordinator's existing route (`factory_coordinator.py` lines 511-518) sends it to the PRODUCER as a rework.
  - **With no findings:** the session runs as today. `read_verdict` takes the keyword `gate_receipt: str | None = None`.
    When it is given, `read_verdict` uses it in place of `_feature_regression_receipt` and never reads a
    worker-written `feature-regressions.json`.
  - **`SuiteUnrunnable`** gives `WorkerOutcome("feature-regressions-missing")`.

When no gate is given, nothing changes. This is the case for the offline, sandbox and lifecycle-capstone profiles,
which never land on main.

### 2.3 Composition

- **`work_registry.py` `_launch_chain`** builds one `RegressionGate` and passes it to the `RealWorkerProvider`.
  - `run` uses the worker's sudo rule and environment (`worker_prefix`), or runs directly when there is no worker user.
  - `checkout` uses the producer allocator.
  - `read` uses `handover.read_result`. Without a worker user it reads the `<launch root>/regression-results/` folders
    of 2.2 directly.
  - The `CandidateHandover` protocol's `read_result` (`real_worker.py` line 212) gains `limit: int = 1 << 20`, and test
    fakes of it accept `limit`.
  - `CliWorkerProvider` is built with the new keyword `feature_regressions=False`, so its old step
    (`cli_worker.py` lines 202-207) does not run in the registry profile.
- **Tests:** `WorkRegistry` takes the keyword `suite_run: Callable[[Path, Path], int] | None = None`, with the real
  runner as the default. Test fixtures that launch a VERIFIER through the registry pass a fake that writes one passing
  junit test case. The fixtures are in `test_worker_launch.py`, `test_work_registry.py`, `test_cli.py` and
  `test_upstream_integration_capstone.py`.

### 2.4 The replay (evidence tooling)

`tools/verification/replay_regression_gate.py <base sha> <candidate sha>`:
- checks out each revision into a temporary folder;
- runs `SUITE` with the current user;
- prints the findings of `compare` as a JSON list, and writes both junit files beside it.

No test calls it.

## 3. Acceptance checks

1. **Comparison** (`tests/invocation_runtime/test_regression_gate.py`). Each case is its own test, named
   `test_compare_<case>`, with these cases:
   - `passed_to_failed`, `passed_to_error`, `passed_to_missing` and `passed_to_skipped`;
   - `new_test_fails` and `new_test_errors`;
   - `failed_stays_failed`, `error_to_failed` and `skipped_to_failed` (no finding);
   - `passed_stays_passed` and `new_test_passes` (no finding).
2. **Unrunnable suite:** `results` raises `SuiteUnrunnable` for exit codes 2, 3, 4 and 5 and for XML that cannot be
   parsed. A collection-error test case in the XML with exit code 1 is a result.
3. **The 057fbc1 case, recorded** (test `test_compare_names_the_057fbc1_regressions`). `fixtures/regression_gate/cd5314b.xml`
   and `057fbc1.xml` are the junit files the main session recorded (section 1), committed unchanged. `compare` on them
   gives exactly the findings listed in section 1. This proves `compare` on recorded data only; checks 6 and 8 are
   the proof under real conditions.
4. **The decision is taken before the session, from the control plane's own read** (test
   `test_a_rewritten_junit_file_changes_nothing`). A fake suite run writes a junit file with a regression, and a fake
   session then rewrites that file with all tests passing and leaves an `accept` verdict. The outcome is `reject` with
   the `regression:` finding, and the session was never started. A second case has the suite write a `verdict.json`
   into `<results>/<invocation id>/`: the outcome is `verdict-preexisting`.
5. **The candidate cannot redefine the gate** (test `test_the_candidate_workspace_does_not_define_the_gate`). The
   candidate workspace holds a `tools/verification/run_feature_regressions.py` that exits 0, a manifest selecting no
   pack, and, in the worker results folder, a `feature-regressions.json` with `passed: true` and a valid digest. A
   test that passed at the baseline and fails at the candidate still gives `reject` with its finding.
6. **Replay, run by the VERIFIER:** `python3 tools/verification/replay_regression_gate.py cd5314b 057fbc1` prints
   exactly the findings of section 1. The VERIFIER records the output.
7. **Mutations, run exactly by the VERIFIER:**
   - **M1:** in `regression_gate.py` `compare`, `return ()`. Then
     `python3 -m pytest -q tests/invocation_runtime/test_regression_gate.py -k test_compare_names_the_057fbc1_regressions`
     must FAIL. Revert, and it must pass.
   - **M2:** in `real_worker.py` `_evaluate`, call `gate.check` after the session instead of before it. Then
     `python3 -m pytest -q tests/invocation_runtime/test_regression_gate.py -k test_a_rewritten_junit_file_changes_nothing`
     must FAIL. Revert, and it must pass.
   - **M3:** in `compare`, drop the missing case. Then
     `python3 -m pytest -q tests/invocation_runtime/test_regression_gate.py -k test_compare_passed_to_missing` must
     FAIL. Revert, and it must pass.
8. **Whole-suite comparison by the VERIFIER:** the VERIFIER runs the whole suite at the starting revision and at the
   candidate, using no gate code from the candidate, and compares them per test. The candidate adds no failing test
   and changes no passing test to anything else.

## 4. Review record

**Revision 4 (2026-10-06).** Follow-up check of `0632e75` (FAIL; B1-B10 fixed, plus new findings N1-N6).
- The junit files go only into folders that already exist: the baseline folder `allocate` makes, and the invocation's
  own results folder. Without a worker user, they go into control-plane folders (N1, N6).
- No results folder is removed, as today (N2).
- The cache is written before cleanup, a cleanup refusal does not fail the gate, and the baseline branch is deleted
  without a worker user (N3).
- The `producer-` prefix is stated (N4).
- The protocol gains `limit` (N5).
- `PYTHONDONTWRITEBYTECODE=1` is set for both runs (N6).
- The `docs/operations.md` assertion stays unchanged (B10).

**Revision 3 (2026-10-06).** Follow-up REVIEWER of `2b9ecff` (FAIL; 13 of revision 1's 14 findings fixed). The
recorded replay matches `findings.txt` exactly.
- The method is `_evaluate` (B1).
- `regression_base` is passed to the provider (B2).
- Baseline identities are unique per invocation, with their junit folder and their cleanup named (B3).
- The checkout revision is read as the worker (B4).
- The allocator without a worker user is named (B5).
- A 64 MiB read limit, with `OSError` handled (B6).
- The suite gets its own results folder, with a check that the verdict file is absent (B7).
- The excluded live check is named (B8).
- The folder mode is 0711, checked as in `_export` (B9).
- The stale documentation is named (B10).

**Revision 2 (2026-10-06).** REVIEWER of `6d559d8` (FAIL, 14 findings). The gate is now one control-plane step
before the VERIFIER session, in the registry profile only.
- The decision is taken from bytes read before any session can rewrite them.
- Exit code 1 is a result, and collection errors do not stop the run.
- The baseline is a fresh clone at the SHA, checked, and written atomically into a folder the control plane owns.
- Each suite run has its own wall clock.
- No receipt written by the worker is used.
- The profiles that never land are left unchanged, so the fixtures that depended on the old receipt stay as they are.
- The identity rule, the comparison wording and the mutation names are exact.

**Revision 1 (2026-10-06).** First draft, from the Founder's decisions of 2026-10-06 (maintenance-required mode).
