# Work unit: the regression gate runs the whole suite and the candidate never defines it

**Label:** `REGRESSION-GATE` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-06, for independent review. Not registered, not approved, not assessed, not released.
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
 "version": "revision-1",
 "intent": "Replace the VERIFIER's path-selected regression packs with one whole-suite comparison. The control plane runs every test under tests/ and tools/ at the release baseline and at the candidate, as the worker, and reads the per-test results itself. A candidate is inadmissible if any test that passed at the baseline fails, errors, disappears or cannot run at the candidate, or if a test that exists only at the candidate fails. The suite definition, the comparison and the baseline results come from the control plane's installed code and its own state, never from the candidate.",
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
  "src/alienintent/invocation_runtime/adapters/cli_worker.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/adapters/scripted_worker.py",
  "src/alienintent/invocation_runtime/domain/runtime.py",
  "src/alienintent/composition/work_registry.py",
  "tests/invocation_runtime/test_regression_gate.py",
  "tests/invocation_runtime/fixtures/regression_gate/cd5314b.xml",
  "tests/invocation_runtime/fixtures/regression_gate/057fbc1.xml",
  "tests/support/feature_regressions.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/k1_fixture.py",
  "tests/composition/k3_fixture.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_sandbox_run_profile.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tools/verification/replay_regression_gate.py"
 ],
 "excluded_scope": [
  "repairing any currently failing test (that is MAIN-GREEN)",
  "selecting tests by dependency or by changed path",
  "the coordinator's accept rule: it keeps requiring one feature-regressions:sha256: receipt for the exact candidate",
  "deleting tools/verification/run_feature_regressions.py, its manifest or its tests (they stop deciding admission; their removal is separate)",
  "the tools/evidence and tools/live scripts"
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
  "the replay of check 6 does not name exactly the tests the main session found (section 1)",
  "an existing test outside authorized_scope depends on the old receipt being written by the worker",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

The first factory DONE, `057fbc1` (work item `a41075ab`), landed 27 regressions in `tests/context_assembly`. The main
session found them on 2026-10-06 and proved the cause:

- **Which tests broke.** At `cd5314b`, `tests/context_assembly` had 2 failing tests. At `057fbc1` it has 29: 26 in
  `test_work_context.py` (`authorize` answers `AUTHORIZATION_STALE`) and 1 more there that holds on a missing READY
  assessment.
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

### 2.1 One suite, defined by the control plane

`src/alienintent/invocation_runtime/application/regression_gate.py` is new, and it is control-plane code. It is
imported from the installed runtime, never from the candidate.

- **The suite command** is fixed:
  `SUITE = ("python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", "<results file>", "tests", "tools")`.
  `tools/test_architecture_fitness.py` and `tools/verification/test_*.py` are inside `tools`, so the architecture
  checks are part of the suite.
- **`results(xml: bytes, exit_code: int) -> dict[str, str]`** maps each test's identity
  (`<file>::<classname-path>::<name>`, built from the junit `classname` and `name`) to one of `passed`, `failed`,
  `error` or `skipped`.
  - A collection error appears in junit as an `error` test case naming the file; it is kept under that identity.
  - If `exit_code` is not 0 or 1 (interrupted, usage error, internal error or no tests collected), or the XML cannot
    be parsed, it raises `SuiteUnrunnable`.
- **`compare(baseline: Mapping[str, str], candidate: Mapping[str, str]) -> tuple[str, ...]`** returns the sorted
  findings. It is empty when the candidate is admissible. Each finding is one of:
  - `regression:<id>:passed->failed`, `...:passed->error` or `...:passed->missing`, for every identity that is
    `passed` at the baseline and not `passed` or `skipped` at the candidate (a test the candidate skips, when it
    passed at the baseline, is also a finding: `passed->skipped`);
  - `new-test-fails:<id>:<outcome>`, for every identity absent at the baseline whose candidate outcome is `failed` or
    `error`.

  A baseline identity that is `failed` or `error` at the baseline is never a finding.
- **`receipt(baseline_sha, candidate_sha, baseline, candidate) -> str`** returns
  `"feature-regressions:sha256:" + sha256` over the canonical JSON of
  `{"baseline": baseline_sha, "candidate": candidate_sha, "baseline_results": baseline, "candidate_results": candidate}`.
  It is called only when `compare` is empty.

### 2.2 Who runs it

`cli_worker.py`: `_feature_regressions` and `_worker_feature_regressions` no longer run anything from the workspace's
`tools/verification`.
- **The candidate run:** the worker runs `SUITE` in the candidate workspace, through the existing sudo rule when there is
  a worker user, with the existing process-group wall clock. The junit file goes to
  `<results>/<invocation id>/candidate-junit.xml`, and the exit code is kept in memory.
- **The baseline run:** the same `SUITE`, in a fresh worker workspace checked out at the baseline SHA (with a worker user,
  `regression_base(invocation id)`; without one, `git merge-base HEAD origin/main` as today).
  - Its results are stored by the control plane at `<launch root>/regression-baselines/<baseline sha>.json`, as
    `{"baseline": sha, "results": {...}}` with mode 0644. That file is owned by the control-plane user, and the worker
    cannot write to it.
  - If that file already exists, the baseline is not run again.

### 2.3 Who decides

`real_worker.py`, `read_verdict` (line 145): `_feature_regression_receipt` no longer reads a worker-written receipt.
- **Reading:** it reads `candidate-junit.xml` through the same checked `read` the verdict uses, and the baseline results
  from the control plane's own file.
- **Deciding:** it calls `results` and then `compare`.
  - If there are findings, the VERIFIER outcome is `reject` with those findings, whatever the worker's verdict says.
    The existing route returns that to the PRODUCER.
  - If the suite could not run, the outcome is `feature-regressions-missing`.
  - Otherwise the receipt is `receipt(...)`, and the worker's verdict decides between accept and reject, as today.
- The coordinator's accept rule (`factory_coordinator.py` line 512) is unchanged.

### 2.4 Test fixtures

`tests/support/feature_regressions.py` is the one place fixtures build a passing regression result. It now writes a
`candidate-junit.xml` with one passing test, and the matching baseline file. Each listed fixture uses it.

### 2.5 The replay

`tools/verification/replay_regression_gate.py <base sha> <candidate sha>`:
- checks out each revision into a temporary folder;
- runs `SUITE` there with the current user;
- prints the findings of `compare` as one JSON list.

It uses only the installed `regression_gate` module. It is evidence tooling: it is not part of the suite, and no test
calls it.

## 3. Acceptance checks

1. **Comparison** (`tests/invocation_runtime/test_regression_gate.py`): `compare` gives exactly one finding for each of
   these cases, and no finding where none is due:
   - passed→failed, passed→error, passed→missing and passed→skipped;
   - a new test that fails, and a new test that errors;
   - failed→failed and error→failed (no finding);
   - passed→passed (no finding);
   - a new test that passes (no finding).
2. **Unrunnable suite:** `results` raises `SuiteUnrunnable` for exit codes 2, 3, 4 and 5, and for XML that cannot be
   parsed.
3. **The 057fbc1 case, recorded:** the junit files `fixtures/regression_gate/cd5314b.xml` and `057fbc1.xml`, produced by
   the replay of check 6 and committed. `compare` on them gives findings that include every `test_work_context.py`
   test that passes at `cd5314b` and fails at `057fbc1`. It gives no finding for the 2 tests already failing at
   `cd5314b`.
4. **The candidate cannot redefine the gate** (`test_regression_gate.py`, test
   `test_the_candidate_workspace_does_not_define_the_gate`). In a candidate workspace whose
   `tools/verification/run_feature_regressions.py` exits 0 and writes a passing receipt, and whose
   `feature_regressions.json` selects no pack, a failing test that passed at the baseline still gives a `reject` with
   its `regression:` finding.
5. **A worker-written receipt is ignored:** a `feature-regressions.json` written in the worker results folder with
   `passed: true` and a valid digest gives no receipt unless `compare` is empty.
6. **Replay, run by the VERIFIER:** `python3 tools/verification/replay_regression_gate.py cd5314b 057fbc1` prints a
   non-empty list naming the `test_work_context.py` tests of check 3. The VERIFIER records the output.
7. **Mutations, run exactly by the VERIFIER:**
   - **M1:** in `regression_gate.py` `compare`, return `()`. Then
     `python3 -m pytest -q tests/invocation_runtime/test_regression_gate.py -k 057fbc1` must FAIL. Revert, and it must
     pass.
   - **M2:** in `real_worker.py`, make `_feature_regression_receipt` read the worker's `feature-regressions.json` again.
     Then `python3 -m pytest -q tests/invocation_runtime/test_regression_gate.py -k test_the_candidate_workspace_does_not_define_the_gate`
     must FAIL. Revert, and it must pass.
   - **M3:** in `compare`, drop the `passed->missing` case. Then
     `python3 -m pytest -q tests/invocation_runtime/test_regression_gate.py -k missing` must FAIL. Revert, and it must
     pass.
8. **Whole-suite comparison by the VERIFIER:** the VERIFIER runs the whole suite at the starting revision and at the
   candidate, using no gate code from the candidate, and compares them per test. The candidate must add no failing
   test and change no passing test to failing.

## 4. Review record

**Revision 1 (2026-10-06).** First draft, from the Founder's decisions of 2026-10-06 (maintenance-required mode).
