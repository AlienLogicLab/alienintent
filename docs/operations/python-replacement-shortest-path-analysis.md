# AlienIntent — Shortest Defensible Path to Python-Only Replacement

**Date:** 2026-09-29 (Asia/Bangkok)
**Status:** Dependency and proof analysis, not a release/cutover instruction.
**Repository baseline:** `origin/main` `90d803135083e9597737a2a9647084629dc78d03`; Project #1 and runtime observations are point-in-time.
**Objective:** completely remove dependence on the AlienIntent Node.js/B-DISP factory while a Python AlienIntent autonomously turns authorized intent into independently verified, high-quality product outcomes.

## 1. Three finish lines that must not be conflated

1. **Stop using Node to build Python.** The Founder has chosen this now. Pausing/shutting down the old build engine preserves a safe offline work period; it does not establish a Python replacement. A separate Codex process owns shutdown.
2. **Python execution sovereignty.** A single Python writer owns live intake, scheduling, admission, worker supervision/custody, verification, effects, observation, liveness, attention, mailbox, checkpoint, operator/launch paths and rollback. No AlienIntent Node service or required Node alias remains. This is the binding 2026-09-27 Python-only cutover contract, not just WO-220607/R7.
3. **AlienIntent product success.** The factory rejects wrong, drifted, duplicated, overbuilt or unsupported software and reaches verified product outcomes. Python sovereignty is necessary but insufficient. Minimum agent-slop controls in the accompanying problem/gap documents must gate the first production claim.

The word **shortest** here means the smallest dependency/proof chain under current authority, not a duration estimate. WIP, release gates, operational access, unresolved decisions and new defects can extend elapsed time. A Project DONE lane or a local fixture does not discharge an operational predecessor.

## 2. Current substrate and limits

The Python repository already contains `src/alienintent/` (197 Python source files in the current checkout), PY-01–PY-10/PY-09B marked DONE, and accepted Wave 2 bounded work through offline multi-role and several live-target proofs. These are useful code and evidence to **inspect and selectively reuse**. The formal v2 design explicitly rejects porting the v1 state machine; accepted old BIUs do not automatically satisfy new v2 ledger/architecture acceptance.

At the read-only snapshot during this analysis, Project #1 had #125/WO-220505 READY, #131/R2 TASKS, #132/B6 TASKS, #134/B8 TASKS, #135/R3 TASKS, #136/R4 TASKS, #137/R5 TASKS, #139/R7 TASKS, #144 and #145 TASKS; #138/R6, #124/B1, #126/B3, #127/B4, #128/B5, #129/B7 and #130/R1 were DONE. #143 (the Node ledger source for the observer successor) was DONE. R8/WO-220608, B9/WO-220512 and R9/WO-220609 exist as candidate BIUs in the DAG but had no materialized GitHub Issue in the open-Issue/Project inventory. These statuses require fresh readback before release.

The separate shutdown process had changed runtime state by about 20:39 ICT: `alienintent-factory-director-host.service` was inactive, while `alienintent.service` (Node), `alienintent-liveness.service` and `alienintent-observer.service` were active. The earlier Director `PAUSE` file was absent. Node `state.json` had a #150 PRODUCER record with DONE signal pending in ACCEPT. This read-only snapshot does not reveal the shutdown owner's plan or establish quiescence; **do not restart, stop, clear or migrate claims based on this document**.

The repository was still PUBLIC. **The first step is to make a proper home for the product in Git**, as the Founder clarified on 2026-09-29. The plan calls this repository stage “M-1”: make the existing canonical engineering repository private without losing its Issues, Project, branches or integrations; verify access and event delivery; classify what may be public; build a deterministic publication process; and use a separate curated public repository. Complete the plan's V2-000A–H repository work before serious kernel or other codebase implementation. The later handoff's kernel-first ordering is superseded by this explicit clarification.

## 3. Minimum Python capability path under the current v2 plan

| Stage | Existing planned work | Proof that advances the replacement |
|---|---|---|
| C0 — prepare the Git home first | Preserve #150/#152 and other open work/effects under the shutdown owner; complete V2-000A–H before coding | Exact recoverable checkpoint/claim/effect inventory; canonical repo PRIVATE, integrations checked, public target built from allowlist and no private history. The long-term repository rename remains deferred. |
| C1 — v2 design contract | V2-001–005 (M0) | Ratified UL/context ownership, typed ports, architecture fitness, canonical event/state/evidence schemas and a test worker that kills violating fixtures. |
| C2 — deterministic offline factory | V2-101–108 (M1); inspect PY-02/03/04 and WO-220307/404 as evidence | One WAL ledger/projection, pure legal transitions, priority/dependency/WIP scheduling, claims/typed blockers, idempotent effects, bounded resources, restart/replay, CLI, exact candidate/independent verifier. Provider-free fault test reaches truthful DONE without duplicate effect or no-silent-idle failure. |
| C3 — authorized intent to executable work | V2-201–208 (M2); bring minimum SF-REQ-051/#62 and SF-REQ-057/#147 into this path | Exact Founder input/provenance survives; ambiguity and design authority are resolved; every obligation maps through spec/design/plan/BIU; Agent Ready is consumed through its public contract; mechanical proof obligations are fixed before implementation. Current plan includes REST/MCP/UX units; any compressed CLI-first subset requires a revised milestone decision. |
| C4 — real single-project delivery | V2-301–306 (M3); adapt PY-05/06/08/09/09B and WO-220401–404 after conformance review | Authenticated GitHub/worker/source-control adapters; fresh install/doctor; one real BIU traverses producer → independently retrieved exact candidate → verifier → accepted landing → actual closure, survives fault/restart and projects without giving GitHub a second authority. |
| C5 — minimum product-quality gate | Minimum V2-402 and V2-406 extents, plus the gap document's GR-01–08, before treating C4 as production success | Wrong solution, dropped obligation, duplicated mechanism, unsupported PASS, self-review, regression repair, resource leak and failed operational outcome are each rejected by a discriminating fixture. Broader M4 metrics/N-project scope can follow cutover unless a live predecessor requires it. |

**Later scope optimization, not a change to the starting point:** M2's REST/MCP/UX breadth and M4 multi-project/dashboard/learning work may be reviewed against the one-profile replacement objective. The current canonical plan orders the complete repository stage before M0–M3 coding; that order is now expressly confirmed by the Founder. Any later dependency-minimal revision must explicitly amend the plan and preserve intent, exact-candidate verification and quality hard gates. Treating earlier Python modules as complete v2 is not a shortcut.

## 4. Existing Wave 2 retirement BIUs: dependency-minimal frontier

The Wave 2 DAG supplies a concrete custody/proof checklist after C2–C4 Python capability exists. The table identifies remaining gates, not an instruction to feed them to the stopped Node factory. Rebind each to the new v2 canonical state and obtain a fresh Agent Ready assessment before use.

| Chain | Existing BIUs / Project snapshot | Necessary completion |
|---|---|---|
| Liveness | B2 `WO-220505`/#125 READY → R3 `WO-220603`/#135 TASKS | Real lost-trigger recovery, suppression on genuine block, late delivery and restart duplicate safety; then retire the temporary liveness duty only after successor readback. #125's older two-phase/parked evidence needs target reassessment, not a fictional DONE. |
| Observation | B1 `WO-220504`/#124 DONE → R4 `WO-220604`/#136 TASKS | No observation loss, cursor/identity/restart/retention and consumer equivalence. The planned Node-ledger split #143 DONE → #144 TASKS → #145 TASKS should be **reassessed**: a canonical Python ledger may replace the need for further Node-specific implementation if the same acceptance predicates are proved. Do not discard its pending/handled history. |
| Admission | B3 `WO-220506`/#126 DONE → R6 `WO-220606`/#138 DONE | Revalidate the six prelaunch guards plus eligibility against the actual v2 writer; prior DONE is predecessor evidence, not automatic proof for a different kernel. |
| Mailbox/attention | B4 `WO-220507`/#127 DONE + R1 `WO-220601`/#130 DONE → R2 `WO-220602`/#131 TASKS; B5 `WO-220508`/#128 DONE + R2 → B8 `WO-220511`/#134 TASKS; R3 + R4 + B8 → R5 `WO-220605`/#137 TASKS | Preserve pending and handled identities, genuine attention/judgment wake-up, checkpoint, tenure, suppression and consumer handoff. Empty queue does not satisfy the gate. |
| One-writer sovereignty | B1 + B2 + B3 + B5 + E2 `WO-220503`/#123 DONE → B6 `WO-220509`/#132 TASKS | Live Node-independent Python profile, real workload, active-work/effect reconciliation, checkpoint, rollback and exact one-writer proof. |
| Node execution retirement | R3 + R4 + R5 + R6 + B6 → R7 `WO-220607`/#139 TASKS | Read back that Python owns dispatch/webhook/worker/candidate/effects and no AlienIntent Node execution authority remains. An explicit cutover decision and reproducible rollback remain required. |
| Alias and bootstrap roles | B7 `WO-220510`/#129 DONE → R8 `WO-220608` **candidate only**; R2 + B8 → B9 `WO-220512` **candidate only** → R9 `WO-220609` **candidate only** | Materialize/assess the three candidate BIUs as needed; dispose the required alias and local Program Director role, or prove their Python successors and bounded custody. R7 alone is not complete replacement. |

With WIP=1, the dependency frontier for *remaining* existing BIUs is approximately: #125 and the observer successor decision first; then #135/#136, #131, #134; then #137 and #132; then #139, with R8 and B9/R9 prepared along their independent branches. Exact order among ready independent branches depends on current priority, proof/authority and the revised v2 plan. There is no basis here to claim a calendar duration or to assign the stopped Node factory as executor.

## 5. What can be removed from the critical path, and what cannot

- Do **not** rerun PY-01–PY-10 or every DONE Wave 2 BIU merely to reproduce history. Inspect their accepted code/receipts and reuse only semantics that match v2. A targeted conformance fixture is cheaper than blanket parity.
- Do **not** finish unrelated Node maintenance (#133, #149–152) as prerequisites to new Python architecture. Preserve unresolved work/custody for shutdown and later reconciliation; #146's no-silent-idle and #147's durable Founder intake are **product invariants** to carry into v2.
- Do **not** mechanically complete #144/#145 if their Node ledger topology has become obsolete. The R4 observation invariants still must pass against the Python ledger and real consumers; change the BIU plan under authority rather than declare a dependency met by name.
- Do **not** defer minimum intent/design/quality/evidence/outcome controls to after production cutover simply because their full SF-REQs are Wave 3 or M4. That would satisfy language migration while failing the product's primary purpose.
- Do **not** treat a temporary Node stop as R7 DONE. Equally, do not require unrelated developer tools that happen to use Node.js to be removed.

## 6. Remaining authority/proof decisions

1. Execute the repository work V2-000A–H first and verify its exit criteria. The prior kernel-first handoff is superseded on sequence; repo visibility readback was PUBLIC.
2. Rebind old B/R proof packets to the v2 ledger and decide which old candidate paths remain valid. The observer chain #143–145 is the clearest potential redundant Node-specific work.
3. Establish a named operational Python target and exact workload for B2/B6, with live effect/rollback receipts. Offline/sandbox proof cannot retire old duties.
4. Resolve the historical Founder gates for broader attention activation and resident-coordinator tenure before B8/R9; the 2026-09-27 disposition also records a temporary PRODUCER-on-Claude profile question. Reassess it against the Founder's newer shutdown/provider strategy rather than apply stale v1 provider policy to v2.
5. Complete the R8/B9/R9 candidate materialization/assessment and audit every required launch/alias/bootstrap consumer. A prior audit corrected its initial “no linkage” claim: transition steps 1 and 2 were satisfied; step 5 tunnel was correctly retained, and step 4 was a Founder disposition, not an invented new BIU.
6. Agree to a minimum end-to-end agent-slop release packet (GR-01–08) before calling the replacement a **successful high-quality software factory**.

## 7. Evidence sources

- Canonical v2 plan: `docs/decisions/alienintent-v2-canonical-project-plan.md`; architecture: `docs/architecture/alienintent-factory-v2-formal-design.md`.
- Existing replacement handoff: `docs/operations/python-replacement-priority-2026-09-29.md` (priority overlay; no cutover proof).
- Binding full cutover contract: `docs/decisions/2026-09-27-python-only-alienintent-factory-cutover.md`.
- Dependency and candidate maps: `docs/evidence/wave2-dependency-dag.json`, `docs/evidence/wave2-candidate-bius.md`, `docs/work-units/wave2/WO-2205*.md` and `WO-2206*.md`.
- Scope audit and correction: `docs/evidence/python-only-cutover-node-inventory-audit-20260927.md`, `docs/evidence/2026-09-27-python-cutover-steps-1-2-4-5-disposition.md`.
- Live board: [Project #1](https://github.com/orgs/AlienLogicLab/projects/1), read 2026-09-29. Runtime snapshot is read-only and time-limited. No service, Issue, Project field or repository visibility was changed by this analysis.
