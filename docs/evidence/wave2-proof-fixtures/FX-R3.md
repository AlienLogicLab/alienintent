# FX-R3 — SWF-29 liveness replacement preparation

Status: LOCAL_PREPARATION_ONLY for WO-220603/#135. No live target, cutover, or retirement is bound. The predecessor WO-220505/#125 remains TASKS under a Founder hold; its accepted operational proof is unavailable.

Authority reconciliation: the binding [2026-09-26 Wave 2 delegation](../../decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md) disposes POSTW1-DECIDE-006A and EXPLICIT_LIVE_TRANSPORT_PROOF_AUTHORITY for approved Wave 2 replacement work within its stated bounds. It does not supply #125's proof, this BIU's target or allocation, or a passing release admission. The older materialization's `GAP_BLOCKED` label is historical planning state.

## Executable local probes

Run from the repository root at the recorded source SHA. These commands use disposable `tmp_path` stores and do not establish the operational replacement predicate:

```sh
python3 -m pytest -q tests/execution_coordination/test_liveness_reconciliation.py
python3 -m pytest -q tests/composition/test_bounded_control_capstone.py
```

The first suite exercises policy boundary, healthy independent scan, correlated evidence, judgment suppression, delayed original/restart contention, durable effect readback, and refusal on missing authority. The second exercises episode-end duplicate/delayed outcomes, judgment attention across episode end, and stale/degraded scan reporting. Record each exact test result and exit code. A passing local suite is a local mechanics observation only.

Local observation on 2026-09-28 at code baseline `4fd779843a951bbed3ca7ad09dc4a26e469e054f`: first command exit 0, 53 passed; second command exit 0, 4 passed. No operational probe was run.

## Required intact, fault, restored operational contrast

Once #125 is DONE and a separate live target/readback, budget, and authority are bound: (1) record one known active item, writer/generation and retained attention linkage; (2) with the independent scan healthy, suppress one event trigger and require recovery within the configured G+I bound; (3) block provider or judgment and require zero unauthorized recovery actions with attributed hold; (4) deliver the delayed original across restart and require one fenced effect by durable readback; (5) restore the path and verify resolution and old protection continuity. The current target, invocation command, and expected live effect key are **UNBOUND**. No operational case has run.

## Evidence record

For any future run, retain `FX-R3/<run-id>/execution-record.json` with `proof_level`, source/candidate/fixture SHA, predecessor #125 receipt and candidate SHA, target/profile and policy digest, exact command and exit status, per-case expected/observed values, event and scan timestamps, G/I/C boundaries, application count, effect key, writer/generation, attention identity, readback ref, old-protection ref, and independent verdict ref. Raw observations belong in `observations/<sha256>` with `digest-manifest.json` and a `proven-red.json` for fault discrimination. Missing measurements are `UNKNOWN` and block an operational PASS.
