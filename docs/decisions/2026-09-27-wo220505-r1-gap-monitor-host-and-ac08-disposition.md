# WO-220505 R1-GAP-MONITOR-HOST disposition and SF-REQ-056-AC-08 clarification

Date: 2026-09-27. Status: **Founder decision — binding**.

Recorded via Director inbox handoff `founder-authorize-full-biu-unblock-20260927T0202Z`
(2026-09-27T02:01:41Z, relayed by a Founder-authorized observing session (ChatGPT), not
acting as Factory Director, "relaying direct Founder decision verbatim"). This channel and
phrasing match the precedent already accepted and acted on for
`founder-wave2-authority-delegation-20260926T200500Z` (see
[2026-09-26-wave2-bounded-operational-authority-delegation.md](2026-09-26-wave2-bounded-operational-authority-delegation.md))
and `founder-authorize-local-live-proof-target-20260927T0102Z`.

## Decision

This decision answers, narrowly, the four owner-level clarifications the native Agent
Ready assessment of WO-220505 (Issue #125) returned CLARIFY on
(`docs/evidence/wave2-readiness-assessments/WO-220505.2026-09-27T015036.183383Z.assessment.json`):

1. **R1-GAP-MONITOR-HOST / DESIGN_CANDIDATE_WITH_SPECIFY_HOLD, scoped to this
   composition only.** The Founder disposes this gap for the specific composition SF-REQ-056's
   design contract binds to hosting (`docs/evidence/wave2-design-contracts.md:995`) —
   `alienintent.composition.monitor_host` wrapping `LivenessProfile` /
   `CanonicalEffectAdmission` / `LivenessReconciler` over `SQLiteOperationalStore`, supervised
   by real `systemd --user` via `MonitorHostProfile`/`SystemdHostManager` — based on WO-220305
   (Issue #114, Project #1 status DONE) having built exactly that composition, and on the
   current supervisor evidence that `systemd --user` already supervises the sibling
   `alienintent.service`/`alienintent-observer.service` units on the same host (ALIENLAPTOP)
   through the identical mechanism. Hosting/supervision is therefore no longer "unassigned"
   (`docs/evidence/wave2-design-contracts.md:999`) for this composition.

   This disposition is **narrow**: it does not claim the SF-REQ-056-AC-08 live-workload
   proof is already complete (see point 2), and it does **not** dispose R1-GAP-MONITOR-HOST
   for any other node that references it — the general gap record
   (`docs/evidence/wave2-design-contracts.md:65-120`) and the separate SF-REQ-053 Authority
   line (`docs/evidence/wave2-design-contracts.md:969`) are unchanged and continue to govern
   every other affected node (the C-series and B-series nodes, including C5 itself, already
   tracked as DONE via WO-220305). Only the WO-220505/SF-REQ-056 Authority paragraph is
   updated to record this disposition, citing this decision.

2. **SF-REQ-056-AC-08 "that workload" meaning.** Phase 1 (the isolated FX-B2 fixture against
   the synthetic `FX-B2-PROBE-<launch-id>` record) does not satisfy AC-08 and is not grounds
   for any SWF-29 bootstrap-retirement claim. Phase 2 must exercise the actual live factory
   workload, with a true readback of the result, before AC-08 is closed or bootstrap
   retirement is declared. This decision does not itself name or bind the exact phase-2
   target; that remains open and is not required to unblock phase 1.

3. **Relayed target-binding acknowledgment.** The Director's binding of the isolated
   `fx-b2-liveness-operational` target under
   `founder-authorize-local-live-proof-target-20260927T0102Z` (recorded in WO-220505.md
   "Target binding and fixture pin — 2026-09-27") is directly acknowledged by the Founder
   through this inbox handoff. No further separate acknowledgment is required for phase 1.

4. **DAG-shape choice.** The handoff expressly delegates this choice to the Director
   ("Director may choose whether phase 1 is in #125 or a prerequisite BIU to keep scope
   bounded"). The Director keeps phase 1 and phase 2 within the single existing BIU (#125,
   WO-220505); no new prerequisite Issue/BIU is created. Rationale: WO-220505.md's own
   "Acceptance plan — two phases" section (recorded 2026-09-27) already separates phase 1
   (mechanics-only, no requirement-satisfaction claim) from phase 2 (the only path to this
   BIU's own DONE); splitting into a new GitHub Issue/Project item would be a DAG expansion
   for marginal benefit and would not reduce the reported material risk that phase 1
   evidence could be misread as AC-08 closure. Single-BIU scope is the conservative choice
   under the mission's "expand scope conservatively" principle.

## Boundaries

This decision does not authorize declaring Issue #125 DONE, does not authorize any SWF-29
bootstrap-retirement claim, and does not identify or bind a specific phase-2 live-workload
target — that remains a separate future decision when phase 2 is undertaken. It does not
alter R1-GAP-MONITOR-HOST, DESIGN_CANDIDATE_WITH_SPECIFY_HOLD, or any Authority text for any
node other than the single WO-220505/SF-REQ-056 paragraph named above.

## Consequences

WO-220505.md is revised to record this disposition and state that phase 1 has no remaining
owner-level blocker. `docs/evidence/wave2-design-contracts.md`'s SF-REQ-056 Authority
paragraph is revised narrowly to cite this decision for the hosting/supervision sub-question
only. A fresh native Agent Ready assessment of the resulting WO-220505.md revision determines
actual disposition (READY/CLARIFY/HOLD); this decision does not itself make Issue #125 READY
or eligible. Where that fresh assessment still returns CLARIFY or HOLD on grounds independent
of this decision, the Founder-hold entry for #125 is narrowed to name only those remaining
grounds, not removed.
