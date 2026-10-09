# Work unit: plan-level execution authority, with actual-diff containment

**Label:** `PLAN-AUTHORITY-INHERITANCE-R2` (a document label; permanent id `fb305fc5-5eef-494b-bcae-6276cf81bc31`). Re-issue of
`795cefb2` (#173), retired as a packet-definition failure: its packet sent the PRODUCER to the wrong source for the diff.
**Status:** R2, 2026-10-09. Registered.
**Position on the path (Founder 2026-10-09, decisions section 16):** step 3. VERIFIER gate evidence (done) -> NO-CHANGE
(done) -> PLAN-AUTHORITY-INHERITANCE -> BOUNDED-ROUTINE-LAUNCH -> Work Preparation / READY refill -> three-item proof.
**Starting revision:** main `17910f7`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.
**After landing, one genuine owner decision:** the Founder approves the landed plan revision once (`work approve-plan`).

## Contract

```json alienintent-contract
{
 "identity": "fb305fc5-5eef-494b-bcae-6276cf81bc31",
 "version": "revision-3",
 "intent": "The Founder approves an exact revision of the canonical plan once (`work approve-plan`); the plan names its obligations (each with allowed paths), its limits and its protected paths. A Work Item that names one of those obligations, stays inside its paths and the plan's limits, is assessed READY and is satisfiable is released by the control plane (`work release`) with no Founder words: release record, card READY with the obligation's priority, read back. Anything outside stops with a typed owner-decision requirement; ad hoc work keeps the explicit Founder release. A plan-derived candidate may advance only when its actual changed paths, read by the control plane from the trusted start to the candidate, are a subset of the exact assessed scope and touch no protected path; the PRODUCER checks before publication and CLOSURE checks the diff that would land, against the CURRENT approved authority, before any landing effect. A new plan approval stops items released under the old one. The canonical plan's section 2.2 states this rule.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-08 (decision 1): plan-level execution authority binds to an exact canonical-plan revision; a derived item inherits only when traceably derived from the plan, Agent Ready READY, satisfiable, dependencies and priority deterministic, and it introduces no new owner decision; otherwise a typed owner-decision requirement; ad hoc work keeps explicit Founder approval.",
  "Founder 2026-10-08 (decision 2): the authority root is docs/decisions/alienintent-v2-canonical-project-plan.md bound to an exact commit and content digest; a changed plan is not authorized by an old approval.",
  "Founder 2026-10-08 (decision 5): section 2.2 becomes 'After the Founder approves canonical product intent/plan authority, derived Work Items advance without additional Founder approval unless they cross a new owner-decision boundary.'",
  "Founder 2026-10-08 (decision 6): a plan-derived candidate may advance only when its actual changed paths are a subset of the exact assessed Work Item scope, and none of those paths intersect the protected authority surface; trusted inputs only (actual diff start->candidate, scope from the control plane's assessed packet, protected paths from the approved plan digest, evaluation code from the trusted baseline); checked before VERIFY admission (a failure is a PRODUCER rework, no VERIFIER attempt) and confirmed by CLOSURE before landing; core files are not blanket-protected.",
  "Founder 2026-10-09 (section 16): mission - approved canonical plan in, three real Work Items reach DONE automatically, the Founder does nothing except genuine owner decisions; the standing rule.",
  "Founder 2026-10-09: the whole suite is the regression gate's; the VERIFIER does not rerun it."
 ],
 "authorized_scope": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/application/inherited_release.py",
  "src/alienintent/context_assembly/application/plan_approval.py",
  "src/alienintent/control_plane/adapters/cli.py",
  "src/alienintent/control_plane/application/operator.py",
  "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/execution_coordination/domain/plan_authority.py",
  "src/alienintent/execution_coordination/domain/satisfiability.py",
  "src/alienintent/execution_coordination/domain/scope_containment.py",
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/invocation_runtime/adapters/git_source_control.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/invocation_runtime/ports/source_control.py",
  "tests/composition/test_work_registry.py",
  "tests/composition/test_worker_launch.py",
  "tests/context_assembly/test_inherited_release.py",
  "tests/context_assembly/test_plan_approval.py",
  "tests/control_plane/test_cli.py",
  "tests/execution_coordination/domain/test_plan_authority.py",
  "tests/execution_coordination/domain/test_satisfiability.py",
  "tests/execution_coordination/domain/test_scope_containment.py",
  "tests/execution_coordination/test_containment_wiring.py",
  "tools/fitness/coupling_register.json"
 ],
 "excluded_scope": [
  "src/alienintent/execution_coordination/domain/release.py",
  "src/alienintent/execution_coordination/application/release_admission.py",
  "src/alienintent/execution_coordination/adapters/release_admission.py",
  "src/alienintent/composition/release_admission.py",
  "src/alienintent/invocation_runtime/application/regression_gate.py",
  "src/alienintent/context_assembly/application/work_authorization.py",
  "src/alienintent/execution_coordination/adapters/github_work_management.py",
  "the worker effect ledger and the card projection outbox",
  "BASE_MOVED revalidation",
  "the runner (BOUNDED-ROUTINE-LAUNCH) and Work Preparation"
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
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/plan-authority-inheritance.diff (sha256 35686536f9e8dadf239fff0551d6dfe4c512f09009557a16fe3fc2c0d14a2b95), ignoring only `index` lines",
  "the VERIFIER runs the 17 mutations of check 4 exactly and records that each makes its named tests fail and that reverting makes them pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a generic messaging framework",
  "rewriting the coordinator's release labels"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md",
  "docs/work-units/python/plan-authority-inheritance.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/plan-authority-inheritance.diff is absent from the context package, its text's sha256 is not 35686536f9e8dadf239fff0551d6dfe4c512f09009557a16fe3fc2c0d14a2b95, or those bytes do not apply exactly at the starting revision",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

Every registry Work Item needs the Founder: `explicit-human-off` is the only accepted release policy, a release record
needs `work authorize --quote`, and the card's READY is set by hand. Decisions 1-6 replace this with one approval of an
exact plan revision, inherited by derived items, and containment so that inherited authority cannot reach outside the
assessed scope or touch what releases it.

## 2. The change: exactly the referenced prototype diff at `17910f7`

The exact change is one reviewed, immutable artifact, referenced rather than embedded (Founder 2026-10-09: Agent Ready
inputs stay semantically bounded; large diffs are referenced through immutable, provenance-bearing artifacts):

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/plan-authority-inheritance.diff`; that entry's `text` field
  holds the exact diff. (The same package the PRODUCER receives at launch; its `work context` command re-prints it.)
- **SHA-256 of those bytes (UTF-8):** `35686536f9e8dadf239fff0551d6dfe4c512f09009557a16fe3fc2c0d14a2b95` (145,435 bytes, 25 files, unified diff, `git apply` format).
- **Baseline:** main `17910f7`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 25 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `35686536f9e8dadf239fff0551d6dfe4c512f09009557a16fe3fc2c0d14a2b95`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff. The VERIFIER and the conformance
check compare the candidate's diff from the starting revision with the same context entry, ignoring only `index` lines.

Invariants the diff implements:
1. **Authority root.** `work approve-plan --commit <sha> --quote <words>` reads the canonical plan at `<sha>` (reachable
   from main), parses exactly one `alienintent-plan-authority` block (target repositories, capabilities, budget caps,
   protected paths, obligations with allowed paths and priority), records it as evidence bound to the commit and the
   `sha256:` of the file bytes, and sets `plan-authority:current`. A changed plan needs a new approval.
2. **Derived means inside an obligation.** `outside_authority(contract, authority)` gives one `owner-decision-required:`
   reason per broken rule (issuer digest, one obligation reference, repositories, capabilities, requirement ids, budget
   caps, scope under the obligation's paths in exact case, no scope entry crossing a protected path, case-folded).
   Satisfiability accepts `automatic-on` only through it.
3. **Release with no Founder words.** `work release <id>` writes the release record (baseline = default branch head),
   `approval_ref`, links the item, writes the card text, Status READY and the obligation's Priority, each read back; on
   any owner-decision reason it writes nothing but one attention item.
4. **Per-contract release, current authority only.** The registry coordinator releases by policy only items whose
   contract is `automatic-on` AND inside the CURRENT authority; `explicit-human-off` items keep the Founder release.
5. **Containment (decision 6).** For `automatic-on` items: the PRODUCER's actual diff (read by the control plane: the
   intake with a worker user, from the trusted `starting_revision`; fail closed without one) must be inside the exact
   scope and off the protected paths (symlinks, submodules, `sitecustomize.py`, `.pth`, `conftest.py` refused anywhere);
   a violation is a typed `scope-violation` PRODUCER rework, nothing published, no VERIFIER attempt. CLOSURE, at the top
   of `_order` (every first order and re-order) and before a journaled re-land, checks the diff from the actual landing
   base against the CURRENT authority (`outside_authority` and protected paths) before any landing effect; a violation is
   a typed `scope-violation` hold with the reasons, plus one owner-decision attention item when outside authority.
6. **The canonical plan** gets decision 5's sentence in section 2.2 and a new section 2.2.1 with the block: obligations
   BOUNDED-ROUTINE-LAUNCH, WORK-PREPARATION-REFILL, TERMINAL-BOARD-STATUSES, STORE-SCHEMA-HARDENING, AUTONOMY-PROOF.

What each file carries (the artifact is the authority; this list is for reasoning about it):

| File | Change |
| --- | --- |
| `docs/decisions/alienintent-v2-canonical-project-plan.md` | section 2.2 sentence replaced by decision 5; new section 2.2.1 with the one `json alienintent-plan-authority` block (5 obligations, budget caps, protected paths) |
| `src/alienintent/execution_coordination/domain/plan_authority.py` (new) | pure rule: `PlanScope`, `parse_scope`, `PlanAuthority`, path `normalized`/`under`, `outside_authority` (invariant 2) |
| `src/alienintent/execution_coordination/domain/scope_containment.py` (new) | pure rule `contained(changes, authorized_scope, protected_paths)` (invariant 5) |
| `src/alienintent/execution_coordination/domain/satisfiability.py` | `automatic-on` satisfiable only through a `plan_authority` argument with no `outside_authority` reason |
| `src/alienintent/context_assembly/application/plan_approval.py` (new) | `work approve-plan`: evidence record bound to commit + content digest, `plan-authority:current` (invariant 1) |
| `src/alienintent/context_assembly/application/inherited_release.py` (new) | `work release`: release record, link, card READY + Priority with read-back, or one owner-decision attention item (invariant 3) |
| `src/alienintent/execution_coordination/adapters/github_projects_v2.py` | `write_priority`, like `write_status` |
| `src/alienintent/execution_coordination/ports/worker_provider.py` | typed outcome `SCOPE_VIOLATION` |
| `src/alienintent/execution_coordination/application/factory_coordinator.py` | `SCOPE_VIOLATION` routed like `NO_CHANGE` to PRODUCER rework |
| `src/alienintent/invocation_runtime/ports/source_control.py`, `src/alienintent/invocation_runtime/adapters/git_source_control.py` | `raw_changes`/`changes`: `(mode, path)` pairs from `git diff --raw --no-renames` |
| `src/alienintent/invocation_runtime/application/real_worker.py` | `protected_paths` argument; containment in `_produce` from the trusted `starting_revision`, before publication |
| `src/alienintent/composition/work_registry.py` | services wired; `automatic(contract, current)` for release by policy (invariant 4); CLOSURE `_scope_violations` at the top of `_order` and in the settle retry (invariant 5) |
| `src/alienintent/control_plane/adapters/cli.py`, `src/alienintent/control_plane/application/operator.py` | `work approve-plan`, `work release` commands |
| `tools/fitness/coupling_register.json` | the new module couplings |
| the 9 test files | the tests named in section 3 |

## 3. Acceptance checks

1. **The rules**: `tests/execution_coordination/domain/test_plan_authority.py`,
   `tests/execution_coordination/domain/test_scope_containment.py`, `tests/execution_coordination/domain/test_satisfiability.py`.
2. **Approval and release**: `tests/context_assembly/test_plan_approval.py`, `tests/context_assembly/test_inherited_release.py`;
   the existing `tests/context_assembly/test_work_authorization.py` passes unchanged.
3. **Wiring and the factory path**: `tests/execution_coordination/test_containment_wiring.py` (containment before
   publication, from the trusted start; CLOSURE at the landing base before any order; current authority at the gate;
   re-land re-check), `tests/composition/test_work_registry.py` (plan-derived item assess -> release -> PRODUCER with no
   `work authorize`; an explicit item without a release never dispatched; a new approval stops an item released under
   the old one), `tests/composition/test_worker_launch.py::test_an_item_released_under_one_plan_revision_does_not_land_after_another_is_approved`.
4. **Mutations, run exactly by the VERIFIER** (each must fail its named tests and pass when reverted). Every replacement
   listed for one mutation is applied together, as that one mutation; quote test node ids in the shell (some contain spaces):
- **M1 raw startswith, no normalization (outside_authority)** (`src/alienintent/execution_coordination/domain/plan_authority.py`): `entries = [(entry, normalized(entry)) for entry in contract.authorized_scope]` -> `entries = [(entry, entry) for entry in contract.authorized_scope]`; `allowed = [normalized(path) for path in obligation.allowed_paths]` -> `allowed = list(obligation.allowed_paths)`; `for entry, path in entries if path is None or not any(under(path, a) for a in allowed)]` -> `for entry, path in entries if path is None or not any(path.startswith(a) for a in allowed)]`; `protected = [normalized(path, fold=True) for path in scope.protected_paths]` -> `protected = list(scope.protected_paths)`; `and any(under(path.casefold(), p) or under(p, path.casefold()) for p in protected)]` -> `and any(path.startswith(p) for p in protected)]` -> must fail: `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change15-crosses a protected path: docs/decisions]`, `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change16-crosses a protected path: src/alienintent]`, `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change17-crosses a protected path: src/alienintent/execution_coordination/domain/Release.py]`, `tests/execution_coordination/domain/test_plan_authority.py::test_each_single_change_is_exactly_one_owner_decision[change20-a/../docs/decisions/x is malformed]`
- **M2 automatic-on passes with no plan authority** (`src/alienintent/execution_coordination/domain/satisfiability.py`): `reasons.append("release_policy: automatic-on requires an approved plan authority")` -> `pass` -> must fail: `tests/execution_coordination/domain/test_satisfiability.py::test_automatic_on_passes_only_through_an_approved_plan_authority`
- **M3 work release skips set_evidence(approval)** (`src/alienintent/context_assembly/application/inherited_release.py`): `self.identities.set_evidence(item.id, "approval", reference)` -> `(deleted)` -> must fail: `tests/context_assembly/test_inherited_release.py::test_a_plan_derived_item_is_released_its_card_reads_back_ready_p0_and_its_producer_context_assembles`
- **M4 wrapper sets every item automatic** (`src/alienintent/composition/work_registry.py`): `return tuple(replace(item, automatic_release=automatic(item.contract, current))` -> `return tuple(replace(item, automatic_release=True)` -> must fail: `tests/composition/test_work_registry.py::test_check7_a_released_registry_item_passes_the_gate_on_the_registry_store`, `tests/composition/test_work_registry.py::test_check6_an_explicit_item_with_a_ready_card_and_no_release_record_is_never_dispatched`
- **C1 containment call removed from _produce** (`src/alienintent/invocation_runtime/application/real_worker.py`): `violations = self._scope_violations(context, reader, workspace.path, starting_revision, revision)` -> `violations = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_source_the_producer_checks_containment_before_publication`, `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published`
- **C2 CLOSURE recheck removed** (`src/alienintent/composition/work_registry.py`): `violations = self._scope_violations(clone, identity, base, revision)` -> `violations = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_source_closure_checks_containment_against_the_landing_base_before_every_order`, `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_an_automatic_on_candidate_outside_its_boundary_before_any_order`, `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_a_candidate_that_reverts_a_protected_change_main_made_after_its_release`
- **C3 symlink mode allowed** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `FORBIDDEN_MODES = {"120000": "a symbolic link", "160000": "a submodule"}` -> `FORBIDDEN_MODES = {"160000": "a submodule"}` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[symlink]`, `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published[symlink]`
- **C4 protected path allowed** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `if compared is not None and any(under(compared.casefold(), entry) for entry in protected):` -> `if False:` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[protected]`, `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published[protected]`
- **C5 containment skipped for automatic-on** (`src/alienintent/invocation_runtime/application/real_worker.py`): `or context.release_policy != "automatic-on":` -> `or context.release_policy == "automatic-on":` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_an_automatic_on_candidate_outside_its_boundary_is_never_published`, `tests/execution_coordination/test_containment_wiring.py::test_without_a_plan_authority_no_automatic_on_candidate_is_published`
- **C6 scope compared case-folded** (`src/alienintent/execution_coordination/domain/plan_authority.py`): `return stripped.casefold() if fold else stripped` -> `return stripped.casefold()` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[scope-is-exact-case]`
- **C7 protected paths compared with exact case** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `if compared is not None and any(under(compared.casefold(), entry) for entry in protected):` -> `if compared is not None and any(under(compared, entry) for entry in protected):`; `protected = [path for path in (normalized(entry, fold=True) for entry in protected_paths) if path is not None]` -> `protected = [path for path in (normalized(entry) for entry in protected_paths) if path is not None]` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[protected-ignores-case]`
- **B1 CLOSURE checks the release-baseline diff, not the landing base** (`src/alienintent/composition/work_registry.py`): `violations = self._scope_violations(clone, identity, base, revision)` -> `violations = self._scope_violations(clone, identity, self._registry.assessment.authorizations.release_authorization(identity).baseline, revision)` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_a_candidate_that_reverts_a_protected_change_main_made_after_its_release`
- **B2 worker-reported start used as the diff start** (`src/alienintent/invocation_runtime/application/real_worker.py`): `starting_tree = reader.tree(workspace.path, reader.revision(workspace.path))` -> `starting_revision = reader.revision(workspace.path)
            starting_tree = reader.tree(workspace.path, starting_revision)` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_a_worker_reported_start_cannot_narrow_the_diff`, `tests/execution_coordination/test_containment_wiring.py::test_without_a_trusted_starting_revision_no_automatic_on_candidate_is_published`
- **B3 current-authority condition removed from release-by-policy** (`src/alienintent/composition/work_registry.py`): `return contract.release_policy == "automatic-on" and current is not None \
        and not outside_authority(contract, current)` -> `return contract.release_policy == "automatic-on"` -> must fail: `tests/composition/test_work_registry.py::test_a_new_plan_approval_stops_an_item_released_under_the_old_one`
- **CD1 conftest.py allowed** (`src/alienintent/execution_coordination/domain/scope_containment.py`): `if name == CONFTEST:` -> `if False:` -> must fail: `tests/execution_coordination/domain/test_scope_containment.py::test_each_violation_is_named[conftest]`
- **BL1 outside_authority check removed from the landing gate** (`src/alienintent/composition/work_registry.py`): `outside = outside_authority(contract, current)` -> `outside = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_closure_refuses_a_candidate_outside_the_current_plan_authority_and_raises_one_owner_decision`, `tests/execution_coordination/test_containment_wiring.py::test_a_journaled_order_is_not_re_landed_after_its_plan_authority_is_replaced`, `tests/composition/test_worker_launch.py::test_an_item_released_under_one_plan_revision_does_not_land_after_another_is_approved`
- **SR settle-retry re-land check removed** (`src/alienintent/composition/work_registry.py`): `violations = self._scope_violations(clone, identity, order["base"], revision)` -> `violations = ()` -> must fail: `tests/execution_coordination/test_containment_wiring.py::test_a_journaled_order_is_not_re_landed_after_its_plan_authority_is_replaced`

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

### Stated limits (can defer, recorded in decisions section 19)
- Code that drives containment but is not on the protected list (the raw-diff parser, the intake reader, the
  satisfiability wiring) can be edited by a later obligation; the wiring tests and the regression gate catch removal.
- Without a worker user, the PRODUCER diff is read in the worker's workspace (CLOSURE's fresh clone is the backstop).
- Items stopped by a new approval in `start()` get no per-item signal (they are not eligible; `launch()` holds them typed).
- An approved plan with no protected paths cannot run automatic work (fails closed).
- Only the registry profile wires the `protected_paths` hook into the PRODUCER; the offline, sandbox and capstone
  profiles run no containment, which is safe because satisfiability refuses `automatic-on` without a plan authority.
- The NO-CHANGE tree check still reads the starting tree through the worker (pre-existing).

## 4. Evidence and review record

The prototype is exactly the referenced artifact `docs/work-units/python/plan-authority-inheritance.diff` on `17910f7` (a byte copy of
`~/.local/state/alienintent/manual/path-to-done/plan-authority/prototype-on-17910f7.diff`), sha256 `35686536f9e8dadf239fff0551d6dfe4c512f09009557a16fe3fc2c0d14a2b95`. 548 targeted tests
pass across 18 files; the fitness check passes; the 17 mutations behave as stated (`mutations.log`, run independently by
the main session). Reviews: adversarial review FAIL (B1 CLOSURE checked the release-baseline diff, B2 worker-reported
start, B3 old approvals kept running) -> fixed test-first; follow-up FAIL (BL-1: VERIFY/ACCEPT items under an old
approval could land) -> fixed at the landing gate with the re-land re-check.

**R2 (2026-10-09).** Same reviewed diff, scope, requirements and authority as #173; only the retrieval
instruction in section 2 changed (Founder decision, decisions section 21).

**Revision 3 (2026-10-09).** Rebuilt on `17910f7` from revision 2 plus the design delta
(`manual/path-to-done/plan-authority/rev3-design-delta.md`).
