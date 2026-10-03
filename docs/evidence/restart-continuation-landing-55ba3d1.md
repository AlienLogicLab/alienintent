# RESTART-CONTINUATION landing record (55ba3d1)

Restart continuation for registry launches: close the two capacity leaks, enforce one work launch at a time, resolve parked launches with `work decide`, and name every retained PRODUCER worktree. Work item `bb39a588-bf9a-4d30-b573-b8245b8979a0`. Landed by direct merge into `main`. No pull request.

## Status

Restart continuation: the two capacity leaks are closed; one work launch at a time is enforced in code; parked launches are resolved by work decide, with the remote reconciled after a possible publication; retained PRODUCER worktrees are named and reported.

## What landed

- Accepted candidate: `55ba3d17a0c13ebd579e43fcfc2d98c1d36a4a48` (branch `producer/restart-continuation-bb39a588`), built on base `86fb2fc804db329a93d391e50704222db194b7e7`.
- Candidate chain on `86fb2fc`:
  - `2f9a374`: the implementation. Rejected in VERIFIER round 1 on finding B1.
  - `7c57d25`: first B1 repair. It also changed `src/alienintent/composition/role_binding.py`, which is outside the packet's authorized scope.
  - `55ba3d1`: the B1 repair, reading the kept reason from the journal. It reverts the out-of-scope `role_binding.py` change. Accepted in round 2.
- Merge base: `origin/main` `86fb2fc804db329a93d391e50704222db194b7e7`, the same commit as the candidate's base. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/restart-continuation.md`, revision 5. It reached `main` in docs-only commit `86fb2fc`, byte-for-byte equal to packets commit `82df917` (`82df917f9fcfaf778bd4cf35c750926fd9583aaf`, sha256 `75cb433af746d23f1cf0bd4d909097ac60b6e14d8a45bb63a3d2610d0d9495ee`). Its handoff `docs/work-units/python/restart-continuation-handoff.md` is byte-for-byte equal to the copy in the registry approvals (sha256 `b4ab67a0f17a806fe492aaa4a314a554e2fb9c66019cd069abaf427a956b5fec`). The candidate changes neither.
- Scope: `git diff 86fb2fc 55ba3d1 --stat` lists 11 files (6 production, 5 test; 677 insertions, 21 deletions), all inside the packet's authorized scope. `role_binding.py` is not in the net diff. No new store, record kind, state or outcome kind.

## Approvals (private records, outside the repo; paths only)

- Work item in the permanent registry: `bb39a588-bf9a-4d30-b573-b8245b8979a0` (`~/.local/state/alienintent/registry/`).
- Agent Ready, packets commit `82df917`: READY with `work assess`, attempt `d157b4ba-a0a1-413a-9b7c-f1d00797c04b` (`readiness/bb39a588-bf9a-4d30-b573-b8245b8979a0/d157b4ba-a0a1-413a-9b7c-f1d00797c04b/raw`).
- Founder implementation approval: `~/.local/state/alienintent/registry/approvals/bb39a588-bf9a-4d30-b573-b8245b8979a0.json` (item and commit `82df917f9fcfaf778bd4cf35c750926fd9583aaf` bound; recorded 2026-10-03T16:02:58Z). Two clarifications were attached: an empty journal alone must not prove that nothing started, and retained worktrees need a named owner with the cleanup obligation carried into row 8. The reservation protection and publication reconciliation stay required acceptance checks. Implementation approval only; the work item stays at CAPTURE.
- Handoff binding both roles: `~/.local/state/alienintent/registry/approvals/bb39a588-bf9a-4d30-b573-b8245b8979a0-handoff.md`.

## Independent verification

| Round | Candidate | Packet | Verdict | Evidence | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `2f9a374` | revision 5 | REJECT | B1: handoff section 2 not met. After a restart, a parked worktree and a missing-terminal-result worktree were reported only as `retained`, with no reason; the authorized-and-relaunched case was not reported. Checks 0 and 3 met, every non-equivalent VERIFIER mutation killed. 5 changed test files 161 passed; role_binding + lifecycle_capstone 35 passed; fitness PASS. | `~/.local/state/alienintent/manual/restart-continuation-verification/round1-2f9a374/verdict.md` |
| 2 | `55ba3d1` | revision 5 | ACCEPT | B1 closed: `_kept_reason` reads the shared journal and names `parked` or `missing-terminal-result`; `work decide` records `authorized and relaunched`. Diff from `2f9a374` is 4 files in scope; `role_binding.py` not touched. VERIFIER mutation (back to `"retained"`) killed. 7 test files 196 passed; fitness PASS. | `~/.local/state/alienintent/manual/restart-continuation-verification/round2-55ba3d1/verdict.md` |

## Landing checks

- Candidate fetched from the PRODUCER worktree into a fresh closure clone of `origin`; `git rev-parse` gave `55ba3d17a0c13ebd579e43fcfc2d98c1d36a4a48`.
- `origin/main` was still `86fb2fc` at landing time, so no change on `main` since the candidate's base.
- `git diff 86fb2fc 55ba3d1 --stat` does not list `role_binding.py`.
- Merge commit: `535a85e0cafd54b67ef228cf4cb998b3726a7cb3` (first parent `86fb2fc`, second parent `55ba3d1`).
- `git diff 55ba3d1 HEAD -- src tests tools` on the merged tree: empty.

Read-back on the merged tree (not a re-verification; no full suite):

- `python3 -m pytest -q tests/execution_coordination/test_factory_coordinator.py tests/composition/test_worker_launch.py tests/invocation_runtime/test_runtime.py tests/control_plane/test_cli.py tests/invocation_runtime/test_git_source_control.py tests/composition/test_role_binding.py tests/composition/test_lifecycle_capstone.py`: 196 passed, 0 failed.
- Fitness: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all` gave `PASS: all architecture fitness checks`.

## Follow-ups

- F1 (round 1, open point b): the Founder's decision words are not kept durably on either decision path (`decisions decide` or `work decide`). Keeping them needs a new field or record kind, so its own packet.
- F2 (round 2 note): if the journal cannot be read, `_kept_reason` falls back to the reason `parked`, so a missing-terminal-result worktree would be labelled `parked`. It is still kept and reported.
- F3: a reservation whose work item is missing from the READY view still wedges recovery.
- F4: the binding-refused inbox reason.
- F5: `cancel()` passes the work identity, not the correlation.
- F6: an already published but unrecorded candidate stays parked.
- F7 (Founder 2026-10-03; path plan 4A): row 8 owns the cleanup of retained PRODUCER worktrees and of VERIFIER, read-back and CLOSURE clones.
