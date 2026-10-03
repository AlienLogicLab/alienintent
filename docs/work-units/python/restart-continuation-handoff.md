# Handoff for restart continuation (work item bb39a588-bf9a-4d30-b573-b8245b8979a0)

Attached to the assessed packet `docs/work-units/python/restart-continuation.md` at packets
`82df917f9fcfaf778bd4cf35c750926fd9583aaf` (sha256 75cb433a…), assessment `readiness/bb39a588-bf9a-4d30-b573-b8245b8979a0/d157b4ba-a0a1-413a-9b7c-f1d00797c04b/raw` (READY).
Founder implementation approval 2026-10-03, recorded in the work registry. Binding on both the PRODUCER and the
VERIFIER. The packet text is not changed.

## 1. An empty journal is not proof that nothing started (Founder)
For a parked correlation with no journal record, `work decide --choice authorize` is allowed only when both hold:
- the recorded launch state shows the launch was saved but never claimed by its launcher: the open decision request's
  reason is exactly the change-2 reason `launch saved but never started`, which recovery writes only after it found
  the effect `pending` and claimed it itself;
- the existing ownership check finds no process carrying that correlation's marker (`ProcOwnership.owned_work`
  empty), and the launcher that held the exclusive reservation is `terminated` (that is why recovery ran).
Otherwise `authorize` answers `START_UNPROVEN`, naming which fact is missing, and writes nothing. Test it in
acceptance check 3: an empty journal with a different park reason, or with owned work found, gives `START_UNPROVEN`.

## 2. Retained worktrees have a named owner and a cleanup obligation (Founder)
- The owner of a retained PRODUCER worktree is its launch correlation, named by its fixed path
  `<workspace root>/<correlation>` and branch `invocation/…`.
- Every retained worktree is reported in the existing `cleanup_diagnostics` with its correlation, work item and
  reason (dirty, live owner, unattested, parked, authorized and relaunched). `work decide` lists the retained worktree
  of the launch it resolves.
- Section 0's "recorded or decided" is narrowed: change 4 cleans only after a recovered PRODUCER result. The worktree
  of a parked launch that is authorized and relaunched is kept as evidence of a run that may have partly happened.
- The cleanup obligation for retained PRODUCER worktrees, VERIFIER clones, PRODUCER read-back folders and CLOSURE
  clones is carried into row 8 (path plan section 4A).

## 3. Required acceptance checks (Founder)
Acceptance check 0 (one launch at a time; recovery never releases another launch's reservation) and acceptance check
3 (publication reconciled against the remote before another attempt) are required. They cannot be waived, narrowed
or replaced by a lower-cost test.

## 4. Assessment notes passed on
- New answer codes (`LAUNCH_IN_PROGRESS`, `LAUNCH_OWNER_UNAVAILABLE`, `OWNER_STILL_RUNNING`, `START_UNPROVEN`,
  `REMOTE_UNVERIFIED`, `REMOTE_CONFLICT`, `CANDIDATE_PUBLISHED`, `NO_OPEN_DECISION`) are command answers, not
  outcome kinds; the exclusive reservation is an ordinary store reservation.
- Prove, not assume, that `_recover` is reachable in the registry profile only through `work launch` (check 0).
- Dependency 621b0120 is recorded DONE in the permanent work registry.
