# Domain Model — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-02](../../work-units/pre-python-gate/PG-02.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

Ownership refinement: [binding FD-01](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md), applied through [PG-17](../../work-units/pre-python-gate/PG-17.md). FD-01 is approved; other design choices remain candidate.

## Candidate ubiquitous language v1
| Term | Meaning and identity | Not the same as |
|---|---|---|
| Product Intent | Desired problem/outcome before technical allocation; stable work identity | Repository Issue |
| Work Item | Repository-neutral product/work intent, canonical in the external Work Management Provider; imported with provider identity/version/provenance | Canonical AlienIntent product backlog or bare GitHub item ID |
| BIU | Bounded Implementation Unit; upstream READY work becomes a pinned execution contract on explicit release, with AlienIntent-owned execution authorization/state | Transfer of product ownership or arbitrary shell session |
| Release | Explicit authorized handoff of a specific READY BIU version from Work Management to AlienIntent Execution | Readiness, a display-field edit, or transfer of the entire Work Item |
| Invocation | One role execution with unique ID and pinned context/policy/input versions | Role or reusable worker account |
| Candidate | Immutable artifact identity, repository revisions and provenance | Mutable branch name alone |
| Verification | Mechanically determined evidence against the contract | Engineering judgment |
| Review | Qualitative judgment of intent fit, quality and tradeoffs | Necessarily a separately dispatched lane |
| Acceptance | Authorized decision about exact candidate/evidence | Merge |
| Closure | Authorized remaining landing/publication/deployment/verification actions | ACCEPT itself |
| Profile | Isolated configuration/state/workspace/credential/evidence namespace | One globally shared identity |
| Trajectory | Observable ordered engineering facts and artifact lineage | Hidden reasoning |
| Quality Evidence | Measurements/findings/interventions/outcomes derived from facts | A universal quality score |
| Capability Grant | Attributable bounded permission for worker/BIU/target | Provider credentials by themselves |

PRODUCER creates the candidate; VERIFIER independently verifies/reviews it. Morty/JC are bootstrap identity bindings only. Lifecycle vocabulary remains CAPTURE, SPECIFY, PLAN, TASKS, READY, IMPLEMENT, VERIFY, REVIEW, ACCEPT, DONE; no label is renamed here. Cancellation is an exceptional outcome, not an eleventh happy-path stage.

## Approved ownership boundary (FD-01)

| Bounded context | Canonical authority | Boundary representation |
|---|---|---|
| External Work Management | CAPTURE, SPECIFY, PLAN, TASKS, READY; prioritization, product ownership and business context | Work Management port/ACL imports versioned noncanonical views; explicit release hands off a READY BIU |
| AlienIntent Execution | Released execution authorization; IMPLEMENT, VERIFY, REVIEW, ACCEPT, closure, DONE; invocations/workers/retries/recovery; Engineering Trajectory, Quality Evidence, capabilities and cost/routing evidence | Pinned released BIU, authoritative execution state and attributable results; optional downstream projections back to provider |

This is an architectural split, not an installation/profile choice. A Work Item may have multiple released BIUs; completing one BIU does not rewrite upstream product ownership or declare the entire product intent complete. External display of downstream status does not make the provider a second execution authority.

## Candidate internal decomposition (FD-02 remains open)

Within the approved AlienIntent Execution boundary, the earlier Work Coordination proposal is narrowed to **Execution Coordination**: released BIU versions, execution dependencies, release acceptance and execution lifecycle/closure guards, never canonical upstream backlog. **Invocation Runtime** covers worker/resource ownership and cancellation. **Context Assembly** and **Evidence and Learning** provide separate context/evidence models; **Installation** is supporting profile/adapter/secret configuration. These are candidate internal submodels/modules, not a claim that the Founder approved five additional bounded contexts or services.

The Control Plane coordinates those application services without becoming another state owner. Cross-model references use IDs and versioned contracts. FD-02 now concerns internal decomposition and aggregate ownership inside these fixed authority limits; it cannot reopen whole-lifecycle or configurable ownership. Exact package names remain unset.

## EOS translation
BIU maps to the bounded execution/acceptance aspects of an EOS Work Order, without claiming every BIU is an organizational Work Order. AlienIntent Profile is not EOS Project. Trajectory facts are Evidence; an interpretation is a Claim with uncertainty; accepted learning is a reviewed Knowledge Claim. A proposed policy change maps to a Decision/proposal, never automatic adoption. ADR-0004 preserves both vocabularies.

## Checks
Producer invocation I1 cannot approve candidate C1 as an independent verifier. A new candidate C2 cannot reuse acceptance of C1. Every state-changing invariant above has one owner; an adapter translating Issue42 cannot manufacture a Work Item identity by repository number alone. FD-01 fixes the two authority contexts; FD-02 still requires approval of the internal decomposition. Package names are deliberately not established.

## Traceability and acceptance

- **G02 — Ubiquitous Language v1**: Terms have one definition, examples/non-examples and ownership; BIU remains; domain roles are not external users; EOS mapping preserves project language. Sources: reset §§15–18,21,26–30; EOS ADR-0004 and ontology.
- **G03 — bounded-context model**: Each business invariant has exactly one owning context, aggregates and identities are explicit, dependencies and integration seams form a coherent context map with Founder-approved boundaries. Sources: Authority §§7,8,41; canonical-architecture responsibility list.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
