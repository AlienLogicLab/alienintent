# Hexagonal Contracts — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-03](../../work-units/pre-python-gate/PG-03.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

Ownership refinement: [binding FD-01](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md), applied through [PG-17](../../work-units/pre-python-gate/PG-17.md). FD-01 is approved; other design choices remain candidate.

## Dependency contract
Domain depends on domain value objects and policies only. Application services coordinate domain decisions and abstract ports. Adapters implement ports; composition injects them. Domain/application must not import GitHub/Jira/Codex/Cloudflare SDK types, filesystem process APIs or concrete databases. Domain errors are typed semantic rejections; transport exceptions become sanitized adapter outcomes.

## Candidate ports
| Port | Input -> output; important failure |
|---|---|
| WorkManagement | scoped provider/work reference + version -> noncanonical upstream snapshot and READY evidence; explicit release proposal -> execution admission result; execution revision/projection -> external display receipt; ambiguous/incomplete evidence rejects |
| EventIngress | authenticated envelope -> durable receipt/rejection; no receipt before durable custody |
| SourceControl | repository/candidate reference -> immutable revision/diff/publication evidence; wrong repository rejects |
| WorkerProvider | invocation + context + grants + budget -> start receipt/observable outcomes; missing capability rejects |
| Workspace | scoped owner + baseline -> owned workspace; cleanup requires same owner and proven quiescence |
| OperationalStore | scoped expected version + change set -> committed version/conflict |
| EvidenceStore | versioned observation/measurement -> immutable reference or sanitized failure |
| ContextSource | authorized source/version/query -> provenance-bearing content or unavailable |
| SecretProvider | authorized reference/consumer -> protected handle; never secret in diagnostic |
| Clock/Identifier | time/unique identity requests -> stable typed values |
| RequirementSource *(added 2026-09-22, Founder decisions v0.1 §9)* | scoped source reference/version -> provenance-bearing Source Record (external identity, revision, link, ingestion time, authority status); provider vocabulary never enters the domain; unsupported or ambiguous source rejects. Distinct from WorkManagement: one vendor may implement both through separate adapters |
| ReadinessAssessment *(added 2026-09-22, §7)* | candidate work unit text -> Readiness Assessment (raw Agent Ready assessment preserved, plus provenance: input fingerprint, Agent Ready version, contract version, provider/model, timestamp); malformed, timed-out or failed assessment is an execution failure, never a disposition. Adapters: Agent Ready CLI, Agent Ready local MCP. Domain never knows executable location, subprocess syntax, transport or package internals |
| AssessmentFeedback *(added 2026-09-22, §4; timing unsettled)* | attributable structured outcome evidence linked to a prior Readiness Assessment -> acknowledged feedback receipt; never reduced to success/failure; emission point is a Wave 2 learning objective |

Budget, assurance and release decisions are application/domain policy, not arbitrary adapter permissions. Binding FD-01 fixes direction: the Work Management Provider owns upstream product/work state; AlienIntent owns execution after explicit READY release. Adapter methods must distinguish upstream imports/release intents from downstream projection writes. There is no generic vendor status update capable of overwriting internal execution authority.

## Anti-Corruption Layers
GitHub adapter maps Project item + Issue/Draft identity and configured Status values to neutral Work Item/status semantics, with profile ownership and complete membership evidence. A Jira-work/GitLab-source scenario maps independent Jira issue/status versions and GitLab immutable revisions to the same BIU/candidate concepts. Neither vendor payload, node ID nor comment syntax enters a domain method. Ambiguous many-to-one mappings, missing membership, unsupported versions and incomplete pages fail closed; transport unavailability is distinct from wrong identity.

## Version and extensibility
Each adapter declares contract version and supported operations/capabilities. Negotiation rejects required unsupported behavior before launch. Backward-compatible optional fields cannot weaken invariants. Breaking changes require explicit migration/preflight. Both vendor scenarios are design exercises, not two functioning implementations: API stability remains unproven until two implementations pass the same conformance cases. No plugin marketplace/framework is proposed.

## ACL contract across the release boundary

An imported upstream snapshot carries provider/profile/work identity, source version or digest, upstream status, product-context provenance and observed time. It is never persisted or returned as canonical product backlog. Release proposals identify the exact READY BIU snapshot and authorization; AlienIntent admission validates them and returns its own execution identity. Internal execution commands are a distinct application interface: an external UI may explicitly submit an authorized command through an adapter, but a downstream display edit is not that command.

A projection request carries execution identity, monotonically comparable execution revision and target field mapping. The adapter serializes/fences updates per execution target or supplies an equivalent conditional-write guarantee; a stale queued revision must not overwrite a newer projection. Unsupported safe ordering requires a visible unsupported/unconfirmed outcome rather than best-effort authority changes. Projection receipts/echoes can update delivery health only. Vendor-specific conflict resolution remains adapter detail within this invariant, with transaction mechanics still candidate.

For GitHub Projects or Jira alike, READY evidence plus explicit authorized release may admit execution; an external ACCEPT field edit without an AlienIntent acceptance command cannot accept a candidate. Mapping labels is configurable; ownership direction is not.

## Traceability and acceptance

- **G04 — Hexagonal Architecture / ports-and-adapters specification**: Core/domain dependency direction and named input/output port contracts include success, rejection and unavailable evidence; no vendor types leak inward. Sources: Authority §§3,17,29,41; interface-contracts.
- **G05 — Anti-Corruption Layer rules**: GitHub and a non-GitHub example map external IDs/status/events/errors to domain concepts and fail closed on ambiguous or incomplete translations. Sources: Authority §§3,8,17; src/github/authority.mjs.
- **G27 — adapter versioning/extensibility model**: Versioned ports advertise capability/compatibility with conformance rejection; third-party replacement possible; two implementations required before API stability claim. Sources: Authority §§29–30; provider compatibility decision.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
