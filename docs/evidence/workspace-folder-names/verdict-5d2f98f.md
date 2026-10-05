ACCEPT

Fresh VERIFIER, work item 6e06e5dc-34a6-4125-b69d-bdfce0d850a8, candidate 5d2f98f2cbee27ca621027ca8a72e36fbd693b18, 2026-10-05. The VERIFIER's own report, saved unchanged below by the main session.


The candidate passes all four checks. HEAD is 5d2f98f2cbee27ca621027ca8a72e36fbd693b18 (one commit on 5dbaa09) and the worktree was clean before and after. I edited no tracked file.

Check 1, scope: all 11 changed files are in authorized_scope (7 source and tool files, 4 test files). The diff does only what section 2 lists:
- `workspace_folder` added at src/alienintent/invocation_runtime/domain/runtime.py:29, with the same rule as `ref_safe`.
- git_worktree.py:57 and :114, and the `ref_safe` docstring sentence, changed word for word as the packet says.
- real_worker.py:309, :360, :382 and :550.
- work_registry.py:560, :1037, :1502, :1515 and :1542.
- offline_proof.py:153, lifecycle_capstone.py:367 and :369, and py10_proven_red.py:133.
- One site is not listed in section 2: lifecycle_capstone.py:527 (`restarted.workspaces / workspace_folder(original)`). It reads the folder that `GitWorktreeAdapter.allocate` makes, so it counts as a reader of the same folders and is allowed.
- Minor: work_registry.py:154 imports `workspace_folder` through the real_worker module, not from domain/runtime.py. The fitness check passes with it.

Check 2, every site: I grepped src/ and tools/live/ for folders still built from a raw id. Each hit is allowed:
- Results and exports folders, which excluded_scope allows: real_worker.py:327, git_source_control.py:359, cli_worker.py:140, git_worktree.py:117, work_registry.py:1088 and :1092, and work_context.py:76.
- tools/live/worker_launch_provider_check.py:188 `verifier-{number}`: `number` is a whole-number check number, so the name has no ':'.
- tools/live/fx_b3_release_admission_proof.py:386 `probe_identity` makes an id, not a folder.
- real_worker.py:687 `self._verifier_root / verifier_invocation_id` is unchanged. The PRODUCER's claim is confirmed: `RealWorkerProvider.verify` (line 676) has no caller in src/ or tools/. The other `.verify(` hits are the cutover checkpoint `verify`, a different method.
- `candidate_clone` builds its path through `_new`, so it is covered.
- No workspace or clone folder outside the scope is named after a raw correlation id, so no stop condition applies.

Check 3, tests and fitness:
- The test command passed: 199 passed in 212 s.
- `check_architecture.py --check all`: "PASS: all architecture fitness checks", exit 0.
- On a /tmp `git worktree add --detach` copy at 5dbaa09, with the new test file copied in, all 9 tests in test_workspace_folder.py failed. The check 2 test failed for the real reason, `ModuleNotFoundError: No module named 'alienintent'` (child exit 1), not an import error of the new function. I removed the copy and pruned the worktree record.

Check 4, as alienintent-worker:
- The worktree's .git is a file, so I cloned from /home/netmarine/.local/state/alienintent/registry/clone (`--no-local`). I fetched producer/workspace-folder-names-6e06e5dc into FETCH_HEAD only, created no ref, and checked out 5d2f98f2 detached.
- run_feature_regressions.py wrote receipt.json with `"passed": true`, base 5dbaa09d…, candidate 5d2f98f2…, and receipt_digest sha256:a512115a….
- The receipt ran one pack, canonical-live-release-admission-proof (passed, exit 0). That is the only pack picked for this diff.
- I removed $F with `W rm -rf`, confirmed it is gone, and left no worker processes running.

Left unchecked:
- The last stop condition (folders with ':' for work items that have not ended under worker/, workspaces/, the verifier root or landing/). That needs the databases or journal, which I may not read.
- The receipt's single pack does not re-run the packs that failed for dc49e880. The check 2 test covers that failure directly.
- I did not run the full test suite outside the named files.
