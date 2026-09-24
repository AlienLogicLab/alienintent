# WO-220205 R1 replacement producer receipt

Invocation: `AlienLogicLab/alienintent#97:PRODUCER:f5a03022-b0dc-4643-bd35-78bc8293ad21`.
Worker: Morty (`morty-worker`), current Codex invocation. Tokens/cost UNKNOWN.
Candidate branch: `b-disp/440039d5-1752-4c7a-940c-56672fd74445`.

## Authority and reconstruction

Issue #97 release 5814787888, JC rejection 5815345624 and Director continuation
5815964458 authorize U5 R1 repair and replacement validation/publication. The assigned
worktree began clean at `1f8648b8cc3d9aa707588ab7698ef4f7f368fb4c`. The retained repair
`98d60b004e9df9b415eaa9bbe85491654e06ae54` was merged into this invocation's own branch,
preserving its ancestry and the rejected producer evidence. Tested merge revision:
`e80ec9233bc2712359b4438732c6692062266141`. The baseline's unrelated C3 preparation
is unchanged; no C3 work was performed. No further implementation repair was needed.

U2 accepted `d0eacfb6dd8626b07ff1d99e9c633294f13d9de4` and U4 accepted
`c8ed707efdb0cd70294bfdb6814ec9f9eb71216d` are ancestors. Their Issue ACCEPT comments
5808965906 / 5814553759 and retained JC receipts `4f03da9` / `42d5219` were read.
All 13 pinned input hashes match. Original producer custody verifies 146 entries;
prior JC custody at `4dab2234ca3a139d1688bb44a1b05d01450434ac` verifies 154 entries.
No prior evidence is superseded. JC's earlier judgment and rejection remain history.

## R1 repair and replacement proof

The retained repair refuses a reviewer invocation already recorded as deciding the same
mechanical report. This durable history check prevents historical review from restoring
readiness after invalidation and re-inspection or a design revision round trip. Unchanged
VERIFIED duplicate imports remain idempotent; a fresh independent invocation can verify.
Exact revision binding, architecture holds, premise checks, append-only history and
Project lifecycle non-mutation are preserved.

The Revision 2 fixture contract and two new controls were pinned in the recovered commit
before this replacement's run. Its older invocation text is historical; this receipt and
the new report identify the replacement run. No contract semantics were changed here.

The exact independent JC oracle was retrieved from the rejected-candidate review receipt
without editing it. On the repaired service all three tests pass (exit 0). With only the
service replaced by rejected `c9a8699` bytes in a disposable source copy, it exits 1:
two controls pass and only historical replay fails (ReviewAdmitted, readiness true).
This is a producer rerun of an independent oracle, not a fresh independent verdict.

## Custody and limits

Raw observations, commands, logs, immutable evidence objects and hashes are retained in
`wo-220205-fx-u5-r2/`. SQLite operational state remains outside the repository. The harness
plan root/helpers retain original producer labels; phase observations/report carry this
replacement invocation. A fresh independent verifier must assess this exact published
candidate, including R1 and judgment applicability; no self-acceptance is claimed.

Only local proof is claimed. Direction-dependent admission continues to hold under
R2-GAP-051-EDGE-AUTHORITY. No other repository, PR, baseline push, live operation,
Project transition, provider configuration or execution limit was changed.
Runtime-managed branch/worktree retained under BIU candidate policy pending independent
VERIFY and Factory Director SWF-19 merge-at-closure/disposition. This is not LANDED.

## Fresh results

- Python suite: exit 0, **635 passed in 74.83s**.
- Architecture checks: exit 0, PASS. Required Node checks: exit 0.
- FX-U5: exit 0, **25/25 QUALIFIED_KILL**; 75 phase logs hash-verified,
  intact/fault/restored exit codes 0/1/0 and application counts 0/1/0.
  Proof-order diagnostics empty; disconnected domain control remains green.
- Independent JC oracle: repaired exit 0 (3/3), rejected-service control exit 1
  (2 pass / 1 expected regression failure).
- Retained 76 immutable objects and 76 control logs including the disconnected-domain log.
- `git diff --check`: exit 0.
