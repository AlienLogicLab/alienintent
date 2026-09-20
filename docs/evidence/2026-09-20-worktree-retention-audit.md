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
| ACCEPTED_CANDIDATE_RETENTION | 17 | retained at audit time — candidate published to `origin`, not landed; **since removed under [SWF-30](../decisions/2026-09-20-candidate-worktree-retention.md), see "Application of SWF-30" below** |
| REQUIRED_EVIDENCE_RETENTION | 2 | retained — sole copy, reachable from **no** remote ref |
| ORPHANED | 0 | — |
| CLEANUP_FAILED (as sole classification) | 0 | every failure resolved to one of the above |
| UNKNOWN | 0 | — |

**Retained after cleanup: 21** — published-but-unlanded candidates, 2 sole-copy evidence worktrees,
1 active runtime worktree. *(Correction: the breakdown originally written here said 17 published-but-unlanded,
which sums to 20 against a stated 21. The direct recount at SWF-30 application time was 18 + 2 + 1 = 21.
See "Population count corrected" below — the discrepancy is a counting error in this table, not a
missing or unaccounted worktree.)*

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

### Debt A — resolved on landing (2026-09-20)

PY-06 reached DONE and landed as merge `896c0fe`. The canonical Python cleanup does **not** reproduce
the defect: `GitWorktreeAdapter.cleanup` in `src/alienintent/invocation_runtime/adapters/git_worktree.py`
tests quiescence with

```python
status = subprocess.run(["git", "status", "--porcelain"], cwd=workspace.path, ...)
```

— **no `--ignored`**. Gitignored build and test artifacts therefore cannot by themselves mark a
workspace as evidence-bearing, while real tracked or untracked content still retains it, which is
exactly what debt A asked for. Ownership scoping (`is_relative_to` the managed root) and the liveness
check (`/proc/<pid>`) are also present, and removal uses `git worktree remove`, so records deregister.
**Debt A is closed in canonical Python; no follow-up work is owned.** The defect remains in the frozen
Node bootstrap (Architecture Authority §42) and is not fixed there.

Debt B remains open and is carried in the PY-08 contract.

Neither requires a new Product Requirement: existing requirement and BIU authority owns both.

## Application of SWF-30 — final dispositions (2026-09-20)

The Founder approved [PROP-2026-0007](../proposals/PROP-2026-0007-candidate-worktree-retention.md)
with a clarification to condition 2, canonicalized as an amendment to **SF-REQ-007** in
[SWF-30](../decisions/2026-09-20-candidate-worktree-retention.md). The rule was then applied once to
the retained population.

### Population count corrected

The audit's classification table recorded **17** published-but-unlanded worktrees, which does not
reconcile with its own stated total of 21 retained (17 + 2 sole-copy + 1 active = 20). A direct
recount immediately before applying the rule found **21 worktrees: 18 published-but-unlanded,
2 sole-copy, 1 active** — so the published-but-unlanded class was under-counted by one. Every one of
the 21 is accounted for in the disposition table below; nothing was missing, and the Founder
instruction's "17" refers to this same class. **All 18 were evaluated**, not just 17.

PY-06 also advanced during the operation: its PRODUCER (`280b55a2`) was active when evaluation
started and had published and exited by the time it was reached, and a new VERIFIER worktree
(`9d9b4424`) was created afterwards. Neither was removed.

### Evidence gathered per worktree

- **Condition 1** — exact candidate identity = the worktree's `HEAD` commit.
- **Conditions 2 and 3** — `git ls-remote origin refs/heads/b-disp/<uuid>` resolves to that exact
  commit. Durability of that reference was checked, not assumed: the repository has
  `delete_branch_on_merge: false`, no workflow or source path deletes `b-disp/*` refs, and no
  retention window applies to them. Their retention is the repository's own, which is at least as
  strong as the local-first evidence obligation in Architecture Authority §26. They are therefore
  **not** transient branches in the sense the Founder's clarification excludes.
- **Condition 4** — genuine read-back, not a local lookup: a **bare repository with no objects** was
  created, `origin` added, each candidate branch fetched from GitHub, and the **fetched tree SHA
  compared to the local tree SHA**. 18 of 18 matched exactly.
- **Condition 5** — the dispatcher's durable `active` map was re-read immediately before each
  removal, not once at the start. This mattered again: PY-06 transitioned PRODUCER → VERIFIER during
  the operation.
- **Condition 6** — `git status --porcelain=v1 --untracked-files=all` (deliberately **without**
  `--ignored`, the flag that caused the original retention defect) empty for all 18.
- **Condition 7** — no BIU contract or decision record requires local worktree retention. The one
  case that does — PY-04's unpublished sole copies under SWF-22 — is excluded by name.

### Dispositions

| Worktree | Candidate | Invocation | Remote reference | Disposition |
|---|---|---|---|---|
| `0db48200` | `5cb53b27` | #52 PRODUCER | `origin/b-disp/0db48200-4ce9-4696-b64a-22fcafc1282e` — preserved | **removed** |
| `10cfeefc` | `a73baf72` | #52 PRODUCER | `origin/b-disp/10cfeefc-34de-4ee9-ae4e-c31a4dee0529` — preserved | **removed** |
| `178fb027` | `847c90c8` | #52 PRODUCER | `origin/b-disp/178fb027-ea2e-440f-9d28-c4f094344397` — preserved | **removed** |
| `19cdab7a` | `064432a7` | #52 PRODUCER | `origin/b-disp/19cdab7a-940b-45b6-9569-351b1343c9a0` — preserved | **removed** |
| `51f942f0` | `1b372c2a` | #52 VERIFIER | `origin/b-disp/556798a5-e858-4461-b59c-72694fc26b14` — preserved | **removed** |
| `556798a5` | `1b372c2a` | #52 PRODUCER | `origin/b-disp/556798a5-e858-4461-b59c-72694fc26b14` — preserved | **removed** |
| `97729731` | `d9537d1e` | #54 PRODUCER | `origin/b-disp/97729731-1dc3-4334-b622-12bfe2807d36` — preserved | **removed** |
| `9a45c5a9` | `f95199e6` | #52 PRODUCER | `origin/b-disp/9a45c5a9-7ea7-49a7-9b61-32c833a2202c` — preserved | **removed** |
| `a3f6708a` | `5b1e3b32` | #2 PRODUCER | `origin/b-disp/a3f6708a-6b31-4bf2-8459-95f1dd3763d0` — preserved | **removed** |
| `aa564910` | `38a317fc` | #54 PRODUCER | `origin/b-disp/aa564910-2d79-4f6b-bf4f-e7d2f35315e5` — preserved | **removed** |
| `ac445ca0` | `c14beb6e` | #52 PRODUCER | `origin/b-disp/ac445ca0-1bd0-418b-9582-951317728380` — preserved | **removed** |
| `bf5a33e9` | `e0709658` | #54 PRODUCER | `origin/b-disp/bf5a33e9-9419-4faf-ae13-da909d217aea` — preserved | **removed** |
| `bfb7f742` | `468cb562` | #52 PRODUCER | `origin/b-disp/bfb7f742-0017-4d1e-9160-8f5a39fd4441` — preserved | **removed** |
| `c76799ea` | `deb4da34` | #53 PRODUCER | `origin/b-disp/c76799ea-cffa-4d68-a636-3b4d4de8d722` — preserved | **removed** |
| `cd1d6d6f` | `10fb82ef` | #52 PRODUCER | `origin/b-disp/cd1d6d6f-fcb4-4dec-be97-5a183762eda2` — preserved | **removed** |
| `cfa85fcf` | `468cb562` | #52 VERIFIER | `origin/b-disp/bfb7f742-0017-4d1e-9160-8f5a39fd4441` — preserved | **removed** |
| `eb5309f4` | `a7549b38` | #54 PRODUCER | `origin/b-disp/eb5309f4-e4e0-4ec0-a734-6c77f9abd84e` — preserved | **removed** |
| `f9801afa` | `064432a7` | #52 VERIFIER | `origin/b-disp/19cdab7a-940b-45b6-9569-351b1343c9a0` — preserved | **removed** |
| `280b55a2` | `e6607486` | #54 PRODUCER | `origin/b-disp/280b55a2-…` (published after evaluation) | retained — condition 5 — it was the **active** PY-06 PRODUCER worktree when the rule was applied (pid 550929, `IMPLEMENT`). The producer has since published `e6607486` and PY-06 moved to `VERIFY`; it is now the candidate under verification. Left untouched; routine cleanup will re-evaluate it after PY-06 reaches a terminal state. |
| `3da684ca` | `5d8fe096` | #52 PRODUCER | none | retained — conditions 2, 3, 4 — candidate reachable from **no** remote ref (sole copy); excluded by SWF-30 and [SWF-22](../decisions/2026-09-20-py04-custody-transfer.md) ; also condition 6 — real uncommitted content |
| `bdb4f6ba` | `62cd4f70` | #52 PRODUCER | none | retained — conditions 2, 3, 4 — candidate reachable from **no** remote ref (sole copy); excluded by SWF-30 and [SWF-22](../decisions/2026-09-20-py04-custody-transfer.md) |

**18 removed, 3 retained.** A fourth worktree (`9d9b4424`, the PY-06 VERIFIER) was created by the
factory *after* evaluation began and was never touched; it holds no candidate of its own.

### Guarantees checked after the fact

- **Every remote reference was preserved.** After each removal, `git ls-remote` was re-run against
  `origin` and confirmed the branch still resolves to the same candidate commit. 18 of 18 confirmed.
  No branch was deleted, force-updated or pruned.
- **No sole copy was removed.** The only three candidates reachable from no remote ref
  (`5d8fe096`, `62cd4f70`, and `e6607486` at evaluation time) were all retained.
- **Removal used `git worktree remove`**, so each registration is deregistered and the resource
  record reconciles to `REMOVED` rather than becoming a permanent `registered worktree missing`
  diagnostic.
- **PY-06 was not disturbed.** Its active worktree was untouched, its running worker was not
  signalled, and no lifecycle or Project state was changed.

## Verification

- Active invocation kept its workspace throughout: directory present, PID alive, before and after.
- Every retained worktree has an explicit recorded reason, at both the audit and the SWF-30
  application (4 retained at the end: 1 active VERIFIER, 1 just-published PY-06 producer copy,
  2 sole-copy PY-04 evidence worktrees).
- Resource records reconciling to `REMOVED` as sweeps run (23 → 29 immediately after the audit; the remainder clear on subsequent event-driven sweeps).
- No lifecycle state, Project state, BIU contract, Node source or FactoryChecks content was modified.
