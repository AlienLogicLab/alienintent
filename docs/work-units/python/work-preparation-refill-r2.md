# Work unit: current-main execution baseline (WORK-PREPARATION-REFILL R2)

**Label:** `WORK-PREPARATION-REFILL-R2` (a document label; permanent id `e9d6d1fc-7ad5-4025-8a24-00ab12768e3e`).
**Status:** Revision 1, 2026-10-11. Registered as work item e9d6d1fc-7ad5-4025-8a24-00ab12768e3e.
**Authority:** obligation WORK-PREPARATION-REFILL of the live canonical plan (tip `58b3742`, `sha256:3be660b28ca00d450a0baa195161e9dcfe33ed63b2cbd13da9ca712c556f2324`),
acceptance WPR-A1, plus the Founder's explicit authorization of the canonical-main infrastructure-failure changes in
`execution_coordination/` and `inherited_release.py` (decisions sections 44-45, quoted in `fixed_decisions`). It is
therefore an explicit exception, not plan-derived: released by `work authorize` with those words and one bootstrap
`work launch`; the exception is not carried forward to R3/R4.
**Starting revision:** main `58b3742`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "e9d6d1fc-7ad5-4025-8a24-00ab12768e3e",
 "version": "revision-1",
 "intent": "WPR-A1: every new PRODUCER attempt starts from current canonical main (the default branch fetched from the remote) only after deterministic baseline revalidation at one fetched SHA; work that cannot be revalidated is held baseline-revalidation-required for Work Preparation and Agent Ready, never silently retargeted; the revalidated execution baseline is recorded per attempt and per candidate and is the VERIFIER's, regression gate's and mutation control run's baseline, while the release baseline stays the provenance anchor.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-11 (decisions section 45, the explicit authorization of this item): I authorize WORK-PREPARATION-REFILL R2 to include the bounded canonical-main infrastructure-failure changes in `src/alienintent/execution_coordination/`, `src/alienintent/context_assembly/application/inherited_release.py`, and their directly corresponding tests, solely to ensure that transient canonical-main fetch/read failures preserve Work Item state, retry under bounded infrastructure policy, never fabricate plan-authority failure, and never escalate to the Founder. This authorization does not broaden the WORK-PREPARATION-REFILL obligation generally and applies only to this R2 candidate and the reviewed scope.",
  "Founder 2026-10-11 (decisions section 44): \"Infrastructure failure is not an owner decision.\" A transient canonical-main fetch failure preserves Work Item and candidate state, returns a typed retryable infrastructure outcome, retries under the bounded infrastructure policy and on exhaustion holds as typed infrastructure; it never grants a release from stale state, never proceeds on an unknown tip, never becomes NO_PLAN_AUTHORITY or another authority failure and never escalates to the Founder; CLOSURE still requires live canonical authority before landing.",
  "Founder 2026-10-10 (decisions section 39): \"Never silently retarget an assessed Work Item onto changed code. Revalidate it first.\"",
  "Founder 2026-10-11 (decisions section 43): guard the exact targeted proof set Agent Ready assessed (a machine-readable proof block, never inferred); one fetched canonical-main SHA per revalidation for plan authority, changed paths, reference resolution and the resulting execution baseline; release baseline = provenance anchor, execution baseline = the revalidated main the candidate was built on, used by the regression gate, VERIFIER context, candidate custody and CLOSURE.",
  "Founder 2026-10-11 (decisions section 43, addendum): main == baseline -> proceed; baseline an ancestor of main -> checks, retarget if they pass; anything else -> reprepare/hold. \"Never execute from a revision ahead of the current canonical main merely because canonical main is its ancestor.\"",
  "Founder 2026-10-11 (decisions section 43, addendum 2): the last-fetched-canonical-main fallback is a read-only containment fallback only; it never becomes an execution baseline or an inherited-release authority source.",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-10 (decisions section 28): the targeted test set is part of the Work Item's proof contract."
 ],
 "authorized_scope": [
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/application/inherited_release.py",
  "src/alienintent/context_assembly/application/packet_assessment.py",
  "src/alienintent/context_assembly/application/work_context.py",
  "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "src/alienintent/context_assembly/domain/proof_set.py",
  "src/alienintent/context_assembly/domain/work_context.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/execution_coordination/domain/closure.py",
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "tests/composition/test_bounded_routine_launch.py",
  "tests/composition/test_work_registry.py",
  "tests/composition/test_worker_launch.py",
  "tests/context_assembly/test_baseline_revalidation.py",
  "tests/context_assembly/test_inherited_release.py",
  "tests/context_assembly/test_proof_set.py",
  "tests/context_assembly/test_work_context.py",
  "tests/control_plane/test_cli.py",
  "tests/execution_coordination/test_factory_coordinator.py"
 ],
 "excluded_scope": [
  "every protected path of the canonical plan authority except src/alienintent/execution_coordination/ and src/alienintent/context_assembly/application/inherited_release.py (decisions section 45) and their tests",
  "src/alienintent/context_assembly/application/work_authorization.py (its CONTRACT_UNSATISFIABLE label for an unfetchable main is deferred, decisions section 45)",
  "the PREPARER, Work Preparation service, refill and READY-supply fault (WORK-PREPARATION-REFILL R3-R4)"
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
  "acceptance checks 1-5 pass",
  "WPR-A1 (every new PRODUCER attempt starts from current main only after deterministic baseline revalidation; work that cannot be revalidated goes back through Work Preparation and Agent Ready, never silently retargeted)"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "no test id collected at the starting revision is missing at the candidate (acceptance check 4)",
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/work-preparation-refill-r2.diff (sha256 33b82c165f82b1fd4e973f456e34e276b47a1125db300cbc8e6055cb1557c489), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a diagnostic for a failed execution-baseline record write (deferred; it fails safe)",
  "`work authorize`'s CONTRACT_UNSATISFIABLE label for an unfetchable canonical main (deferred, decisions section 45)",
  "dependency/test-impact analysis beyond scope and proof files (accepted limit, decisions section 43)"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md obligation:WORK-PREPARATION-REFILL",
  "docs/work-units/python/work-preparation-refill-r2.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/work-preparation-refill-r2.diff is absent from the context package, its text's sha256 is not 33b82c165f82b1fd4e973f456e34e276b47a1125db300cbc8e6055cb1557c489, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

A PRODUCER today starts at its release baseline, so a second item released at the same main fails CLOSURE with
base-moved after the first lands, and "current main" is the clone's local branch, which moves only when someone pulls.
This child makes current canonical main the fetched remote branch and revalidates each new PRODUCER attempt against it
(decisions sections 39 and 43).

## 2. The change: exactly the referenced prototype diff at `58b3742`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/work-preparation-refill-r2.diff`; that entry's `text` field
  holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `33b82c165f82b1fd4e973f456e34e276b47a1125db300cbc8e6055cb1557c489` (151,887 bytes, 19 files, unified diff, `git apply` format).
- **Baseline:** main `58b3742`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 19 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `33b82c165f82b1fd4e973f456e34e276b47a1125db300cbc8e6055cb1557c489`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. `composition/work_registry.py`: current canonical main is fetched (`_canonical_main`: fetch, then the remote-tracking
   ref; the same fetch moves local branch `alienintent/canonical-main` so worker clones receive it; it records whether
   that read's fetch failed); inherited release and the dispatch gate check baselines against it (the coordinator
   refreshes it when built); `_revalidate` (one SHA: ancestry, plan authority pinned at it, changed paths, guarded
   paths); `_on_canonical_main`; `protected_paths` falls back to the last fetched main on a fetch failure (read-only
   containment); `_satisfiable` never skips the plan check on an unknown tip; `LaunchPreparation` records the attempt's
   and the candidate's execution baseline, holds `baseline-revalidation-required`, and answers the typed outcome
   `canonical-main-unavailable` when canonical main cannot be fetched; CLOSURE answers `remote-unreadable` (never
   "no plan authority" or "landing-ambiguous") when its landing fetch, its live-authority read or the settlement of a
   journaled order cannot reach canonical main. Fresh fetches happen only where the current tip decides (release,
   PRODUCER revalidation, landing, assessment); the READY snapshot and started items read the last fetched main
   (`_fetched_authority`), which never releases, starts or lands work. Git that cannot answer an ancestry question is
   "unavailable", never "diverged".
2. `context_assembly/domain/baseline_revalidation.py` (with `reference_paths`: `<path> obligation:<label>` guards its
   path, any other reference is kept whole so prose holds) and `proof_set.py` (new, pure).
3. `context_assembly/application/work_context.py`, `domain/work_context.py`: the `execution_baseline` package field;
   VERIFIER/CLOSURE `starting_revision` and diff base from the candidate's record; create-only records.
4. `context_assembly/application/inherited_release.py` (decisions section 45): canonical main fetched once, the plan
   authority read at that commit; an unfetchable main answers CANONICAL_MAIN_UNAVAILABLE, writes nothing and raises
   no owner decision. `packet_assessment.py`: that reason holds as CANONICAL_MAIN_UNAVAILABLE.
5. `execution_coordination/` (decisions section 45): PRODUCER outcome `canonical-main-unavailable` and CLOSURE's
   `remote-unreadable` are infrastructure: the stage stays, a later pass retries (PRODUCER_RETRY / CLOSURE_RETRY) at
   most VERIFIER_RETRY_LIMIT times in a row, then INFRASTRUCTURE_HOLD, typed, never an authority block or a Founder
   decision, retried by the next run of the factory; `RunSummary.infrastructure_held` names such items (the
   `work launch`/`work run` JSON gains that key).
6. Tests: the new pure tests; Work Context cases; composition tests (fetched remote tip, worker-clone reach, one
   snapshot, backward/rewritten main, crash re-prepare, containment fallback, release after a remote-only landing,
   assessment on an unknown tip); coordinator retry and exhaustion; inherited release fetch failure then success; BRL
   end to end (disjoint scopes retarget and land with the recorded execution baseline as candidate parent and gate
   baseline; overlapping scopes held; PRODUCER and CLOSURE fetch failures retried with no Founder decision; exhaustion
   held as infrastructure and landed by the next run). Fixtures release at canonical main.

## 3. Acceptance checks

1. `tests/context_assembly/test_baseline_revalidation.py`, `tests/context_assembly/test_proof_set.py`.
2. The targeted proof set (decisions sections 28 and 43), the block below.
3. The protected tests `tests/context_assembly/test_plan_approval.py` and
   `tests/execution_coordination/test_containment_wiring.py` pass unmodified; `test_inherited_release.py` changes only
   by the added fetch-failure test (decisions section 45).
4. **No test id disappears**: `python3 -m pytest --collect-only -q tests` at the starting revision and at the candidate;
   every id collected at the starting revision is collected at the candidate (collection only; nothing runs).
5. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-proof
{"targeted_tests": ["tests/execution_coordination/test_factory_coordinator.py", "tests/context_assembly/test_baseline_revalidation.py", "tests/context_assembly/test_proof_set.py", "tests/context_assembly/test_work_context.py", "tests/context_assembly/test_plan_approval.py", "tests/context_assembly/test_inherited_release.py", "tests/composition/test_work_registry.py", "tests/composition/test_worker_launch.py", "tests/composition/test_bounded_routine_launch.py", "tests/composition/test_lifecycle_capstone.py", "tests/invocation_runtime/test_runtime.py", "tests/execution_coordination/test_containment_wiring.py", "tests/control_plane/test_cli.py"]}
```

```json alienintent-mutations
[
 {
  "name": "the plan-authority check is ignored",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "(\"plan-authority\", not authority_reasons,",
    "new": "(\"plan-authority\", True,"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[outside-authority]"
  ]
 },
 {
  "name": "a packet without a proof set is retargeted",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "(\"proof-declared\", proof_declared,",
    "new": "(\"proof-declared\", True,"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[no-proof-set]"
  ]
 },
 {
  "name": "only an exactly equal path counts as touching a guarded entry",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "if any(under(path, entry) or under(entry, path) for entry in readable))",
    "new": "if any(path == entry for entry in readable))"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[directory-entry-slash]",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[over-a-guarded-entry]",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[under-a-directory-entry]"
  ]
 },
 {
  "name": "a main that moved backward proceeds at the old baseline",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "    if baseline == main:\n",
    "new": "    if baseline == main or relation == BEHIND:\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_an_item_whose_baseline_canonical_main_no_longer_contains_is_never_run_from_that_baseline[backward]",
   "tests/context_assembly/test_baseline_revalidation.py::test_main_that_no_longer_contains_the_baseline_goes_back_to_preparation_and_never_runs_ahead_of_main[behind]"
  ]
 },
 {
  "name": "a failed check still retargets",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "    if all(passed for _, passed, _ in checks):\n",
    "new": "    if True:\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_a_reference_guards_its_path_and_prose_is_kept_whole_so_it_holds",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[directory-entry-slash]",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[dotted-entry]",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[entry-a-glob]"
  ]
 },
 {
  "name": "a proof file outside tests/ and tools/ is accepted",
  "path": "src/alienintent/context_assembly/domain/proof_set.py",
  "edits": [
   {
    "old": "            and any(under(path, root) for root in PROOF_ROOTS) for path in tests):",
    "new": "            for path in tests):"
   }
  ],
  "tests": [
   "tests/context_assembly/test_proof_set.py::test_a_malformed_proof_block_is_refused[outside-tests-and-tools]"
  ]
 },
 {
  "name": "canonical main is the clone's stale local branch",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                                 f\"{canonical_ref(location)}^{{commit}}\"],",
    "new": "                                 f\"refs/heads/{location.default_branch}^{{commit}}\"],"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_the_live_authority_is_canonical_main_fetched_from_the_remote_not_the_local_branch"
  ]
 },
 {
  "name": "the plan authority is read at a second fetch, not the snapshot",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "(lambda: self._head(name)) if tip is None else (lambda: tip))",
    "new": "(lambda: self._head(name)))"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_one_baseline_revalidation_reads_canonical_main_once_and_judges_every_fact_at_that_sha"
  ]
 },
 {
  "name": "a held item's PRODUCER runs on its old baseline",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "            if decision.kind == REPREPARE:\n",
    "new": "            if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_an_item_whose_scope_main_changed_is_held_for_re_preparation_not_retargeted"
  ]
 },
 {
  "name": "the candidate's execution baseline is not recorded",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "            self.context.record_execution_baseline(identity, candidate.content_digest, self.context.attempt_baseline(",
    "new": "            (identity, candidate.content_digest, self.context.attempt_baseline("
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_retargeted_candidate_is_built_and_verified_on_its_execution_baseline_and_keeps_its_release_baseline",
   "tests/composition/test_bounded_routine_launch.py::test_an_item_whose_scope_main_changed_is_held_for_re_preparation_not_retargeted"
  ]
 },
 {
  "name": "the VERIFIER starts at the release baseline",
  "path": "src/alienintent/context_assembly/application/work_context.py",
  "edits": [
   {
    "old": "            fields[\"starting_revision\"] = fields[\"execution_baseline\"][\"execution_baseline\"]\n            revision = candidate_revision(held)",
    "new": "            revision = candidate_revision(held)"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_retargeted_candidate_is_built_and_verified_on_its_execution_baseline_and_keeps_its_release_baseline",
   "tests/context_assembly/test_work_context.py::test_a_retargeted_candidate_is_verified_against_its_execution_baseline_not_its_release_baseline"
  ]
 },
 {
  "name": "a candidate with no record falls back to the release baseline",
  "path": "src/alienintent/context_assembly/application/work_context.py",
  "edits": [
   {
    "old": "            raise _hold(MISSING, \"execution_baseline\", detail=\"no execution baseline recorded for this candidate\")",
    "new": "            return {\"release_baseline\": release_baseline, \"execution_baseline\": release_baseline, \"kind\": \"proceed\", \"checks\": []}"
   }
  ],
  "tests": [
   "tests/context_assembly/test_work_context.py::test_a_candidate_with_no_recorded_execution_baseline_is_never_verified_against_the_release_baseline"
  ]
 },
 {
  "name": "the PRODUCER ignores its recorded execution baseline",
  "path": "src/alienintent/context_assembly/application/work_context.py",
  "edits": [
   {
    "old": "            fields[\"starting_revision\"] = fields[\"execution_baseline\"][\"execution_baseline\"]\n            fields[\"assessment\"]",
    "new": "            fields[\"assessment\"]"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_retargeted_candidate_is_built_and_verified_on_its_execution_baseline_and_keeps_its_release_baseline",
   "tests/context_assembly/test_work_context.py::test_a_producer_attempt_starts_at_its_recorded_execution_baseline_and_keeps_its_release_baseline"
  ]
 },
 {
  "name": "a scope entry is compared unnormalized",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "    paths = {entry: None if any(c.isspace() for c in str(entry)) else normalized(entry) for entry in guarded}\n",
    "new": "    paths = {entry: entry for entry in guarded}\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_a_reference_guards_its_path_and_prose_is_kept_whole_so_it_holds",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[directory-entry-slash]",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[dotted-entry]",
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[entry-a-glob]"
  ]
 },
 {
  "name": "a malformed mutations block is ignored",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "(\"packet-readable\", not packet_errors,",
    "new": "(\"packet-readable\", True,"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_anything_that_cannot_be_revalidated_goes_back_to_preparation_at_the_assessed_baseline[packet-unreadable]"
  ]
 },
 {
  "name": "worker clones never receive canonical main",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                                 f\"+refs/heads/{branch}:refs/heads/{CANONICAL_MAIN}\"],\n",
    "new": "                                 ],\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_fetched_canonical_main_reaches_a_clone_of_the_clone"
  ]
 },
 {
  "name": "a failed fetch leaves no protected paths",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        current = self._fetched_authority()\n        if current is None and self.plan_approval is not None and \\\n",
    "new": "        current = self.plan_approval.current()\n        if current is None and self.plan_approval is not None and \\\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_containment_reads_the_last_fetched_main_never_a_newer_tip",
   "tests/composition/test_work_registry.py::test_protected_paths_survive_a_failed_fetch_at_the_last_fetched_canonical_main"
  ]
 },
 {
  "name": "a re-prepared attempt runs ahead of canonical main",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                if on_main is False:\n",
    "new": "                if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_re_prepared_attempt_keeps_its_recorded_baseline_only_while_it_is_on_canonical_main"
  ]
 },
 {
  "name": "a release is checked against the clone's local branch",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                                {name: canonical_ref(location) for name, location in repositories.items()},\n                                self._head,",
    "new": "                                {name: location.default_branch for name, location in repositories.items()},\n                                self._head,"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_landing_that_only_the_remote_has_never_blocks_the_next_release_or_its_dispatch"
  ]
 },
 {
  "name": "the dispatch gate checks the clone's local branch",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                                       canonical_ref(packets))",
    "new": "                                       packets.default_branch)"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_landing_that_only_the_remote_has_never_blocks_the_next_release_or_its_dispatch"
  ]
 },
 {
  "name": "a PRODUCER infrastructure failure is not retried",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if outcome.kind in PRODUCER_INFRASTRUCTURE:\n",
    "new": "            if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_producer_that_cannot_fetch_canonical_main_is_retried_and_lands_with_no_founder_decision",
   "tests/execution_coordination/test_factory_coordinator.py::test_a_producer_that_cannot_read_canonical_main_is_retried_with_no_founder_decision"
  ]
 },
 {
  "name": "exhausted infrastructure retries escalate",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            return _Advance(state, INFRASTRUCTURE_HOLD, fields | {",
    "new": "            return _Advance(state, \"authority-block\", fields | {"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_canonical_main_unreachable_past_the_retries_holds_as_infrastructure_and_the_next_run_lands_it",
   "tests/execution_coordination/test_factory_coordinator.py::test_canonical_main_unreachable_past_the_retry_limit_is_a_typed_infrastructure_hold_never_a_founder_decision"
  ]
 },
 {
  "name": "an infrastructure hold is rerun at once by the same run",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if projected.outcome == INFRASTRUCTURE_HOLD and item.identity in self._infrastructure_held:\n",
    "new": "            if False:\n"
   }
  ],
  "tests": [
   "tests/execution_coordination/test_factory_coordinator.py::test_canonical_main_unreachable_past_the_retry_limit_is_a_typed_infrastructure_hold_never_a_founder_decision"
  ]
 },
 {
  "name": "a closure remote-unreadable hold escalates",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            if held is not None and held[0] in CLOSURE_INFRASTRUCTURE:\n",
    "new": "            if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_closure_that_cannot_fetch_canonical_main_is_retried_and_lands_with_no_founder_decision"
  ]
 },
 {
  "name": "a release fetch failure becomes an owner decision",
  "path": "src/alienintent/context_assembly/application/inherited_release.py",
  "edits": [
   {
    "old": "        if baseline is None:\n            return ReleaseResult(item.id, CANONICAL_MAIN_UNAVAILABLE,",
    "new": "        if False:\n            return ReleaseResult(item.id, CANONICAL_MAIN_UNAVAILABLE,"
   }
  ],
  "tests": [
   "tests/context_assembly/test_inherited_release.py::test_a_fetch_failure_writes_nothing_raises_no_owner_decision_and_the_same_item_is_released_on_retry"
  ]
 },
 {
  "name": "a PRODUCER fetch failure is an authority refusal",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "            if answered is None:\n                return unavailable\n",
    "new": "            if answered is None:\n                return self._refusal(invocation, \"starting_revision: unavailable\")\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_producer_that_cannot_fetch_canonical_main_is_retried_and_lands_with_no_founder_decision"
  ]
 },
 {
  "name": "the landing gate calls a fetch failure no plan authority",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                return (REMOTE_UNREADABLE,) if getattr(self._registry, \"canonical_main_unreadable\", False) \\\n",
    "new": "                return (NO_PLAN_AUTHORITY,) if getattr(self._registry, \"canonical_main_unreadable\", False) \\\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_closure_that_cannot_fetch_canonical_main_is_retried_and_lands_with_no_founder_decision"
  ]
 },
 {
  "name": "an assessment skips the plan check on an unknown tip",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "            if main is None:\n                return (UNAVAILABLE_REASON,)\n",
    "new": "            if main is None:\n                return ()\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_an_assessment_never_skips_the_plan_check_on_an_unknown_tip_and_runs_once_main_is_reachable"
  ]
 },
 {
  "name": "an unreadable remote at settlement is a landing ambiguity for the Founder",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "            return (), (hold(REMOTE_UNREADABLE),)\n        published = (receipt(",
    "new": "            return (), (hold(\"landing-ambiguous\", order[\"base\"], order[\"merge\"], order[\"record\"], \"unreadable\"),)\n        published = (receipt("
   }
  ],
  "tests": [
   "tests/composition/test_worker_launch.py::test_an_ambiguous_landing_holds_with_facts_and_is_settled_before_any_later_session[unreadable]"
  ]
 },
 {
  "name": "eligibility fetches the live authority",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "_ContractRelease(self.ready_view, self._fetched_authority)",
    "new": "_ContractRelease(self.ready_view, self.plan_approval.current)"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_an_outage_never_makes_a_released_plan_derived_item_ineligible"
  ]
 },
 {
  "name": "prose references are truncated to their first word",
  "path": "src/alienintent/context_assembly/domain/baseline_revalidation.py",
  "edits": [
   {
    "old": "        entry = parts[0] if len(parts) == 2 and parts[1].startswith(\"obligation:\") else reference\n",
    "new": "        entry = parts[0] if parts else reference\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_baseline_revalidation.py::test_a_reference_guards_its_path_and_prose_is_kept_whole_so_it_holds"
  ]
 },
 {
  "name": "git that cannot answer reads as not an ancestor",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "    return {0: True, 1: False}.get(code)\n",
    "new": "    return code == 0\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_git_that_cannot_answer_an_ancestry_question_is_unknown_never_diverged"
  ]
 },
 {
  "name": "an infrastructure retry count is never reset by another outcome",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "        if counter is not None and counter not in advanced.fields:\n",
    "new": "        if False:\n"
   }
  ],
  "tests": [
   "tests/execution_coordination/test_factory_coordinator.py::test_a_closure_outcome_that_is_not_infrastructure_resets_the_closure_streak",
   "tests/execution_coordination/test_factory_coordinator.py::test_infrastructure_retries_count_failures_in_a_row_and_any_other_outcome_resets_them"
  ]
 },
 {
  "name": "the run summary hides infrastructure holds",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "            tuple(item.identity for item in items if self._outcome(item.identity) == INFRASTRUCTURE_HOLD),\n",
    "new": "            (),\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_closure_whose_remote_stays_unreadable_holds_as_infrastructure_visibly_and_never_for_the_founder"
  ]
 },
 {
  "name": "work launch hides an infrastructure hold",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "                          infrastructure_held=(identity,) if outcome == INFRASTRUCTURE_HOLD else ())",
    "new": "                          infrastructure_held=())"
   }
  ],
  "tests": [
   "tests/execution_coordination/test_factory_coordinator.py::test_work_launch_names_an_infrastructure_hold_in_its_summary"
  ]
 },
 {
  "name": "a candidate fetch failure at CLOSURE is reworked",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        if not self._present(clone, revision) and self._candidate_unreadable(clone, candidate):\n            return (), (*findings, hold(REMOTE_UNREADABLE))",
    "new": "        if False:\n            return (), (*findings, hold(REMOTE_UNREADABLE))"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_fetch_failure_at_closure_is_retried_never_reworked"
  ]
 },
 {
  "name": "a release-gate refusal keeps the PRODUCER streak",
  "path": "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "edits": [
   {
    "old": "{\"hold_reason\": f\"release-precondition:{refusal.check}\", \"producer_retries\": 0})",
    "new": "{\"hold_reason\": f\"release-precondition:{refusal.check}\"})"
   }
  ],
  "tests": [
   "tests/execution_coordination/test_factory_coordinator.py::test_a_release_gate_refusal_between_canonical_main_failures_resets_the_streak"
  ]
 },
 {
  "name": "a candidate the remote no longer has loops as infrastructure",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        if not reference:\n            return False\n",
    "new": "        return True\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_branch_the_remote_no_longer_has_is_judged_never_retried_as_infrastructure"
  ]
 },
 {
  "name": "an unreachable candidate remote is judged instead of retried",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        if not answer:\n            return True\n",
    "new": "        if not answer:\n            return False\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_fetch_failure_at_closure_is_retried_never_reworked"
  ]
 },
 {
  "name": "a candidate the remote still advertises is judged",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        return f\"{revision}\\trefs/heads/{reference}\" in answer.splitlines()",
    "new": "        return False"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_a_candidate_the_remote_still_advertises_but_that_did_not_arrive_is_retried",
   "tests/composition/test_bounded_routine_launch.py::test_one_remote_answer_decides_an_absent_candidate"
  ]
 },
 {
  "name": "a pruned baseline is retried forever as unavailable",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "        if not _has_commit(clone, baseline):  # pruned after main moved past it: off canonical history, not a failure\n",
    "new": "        if False:\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_baseline_commit_canonical_main_no_longer_has_is_off_history_never_unavailable"
  ]
 },
 {
  "name": "a local read failure of the last fetched main escapes",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                                     f\"{canonical_ref(location)}^{{commit}}\"],\n                                    cwd=location.clone, capture_output=True, check=False, timeout=60)\n        except (OSError, subprocess.SubprocessError):\n",
    "new": "                                     f\"{canonical_ref(location)}^{{commit}}\"],\n                                    cwd=location.clone, capture_output=True, check=False, timeout=60)\n        except ZeroDivisionError:\n"
   }
  ],
  "tests": [
   "tests/composition/test_work_registry.py::test_a_local_git_failure_reading_the_last_fetched_main_is_no_answer_never_a_crash"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `58b3742` (byte copy:
`~/.local/state/alienintent/manual/path-to-done/work-preparation-refill/r2-prototype-on-58b3742.diff`). Built
test-first; the targeted set passes (1507, 4 skipped); 0 test ids missing against main; fitness passes; the
42 mutations each fail their named tests and pass when restored. A first fresh adversarial review found a
blocker (worker clones never received a fetched canonical main) and four majors (unnormalized guarded paths, a
malformed mutations block silently weakening the guard, a fetch failure becoming a false containment rejection, a crash
re-prepare reusing an off-history baseline); a second found a blocker (release reachability checked against the
local branch) and the Founder-escalation of transient fetch failures (decisions sections 44-45); a third found five
more fetch-failure and reference defects, resolved by fetching fresh only where the current tip decides; four more
rounds found and fixed the in-a-row retry semantics, CLOSURE's candidate-branch fetch (decided by one `git ls-remote`
answer), a pruned baseline (off history, not unavailable), containment reading the last fetched main, and an
unguarded local read; all fixed test-first, each with a mutation. The final review of the frozen diff found no defect
in its scope. Known, decided next (decisions section 46): the custody-read check in `invocation_runtime/real_worker.py`
turns a transient candidate read failure at VERIFIER/CLOSURE into an authority block; the same file's containment
answers SCOPE_VIOLATION when both the local read and a fresh fetch fail.
