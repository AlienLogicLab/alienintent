# Work unit: verification outcome integrity

**Label:** `VERIFICATION-OUTCOME-INTEGRITY` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Revision 1, 2026-10-10. Not registered.
**Authority:** derived from the approved canonical plan revision `28df5c3` (`sha256:415231dcd846671f40bbf24fd6429515592d2d920d4d159d599c9aed9a468dff`), obligation
`VERIFICATION-OUTCOME-INTEGRITY` (P0); released by the control plane (`work release`), no per-item Founder release.
**Starting revision:** main `28df5c3`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "Only an admitted, evidence-backed engineering REJECT returns a Work Item to PRODUCER. Every failure of the verification environment or machinery keeps the exact candidate and retries VERIFY within VERIFIER_RETRY_LIMIT, then a typed hold, never a rejection. Packet mutations are a machine-readable block run by a deterministic control-plane harness; a VERIFIER session REJECT is admitted only when every finding's typed evidence (pytest, reproducer, fitness, text) is independently reproduced on a fresh checkout of the exact candidate; one same-environment control rule decides whether any test result counts against the candidate.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-09 (decisions section 23): only an admitted, evidence-backed engineering REJECT may return a Work Item to PRODUCER; infrastructure failure, malformed verdict, invalid or incomplete verification evidence, or verification-procedure failure preserves the exact candidate and retries VERIFY within bounded policy.",
  "Founder 2026-10-10: a model REJECT is admitted only when every blocking finding has deterministic evidence that the control plane independently reproduces against the exact candidate; existing tests are one evidence type among several.",
  "Founder 2026-10-10: the candidate must not be blamed for a failure of the verification environment or machinery (skips, timeouts, workspace failures, non-assertion failures are not candidate evidence).",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution; VERIFIER adds only acceptance, mutation and finding-specific tests.",
  "Founder 2026-10-09 (decisions section 24): plan revision 28df5c3 is the authority root; this item is the first released through inherited plan authority."
 ],
 "authorized_scope": [
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/domain/diagnostics.py",
  "src/alienintent/invocation_runtime/domain/mutation_spec.py",
  "src/alienintent/invocation_runtime/domain/verdict_admission.py",
  "tests/composition/test_work_registry.py",
  "tests/composition/test_worker_launch.py",
  "tests/invocation_runtime/test_mutation_harness.py",
  "tests/invocation_runtime/test_mutation_spec.py",
  "tests/invocation_runtime/test_verdict_admission.py",
  "tests/invocation_runtime/test_verification_outcome.py"
 ],
 "excluded_scope": [
  "src/alienintent/invocation_runtime/application/regression_gate.py",
  "tools/fitness/",
  "the offline, sandbox and capstone profiles",
  "a supersede command for verdicts recorded before this lands"
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
  "acceptance checks 1-3 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/verification-outcome-integrity.diff (sha256 d693531bc63627ff47063a4c031f9e186e5aeac3acfbdf52e13153f74c684b04), ignoring only `index` lines",
  "the VERIFIER applies every mutation of the `alienintent-mutations` block with a script that reads the JSON (never by typing the edits), and records that each makes its named tests fail and that restoring the file makes them pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "changing the regression gate",
  "a generic evidence framework beyond the four typed forms"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "automatic-on",
 "authority_issuer": "plan-authority:sha256:415231dcd846671f40bbf24fd6429515592d2d920d4d159d599c9aed9a468dff",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md obligation:VERIFICATION-OUTCOME-INTEGRITY",
  "docs/work-units/python/verification-outcome-integrity.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/verification-outcome-integrity.diff is absent from the context package, its text's sha256 is not d693531bc63627ff47063a4c031f9e186e5aeac3acfbdf52e13153f74c684b04, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

On 2026-10-09 a VERIFIER rejected candidate `8fbad98`, which was exactly the reviewed diff, because it copied mutation
M4 by hand without its closing parenthesis; the reject cleared the candidate and sent the item back to PRODUCER. The
factory treated a failure of the verification process as a failure of the candidate. This item makes that impossible:
"Artifact state may change because the artifact failed its evaluation. Artifact state must not change merely because
the evaluation mechanism failed."

## 2. The change: exactly the referenced prototype diff at `28df5c3`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/verification-outcome-integrity.diff`; that entry's
  `text` field holds the exact diff. (The same package the PRODUCER receives at launch; its `work context` command
  re-prints it.)
- **SHA-256 of those bytes (UTF-8):** `d693531bc63627ff47063a4c031f9e186e5aeac3acfbdf52e13153f74c684b04` (137,465 bytes, 13 files, unified diff, `git apply` format).
- **Baseline:** main `28df5c3`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 13 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `d693531bc63627ff47063a4c031f9e186e5aeac3acfbdf52e13153f74c684b04`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

Invariants the diff implements:
1. **Only an admitted REJECT reaches PRODUCER.** The legitimate sources are: a gate finding confirmed by the control
   run, a surviving mutation or a control-confirmed restored-run failure, and a VERIFIER session REJECT whose every
   finding's typed evidence reproduces. Every other VERIFIER outcome is in `VERIFIER_INFRASTRUCTURE`
   (`verification-evidence-invalid`, `mutation-harness-unavailable` added) and goes to `_retry_verifier`: stage VERIFY,
   candidate kept, no rejection counted; after `VERIFIER_RETRY_LIMIT` the typed hold
   `verifier-infrastructure-exhausted:<kind>`.
2. **Mutations by machine.** `invocation_runtime/domain/mutation_spec.py` parses one ```` ```json alienintent-mutations ````
   block of the packet (name, path, edits `{old, new}`, named pytest node ids). `invocation_runtime/application/
   mutation_harness.py` runs each mutation after the regression gate passes and before the VERIFIER session, in its own
   fresh checkout of the exact candidate: every `old` occurs exactly once, all edits applied together, the file must
   compile, named tests run, the file restored byte-exact and the tests run again. Results: KILLED, SURVIVED,
   REVERTED_FAILS, SPEC_INVALID; receipt `mutation-harness:sha256:` binding candidate SHA and spec digest. All killed:
   the table is added to the VERIFIER's instructions, which no longer ask it to apply mutations.
3. **Typed, reproduced evidence for a session REJECT.** `invocation_runtime/domain/verdict_admission.py`: each finding is
   `{"finding", "evidence"}` with evidence `pytest` (node ids), `reproducer` (an ephemeral test file kept outside the
   candidate), `fitness` (a check name) or `text` (contains/absent at a path). Each evidence item is reproduced in its own
   fresh checkout of the exact candidate; the reject is admitted only if every one reproduces (receipt
   `reject-reproduced:sha256:`), otherwise `verification-evidence-invalid` with each refused finding and why.
4. **One same-environment control rule** (`against_candidate`): a test that exists at the starting revision counts
   against the candidate only when it does not pass at the candidate now and passes at the starting revision now; a
   test absent there counts only when it fails on an assertion at the candidate now; a skip at the candidate is never
   evidence. Every test the control plane judges runs through one method, `MutationHarness.observe(revision, node)`:
   one node, alone, in a fresh checkout of that exact revision, strict junit reading; absence is proven (git listing
   or that node's clean run), never inferred; anything else is no result. The mutated run is the one batch run. Applied to gate `regression:` and `new-test-fails:` findings
   (in `real_worker.py`; the gate itself is unchanged), restored runs, and `pytest` evidence; fitness evidence counts
   only when the check reports a violation at the candidate and passes at the starting revision now; a reproducer counts
   only on an assertion failure.
5. **Failures of the machinery are typed outcomes.** Harness timeouts, checkout/workspace failures, unreadable junit
   and OS errors become `mutation-harness-unavailable` with the cause; malformed specs or evidence are refused at parse
   time (including text that does not encode as UTF-8).

What each file carries:

| File | Change |
| --- | --- |
| `src/alienintent/invocation_runtime/domain/mutation_spec.py` (new) | pure parser of the `alienintent-mutations` block; spec digest |
| `src/alienintent/invocation_runtime/domain/verdict_admission.py` (new) | pure typed-evidence parser and admission rule; reject receipt |
| `src/alienintent/invocation_runtime/application/mutation_harness.py` (new) | the deterministic harness: mutations, evidence reproduction, control runs, `against_candidate` |
| `src/alienintent/invocation_runtime/application/real_worker.py` | `_evaluate`: gate-finding control, `_mutate` before the session, `_admit` for a session reject; `HARNESS_FAILURES` |
| `src/alienintent/execution_coordination/ports/worker_provider.py` | two kinds added to `VERIFIER_INFRASTRUCTURE` |
| `src/alienintent/invocation_runtime/domain/diagnostics.py` | causes for the two kinds |
| `src/alienintent/composition/work_registry.py` | harness composition (checkouts, worker-user file I/O, revision checkout), packet mutations, VERIFIER instructions |
| `tests/composition/test_worker_launch.py`, `tests/composition/test_work_registry.py` and the 4 new test files | the tests named in section 3 |

## 3. Acceptance checks

1. **The rules**: `tests/invocation_runtime/test_mutation_spec.py`, `tests/invocation_runtime/test_verdict_admission.py`.
2. **The harness and the outcomes**: `tests/invocation_runtime/test_mutation_harness.py`,
   `tests/invocation_runtime/test_verification_outcome.py`, `tests/composition/test_worker_launch.py`,
   `tests/composition/test_work_registry.py`; the existing `tests/execution_coordination/test_factory_coordinator.py`,
   `tests/invocation_runtime/test_real_worker_outcome.py` and `tests/invocation_runtime/test_regression_gate.py` pass
   unchanged.
3. **Mutations**: the block below. The VERIFIER applies each with a script that reads this JSON, never by typing an
   edit by hand. The block is the lines between the line that is exactly ```` ```json alienintent-mutations ```` and the
   next line that is exactly ```` ``` ````. For each mutation: each `old` must occur exactly once in `path`; apply all
   its edits together; run `python3 -m pytest -q -p no:cacheprovider <node id> ...` with every named node id passed as
   its own argument (an argv list, never a shell string: ids hold spaces, brackets, colons and backslashes); every
   named test must fail; restore the file byte-exact; run them again: every one must pass.

```json alienintent-mutations
[
 {
  "name": "session reject bypasses admission",
  "path": "src/alienintent/invocation_runtime/application/real_worker.py",
  "edits": [
   {
    "old": "    typed = admission is not None and document.get(\"verdict\") == \"reject\"",
    "new": "    typed = False"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[reproduce-failure0]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[reproduce-failure1]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[reproduce-failure2]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_reproduction_that_cannot_run_is_no_result_never_a_rejection"
  ]
 },
 {
  "name": "unreproduced evidence admitted",
  "path": "src/alienintent/invocation_runtime/domain/verdict_admission.py",
  "edits": [
   {
    "old": "        elif reproduction is None or not reproduction.reproduced:",
    "new": "        elif False:"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_verdict_admission.py::test_a_reject_is_admitted_only_when_every_finding_reproduces",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_session_reject_that_is_not_reproduced_is_not_admitted[findings1-reproduced1]"
  ]
 },
 {
  "name": "harness not run before the session",
  "path": "src/alienintent/invocation_runtime/application/real_worker.py",
  "edits": [
   {
    "old": "                if self._mutation_harness is not None:\n",
    "new": "                if False:\n"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_that_cannot_judge_keeps_the_candidate_for_a_fresh_verify[spec0-None-verification-evidence-invalid]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_that_cannot_judge_keeps_the_candidate_for_a_fresh_verify[spec1-mutated1-verification-evidence-invalid]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_that_cannot_judge_keeps_the_candidate_for_a_fresh_verify[spec2-mutated2-mutation-harness-unavailable]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[mutations-failure0]"
  ]
 },
 {
  "name": "surviving mutation counted as killed",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "            return result(SURVIVED,",
    "new": "            return result(KILLED,"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_surviving_mutation_and_a_failing_reverted_run_are_the_candidates"
  ]
 },
 {
  "name": "evidence-invalid is not a VERIFY retry",
  "path": "src/alienintent/execution_coordination/ports/worker_provider.py",
  "edits": [
   {
    "old": "\"feature-regressions-missing\", \"verification-evidence-invalid\",",
    "new": "\"feature-regressions-missing\","
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_that_cannot_judge_keeps_the_candidate_for_a_fresh_verify[spec0-None-verification-evidence-invalid]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_that_cannot_judge_keeps_the_candidate_for_a_fresh_verify[spec1-mutated1-verification-evidence-invalid]"
  ]
 },
 {
  "name": "a skip at the candidate counts against it",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "    if at_candidate == \"skipped\":\n",
    "new": "    if False:\n"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_test_skipped_at_the_candidate_is_never_against_it"
  ]
 },
 {
  "name": "asserting at both revisions counts",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "    return at_candidate != \"passed\" and at_start == \"passed\"",
    "new": "    return at_candidate == \"asserted\" or (at_candidate != \"passed\" and at_start == \"passed\")"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_test_absent_at_the_start_does_not_hide_one_that_exists",
   "tests/invocation_runtime/test_mutation_harness.py::test_an_assertion_failing_at_both_revisions_is_never_the_candidates[gate regression]",
   "tests/invocation_runtime/test_mutation_harness.py::test_an_assertion_failing_at_both_revisions_is_never_the_candidates[pytest evidence]",
   "tests/invocation_runtime/test_mutation_harness.py::test_an_assertion_failing_at_both_revisions_is_never_the_candidates[restored run]"
  ]
 },
 {
  "name": "a new test counts on any failure",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "        return at_candidate == \"asserted\"\n",
    "new": "        return at_candidate != \"passed\"\n"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_new_test_counts_only_when_it_fails_on_an_assertion[def test_new():\\n    raise ConnectionError\\n-stands0]"
  ]
 },
 {
  "name": "fitness ignores the starting revision",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "            return Reproduction(started == 0,",
    "new": "            return Reproduction(True,"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_fitness_violation_reproduces_only_when_the_starting_revision_passes[base_files0-False]"
  ]
 },
 {
  "name": "a collection error reads as no error",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "        if collection:\n            raise SuiteUnrunnable(",
    "new": "        if False:\n            raise SuiteUnrunnable("
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_collection_error_at_the_starting_revision_is_no_result_never_an_absent_test[gate regression]",
   "tests/invocation_runtime/test_mutation_harness.py::test_a_collection_error_at_the_starting_revision_is_no_result_never_an_absent_test[pytest evidence]",
   "tests/invocation_runtime/test_mutation_harness.py::test_a_collection_error_at_the_starting_revision_is_no_result_never_an_absent_test[restored run]"
  ]
 },
 {
  "name": "harness timeout or workspace failure escapes",
  "path": "src/alienintent/invocation_runtime/application/real_worker.py",
  "edits": [
   {
    "old": "HARNESS_FAILURES = (SuiteUnrunnable, CandidateUnavailable, OSError, subprocess.TimeoutExpired)",
    "new": "HARNESS_FAILURES = (SuiteUnrunnable,)"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[mutations-failure0]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[mutations-failure1]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[mutations-failure2]",
   "tests/invocation_runtime/test_verification_outcome.py::test_a_harness_timeout_or_workspace_failure_is_unavailable_with_its_cause[reproduce-failure0]"
  ]
 },
 {
  "name": "any failure counts as an assertion",
  "path": "src/alienintent/invocation_runtime/application/mutation_harness.py",
  "edits": [
   {
    "old": "failure.get(\"type\", \"AssertionError\") == \"AssertionError\" and _ASSERTION.match(failure.get(\"message\", \"\"))",
    "new": "True"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_mutation_harness.py::test_a_new_test_counts_only_when_it_fails_on_an_assertion[def test_new():\\n    raise ConnectionError\\n-stands0]",
   "tests/invocation_runtime/test_mutation_harness.py::test_a_reproducer_reproduces_only_with_an_assertion_failure[raised-False]"
  ]
 },
 {
  "name": "a git failure reads as absent",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "    if listed.returncode != 0:\n        raise OSError(",
    "new": "    if False:\n        raise OSError("
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_path_is_absent_at_a_revision_only_when_git_proves_it"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (can defer)
- The offline, sandbox and capstone profiles build the worker without the harness; their string-finding rejects are
  unchanged. The registry profile (the real factory) always has the gate, the harness and admission.
- A mutation that makes the named tests fail to collect counts as killed (the restored run proves they exist and pass).
- A reproducer proves its test fails on an assertion at the candidate, not that it asserts the right thing.
- Without a worker user, harness worktree checkouts holding a reproducer are not cleaned up.
- A parametrize id containing `::`, a dotted test folder, or a regression that only shows in suite order is not
  reproduced when rerun alone: it ends in the typed hold, never a rework.
- This item's own VERIFIER runs on the old code, so it applies the mutations itself (by script, per check 3).
- A node id's path and test name hold no whitespace; only a parametrize id in brackets may (never a line break).

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `28df5c3` (byte copy:
`~/.local/state/alienintent/manual/path-to-done/verification-outcome-integrity/prototype-on-28df5c3.diff`). Built
test-first; 517 targeted tests pass across 17 files; fitness passes; the 13 mutations of check 3 each fail their named
tests and pass when restored (`packet-mutations.log`), plus earlier mutation rounds (`mutations.log`). Real conditions,
real worker user, real candidate `8fbad98`: M4 and C3 killed, malformed specs SPEC_INVALID, true/false evidence told
apart, two ids one absent read per node, a broken reproducer refused (`real-conditions-r4.log`). Reviews: eight fresh
adversarial reviews; each finding fixed test-first at its single source (skips; one checkout per evidence item;
escaping timeouts; assertion-only reproducers; the same-environment control rule and its root; proven absence; one
`observe` choke point with a wiring test). The eighth review: PASS.
