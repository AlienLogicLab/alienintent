# Eos Inheritance — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-15](../../work-units/pre-python-gate/PG-15.md), Agent-Ready READY before drafting. Revised by [PG-19](../../work-units/pre-python-gate/PG-19.md), Agent-Ready READY before revision.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).
Binding decision: [Founder decisions FD-02 through FD-06](../../decisions/2026-09-19-pre-python-gate-founder-decisions-fd02-fd06.md), FD-06 section.

## Conformance baseline: EOS v1.0

AlienIntent conforms to **EOS v1.0**, ratified 2026-09-19 by `DR-000007` in
`AlienLogicLab/P000-all-eos`. The version's contents are authoritatively stated in
that repository's `docs/00-foundation/all_eos_versions.md`. AlienIntent's
conformance record is the [EOS conformance manifest](eos-conformance-manifest.md).

Authority §40 is satisfied: one internally consistent, approved EOS version is
recorded, no mixed per-document maturity is carried, and the inconsistencies were
reconciled in EOS itself before the claim was made.

AlienIntent is registered as project **P007** in the EOS project registry, which
was reviewed and ratified into v1.0 so that the identity sits inside the approved
version rather than outside it. The repository `AlienLogicLab/alienintent` remains
public by Founder decision; that deviation from ADR-0001 is registered in EOS as
`ADR-0007` rather than left silent.

### How the baseline was reached

The audit under PG-19 found EOS could not be represented as one approved version:
no version identity, seventeen inconsistencies, six authority tiers of which three
were undefined. The Founder then authorized EOS `WO-000013`, which:

- established the ALL-EOS version scheme and ratified **EOS v1.0** (`DR-000007`);
- **substantively reviewed** Engineering Principles v0.2, Playbook Registry v0.2
  and Organizational Learning v0.2 (`REVIEW-000004`). All three survived review
  and were adopted; the ten Agentic Development Discipline rules are now Adopted
  policy binding AlienIntent;
- added Playbook and Playbook Entry to the ontology (`ADR-0006`), closing the root
  cause that let that layer invent statuses;
- registered the public-repository exception (`ADR-0007`) and the `SI` record
  class (`DR-000008`);
- ratified the project registry and registered AlienIntent as P007;
- left the seven playbook placeholders `Draft`, `cir-000009`…`cir-000019`
  `Proposed`, and `deployment_discipline.md` `Draft`, each **excluded by name**
  from v1.0 rather than promoted.

**Withdrawn:** the earlier candidate baseline pinned commit `79d7692` with
retained per-document maturity. That approach was rejected by Founder direction.
The withdrawn text remains at commit `727de90685ebdd6cca48f61fd9b1948efc8bbc33`.

## What AlienIntent may cite

EOS ratified Status Rules state that Draft records may guide active work but are
not authoritative, and that no record is authoritative merely because it exists.
Membership of EOS v1.0 is the operative test, and the authoritative list is the EOS
version register, not this document.

- **Citable as inherited authority.** Everything included in EOS v1.0: the
  foundation doctrine, now `Accepted v1.0`, including the Constitution's
  epistemic-integrity, architecture-before-implementation, knowledge-preservation
  and evidence-linked organizational-learning commitments; Ontology v0.2; ADR-0001
  through ADR-0007; the Accepted Decision Records; the Accepted v0.1 foundation
  records including Knowledge Lifecycle and Capability Evidence Chains, which
  require that provenance, supporting and contradicting evidence, owner,
  qualitative confidence, review cadence and supersession remain traceable;
  `cir-000001` through `cir-000008`; and the adopted Playbook material.
- **Adopted Playbook policy.** The ten Agentic Development Discipline rules in
  Engineering Principles, registry entry `PB-DIR-0001`. The seven `PB-CAND-*`
  entries remain `Candidate` and are not citable as policy.
- **Not citable.** Anything named in the version register's exclusion list:
  `cir-000009` through `cir-000019`, which are `Proposed`; the six playbook
  placeholders including Decision Principles, which are `Draft`;
  `deployment_discipline.md`, which is `Draft` and was found not required as
  authority for AlienIntent; `DR-000003` through `DR-000005`, which carry a
  `Draft / Proposed` dual label; and the nine `Draft` opportunity-evaluation
  artifacts.

Ontology v0.2 establishes Work Order, Claim, Evidence and Decision distinctions;
do not flatten them into AlienIntent operational state.

## Inheritance contract

Maintain an explicit conformance manifest, as [eos-conformance-manifest.md](eos-conformance-manifest.md) now does:
source repository, EOS version, commit, path, section and status; the AlienIntent
requirement, artifact and check; translation notes; deviations; and the approving
authority. A new EOS version triggers a delta review; it does not silently
overwrite product semantics or approved deployment behavior. Maintain the current
known-good Node capability and distinguish historical proof from new assertions.
The manifest records an EOS version, never a bare commit with per-document
maturity annotations.

AlienIntent's public repository visibility is registered in EOS as `ADR-0007`, a
bounded exception to ADR-0001 with standing no-secrets and publication
obligations. The repository name and visibility are unchanged.

AlienIntent holds project identity **P007** in the ratified EOS project registry,
so the manifest names a registered inheriting party.

## Contribution path

An AlienIntent finding links exact source, commit and verification with its
limits, creates a local candidate organizational lesson or CIR proposal, receives
engineering and governance review, then is submitted through an explicit EOS
proposal, pull request or other authorized mechanism. Acceptance records the EOS
decision and version and feeds back into the conformance manifest. Organizational
learning must not obstruct bounded product learning or invent a new product or
program.

PG-19 performed the EOS-side work directly under Founder-authorized EOS
`WO-000013` rather than through this contribution path, because the work was
EOS normalization commissioned by the Founder, not a project finding proposed
upstream. The resulting EOS records were reviewed by the Chief Architect on 2026-09-19 and
returned PASS: EOS `REVIEW-000005-chief-architect-eos-v1-normalization.md`.
Nothing was pushed. No unreviewed EOS material was promoted.

## Scenarios

A Node bootstrap lesson about exact result correlation may be proposed with
Issue1 evidence, but is not instantly an organizational law. An EOS vocabulary
difference produces a translation entry rather than renaming BIU. A pending-review
engineering policy is excluded from inheritance rather than carried with a
qualifying label, and its separately marked candidate-principle table is not
promoted with it. A new EOS version, once ratified, triggers an explicit delta
review before any conformance claim changes.

## Traceability and acceptance

- **G31 — EOS inheritance/contribution mechanism**: **PASS.** One internally
  consistent approved EOS version is recorded (EOS v1.0); inheritance, translation
  and evidence-linked contribution review are explicit; no unreviewed EOS material
  was promoted, and every exclusion is named. Sources: EOS Constitution and
  ontology v0.2, ADR-0004, ADR-0006, ADR-0007, knowledge lifecycle, evidence
  chains, DR-000001, DR-000007, DR-000008, the ratified record conventions,
  REVIEW-000003 and REVIEW-000004.

Assessment method: provide this entire candidate plus the cited authority, EOS
and Node evidence and these criteria to Agent-Ready; classify missing criteria or
conflicting authority explicitly, repair and reassess. READY is BIU readiness,
not design approval. Concrete scenarios above are design checks; no Python
executable proof exists. See [source inventory](inventory.md),
[reconciliation](authority-reconciliation.md), [EOS normalization plan](eos-normalization-plan.md)
and [Founder decisions](founder-decisions.md).
