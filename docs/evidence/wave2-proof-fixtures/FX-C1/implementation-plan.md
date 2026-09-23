# C1 implementation and proof plan

Authority: Issue #78 corrected release comment 5793830383, merged C1 packet,
allocation and FX-C1. Admission is `3d14d3004971d447bc597075f778c4aad4b037d9`;
the release advances the packet's earlier preparation baseline. The pinned source
blob and both accepted predecessor SHAs were verified locally; their independent
acceptance and closure receipts were retrieved. The durable dispatcher assignment
binds Morty, IMPLEMENT and this worktree to invocation
`AlienLogicLab/alienintent#78:PRODUCER:f4f2ffd3-6e47-4192-8fab-3766200a06e4`.
Initial tree is clean, Git/GitHub identities are Morty / morty-worker, and the
active profile binds three cycles and one replacement per phase for #78.

## Design within the approved extent

Use separate `attention:` aggregates with stable event identity, immutable
Observation history in the S1 repository, and versioned SQLite CAS pointers.
Keep typed attention values/ports in control_plane, repository and bootstrap
reader in adapters, orchestration in application, explicit dependency injection
in composition. No schema migration or existing writer modification is needed.
Resolution binds the configured resolver, authority, work revision and lane;
seen receipts never resolve. Persist notification attempts before the channel
call and correlate returned receipts; unavailable outcomes remain inspectable.
Activation is a separate, explicitly bound policy/capability; absent binding
returns a hold and does not call it. No episode implementation is added.

Migration reads a disposable snapshot of the existing append-only queue format,
retains raw bytes and original IDs/history/attribution, and stages aliases and
comparison data in a distinct namespace. It neither promotes staged records to
the active attention writer nor retires the source. Rollback retains snapshots
and aliases and reports unresolved effects; no live switchover API is supplied.

## Execution checklist

- [ ] Write `tests/control_plane/test_attention.py` for restart/dedupe, failed
  delivery and fresh consumer, guarded resolution, DecisionInbox separation,
  unbound activation, immutable history, CAS conflicts and staged migration.
  Run `python3 -m pytest -q tests/control_plane/test_attention.py` before source.
- [ ] Add typed values/ports, immutable repository and attention application;
  compose a disposable profile using existing SQLite and S1 evidence adapters.
  Run the focused tests and repair within C1 only.
- [ ] Add `tools/evidence/fx_c1_evidence.py`. In disposable source copies remove
  each identity, durable-create, consumer bridge, actor, revision, lane and
  activation guard independently. Require exactly one applied mutation, pytest
  assertion failure (exit 1), then restored exit 0. Record raw command output,
  durable readback, injected profile/input digests and measured launch count.
- [ ] Run `python3 -m pytest -q`,
  `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`
  and `node scripts/check.mjs all`. Retain command status and counts; failures
  remain failures. Keep predecessor evidence unchanged.
- [ ] Obtain read-only independent code review, repair findings, commit source,
  generate immutable FX-C1 observations against the exact committed source,
  retain them with their manifest and acceptance map in a separate evidence
  commit. Tokens/cost remain null with UNKNOWN reason where unavailable.
- [ ] Push the runtime candidate branch, read back the full SHA, and post exactly
  one invocation result comment. Retain runtime resources for independent BIU
  verification and dispatcher-owned closure; no main push or live operation.

These probes establish local composed/mechanical behavior only. S1/S2 receipts
are inputs, not self-issued independent verdicts; final VERIFY requests the fresh
invocation mandated by BIU policy.
