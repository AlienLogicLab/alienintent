# Work unit: candidate read failures are infrastructure (CUSTODY-READ-INFRASTRUCTURE-RETRY)

**Label:** `CUSTODY-READ-INFRASTRUCTURE-RETRY` (a document label; permanent id `9a38215c-54b8-4e01-926e-cb661edca88a`).
**Status:** Revision 1, 2026-10-11. Registered as work item 9a38215c-54b8-4e01-926e-cb661edca88a.
**Authority:** the Founder's explicit bounded authorization (decisions section 48 and its addendum, quoted in
`fixed_decisions`); released by `work authorize` with those words and one bootstrap `work launch`.
**Starting revision:** main `fb45106`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "9a38215c-54b8-4e01-926e-cb661edca88a",
 "version": "revision-1",
 "intent": "\"Cannot read the candidate right now\" is not \"candidate custody is invalid\": a transient inability of the VERIFIER or CLOSURE to read the exact candidate (the remote holding it cannot be asked) is a typed infrastructure outcome, `candidate-unreadable`, that keeps the stage on the same candidate, retries at most VERIFIER_RETRY_LIMIT times in a row and then holds as typed infrastructure, never an authority hold or a Founder decision; a remote that answers without the exact candidate, an intake not holding it, a digest mismatch or a malformed locator still fail closed as custody refusals.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-11 (decisions section 48, the authorization of this item): I authorize one bounded CUSTODY-READ-INFRASTRUCTURE-RETRY Work Item to modify `src/alienintent/invocation_runtime/real_worker.py`, directly related custody-read/containment code in `src/alienintent/invocation_runtime/`, and their corresponding tests, solely to ensure that transient inability to read the exact candidate is treated as retryable infrastructure failure rather than an authority/custody judgment or Founder escalation. The exact candidate must be preserved; retries must be bounded; retry exhaustion must produce a typed infrastructure hold; genuine custody violations must continue to fail closed. This authorization grants no broader invocation-runtime authority and applies only to this Work Item.",
  "Founder 2026-10-11 (decisions section 48, addendum): the authorization extends narrowly to execution_coordination/ports/worker_provider.py (the typed candidate-read infrastructure outcome) and execution_coordination/application/factory_coordinator.py (mapping it into the bounded retry -> typed infrastructure-hold path), plus directly corresponding tests; nothing else in execution_coordination.",
  "Founder 2026-10-11 (decisions section 48): required proof: transient custody read failure -> same candidate, bounded retry, no Founder escalation; failure then recovery -> normal VERIFY/CLOSURE continuation; retry exhaustion -> typed infrastructure hold; genuine wrong/missing candidate identity -> fail closed as custody violation; no fallback to stale or unverified candidate state; no weakening of containment.",
  "Founder 2026-10-11 (decisions section 44): \"Infrastructure failure is not an owner decision.\"",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-10 (decisions section 28): the targeted test set is part of the Work Item's proof contract."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/domain/runtime.py",
  "tests/composition/test_bounded_routine_launch.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/invocation_runtime/test_git_source_control.py"
 ],
 "excluded_scope": [
  "containment's answer when the plan authority cannot be read (pinned by the protected tests/execution_coordination/test_containment_wiring.py; deferred)",
  "every other path of src/alienintent/execution_coordination/ and every protected path"
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
  "acceptance checks 1-4 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "no test id collected at the starting revision is missing at the candidate (acceptance check 3)",
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/custody-read-infrastructure-retry.diff (sha256 11de161059780c57a238abbb799a0f769db18d8ece860fa4f71149be7440a01a), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "containment's answer when both the local plan read and a fresh fetch fail (deferred)",
  "`RealWorkerProvider.verify()` (no lifecycle caller) and the legacy `_close` without a closure hook",
  "an intake whose HEAD exists but whose objects or refs were damaged from outside (still retried as unreadable; deferred)"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/custody-read-infrastructure-retry.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/custody-read-infrastructure-retry.diff is absent from the context package, its text's sha256 is not 11de161059780c57a238abbb799a0f769db18d8ece860fa4f71149be7440a01a, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

When the VERIFIER or CLOSURE cannot read the exact candidate because the remote holding it cannot be asked, the
runtime answers a custody refusal: an authority block and a Founder decision. That makes a transient network failure an
owner decision (decisions sections 44, 46, 48).

## 2. The change: exactly the referenced prototype diff at `fb45106`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/custody-read-infrastructure-retry.diff`; that entry's `text` field
  holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `11de161059780c57a238abbb799a0f769db18d8ece860fa4f71149be7440a01a` (26,954 bytes, 8 files, unified diff, `git apply` format).
- **Baseline:** main `fb45106`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 8 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `11de161059780c57a238abbb799a0f769db18d8ece860fa4f71149be7440a01a`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. `invocation_runtime/domain/runtime.py`: `CandidateUnreadable(CandidateUnavailable)`, "the candidate could not be
   read right now".
2. `invocation_runtime/adapters/git_source_control.py`: raised only where the remote holding the candidate cannot be
   asked (`retrieve_for_verification`: `ls-remote`, `clone`; `IntakeSourceControl.candidate_clone`: the packets-remote
   `ls-remote`, after checking locally that the intake exists). Every custody check stays `CandidateUnavailable`.
3. `invocation_runtime/application/real_worker.py`: the VERIFIER and CLOSURE answer `candidate-unreadable` for it.
4. `execution_coordination/ports/worker_provider.py`: `CANDIDATE_UNREADABLE`, `CANDIDATE_READ_INFRASTRUCTURE`.
   `execution_coordination/application/factory_coordinator.py`: the VERIFIER (counter `verifier_custody_retries`) and
   CLOSURE (`closure_infrastructure_retries`) map it into the bounded retry -> INFRASTRUCTURE_HOLD path.
5. Tests: adapter classification (unreachable remote, clone failure, missing branch, branch elsewhere, worker path,
   missing intake), coordinator retry/exhaustion/refusal, and end to end through the runtime
   (`tests/composition/test_bounded_routine_launch.py`: VERIFIER then CLOSURE unreadable once and landing; exhaustion
   held as infrastructure; a custody refusal still failing closed).

## 3. Acceptance checks

1. The targeted proof set, the block below, passes; the protected `tests/execution_coordination/test_containment_wiring.py`
   passes unmodified.
2. `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.
3. **No test id disappears**: `python3 -m pytest --collect-only -q tests` at the starting revision and at the candidate;
   every id collected at the starting revision is collected at the candidate (collection only; nothing runs).
4. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-proof
{"targeted_tests": ["tests/invocation_runtime/test_git_source_control.py", "tests/execution_coordination/test_factory_coordinator.py", "tests/composition/test_bounded_routine_launch.py", "tests/invocation_runtime/test_runtime.py", "tests/execution_coordination/test_containment_wiring.py", "tests/composition/test_worker_launch.py", "tests/composition/test_work_registry.py", "tests/composition/test_lifecycle_capstone.py", "tests/control_plane/test_cli.py"]}
```

```json alienintent-mutations
[
 {
  "name": "an unreachable remote is a custody refusal at retrieval",
  "path": "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "edits": [
   {
    "old": "            raise CandidateUnreadable(\"the remote holding the candidate cannot be read\") from None",
    "new": "            raise CandidateUnavailable(\"the remote holding the candidate cannot be read\") from None"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_git_source_control.py::test_retrieval_from_a_remote_that_cannot_be_read_is_unreadable_never_a_custody_judgment"
  ]
 },
 {
  "name": "an unreachable packets remote is a custody refusal for a worker clone",
  "path": "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "edits": [
   {
    "old": "            raise CandidateUnreadable(\"the packets remote holding the candidate cannot be read\") from None",
    "new": "            raise CandidateUnavailable(\"the packets remote holding the candidate cannot be read\") from None"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_git_source_control.py::test_a_worker_clone_of_a_candidate_whose_remote_cannot_be_read_is_unreadable_and_a_missing_one_a_refusal"
  ]
 },
 {
  "name": "a remote that answers without the candidate is retried as infrastructure",
  "path": "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "edits": [
   {
    "old": "        if not advertised or advertised.split()[0] != revision:\n            raise CandidateUnavailable(\"candidate revision is not retrievable for verifier\")\n        try:\n            self._git(\"clone\"",
    "new": "        if not advertised or advertised.split()[0] != revision:\n            raise CandidateUnreadable(\"candidate revision is not retrievable for verifier\")\n        try:\n            self._git(\"clone\""
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_git_source_control.py::test_retrieval_from_a_remote_that_answers_without_the_exact_candidate_is_a_custody_refusal[branch-missing]"
  ]
 },
 {
  "name": "the VERIFIER calls an unreadable candidate a custody refusal",
  "path": "src/alienintent/invocation_runtime/application/real_worker.py",
  "edits": [
   {
    "old": "            except CandidateUnreadable:  # cannot read it right now: infrastructure, never a custody judgment\n                return WorkerOutcome(CANDIDATE_UNREADABLE)\n",
    "new": ""
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_that_cannot_be_read_right_now_is_retried_at_verify_and_closure_and_lands",
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_unreadable_past_the_retries_holds_as_infrastructure_never_for_the_founder"
  ]
 },
 {
  "name": "CLOSURE calls an unreadable candidate missing receipts",
  "path": "src/alienintent/invocation_runtime/application/real_worker.py",
  "edits": [
   {
    "old": "        except CandidateUnreadable:  # cannot read it right now: infrastructure, never a custody judgment\n            return WorkerOutcome(CANDIDATE_UNREADABLE)\n",
    "new": ""
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_that_cannot_be_read_right_now_is_retried_at_verify_and_closure_and_lands"
  ]
 },
 {
  "name": "the coordinator does not retry a VERIFIER custody read",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if outcome.kind in CANDIDATE_READ_INFRASTRUCTURE:  # same candidate, retried, then typed infrastructure\n",
    "new": "            if False:\n"
   }
  ],
  "tests": [
   "tests/execution_coordination/test_factory_coordinator.py::test_a_candidate_unreadable_past_the_retries_holds_as_infrastructure_and_a_custody_refusal_still_fails_closed",
   "tests/execution_coordination/test_factory_coordinator.py::test_a_verifier_that_cannot_read_the_candidate_retries_on_the_same_candidate_with_no_founder_decision"
  ]
 },
 {
  "name": "the coordinator does not retry a CLOSURE custody read",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "        if outcome.kind in CANDIDATE_READ_INFRASTRUCTURE:  # CLOSURE could not read the candidate: same candidate, retried\n",
    "new": "        if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_that_cannot_be_read_right_now_is_retried_at_verify_and_closure_and_lands"
  ]
 },
 {
  "name": "the VERIFIER custody-read count is not carried",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "           \"verifier_custody_retries\")",
    "new": "           )"
   }
  ],
  "tests": [
   "tests/execution_coordination/test_factory_coordinator.py::test_a_candidate_unreadable_past_the_retries_holds_as_infrastructure_and_a_custody_refusal_still_fails_closed"
  ]
 },
 {
  "name": "a missing intake is retried as unreadable",
  "path": "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "edits": [
   {
    "old": "        if not (self.intake / \"HEAD\").is_file():  # no intake holds no candidate: a custody refusal, decided locally\n",
    "new": "        if False:\n"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_git_source_control.py::test_a_worker_clone_from_an_intake_that_is_gone_fails_closed_never_retried_as_unreadable"
  ]
 },
 {
  "name": "a clone failure after the remote answered is a custody refusal",
  "path": "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "edits": [
   {
    "old": "            raise CandidateUnreadable(\"the remote holding the candidate cannot be cloned\") from None",
    "new": "            raise CandidateUnavailable(\"the remote holding the candidate cannot be cloned\") from None"
   }
  ],
  "tests": [
   "tests/invocation_runtime/test_git_source_control.py::test_a_clone_that_fails_after_the_remote_answered_is_unreadable"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `fb45106`. Built test-first; targeted set 1082 passed; 0 test ids
missing against main; fitness passes; the 10 mutations each fail their named tests and pass when
restored. Fresh review found a missing intake retried as unreadable (now a custody refusal) and an untested clone
branch (now tested); a containment change was withdrawn because a protected test pins containment's answer.
