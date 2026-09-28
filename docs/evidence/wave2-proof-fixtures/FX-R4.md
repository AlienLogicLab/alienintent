# FX-R4 — SWF-27 observer preparation pin

Status: preparation only; no observer cutover or retirement is performed.
Prepared by Factory Director episode `factory-director-67482e852e5c455ba653cfad249963a3` on 2026-09-28.

## Bound target

The existing `alienintent-observer.service` is the retained observer and remains active. The preparation
fixture uses a disposable state root and the already implemented observer/trajectory interfaces; it must not
read or mutate the resident factory `state.json`, Project #1, or the observer's live data. The external observer
remains the governing mechanism until a reviewed design explicitly replaces it.

## Pinned cases

1. intact capture: ordered records with identity, timestamp, anomaly and retention fields survive a process
   restart;
2. fault: inject a bounded write/consumer interruption in the disposable root and require the record to remain
   pending rather than disappear;
3. restored: resume consumption and require each record to be delivered once, in order, with no loss;
4. cutover contrast: compare two disposable generations and require the queue and identity continuity to be
   preserved. This is a contrast only, not a live cutover.

The producer must record exact source/profile/fixture digests, process and systemd observations, command exit
status, and independent verdict inputs. Unavailable measurements remain `UNKNOWN`.

## Evidence shape

The output directory is `docs/evidence/wave2-proof-fixtures/FX-R4/<run-id>/` and contains
`execution-record.json`, `observations/<sha256>`, `digest-manifest.json`, `proven-red.json`, and an independent
verdict receipt. No output may claim observer replacement, live no-loss, or retirement.
