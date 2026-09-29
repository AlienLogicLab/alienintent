# MAINT-151 — preserve released Project admission across listener downtime

**Issue:** AlienLogicLab/alienintent#151. **Project priority:** inherited P0 from #149.
**Admission baseline:** `5d9e4795a696982286a3c68d262472dd99810368` (`origin/main` at packet preparation, 2026-09-29).
**Authority:** delegated factory machinery repair under the Factory Director runtime contract and the bounded Issue #151 task. This packet does not create a Product Requirement or change the Wave 2 DAG.

## Intent and ownership

Give one isolated PRODUCER ownership of the Node Project admission path and focused tests. A fresh, independent VERIFIER must retrieve the published candidate branch and exact SHA in its own worktree. The Producer must not edit #125's parked Producer A workspace, the retained #138 resource, #149's worker custody, #150's cleanup repair, the separate PROCESSING delivery, or the installed service. Classify any pre-existing changes before mutation.

## Observed fault and retained evidence

The exact #149 READY-to-IMPLEMENT Project delivery was GitHub App delivery `3845384703708250112`, GUID `85d40300-bba8-11f1-89b4-6362ffb83f6a`, at 2026-09-29 01:53:11 UTC. GitHub recorded HTTP 502; a later exact redelivery returned HTTP 504. At those readbacks the delivery ledger had no GUID and no #149 claim. Preserve these observations, the later #149 result and its separately granted live recovery, and UNKNOWN where a historical effect remains unavailable. Do not replay an unrelated delivery or infer that TCP acceptance proves dispatch.

Two later Node claim readbacks showed 2/1 and 3/1 global occupancy against configured Factory WIP 1. The current `src/runtime/dispatcher.mjs` checks the lane and per-BIU cycle limits before storing a new claim, but has no global capacity guard at its synchronous check-and-reserve point. Startup reconciliation and webhook admission both reach that path. Reconstruct the exact admission ordering where possible; the source gap and occupancy do not by themselves identify one triggering event.

## Bounded implementation

Implement restart-safe, duplicate-resistant reconciliation for already RELEASED, dependency-eligible Project worker states across pre-listener startup and lost deliveries. It must use authoritative current Project and Issue identity, release evidence, configured finite per-Issue limit, dependencies, existing claim, role, owner and preflight checks. Add a global WIP check at the common synchronous reservation point used by startup, webhook and phase handoff. The authoritative capacity must come from the existing configured factory limit; refuse if it is unavailable or malformed. The check and claim write must remain under the runtime's one-writer fence. Do not start a worker directly from Director control.

Limit repository source changes to `bin/alienintent.mjs`, `src/runtime/dispatcher.mjs`, the existing Node admission/configuration path needed to carry the capacity, and focused Node tests/evidence. Any additional path requires a recorded scope reason on #151 before implementation. Keep #150 cleanup and #149 missing-unit recovery separate. Preserve persisted identities and compatibility markers.

## Acceptance and proof

Tests must show that a released transition before listener readiness, and a lost delivery, eventually cause exactly one eligible claim; repeated webhook and reconciliation calls cannot create another. Test competing starts and phase handoff at WIP 1. Unreleased, held, blocked, stale, ambiguous, missing-limit, over-WIP and conflicting-owner cases must refuse without a claim. Preserve retained resources and UNKNOWN historical outcomes. Show restart behavior and bounded work so routine admission does not replay the historical resource ledger. Record concrete claim, finite execution state, isolated worktree and preflight evidence before asserting live #149 dispatch.

PRODUCER must publish its candidate branch and full SHA before `RESULT=VERIFY`. Run every applicable feature regression pack and retain its passing receipt on the exact candidate. VERIFIER must inspect the stated refusal and resource/quality obligations, cite concrete findings, and use an independent worktree. Repair findings monotonically. Normal ACCEPT, landing and Project DONE readback remain required.

## Release and operation boundary

Run native Agent Ready on these exact document bytes after they land on remote `main`; post its native ASSESSED receipt to #151. Structural release admission must bind that receipt to this work unit and a reachable baseline. The external profile already names finite #151 limits (`maxCycles: 3`, `maxReplacementsPerPhase: 1`); recheck it before release. READY is supply, not release. Preserve the Founder-directed #125 order and its existing Producer A custody before scheduling #151. Installed-service update/restart and #149 ACCEPT re-entry require separate safe quiescent custody and live readback; this packet itself grants neither.

General lesson: **MECHANICAL_ENFORCEMENT** — global WIP must be fenced where every runtime admission path reserves a claim.
