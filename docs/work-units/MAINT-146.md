# MAINT-146 — READY supply invariant closure

**Issue:** AlienLogicLab/alienintent#146. **Admission baseline:** `90d803135083e9597737a2a9647084629dc78d03` (`origin/main`, 2026-09-29). **Authority:** the bounded factory reliability repair in Issue #146 and the Founder's instruction to complete #146 before #125. This packet does not change the Wave 2 DAG or authorize other BIU work.

## Intent and ownership

Prove that READY starvation remains visible to the Factory Director while actionable supply exists. Use one isolated Producer and an independent Verifier. The Producer owns only the Director input/host supply calculation, its focused tests, and evidence for this Issue. Preserve the existing #125 parked Producer A branch, #138's unknown historical outcome, and all unrelated Issue claims and Project cards. Keep factory WIP at one.

## Existing implementation to reuse

Commit `921fdfbf3783bf73749fa3b7957fa2c88460560e` is already an ancestor of the admission baseline. It added the prepared BIU supply buffer logic and focused tests. Review and exercise that code before making any change. If it satisfies the Issue, publish an exact candidate branch and SHA with a concise no-change implementation record; do not reimplement the same behavior. Make a code repair only for a concrete failed acceptance check, in the Producer's isolated worktree.

## Acceptance and execution

Check each Issue #146 acceptance criterion against the exact candidate: HOLD and CLARIFY do not count toward prepared depth; a below-target buffer with actionable backlog keeps control required even when WIP is full; READY at zero cannot produce healthy idle while actionable supply exists; diagnostics expose actual prepared depth, target and supply candidates; focused regression tests pass. Include the live installed Director adapter readback where relevant, distinguishing observation from an independent verdict. Inspect bounded work and resource growth; do not add historical-ledger replay or unbounded retained objects.

The Producer publishes the candidate branch and full SHA before `RESULT=VERIFY`. Run applicable feature regression packs on that exact candidate and retain their passing receipt. The fresh Verifier retrieves that SHA in its own worktree, checks the five criteria and applicable antipatterns, and records concrete findings. Repair findings monotonically. Continue through normal ACCEPT, landing and authoritative Project DONE readback. An already merged implementation is evidence to reuse, not permission to skip verification or mark DONE manually.

## Release and boundaries

Run native Agent Ready against these exact bytes after this packet lands on remote `main`; post its native ASSESSED receipt to #146. Bind the receipt to this packet and the admission baseline before release. The configured finite #146 limit is `maxCycles: 3`, `maxReplacementsPerPhase: 1`; read it back from the running engine before launch. #146 currently has no parent Issue; assign and read back its own Project Priority as an explicit scheduling choice. Only then issue RELEASED and use normal READY-to-IMPLEMENT admission. Keep #125 unclaimed until #146 reaches DONE, then return to its existing P0 sequence.

No bootstrap liveness stop, protected-branch push by a BIU worker, manual runtime-state edit, #138 outcome inference, or unrelated card transition is authorized by this packet.
