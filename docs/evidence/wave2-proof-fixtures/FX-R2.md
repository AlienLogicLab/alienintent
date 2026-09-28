# FX-R2 — Program Director bridge-waiter discharge fixture

Status: specification and local preparation only; no message is sent and no bootstrap mechanism is retired.
Prepared by Factory Director episode `factory-director-67482e852e5c455ba653cfad249963a3` on 2026-09-28.

The Founder selected the completed-programme/no-outstanding-duties alternative on Issue #131
(2026-09-28, comment 5872218987). The Wave 2 technical plan replacement table and M-R2
already permit this path. The local waiter cases below remain historical preparation, not
the operational discharge predicate.

## Completed-programme route: required inputs and commands

Pin the exact `origin/main` commit and digests of `docs/operations/post-wave1-program/program-state.json`,
`task-ledger.md`, every file under `messages/`, and `reports/FINAL-REPORT.md`. Record the
independently accepted WO-220507/B4 candidate and verdict, the WO-220601/R1 candidate and
verdict, and the Founder's Issue #131 decision. Enumerate the message directory, including
unexpected files, and reconcile every request ID, reply/correlation ID, pending entry,
handled attribution and duplicate-handling record against the programme's authoritative
terminal state. A zero count is valid only when the full inventory and source digests show it.
Record the exact inventory command, exit code, raw output digest and timestamp. Preserve
the incumbent bridge configuration and service identity; read back its continuity before
any retirement action. If an input, identity or readback is unavailable, record `UNKNOWN`
and fail the gate.

Run the inventory and reconciliation first on a read-only source snapshot. For mechanical
discrimination, copy that snapshot into a disposable directory and test: intact terminal
records pass; one injected pending duty fails; one missing or mismatched correlation fails;
one duplicate handled record fails; restoring the exact snapshot passes with the original
digests. Record each injected change and observed exit status. These disposable tests do
not establish the current operational inventory or authorize stopping the incumbent.
An independent verifier must compare the current source inventory, authority, predecessor
receipts and protection readback to this predicate on the exact candidate revision.

If a real authorized successor message consumer is later selected, pin its target and
run a separate harmless request/reply fixture with pending, restart and duplicate cases.
Do not reuse the disposable waiter as that operational target.

## Bound target

Use the existing local bridge waiter at `/home/netmarine/.local/share/alienintent-bootstrap/attention_wait.py`
and its durable attention source under the configured AlienIntent profile. The preparation fixture must run
against a disposable copy of the attention state, with the current bridge retained and untouched. No GitHub,
Project, service, or production state is a fixture input.

## Pinned cases

1. intact: one authorized synthetic attention item is observed, correlated, and acknowledged once;
2. pending restart: leave the item pending, restart only the disposable waiter process, then observe the same
   item and correlation without a second acknowledgement;
3. duplicate delivery: replay the same item and require zero second handling;
4. restored: clear the disposable state and require no residual pending item.

The producer must record the exact source/profile copy digest, fixture input digest, command, exit status,
stdout/stderr digests, and per-case observations. Missing or unavailable observations are `UNKNOWN`, never zero.

## Evidence shape

The output directory is `docs/evidence/wave2-proof-fixtures/FX-R2/<run-id>/` and contains
`execution-record.json`, `observations/<sha256>`, `digest-manifest.json`, `proven-red.json`, and an independent
verdict receipt. The record must distinguish disposable discrimination from current-source inventory and
operational protection readback. Local preparation alone cannot discharge R2 or authorize retirement.
