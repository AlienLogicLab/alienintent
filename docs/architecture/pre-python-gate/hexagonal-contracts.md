# Hexagonal Contracts — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-03](../../work-units/pre-python-gate/PG-03.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Dependency contract
Domain depends on domain value objects and policies only. Application services coordinate domain decisions and abstract ports. Adapters implement ports; composition injects them. Domain/application must not import GitHub/Jira/Codex/Cloudflare SDK types, filesystem process APIs or concrete databases. Domain errors are typed semantic rejections; transport exceptions become sanitized adapter outcomes.

## Candidate ports
| Port | Input -> output; important failure |
|---|---|
| WorkManagement | scoped external reference + expected version -> normalized work snapshot/update receipt; ambiguous/incomplete authority rejects |
| EventIngress | authenticated envelope -> durable receipt/rejection; no receipt before durable custody |
| SourceControl | repository/candidate reference -> immutable revision/diff/publication evidence; wrong repository rejects |
| WorkerProvider | invocation + context + grants + budget -> start receipt/observable outcomes; missing capability rejects |
| Workspace | scoped owner + baseline -> owned workspace; cleanup requires same owner and proven quiescence |
| OperationalStore | scoped expected version + change set -> committed version/conflict |
| EvidenceStore | versioned observation/measurement -> immutable reference or sanitized failure |
| ContextSource | authorized source/version/query -> provenance-bearing content or unavailable |
| SecretProvider | authorized reference/consumer -> protected handle; never secret in diagnostic |
| Clock/Identifier | time/unique identity requests -> stable typed values |

Budget, assurance and release decisions are application/domain policy, not arbitrary adapter permissions. FD-01 must resolve the authoritative work-state ownership before WorkManagement update contracts can be adopted.

## Anti-Corruption Layers
GitHub adapter maps Project item + Issue/Draft identity and configured Status values to neutral Work Item/status semantics, with profile ownership and complete membership evidence. A Jira-work/GitLab-source scenario maps independent Jira issue/status versions and GitLab immutable revisions to the same BIU/candidate concepts. Neither vendor payload, node ID nor comment syntax enters a domain method. Ambiguous many-to-one mappings, missing membership, unsupported versions and incomplete pages fail closed; transport unavailability is distinct from wrong identity.

## Version and extensibility
Each adapter declares contract version and supported operations/capabilities. Negotiation rejects required unsupported behavior before launch. Backward-compatible optional fields cannot weaken invariants. Breaking changes require explicit migration/preflight. Both vendor scenarios are design exercises, not two functioning implementations: API stability remains unproven until two implementations pass the same conformance cases. No plugin marketplace/framework is proposed.

## Traceability and acceptance

- **G04 — Hexagonal Architecture / ports-and-adapters specification**: Core/domain dependency direction and named input/output port contracts include success, rejection and unavailable evidence; no vendor types leak inward. Sources: Authority §§3,17,29,41; interface-contracts.
- **G05 — Anti-Corruption Layer rules**: GitHub and a non-GitHub example map external IDs/status/events/errors to domain concepts and fail closed on ambiguous or incomplete translations. Sources: Authority §§3,8,17; src/github/authority.mjs.
- **G27 — adapter versioning/extensibility model**: Versioned ports advertise capability/compatibility with conformance rejection; third-party replacement possible; two implementations required before API stability claim. Sources: Authority §§29–30; provider compatibility decision.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
