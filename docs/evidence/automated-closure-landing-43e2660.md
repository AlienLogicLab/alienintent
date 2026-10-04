# AUTOMATED-CLOSURE landing record (43e2660)

Automated closure as a launched step: the control plane orders CLOSURE after an ACCEPT, the Landing Authority lands or refuses, and recovery settles a journaled order after a crash. Work item `0677f8bb-71c2-4c62-8b4a-d0e5318ba689`. This is the last manual CLOSURE for row 8. Landed by direct merge into `main`. No pull request.

## Status

Automated closure is built and verified offline. Landing is disabled (no landing flag); the factory App's permissions are unchanged and show no contents access; operating-system credential separation is the next prerequisite unit. Real-use evidence is ready-to-land only.

## What landed

- Accepted candidate: `43e2660b643be0fb65fcd80c081a27f2eba59e00` (branch `producer/automated-closure-0677f8bb`), built on base `942f393b13647b6b300cd3d25b74dec607afcef4`.
- Candidate chain on `942f393`:
  - `d63c10d`: the implementation (PRODUCER).
  - `e09d59d`: three tests added. Rejected in VERIFIER round 1 on finding B1, a test gap.
  - `43e2660`: two tests added for B1 (test-only). Accepted in round 2.
- Merge base: `origin/main` `942f393b13647b6b300cd3d25b74dec607afcef4`, the same commit as the candidate's base. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/automated-closure.md`, revision 7, at packets commit `7cedff1` (`7cedff1c3dc2932022e988a03767cbb94bbc73b0`). It reached `main` in docs-only commit `942f393`, with its handoff `docs/work-units/python/automated-closure-handoff.md`. The candidate changes neither.
- Scope: `git diff 942f393 43e2660 --stat` lists 18 files (10 production, 8 test; 2230 insertions, 89 deletions), all inside the packet's authorized scope (round 1 verdict, check "Scope").

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `0677f8bb-71c2-4c62-8b4a-d0e5318ba689` (`~/.local/state/alienintent/registry/`).
- Agent Ready, packets commit `7cedff1`: READY with `work assess`, attempt `1c8053d4-cbbc-47ef-adc2-f58019883e7a` (`readiness/0677f8bb-71c2-4c62-8b4a-d0e5318ba689/1c8053d4-cbbc-47ef-adc2-f58019883e7a/raw`).
- Founder implementation approval: `~/.local/state/alienintent/registry/approvals/0677f8bb-71c2-4c62-8b4a-d0e5318ba689.json` (item and commit `7cedff1c3dc2932022e988a03767cbb94bbc73b0` bound; recorded 2026-10-04T04:59:28Z). Implementation approval only, on the manual release path; the work item stays at CAPTURE. Landing must not be enabled.
- Handoff binding both roles: `~/.local/state/alienintent/registry/approvals/0677f8bb-71c2-4c62-8b4a-d0e5318ba689-handoff.md`.

## Independent verification

| Round | Candidate | Packet | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `e09d59d` | revision 7 | REJECT | B1: the main-moved rework path in `RegistryClosure._settle` after a journaled order had no test. Mutation V10 (rework replaced by a `base-unstable` hold, check 12's named wrong implementation) passed all 226 tests. Checks 8 (third crash case) and 12 not caught there. Behaviour itself correct; repair is test-only. | `~/.local/state/alienintent/manual/automated-closure-verification/round1-e09d59d/verdict.md` |
| 2 | `43e2660` | revision 7 | ACCEPT | B1 closed: diff from `e09d59d` is only `tests/composition/test_worker_launch.py` (49 insertions). Two new tests cover check 12 and check 8's third bullet. V10 now fails exactly those two tests. test_worker_launch + test_landing_authority 65 passed; fitness PASS. | `~/.local/state/alienintent/manual/automated-closure-verification/round2-43e2660/verdict.md` |

## Landing checks

- Candidate fetched from the PRODUCER worktree into a fresh closure clone of `origin`; `git rev-parse` gave `43e2660b643be0fb65fcd80c081a27f2eba59e00`.
- `origin/main` was still `942f393` at landing time, so no change on `main` since the candidate's base.
- Merge commit: `bb2398fe28abdc233bfb5323cd6af8862dba1bb7` (first parent `942f393`, second parent `43e2660`).
- `git diff 43e2660 HEAD -- src tests tools` on the merged tree: empty.

Read-back on the merged tree (not a re-verification; no full suite):

- `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py tests/composition/test_worker_launch.py tests/composition/test_landing_authority.py tests/composition/test_role_binding.py tests/invocation_runtime/test_runtime.py tests/installation/test_installation_credentials.py tests/context_assembly/test_work_context.py tests/context_assembly/test_work_completion.py tests/execution_coordination/test_role_orchestration.py tests/composition/test_sandbox_run_profile.py tests/composition/test_offline_proof.py tests/composition/test_lifecycle_capstone.py tests/context_assembly/test_work_link.py tests/composition/test_work_registry.py`: 477 passed, 0 failed.
- Fitness: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` gave `PASS: all architecture fitness checks`.

## Follow-ups

- F1: CLOSURE's own `work context` call fails, because `operator.py` passes the workspace only for the VERIFIER (out of scope for this packet).
- F2: the receipt format is repeated in `real_worker.py`.
- F3: `WorkCompletion` has a `fetch=` keyword.
- F4: check 17 is waiting on the section 1 prerequisites.
- F5: the factory App needs `contents: write` as well as the protected-main bypass.
