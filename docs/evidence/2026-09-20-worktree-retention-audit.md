# Worktree retention audit — 2026-09-20

Scope: retained dispatcher worktrees and accumulating `WORKTREE_CLEANUP_FAILED` diagnostics. Repository maintenance only; no lifecycle, Project or Node source change.

## Root cause

`worktreeManager.cleanup()` refuses to remove a worktree when

```js
run(record.path, 'status', '--porcelain=v1', '--untracked-files=all', '--ignored')
```

returns anything — and it passes **`--ignored`**. Every worktree that has run the Python suite therefore contains `.pytest_cache/` and `__pycache__/`, which are gitignored build artifacts, and is reported dirty:

```
$ git -C <worktree> status --porcelain=v1 --untracked-files=all --ignored
!! .pytest_cache/.gitignore
!! .pytest_cache/CACHEDIR.TAG
...
$ git -C <worktree> status --porcelain=v1 --untracked-files=all
(empty)
```

The worktree is clean of real content. **Gitignored artifacts alone make a worktree permanently un-removable**, so retention was unbounded rather than evidence-driven. The check cannot distinguish "worker left uncommitted work worth keeping" from "pytest wrote a cache directory".

## Inventory and classification

**45 worktrees before, 21 after.** 25 removed.

| Classification | Count | Disposition |
|---|---|---|
| ACTIVE_RUNTIME | 1 | retained — live invocation, untouched |
| MERGED_AND_SAFE_TO_REMOVE | 23 | **removed** — HEAD reachable from `origin/main` |
| Coordinator scratch (`gate_tree`, `mut`) | 2 | **removed** — created by the SWF-26 battery and this audit |
| ACCEPTED_CANDIDATE_RETENTION | 17 | retained — candidate published to `origin`, not landed; **awaiting the retention decision in [PROP-2026-0007](../proposals/PROP-2026-0007-candidate-worktree-retention.md)** |
| REQUIRED_EVIDENCE_RETENTION | 2 | retained — sole copy, reachable from **no** remote ref |
| ORPHANED | 0 | — |
| CLEANUP_FAILED (as sole classification) | 0 | every failure resolved to one of the above |
| UNKNOWN | 0 | — |

**Retained after cleanup: 21** — 17 published-but-unlanded candidates, 2 sole-copy evidence worktrees, 1 active runtime worktree.

Retention test applied per worktree: is its HEAD reachable from `origin/main` (landed), from any remote ref (durable elsewhere), or nowhere but locally (sole copy)? Plus whether real, non-ignored uncommitted content exists.

The two sole-copy retentions are PY-04 candidates the producer deliberately did **not** publish (`5d8fe09`, `62cd4f7`) — one also carries real uncommitted content. Removing either would destroy the only copy.

Each removal was re-checked immediately before deletion for (a) having become the active invocation and (b) real dirt appearing. That mattered: PY-06 transitioned PRODUCER → VERIFIER during the audit, changing which worktree was active.

## Why removal method matters

Removal used `git worktree remove`, which **deregisters and deletes**. `cleanup()` then takes

```js
if (!existsSync(record.path)) {
  if (registered) fail('registered worktree missing; retain for diagnosis');
  return { ...record, lifecycle: 'REMOVED' };
}
```

so the resource record reconciles to `REMOVED` on the next sweep. Deleting the directories with `rm -rf` instead would have left the registrations behind and converted finite noise into a **permanent** `registered worktree missing` diagnostic for each one.

`git worktree prune` reported nothing to prune: no stale registrations existed.

## Implementation debt — repeated identical diagnostics

`WORKTREE_CLEANUP_FAILED` is emitted on every reconcile sweep for every retained worktree, with no coalescing:

- **1,202 emissions today** from **43 distinct `(invocationId, error)` pairs** — roughly 28× duplication;
- 980 `dirty worktree retained`, 222 `worktree registration/branch mismatch`.

Both are **persistent conditions**, not events: the same worktree is re-examined and fails identically each sweep. The volume buried the PY-06 dropped-delivery stall in unrelated output.

No existing authority specifies diagnostic coalescing (Architecture Authority §35 requires structured logs and diagnostics but not dedup). Recorded here as **implementation debt**, not a new requirement:

1. A resource diagnostic for an unchanged persistent condition should be emitted on transition, with a repeat count or suppression window, rather than once per sweep.
2. The dirtiness test should distinguish tracked/untracked real content from ignored build artifacts, otherwise retention is decided by whether a test suite ran.

Node is frozen under Architecture Authority §42, so neither is changed there. Ownership in canonical Python:

| Debt | Owner | Why that owner |
|---|---|---|
| **A. Worktree dirtiness classification** — ignored build/test artifacts (`.pytest_cache/`, `__pycache__/`) must not by themselves mark a worktree as evidence-bearing dirty state, while real tracked/untracked unique content stays protected | **PY-06 invocation runtime**, scope item 1 (Workspace port, owner-scoped cleanup with quiescence check) | PY-06 owns workspace lifecycle and cleanup semantics in canonical Python |
| **B. Persistent diagnostic coalescing** — emit on transition with repeat-count / last-seen metadata rather than identically every sweep, preserving enough evidence to reconstruct persistence without flooding operational signal | **PY-08 Control Plane CLI**, under Architecture Authority §35 observability and SF-REQ-024 factory yield | PY-08 owns operator-facing diagnostics and status surfaces |

**PY-06 is in flight and is not amended.** Debt A is recorded here as planning input for the work that follows its acceptance; expanding a released BIU mid-cycle would violate SWF-20. Debt B is recorded in the PY-08 contract, which has not been released.

Neither requires a new Product Requirement: existing requirement and BIU authority owns both.

## Verification

- Active invocation kept its workspace throughout: directory present, PID alive, before and after.
- All 21 retained worktrees have an explicit recorded reason.
- Resource records reconciling to `REMOVED` as sweeps run (23 → 29 immediately after the audit; the remainder clear on subsequent event-driven sweeps).
- No lifecycle state, Project state, BIU contract, Node source or FactoryChecks content was modified.
