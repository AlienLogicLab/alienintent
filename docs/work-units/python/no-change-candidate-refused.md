# Work unit: a PRODUCER that changes nothing does not produce a candidate

**Label:** `NO-CHANGE-CANDIDATE-REFUSED` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 3, 2026-10-06, for independent review. Not registered, not approved, not assessed, not released.
**Position on the path:** a factory repair that must land before BOUNDED-ROUTINE-LAUNCH is retried. Work item
`3d4e1215-c293-42d9-a112-57eabc289eed` was stopped (`cancelled-by-operator`, version 3). Its PRODUCER returned the
starting revision `bceea00` unchanged, and the factory admitted it as a successful PRODUCER result with a candidate,
then advanced the item to VERIFY.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-3",
 "intent": "When a PRODUCER's process succeeds but its claimed revision equals the starting revision, the factory publishes no candidate. It records a typed no-change PRODUCER result with a finding, and the work item stays in IMPLEMENT as a rework within its attempt budget. No VERIFIER attempt is used. A genuine descendant commit is admitted as today.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-06: a PRODUCER assigned to IMPLEMENT must produce a repository change. If it returns the starting revision unchanged, implementation did not occur.",
  "Founder 2026-10-06: candidate == starting revision -> typed no-change PRODUCER result -> finding -> _rework -> remains IMPLEMENT -> no VERIFIER attempt consumed.",
  "Founder 2026-10-06: the current work item contract has no authorized no-repository-change execution mode. This repair therefore refuses unchanged candidates. Introducing such a mode requires a separate contract and schema decision and is out of scope.",
  "Founder 2026-10-06: the rejection test is discriminating: restoring the ancestor-only check makes it fail."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "tests/invocation_runtime/test_no_change_candidate.py",
  "tests/invocation_runtime/test_git_source_control.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/composition/test_sandbox_run_profile.py"
 ],
 "excluded_scope": [
  "any contract or schema field that allows a no-change work item",
  "the lifecycle transition rules in execution_coordination/domain/lifecycle.py",
  "the VERIFIER, CLOSURE and Landing Authority paths",
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
  "acceptance checks 1-6 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1 and M2 of section 3 exactly and records that each makes its named test fail and that reverting makes it pass"
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
  "scope outside the authorized files"
 ]
}
```

## 1. Why

`RealWorkerProvider._produce` (`real_worker.py`, about lines 483-503) treats a successful process as a successful
PRODUCER result. It then publishes whatever revision the workspace's HEAD names. The only check on that revision is
`GitIntakeHandover.hand_over` (`git_source_control.py` line 291), which requires the claimed revision to descend from
the starting revision. A revision descends from itself, so an unchanged workspace passes.

Work item `3d4e1215` showed the effect. The intake ref `refs/intake/launch-3d4e1215-…-0`, the bundle head and the
candidate branch all name `bceea00`, which is the release baseline. Yet the coordinator recorded `success` and
advanced to VERIFY (`factory_coordinator.py` lines 492-497).

## 2. The change

1. **One constant.** `NO_CHANGE = "no-change"` in `execution_coordination/ports/worker_provider.py`, next to
   `MISSING_TERMINAL_RESULT`.
2. **The PRODUCER refuses an unchanged revision** (`real_worker.py`, `_produce`). This is the one place the rule is
   decided, before both publication paths.
   - **The starting SHA** has one source in every case: the workspace's own revision, read with
     `(self._source if self._handover is None else self._handover).revision(workspace.path)`. This read is the first
     statement inside the existing `try:` after `allocate` (`real_worker.py` line 477), before the session runs. The
     workspace is checked out at the starting revision either way, and a raise there is cleaned up by the existing
     `finally`. A prepared value is never compared directly.
   - **After a successful process,** right after `revision = ...` (line 494) and before the `publication-started`
     append (line 495), when `revision == <starting SHA>`:
     - The outcome is `WorkerOutcome(NO_CHANGE, None, findings=(f"no-change-candidate:{revision}: the PRODUCER returned the starting revision unchanged; IMPLEMENT requires a repository change",))`.
     - Nothing is handed over, nothing is published, and no `publication-started` record is written.
     - The outcome is journaled and read back like any other PRODUCER result, through the existing
       `invocation-outcome` record with `candidate: None` and the finding.
     - The workspace is cleaned up as for any non-success result.
   - `correlated_outcome` (`real_worker.py` line 67) already admits a PRODUCER kind other than `success` only with no
     candidate. So no change is needed there.
3. **Defence at the intake** (`git_source_control.py`, `hand_over`, line 291). It raises
   `CandidateUnavailable("candidate equals the starting revision")` when `claimed == starting`, before the ancestor
   check.
4. **The coordinator sends it to rework** (`factory_coordinator.py`, `_advance`, PRODUCER branch, line 492).
   - Before the existing `if outcome.kind != "success" or outcome.candidate is None` line, add:
     `if outcome.kind == NO_CHANGE: return self._rework(item, current, prior, invocation, "producer", tuple(outcome.findings))`.
   - In `_rework` (line 563), the item is already at IMPLEMENT, and the lifecycle refuses `rework` from IMPLEMENT
     (`lifecycle.py` line 66). So `_rework` uses `reworked = state if state.stage is LifecycleStage.IMPLEMENT else
     transition(state, state.version, "rework")`. Everything else in `_rework` is unchanged: the rejection count, the
     recorded finding with `source: "producer"`, and `attempt-budget-exhausted` → `failure` at the limit.
   - The next `launch` runs the PRODUCER again, exactly as after a VERIFIER rejection: stage IMPLEMENT, outcome `rework`.
     The recorded finding reaches it through the work context's `history.findings`.
   - **Counts:** a no-change rework leaves `implement_cycles` and the state version unchanged. The lifecycle `rework`
     transition adds one to each, but this path makes no transition.
   - **Old records:** the `_cycles` fallback for records without stored counts (`factory_coordinator.py` lines 847-862)
     assumes every rejection had a VERIFY. Records written after this change always store both counts, so the fallback
     is never used for them.
5. **Limit stated in the module docstring of `real_worker.py`:** the current work item contract has no
   no-repository-change execution mode, so every PRODUCER result must change the repository.
6. **Existing tests that change.** These are exactly the tests that fail when the rule alone is applied. The main
   session ran `tests/invocation_runtime`, `tests/composition` and `tests/execution_coordination` on a copy of main
   `bceea00` with only the rule added: 6 failed and 891 passed. With these six corrections, both files pass (69
   passed).
   - `tests/invocation_runtime/test_runtime.py`, the three `class Source: pass` fakes (lines 89, 118 and 150: the
     authority-block, exponential-retry and cancel tests). Each becomes
     `class Source:` with `def revision(self, _): return "0" * 40`.
   - Same file, the `Source` of `_preparing_worker` (lines 536-537), used by
     `test_the_producer_starts_at_the_prepared_revision_and_publication_is_reported`. Its `revision` counts its calls:
     the first returns `"c" * 40` and later calls return `"a" * 40`.
   - Same file, `test_real_worker_returns_only_a_published_independently_read_back_source_candidate` (lines 353-380).
     Its `CliWorkerProvider` command `("-c", "pass")` becomes
     `("-c", "import subprocess; subprocess.run(['git', 'commit', '--allow-empty', '-qm', 'c'], check=True)")`, so the
     PRODUCER commits.
   - `tests/composition/test_sandbox_run_profile.py` line 357. This test already fails on main `bceea00`, because
     WORKSPACE-FOLDER-NAMES changed folder names. `assert workspace.path.name == "launch:SB-01:0"` becomes
     `== "launch-SB-01-0"`.

## 3. Acceptance checks

1. **No-change is refused** (`tests/invocation_runtime/test_no_change_candidate.py`, test
   `test_unchanged_producer_revision_is_a_no_change_result`). It is parametrized over two set-ups:
   - with a handover: a recording fake handover whose `revision` answers the starting SHA, and which asserts
     `hand_over` and `publish_intake` are never called;
   - without a handover: the existing git source of `test_runtime.py`, with no preparation (`"HEAD"`).

   In each case, a PRODUCER whose process succeeds without committing returns kind `no-change` with exactly the finding text of 2.2. Also:
   - there is no `publication-started` record;
   - no candidate branch exists on the remote, and no `refs/intake/<correlation>` ref exists;
   - `read_back` returns the same `no-change` outcome.
2. **A real change is still admitted** (same file, test `test_descendant_commit_is_admitted`): one new commit gives
   kind `success` with that commit as the candidate.
3. **Intake defence** (`tests/invocation_runtime/test_git_source_control.py`, next to line 446): `hand_over` with
   `claimed == starting` raises `CandidateUnavailable` matching `"candidate equals the starting revision"`. The test is named
   `test_hand_over_refuses_a_candidate_equal_to_the_starting_revision`.
4. **No VERIFIER attempt is used** (`tests/execution_coordination/test_factory_coordinator.py`, test
   `test_no_change_producer_result_reworks_without_a_verifier`). A subclass of `ScriptedWorker` (lines 81-83) lets a
   PRODUCER step return `WorkerOutcome("no-change", None, findings=(...))`.
   - Afterwards the record is at stage IMPLEMENT, with outcome `rework`, `rejections` 1, and one finding whose `source`
     is `producer`. `verify_cycles`, `implement_cycles`, the state version and `candidate` are unchanged.
   - No VERIFIER invocation was started.
   - The next `launch` dispatches the PRODUCER.
   - With `maximum_attempts` 3, a third `no-change` ends in `failure` with `hold_reason` `attempt-budget-exhausted`.
5. **Mutations, run exactly by the pre-check and the VERIFIER:**
   - **M1:** in `src/alienintent/invocation_runtime/application/real_worker.py` `_produce`, replace the no-change
     condition with `False`. Then
     `python3 -m pytest -q tests/invocation_runtime/test_no_change_candidate.py -k test_unchanged_producer_revision_is_a_no_change_result`
     must FAIL. Revert, and it must pass.
   - **M2:** in `src/alienintent/invocation_runtime/adapters/git_source_control.py` `hand_over`, delete the
     `claimed == starting` refusal, leaving only the ancestor check. Then
     `python3 -m pytest -q tests/invocation_runtime/test_git_source_control.py -k test_hand_over_refuses_a_candidate_equal_to_the_starting_revision`
     must FAIL. Revert, and it must pass.
6. **Fitness:** these all pass (no full suite):
   - `python3 -m pytest -q tests/invocation_runtime tests/execution_coordination/test_factory_coordinator.py tests/composition/test_worker_launch.py tests/composition/test_role_binding.py tests/composition/test_sandbox_run_profile.py`
   - `tools/fitness/check_architecture.py --root src/alienintent --check all`

## 4. Review record

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
