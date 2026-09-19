# EOS normalization plan — FD-06

Date: 2026-09-19. Status: AUDIT RESULT AND FOUNDER DECISION PACKET; no EOS
conformance baseline is established by this document.

BIU: [PG-19](../../work-units/pre-python-gate/PG-19.md), Agent-Ready READY before
execution. Binding input: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) §40.

Authority §40 requires AlienIntent to record one internally consistent, approved
EOS version before claiming conformance, states that mixed per-document maturity
is not a conformance baseline, and requires maturity inconsistencies to be
reconciled in EOS itself first. FD-06 therefore could not be resolved by pinning
a commit and annotating documents. EOS was audited instead.

## Canonical EOS repository and revision audited

Repository `AlienLogicLab/P000-all-eos`, working copy
`AlienLogicLab/P000-all-eos` (private repository), branch `main`, revision
`79d769228c266064e71b7ab7f556ea831cfc9537`, clean at entry. This is the canonical
Alien Logic Lab EOS repository. It is a revision, not an approved version; EOS
has no version identity (N-01).

The audit is recorded durably inside EOS as
`docs/05-artifacts/reviews/REVIEW-000003-all-eos-conformance-normalization-audit.md`,
with status `Approved` following Chief Architect review, a status
that is inside the ratified EOS Review lifecycle.

## Outcome

**Resolved.** EOS v1.0 was ratified on 2026-09-19 by `DR-000007`. The audit result
below is retained as the record of the condition that prompted it.

| Finding | Disposition |
| --- | --- |
| N-01 | Resolved — version scheme and EOS v1.0 ratified |
| N-02 | Resolved — three v0.2 documents reviewed, survived, adopted |
| N-03 | Resolved — seven placeholders restated `Draft`, excluded by name |
| N-04 | Resolved — `ADR-0006` adds the Playbook entity; ontology v0.2 |
| N-05 | Deferred by Founder direction — remain `Proposed`, excluded, carried to v1.1 |
| N-06 | Resolved — registry reviewed and ratified into v1.0 |
| N-07 | Resolved — AlienIntent registered as `P007` |
| N-08 | Resolved — reviewed, not required as authority, excluded, carried to v1.1 |
| N-09 | Resolved — `DR-000008`; SI-0002 found correct |
| N-10 | Resolved — `SI` class registered, directory index added |
| N-11…N-15 | Applied during the audit |
| N-16 | Open — carried to v1.1 |
| N-17 | Resolved — `ADR-0007` registers the public-repository exception |

## Audit result as found

**EOS could not then be represented as one internally consistent approved
version.** Seventeen inconsistencies were found. Five were correctable under
existing accepted EOS authority and have been applied in EOS. One is recommended
but deliberately not applied. Eleven require Founder decisions and are presented
below.

## Maturity tiers found at the audited revision

Ratified EOS vocabulary is the default record lifecycle `Draft -> Reviewed ->
Accepted -> Active -> Superseded or retired -> Archived`, the CIR lifecycle, and
the per-entity lifecycles in the Accepted ontology.

The six authority tiers are Undeclared, Accepted, Proposed, Directed, Scaffold
and Draft. The table separates several Accepted classes, so it has more rows than
there are tiers.

| Tier | Representative artifacts | Authoritative under ratified rules |
| --- | --- | --- |
| Foundation, no status or version | Constitution, README, WHY, spec-driven development, AGENTS, documentation index | Undeclared |
| Accepted ADRs | ADR-0001 … ADR-0005 | Yes |
| Accepted v0.1 records | ontology, record conventions, artifact system, knowledge lifecycle, evidence chains, capability model set, agent operating model, learning-loops set | Yes |
| Accepted Decision Records | DR-000001 … DR-000006 | Yes |
| Accepted CIRs | cir-000001 … cir-000008 | Yes |
| Proposed CIRs | cir-000009 … cir-000019 | No |
| Directed but unratified policy v0.2 | engineering principles, playbook registry, playbook organizational learning | No |
| Scaffold v0.1 | seven playbook entries including decision principles | No |
| Draft operating material | deployment discipline, current project registry | No |
| Superseded but unmarked | horizon baseline vision v0.1 | No |

## Normalization plan

| ID | Artifact | Problem | Proposed correction | Class | Founder approval |
| --- | --- | --- | --- | --- | --- |
| N-01 | Repository-wide | No EOS version identity exists; "approved EOS version" has no referent | Define an EOS version scheme and ratify an initial version by Decision Record, naming the artifacts in scope | Governance + architectural | **Required** |
| N-02 | Three v0.2 playbook entries | "Directed organizational policy - review pending" asserts directive force while declaring review pending; not a ratified state | Complete Rick review and move to a ratified state, or relabel `Draft` and exclude from the canonical version | Governance | **Required** |
| N-03 | Seven v0.1 playbook entries | "Scaffold - Pending review" is not a ratified state and the entries are placeholders | Map to `Draft` and exclude, or retire and recreate when evidence exists | Governance | **Required** |
| N-04 | Ontology | No Playbook, Playbook Entry or Principle entity; root cause of N-02 and N-03 | Add the entity and lifecycle by ADR or Decision Record, then restate playbook statuses in that vocabulary | Architectural + governance | **Required** |
| N-05 | cir-000009 … cir-000019 | Eleven CIRs unreviewed against eight Accepted; the learning layer is itself mixed | Run Chief Architect review, or scope the canonical version to Accepted CIRs and state the exclusion | Governance | **Required** |
| N-06 | Current project registry | The only portfolio reality register is `Draft` | Review and ratify, or declare portfolio membership non-authoritative | Governance | **Required** |
| N-07 | Project registry and ADR-0001 | AlienIntent appears nowhere in EOS, is absent from the registry, and its repository does not follow the P-number pattern | Assign a Project identity, decide repository naming, register the project | Governance | **Required** |
| N-08 | Deployment discipline | The sole engineering-discipline artifact is `Draft` yet is cited as an EOS input to AlienIntent deployment-authority design | Review and ratify, or exclude the layer and drop the inheritance citation | Governance | **Required** |
| N-09 | SI-0001, SI-0002, SI-0003, SI-0005 | `Closed`, `Draft` and `Authorized` are Work Order states, not ontology Strategic Initiative states; SI-0002 states status mid-document | Restate each initiative in the ontology Strategic Initiative vocabulary | Semantic in form, governance in effect | **Required** |
| N-10 | `strategic-initiatives/` | `SI` is not in the ratified identifier table or approved directory structure and the directory has no README index | Amend the convention by Decision Record, then add the index | Governance | **Required** |
| N-11 | Record directories and numbering | Header says `Accepted v0.1`; body says the convention "remains draft until ratified", although DR-000001 ratified it | Record that DR-000001 satisfied the condition; retain the original sentence as provenance | Editorial | Not required — **applied** |
| N-12 | Horizon baseline vision v0.1 | Superseded by the Approved v1.0 record but still labelled Draft with no forward link, violating ratified Status Rules | Set `Superseded` with a forward link; preserve the body | Editorial + semantic | Not required — **applied** |
| N-13 | Documentation index | Lists three directories that do not exist, points at the superseded vision record, omits whole record classes | Rebuild the index accurately from repository contents | Editorial | Not required — **applied** |
| N-14 | Work Orders index | `WO-000012` exists but is unindexed | Add it | Editorial | Not required — **applied** |
| N-15 | ADR-0001 … ADR-0005 | No owner stated, although the ADR index and ratified Owner Rules require one | Add `Owner: Alien Logic Lab`, the owner used by every other statused foundation record | Editorial | Not required — **applied**, value correctable by the Founder |
| N-17 | ADR-0001, `AGENTS.md` line 70, `AlienLogicLab/alienintent` | ADR-0001 decides on a private GitHub Organization as operational substrate and the agent rules forbid public repositories; the AlienIntent repository is public while every other project repository is private. The Founder confirms this is intentional, but EOS records no deviation and no permitting rule | Record an explicit approved deviation, or amend ADR-0001 to distinguish the private operational substrate from deliberately published project repositories; restate the publication and no-secrets rules for public repositories | Governance | **Required** |
| N-16 | Nine record-directory indexes and the documentation index | Eighteen sibling indexes carry `Status` and `Owner` headers; these do not | Add the headers | Editorial | Not required — **deliberately not applied**, because the ratified Index Rules do not require a status header on an index, so applying it would establish a convention rather than enforce one |

## What was deliberately not done

No record was promoted. No `Draft`, `Scaffold`, `Proposed` or directed-but-
unratified material was treated as authoritative or moved to a stronger status.
No EOS version identity was created. No EOS governance rule was relaxed to let
the gate pass. No record was deleted; superseded material remains in place with
forward links. Nothing was pushed to any remote.

## Consequence for AlienIntent

AlienIntent's conformance baseline is **EOS v1.0**, recorded in
[eos-conformance-manifest.md](eos-conformance-manifest.md). G31 is PASS. AlienIntent may continue to cite individually Accepted
EOS records within their stated scope, because the ratified EOS Status Rules
permit that, but such citations are not conformance to EOS as a system. See
[eos-inheritance.md](eos-inheritance.md) and FD-06 in
[founder-decisions.md](founder-decisions.md).
