# Proposal intake index

Proposal files in this directory are **immutable provenance artifacts**. They are submitted intake records, not canonical backlog state, and are never edited after submission. Canonical state lives in the decision records and Product Issues listed below.

| proposal_id | Title | Classification | Canonical decision record | Product Requirement | Issue | Status |
|---|---|---|---|---|---|---|
| PROP-2026-0001 | Deterministic Failure-Class Promotion / Proven-Red Verification | Product Requirement + binding engineering principle | [SWF-24](../decisions/2026-09-20-deterministic-failure-class-promotion.md) | SF-REQ-050 | [#61](https://github.com/AlienLogicLab/alienintent/issues/61) | canonicalized 2026-09-20 |
| PROP-2026-0002 | Design Contract and Design Verification before BIU execution | Workflow/architecture semantics + Product Requirement | [SWF-25](../decisions/2026-09-20-design-contract-and-design-verification.md) | SF-REQ-051 | [#62](https://github.com/AlienLogicLab/alienintent/issues/62) | canonicalized 2026-09-20, two open Founder decisions |

## Intake rules

1. A proposal is read completely, its metadata and provenance validated, and checked for duplicates or substantial overlap with existing SF-REQ Issues, Founder/architecture decision records, Wave planning material and current architecture authority.
2. It is classified, and the canonical artifacts it requires are created or updated.
3. The original file is preserved unchanged.
4. The mapping from `proposal_id` to canonical artifacts is recorded here.
5. Priority and wave are never invented. New Product Requirements enter CAPTURE with Priority and Wave unset unless existing binding authority already determines them.
6. Proposals do not create BIUs and do not start implementation.
7. A genuine unresolved Founder decision is surfaced specifically, not decided silently.

## Open Founder decisions arising from intake

- **PROP-2026-0002 / SWF-25 effective scope** — does the Design Contract / Design Verification gate apply to the remaining Wave 1 BIUs (PY-05..PY-10), or only from Wave 2 onward? Wave 1 proceeds unchanged until decided.
- **PROP-2026-0002 / SWF-25 visible lifecycle states** — whether DESIGN / DESIGN VERIFY later become visible Project states. Deferred by the proposal; not blocking.
- **Priority and wave** for SF-REQ-050 and SF-REQ-051.
