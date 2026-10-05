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
  "tools/live/py10_proven_red.py",
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
  "scope outside the authorized files",
  "a folder whose name contains ':' exists under <launch>/worker, <launch>/workspaces, the verifier root or <launch>/landing for a work item that has not ended"
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
     (`f"{prefix}-{invocation_id}"`); the `ref_safe` docstring sentence "The workspace path still uses the exact identity,
     so two different invocations always get different directories; a branch name that did collide fails closed on
     `worktree add` rather than quietly sharing a branch." becomes "Workspace folders use `workspace_folder`, the same
     rule; `allocate` and `_new` refuse a path that already exists, and a branch name that collides fails closed on
     `worktree add`, so a collision never quietly shares a folder or a branch.";
   - `real_worker.py`: the `verifier-`, two `closure-` and the `producer-` read-back folders (about lines 309, 360, 382
     and 550);
   - `work_registry.py`: `_producer_worktree` (`f"{prefix}{correlation}"`, which becomes
     `f"{prefix}{workspace_folder(correlation)}"`, since its prefix already ends in `-`), `_authorize_refusal`'s PRODUCER worktree
     without a worker user (`workspaces / correlation`, about line 560, becomes `workspaces / workspace_folder(correlation)`),
     the cleanup paths
     (`f"{prefix}-{correlation}"`, two places, about lines 1502 and 1515), and the landing clone
     (`f"landing-{correlation}"`, about line 1542);
   - `offline_proof.py` (about line 152) and `lifecycle_capstone.py` (about lines 367 and 369), which rebuild the same
     paths for their proofs;
   - `tools/live/py10_proven_red.py` (about line 133), whose exact copy of the `real_worker.py` line becomes
     `'        return self._verifier_root / f"producer-{workspace_folder(invocation.correlation_id)}"',`.
   - Tests that assert the raw names change to the new form: `tests/composition/test_offline_proof.py` (about lines 116
     and 130) and `tests/composition/test_worker_launch.py` (about lines 1047, 1059 and 1099).
   The guards that refuse unsafe ids (`/`, `\`, `..`, NUL) stay as they are, and run on the correlation id first.
3. Nothing else changes. Folders that already exist for work items that have ended keep their names. At the starting
   revision no work item that has not ended has a folder whose name contains `:` (checked on 2026-10-05: the three
   such folders belong to `6cf0fee9`, `8427eb3d` and `dc49e880`, which have ended); the stop condition covers a change.

## 3. Acceptance checks

1. **One rule** (`test_workspace_folder.py`): `workspace_folder("launch:dc49e880-0de2-46fd-89a7-bf827f35cccd:2")`
   equals `"launch-dc49e880-0de2-46fd-89a7-bf827f35cccd-2"`; two different correlation ids of that form never give the
   same name; and the result never contains `:`, `/` or whitespace.
2. **The real boundary** (`test_workspace_folder.py`): create a `WorkerCloneAdapter` workspace (with the existing fake
   sudo pattern) for a correlation id containing `:`; write a minimal `src/alienintent/__init__.py` into it; run
   `sys.executable -c "import alienintent,sys; print(alienintent.__file__)"` with `cwd=tmp_path` and
   `PYTHONPATH=<workspace>/src:<workspace>`, and assert it exits 0 and prints a path under `<workspace>/src`. The same
   check in a folder named with the raw correlation id must not print a path under that folder's `src`, which shows the
   test reaches the real failure.
3. **Every site** (`test_workspace_folder.py`): for a correlation id containing `:`, the folders produced by
   `WorkerCloneAdapter` (PRODUCER, VERIFIER, CLOSURE), `RealWorkerProvider` (`verifier-`, `closure-`, `producer-`
   read-back), `_producer_worktree`, `_authorize_refusal`'s worktree, the registry cleanup and the landing clone contain
   no `:`. `_producer_worktree(...).path` equals the path `WorkerCloneAdapter.allocate` returned for the same
   correlation, and the registry cleanup removes the VERIFIER and CLOSURE clones `_new` made.
4. **Fitness**: `python -m pytest tests/invocation_runtime tests/composition/test_worker_launch.py
   tests/composition/test_offline_proof.py tests/composition/test_lifecycle_capstone.py` passes, and
   `tools/fitness/check_architecture.py --root src/alienintent --check all` passes. Also, as `alienintent-worker`
   (`sudo -n -u alienintent-worker -- env -i PATH=/usr/bin:/bin HOME=/var/lib/alienintent-worker`), in the folder
   `<launch>/worker/verifier-launch-6e06e5dc-34a6-4125-b69d-bdfce0d850a8-99` holding the candidate, the command
   `/home/netmarine/.local/state/alienintent/runtime-venv/bin/python tools/verification/run_feature_regressions.py
   --base <starting revision> --candidate HEAD --receipt <that folder>/receipt.json` writes a receipt with
   `"passed": true`; the folder is removed afterwards.

## 4. Review record

**Revision 1c (2026-10-05).** Follow-up of `df582e8`: the full `ref_safe` docstring sentence, and the
`_producer_worktree` form.

**Revision 1b (2026-10-05).** REVIEWER of `fcde7c7` (FAIL): two missed sites (`work_registry.py` about line 560;
`tools/live/py10_proven_red.py` about line 133), the `ref_safe` docstring, a stop condition for open work items with
old folders, the test lines that assert raw names, and mechanical checks 2-4.

**Revision 1 (2026-10-05).** First draft, from the VERIFY failure of `dc49e880` and the path-to-DONE walkthrough.
