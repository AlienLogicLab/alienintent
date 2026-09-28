# Private canonical repository / publication governance — handoff receipt and disposition

Date: 2026-09-28. Status: **Founder decision — binding on the stated hard requirements;
near-term migration step deferred on its own stated precondition; detailed technical design
not yet decided.**

Recorded via Director inbox handoff
`founder-private-canonical-publication-governance-20260928T034829Z`
(2026-09-28T03:48:29Z, "Founder-authorized observing session (ChatGPT), relaying
Founder-approved repository-governance direction; not acting as Factory Director").

## Decision

The Founder has decided, as durable policy, that the canonical AlienIntent engineering
repository is private by default; any public repository is a separately configured
publication target produced from explicit, deterministic, allowlist-based publication
policy, never inferred from memory or implied by an internal commit. The twelve hard
requirements listed in the inbox handoff are accepted as binding product/architecture
policy effective now, in the same sense as any other durable Founder decision recorded on
this repository's own decision log.

This decision does **not** itself pick the target's classification taxonomy, allowlist
mechanism, or publication tooling design. Those are substantive product/architecture design
choices (multiple `hardRequirements` items — classification scheme, allowlist enforcement,
publication tooling, secret-scanning validation) that a Director does not unilaterally
design under contract section 6; they require normal CAPTURE → SPECIFY intake as their own
initiative before any implementation BIU is carved out. Unlike the WO-220611/B3P precedent
(a single, narrowly bounded coverage gap the Founder described precisely enough to
implement directly), this handoff describes an open-ended governance framework.

## Near-term migration step: repository visibility

The handoff's own near-term migration list gates the one concrete, immediately actionable
step — flipping `AlienLogicLab/alienintent` to private — behind "after #141/#126 are safely
progressing." As of this disposition:

- WO-220611 (Issue #141, DAG node B3P) has an independent-verifier cycle in flight
  (PRODUCER cycle 3 candidate published for VERIFY, VERIFIER dispatched
  `AlienLogicLab/alienintent#141:VERIFIER:7476be5c-bb4c-4d17-a9da-7aa0e65a7b45`, started
  2026-09-28T03:56:15Z) after this episode restored a stalled dispatch (see this episode's
  own record). It has not reached DONE.
- WO-220506 (Issue #126) remains on its own unchanged Founder-hold ground
  (`founder-holds.json`): dependency-blocked on WO-220611 reaching DONE and its own
  FX-B3/FX-B4 fixtures being re-pinned. It is not progressing; it is held.

The stated precondition is therefore **not yet met** — #141 is progressing but not DONE,
and #126 is not progressing at all, only held pending #141. This episode does **not** change
`AlienLogicLab/alienintent` repository visibility. A successor episode should reconsider this
step once #141 reaches DONE and #126's own hold is either resolved or the Director confirms
its dependency-blocked (not stalled) state still counts as "safely progressing" — that
reading is not this episode's to assume unilaterally given the live-webhook and GitHub-App
integration risk a visibility change carries for the resident Node runtime, webhooks and
worker GitHub identities the handoff itself calls out ("verify GitHub App, webhooks, workers,
Project access and Director remain healthy after visibility change").

## Boundaries

This decision record does not: change repository visibility; design the
INTERNAL/PUBLIC_SOURCE/PUBLIC_DOCUMENTATION classification scheme; create a publication
allowlist or publication tooling; create a new Wave 2 DAG node, Work Unit, or Product
Requirement; or alter `docs/evidence/wave2-dependency-dag.json` /
`wave2-candidate-bius.json`. It records receipt of a binding Founder policy decision and the
concrete reason its one near-term actionable step is not yet executed.

## Consequences

The twelve `hardRequirements` are binding policy from this date forward for any future work
that touches repository publication, installer/init behavior, or public-facing artifacts;
new work in those areas must not contradict them. The broader publication-governance
framework (classifications, allowlist, tooling) should enter normal CAPTURE/SPECIFY intake as
its own initiative rather than being decomposed by Director fiat. The repository-visibility
migration step is deferred, not declined, and should be re-evaluated once #141 reaches DONE.
The handoff's private continuity reference
(`~/ai_vault/wiki/projects/alienintent-public-repository-governance-migration-plan-20260928.md`)
is not reproduced here, consistent with the handoff's own instruction not to publish the
private continuity plan itself.
