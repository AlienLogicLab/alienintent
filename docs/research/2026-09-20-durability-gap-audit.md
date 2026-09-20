# Durability-gap audit — 2026-09-20

Two passes, both 2026-09-20. The second pass is the
[coordinator role tooling addendum](#addendum--coordinator-role-tooling-and-safe-operational-interfaces),
which refines one row of the matrix below.

## Method and boundary

This audit treats canonical Product Requirements and binding decision records as
authority. Proposals and execution evidence identify gaps but do not create
authority. It is documentation/intake work only: no BIU, implementation,
runtime, worker, service, Project Status or live Wave 1 action was changed.
Proposal Intake and the amendments recommended below were subsequently
processed under explicit Founder instruction; see the dated disposition at the
end of this report.

## Traceability matrix

| Candidate capability / decision | Classification | Authority inspected | Gap | Recommended durable action | Target artifact/path |
|---|---|---|---|---|---|
| Execution Evidence Derivation and Consistency Verification | **NEW REQUIREMENT** | SF-REQ-016, 020, 024, 029, 030; existing trajectory/quality evidence | SF-REQ-030 requires derivation but not mechanical reconciliation that detects drift between factual events and derived metrics. | Submit for normal Product Requirement intake; do not prescribe storage or runtime design. | [PROP-2026-0004](../proposals/PROP-2026-0004-execution-evidence-derivation-and-consistency-verification.md) |
| Proposal Intake as a product capability | **NEW REQUIREMENT** | `docs/proposals/INDEX.md`; SF-REQ-011–016, 032; SF-REQ-041–044 | The index is an operating convention; external-artifact intake is distinct. Neither provides provider-neutral, idempotent proposal-to-canonical admission. | Submit for normal Product Requirement intake. | [PROP-2026-0005](../proposals/PROP-2026-0005-proposal-intake-as-product-capability.md) |
| SF-REQ-050 / SWF-24 mutation semantics | **AMEND EXISTING** | SF-REQ-050 / SWF-24; SWF-23; SWF-26 historical mutation gate | Existing authority requires meaningful violations and retained promotion evidence, but does not explicitly retain semantic violation, applicability, expected/actual result, provenance/version, or the `NOT_APPLIED` rule. | Amend the canonical requirement and decision under normal authority; do not create a duplicate requirement. | SWF-24 / Issue [#61](https://github.com/AlienLogicLab/alienintent/issues/61) |
| SF-REQ-007 VERIFY candidate-identity admission | **ALREADY COVERED** | SF-REQ-007; candidate-publication invariant; SWF-22; PY-06 contract | No authority gap: exact identity, independent retrievability/read-back and inadmissible VERIFY are explicit across source-control and local-artifact forms. | Treat missing/unresolved identity as deterministic admission and negative-test work. | SF-REQ-007 / PY-06 implementation and verification obligation |
| Rejection/failure taxonomy | **AMEND EXISTING** | SF-REQ-029, 030, 024; PY-04 execution evidence; PROP-2026-0004 | The plan names failure taxonomy but does not define the classifications needed for derived counts and explicit UNKNOWN/partial states. | Add evidence-backed taxonomy to SF-REQ-029/030 when PROP-2026-0004 is canonicalized; do not create a second taxonomy requirement. | PROP-2026-0004; then canonical SF-REQ-029/030 |
| Verification liveness | **IMPLEMENTATION DEBT** | SWF-09; scheduling/recovery design; PY-04 and PY-06 contracts | Hard wall-clock, cancellation, finite retry/timeout and bounded outcomes are already required; PY-04 shows the need for enforcement and tests. | Implement timeout classification and hang-to-failure/cancellation behavior under existing authority. | SWF-09 / SF-REQ-009 implementation and verification backlog |
| Coordinator role tooling and safe operational interfaces | **AMEND EXISTING** + **IMPLEMENTATION DEBT** | SF-REQ-034 / Authority §36; SWF-27 / SF-REQ-053; Authority §§11, 13, 18, 20, 21, 24; SWF-21; SF-REQ-007, 008, 009, 029, 030; control-plane, capabilities-and-assurance and context-and-memory candidates; PY-08 contract | Nine of twelve candidate operations are already owned by SF-REQ-034 / §36. Awaiting a lifecycle transition, and tracked auxiliary background tasks with durable identity, are owned by nothing. No authority states the tool-first obligation or governs promotion of recurring operational work into tools. | Amend SF-REQ-034 / §36, SWF-27 / SF-REQ-053 and Authority §13; fold the two missing operations into PY-08 before release. **No new Product Requirement.** | [Addendum](#addendum--coordinator-role-tooling-and-safe-operational-interfaces); SF-REQ-034 / Issue [#13](https://github.com/AlienLogicLab/alienintent/issues/13); SWF-27 / SF-REQ-053 / Issue [#64](https://github.com/AlienLogicLab/alienintent/issues/64) |
| Temporary/bootstrap controls | **ALREADY COVERED** | SWF-26; SWF-27 / SF-REQ-053 | SWF-26 records authority, scope, expiry, provenance and replacement target for the historical gate. SWF-27 makes the general no-silent-promotion rule durable. | Preserve SWF-26 as expired evidence; apply standing rule through SF-REQ-053. | SWF-26 and SWF-27 |

## Amendments recommended by the audit

### SF-REQ-050 / SWF-24 — deterministic mutation semantics

Target: `docs/decisions/2026-09-20-deterministic-failure-class-promotion.md`
and canonical Product Issue #61.

> For each promoted mutation, proven-red or negative-control check, retain the
> governing binding rule; the semantic violation intentionally introduced;
> applicability conditions; expected failing evidence; actual result; the
> implementation/reference and provenance/version of the mutation/check; and
> one of `KILLED`, `SURVIVED`, or `NOT_APPLIED`. `NOT_APPLIED` records why the
> mutation could not be applied and must never be counted as `KILLED`. A source
> patch alone is insufficient: the record must state the rule violation the
> mutation is intended to demonstrate.

This is an evidence-shape amendment only. It does not revive SWF-26 or impose a
retroactive Wave 1 gate.

### SF-REQ-029 / SF-REQ-030 — rejection and failure taxonomy

Target: canonical SF-REQ-029 and SF-REQ-030 artifacts, if and when
PROP-2026-0004 is admitted.

> Trajectory events may carry a versioned, evidence-backed failure
> classification that distinguishes behavioral defects, evidence/proof defects,
> custody/identity defects, tooling/publication defects, process-instruction
> adherence, genuine authority requirements, false/escalated authority
> requests, and provider-capacity interruptions where observed. Quality
> Evidence derives aggregate counts and explicit UNKNOWN/partial states from
> cited trajectory events and named sources; deterministic reconciliation rejects
> contradictions where the facts make reconciliation possible.

The vocabulary is proposed, not a schema change or a claim that every event has
every classification.

## Confirmed coverage notes

### Candidate identity

SF-REQ-007 requires that VERIFY never begins until the exact candidate is
durably identifiable and retrievable by a fresh independent verifier, enforced
by the control plane. The candidate-publication invariant requires recorded
ref/SHA, independent retrieval and rejection of unpublished candidates. SWF-22
adds semantic/content-addressed local-artifact custody transfer. PY-06 requires
typed rejection and negative proof for unreachable or mismatched candidates.

### Verification liveness

SWF-09 makes wall-clock duration and cancellation hard-enforced dimensions.
The scheduling/recovery design carries finite timeout/retry/cancellation and
explicit unresolved recovery conditions; PY-06 requires bounded timeout proof.
A hung check is therefore an implementation/verification debt under existing
authority, not a new Product Requirement.

### Temporary controls

SWF-26 expired when PY-04 reached DONE and explicitly identifies SF-REQ-050 as
the normal replacement path for a standing mutation gate. SWF-27 / SF-REQ-053
generalizes the durable requirements: explicit authority, bounded scope,
expiry, provenance, replacement target, and no silent promotion into
architecture.

## Addendum — coordinator role tooling and safe operational interfaces

Second audit pass, 2026-09-20. Trigger: the long-lived Wave 1 coordinator has
repeatedly built ad hoc shell monitoring/control scaffolding and tripped over
ordinary shell and process-management hazards. This pass re-examines the
`Coordinator local tooling/watchers` row against the full canonical authority
rather than against the watcher incident alone, and **refines** that row. The
first pass was not wrong — these are not a new product capability by
themselves — but it stopped at "implementation debt" without naming which
authority owns the capability, which parts nothing owns, or what the durable
rule should say.

### Classification

> **AMEND EXISTING** (primary) + **IMPLEMENTATION DEBT** (secondary).
> **Not a new Product Requirement.**

Nine of the twelve candidate operations are already owned by SF-REQ-034 /
Architecture Authority §36. Two are owned by nothing. The tool-first rule and
the promotion rule are unstated, but each is the direct extension of a rule
that already binds — §36's no-backdoor rule and SWF-27 rules 9 and 10.
Creating a Product Requirement here would duplicate SF-REQ-034 and SF-REQ-053.

### Coverage of the candidate operational interfaces

| Candidate operation | Owning authority | Status |
|---|---|---|
| Observe BIU / lifecycle state | Authority §36 (`status`, inspect active BIUs, inspect state-machine state); SF-REQ-034; PY-08 §Scope 3 | covered |
| Inspect active invocation identity and status | Authority §36 (inspect workers/invocations); PY-08 §Scope 3 | covered |
| Inspect WIP / reservations | Authority §36 (inspect state-machine state); SF-REQ-009; scheduling-and-recovery reservation model | covered |
| Inspect candidate identity / publication status | SF-REQ-007; candidate-publication invariant; SWF-22; Authority §36 (inspect evidence) | covered |
| Inspect required evidence / check results | Authority §36 (inspect evidence); SF-REQ-016, SF-REQ-017 | covered |
| Reconcile state after restart | Authority §36 (`reconcile`, `resume`); SF-REQ-008; PY-08 §Scope 6 | covered |
| Authorized lifecycle mutation through typed operations | Authority §36 critical rule; control-plane candidate §Application model; PY-08 binding rule 1 (actor, authority, target, intent, expected version, reason, idempotency key) | covered |
| Capture coordinator observations / evidence durably | SF-REQ-029, SF-REQ-030; SWF-27 rules 3 and 9; Authority §§25–26 | covered |
| Typed inputs/outputs, explicit authority, idempotency, sanitization, nonzero exit | PY-08 binding rules 1–5; python-engineering candidate; context-and-memory candidate ("Tools carry purpose, authority, version and conditions") | covered |
| **Wait for / subscribe to a lifecycle transition** | — | **not owned** |
| **Start / stop / cancel a tracked watcher or bounded task; enumerate tracked background tasks** | — | **not owned** |
| Role-specific capability profiles | Authority §§11, 13; capabilities-and-assurance candidate (grants bind invocation/role; a default verifier profile exists); Authority §24 and G19 role/phase context compiler | owned in principle; coordinator/director role not enumerated |

Two clarifications on the unowned rows. Authority §21 prohibits polling as an
integration mechanism and prefers event-driven operation, and §18 defines event
delivery guarantees — but neither exposes an operator- or coordinator-facing
*await* primitive, so a role told to observe a transition has no sanctioned way
to do it. Authority §20 and §36 cover cancelling and inspecting **workers and
invocations** the factory itself owns; neither covers auxiliary tasks a
coordinator starts to observe the factory. Reservations under
scheduling-and-recovery name an invocation, owner, version/fence and workspace
— that is the shape a tracked background task needs, applied to a different
class of task.

### Why the failures happened

The three reported incidents — a stale hard-coded timestamp carried into a
copied watcher, a detached watcher the harness did not track, and a broad
`pkill -f` pattern that matched the command running it and killed its own
process group — are not three unrelated shell mistakes. Each is the predicted
consequence of an identified structural gap:

- **Copied, unversioned procedure.** There is no reviewed, versioned tool, so
  each episode starts from a copy of the last one. Context Engineering already
  requires tools to carry purpose, authority, version and conditions; a pasted
  shell fragment carries none of them.
- **Untracked background task.** The coordinator's own conversation was the
  only record that the watcher existed. SWF-27 rule 9 forbids exactly this for
  state; nothing yet says it about operations.
- **Pattern matching in place of identity.** `pkill -f` is process selection by
  substring because no durable task identity exists to select by. The
  repository already records the same class of weakness elsewhere:
  `docs/operations.md` notes that restart liveness uses PIDs without durable
  process-start identity, so PID reuse can retain resources conservatively.

None harmed factory state. They are evidence about missing interfaces, not
about coordinator discipline — which is the point: instructing a model to
remember safer shell technique is the intervention that does not hold, and
AlienIntent's own authority already prefers structural enforcement to prose
(SWF-24; Authority §36 critical rule; context-and-memory candidate,
"guardrails with deterministic meaning belong in enforcement, not only prose").

### Proposed amendment A1 — SF-REQ-034 / Authority §36

Targets: `docs/architecture/alienintent-architecture-authority-2026-09-19.md`
§36, the SF-REQ-034 entry in
`docs/decisions/alienintent-software-factory-plan.md`, and Product Issue
[#13](https://github.com/AlienLogicLab/alienintent/issues/13).

Add to the §36 capability list:

> - await a named lifecycle transition or terminal outcome, with an explicit
>   bounded timeout and distinct success, failure and timeout results;
> - register, enumerate, inspect and cancel tracked auxiliary background tasks
>   — watchers and bounded observation tasks — by durable task identity.

Add alongside the existing critical rule:

> **Second critical rule:**
>
> **Where AlienIntent supplies a canonical control-plane operation for a task,
> every role — human operator and model-based coordinator alike — uses that
> operation rather than synthesizing an equivalent shell procedure. Shell
> remains a bounded escape hatch for genuinely novel work; it is not the
> interface for recurring factory operations.**

Append to the SF-REQ-034 requirement text:

> Recurring control-plane operations are exposed as typed operations with
> explicit authority requirements, idempotency or exposed effect identity, and
> distinct success, failure and timeout results. Background tasks the control
> plane starts are tracked by durable identity, enumerable and individually
> cancellable, and expose enough evidence for later reconstruction. Control
> never selects a process by command-line pattern when an exact identity
> exists.

The two added operations belong in the **P0 minimum**, not the P5 polish
scope: SWF-21 already requires the coordinator to monitor for meaningful
lifecycle changes, and without them that instruction has no sanctioned
implementation.

### Proposed amendment A2 — SWF-27 / SF-REQ-053

Targets: `docs/decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md`
and Product Issue [#64](https://github.com/AlienLogicLab/alienintent/issues/64).

Extend durable rule 9:

> Rule 9 covers operations as well as state. An operation a coordinator started
> — a watcher, an observation task, any background process — is hidden state
> unless it is registered under a durable identity a successor can enumerate
> and cancel without access to the prior conversation. If terminating the
> coordinator would orphan a running operation, or if a successor could not
> discover that the operation exists, the operation has not been made durable.

Add durable rule 11:

> **11. Recurring operational work is promoted, not re-improvised.** A
> coordinator may synthesize an ad hoc procedure for genuinely novel work. Once
> the same operation recurs, proves valuable, or fails in execution, it becomes
> a candidate for promotion into a reusable tool, skill or control-plane
> operation through the normal requirement, design and BIU path. Promotion is
> governed: writing a useful script creates no permanent architecture, and
> continued use of an ad hoc procedure is not adoption. This is the
> constructive counterpart of rule 10 — rule 10 stops temporary behaviour
> becoming architecture silently; rule 11 stops useful behaviour remaining ad
> hoc indefinitely.

Promotion path, for the record and not as a new mechanism:

```text
ad hoc model procedure
    ↓  recurs, fails, or proves valuable
candidate reusable operation
    ↓  requirement / design / BIU path
tool, skill or control-plane operation
    ↓
role capability profile
```

This is the same shape SF-REQ-050 / SWF-24 already uses to promote a proven
failure class into a standing deterministic check. A2 applies that shape to
operational tooling rather than to verification checks, which is why it is an
amendment to SWF-27 and not a second promotion requirement.

### Proposed amendment A3 — Authority §13 role capability profiles

Targets: `docs/architecture/alienintent-architecture-authority-2026-09-19.md`
§13, and the capability/authority model design item (§44.9) carried by
`docs/architecture/pre-python-gate/capabilities-and-assurance.md`.

Add to §13:

> Capability profiles bind to an invocation's role as well as to its BIU. Roles
> that operate outside a single BIU — coordinator, and any future director role
> — carry their own profile. A coordinator profile grants the minimum reusable
> control-plane operations required for coordination and nothing further;
> producer and verifier profiles remain narrower and task-scoped. No role
> receives another role's operational surface by default.

A3 is the smallest of the three. Authority §11 and the capabilities-and-assurance
candidate already bind a grant to invocation/role and already define a default
verifier profile; Authority §24 and G19 already select tools by role and phase.
What is missing is only that COORDINATOR is not an enumerated role in either —
the role/phase compiler names PRODUCER, VERIFIER, closure and operator. That is
design work under SF-REQ-051, not new product scope.

### Interaction with SWF-27 / SF-REQ-053

These amendments complement bounded coordinator episodes rather than
duplicating them:

- bounded episodes reduce hidden **cognitive** state; stable operational tools
  reduce hidden **procedural** state;
- tracked operations make coordinator replacement and restart safe in practice,
  which is what rule 8's restart-equivalence target property asserts in
  principle;
- a successor can inspect active operational tasks without inheriting the prior
  coordinator's conversation — the operational case of rule 3.

SF-REQ-053 is P0 / Wave 2. A1's two operations are Wave 1 scope under
SF-REQ-034. They are deliberately kept in separate authority: the interface
belongs to the control plane, the rule about using it belongs to coordinator
tenure policy.

### Implementation debt

| # | Debt | Owning authority | Smallest action |
|---|---|---|---|
| D1 | The SF-REQ-034 P0 minimum is unimplemented. `src/alienintent/control_plane/` is an empty package and PY-08 sits in TASKS behind PY-04 → PY-07. The coordinator improvised because the surface it should have used does not exist yet. | SF-REQ-034 / Issue #13; PY-08 | If A1 is approved, fold the two added operations into the PY-08 contract **before PY-08 is released**, with acceptance criteria covering distinct timeout results and cancellation by durable identity. Do not create a new BIU. |
| D2 | SWF-21 instructs the coordinator to "monitor only for meaningful lifecycle changes or genuine authority blockers" and supplies no tool for it. | SWF-21; SF-REQ-034 | Until PY-08 exists, the monitoring procedure should be one reviewed, versioned repository-held script with an explicit task identity, not a per-episode copy. Record as a backlog item against SF-REQ-034; it is not a BIU and needs no new requirement. |
| D3 | `docs/operations.md` already records that restart liveness uses PIDs without durable process-start identity. Same root class as the `pkill -f` incident. | SF-REQ-008; SF-REQ-034 | Carry the "never select a process by command-line pattern when an exact identity exists" rule from A1 into PY-08 acceptance criteria and the Node restart-liveness note. |

### Evidence and its provenance

The three incidents are reported by the Founder in the 2026-09-20 audit
request. They are **not** reproduced from repository artifacts and no execution
log for them is held in this repository; they are recorded here as reported
coordinator-operations evidence. Corroborating in-repository facts, which are
verifiable: `src/alienintent/control_plane/__init__.py` is an empty package;
PY-08's P0 command set is `run`, `stop`, `status`, `explain`, `cancel`,
`reconcile`/`resume`, `decisions`, `version` and contains no await or
background-task operation; SWF-21 requires monitoring; `docs/operations.md`
records the PID-identity limitation.

The three incidents are used as motivating evidence for a narrow amendment.
They are deliberately not generalized into a control-plane architecture: the
exact API surface remains a design concern under SF-REQ-051, and this audit
prescribes no single large control plane.

## Sources inspected

- [Proposal index](../proposals/INDEX.md) and PROP-2026-0001 through
  PROP-2026-0003.
- [Factory plan](../decisions/alienintent-software-factory-plan.md), including
  SF-REQ-007, 016, 020, 024, 029, 030, 032 and 041–044.
- [SWF-24](../decisions/2026-09-20-deterministic-failure-class-promotion.md),
  [SWF-25](../decisions/2026-09-20-design-contract-and-design-verification.md),
  [SWF-26](../decisions/2026-09-20-py04-coordinator-mutation-gate.md),
  [SWF-27](../decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md),
  [SWF-09](../decisions/2026-09-20-wave1-plan-approval-d1-d2.md), and
  [SWF-22](../decisions/2026-09-20-py04-custody-transfer.md).
- [Candidate-publication invariant](../evidence/candidate-publication-invariant.md),
  [PY-04 contract](../work-units/python/PY-04.md), [PY-06 contract](../work-units/python/PY-06.md),
  and [scheduling/recovery design](../architecture/pre-python-gate/scheduling-and-recovery.md).

## Post-audit disposition — 2026-09-20

The Founder directed Proposal Intake for PROP-2026-0004 and PROP-2026-0005,
then directed materialization of both amendments above. The records now map to:

- PROP-2026-0004 → **SF-REQ-054**, Issue [#65](https://github.com/AlienLogicLab/alienintent/issues/65), CAPTURE, Priority/Wave unset.
- PROP-2026-0005 → **SF-REQ-055**, Issue [#66](https://github.com/AlienLogicLab/alienintent/issues/66), CAPTURE, Priority/Wave unset.
- SF-REQ-050 / SWF-24 semantic mutation requirements are recorded in the
  canonical decision and Issue [#61](https://github.com/AlienLogicLab/alienintent/issues/61).
- SF-REQ-029 / SF-REQ-030 taxonomy and reconciliation semantics are recorded
  in the canonical backlog plan and Issues [#44](https://github.com/AlienLogicLab/alienintent/issues/44) / [#45](https://github.com/AlienLogicLab/alienintent/issues/45).

Proposal provenance files remain unchanged. The two implementation-debt items
remain debt; no new Product Requirement was created for them.

Added by the second pass (coordinator role tooling):

- [Architecture Authority](../architecture/alienintent-architecture-authority-2026-09-19.md)
  §§11, 13, 14, 18, 19, 20, 21, 24, 25, 35, 36, 37 and 44.
- [SWF-21 temporary Wave 1 release-coordinator policy](../decisions/2026-09-20-wave1-release-coordinator.md).
- SF-REQ-034 and the Wave 1 requirement set in the
  [factory plan](../decisions/alienintent-software-factory-plan.md), plus the
  [Wave 1 PLAN](../work-units/sf-wave1-plan.md).
- [PY-08 contract](../work-units/python/PY-08.md) and its Agent-Ready assessment.
- Pre-Python candidates: [control plane](../architecture/pre-python-gate/control-plane.md),
  [capabilities and assurance](../architecture/pre-python-gate/capabilities-and-assurance.md),
  [context and memory](../architecture/pre-python-gate/context-and-memory.md).
- [Interface contracts](../architecture/interface-contracts.md) §4 Operator → AlienIntent.
- [Operations contract](../operations.md) and [documentation authority model](../README.md).
- Repository source tree: `src/alienintent/control_plane/`, `src/runtime/`, `tools/`, `scripts/`, `bin/`.

## Non-actions

No additional Priority/Wave assignment was made. No Product Requirement,
canonical decision, BIU, Project Status, live Wave 1 action, implementation
source or runtime behavior changed in this audit.

The second pass adds no exception. It created no BIU, assigned no Priority or
Wave, invented no Founder decision, and created no Product Requirement or
proposal artifact — its classification is AMEND EXISTING, so amendment text is
proposed here and canonical authority was deliberately left unedited. No
coordinator or runtime behaviour was changed, no live Wave 1 execution was
touched, and no implementation source was modified. Proposed amendments A1–A3
remain recommendations until adopted into the named canonical artifacts. The
separately listed post-audit dispositions apply to the earlier audit's SF-REQ-050
and SF-REQ-029/030 amendments only.
