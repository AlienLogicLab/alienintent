# FX-R7 — Node/bootstrap execution authority preparation

Status: LOCAL_PREPARATION_ONLY for WO-220607/#139. #138/R6 is DONE; #135/R3, #136/R4, #137/R5 and #132/B6 are not DONE. No specific live cutover target or window is bound. The Node/bootstrap writer stays in place.

Authority reconciliation: the binding [2026-09-26 Wave 2 delegation](../../decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md) disposes POSTW1-DECIDE-006A, EXPLICIT_SOVEREIGNTY_CUTOVER_AUTHORITY, EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY, EXPLICIT_FUTURE_RELEASE_AUTHORITY, SWF-21_SCOPE_DISPOSITION and ATTENTION_ACTIVATION_AUTHORITY for approved Wave 2 work within its stated bounds. It does not bind this BIU's live profile/window, authorize dual writers, or discharge predecessor and rollback proof.

## Executable local probes

Run from the repository root at the recorded source SHA. These tests operate on isolated temporary roots and do not touch the configured live state:

```sh
python3 -m pytest -q tests/execution_coordination/test_one_writer_cutover.py
python3 -m pytest -q tests/execution_coordination/test_fenced_store.py
```

Record exact exit codes and case results. The cases discriminate live-path isolation, no-authority refusal, quiescence blockers, checkpoint tamper, record reconciliation, one-writer admission races, rollback without redispatch, and fenced-store rejection. A local cutover rehearsal is not Node-independent live self-hosting proof.

Local observation on 2026-09-28 at code baseline `4fd779843a951bbed3ca7ad09dc4a26e469e054f`: first command exit 0, 10 passed; second command exit 0, 44 passed. No live cutover was run.

## Required intact, fault, restored operational contrast

Only after every predecessor is DONE with accepted proof, exact live profile, budget, full-suite scope and explicit cutover authority: (1) inventory every active Node claim and external effect and verify a consistent checkpoint of both stores; (2) require quiescence and single-writer admission before changing writer epoch; (3) prove a live Python-controlled factory cycle with independent readback while Node dispatch of the same work is refused; (4) inject failure and restore from the retained checkpoint without redispatch of completed effects; (5) run the full required suite, read back continuity and obtain independent verdict before any incumbent retirement. The live commands, target, cutover window and authority are **UNBOUND**. No operational case has run.

## Evidence record

Retain `FX-R7/<run-id>/execution-record.json` with `proof_level`, source/candidate/fixture SHA, all predecessor candidate/proof refs, live profile and writer epoch, Node/Python process and claim inventory, external-effect ledger, checkpoint manifests and digests, exact command and exit status, single-writer refusal counts, full-suite results, rollback and old-protection readback, and independent verdict ref. Preserve raw observations by SHA-256, `digest-manifest.json`, and `proven-red.json`. Missing proof or counts are `UNKNOWN`/HOLD, never PASS.
