# MAINT-150 — keep historical resource cleanup from blocking current factory dispatch

**Issue:** AlienLogicLab/alienintent#150. **Project priority:** P0.
**Admission baseline:** `163a7fc6b5c3f3974fca5e9ee17957cbbf62b535` (`origin/main` at packet preparation, 2026-09-29).
**Authority:** delegated machinery repair under #149 and the Factory Director continuous-control obligation. The Issue is the source of this bounded task; its current body must be checked at release.

## Intent and owner boundary

Implement a restart-safe way for current authoritative Project reconciliation and listener/dispatch to proceed without waiting for the entire best-effort historical resource cleanup sweep. Assign one isolated implementation owner before source mutation. Keep the #149 worker and every retained historical worktree under their existing owners. This packet grants no new Product Requirement, Wave 2 DAG change, product priority decision, live cutover, or service restart.

## Observed fault

On 2026-09-29 UTC, `alienintent.service` remained active while `127.0.0.1:8788` refused connections and Node `active={}`. At the initial observation, the state held 332 retained resource records. The service progressed through old resource cleanup, so the observation shows startup starvation rather than a permanent deadlock. `bin/alienintent.mjs` awaits `relay.startupReconcile()` before `listen()`, and `src/runtime/dispatcher.mjs` awaits `reconcileResources()` at the end of startup. Read back the current #149 claim and listener before implementation; if the sweep has completed, retain this as recurrence prevention.

## Scope and acceptance

Limit source changes to the startup reconciliation, historical resource cleanup, and their focused tests and evidence. Preserve exact resource ownership, active-claim and supervised-unit checks, retained dirty or mismatched worktrees, diagnostics, idempotency, and refusal on ambiguous custody. Do not discard records, infer historical results, or skip cleanup permanently. Historical cleanup must remain resumable and observable with bounded work per pass and no overlapping cleanup owners.

Use discriminating tests for a large retained-resource set, slow cleanup, dirty-worktree refusal, ambiguous or live ownership, restart during a partial sweep, and repeated execution. Show that current eligible work can be admitted while cleanup remains pending, and that pending records remain available for later safe cleanup. Publish an exact candidate branch and full SHA before `RESULT=VERIFY`; independently verify that candidate and its applicable feature-regression receipt before normal landing.

## Release and operation boundaries

Run native Agent Ready on these exact document bytes after this packet is on `origin/main`, post the resulting native receipt to #150, and rerun structural release admission. The finite issue-specific execution limit is in the external self-hosting profile; the runtime enforces its loaded profile. Installed-service rollout requires a separate safe quiescent preflight and remote/readback evidence. Do not restart the current service into the same sweep, change #149's custody packet, touch #138's unknown historical outcome, or clear the separate PROCESSING delivery from this task.

General lesson: **DETERMINISTIC_PREFLIGHT** — make historical cleanup resumable without letting it block current admission, and prove the retained records survive restart.
