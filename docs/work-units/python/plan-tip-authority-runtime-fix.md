# Work unit: plan tip is the live authority (runtime fix)

**Label:** `PLAN-TIP-AUTHORITY-RUNTIME-FIX` (a document label; permanent id `c2c5b816-ec10-404f-8c2b-20da0f0a0861`).
**Status:** Revision 1, 2026-10-10. Registered (CAPTURE).
**Authority:** Founder authorization 2026-10-10 (decisions section 31), quoted in `fixed_decisions`; it changes protected
plan-authority/release machinery, so it is not plan-derived and is released by `work authorize` with those words.
**Starting revision:** main `83eb7b7`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "c2c5b816-ec10-404f-8c2b-20da0f0a0861",
 "version": "revision-1",
 "intent": "Make the runtime enforce the approved plan: the canonical plan at the tip of canonical main is the live plan authority, read at every decision with its exact commit and digest; no approve-plan snapshot is needed to activate a revision; a derived Work Item records the plan revision it was prepared from and the tip it was released under, and an item prepared from an older revision is revalidated against the tip by the same scope rules before inherited release and again at CLOSURE.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-10 (decisions section 31, the authorization of this item): I authorize a narrowly scoped Work Item to update plan-authority enforcement so that: The canonical AlienIntent project plan at canonical `main` tip is the live authority root. Exact plan commit/digest remains recorded on each derived Work Item for provenance and stale-work detection, but no prior `approve-plan` snapshot is required to activate a newer owner-authorized plan revision. A Work Item prepared from an older plan revision must be deterministically revalidated against current tip before inherited release. Scope only the plan-authority/release machinery and its tests. No other protected-path changes. (Founder, 2026-10-10)",
  "Founder 2026-10-10 (plan 8440338, section 2.2.1): the canonical project plan at the tip of canonical main is the live authority root; authority follows the protected plan tip; an owner-authorized plan change that lands becomes active automatically.",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-10 (decisions section 28): the targeted test set is part of the Work Item's proof contract."
 ],
 "authorized_scope": [
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/application/inherited_release.py",
  "src/alienintent/context_assembly/application/plan_approval.py",
  "src/alienintent/execution_coordination/domain/plan_authority.py",
  "tests/composition/test_work_registry.py",
  "tests/composition/test_worker_launch.py",
  "tests/context_assembly/test_inherited_release.py",
  "tests/context_assembly/test_plan_approval.py",
  "tests/execution_coordination/domain/test_plan_authority.py",
  "tests/execution_coordination/test_containment_wiring.py"
 ],
 "excluded_scope": [
  "any protected path other than the plan-authority/release machinery and its tests",
  "src/alienintent/execution_coordination/domain/satisfiability.py",
  "src/alienintent/execution_coordination/domain/release.py",
  "src/alienintent/composition/landing_authority.py",
  "the canonical plan document"
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
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/plan-tip-authority-runtime-fix.diff (sha256 7802ab871528854ae0ffb118d34c8307d23551a39a83105e96338be0f5d8c743), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "checking that an issuer digest names a real plan revision (it is provenance and grants nothing)",
  "event-driven wakeups",
  "the PRODUCER starting revision (WORK-PREPARATION-REFILL)"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "docs/work-units/python/plan-tip-authority-runtime-fix.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/plan-tip-authority-runtime-fix.diff is absent from the context package, its text's sha256 is not 7802ab871528854ae0ffb118d34c8307d23551a39a83105e96338be0f5d8c743, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

The canonical plan (8440338, section 2.2.1) makes the plan at the tip of canonical main the live authority root, but
the runtime still grants authority only from the `work approve-plan` record of revision 28df5c3 and refuses any item
whose issuer names another digest. The next autonomous release would depend on that obsolete snapshot model.

## 2. The change: exactly the referenced prototype diff at `83eb7b7`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/plan-tip-authority-runtime-fix.diff`; that entry's `text` field
  holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `7802ab871528854ae0ffb118d34c8307d23551a39a83105e96338be0f5d8c743` (46,279 bytes, 10 files, unified diff, `git apply` format).
- **Baseline:** main `83eb7b7`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 10 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `7802ab871528854ae0ffb118d34c8307d23551a39a83105e96338be0f5d8c743`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. **The live authority** (`context_assembly/application/plan_approval.py`): `PlanApproval.current()` reads the
   canonical plan at the tip of the packets clone's default branch (`refs/heads/<branch>`, through the composition's
   `_head`) at every call, parses its plan-authority block and answers its exact commit and `sha256:` digest
   (`record_ref` `git:<commit>:<plan path>`, approver `canonical main tip`); None when the tip, the plan or its block
   cannot be read. `work approve-plan` still records an exact revision, as a record, never an activation switch.
2. **Revalidation** (`execution_coordination/domain/plan_authority.py`): the issuer rule requires a well-formed
   `plan-authority:sha256:<64 hex>` (the revision the item was prepared from, provenance); every other rule checks the
   contract against the live plan's scope, so an item from an older revision inherits exactly when the tip still
   grants it. The canonical plan file is always a protected path, whatever the live block lists.
3. **Provenance** (`context_assembly/application/inherited_release.py`): `work release` reads the live authority once,
   checks the item against exactly that read (`_satisfiable(..., authority)`), and records `plan: {commit,
   content_digest, prepared_from}`; its release text adds `; revalidated from <digest>` when they differ.
4. **Wiring** (`composition/work_registry.py`): the tip reader and comments; every consumer (ready view, release,
   satisfiability, CLOSURE landing gate, protected paths) already reads `current()`.

## 3. Acceptance checks

1. `tests/context_assembly/test_plan_approval.py` (the tip is the authority with no approval; it follows the tip; an
   invalid tip block is no authority; a tag named like the branch is ignored), `tests/context_assembly/test_inherited_release.py`
   (an item from an older revision is revalidated and released with its provenance; a tip that drops the obligation
   refuses with an owner decision; one tip read per release), `tests/execution_coordination/domain/test_plan_authority.py`
   (issuer format; revalidation; the plan always protected).
2. The targeted proof set (decisions section 28), every test file that exercises plan authority:
   `tests/context_assembly/test_plan_approval.py`, `tests/context_assembly/test_inherited_release.py`, `tests/execution_coordination/domain/test_plan_authority.py`, `tests/execution_coordination/domain/test_satisfiability.py`, `tests/execution_coordination/test_containment_wiring.py`, `tests/composition/test_worker_launch.py`, `tests/composition/test_bounded_routine_launch.py`, `tests/composition/test_work_registry.py`, `tests/control_plane/test_cli.py`.
3. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-mutations
[
 {
  "name": "the issuer must equal the tip digest",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "    if ISSUER.fullmatch(contract.authority_issuer or \"\") is None:",
    "new": "    if contract.authority_issuer != ISSUER_PREFIX + authority.content_digest:"
   }
  ],
  "tests": [
   "tests/context_assembly/test_inherited_release.py::test_a_release_records_and_checks_one_and_the_same_tip",
   "tests/context_assembly/test_inherited_release.py::test_an_item_prepared_under_an_older_plan_revision_is_revalidated_and_released_under_the_tip",
   "tests/execution_coordination/domain/test_plan_authority.py::test_a_contract_prepared_under_an_older_plan_revision_is_revalidated_against_the_live_one"
  ]
 },
 {
  "name": "the issuer format is not checked",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "    if ISSUER.fullmatch(contract.authority_issuer or \"\") is None:",
    "new": "    if False:"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change0-authority_issuer: not a plan authority digest]",
   "tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change1-authority_issuer: not a plan authority digest]"
  ]
 },
 {
  "name": "the live authority ignores the tip",
  "path": "src/alienintent/context_assembly/application/plan_approval.py",
  "edits": [
   {
    "old": "            commit = self.tip()\n",
    "new": "            commit = None\n"
   }
  ],
  "tests": [
   "tests/context_assembly/test_inherited_release.py::test_a_plan_derived_item_is_released_its_card_reads_back_ready_p0_and_its_producer_context_assembles",
   "tests/context_assembly/test_inherited_release.py::test_a_release_records_and_checks_one_and_the_same_tip",
   "tests/context_assembly/test_inherited_release.py::test_an_item_prepared_under_an_older_plan_revision_is_revalidated_and_released_under_the_tip",
   "tests/context_assembly/test_inherited_release.py::test_each_refusal_answers_its_code_and_writes_nothing[dropped-obligation]"
  ]
 },
 {
  "name": "the release omits the revision it was prepared from",
  "path": "src/alienintent/context_assembly/application/inherited_release.py",
  "edits": [
   {
    "old": "\"prepared_from\": prepared}",
    "new": "\"prepared_from\": authority.content_digest}"
   }
  ],
  "tests": [
   "tests/context_assembly/test_inherited_release.py::test_an_item_prepared_under_an_older_plan_revision_is_revalidated_and_released_under_the_tip"
  ]
 },
 {
  "name": "the release text hides the revalidation",
  "path": "src/alienintent/context_assembly/application/inherited_release.py",
  "edits": [
   {
    "old": "        revalidated = \"\" if prepared == authority.content_digest else f\"; revalidated from {prepared}\"",
    "new": "        revalidated = \"\""
   }
  ],
  "tests": [
   "tests/context_assembly/test_inherited_release.py::test_an_item_prepared_under_an_older_plan_revision_is_revalidated_and_released_under_the_tip"
  ]
 },
 {
  "name": "the release checks a second read of the tip",
  "path": "src/alienintent/context_assembly/application/inherited_release.py",
  "edits": [
   {
    "old": "item.pointer.commit, item.id, authority)  # checked against this read",
    "new": "item.pointer.commit, item.id)  # checked against this read"
   }
  ],
  "tests": [
   "tests/context_assembly/test_inherited_release.py::test_a_release_records_and_checks_one_and_the_same_tip"
  ]
 },
 {
  "name": "the tip is read by its bare name",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "                                 f\"refs/heads/{location.default_branch}^{{commit}}\"],",
    "new": "                                 f\"{location.default_branch}^{{commit}}\"],"
   }
  ],
  "tests": [
   "tests/context_assembly/test_plan_approval.py::test_a_tag_named_like_the_branch_never_becomes_the_authority"
  ]
 },
 {
  "name": "the plan is not protected",
  "path": "src/alienintent/execution_coordination/domain/plan_authority.py",
  "edits": [
   {
    "old": "for path in (*scope.protected_paths, PLAN_PATH)]",
    "new": "for path in scope.protected_paths]"
   }
  ],
  "tests": [
   "tests/execution_coordination/domain/test_plan_authority.py::test_the_plan_itself_is_protected_whatever_the_live_block_says"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (can defer)
- The issuer digest is provenance only: one naming no real plan revision is accepted and grants nothing (the tip
  decides scope).
- The live authority is read from the packets clone's local default branch; a clone that has not fetched lags the
  remote tip (the release gate and baseline read the same branch).

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `83eb7b7` (byte copy:
`~/.local/state/alienintent/manual/path-to-done/plan-tip-authority/prototype-on-83eb7b7.diff`). Built test-first;
the targeted set passes; fitness passes; the 8 mutations each fail their named tests and pass when
restored. Reviews: the first found a tag named like the branch winning over it and a release recording one tip read
while checking another; both fixed test-first, plus the plan always protected; the second review: PASS.
