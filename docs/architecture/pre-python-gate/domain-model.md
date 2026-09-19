# Domain Model — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-02](../../work-units/pre-python-gate/PG-02.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Candidate ubiquitous language v1
| Term | Meaning and identity | Not the same as |
|---|---|---|
| Product Intent | Desired problem/outcome before technical allocation; stable work identity | Repository Issue |
| Work Item | Repository-neutral unit of intent with lifecycle semantics | GitHub Project item ID |
| BIU | Bounded Implementation Unit; immutable version of executable scope, authority and acceptance | Whole feature or arbitrary shell session |
| Release | Policy-authorized admission of a READY BIU version | Readiness assessment |
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

## Proposed context map (FD-02)
| Context | Owns | Consumes / publishes |
|---|---|---|
| Work Coordination | Work/BIU versions, dependencies, release, acceptance/closure guards | Authority and evidence references; semantic commands/events |
| Execution | Invocation, reservation, worker/workspace ownership, cancellation | Released BIU and capability/budget decision; execution outcomes |
| Context Assembly | Role/phase context manifests and retrieval policy | Versioned authorized sources; bounded context bundles |
| Evidence and Learning | Separate trajectory, measurements and proposed learned policy | Observable events; evidence projections and reviewed proposals |
| Installation | Profile configuration, adapters, secret references and health | Explicit operator configuration; validated installation capabilities |

These are logical boundaries in one service, not five deployed microservices. The Control Plane is application orchestration over these contexts, not a separate state owner. Cross-context references use IDs/versioned contracts, never another context's storage model. Work Coordination alone guards lifecycle progression; Execution alone owns invocation resource release. FD-01 still governs whether lifecycle is persisted internally or projected from external authority.

## EOS translation
BIU maps to the bounded execution/acceptance aspects of an EOS Work Order, without claiming every BIU is an organizational Work Order. AlienIntent Profile is not EOS Project. Trajectory facts are Evidence; an interpretation is a Claim with uncertainty; accepted learning is a reviewed Knowledge Claim. A proposed policy change maps to a Decision/proposal, never automatic adoption. ADR-0004 preserves both vocabularies.

## Checks
Producer invocation I1 cannot approve candidate C1 as an independent verifier. A new candidate C2 cannot reuse acceptance of C1. Every state-changing invariant above has one owner; an adapter translating Issue42 cannot manufacture a Work Item identity by repository number alone. FD-02 requires approval of this partition; package names are deliberately not established.

## Traceability and acceptance

- **G02 — Ubiquitous Language v1**: Terms have one definition, examples/non-examples and ownership; BIU remains; domain roles are not external users; EOS mapping preserves project language. Sources: reset §§15–18,21,26–30; EOS ADR-0004 and ontology.
- **G03 — bounded-context model**: Each business invariant has exactly one owning context, aggregates and identities are explicit, dependencies and integration seams form a coherent context map with Founder-approved boundaries. Sources: Authority §§7,8,41; canonical-architecture responsibility list.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
