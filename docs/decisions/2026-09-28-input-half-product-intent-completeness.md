# Input-half product-intent completeness — Founder requirement and bounded audit

Date: 2026-09-28. Status: **Founder decision — binding, hard Factory Director
requirement (P0_FACTORY_CORRECTNESS).**

Recorded via Director inbox handoff
`founder-input-half-product-intent-completeness-20260928`
(`INPUT_HALF_PRODUCT_INTENT_COMPLETENESS_INVARIANT`).

## Decision

AlienIntent has two halves: an input half (capture/classification of requirements,
architecture and design into a groomed, specifiable, plannable backlog and BIUs) and an
implementation half (turning admitted BIUs into software). Product intent must not be
lost between Founder input and canonical backlog. The implementation WIP limit (1)
constrains implementation dispatch only; it does not excuse the Director from tracking,
classifying or materializing durable Founder input. Acknowledgement of a Founder handoff
is not completion: a durable product-intent item remains outstanding until it is
materialized into the correct canonical bounded-context artifact with exact artifact
identity and commit/revision provenance, distinct from merely being acknowledged. This is
binding policy for every Factory Director episode from this date.

## Existing mechanism candidate

`docs/proposals/PROP-2026-0005-proposal-intake-as-product-capability.md` already proposes
substantially this mechanism (proposal capture → classify/deduplicate → resolve authority
→ canonicalize → retain immutable provenance → record proposal-to-canonical mapping), but
remains `status: submitted`, `authority_level: unresolved`. This decision does not adopt
PROP-2026-0005 or design a new ledger; per contract section 6, an open-ended product-shape
capability is not this Director's to design or adopt unilaterally. It should be routed
through normal CAPTURE/SPECIFY intake as its own initiative, citing this existing proposal
rather than a Director-invented parallel mechanism.

## Bounded audit of the handoff's named at-risk items

This episode did not run the handoff's full "oneTimeAudit" (a repository-wide
reconciliation of every Founder/product-intent handoff against canonical artifacts); that
is a substantial initiative better scoped as its own bounded task. This episode instead
checked the four items the handoff itself names:

1. **Operator Control Plane API architecture (SF-REQ-034).** Confirmed: `SF-REQ-034`
   exists in `docs/evidence/wave2-specified-requirements.md`/`.json` only as "operator and
   decision surfaces" — it has not been amended to include the protocol-neutral hexagonal
   ports/query/command/event architecture a prior episode acknowledged
   (`inbox/processed/founder-operator-control-plane-api-architecture-20260928T023012Z.json`,
   disposition `DEFERRED_TO_FUTURE_CAPACITY`). Status: **ACKNOWLEDGED, NOT MATERIALIZED.**
   That prior episode's own `next_action` (confirm SF-REQ-034's existing text, amend it in
   place, add a Wave 2 DAG node/BIU under it, prioritize the `directorOptimization`
   query surfaces) still stands and is not repeated here; deciding the amendment's
   substantive content is Founder/architecture-reserved work this episode does not
   perform unilaterally.
2. **Factory Director maintenance delegation / continuous self-improvement mandate.**
   Confirmed: no canonical requirement, decision or work-unit document names this. The
   only repository match is an unrelated mention in
   `docs/research/alienintent-prior-art-cognitive-factory-research-spike.md`. Status:
   **NOT MATERIALIZED; not yet formally ACKNOWLEDGED as a distinct canonical item either.**
   This is itself a Founder-reserved product-shape decision (what such a mandate would
   authorize a Director to do to its own operating contract/tooling); this record surfaces
   the gap rather than inventing the requirement's content.
3. **Private-canonical/publication governance.** Confirmed materialized as durable hard
   policy at `docs/decisions/2026-09-28-private-canonical-publication-governance-handoff.md`
   (commit `1c8e632`). Its own text already records that the broader classification/
   allowlist/publication-tooling framework is deferred to normal CAPTURE/SPECIFY intake as
   its own initiative, not decomposed by Director fiat — this is the correct disposition,
   not a gap.
4. **Verification ceremony proportional to risk.** Confirmed materialized this same
   episode at `docs/decisions/2026-09-28-verification-ceremony-proportional-to-risk.md`
   (commit `47abe3d`). The handoff itself cites this as its positive control.

## Consequences

Items 1 and 2 above are recorded here as open, ACKNOWLEDGED-NOT-MATERIALIZED gaps for a
successor episode or the Program Director to route through CAPTURE/SPECIFY; neither is
decided or drafted by this record. The full input-half ledger/backlog mechanism
(`desiredMechanism`) is not built by this episode; it should enter normal CAPTURE/SPECIFY
intake, citing PROP-2026-0005 as prior art. This episode's private-continuity references
(`~/ai_vault/wiki/projects/...`) were read only to locate confirmed intent already named
in the public handoff payload and are not reproduced here, consistent with the handoff's
own privacy constraint and its instruction that private continuity is evidence, not
authority.
