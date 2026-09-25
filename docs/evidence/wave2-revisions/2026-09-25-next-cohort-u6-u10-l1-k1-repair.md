# Wave 2 next-cohort planning repair — U6 / U10 / L1 / K1

Date: 2026-09-25

Status: **REVISED — pending independent scoped Design Verification.** No BIU materialization, Agent Ready assessment, release or implementation authority is created by this record.

## Purpose

Prepare the next execution-supply cohort behind WO-220209 (#105) and WO-220303 (#99) by removing stale authority assumptions from four already-planned Wave 2 candidates while preserving real dependency, proof, live-operation and replacement gates.

Target nodes:

- U6 / WO-220206 — Conditional direction-dependent design applicability
- U10 / WO-220210 — Agent Ready public-interface assessment binding
- L1 / WO-220306 — Known-active liveness reconciliation
- K1 / WO-220401 — Conditional real-worker role outcome producer

## Authority basis

This revision consumes decisions already made; it does not invent new product authority:

- `docs/decisions/2026-09-25-cross-module-coupling-risk-disposition.md`
- `docs/evidence/2026-09-25-wave2-authority-blocker-grooming.md`
- Architecture Authority FD-01 / FD-02 and amendments A1, A5, A6, A9
- SWF-29 / `docs/decisions/2026-09-20-liveness-reconciliation.md`
- SF-REQ-015, SF-REQ-039, SF-REQ-051 and SF-REQ-056 in the canonical software-factory plan
- retained 2026-09-22 Founder-decision bundle classification

## U6 — scoped coupling disposition

The old R1 `allowed_edges` table remains withdrawn and non-normative.

U6 now consumes the binding 2026-09-25 disposition:

- retain existing approved architecture fitness checks;
- add mechanically useful cross-module cycle detection;
- inventory/classify cross-module domain imports against bounded-context ownership;
- assert persistence/table ownership where mechanically expressible;
- keep Ubiquitous Language/domain-meaning coherence as independent review judgment where not reliably mechanizable;
- a dependency is not automatically a defect merely because it crosses a module boundary.

SF-REQ-051 AC-03 remains intact: a genuinely forbidden dependency or incompatible interface must fail mechanically before independent review.

## U10 — Agent Ready ownership gate removed

POSTW1-DECIDE-004A is not an unresolved Founder decision.

Binding Architecture Authority A1 already assigns:

- Agent Ready product: assessment semantics, implementation, public assessment contract/schema, CLI, local MCP, provider adapters and interface compatibility;
- AlienIntent SF-REQ-015: integration through supported public interfaces behind the ReadinessAssessment port.

U10 therefore binds and proves that public interface. It does not create an AlienIntent-owned Agent Ready implementation or schema.

WO-220209 remains U10's predecessor; U10 cannot become execution-ready until that predecessor is accepted/DONE and the exact dependency proof is available.

## L1 — ratification gate removed, operational replacement preserved

POSTW1-DECIDE-008A is stale because SWF-29 already canonicalized SF-REQ-056 as binding P0 / Wave 2 authority.

L1 local/composed proof may therefore proceed without a second ratification decision.

This does **not** claim:

- canonical live monitor/scanner host replacement;
- live transport proof;
- bootstrap liveness retirement;
- new nonterminal retry semantics;
- budget reset.

Those remain separate operational/replacement concerns.

Monitor-host ownership is no longer treated as a Founder question. The remaining obligation is engineering proof of configured independent supervision, restart, scan/self-health and Doctor validation under SF-REQ-053/037/038.

## K1 / SF-REQ-039 — existing ownership, simplified design

The old SF-REQ-039 design introduced a proposed `RoleOutcomeRecord` sidecar and then asked who owned it and who owned the multi-role lifecycle change.

The canonical architecture already supplies the owners:

- Execution Coordination owns released-BIU execution lifecycle, verification/review/acceptance/closure guards and durable result correlation.
- Invocation Runtime owns worker/resource execution behind `WorkerProvider`.
- SF-REQ-039 explicitly requires Deterministic Test Worker and Real Worker to use the same worker-facing port/protocol.

The real capability gap is retained: the current `FactoryCoordinator._completed_for_outcome` collapses producer success through verify/review/accept/close instead of invoking a fresh independent verifier.

The revised design therefore requires:

- producer success publishes/carries exact candidate identity and advances only to VERIFY;
- a distinct independent verifier invocation retrieves/evaluates that candidate;
- rejection records findings and returns to IMPLEMENT under existing attempt/budget authority;
- repair produces a fresh candidate;
- malformed/missing/miscorrelated result holds despite process success;
- restart/readback preserves original attributable identity;
- deterministic and real workers remain behind the same WorkerProvider port;
- no parallel RoleOutcomeRecord state owner is introduced unless later independent Design Verification proves the existing typed result/evidence boundary is insufficient.

## Scope deliberately not repaired in this pass

This revision prepares only U6, U10, L1 and K1.

Downstream candidates that inherited old authority-gap/gate strings — including U8/A, K2/K3/O and later replacement/live-cutover nodes — remain unscheduled and must be refreshed against current authority before their own materialization/readiness assessment.

No topology/depends_on edge, requirement identity, product priority, Wave assignment or current live/cutover authority is changed here.

## Files revised

- `docs/evidence/wave2-design-contracts.json`
- `docs/evidence/wave2-dependency-dag.json`
- `docs/evidence/wave2-candidate-bius.json`

The Markdown historical renderings and `wave2-founder-approval-packet.json` are not rewritten as if history changed. This revision record is the explicit current delta; historical snapshots remain provenance for the baseline at which they were produced.

## Structural validation

Final revised content before independent review:

- `python3 tools/evidence/check_design_contracts.py docs/evidence/wave2-design-contracts.json` — PASS, 0 failures
- `python3 tools/evidence/check_wave2_dag.py docs/evidence/wave2-dependency-dag.json` — PASS, 0 failures
- `python3 tools/evidence/check_wave2_bius.py docs/evidence/wave2-candidate-bius.json` — PASS, 0 failures
- `python3 tools/evidence/check_wave2_specify.py docs/evidence/wave2-specified-requirements.json` — PASS, 0 failures
- `python3 tools/evidence/check_canonical_vocabulary.py` — PASS, 0 failures
- `python3 -m pytest tools/evidence -q` — 351 passed
- `git diff --check` — clean

These establish structural consistency only. Independent Design Verification must still judge authority fidelity, semantic completeness and whether K1 leaves any material design choice to implementation.

## Intended next sequence

For each accepted revised candidate:

1. retain independent Design Verification result;
2. land this planning revision;
3. compile the work-unit document and execution packet from the revised candidate;
4. prepare and pin the executable proof packet;
5. run native Agent Ready against the exact current work-unit revision;
6. materialize/advance through normal PLAN → TASKS → READY read-backed lifecycle only when predecessor proof and all normal gates are satisfied.

No candidate is released by this record.

## Independent Design Verification result

Round 1 returned **REJECT** on two repairable defects: stale K1 ownership prose and insufficiently explicit A1/FD-01/FD-02 provenance. Both were repaired and the full structural/evidence-tool suite rerun successfully.

Round 2 returned **ACCEPT_WITH_NOTES** with **no blocking findings**. The sole note is that the historical label `DV-6` is not repeated even though the split-recommendation carrier remains functionally preserved through the existing authority-block / HumanDecisionRequired route.

Retained review: `docs/evidence/wave2-revisions/reviews/2026-09-25-next-cohort-u6-u10-l1-k1-review.md`.

**Final planning status: independently accepted for compilation.** Release/implementation remain separately gated.
