# Work unit: a PRODUCER that changes nothing does not produce a candidate

**Label:** `NO-CHANGE-CANDIDATE-REFUSED-R2` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** R2 draft revision 1, 2026-10-09, for independent review. Not registered, not assessed, not released.
**Re-issue:** this is NO-CHANGE-CANDIDATE-REFUSED revision 5 (work item `77d48c83-af41-40fa-bd0d-a56e7e67fc30`, packet
`4dd5c48`) re-issued against main `bc9a9d8`, with the same approved requirement. Maintenance commit `bc9a9d8` moved
main while `77d48c83` was in flight (its accepted candidate `6c16563` sat on `1837fd4`), and the factory has no
BASE_MOVED revalidation yet, so `77d48c83` was wound down (`cancelled-by-operator`, retired; not DONE). Founder
decision 2026-10-09 (`founder-decisions-2026-10-09-reissue.md`): the replacement is assessed and verified on its own;
the ratification of `6c16563` does not transfer. Bootstrap release 3 releases it.
**Position on the path:** a factory repair that must land before BOUNDED-ROUTINE-LAUNCH is retried. Work item
`3d4e1215-c293-42d9-a112-57eabc289eed` was stopped (`cancelled-by-operator`, version 3). Its PRODUCER returned the
starting revision `bceea00` unchanged, and the factory admitted it as a successful PRODUCER result with a candidate,
then advanced the item to VERIFY.
**Starting revision:** main `bc9a9d8` (after the closure-recovery maintenance repair; the whole suite passes there:
2003 passed, 4 skipped). Every line number below is at `bc9a9d8`. Between `a632147` (revision 5's base) and `bc9a9d8`
only `factory_coordinator.py` changed among the scope files; its line numbers below are updated.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "r2-revision-1",
 "intent": "When a PRODUCER's process succeeds but its claimed revision has the same git tree as the starting revision (the same commit, an empty commit, or a commit that is later reverted), the factory publishes no candidate. It records a typed no-change PRODUCER result with a finding, and the work item stays in IMPLEMENT as a rework within its attempt budget. No VERIFIER attempt is used. A descendant commit with a different tree is admitted as today.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: a PRODUCER assigned to IMPLEMENT must produce a repository change. If it returns the starting revision unchanged, implementation did not occur.",
  "Founder 2026-10-06: candidate == starting revision -> typed no-change PRODUCER result -> finding -> _rework -> remains IMPLEMENT -> no VERIFIER attempt consumed.",
  "Founder 2026-10-06: the current work item contract has no authorized no-repository-change execution mode. This repair therefore refuses unchanged candidates. Introducing such a mode requires a separate contract and schema decision and is out of scope.",
  "Founder 2026-10-06: the rejection test is discriminating: restoring the ancestor-only check makes it fail.",
  "Founder 2026-10-08: 'changed the repository' means the candidate's git tree differs from the starting revision's git tree (`<revision>^{tree}`). Commit identity is not enough: an empty commit, a commit then its revert, or any other commit whose contents equal the starting revision's is no-change. The check is made in `_produce` (so the coordinator sees the no-change result at once) and in `hand_over` (the custody backstop).",
  "Founder 2026-10-08: tests cover the same commit, an empty descendant commit and a commit-then-revert (each refused), and a descendant commit with a different tree (accepted).",
  "Founder 2026-10-09: this item re-issues work item 77d48c83 (packet 4dd5c48, revision 5) against baseline bc9a9d8 with the same approved requirement; its candidate is independently assessed and verified, and the ratification of candidate 6c16563 does not transfer."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/ports/source_control.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "tests/invocation_runtime/test_no_change_candidate.py",
  "tests/invocation_runtime/test_git_source_control.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/execution_coordination/test_factory_coordinator.py"
 ],
 "excluded_scope": [
  "any contract or schema field that allows a no-change work item",
  "the lifecycle transition rules in execution_coordination/domain/lifecycle.py",
  "the VERIFIER, CLOSURE and Landing Authority paths",
  "the regression gate (invocation_runtime/application/regression_gate.py) and its call in RealWorkerProvider._evaluate",
  "BOUNDED-ROUTINE-LAUNCH and BOARD-FOLLOWS-WORK-STATE changes"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-7 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1-M5 of check 6 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "keeping the worker session's text: the durable evidence is the journal, the workspace and the coordinator record"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
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
  "the change would need a lifecycle transition rule change",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

`RealWorkerProvider._produce` (`real_worker.py` lines 496-567) treats a successful process as a successful PRODUCER
result. It then publishes whatever revision the workspace's HEAD names (line 543). The only check on that revision is
`IntakeSourceControl.hand_over` (`git_source_control.py` lines 271-294), which requires the claimed revision to descend
from the starting revision (line 291). A revision descends from itself, so an unchanged workspace passes. So does any
descendant commit with the starting tree: an empty commit, or a commit and its revert.

Work item `3d4e1215` showed the effect. The intake ref `refs/intake/launch-3d4e1215-…-0`, the bundle head and the
candidate branch all name `bceea00`, which is the release baseline. Yet the coordinator recorded `success` and
advanced to VERIFY (`factory_coordinator.py` lines 492-498).

## 2. The change

1. **One constant.** `NO_CHANGE = "no-change"` in `execution_coordination/ports/worker_provider.py`, next to
   `MISSING_TERMINAL_RESULT` (line 17).
2. **A tree reader next to `revision`.** `tree(self, workspace: Path, revision: str) -> str` answers
   `<revision>^{tree}` as a 40-hex object id, or raises `CandidateUnavailable("tree id is not a full object id")`.
   - Declared in the `SourceControl` protocol (`invocation_runtime/ports/source_control.py`, after line 41) and in the
     hand-over protocol in `real_worker.py` (after line 213).
   - `GitSourceControl.tree` (`git_source_control.py`, after `revision`, line 75):
     `self._git("rev-parse", "--verify", f"{revision}^{{tree}}", cwd=workspace)`, with the length check of `revision`.
   - `IntakeSourceControl.tree` (after its `revision`, line 260): run as the worker in its own workspace, exactly as its
     `revision` is: `self._as_worker(workspace, "git", "rev-parse", "--verify", f"{revision}^{{tree}}")`, checked with
     `_FULL_SHA`. Like `revision`, its output is data, and the trusted decision is the intake's (2.4).
3. **The PRODUCER refuses an unchanged tree** (`real_worker.py`, `_produce`). This is the one place the rule is decided,
   before both publication paths.
   - **The starting tree** has one source in every case: the workspace's own revision, read through
     `reader = self._source if self._handover is None else self._handover` as
     `starting_tree = reader.tree(workspace.path, reader.revision(workspace.path))`. These two statements are the first
     inside the existing `try:` (line 526), before `schedule = RetrySchedule(...)` (line 527) and before the session
     runs. The workspace is checked out at the starting revision either way, and a raise there is cleaned up by the
     existing `finally`. A prepared value is never compared directly.
   - **After a successful process,** right after `revision = ...` (line 543) and before the `publication-started`
     append (lines 544-546), when `reader.tree(workspace.path, revision) == starting_tree`:
     - The outcome is `WorkerOutcome(NO_CHANGE, None, findings=(f"no-change-candidate:{revision}: the PRODUCER's revision has the starting revision's tree; IMPLEMENT requires a repository change",))`.
     - Nothing is handed over, nothing is published, and no `publication-started` record is written.
     - The outcome is journaled and read back like any other PRODUCER result, through the existing
       `invocation-outcome` record with `candidate: None` and the finding.
     - The workspace is cleaned up as for any non-success result.
   - `correlated_outcome` (`real_worker.py` line 72) already admits a PRODUCER kind other than `success` only with no
     candidate (lines 101-103). So no change is needed there.
4. **The custody backstop** (`git_source_control.py`, `IntakeSourceControl.hand_over`). After the ancestor check
   (line 291) and in place of the bare tree read on line 293, the intake reads both trees in its own repository and
   refuses equal ones:
   `tree = self._intake_out("rev-parse", "--verify", f"{claimed}^{{tree}}")`, then
   `if tree == self._intake_out("rev-parse", "--verify", f"{starting}^{{tree}}"): raise CandidateUnavailable("candidate tree equals the starting revision's tree")`.
   A claim equal to the starting SHA has the starting tree, so it is refused here too. A refusal here is a custody
   refusal, handled exactly as today's ancestor refusal (the `CandidateUnavailable` leaves `_produce` as it does now),
   not a no-change result. It is reachable only if the worker-run tree read of 2.3 lies.
5. **The coordinator sends it to rework** (`factory_coordinator.py`, `_advance`, PRODUCER branch).
   - Just before `if outcome.kind != "success" or outcome.candidate is None:` (line 497), add:
     `if outcome.kind == NO_CHANGE: return self._rework(item, current, prior, invocation, "producer", tuple(outcome.findings))`.
   - In `_rework` (line 580), line 587 becomes
     `reworked = state if source == "producer" else transition(state, state.version, "rework")`. The item is already at
     IMPLEMENT and the lifecycle refuses `rework` from IMPLEMENT (`lifecycle.py` line 66). The `verifier`, `review` and
     `closure` callers (lines 522, 527 and 554) keep the transition, so a wrong stage still raises. Everything
     else in `_rework` is unchanged: the rejection count, the recorded finding with `source: "producer"`, and
     `attempt-budget-exhausted` → `failure` at the limit (line 590).
   - The next `launch` runs the PRODUCER again, exactly as after a VERIFIER rejection: stage IMPLEMENT, outcome `rework`.
     The recorded finding reaches it through the work context's `history.findings`.
   - **Counts:** a no-change rework leaves `implement_cycles` and the lifecycle version unchanged. The lifecycle
     `rework` transition adds one to each, but this path makes no transition.
   - **Old records:** the `_cycles` fallback for records without stored counts (lines 847-862) assumes every rejection
     had a VERIFY. Records written after this change always store both counts, so the fallback is never used for them.
6. **Limit stated in the module docstring of `real_worker.py` (line 1):** the current work item contract has no
   no-repository-change execution mode, so every PRODUCER result must change the repository's tree.
7. **Existing tests that change: exactly six, all in `tests/invocation_runtime/test_runtime.py`.** These are exactly
   the tests that fail when the rule is applied to `a632147`. Each fake gains `tree`, and one PRODUCER commits a real
   file:
   - `test_real_worker_retries_a_failed_process_and_records_next_eligible_event`: its `Source` (line 59) gains
     `def tree(self, _, revision): return "1" * 40`.
   - The three `class Source: pass` fakes (lines 89, 118 and 150: the authority-block, exponential-retry and cancel
     tests) each become `class Source:` with `def revision(self, _): return "0" * 40` and
     `def tree(self, _, revision): return "1" * 40`.
   - `_preparing_worker`'s `Source` (lines 536-537), used by
     `test_the_producer_starts_at_the_prepared_revision_and_publication_is_reported`. Its `revision` becomes, exactly:
     ```python
     calls = 0
     def revision(self, _):
         Source.calls += 1
         return "c" * 40 if Source.calls == 1 else "a" * 40
     def tree(self, _, revision): return f"tree-of-{revision}"
     ```
     `Source` is defined inside `_preparing_worker`, so the count starts at 0 for every call of it.
   - `test_real_worker_returns_only_a_published_independently_read_back_source_candidate` (lines 353-385): its
     `CliWorkerProvider` command `("-c", "pass")` (line 372) becomes
     `("-c", "import pathlib, subprocess; pathlib.Path('change.txt').write_text('c'); subprocess.run(['git', 'add', 'change.txt'], check=True); subprocess.run(['git', 'commit', '-qm', 'c'], check=True)")`,
     so the PRODUCER changes a file.

## 3. Acceptance checks

1. **No-change is refused for all three forms** (`tests/invocation_runtime/test_no_change_candidate.py`, test
   `test_a_revision_with_the_starting_tree_is_no_change`, parametrized with ids `same-sha`, `empty-commit` and
   `commit-then-revert`). Each runs the real path with `GitSourceControl` and a local bare remote, as in
   `test_real_worker_returns_only_a_published_independently_read_back_source_candidate`. The PRODUCER command commits
   nothing; commits with `--allow-empty`; or commits a file and then runs `git revert --no-edit HEAD`. Every case
   builds `RealWorkerProvider` with `journal=JsonlInvocationJournal(tmp_path / "journal.jsonl", time.time)` (as the
   journal tests of `test_runtime.py` do, line 613). In each case:
   - the kind is `no-change`, the candidate is `None`, and the one finding starts with `no-change-candidate:`;
   - no `candidate/...` branch exists on the remote;
   - the journal has no `publication-started` record for the correlation, and exactly one `invocation-outcome` record
     with kind `no-change`, candidate `null` and that one finding;
   - `read_back` (which, with a journal, answers only from the journal) returns the same outcome.
   Separately, test `test_a_handover_revision_with_the_starting_tree_is_never_handed_over` (same file): a recording fake
   handover whose `revision` and `tree` answer the starting values gives kind `no-change`, and `hand_over` and
   `publish_intake` are never called. It is not one of M1's failing cases.
2. **A real change is still admitted** (same file, test `test_a_revision_with_a_different_tree_is_admitted`): a commit
   that adds a file gives kind `success`, with that commit as the candidate and its branch on the remote.
3. **The intake refuses the starting tree** (`tests/invocation_runtime/test_git_source_control.py`, after line 446, using
   the existing `handover` fixture): test `test_hand_over_refuses_a_candidate_with_the_starting_tree`, parametrized
   with ids `same-sha`, `empty-commit` and `commit-then-revert`, each made from `handover.base` in the worker's
   workspace. `hand_over` raises `CandidateUnavailable` matching `"candidate tree equals the starting revision's tree"`.
4. **No VERIFIER attempt is used** (`tests/execution_coordination/test_factory_coordinator.py`, test
   `test_no_change_producer_result_reworks_without_a_verifier`). A subclass of `ScriptedWorker` (line 50) lets a
   PRODUCER step return `WorkerOutcome("no-change", None, findings=(...))`.
   - After the first and the second no-change the record is at stage IMPLEMENT, with outcome `rework`, `rejections` 1, 2, and one finding
     per no-change whose `source` is `producer`. `implement_cycles` is 1 and `verify_cycles` is 0 after each (the
     first PRODUCER launch sets `implement_cycles` to 1, line 412), the lifecycle version equals the version before the
     first launch, and `candidate` is `None`.
   - No VERIFIER invocation was started.
   - The next `launch` dispatches the PRODUCER.
   - With `maximum_attempts` 3, a third `no-change` ends in `failure` with `hold_reason` `attempt-budget-exhausted`.
5. **A VERIFIER rejection still transitions** (same file): the existing tests
   `test_check1_a_slot_is_a_work_item_kept_from_producer_through_verifier_and_rework` and
   `test_check8_cycle_counts_change_only_with_recorded_transitions` pass unchanged.
6. **Mutations, run exactly by the VERIFIER** (each with `PYTHONDONTWRITEBYTECODE=1`; revert after each):
   - **M1:** in `_produce`, compare commit ids instead of trees: `starting_sha = reader.revision(workspace.path)` and
     `if revision == starting_sha:`. Then
     `python3 -m pytest -q tests/invocation_runtime/test_no_change_candidate.py` must fail exactly the `empty-commit`
     and `commit-then-revert` cases. Revert, and all must pass.
   - **M2:** in `hand_over`, delete the tree-equality refusal (keep the ancestor check). Then
     `python3 -m pytest -q tests/invocation_runtime/test_git_source_control.py -k test_hand_over_refuses_a_candidate_with_the_starting_tree`
     must fail all three cases. Revert, and they must pass.
   - **M3:** in `_rework`, restore line 587 to `reworked = transition(state, state.version, "rework")`. Then
     `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py -k test_no_change_producer_result_reworks_without_a_verifier`
     must fail. Revert, and it must pass.
   - **M4:** in `_produce`, move the no-change check (the `if` and its body) to just after the `publication-started`
     append. Then `python3 -m pytest -q tests/invocation_runtime/test_no_change_candidate.py -k test_a_revision_with_the_starting_tree_is_no_change`
     must fail all three cases. Revert, and they must pass.
   - **M5:** in `_rework`, make line 587 `reworked = state` for every source. Then
     `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py -k "test_check1_a_slot_is_a_work_item_kept_from_producer_through_verifier_and_rework or test_check8_cycle_counts_change_only_with_recorded_transitions"`
     must fail both. Revert, and they must pass.
7. **The suite stays green:** the regression gate's own run at the candidate (as the worker) has no failed and no error
   test case, and `tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

A prototype of 2.1-2.5 and 2.7, with checks 1 (without a handover), 2, 3 and 4 (final state only), on `a632147` (not the candidate; for
the REVIEWER and PRODUCER only): `manual/path-to-done/no-change/prototype-rev5-on-a632147.diff`, sha256
`dc3ccd1a…0726c`. With it, `tests/invocation_runtime`, `tests/composition` and `tests/execution_coordination` gave
932 passed, and the architecture fitness check passed. M1 failed exactly `empty-commit` and `commit-then-revert`, M2
failed all three hand-over cases, M3 failed the coordinator test, M4 (with the journal of check 1) failed all three
refusal cases, M5 failed both named tests (and four others), and each passed when reverted.

## 4. Review record

**R2 revision 1 (2026-10-09).** Re-issue of revision 5 against main `bc9a9d8` (see Re-issue above). Changed: label,
identity, status, starting revision, one fixed decision, and the `factory_coordinator.py` line numbers (408, 493,
518/523/550, 563, 570, 573 at `a632147` are 412, 497, 522/527/554, 580, 587, 590 at `bc9a9d8`). The requirement,
scope, checks and mutations are unchanged. Line numbers of the other scope files are unchanged (no diff since
`a632147`).

**Revision 5 (2026-10-08).** Follow-up REVIEWER of `7822e15` (FAIL; R1-R7 fixed except R6 in part; S1-S5). All cited
lines were confirmed at `a632147`, and the six test corrections are exactly the failing set.
- Check 1 requires a journal and asserts the journal's records and `read_back` from it; M4 moves the check after the
  `publication-started` append and must fail check 1 (S1, R6).
- The fake-handover case is its own named test (S2).
- Check 4 states the counts exactly (S3).
- Check 5 names its tests; M5 proves them (S4).
- 2.4 says a backstop refusal is a custody refusal, as today (S5).
- Final check of `1ad017e`: PASS, with two low wording corrections applied (the prototype covers check 4's final
  state only; "after the first and the second no-change").

**Revision 4 (2026-10-08).** REVIEWER of `ffdee2b` against main `a632147` (FAIL; R1-R7), and a Founder decision.
- Founder 2026-10-08: "changed" means a different git tree, checked in `_produce` and in `hand_over`, with tests for
  the same commit, an empty commit and commit-then-revert (refused) and a real change (accepted) (R2).
- The packet is rebased on `a632147`. MAIN-GREEN already fixed `test_sandbox_run_profile.py` line 357, so that file
  leaves scope. With the tree rule, exactly six tests in `test_runtime.py` change (R1).
- `GitIntakeHandover` is `IntakeSourceControl` (R3). Line numbers are at `a632147` (R4).
- `_rework` skips the transition only for `source == "producer"` (R5).
- Check 1's remote and intake checks apply to the git set-up; the fake handover asserts no hand-over (R6).
- `_preparing_worker`'s fake is given exactly (R7).
- New: M3, check 5, and the regression gate in excluded_scope.

**Revision 3 (2026-10-06).** Follow-up check of `6f32264` (FAIL): two more existing tests expect success from a
PRODUCER that never commits. The main session then proved the full list by running the rule on a copy of main. Exactly
six tests change (2.6), including one already failing on main since WORKSPACE-FOLDER-NAMES. With the corrections, they
pass.

**Revision 2 (2026-10-06).** REVIEWER of `d8a3fb0` (FAIL, 7 findings):
- the `test_runtime.py` fakes gain `revision`, with the file in scope;
- the starting SHA is read inside the `try:`, from the workspace only, in every case;
- the exact place of the check;
- the `ScriptedWorker` subclass;
- the counts asserted;
- the old-record fallback stated;
- the check 1 fakes named.

**Revision 1 (2026-10-06).** First draft, from the Founder's decisions of 2026-10-06, after work item `3d4e1215`
(stopped, version 3).

A lesson for later, outside this scope (Founder 2026-10-06): a stage transition must prove the stage's output
contract, not only that the worker process exited successfully.
