# FX-R5 — attention queue migration preparation

Status: LOCAL_PREPARATION_ONLY for WO-220605/#137. #135/R3 and #134/B8 are TASKS; #136/R4 is held. No producer/consumer replacement proof or live queue migration target is bound.

Authority reconciliation: the binding [2026-09-26 Wave 2 delegation](../../decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md) disposes the recurring POSTW1-DECIDE-006A, live-proof, and attention-activation references for approved Wave 2 work within its bounds. It does not dispose #136's separate observer design question, predecessor proof, migration inventory, or this BIU's target and allocation.

## Executable local probes

Run from the repository root at the recorded source SHA. The tests use disposable `tmp_path` stores and leave the source writer in place:

```sh
python3 -m pytest -q tests/control_plane/test_attention.py
python3 -m pytest -q tests/control_plane/test_attention_acknowledgement.py
```

Record exact exit codes and case results. Named cases include `test_migration_stages_history_aliases_without_switching_writer`, `test_migration_rejects_unknown_or_conflicting_records`, `test_migration_append_and_rewrite_refusal`, `test_seen_is_not_resolved_and_decision_inbox_distinct`, `test_zero_duplicate_handling`, and `test_queue_persists_across_restart`. These are local mechanics and cannot discharge SF-REQ-053-AC-07 for the actual retained queue.

Local observation on 2026-09-28 at code baseline `4fd779843a951bbed3ca7ad09dc4a26e469e054f`: first command exit 0, 31 passed; second command exit 0, 15 passed. No retained-queue migration was run.

## Required intact, fault, restored operational contrast

After all three predecessor proofs are accepted and owner authority is bound: (1) inventory every retained pending/handled identity, aliases, actor attribution and immutable history; keep the programme mailbox separate; (2) stage the inventory with the old writer still active and compare source digests; (3) inject duplicate delivery, unavailable consumer and source append/conflict, requiring no lost pending item or double handling; (4) restart the successor and demonstrate pending consumption, SEEN versus RESOLVED distinction, liveness suppression, and readback against the same source identity; (5) restore old protection or complete only a separately authorized cutover. The actual inventory, target, command and cutover authority are **UNBOUND**. Empty queue is insufficient.

## Evidence record

Retain `FX-R5/<run-id>/execution-record.json` with `proof_level`, source/candidate/fixture SHA, #135/#136/#134 candidate and accepted-proof refs, source and staged queue digests, full pending/handled identity and alias manifests, actor attribution, programme mailbox manifest, command and exit status, notification/handling counts, writer before/after, liveness suppression readback, rollback result, old-protection readback and independent verdict ref. Preserve raw observations by SHA-256, `digest-manifest.json`, and `proven-red.json`. Unknown inventory or missing measurements are `UNKNOWN`/HOLD.
