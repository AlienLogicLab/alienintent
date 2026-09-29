# AlienIntent — Agent-Slop Gap Requirements Analysis

**Date:** 2026-09-29 (Asia/Bangkok)
**Status:** Proposed amendments and acceptance gaps for Founder/product review; **not** newly approved SF-REQ identities, Issue status changes, or implementation authorization.
**Baseline:** `AlienLogicLab/alienintent` `origin/main` `90d803135083e9597737a2a9647084629dc78d03`; GitHub Project #1 read during this analysis. Product Issues and Project lanes are snapshots, not proof of implementation.

## 1. Finding

The original agent-slop problems are **mostly named** in the requirements. The most serious gap is that the highest-value protections are assigned to later Wave 3 or remain CAPTURE while the proposed v2 M3 milestone allows a real agent to land a BIU before the fuller quality controls in M4. A deterministic factory with weak intent/design/evidence gates would reliably produce the wrong software. The shortest safe path is to bring a *minimum effective extent* of the existing quality requirements into the first real vertical delivery proof, then expand depth later.

Project status is not capability status. For example, SF-REQ-012/#18, SF-REQ-014/#20 and SF-REQ-016/#22 are Project DONE but their requirement Issues remain open; that lane alone does not establish complete end-to-end v2 enforcement. Likewise PY-01–PY-10 and many Wave 2 BIUs are DONE as bounded predecessors, not proof of complete product-level conformance. No V2-numbered implementation Issue appeared in the open-Issue inventory; the V2 work units are a plan at this snapshot.

## 2. Problem-to-requirement trace

| Problem | Existing requirement / Issue and Project lane | Gap to close before claiming slop prevention |
|---|---|---|
| PS-01 Lost Founder input | SF-REQ-057/#147 ACCEPT; SF-REQ-011/#17 CAPTURE; SF-REQ-055/#66 CAPTURE | Live, fault-injected intake-to-DONE obligation conservation for multiple inputs and replay, not merely one successful materialization. |
| PS-02 Wrong target/ambiguity | SF-REQ-012/#18 DONE; SF-REQ-051/#62 TASKS; SF-REQ-023/#34 CAPTURE | Independent semantic fit to source intent and explicit unresolved-decision refusal before code, then actual product behavior verification. |
| PS-03 Lost obligations during split | SF-REQ-010/#12 TASKS; SF-REQ-013/#19 CAPTURE; SF-REQ-017/#28 CAPTURE | Machine-verifiable 100% obligation mapping from requirement/design through BIU and closure, with a deliberately dropped obligation rejected. |
| PS-04 Unauthorized design drift | SF-REQ-051/#62 TASKS; SF-REQ-018/#29 CAPTURE; SF-REQ-019/#30 CAPTURE | Enforce design approval/architecture checks on the real release and candidate path; semantic deviations reach independent review. |
| PS-05 Duplicate mechanisms | SF-REQ-051/#62 TASKS; SF-REQ-048/#59 CAPTURE; Reuse Before Build architecture amendment | Evidence of authoritative capability lookup/reuse or a justified exception; detect duplicate owners in design and candidate code. |
| PS-06 Overbuilt or shoddy code | SF-REQ-048/#59 CAPTURE; v2 design §34.6 | Make minimum-work and code-slop review an attributable pre-ACCEPT gate with concrete findings, rather than a guideline or merely a test pass. |
| PS-07 Hallucinated evidence/DONE | SF-REQ-016/#22 DONE; SF-REQ-020/#31 CAPTURE; SF-REQ-030/#45 CAPTURE | Exact-source/candidate/environment evidence and fail-closed UNKNOWN on the integrated lifecycle. |
| PS-08 Self-review/ornamental tests | SF-REQ-014/#20 DONE; SF-REQ-021/#32 CAPTURE; SF-REQ-050/#61 CAPTURE | Fresh independent verdict and proven-red negative control for every applicable mechanical quality rule. |
| PS-09 Repair thrash/regression | SF-REQ-022/#33 CAPTURE; SF-REQ-049/#60 CAPTURE; SF-REQ-052/#63 CAPTURE | Real rejected-candidate repair proves preserved prior behavior/evidence and bounded convergence; focused completion context may follow. |
| PS-10 Fragile runtime/resource slop | SF-REQ-008/#10 TASKS; SF-REQ-018/#29 CAPTURE; v2 design §§18, 34.6 | Explicit object owner, growth budget, retention, high-water and interrupted-cleanup proof on every real worker/effect path. |
| PS-11 Task complete, product broken | SF-REQ-023/#34 CAPTURE; SF-REQ-017/#28 CAPTURE; SF-REQ-020/#31 CAPTURE | Exercise an applicable API/browser/deployment/release predicate and refuse DONE when the candidate landed but outcome failed. |
| PS-12 Lost project cognition | SF-REQ-029/#44 TASKS; SF-REQ-030/#45 CAPTURE; SF-REQ-050/#61 CAPTURE | Typed durable decision/failure context is consumed by a later independent worker, and a recurring finding becomes a governed check. |
| PS-13 Founder as message bus | SF-REQ-001/#3 TASKS; SF-REQ-034/#13 TASKS; SF-REQ-035/#14 TASKS; SF-REQ-053/#64 TASKS | Prospective unattended multi-BIU run with no manual lane pokes; only genuine authority questions interrupt and unblock automatically. |
| PS-14 Activity instead of yield | SF-REQ-024/#35 CAPTURE; SF-REQ-028/#43 CAPTURE | Cohort-level outcome denominator, first-pass/rework/escape and human time/cost; no DONE-count proxy for quality. |
| PS-15 Factory control slop | SF-REQ-008/#10 TASKS; SF-REQ-009/#11 TASKS; SF-REQ-040/#36 CAPTURE; v2 M1 | One canonical ledger/kernel and fault/replay proof, with bounded routine admission cost and no parallel state owner. |

**Important distinction:** “named” is not “implemented”; “bounded predecessor DONE” is not “product problem solved.” The left column is the acceptance target, and the last column describes the missing or unproved integrated behavior.

## 3. Proposed gap requirements and amendments

The IDs below are analysis identifiers. Amend the existing canonical owner after design/authority review; do not create duplicate SF-REQs simply because a cross-cutting acceptance test is missing.

| Gap | Required change and discriminating acceptance | Existing owner | Timing |
|---|---|---|---|
| GR-01 — whole-path quality gate | Define a release-quality contract from source intent to product outcome. Seed wrong-but-plausible implementation, omitted obligation, fake proof, duplicate mechanism and failed operational outcome. The factory rejects each before truthful DONE and accepts a correct control case. | SF-REQ-017/020/021/023/024; v2 M3/M4 plan | **Before first real v2 BIU is called production-ready** |
| GR-02 — obligation conservation | Every source requirement, design decision, acceptance criterion, negative condition, evidence obligation and non-goal has an owner and lineage through decomposition/split/repair; a deliberately removed item blocks READY/ACCEPT. | SF-REQ-010/011/013/017/051/057 | Before autonomous compilation and first real BIU |
| GR-03 — design intent and reuse | Design Verification records authoritative existing-capability search and choice; newly invented storage/service/owner or duplicate code without approval is refused. A relevant existing mechanism is the negative-control fixture. | SF-REQ-048/051; Architecture Authority Reuse Before Build | Before first real BIU |
| GR-04 — independent semantic review | Verifier is independent of producer and compares exact candidate to source requirement/design, including simplicity, user-observable intent, maintainability and non-goals. Reviewer must cite code/evidence locations; a superficial passing test does not suffice. | SF-REQ-018/019/021/048/051 | Before first real BIU |
| GR-05 — evidence authenticity | Checks run against exact candidate and environment; recorded command/exit/output/readback are distinct from agent assertion. Substitute stale SHA, fabricated PASS, missing telemetry or incompatible provenance and force refusal. | SF-REQ-014/016/020/030/050 | Before first real BIU |
| GR-06 — monotonic repair | A rejected candidate repairs the remaining defect without regressing a prior acceptance property or dropping its proof; test an intentional regression and an evidence deletion. Bound retries and preserve history. | SF-REQ-022/049/052 | Before repeated autonomous repair is enabled |
| GR-07 — resource quality | Every persistent/temp object in new Python paths declares custody, budget, retention, crash cleanup and pressure response; long-history and interrupted cleanup tests reject unbounded growth. | SF-REQ-008/018 plus v2 §34.6 | Before live continuous operation |
| GR-08 — outcome closure | Distinguish accepted code from deployed/usable product. For a BIU with a real outcome obligation, fail deployment/API/browser predicate after merge and refuse DONE. | SF-REQ-017/020/023 | Before product-level DONE claim |
| GR-09 — prospective factory yield | Establish reference cohort and collect first-pass acceptance, rework, human interventions, escaped defects, architecture/drift/duplicate catches, latency and full cost per verified outcome with explicit UNKNOWN. | SF-REQ-024/028/029/030 | At first controlled cohort; threshold before broad autonomy |
| GR-10 — learned failure class | A recurring qualitative finding is proposed for promotion, proven red against a meaningful violation, versioned and applied on a subsequent candidate; no model changes binding policy alone. | SF-REQ-050/029/030/032 | Before claiming self-improvement |
| GR-11 — explicit quality decision | Record acceptable risk classes, mandatory independent human/product acceptance (if any), and which verification predicates must be operational for a given product profile. Do not market “bug-free” as a proof claim. | SF-REQ-023/024/034; authority policy | Before external product claims |

## 4. Priority and plan correction

The current v2 plan schedules real single-project delivery at **M3/V2-304** but clusters requirement-evidence traceability, drift, fake-DONE, architecture and repair under **M4/V2-402**, with outcome predicates under **M4/V2-406**. That ordering is acceptable for a clearly labelled engineering probe, **not** for declaring that AlienIntent has solved its primary problem. Pull the minimum GR-01 through GR-08 extents into M2 readiness and M3 exact-candidate acceptance; leave broad policy coverage, richer metrics and multi-project operation in M4. The change is to acceptance and ordering of existing owners, not a license to add ceremony to every trivial edit.

**Repository first, then software.** The Founder clarified on 2026-09-29 that the repository must be properly configured under the existing plan before serious kernel or other codebase work begins. This is the plain meaning of the plan's “M-1” milestone: turn the current engineering repository into the private canonical home for product work, verify its integrations, establish a separate curated public publication target, and prove that publishing is an explicit, controlled action. The repository was still PUBLIC at the earlier readback. The later kernel-first handoff is superseded on ordering; the next implementation milestone is the repository work V2-000A–H, followed by the v2 foundation. Preparation and analysis can continue while that work is performed.

## 5. Proposed validation packet

Run an end-to-end controlled cohort with a known good control and one negative for each of GR-02 through GR-08. Freeze source intent, design, candidate identities and expected outcomes before execution. Use a fresh verifier and retain raw observations and independent verdicts. Then run a prospective, different-task cohort to check that controls generalize; do not score repeated variants of one incident as independent success. Report both quality and cost per verified requirement/outcome. A failed hard invariant blocks quality release regardless of aggregate throughput.

This document is a **gap analysis**. It has not created or reprioritized GitHub Issues, marked requirements DONE, amended Founder authority, trained a model, or executed cutover.

## 6. Source index

- Canonical requirements: `docs/decisions/alienintent-software-factory-plan.md`; GitHub Issues [#3–#67](https://github.com/AlienLogicLab/alienintent/issues) and #147 as applicable.
- V2 delivery mapping: `docs/decisions/alienintent-v2-canonical-project-plan.md` M-1 through M4.
- Slop and resource standard: `docs/architecture/alienintent-factory-v2-formal-design.md` §34.6.
- Binding decisions: `docs/decisions/2026-09-20-design-contract-and-design-verification.md`, `2026-09-20-convergence-assistance-willing-convergence.md`, `2026-09-20-deterministic-failure-class-promotion.md`, `2026-09-28-input-half-product-intent-completeness.md`.
- Project #1 status snapshot: [AlienIntent Project](https://github.com/orgs/AlienLogicLab/projects/1), read 2026-09-29; statuses can change after this document.
