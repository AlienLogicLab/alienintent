# REGRESSION-GATE (a38f0cb8) VERIFIER verdict for 883e4c5

Independent VERIFIER subagent (fresh context, own clones, own comparison code), 2026-10-06, hand-built maintenance path.

**Verdict: ACCEPT** for candidate 883e4c5c36e73851e62f740fc270bb0e93f20915 (REGRESSION-GATE, a38f0cb8-6803-463a-8031-0005f33aef01), checked against the packet at bf3efcc.

I worked only in my own clones under /tmp/claude-1000/-mnt-d-Projects-alienintent/f174fe73-2ea1-4cce-912f-8c725b47503f/scratchpad/verify-a38f/:
- `base` at bf3efcc
- `cand` at 883e4c5, used for mutations and the replay
- `suitecand` at 883e4c5, used for whole-suite runs

I confirmed each SHA with `git rev-parse HEAD`. I made no edits that remain, no commits, no pushes, and used no network.

**Step 1, custody: PASS.**
- 883e4c5 descends from bf3efcc through two commits, 5aeaeb3 and 883e4c5.
- 12 files changed, all in authorized_scope: `regression_gate.py`, `real_worker.py`, `cli_worker.py`, `git_worktree.py`, `work_registry.py`, `test_regression_gate.py`, `test_worker_launch.py`, `test_work_registry.py`, the 3 fixtures and `replay_regression_gate.py`.
- The three fixture sha256 values match the expected ones and the files in /home/netmarine/.local/state/alienintent/manual/path-to-done/regression-replay/: cd5314b.xml 229913df…, 057fbc1.xml 7bd9aa84…, findings.txt 5347c56c….
- `docs/operations.md` and the assertion at `test_worker_launch.py` line 1486 are unchanged.

**Step 2, the diff against the packet: no defects.** The departures the PRODUCER declared:
- **(a) `checkout(sha, identity)` as a context manager, plus a `results` argument: keeps intent and safety.**
  - The cache is written inside the `with` block, so before cleanup.
  - Cleanup runs in `finally`, so also on failure. A cleanup refusal or `branch -D` failure is swallowed ("workspace retained").
  - `results` only names the root of the junit folder, which the packet requires.
  - The identity is `baseline-<sha>-<invocation>`.
  - The revision is checked through `source.revision`. With a worker user, `source` is `IntakeSourceControl`, whose `revision` runs as the worker and checks 40 hex characters.
- **(b) `GitWorktreeAdapter.remove_branch`: keeps intent.**
  - It is the packet's `git branch -D` step, guarded: the branch must start with `invocation/` and the path must be gone.
  - It is called only without a worker user, after a successful cleanup.
- **(c) Without a worker user, the suite runs with the allowlisted worker environment plus `PYTHONDONTWRITEBYTECODE=1`, not `os.environ`: keeps intent and is safer.**
  - No control-plane credentials reach candidate test code.
  - Imports still resolve to the checkout, because `pyproject.toml` sets `pythonpath = ["src"]`.
- **(d) `tools/test_architecture_fitness.py` does not exist: not a defect.** The real file is `tests/test_architecture_fitness.py`, which the `tests` argument of `SUITE` covers. This is an error in the packet's text.

The packet's core claims, each confirmed in the code:
- **Decision from early bytes:** `_gate` runs `gate.check` before `_process.run`. `check` reads each junit file right after its run, and the decision lives in memory.
- **Findings reject without a session:** `WorkerOutcome.reject(candidate, findings, (receipt,))` is returned before the session.
- **No worker-written receipt:** `read_verdict(..., gate_receipt=...)` skips `feature-regressions.json`. `test_worker_launch` now asserts that this file is never read.
- **Baseline cache:** written with `O_EXCL|O_NOFOLLOW` to a temporary file, then fsync and `os.replace`. The folder is made 0711 and checked for not-a-link, is-a-directory and owner uid.
- **Exit codes:** 0 and 1 are results. Any other code, unparseable XML, a read `OSError` or a timeout gives `SuiteUnrunnable`, which becomes `feature-regressions-missing`.
- **`SUITE`** contains `--continue-on-collection-errors`.
- **Verdict path:** checked before and after the suite without a worker user, and via `read_result` with one.
- **Old regression step off:** `CliWorkerProvider(..., feature_regressions=False)` only in `_launch_chain`.
- **Other profiles unchanged:** `regression_gate=` and `feature_regressions=False` are passed only in `work_registry.py` (lines 718 and 728). The defaults leave the offline, sandbox and capstone profiles unchanged.
- **One small addition not in the packet:** a test case that appears more than once keeps its worst outcome. This is harmless; none of the junit files I checked has duplicate identities.

**Step 3, named tests: PASS.**
- The exact command gave `174 passed in 30.57s`.
- My first attempt went through the rtk hook rewrite and gave false collection errors (`No module named tests.invocation_runtime`). This came from the tooling, not the candidate. Run via `rtk proxy`, it passes.

**Step 4, mutations: all three behave as required.**
- **M1** (`return ()` in `compare`): `1 failed, 26 deselected`. After revert: `1 passed, 26 deselected`.
- **M2** (gate check moved after the session): `1 failed` (`AssertionError` at `test_regression_gate.py:200`).
  - The first revert also failed. The cause was stale bytecode: the same file size and the same-second mtime meant Python kept the mutated .pyc.
  - After removing `__pycache__`: `1 passed, 26 deselected`.
- **M3** (drop the missing case): `1 failed`. After revert: `1 passed` (run with `PYTHONDONTWRITEBYTECODE=1`).
- The candidate clone is back at 883e4c5. Its only untracked files are the replay's two xml outputs.

**Step 5, whole suite with my own comparison: no finding.**
- My script is mycompare.py in the scratchpad folder. It uses only `xml.etree` and imports nothing from the candidate.
- bf3efcc: `43 failed, 2825 passed, 4 skipped in 644.71s`, exit 1, 2,872 cases.
- 883e4c5, first run in parallel with the baseline: `45 failed, 2850 passed, 4 skipped`. My comparison gave 2 findings:
  - `tests.invocation_runtime.test_owned_work::test_client_exit_with_detached_owned_work_active_does_not_end_the_invocation`
  - `tests.invocation_runtime.test_owned_work::test_owned_work_outliving_the_wall_clock_is_stopped_with_the_client`
- Cause of those two: `ProcOwnership().owned_work` scans every process on the machine for fixed markers (`launch:AC08:0` and `:1`). The baseline run running at the same moment created processes with the same markers. Both tests pass 3 times out of 3 when run alone at the candidate.
- 883e4c5, re-run alone: `43 failed, 2852 passed, 4 skipped in 581.79s`, 2,899 cases. My comparison gives **findings=0**.

**Step 6, replay: PASS.**
- `python3 tools/verification/replay_regression_gate.py cd5314b 057fbc1` exited 0 and printed a JSON list of 39 entries. It equals the 39 lines of the recorded findings.txt exactly.
- My own comparison on the recorded fixture files gives 39 findings, byte-identical to findings.txt (2,853 baseline cases with 4 failed; 2,869 candidate cases with 43 failed).
- My comparison on the replay's freshly written xml files also gives a byte-identical 39 lines.

**Findings.** None block acceptance.
1. **Low, `tests/invocation_runtime/test_owned_work.py` lines 41 and 51.** Pre-existing and not in this diff. The tests check the whole machine for fixed markers, so two suite runs at the same time give false failures. This matters for the new gate: two VERIFIER gates running at once could reject a good candidate. It should be handled later, under MAIN-GREEN or its own item, since this packet excludes repairing tests.
2. **Low, packet section 2.1.** It names `tools/test_architecture_fitness.py`, but the real path is `tests/test_architecture_fitness.py`. The behavior is correct; the wording should be fixed.
3. **Info, mutation procedure.** Reverting a mutation with `git checkout --` in the same second can leave stale `.pyc` files. Future mutation steps should run with `PYTHONDONTWRITEBYTECODE=1` or clear `__pycache__`.
