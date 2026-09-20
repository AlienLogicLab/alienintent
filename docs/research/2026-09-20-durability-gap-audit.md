# Durability-gap audit — 2026-09-20

## Method and boundary

This audit treats canonical Product Requirements and binding decision records as
authority. Proposals and execution evidence identify gaps but do not create
authority. It is documentation/intake work only: no BIU, implementation,
runtime, worker, service, Project Status or live Wave 1 action was changed.
Proposal Intake and the amendments recommended below were subsequently
processed under explicit Founder instruction; see the dated disposition at the
end of this report.

## Traceability matrix

| Candidate capability / decision | Classification | Authority inspected | Gap | Recommended durable action | Target artifact/path |
|---|---|---|---|---|---|
| Execution Evidence Derivation and Consistency Verification | **NEW REQUIREMENT** | SF-REQ-016, 020, 024, 029, 030; existing trajectory/quality evidence | SF-REQ-030 requires derivation but not mechanical reconciliation that detects drift between factual events and derived metrics. | Submit for normal Product Requirement intake; do not prescribe storage or runtime design. | [PROP-2026-0004](../proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md) |
| Proposal Intake as a product capability | **NEW REQUIREMENT** | `docs/proposals/INDEX.md`; SF-REQ-011–016, 032; SF-REQ-041–044 | The index is an operating convention; external-artifact intake is distinct. Neither provides provider-neutral, idempotent proposal-to-canonical admission. | Submit for normal Product Requirement intake. | [PROP-2026-0005](../proposals/PROP-2026-0005-proposal-intake-as-product-capability.md) |
| SF-REQ-050 / SWF-24 mutation semantics | **AMEND EXISTING** | SF-REQ-050 / SWF-24; SWF-23; SWF-26 historical mutation gate | Existing authority requires meaningful violations and retained promotion evidence, but does not explicitly retain semantic violation, applicability, expected/actual result, provenance/version, or the `NOT_APPLIED` rule. | Amend the canonical requirement and decision under normal authority; do not create a duplicate requirement. | SWF-24 / Issue [#61](https://github.com/AlienLogicLab/alienintent/issues/61) |
| SF-REQ-007 VERIFY candidate-identity admission | **ALREADY COVERED** | SF-REQ-007; candidate-publication invariant; SWF-22; PY-06 contract | No authority gap: exact identity, independent retrievability/read-back and inadmissible VERIFY are explicit across source-control and local-artifact forms. | Treat missing/unresolved identity as deterministic admission and negative-test work. | SF-REQ-007 / PY-06 implementation and verification obligation |
| Rejection/failure taxonomy | **AMEND EXISTING** | SF-REQ-029, 030, 024; PY-04 execution evidence; PROP-2026-0004 | The plan names failure taxonomy but does not define the classifications needed for derived counts and explicit UNKNOWN/partial states. | Add evidence-backed taxonomy to SF-REQ-029/030 when PROP-2026-0004 is canonicalized; do not create a second taxonomy requirement. | PROP-2026-0004; then canonical SF-REQ-029/030 |
| Verification liveness | **IMPLEMENTATION DEBT** | SWF-09; scheduling/recovery design; PY-04 and PY-06 contracts | Hard wall-clock, cancellation, finite retry/timeout and bounded outcomes are already required; PY-04 shows the need for enforcement and tests. | Implement timeout classification and hang-to-failure/cancellation behavior under existing authority. | SWF-09 / SF-REQ-009 implementation and verification backlog |
| Coordinator local tooling/watchers | **IMPLEMENTATION DEBT** | SWF-27 / SF-REQ-053; SF-REQ-009; SF-REQ-048; PY-04 evidence | Copy-derived watcher misfires are local tooling reliability evidence, not a new product capability by themselves. | Retain as evidence for bounded coordinator episodes and add deterministic tooling checks only when the relevant implementation/design work is authorized. | SWF-27 / SF-REQ-053; no new requirement |
| Temporary/bootstrap controls | **ALREADY COVERED** | SWF-26; SWF-27 / SF-REQ-053 | SWF-26 records authority, scope, expiry, provenance and replacement target for the historical gate. SWF-27 makes the general no-silent-promotion rule durable. | Preserve SWF-26 as expired evidence; apply standing rule through SF-REQ-053. | SWF-26 and SWF-27 |

## Amendments recommended by the audit

### SF-REQ-050 / SWF-24 — deterministic mutation semantics

Target: `docs/decisions/2026-09-20-deterministic-failure-class-promotion.md`
and canonical Product Issue #61.

> For each promoted mutation, proven-red or negative-control check, retain the
> governing binding rule; the semantic violation intentionally introduced;
> applicability conditions; expected failing evidence; actual result; the
> implementation/reference and provenance/version of the mutation/check; and
> one of `KILLED`, `SURVIVED`, or `NOT_APPLIED`. `NOT_APPLIED` records why the
> mutation could not be applied and must never be counted as `KILLED`. A source
> patch alone is insufficient: the record must state the rule violation the
> mutation is intended to demonstrate.

This is an evidence-shape amendment only. It does not revive SWF-26 or impose a
retroactive Wave 1 gate.

### SF-REQ-029 / SF-REQ-030 — rejection and failure taxonomy

Target: canonical SF-REQ-029 and SF-REQ-030 artifacts, if and when
PROP-2026-0004 is admitted.

> Trajectory events may carry a versioned, evidence-backed failure
> classification that distinguishes behavioral defects, evidence/proof defects,
> custody/identity defects, tooling/publication defects, process-instruction
> adherence, genuine authority requirements, false/escalated authority
> requests, and provider-capacity interruptions where observed. Quality
> Evidence derives aggregate counts and explicit UNKNOWN/partial states from
> cited trajectory events and named sources; deterministic reconciliation rejects
> contradictions where the facts make reconciliation possible.

The vocabulary is proposed, not a schema change or a claim that every event has
every classification.

## Confirmed coverage notes

### Candidate identity

SF-REQ-007 requires that VERIFY never begins until the exact candidate is
durably identifiable and retrievable by a fresh independent verifier, enforced
by the control plane. The candidate-publication invariant requires recorded
ref/SHA, independent retrieval and rejection of unpublished candidates. SWF-22
adds semantic/content-addressed local-artifact custody transfer. PY-06 requires
typed rejection and negative proof for unreachable or mismatched candidates.

### Verification liveness

SWF-09 makes wall-clock duration and cancellation hard-enforced dimensions.
The scheduling/recovery design carries finite timeout/retry/cancellation and
explicit unresolved recovery conditions; PY-06 requires bounded timeout proof.
A hung check is therefore an implementation/verification debt under existing
authority, not a new Product Requirement.

### Temporary controls

SWF-26 expired when PY-04 reached DONE and explicitly identifies SF-REQ-050 as
the normal replacement path for a standing mutation gate. SWF-27 / SF-REQ-053
generalizes the durable requirements: explicit authority, bounded scope,
expiry, provenance, replacement target, and no silent promotion into
architecture.

## Sources inspected

- [Proposal index](../proposals/INDEX.md) and PROP-2026-0001 through
  PROP-2026-0003.
- [Factory plan](../decisions/alienintent-software-factory-plan.md), including
  SF-REQ-007, 016, 020, 024, 029, 030, 032 and 041–044.
- [SWF-24](../decisions/2026-09-20-deterministic-failure-class-promotion.md),
  [SWF-25](../decisions/2026-09-20-design-contract-and-design-verification.md),
  [SWF-26](../decisions/2026-09-20-py04-coordinator-mutation-gate.md),
  [SWF-27](../decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md),
  [SWF-09](../decisions/2026-09-20-wave1-plan-approval-d1-d2.md), and
  [SWF-22](../decisions/2026-09-20-py04-custody-transfer.md).
- [Candidate-publication invariant](../evidence/candidate-publication-invariant.md),
  [PY-04 contract](../work-units/python/PY-04.md), [PY-06 contract](../work-units/python/PY-06.md),
  and [scheduling/recovery design](../architecture/pre-python-gate/scheduling-and-recovery.md).

## Post-audit disposition — 2026-09-20

The Founder directed Proposal Intake for PROP-2026-0004 and PROP-2026-0005,
then directed materialization of both amendments above. The records now map to:

- PROP-2026-0004 → **SF-REQ-054**, Issue [#65](https://github.com/AlienLogicLab/alienintent/issues/65), CAPTURE, Priority/Wave unset.
- PROP-2026-0005 → **SF-REQ-055**, Issue [#66](https://github.com/AlienLogicLab/alienintent/issues/66), CAPTURE, Priority/Wave unset.
- SF-REQ-050 / SWF-24 semantic mutation requirements are recorded in the
  canonical decision and Issue [#61](https://github.com/AlienLogicLab/alienintent/issues/61).
- SF-REQ-029 / SF-REQ-030 taxonomy and reconciliation semantics are recorded
  in the canonical backlog plan and Issues [#44](https://github.com/AlienLogicLab/alienintent/issues/44) / [#45](https://github.com/AlienLogicLab/alienintent/issues/45).

Proposal provenance files remain unchanged. The two implementation-debt items
remain debt; no new Product Requirement was created for them.

## Non-actions

No additional Priority/Wave assignment was made. No Product Requirement,
canonical decision, BIU, Project Status, live Wave 1 action, implementation
source or runtime behavior changed in this audit.
