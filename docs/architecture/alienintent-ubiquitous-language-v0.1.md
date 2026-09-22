# AlienIntent Ubiquitous Language — v0.1

**Status:** v0.1 — Founder-reviewed first canonical pass — subject to evidence-driven refinement.
**Date:** 2026-09-22. **Source:** Founder Architecture Decisions and Ubiquitous Language v0.1
(`docs/decisions/alienintent-agent-ready-founder-decisions-and-ubiquitous-language-v0.1.md`),
reconciled against Architecture Authority, the software-factory plan, SF-REQ definitions, binding
SWF/FD decisions, the pre-Python candidate domain model, and the Agent Ready v0.1 specification,
schema and prompt.

This is the artifact Architecture Authority §9 and §44(2) reserve for the Ubiquitous Language.
Once approved it is authoritative across code, architecture, docs, prompts, control plane,
integrations and work packets. It defines AlienIntent's language only. **Agent Ready's language
is owned by the Agent Ready product** (`agent-ready/docs/ubiquitous-language.md`) and is
referenced here, never redefined.

Each term gives one definition, the canonical owner of the invariant it names, and what it is
*not*. Where a term collides with an established term elsewhere, the collision is recorded in §4
rather than silently normalized.

---

## 1. Boundary invariants

These are stated once here because they govern how every other term is used.

> **Agent Ready disposition is an assessment result, not an AlienIntent or Work Management
> lifecycle state.** — owner: SF-REQ-015 (amended 2026-09-22).

> **Never project AlienIntent / Work Management lifecycle vocabulary back into Agent Ready's
> assessment vocabulary.** Agent Ready has exactly `READY`, `CLARIFY`, `SPLIT`, `HOLD`. `BLOCKED`
> is an AlienIntent planning / work-management / verdict state and is never an Agent Ready
> disposition. — owner: SF-REQ-015.

> **Agent Ready gives the judgment. AlienIntent performs the authority-bearing mutation.** —
> owner: SF-REQ-013 (split/replan transaction, amended 2026-09-22) and SF-REQ-015 (readiness
> integration).

> **Authorized product intent must be converted into executable work without losing, inventing,
> weakening or silently reallocating obligations.** — owner: the Requirements / Planning bounded
> context (Architecture Authority amendment 2026-09-22; FD-02 refinement).

> **Cognition may be episodic. Deterministic monitoring must be durable.** — owner: SWF-27 /
> SF-REQ-053 (already stated there as bootstrap evidence; not duplicated).

> **Implementation workers do not invent architecture policy.** — owner: Architecture Authority
> §45 (refined 2026-09-22) and SWF-25's design-authority boundary.

Historical vocabulary is preserved as history. Wave 1 and the post-Wave-1 programme assessed
readiness with an **AlienIntent bootstrap assessor** — a coordinator-run prompt that borrowed the
Agent Ready contract shape and returned the historical vocabulary `READY / BLOCKED /
NEEDS_CLARIFICATION / SPLIT_RECOMMENDED` (bootstrap-assessor, not Agent Ready). Those records
are retained verbatim as evidence and are not Agent Ready assessments. Where an old record says a Project item was `BLOCKED` while the assessor returned a
non-READY disposition, both facts are preserved distinctly.

---

## 2. Terms

### Project and intake

**Project** — One independently governed software/product system operated by an AlienIntent
installation, with its own sources, repositories, work-management configuration, policies,
authority and evidence. AlienIntent self-building is one Project instance; any other product is
another; future Projects are first-class. Owner: Architecture Authority §1 (profiles). Not: a
GitHub repository, a Work Management provider's "project" object, or a Profile (the isolated
configuration/state namespace that *hosts* a Project — see the candidate domain model).

**Proposal** — A candidate change in product intent submitted for evaluation; immutable,
noncanonical provenance until admitted through applicable authority. Not yet an authorized
Requirement. Owner: SF-REQ-055.

**Requirement Source** — An external or internal system from which requirement or proposal
information is obtained, reached through the `RequirementSource` port. Examples: GitHub
Issues/Projects, Jira, Linear, Azure DevOps, GitLab, local files, structured product documents,
AlienIntent-native proposal intake, imported prototypes. Owner: SF-REQ-011 (amended 2026-09-22).
Not: a Work Management Provider — a source supplies requirement information; a provider is the
system in which product/work state is represented and projected. One system may play both roles
through two adapters.

**Source Record** — The provider-specific external record observed through a Requirement Source
(an Issue, an Epic, a document section). AlienIntent preserves its identity, revision, link,
ingestion time and authority status as provenance, but provider vocabulary does not enter the
core domain: a Jira Epic is not intrinsically a Requirement; a GitHub Issue is not intrinsically a
BIU; a Linear Project is not intrinsically a Wave. Owner: SF-REQ-011.

**Requirement** — An authorized statement of product capability, behaviour, constraint or outcome
that AlienIntent must preserve through specification, design, planning and execution. Identified
by a stable `SF-REQ-NNN`-form identifier (the Wave 2 design pins the recognised grammar). Owner:
SF-REQ-011 (Requirements IR). Not: a Source Record, a Proposal, or a BIU.

**Requirement Provenance** — The durable relationship between a Requirement and the Source
Records, Proposals, decisions and authority from which it was derived. Owner: SF-REQ-011.

**Specification** — A clarified, sufficiently explicit description of required intent, scope,
constraints, acceptance and non-goals, suitable for design. Owner: lifecycle authority (Architecture
Authority §9 `SPECIFY`); performed by the Requirements / Planning bounded context.

### Design and planning

**Design Contract** — The explicit architecture / invariant / interface / failure / recovery
contract governing implementation of one specified capability or coherent design area. Owner:
SF-REQ-051 / SWF-25.

**Design Verification** — Independent challenge of a Design Contract before implementation
planning: missing owners, impossible premises, inconsistent boundaries, unproven platform
assumptions, hidden architectural decisions. Mechanical checks first. Owner: SF-REQ-051 / SWF-25.

**Plan** — An authorized technical decomposition and dependency strategy for implementing verified
design. Owner: Architecture Authority §9 `PLAN`; produced by the Requirements / Planning bounded
context under SF-REQ-013.

**Wave** — A Founder-authorized set of Requirements / Design / Plan scope approved for autonomous
factory execution under a defined authority and budget envelope. Not merely a label or milestone;
never invented by AlienIntent. Owner: Founder authority (software-factory plan §Planning
authority).

**Bounded Implementation Unit (BIU)** — A bounded executable work contract derived from authorized
Plan scope, containing enough intent, constraints, acceptance, proof and authority for
implementation without inventing product or design policy. Owner: SF-REQ-010. Not: a Work Item,
an Issue, or a Wave.

**BIU Compiler** — The Requirements / Planning capability that materializes authorized planning
intent into candidate BIUs while preserving traceability and obligations. It derives the initial
decomposition itself; it does not require an externally hand-authored allocation as input. Owner:
SF-REQ-013.

**Replan** — An authority-bearing change to technical decomposition after the current Plan / BIU
structure is found inadequate. Owner: SF-REQ-013 (amended).

**Split Transaction** — A specific Replan operation that replaces or restructures one work unit into
multiple units while preserving every authorized Obligation, dependency and required integration
proof, recording lineage, rewriting dependencies deterministically, invalidating stale Readiness
Assessments, and re-submitting resulting candidates for assessment. Owner: SF-REQ-013 (amended);
candidate design: `docs/evidence/wave1-biu-split-replan-design.json`. Not: an Agent Ready `SPLIT`
disposition, which is the *judgment* that a Split Transaction may be warranted.

**Obligation** — A required piece of intent, acceptance, verification, evidence, dependency or
integration responsibility that must not disappear during compilation or replanning. Owner:
SF-REQ-013.

**Obligation Conservation** — The invariant that every authorized Obligation remains attributable
after compilation, split or replan. Owner: SF-REQ-013 (amended); SWF-33 is the worked precedent.

**Integration Parent** — A retained work / integration unit that owns cross-child integration
proof after a split when no child alone can satisfy the original integrated obligation. Owner:
SF-REQ-013 (amended); `retained_integration_parent` in the split design.

### Readiness

**Readiness Assessment** — AlienIntent's immutable recorded use of an Agent Ready Assessment: the
raw assessment plus provenance (input identity/fingerprint, Agent Ready version, assessment
contract version, provider/model provenance, timestamp) and AlienIntent's current read-time
interpretation. AlienIntent does not own readiness semantics. Owners: SF-REQ-015 for obtaining and
honouring it through the `ReadinessAssessment` port; SF-REQ-029 (amended) for retaining it
immutably as an observation. Not: an Agent Ready *Assessment* (which is Agent Ready's artifact
and language), and not a lifecycle state.

**READY (disposition)** — Agent Ready's judgment that a work unit is sufficiently coherent and
constrained to hand to an autonomous implementation agent. It is not execution authorization
and not the AlienIntent lifecycle state `READY`. See §4 collision *READY*.

**CLARIFY / SPLIT / HOLD (dispositions)** — Agent Ready's judgments; defined by Agent Ready.
AlienIntent's *responses* are: `CLARIFY` → resolve only the material owner question(s) through
existing decision authority (SF-REQ-035 Decision Inbox), then reassess; `SPLIT` → a Split
Transaction, then reassess each resulting candidate; `HOLD` → satisfy the prerequisite, then
reassess. Resolved prerequisites never rewrite an old disposition; reassessment is required.
Owner: SF-REQ-015.

### Allocation and execution

**Allocation** — The act of binding authorized work to an eligible execution resource / provider /
model under policy, capability, capacity and budget constraints, producing an attributable
Allocation decision with limits and authority basis. Owner: SF-REQ-026 (amended 2026-09-22).
Not: scheduling (which READY BIU is next — SF-REQ-002), and not the compile-time mapping of
obligations to units (see §4 collision *Allocation*).

**Allocator** — The cognizant AlienIntent capability that makes attributable Allocation decisions.
Deterministic policy settles trivial cases; an adequate local model is the default for allocation
cognition where configured and demonstrated capable; frontier/paid models are optional escalation.
Owner: SF-REQ-026 (amended); initialization of its providers: SF-REQ-037/038.

**Execution Packet** — The exact bounded runtime authority, resources, limits and context assigned
to one work execution attempt or cycle. Owner: SF-REQ-009 (kernel enforces) with SF-REQ-010
(BIU carries budget/capabilities); the canonical-architecture "worker packet" (goal, starting
authority, allowed scope, required evidence, stop condition, escalation condition) is its content
baseline.

**Provider** — A system capable of supplying model/agent execution, reached through the
`WorkerProvider` port and advertising capabilities. Owner: SF-REQ-025.

**Worker** — A concrete execution actor operating under an Execution Packet. PRODUCER and
VERIFIER are AlienIntent domain roles; Morty and JC are bootstrap identities. Owner: Architecture
Authority §4.

**Worker Capability** — A declared or verified capability relevant to Allocation. Owner: SF-REQ-025.

**Deterministic Test Worker** — A deterministic implementation of the same worker-facing port /
protocol used by production workers, producing scripted valid and invalid worker behaviours so the
real control plane, lifecycle, recovery, identity, evidence and fault handling can be exercised
without model inference. It does not simulate frontier-model intelligence and the core never
special-cases it. Owner: SF-REQ-039 (renamed 2026-09-22; formerly "Fake-agent/offline factory
proof"). Not: a fake agent, a mock lifecycle, or a test-mode shortcut.

**Invocation** — One attempt to start or use a Worker, with unique identity and pinned context /
policy / input versions. Not an Execution Cycle. Owner: SF-REQ-009.

**Execution Cycle** — A semantic implementation / verification / rework cycle governed by lifecycle
rules; provider retry or failover within the same phase does not create a new cycle. Owner:
SF-REQ-009 (SWF-32 amendment). *Cycle count is not invocation count.*

**Candidate** — A concrete implementation artifact/result proposed for verification/acceptance,
identified immutably (revision, provenance). Owner: SF-REQ-007.

**Candidate Custody** — The guarantee that an exact Candidate is durably identifiable, retrievable
and attributable throughout verification and acceptance. Owner: SF-REQ-007 (SWF-30 amendment).

### Evidence and verdicts

**Observation** — A factual recorded occurrence. Not a Verdict. Owner: SF-REQ-016.

**Verdict** — An authoritative conclusion about work/result status produced by the designated
authority/process. Provider process exit or textual success is never automatically a Verdict.
AlienIntent verdict vocabulary includes `ACCEPT / REJECT / BLOCKED` and satisfaction states such
as `UNVERIFIED / BLOCKED / REJECT`; this `BLOCKED` is a verdict/lifecycle word, not a readiness
disposition. Owner: SF-REQ-016.

**Evidence** — Durable information supporting an Observation, Verdict, requirement-satisfaction
claim, recovery action or learning conclusion. Owner: SF-REQ-017 / Architecture Authority §26.

**Quality Evidence** — Derived evidence about quality, yield, failure and rework created from
durable observations, preserving fact versus interpretation; `UNKNOWN` is never silently zero.
Owner: SF-REQ-030.

**Engineering Trajectory** — Observable ordered engineering facts and artifact lineage,
independent of Git commits; never private chain-of-thought. Owner: SF-REQ-029.

**REVIEW** — The lifecycle activity that discovers failure classes AlienIntent does not yet know
how to mechanize. *REVIEW explores.* Owner: SWF-24 §Lifecycle role.

**VERIFY** — The lifecycle activity that proves known requirements and invariants AlienIntent
already knows how to check. *VERIFY accumulates.* Owner: SWF-24 §Lifecycle role.

**Deterministic failure-class promotion** — The governed learning mechanism that converts suitable
recurring REVIEW discoveries into deterministic future VERIFY / enforcement capability, complete
only with proven-red evidence. Owner: SWF-24 / SF-REQ-050. *This is the product-native term.* The
concept was informed by the external **Gap Trap** project; "Gap Trap" is attribution, not
AlienIntent language, and is not a canonical noun or verb here (§4).

**Failure Class** — A generalized category of defect or unsafe behaviour discovered from one or
more concrete findings. Owner: SF-REQ-029 (classification) and SF-REQ-050 (promotion).

**Proven Red** — Evidence that a deterministic control fails when a meaningful representative
violation is introduced; where practical, real-data shape complements synthetic mutation. A check
that cannot fail is not evidence. Owner: SWF-24 / SF-REQ-050; SF-REQ-018 for fitness rules.

### Attention, decisions, control

**Attention Item** — A durable indication that something requires model or operator judgment. Not
itself a Founder Decision. Owner: SF-REQ-053 (activation boundary; SWF-27 bootstrap evidence).

**Founder Decision** — A durable human authority decision required because existing authority does
not resolve a material product, architecture, policy, risk or budget question. Owner: SF-REQ-006 /
SF-REQ-035; escalation rule Architecture Authority §45.

**Architecture Decision Required** — A Founder Decision specifically concerning architecture policy
that implementation agents are not authorized to invent. It is a *kind* of `HumanDecisionRequired`
routed through the Decision Inbox, not a second mechanism. Owner: Architecture Authority §45
(refined 2026-09-22).

**Decision Inbox** — The operator-facing surface for unresolved Founder Decisions with enough
context to decide without reconstructing agent history; decisions are durable and unblock work.
Owner: SF-REQ-035. Not: the bootstrap attention queue (SWF-27).

**Work Management Provider** — The external system used to represent and project product / work
state and relationships (GitHub Projects, Jira, …), reached through the `WorkManagement` port
and ACL. Its model is not the AlienIntent domain model. Owner: SF-REQ-005 / FD-01.

**Projection** — A representation of AlienIntent-owned or source-owned domain state in an external
Work Management Provider. A Projection is never authority. Owner: FD-01 §4.

**Release** — The explicit authority-bearing transition that allows an eligible READY work item to
enter implementation under a defined baseline and execution envelope. Owner: FD-01 §3 /
SF-REQ-002 (admission amendment). Not: readiness, a display-field edit, or merge.

**Monitoring** — Durable deterministic observation / reconciliation infrastructure independent of
model-session lifetime (liveness, lifecycle, queues/attention, service health, anomaly detection,
already-authorized reconciliation). Owner: SF-REQ-053 / SWF-27; liveness specifically SF-REQ-056 /
SWF-29.

**Coordinator** — A bounded cognitive/control role that evaluates durable state and makes or
requests authorized coordination decisions. An episode need not be permanent; conversation is
never authority. Owner: SF-REQ-053 / SWF-27.

**Learning Proposal** — A cited recommendation to change policy, routing, context, verification or
design based on evidence; not active policy until approved under promotion authority. Owner:
SF-REQ-032.

**Assessment Feedback** — Attributable, structured downstream outcome evidence that AlienIntent, as
an Agent Ready consumer, derives from durable execution evidence and returns to Agent Ready's
feedback contract (for example `READY → first-pass accepted`, `SPLIT → split proved unnecessary`,
`HOLD → prerequisite proved unnecessary`). Never reduced to success/failure. Owner: SF-REQ-030
(amended 2026-09-22). The lifecycle point at which feedback is mature is **not settled** and is a
Wave 2 design-learning objective. Agent Ready's corpus and rule improvement remain Agent Ready's,
governed and versioned.

**Surrogate Readiness Assessment** *(historical)* — A Wave 1 readiness assessment produced by the
AlienIntent bootstrap assessor: a coordinator-run Codex or Claude prompt shaped to the Agent Ready
contract, not an execution of the Agent Ready product. Retained verbatim as evidence with its
producer declared in `docs/evidence/wave1-readiness-assessment-provenance.json`; never
represented as a native Agent Ready assessment. The recorded instance of the *Authoritative
Capability Substitution* failure class (Architecture Authority amendment (b)).

### Retained candidate-model terms

The pre-Python candidate domain model (`docs/architecture/pre-python-gate/domain-model.md`)
already defined **Product Intent**, **Work Item**, **Profile**, **Verification**, **Review**,
**Acceptance**, **Closure**, **Trajectory** and **Capability Grant**. They stand unchanged and are
incorporated by reference; *Trajectory* and *Verification/Review* are the same concepts as
Engineering Trajectory and VERIFY/REVIEW above.

---

## 3. Lifecycle and the accepted starting workflow

Lifecycle semantics are unchanged: `CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT → VERIFY
→ REVIEW → ACCEPT → DONE` (Architecture Authority §9), with `DESIGN` and `DESIGN VERIFICATION` as
semantic sub-stages inside SPECIFY/PLAN (SWF-25). Merge is closure, not a state.

The accepted *initial* user model (Founder decisions v0.1 §18; a starting point, not final UX):

```text
proposal → CAPTURE → clarify / deduplicate / authority → SPECIFY → DESIGN
  → independent Design Verification → PLAN → candidate BIUs → Agent Ready assessment
  → Wave approval packet → Founder authorizes Wave → autonomous execution
  → Founder interrupted only for real authority decisions → Wave closure / learning
```

Future project initialization (`alienintent init`, validated by `alienintent doctor`) must be able
to configure Project identity, Requirement Sources, the Work Management Provider, repositories,
authority, the Agent Ready interface, workers/providers/models, the local allocator model,
escalation providers, budgets, WIP/concurrency, sandbox/custody, evidence, monitoring, the
Decision Inbox/notifications, and security/privacy policy. Owner: SF-REQ-037/038; polish is
deferred, extension points are protected.

---

## 4. Terminology collisions recorded (not silently normalized)

| Term | Collision | Resolution / recommendation |
|---|---|---|
| **READY** | AlienIntent lifecycle state `READY` (Work Management, FD-01) vs Agent Ready disposition `READY` vs EOS "readiness" (ADR-0004 translation already recorded). | Both stand. Qualify in prose: *READY (lifecycle)* vs *READY (disposition)*. A READY disposition is one input to lifecycle READY; neither implies Release. |
| **BLOCKED** | AlienIntent planning / verdict state vs the bootstrap assessor's disposition name. | `BLOCKED` is never an Agent Ready disposition; the assessment-side concept is `HOLD`. Historical records keep both facts distinct. |
| **Allocation** | Founder UL: binding work to a worker/provider/model (execution). Wave 2 design (SF-REQ-013 contract, R1-GAP-013-ALLOCATION, AR13-CQ-001): the compile-time mapping of obligations to units. | The execution sense is canonical **Allocation**. The compile-time sense is renamed **obligation mapping** ("obligation-to-unit extent mapping", the design contract's own phrase). Existing artifacts keep their historical wording. |
| **Requirement Source** vs **Work Management Provider** | The candidate `WorkManagement` port covered both import and projection. | Two ports, two roles: `RequirementSource` (obtain requirement information) and `WorkManagement` (represent/project work state). One vendor may supply both through separate adapters. |
| **Assessment** vs **Readiness Assessment** | Agent Ready owns *Assessment*; AlienIntent needs a name for its retained record plus provenance. | *Assessment* is Agent Ready's term; *Readiness Assessment* is AlienIntent's record of one. |
| **SPLIT** vs **Split Transaction** | Agent Ready's judgment vs AlienIntent's mutation. | Kept distinct by definition; the invariant *judgment / mutation* names the boundary. |
| **Owner Question / Engineering Unknown** | Founder UL names vs Agent Ready's established *Owner Unknown / Implementation Unknown* (spec §3.5, schema fields). | Agent Ready's terms win inside Agent Ready; AlienIntent uses Agent Ready's terms when speaking of assessments. Recorded in the Agent Ready UL. |
| **Gap Trap** | External project name used as a noun/verb in SWF-24 prose, the post-Wave-1 programme plan and its artifacts. | Not AlienIntent UL. Canonical term: *deterministic failure-class promotion*. Attribution preserved; historical artifact names (e.g. `wave1-gap-trap-promotion-backlog`) unchanged. |
| **Fake worker / fake agent** | SF-REQ-039's former title. | Replaced by *Deterministic Test Worker*; requirement identity preserved. |
| **Verification / Review** (candidate model) vs **VERIFY / REVIEW** (lifecycle) | Same concepts, two spellings. | Lifecycle spelling for lanes; candidate-model nouns for the activities. No semantic difference. |
| **Monitoring** | Founder UL term vs SWF-27's "persistent monitoring is operational infrastructure". | Same invariant; SWF-27 remains the owner, this entry cross-references. |

---

## 5. Explicitly not canonical

- **Gap Trap** — attribution only (see §4).
- **Owner Question**, **Engineering Unknown** as AlienIntent nouns — use Agent Ready's terms.
- **"Fake agent" / "fake worker"** — superseded.
- Any vendor noun (Issue, Epic, Ticket, Sprint, Board) as a domain concept.
