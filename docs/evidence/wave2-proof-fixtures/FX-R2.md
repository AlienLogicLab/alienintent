# FX-R2 — Program Director bridge-waiter preparation pin

Status: preparation only; no message is sent and no bootstrap mechanism is retired.
Prepared by Factory Director episode `factory-director-67482e852e5c455ba653cfad249963a3` on 2026-09-28.

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
verdict receipt. The record must state that this is a local preparation/operational proof candidate and cannot
discharge R2 or authorize retirement.
