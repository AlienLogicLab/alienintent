# Work unit: workspace and clone folder names safe in every path list

**Label:** `WORKSPACE-FOLDER-NAMES` (a document label; permanent id `6e06e5dc-34a6-4125-b69d-bdfce0d850a8`).
**Status:** Draft revision 1 (work item `6e06e5dc-34a6-4125-b69d-bdfce0d850a8`, at CAPTURE) for independent review, 2026-10-05. Not approved, not assessed, not released.
**Position on the path:** blocks every code work item from passing VERIFY. Built outside the factory (its own VERIFIER
would fail the same way): one PRODUCER, one fresh VERIFIER on the exact candidate, direct merge to `main`.
**Roles:** PRODUCER (self-reviews the complete diff); fresh VERIFIER on the exact candidate; CLOSURE by direct merge.

## Contract

```json alienintent-contract
{
 "identity": "6e06e5dc-34a6-4125-b69d-bdfce0d850a8",
 "version": "revision-1",
 "intent": "Make every workspace and clone folder the runtime names after a correlation id use one safe form, with only letters, digits, '.', '_' and '-', so a folder path never contains ':' and stays valid inside PYTHONPATH, PATH and any other ':'-separated list that tests or tools build from it.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-05: fix the whole class at its one source, with a test of the real boundary; do not patch the 53 test files that build PYTHONPATH from the workspace path.",
  "Founder 2026-10-05: no new architecture; remove only what blocks the path to DONE."
 ],
 "authorized_scope": [
  "src/alienintent/invocation_runtime/domain/runtime.py",
  "src/alienintent/invocation_runtime/adapters/git_worktree.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/composition/offline_proof.py",
  "src/alienintent/composition/lifecycle_capstone.py",
  "tests/invocation_runtime/test_workspace_folder.py",
  "tests/invocation_runtime/test_runtime.py",
  "tests/invocation_runtime/test_git_source_control.py",
  "tests/invocation_runtime/test_owned_work.py",
  "tests/invocation_runtime/test_real_worker_outcome.py",
  "tests/composition/test_worker_launch.py",
  "tests/composition/test_offline_proof.py",
  "tests/composition/test_lifecycle_capstone.py"
 ],
 "excluded_scope": [
  "the 53 test files that build PYTHONPATH from the workspace path",
  "correlation ids, the journal, results, exports, candidate branch names and the hand-over bundle name",
  "renaming or deleting folders that already exist for work items that have ended",
  "any other behaviour change"
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
  "check 2 fails on the starting revision and passes on the candidate"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a general path-safety framework"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/worker-credential-boundary.md"
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
  "a site in section 2 does not exist at the starting revision",
  "a workspace or clone folder is named after a correlation id by code outside the authorized scope",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

Correlation ids look like `launch:<work item id>:<version>`. The runtime names workspace and clone folders after them,
for example `<launch>/worker/verifier-launch:<id>:2`. 53 test files start child Python processes with
`PYTHONPATH=<workspace>/src:<workspace>`, and Python splits `PYTHONPATH` at every `:`, so in such a folder the child
cannot import `alienintent`. Work item `dc49e880` failed VERIFY this way: 2 of 4 feature-regression packs failed in
`verifier-launch:…:2`, and the same tests pass as `alienintent-worker` in a folder without `:`.

## 2. The change

1. **One function** in `src/alienintent/invocation_runtime/domain/runtime.py`:
   `workspace_folder(correlation: str) -> str`. It replaces every character outside `[A-Za-z0-9._-]` with `-`, strips
   leading and trailing `.` and `-`, and answers `"invocation"` if nothing is left: the same rule as `ref_safe` in
   `git_worktree.py`. `ref_safe` stays as it is.
2. **Every site that names a folder after a correlation id uses it.** The form is `f"{prefix}-{workspace_folder(c)}"`,
   or `workspace_folder(c)` where there is no prefix today:
   - `git_worktree.py`: `GitWorktreeAdapter.allocate` (`self._root / invocation_id`) and `WorkerCloneAdapter._new`
     (`f"{prefix}-{invocation_id}"`);
   - `real_worker.py`: the `verifier-`, two `closure-` and the `producer-` read-back folders (about lines 309, 360, 382
     and 550);
   - `work_registry.py`: `_producer_worktree` (`f"{prefix}{correlation}"`), the cleanup paths
     (`f"{prefix}-{correlation}"`, two places, about lines 1502 and 1515), and the landing clone
     (`f"landing-{correlation}"`, about line 1542);
   - `offline_proof.py` (about line 152) and `lifecycle_capstone.py` (about lines 367 and 369), which rebuild the same
     paths for their proofs.
   The guards that refuse unsafe ids (`/`, `\`, `..`, NUL) stay as they are, and run on the correlation id first.
3. Nothing else changes. Folders that already exist for work items that have ended keep their names.

## 3. Acceptance checks

1. **One rule** (`test_workspace_folder.py`): `workspace_folder("launch:dc49e880-0de2-46fd-89a7-bf827f35cccd:2")`
   equals `"launch-dc49e880-0de2-46fd-89a7-bf827f35cccd-2"`; two different correlation ids of that form never give the
   same name; and the result never contains `:`, `/` or whitespace.
2. **The real boundary** (`test_workspace_folder.py`): create a `WorkerCloneAdapter` workspace (with the existing fake
   sudo pattern) for a correlation id containing `:`; copy or link a minimal `src/alienintent/__init__.py` into it; start
   `sys.executable -c "import alienintent"` with `PYTHONPATH=<workspace>/src:<workspace>`. It must exit 0. The same
   check against a folder named with the raw correlation id must exit non-zero, which shows the test reaches the real
   failure.
3. **Every site** (`test_workspace_folder.py`): for a correlation id containing `:`, the folders produced by
   `WorkerCloneAdapter` (PRODUCER, VERIFIER, CLOSURE), `RealWorkerProvider` (`verifier-`, `closure-`, `producer-`
   read-back), `_producer_worktree`, the registry cleanup and the landing clone contain no `:`. Recovery and cleanup find
   the folders that allocation created.
4. **Fitness**: `python -m pytest tests/invocation_runtime tests/composition/test_worker_launch.py
   tests/composition/test_offline_proof.py tests/composition/test_lifecycle_capstone.py` passes, and
   `tools/fitness/check_architecture.py --root src/alienintent --check all` passes. Also, as `alienintent-worker`, the
   feature-regression runner passes on the candidate in a folder named exactly as the new rule names a VERIFIER
   workspace.

## 4. Review record

**Revision 1 (2026-10-05).** First draft, from the VERIFY failure of `dc49e880` and the path-to-DONE walkthrough.
