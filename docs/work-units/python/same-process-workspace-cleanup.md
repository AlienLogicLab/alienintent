# Work unit: same-process workspace cleanup

**Label:** `SAME-PROCESS-WORKSPACE-CLEANUP` (a document label; permanent id `3e004d5d-2023-4659-9b38-59d465524d6b`).
**Status:** Revision 1, 2026-10-10. Registered 3e004d5d-2023-4659-9b38-59d465524d6b.
**Authority:** plan-derived: obligation BOUNDED-ROUTINE-LAUNCH of the canonical plan at main's tip
(`sha256:58e0991a00f8273275ae6d00d3a05d1341518260f1903c32ea03ea49413dc532`), released by `work release`.
**Starting revision:** main `c6540de`.
**Roles:** PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "3e004d5d-2023-4659-9b38-59d465524d6b",
 "version": "revision-1",
 "intent": "CLOSURE's workspace cleanup treats an earlier role whose journaled owner is the process running CLOSURE as finished (one `work run` process runs its roles in turn), so the completed earlier-role workspaces are removed, `workspaces-cleaned` reads back and the item settles DONE; an alive owner that is another process, and any marked live process, still keep their workspaces.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-10 (decisions section 34): the invariant: \"When multiple roles execute inside the same long-lived `work run` process, cleanup must distinguish 'this process is alive' from 'this earlier role still owns an active workspace.' Completed earlier-role workspaces must be reclaimable before DONE.\" The defect belongs to BOUNDED-ROUTINE-LAUNCH; the smallest plan-derived cleanup fix, with a test running VERIFIER -> CLOSURE in the same process proving the VERIFIER workspace is cleaned.",
  "Founder 2026-10-10 (plan section 2.2.1): the canonical plan at the tip of main is the live authority root; this item inherits release from obligation BOUNDED-ROUTINE-LAUNCH of that tip.",
  "Founder 2026-10-09 (decisions section 22): PRODUCER must not run the whole regression suite; the regression gate owns whole-suite execution.",
  "Founder 2026-10-10 (decisions section 28): the targeted test set is part of the Work Item's proof contract."
 ],
 "authorized_scope": [
  "src/alienintent/composition/work_registry.py",
  "tests/composition/test_bounded_routine_launch.py",
  "tests/composition/test_worker_launch.py"
 ],
 "excluded_scope": [
  "release, WIP, eligibility, role and lifecycle semantics",
  "the process ownership adapter",
  "src/alienintent/composition/landing_authority.py",
  "tools/fitness/"
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
  "the candidate's diff from the starting revision equals the exact bytes of the context package's `design_rules.authority_references` entry with path docs/work-units/python/same-process-workspace-cleanup.diff (sha256 1acd02e82b883dd9d0cd3a26b8d0d5b96966c5c1b8f39a185f8f380a505673f9), ignoring only `index` lines",
  "the mutations of the `alienintent-mutations` block are applied by the control plane's mutation harness; every one is killed"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "event-driven wakeups",
  "the PRODUCER starting revision (WORK-PREPARATION-REFILL)",
  "stopping retries of a pinned diff rejected by deterministic evidence (decisions section 33)"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "automatic-on",
 "authority_issuer": "plan-authority:sha256:58e0991a00f8273275ae6d00d3a05d1341518260f1903c32ea03ea49413dc532",
 "authority_references": [
  "docs/decisions/alienintent-v2-canonical-project-plan.md obligation:BOUNDED-ROUTINE-LAUNCH",
  "docs/work-units/python/same-process-workspace-cleanup.diff"
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
  "the `design_rules.authority_references` entry with path docs/work-units/python/same-process-workspace-cleanup.diff is absent from the context package, its text's sha256 is not 1acd02e82b883dd9d0cd3a26b8d0d5b96966c5c1b8f39a185f8f380a505673f9, or those bytes do not apply exactly at the starting revision",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

The first real `work run` to reach CLOSURE (PLAN-TIP-AUTHORITY-RUNTIME-FIX-R2, 26b4c673) merged and recorded its
landing but held at ACCEPT, `closure-receipts-incomplete`: no `workspaces-cleaned`. One `work run` process ran VERIFIER
and CLOSURE in turn, so the VERIFIER's journaled owner was the live run process itself, and `RegistryClosure._cleanup`
kept every earlier workspace whose owner is alive. Every item `work run` takes to CLOSURE would hold the same way.
Founder invariant (decisions section 34): When multiple roles execute inside the same long-lived `work run` process, cleanup must distinguish 'this process is alive' from 'this earlier role still owns an active workspace.' Completed earlier-role workspaces must be reclaimable before DONE.

## 2. The change: exactly the referenced prototype diff at `c6540de`

- **Where the bytes are:** in the Work Item context package, NOT in the repository. The package's
  `design_rules.authority_references` list has one entry whose `path` is `docs/work-units/python/same-process-workspace-cleanup.diff`; that entry's `text` field
  holds the exact diff.
- **SHA-256 of those bytes (UTF-8):** `1acd02e82b883dd9d0cd3a26b8d0d5b96966c5c1b8f39a185f8f380a505673f9` (8,701 bytes, 3 files, unified diff, `git apply` format).
- **Baseline:** main `c6540de`; the bytes apply with `git apply` at exactly that revision.
- **Scope:** exactly the 3 files of `authorized_scope`; nothing else changes.

**Do not search the repository for this artifact.** It is not in the worktree and is not on `main`. Read the exact
reviewed diff from the named context entry, verify its digest, and apply those bytes: write the entry's `text` to a file
outside the repository with no byte added or dropped, check that its SHA-256 is `1acd02e82b883dd9d0cd3a26b8d0d5b96966c5c1b8f39a185f8f380a505673f9`, run `git apply` at the
starting revision, and commit the result. Do not edit, reformat or extend the diff.

**PRODUCER: do not run the whole test suite.** Run only the test files named in section 3; the factory's
REGRESSION-GATE owns whole-suite execution (Founder rule, decisions section 22).

What the diff does:
1. `composition/work_registry.py`, `RegistryClosure._cleanup`: reads this process's owner token once
   (`ownership.current()`, None when unreadable); an earlier correlation whose journaled owner token equals it has
   returned, so it is not "owner alive"; the marked-process check (`owned_work`) still keeps any live child.
2. `tests/composition/test_bounded_routine_launch.py`: one `work run` over the real process ownership (this test
   process is the run's live owner) takes an item through PRODUCER, VERIFIER and CLOSURE; the VERIFIER clone is
   removed, `workspaces-cleaned` reads back and the item is DONE; and, the other half of the invariant, when a marked
   process of the earlier role is still alive the VERIFIER clone is kept, no receipt reads back and the item is not DONE.
3. `tests/composition/test_worker_launch.py`, case `[owner-alive]` (same test id): the alive earlier owner (this test
   process) is now another process than the one running CLOSURE, so its workspace is still kept with no receipt.

## 3. Acceptance checks

1. `tests/composition/test_bounded_routine_launch.py::test_one_run_cleans_the_workspaces_of_its_own_earlier_roles_and_settles_done`
   , `tests/composition/test_bounded_routine_launch.py::test_an_earlier_role_of_the_same_run_whose_marked_process_is_alive_keeps_its_workspace`
   and `tests/composition/test_worker_launch.py::test_cleanup_keeps_live_or_foreign_workspaces_and_then_issues_no_receipt`
   (both cases).
2. The targeted proof set (decisions section 28), every test file that exercises CLOSURE cleanup or `work run`:
   `tests/composition/test_bounded_routine_launch.py`, `tests/composition/test_worker_launch.py`, `tests/composition/test_lifecycle_capstone.py`, `tests/context_assembly/test_work_completion.py`, `tests/context_assembly/test_work_link.py`, `tests/execution_coordination/test_containment_wiring.py`, `tests/invocation_runtime/test_regression_gate.py`, `tests/invocation_runtime/test_runtime.py`, `tests/invocation_runtime/test_workspace_folder.py`.
3. **No test id disappears**: `python3 -m pytest --collect-only -q tests` at the starting revision and at the candidate;
   every id collected at the starting revision is collected at the candidate (collection only; nothing runs).
4. **Mutations**: the block below, applied by the control plane's mutation harness (each `old` exactly once in `path`;
   all edits of a mutation together; every named test fails; restored byte-exact; every named test passes).

```json alienintent-mutations
[
 {
  "name": "the run's own process counts as an alive earlier owner",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "if not running and owner_token(owner) != this and ownership.owner_state(owner)",
    "new": "if not running and ownership.owner_state(owner)"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_one_run_cleans_the_workspaces_of_its_own_earlier_roles_and_settles_done"
  ]
 },
 {
  "name": "an alive earlier owner in another process is not kept",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "owner_token(owner) != this and ownership.owner_state(owner) != \"terminated\":",
    "new": "owner_token(owner) != this and False:"
   }
  ],
  "tests": [
   "tests/composition/test_worker_launch.py::test_cleanup_keeps_live_or_foreign_workspaces_and_then_issues_no_receipt[owner-alive]"
  ]
 },
 {
  "name": "a same-process owner skips the marked-process check",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "elif ownership.owned_work(correlation, owner_token(owner)) != ():",
    "new": "elif owner_token(owner) != this and ownership.owned_work(correlation, owner_token(owner)) != ():"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_an_earlier_role_of_the_same_run_whose_marked_process_is_alive_keeps_its_workspace",
   "tests/composition/test_worker_launch.py::test_cleanup_keeps_live_or_foreign_workspaces_and_then_issues_no_receipt[marked-child]"
  ]
 },
 {
  "name": "this process is never observed",
  "path": "src/alienintent/composition/work_registry.py",
  "edits": [
   {
    "old": "            this = ownership.current()\n",
    "new": "            this = None\n"
   }
  ],
  "tests": [
   "tests/composition/test_bounded_routine_launch.py::test_one_run_cleans_the_workspaces_of_its_own_earlier_roles_and_settles_done"
  ]
 }
]
```

The whole suite at the candidate is proven by the factory's REGRESSION-GATE; the VERIFIER does not rerun it.
`python3 tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Evidence and review record

Prototype = exactly the referenced artifact on `c6540de` (byte copy:
`~/.local/state/alienintent/manual/path-to-done/same-process-workspace-cleanup/prototype-on-c6540de.diff`). Built
test-first: the new test failed on main with `closure-receipts-incomplete` (the production hold), passes with the
fix; the targeted set passes (291); 0 test ids missing against main; fitness passes; the 4 mutations
each fail their named test and pass when restored; a fresh adversarial review of the frozen diff: PASS; its one optional gap (a live marked process of an
earlier same-process role) is now a test and a mutation.
