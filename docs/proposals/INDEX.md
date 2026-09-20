# Proposal intake index

Proposal files in this directory are **immutable provenance artifacts**. They are submitted intake records, not canonical backlog state, and are never edited after submission. Canonical state lives in the decision records and Product Issues listed below.

| proposal_id | Title | Classification | Canonical decision record | Product Requirement | Issue | Status |
|---|---|---|---|---|---|---|
| PROP-2026-0001 | Deterministic Failure-Class Promotion / Proven-Red Verification | Product Requirement + binding engineering principle | [SWF-24](../decisions/2026-09-20-deterministic-failure-class-promotion.md) | SF-REQ-050 | [#61](https://github.com/AlienLogicLab/alienintent/issues/61) | canonicalized 2026-09-20; P1 / Wave 3 assigned |
| PROP-2026-0002 | Design Contract and Design Verification before BIU execution | Workflow/architecture semantics + Product Requirement | [SWF-25](../decisions/2026-09-20-design-contract-and-design-verification.md) | SF-REQ-051 | [#62](https://github.com/AlienLogicLab/alienintent/issues/62) | canonicalized 2026-09-20; P0 / Wave 2 assigned; scope/visibility clarified |
| PROP-2026-0003 | Persistent Control Plane with Bounded Coordinator Episodes | Workflow/architecture semantics + Product Requirement | [SWF-27](../decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md) | SF-REQ-053 | [#64](https://github.com/AlienLogicLab/alienintent/issues/64) | canonicalized 2026-09-20; P0 / Wave 2 assigned |
| PROP-2026-0004 | Execution Evidence Derivation and Consistency Verification | Product Requirement | — | SF-REQ-054 | [#65](https://github.com/AlienLogicLab/alienintent/issues/65) | canonicalized 2026-09-20; CAPTURE; Priority/Wave unset |
| PROP-2026-0005 | Proposal Intake as a Product Capability | Product Requirement | — | SF-REQ-055 | [#66](https://github.com/AlienLogicLab/alienintent/issues/66) | canonicalized 2026-09-20; CAPTURE; Priority/Wave unset |

## Intake rules

1. A proposal is read completely, its metadata and provenance validated, and checked for duplicates or substantial overlap with existing SF-REQ Issues, Founder/architecture decision records, Wave planning material and current architecture authority.
2. It is classified, and the canonical artifacts it requires are created or updated.
3. The original file is preserved unchanged.
4. The mapping from `proposal_id` to canonical artifacts is recorded here.
5. Priority and wave are never invented. New Product Requirements enter CAPTURE with Priority and Wave unset unless existing binding authority already determines them.
6. Proposals do not create BIUs and do not start implementation.
7. A genuine unresolved Founder decision is surfaced specifically, not decided silently.

## Requirements canonicalized from decisions, not proposals

| Source decision | Product Requirement | Issue |
|---|---|---|
| [Convergence Assistance / Willing Convergence](../decisions/2026-09-20-convergence-assistance-willing-convergence.md) | SF-REQ-052 | [#63](https://github.com/AlienLogicLab/alienintent/issues/63) |

## Intake verification notes (2026-09-20)

- **PROP-2026-0004 and PROP-2026-0005** carry `submitted_by: durability-gap audit` and `authority_level: unresolved`. Their canonical requirements exist in CAPTURE as **candidate** requirements; ratification of the requirements themselves is open, separately from Priority/Wave assignment.
- **SF-REQ-054 overlaps SF-REQ-030.** The commit that added SF-REQ-054 also amended SF-REQ-030 to carry substantially the same reconciliation obligation; the material difference is SF-REQ-054's additional discriminating negative-control requirement. Intake recorded the overlap on both Issues and did not choose between them.
- Issue #45 was synced to the Founder-amended SF-REQ-030 text.

## Open Founder decisions

- **Priority and wave** for SF-REQ-048, SF-REQ-049, SF-REQ-054 and SF-REQ-055. SF-REQ-050–053 were assigned 2026-09-20.
- **SF-REQ-054 versus SF-REQ-030 boundary** — fold together, or keep both with an explicit stated boundary.
- **Ratification** of SF-REQ-054 and SF-REQ-055, whose proposals carry `authority_level: unresolved`.

