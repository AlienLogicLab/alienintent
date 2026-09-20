# Proposal intake index

Proposal files in this directory are **immutable provenance artifacts**. They are submitted intake records, not canonical backlog state, and are never edited after submission. Canonical state lives in the decision records and Product Issues listed below.

| proposal_id | Title | Classification | Canonical decision record | Product Requirement | Issue | Status |
|---|---|---|---|---|---|---|
| PROP-2026-0001 | Deterministic Failure-Class Promotion / Proven-Red Verification | Product Requirement + binding engineering principle | [SWF-24](../decisions/2026-09-20-deterministic-failure-class-promotion.md) | SF-REQ-050 | [#61](https://github.com/AlienLogicLab/alienintent/issues/61) | canonicalized 2026-09-20; P1 / Wave 3 assigned |
| PROP-2026-0002 | Design Contract and Design Verification before BIU execution | Workflow/architecture semantics + Product Requirement | [SWF-25](../decisions/2026-09-20-design-contract-and-design-verification.md) | SF-REQ-051 | [#62](https://github.com/AlienLogicLab/alienintent/issues/62) | canonicalized 2026-09-20; P0 / Wave 2 assigned; scope/visibility clarified |
| PROP-2026-0003 | Persistent Control Plane with Bounded Coordinator Episodes | Workflow/architecture semantics + Product Requirement | [SWF-27](../decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md) | SF-REQ-053 | [#64](https://github.com/AlienLogicLab/alienintent/issues/64) | canonicalized 2026-09-20; P0 / Wave 2 assigned |
| PROP-2026-0004 | Execution Evidence Derivation and Consistency Verification | Capability ratified; folded into an existing requirement | [SWF-28](../decisions/2026-09-20-evidence-and-intake-ratification.md) | **SF-REQ-030** (amendment) | [#45](https://github.com/AlienLogicLab/alienintent/issues/45) | ratified 2026-09-20; SF-REQ-054 retired, [#65](https://github.com/AlienLogicLab/alienintent/issues/65) closed as duplicate/superseded |
| PROP-2026-0005 | Proposal Intake as a Product Capability | Product Requirement | [SWF-28](../decisions/2026-09-20-evidence-and-intake-ratification.md) | SF-REQ-055 | [#66](https://github.com/AlienLogicLab/alienintent/issues/66) | ratified 2026-09-20; CAPTURE; P1 / Wave 3 |
| PROP-2026-0006 | Deterministic Actor-Launch Liveness Reconciliation | Product Requirement | [SWF-29](../decisions/2026-09-20-liveness-reconciliation.md) | SF-REQ-056 | [#67](https://github.com/AlienLogicLab/alienintent/issues/67) | canonicalized 2026-09-20; CAPTURE; P0 / Wave 2 |
| PROP-2026-0007 | Candidate Worktree Retention — local worktree as operational cache | Operational policy | — | — | — | **submitted 2026-09-20; awaiting Founder approval**; 17 worktrees retained pending it |

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

- **PROP-2026-0004 and PROP-2026-0005** were submitted by the durability-gap audit with `authority_level: unresolved`. Both were **ratified by the Founder on 2026-09-20** ([SWF-28](../decisions/2026-09-20-evidence-and-intake-ratification.md)).
- **The SF-REQ-054 / SF-REQ-030 overlap is resolved.** SF-REQ-030 is the canonical owner; SF-REQ-054 is retired and #65 closed as duplicate/superseded, with the ID not reused and provenance preserved.

## Open Founder decisions

- **PROP-2026-0007** — does remote publication with confirmed read-back satisfy retention for a local candidate worktree? 17 published-but-unlanded worktrees are retained pending the answer. The 2 sole-copy PY-04 worktrees remain retained regardless.

None outstanding from proposal intake.

**PROP-2026-0006 note:** amendment to SF-REQ-001 or SF-REQ-008 was assessed first and rejected — both are Wave 1 and partly implemented, so folding a Wave 2 obligation into them would create the retrofit ambiguity the proposal forbids. Neither is amended; SF-REQ-056 is the single canonical owner. SF-REQ-048, 049, 050, 051, 052, 053 and 055 all carry an assigned Priority and Wave.
