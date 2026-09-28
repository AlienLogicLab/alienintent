# FX-R6 — Release-admission preparation pin

Status: preparation only; the existing release-admission protection remains in force.
Prepared by Factory Director episode `factory-director-67482e852e5c455ba653cfad249963a3` on 2026-09-28.

## Bound target

The proof target is the existing canonical live-profile prelaunch boundary exercised by the real AlienLogicLab/
alienintent Project #1 path. The fixture must use a disposable labelled probe and the configured execution profile,
with read-back of the Project item and host runtime state. It must not retire or bypass
`tools/live/release_admission.py`, launch a worker on an invalid case, or alter unrelated Project items.

## Pinned cases

For each case, the producer records the gate decision before any actor launch and the exact application count:

1. intact valid release preconditions: admission may proceed only for the labelled probe;
2. each of the six existing release preconditions absent or invalid: refusal and zero actor launches;
3. eligibility absent or invalid: refusal and zero actor launches;
4. formal release-authority closure without the required preconditions: refusal and zero actor launches;
5. restored valid probe: the exact Project and runtime read-back is reconciled, with old protection still present.

No case permits old-mechanism retirement. A missing precondition, target readback, budget dimension, or actor
count is `UNKNOWN`/HOLD rather than PASS.

## Evidence shape

The output directory is `docs/evidence/wave2-proof-fixtures/FX-R6/<run-id>/` and contains
`execution-record.json`, `observations/<sha256>`, `digest-manifest.json`, `proven-red.json`, `readback.json`, and
an independent verdict receipt. The record must bind the candidate SHA, profile/config digest, Project item,
runtime-state digest, command, exit status, and old-protection readback separately.
