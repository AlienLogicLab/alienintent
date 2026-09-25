# External bootstrap custody refresh

Date: 2026-09-25

Status: **read-only custody evidence; no migration, deletion, service change or retirement authority.**

## Why this refresh exists

Wave 2 candidate B0 was compiled against a snapshot naming eighteen Python modules under the external AlienIntent bootstrap directory. Current readback shows that directory has grown beyond the historical eighteen, while the original files now fall into materially different categories: live services, live support libraries, tests, historical evidence utilities, and protection code that now has an in-repository successor.

The correct custody problem is therefore **per component**, not one all-or-nothing Founder decision.

## Current operational observations

Current process readback shows two long-lived Python processes executing directly from the external bootstrap directory:

- **liveness.py** — still-running temporary actor/effect liveness protection.
- **observer.py** — still-running deterministic lifecycle observer.

The external **attention.py** library is imported by both liveness and observer and is therefore part of the current live protection chain. It also drives the bootstrap notification path through **notify_founder.py**.

The session-bound **attention_wait.py** is not a long-lived service at this readback, but remains a temporary wake/attention bridge whose retirement is separately gated by successor attention handling.

## Historical / evidence utilities

No long-lived process was observed for:

- cycle_data.py
- py05_py09_quality.py
- py05_py09_trajectory.py
- py10_preflight.py
- trajectory_consistency.py
- their corresponding test files

These files are primarily retained Wave-1 evidence/proof utilities. They are candidates for **provenance-preserving repository custody**, not candidates for blind deletion. Any migration should retain exact source bytes or hashes and update historical documentation references without rewriting the historical evidence.

## Release admission

The external bootstrap contains **release_admission.py** and its test.

The repository now also contains the canonical current implementation and regression coverage under:

- tools/live/release_admission.py
- tools/live/test_release_admission.py
- tools/live/test_release_admission_release_point.py

Therefore release admission is no longer an ownership mystery. It is a **replacement-proof / live-boundary migration problem**. The external copy should remain available until the canonical live replacement gate proves equivalent behavior at the actual release boundary.

## The external directory has expanded

Current readback also found assets not present in the historical eighteen-module B0 list, including:

- factory_status.sh
- project_add_recovery_probe.sh
- worker_credential_probe.sh
- factory-director-host/ directory

At least the project-add recovery probe and Factory Director Host are referenced by user-level service definitions.

Therefore a fixed list of the historical eighteen files is no longer a sufficient current custody inventory.

## Grooming disposition for B0

The current B0 authority gate is too broad.

B0's actual job is to inventory external bootstrap assets, identify consumers and provenance, and obtain truthful per-component custody dispositions. It should **not** be blocked by the entire POSTW1-DECIDE-006A bundle, which also contains unrelated questions about provider choice, coordinator tenure, notification risk and sandbox infrastructure.

Revised B0 planning should separate four activities:

1. **Read-only current inventory and custody classification** — may proceed under existing operational/read authority.
2. **Provenance-preserving migration of historical utilities** — repository custody where useful, without changing historical meaning.
3. **Live replacement proof** — required for currently active protections before retirement or cutover.
4. **Explicit risk/retirement decisions** — only for components whose removal changes current behavior and whose replacement/expiry rule does not already decide the outcome.

Unknowns should block only the affected component/replacement path, not the entire inventory exercise.

## Initial custody classes

| Component group | Current direction |
|---|---|
| liveness.py + suppression tests | **KEEP UNTIL CANONICAL SF-REQ-056 LIVE REPLACEMENT IS PROVEN** |
| observer.py | **KEEP UNTIL CANONICAL TRAJECTORY/MONITOR REPLACEMENT IS PROVEN** |
| attention.py + live attention support | **KEEP UNTIL ATTENTION IDENTITY/HISTORY/CONSUMER MIGRATION IS PROVEN** |
| attention_wait.py | **KEEP UNTIL SUCCESSOR ATTENTION HANDOFF/TENURE PROOF OR EXPLICIT RETIREMENT** |
| notify_founder.py | **SEPARATE NOTIFICATION RISK/REPLACEMENT DISPOSITION** |
| external release_admission.py | **KEEP UNTIL IN-REPO LIVE-BOUNDARY REPLACEMENT PROOF** |
| cycle/trajectory/quality/preflight/consistency utilities + tests | **REPOSITORY-CUSTODY / HISTORICAL-ARCHIVE CANDIDATES; NO LIVE PROCESS OBSERVED** |
| newly discovered shell helpers / Factory Director Host | **INVENTORY SEPARATELY; DO NOT FORCE INTO HISTORICAL EIGHTEEN-MODULE ASSUMPTIONS** |

No file or service was changed by this evidence pass.
