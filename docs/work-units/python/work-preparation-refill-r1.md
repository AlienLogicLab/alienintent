# Work unit: plan obligations state their work (WORK-PREPARATION-REFILL R1)

**Label:** `WORK-PREPARATION-REFILL-R1` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Revision 1, 2026-10-10. Not registered.
**Authority:** Founder authorization 2026-10-10 (decisions section 38), quoted in `fixed_decisions`; it changes the
protected canonical plan and plan-authority machinery, so it is not plan-derived and is released by `work authorize`
with those words. Its one `work launch` is a bootstrap artifact of the pre-REFILL runtime (decisions section 39).
**Starting revision:** main `6b41e34`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "The canonical plan's obligations carry intent, acceptance ids, depends_on and an explicit satisfied_by mapping to landed work; the plan-authority parser validates them (acceptance ids distinct across the block, dependencies known and acyclic, mappings to own ids with a full landed commit and evidence, priority exactly the scheduler's P0-P5); the plan text is the Founder-approved text, including the new obligation EVENT-TRIGGERED-CONTINUATION; and a pure Work Preparation function answers each obligation's state and the next eligible obligation by numeric priority then plan order.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-10 (decisions section 38, the authorization of this item): WORK-PREPARATION-REFILL may amend the canonical plan obligation schema to include intent, acceptance, and depends_on; update plan-authority parsing/validation accordingly; add a bounded PREPARER role that derives executable Work Items only from canonical plan authority; and allow deterministic inherited release inside the autonomous run loop after Agent Ready returns READY. These changes may touch the protected canonical plan, plan-authority machinery, and inherited-release machinery only as required to implement this approved design. No new product authority is granted beyond the current canonical plan.",
  "Founder 2026-10-10 (decisions section 39): \"New acceptance semantics cannot be retroactively proven merely because an old Work Item says DONE\"; satisfaction is an explicit mapping (acceptance id, work item, landed commit, deterministic evidence).",
  "Founder 2026-10-10 (decisions section 40): the obligation text in this diff is approved, with EVENT-TRIGGERED-CONTINUATION as a new obligation and the dependency table VOI none; BRL none; WORK-PREPARATION-REFILL VOI+BRL; TERMINAL-BOARD-STATUSES BRL; STORE-SCHEMA-HARDENING none; EVENT-TRIGGERED-CONTINUATION BRL; AUTONOMY-PROOF REFILL+TBS+SSH+ETC.",
  "Founder 2026-10-10 (decisions section 41): priority is numeric (P<n> -> n), malformed values are refused; the scheduler and Work Preparation mean the same thing by priority.",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-10 (decisions section 28): the targeted test set is part of the Work Item's proof contract."
 ],
 "authorized_scope": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "src/alienintent/context_assembly/domain/obligation_state.py",
  "src/alienintent/execution_coordination/domain/plan_authority.py",
  "tests/composition/test_work_registry.py",
  "tests/context_assembly/test_obligation_state.py",
  "tests/execution_coordination/domain/test_plan_authority.py",
  "tests/execution_coordination/test_containment_wiring.py"
 ],
 "excluded_scope": [
  "any protected path other than the canonical plan, plan_authority.py and their tests",
  "the PREPARER, Work Preparation service, run loop and baseline (WORK-PREPARATION-REFILL R2-R4)",
  "src/alienintent/context_assembly/application/inherited_release.py",
  "src/alienintent/composition/landing_authority.py"
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
  "acceptance checks 1-5 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "no test id collected at the starting revision is missing at the candidate (acceptance check 4)",
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/work-preparation-refill-r1.diff (sha256 17c0467d4203b19fc65dd6d4ccc806b9ec05b89573a7c8351cd28e5bdfdc5188), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "reading the registry to verify a satisfied_by mapping (R3 supplies `mapping_holds`)",
  "PREPARER, preparation service, refill, health fault, current-main baseline (R2-R4)"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "docs/work-units/python/work-preparation-refill-r1.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/work-preparation-refill-r1.diff is absent from the context package, its text's sha256 is not 17c0467d4203b19fc65dd6d4ccc806b9ec05b89573a7c8351cd28e5bdfdc5188, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

WORK-PREPARATION-REFILL (decisions sections 37-41) needs a PREPARER to derive the next Work Item from the live
canonical plan tip alone. Today an obligation holds only a label, a priority, requirement ids and allowed paths; what
it must achieve, when it is finished and what it depends on live outside the plan. This first child puts that
semantic contract into the canonical plan, validates it, and computes obligation state from it.

## 2. The change: exactly the referenced prototype diff at `6b41e34`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/work-preparation-refill-r1.diff`; that entry's `text` field
  holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `17c0467d4203b19fc65dd6d4ccc806b9ec05b89573a7c8351cd28e5bdfdc5188` (51,048 bytes, 7 files, unified diff, `git apply` format).
- **Baseline:** main `6b41e34`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 7 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `17c0467d4203b19fc65dd6d4ccc806b9ec05b89573a7c8351cd28e5bdfdc5188`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. `execution_coordination/domain/plan_authority.py`: `Obligation` gains `intent`, `acceptance` (`Acceptance(id,
   text)`), `depends_on` and `satisfied_by` (`Satisfaction(acceptance_id, work_item, landed_commit, evidence)`);
   `scope_from` validates them and `document()` round-trips them; `PRIORITIES` (P0-P5) and `priority_rank`.
2. `docs/decisions/alienintent-v2-canonical-project-plan.md`: the approved obligation text (decisions section 40)
   in the block, EVENT-TRIGGERED-CONTINUATION added before AUTONOMY-PROOF, VOI and BRL acceptance mapped to their
   landings, one sentence in section 2.2.1. The parser and the plan change together (the parser is exact-keys).
3. `context_assembly/domain/obligation_state.py` (new, pure): `obligation_states` and `next_obligation`.
4. Test fixtures that build a plan block carry the new keys; `test_check7_...` (same name) checks the new label list,
   the dependency table and the mapping.

## 3. Acceptance checks

1. `tests/execution_coordination/domain/test_plan_authority.py` (the obligation semantics validated, a three-way cycle
   refused, the document round-trip, numeric priority, check7 on the canonical plan) and
   `tests/context_assembly/test_obligation_state.py`.
2. The targeted proof set (decisions section 28), every test file that builds or reads a plan block:
   `tests/execution_coordination/domain/test_plan_authority.py`, `tests/context_assembly/test_obligation_state.py`, `tests/execution_coordination/test_containment_wiring.py`, `tests/composition/test_work_registry.py`, `tests/composition/test_worker_launch.py`, `tests/composition/test_bounded_routine_launch.py`, `tests/context_assembly/test_inherited_release.py`, `tests/context_assembly/test_plan_approval.py`, `tests/execution_coordination/domain/test_satisfiability.py`, `tests/control_plane/test_cli.py`.
3. The live canonical plan at the candidate parses: `parse_scope` of the plan file returns seven obligations.
4. **No test id disappears**: `python3 -m pytest --collect-only -q tests` at the starting revision and at the candidate;
   every id collected at the starting revision is collected at the candidate (collection only; nothing runs).
5. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-mutations
[
 {
  "name": "a dependency cycle is not detected",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "        if label in active:\n            raise PlanScopeInvalid",
    "new": "        if False:\n            raise PlanScopeInvalid"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_a_three_obligation_dependency_cycle_is_refused",
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[two-cycle]"
  ]
 },
 {
  "name": "acceptance ids are not distinct across the block",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "    if len(set(ids)) != len(ids):\n",
    "new": "    if False:\n"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[duplicate-id]",
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[id-across-obligations]"
  ]
 },
 {
  "name": "a mapping may name another obligation's id",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "s[\"acceptance_id\"] in ids",
    "new": "isinstance(s[\"acceptance_id\"], str)"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[mapping-other-obligation]"
  ]
 },
 {
  "name": "a mapping's landed commit is not a full sha",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "COMMIT.fullmatch(s[\"landed_commit\"])",
    "new": "s[\"landed_commit\"]"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[mapping-short-commit]"
  ]
 },
 {
  "name": "a priority outside the scheduler's set is accepted",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "        if entry[\"priority\"] not in PRIORITIES:\n",
    "new": "        if not isinstance(entry[\"priority\"], str):\n"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[priority-leading-zero]",
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[priority-lowercase]",
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[priority-off-board]",
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[priority-word]"
  ]
 },
 {
  "name": "an unknown or self dependency is accepted",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "if any(dependency == label or dependency not in edges for dependency in dependencies):",
    "new": "if False:"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_obligation_semantics_are_validated[unknown-dependency]"
  ]
 },
 {
  "name": "a legacy DONE item covers every id",
  "path": "src/alienintent/context_assembly/domain/obligation_state.py",
  "edits": [
   {
    "old": "for identity in item.satisfies}",
    "new": "for identity in (item.satisfies or [a.id for a in obligation.acceptance])}"
   }
  ],
  "tests": [
   "tests/context_assembly/test_obligation_state.py::test_an_unmapped_legacy_done_item_satisfies_nothing"
  ]
 },
 {
  "name": "a plan mapping counts without verification",
  "path": "src/alienintent/context_assembly/domain/obligation_state.py",
  "edits": [
   {
    "old": "for entry in obligation.satisfied_by if mapping_holds(entry)}",
    "new": "for entry in obligation.satisfied_by}"
   }
  ],
  "tests": [
   "tests/context_assembly/test_obligation_state.py::test_a_dependency_finished_only_by_a_failing_mapping_keeps_its_dependent_waiting",
   "tests/context_assembly/test_obligation_state.py::test_a_mapped_obligation_is_finished_only_when_its_mappings_hold"
  ]
 },
 {
  "name": "priority is ignored when choosing the next obligation",
  "path": "src/alienintent/context_assembly/domain/obligation_state.py",
  "edits": [
   {
    "old": "ranked = [(priority_rank(obligation.priority), index, obligation.label)",
    "new": "ranked = [(0, index, obligation.label)"
   }
  ],
  "tests": [
   "tests/context_assembly/test_obligation_state.py::test_the_next_obligation_is_eligible_by_numeric_priority_then_plan_order"
  ]
 },
 {
  "name": "dependencies are ignored for eligibility",
  "path": "src/alienintent/context_assembly/domain/obligation_state.py",
  "edits": [
   {
    "old": "        elif all(dependency in finished for dependency in obligation.depends_on):",
    "new": "        elif True:"
   }
  ],
  "tests": [
   "tests/context_assembly/test_obligation_state.py::test_a_dependency_finished_only_by_a_failing_mapping_keeps_its_dependent_waiting",
   "tests/context_assembly/test_obligation_state.py::test_a_mapped_obligation_is_finished_only_when_its_mappings_hold"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `6b41e34` (byte copy:
`~/.local/state/alienintent/manual/path-to-done/work-preparation-refill/r1-prototype-on-6b41e34.diff`). Built
test-first; the targeted set passes (339, plus the review's two refusal cases); 0 test ids missing against main; fitness
passes; the 10
mutations each fail their named tests and pass when restored; a fresh adversarial review of the frozen diff found
two parser defects (a non-string mapped acceptance id raised TypeError; a blank work item was accepted), both fixed
test-first.
