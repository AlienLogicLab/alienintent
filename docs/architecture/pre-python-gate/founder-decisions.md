# Founder decisions required before gate admission

Status: FD-01–FD-05 are resolved by binding Founder decisions. FD-06 is explicitly blocked pending EOS normalization; it is not deferred or resolved. The binding record for FD-02–FD-06 is [Founder decisions FD-02 through FD-06](../../decisions/2026-09-19-pre-python-gate-founder-decisions-fd02-fd06.md). Historical proposal text below is retained for provenance only and is superseded where it conflicts with that record.

## FD-01 — RESOLVED: Work Management / Execution ownership split

Binding record: [Founder FD-01](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md). Applied by PG-17 after Agent-Ready READY.

The external Work Management Provider owns canonical product/work state through READY, prioritization, product ownership and business context. Explicit release of a READY BIU crosses into AlienIntent-owned execution authorization and IMPLEMENT/VERIFY/REVIEW/ACCEPT/closure/DONE, invocation/worker/retry/recovery, Engineering Trajectory, Quality Evidence, capabilities and cost/routing evidence. Imported upstream views are not a canonical local backlog. External downstream fields are projections only. Ownership is architectural, not configurable; vendors and lifecycle mappings remain configurable.

The earlier recommendation for AlienIntent-owned whole-lifecycle state, and both whole-lifecycle/configurable alternatives, are superseded. Historical text remains at commit 7b16e0ba1acc2a20b959476bbac0a36f0342d22d. This is the Founder's ownership split, not adoption of the earlier option 1 or option 2. No Python implementation or live Node change is authorized. Detailed mechanisms remain candidate where not decided.

## FD-02 — RESOLVED: internal Execution decomposition

**Required decision:** refine/approve the internal decomposition under the now-fixed Work Management versus AlienIntent Execution boundary. Candidate responsibilities are Execution Coordination (released BIU/lifecycle), Invocation Runtime, Context Assembly, Evidence and Learning, and supporting Installation; Control Plane remains application orchestration. These are not five already-approved bounded contexts.

**Why now:** FD-01 approves the two authority contexts; Authority §41 still requires concrete internal model/aggregate ownership before package structure. This decision cannot reopen upstream backlog ownership or make the split configurable.

**Options/tradeoffs:** keep the candidate internal responsibilities as modules within the Execution context, minimizing boundaries while preserving distinct models; or promote proven independently evolving submodels to bounded contexts, adding explicit contracts. A separate Learning context now adds a seam but also coordination overhead before real learning implementations. All options preserve FD-01.

**Recommendation:** use the named internal responsibilities as a candidate module decomposition, keeping trajectory/measurement/learned-policy models separate; promote a new bounded context only with a demonstrated language/invariant boundary. No microservices or package names are implied. This revised recommendation follows FD-01 but is not yet adopted.

**Consequences:** invariant owners and dependency directions become binding once approved; ports and fitness rules must conform.

**If approved:** complete the concrete aggregate/port contracts against this partition and finalize UL v1 for review. Not permission to scaffold Python packages. Existing domain/lifecycle terms remain unchanged.

## FD-03 — RESOLVED: release/capability/budget policy

**Required decision:** approve the candidate per-BIU authority envelope and the initial release default. Confirm fail-closed budget admission when required hard limits cannot be enforced or consumption is unknown.

**Why now:** the bootstrap's shared Claude settings were explicitly excluded from the canonical verifier model. Authority approves powerful capabilities, optional sandboxing and ON/OFF release, but not exact default grants or unspecified cost behavior.

**Options/tradeoffs:** (A) explicit per-BIU grants with default verifier evidence/source reads, specified checks, generated outputs and correlated result; automatic release OFF initially, opt-in ON; reject unbounded budget path. This limits accidental effects but requires init to expose policy. (B) trusted broad worker permissions and automatic release ON by default, with optional restrictions; less setup but greater unintended-effect/spend risk. Sandboxing remains optional in both; no mandatory separate account/provider is proposed.

**Recommendation:** A. Powerful deployment/source operations remain grantable when a BIU requires and authorizes them; the default role is not a permanent capability ceiling. No monetary/token amount is proposed or new paid execution authorized.

**Consequences:** providers without required enforcement are ineligible for that policy, and unknown consumption holds budget rather than treating it as zero. Subscription mode does not waive hard token/cost controls.

**If approved:** refine capability use/revocation, budget reservation/settlement and init policy contracts, then reassess those design BIUs. No actual worker permissions, credentials, services or provider spending change.

## FD-04 — RESOLVED: relay trust/custody contract

**Required decision:** whether the first-class outbound relay may be a trusted authentication/custody adapter, or must be an opaque transport beneath deployment-controlled end-to-end event authentication.

**Why now:** first-class relay support is already approved, but replay cursors, acknowledgment, profile identity, metadata authenticity and credential custody depend on this security boundary. Direct webhook success does not decide it.

**Options/tradeoffs:** a trusted deployer-selected relay adapter can normalize/authenticate events and simplify reconnect, but becomes a sensitive trust/custody component; an opaque relay with end-to-end authenticated profile/event envelopes reduces relay trust but requires a producer/gateway capable of constructing those envelopes and a more explicit installation path. Neither may require an ALL-hosted service.

**Recommendation:** define an end-to-end authenticated event contract with the relay treated as transport; require a deployer-controlled authentication adapter/gateway when the external source cannot supply that envelope. Confirm the resulting installation burden before implementation. Do not assume GitHub's body signature authenticates all copied metadata.

**Consequences:** event-ingress and init must specify custody/ack/replay and credential locations. Delivery failure/delay remains possible; no exactly-once network claim. CLI remains required; web presentation is only a replaceable candidate interface and not an implemented or independently approved deployment.

**If approved:** complete the direct/relay adapter contract and installation sequence for review. No relay deployment, external service commitment, gateway creation or web deployment is authorized.

## FD-05 — RESOLVED: durable effects and multi-instance coordination

**Required decision:** approve the candidate inbox/effect-intent-outbox, expected-version writes and reservation fencing model for SQLite/PostgreSQL conformance, or choose a different consistency model.

**Why now:** SQLite default and PostgreSQL support are already approved. Durable processing effects across crash/external-effect boundaries need a concrete shared contract; Node JSON snapshots are not that design.

**Options/tradeoffs:** inbox/outbox with aggregate versions and fencing provides explicit crash/custody boundaries with moderate schema complexity; full event sourcing provides replay/reconstruction but materially increases event-schema and migration complexity; simpler mutable snapshots are easiest but insufficient without added coordination/effect-reconciliation rules.

**Recommendation:** inbox/outbox plus versions/fencing, without full event sourcing. External effects require idempotency/readback; unknown outcomes block conflicting work instead of blind repeat.

**Consequences:** state changes and effect intents must commit atomically within their authority boundary; multi-instance reservations cannot rely on process-local locks. Resolved FD-01 limits authoritative lifecycle transactions to AlienIntent execution after release; upstream product snapshots and downstream projection receipts remain distinct and cannot overwrite that truth.

**If approved:** refine transaction tables/invariants, effect reconciliation and backend conformance scenarios as design. No schema or Python implementation is authorized.

## FD-06 — RESOLVED: EOS conformance normalization

Binding records: [Founder decisions FD-02 through FD-06](../../decisions/2026-09-19-pre-python-gate-founder-decisions-fd02-fd06.md)
and the Founder FD-06 normalization decision of 2026-09-19 selecting a hybrid of
the audit's Option A and Option B.

**Decision.** Establish `EOS v1.0` on the minimal approved core, and additionally
perform substantive review of Engineering Principles v0.2, Playbook Registry v0.2
and Organizational Learning v0.2, which are intended to govern AlienIntent and all
engineering if they survive review and must not be excluded merely to unblock the
gate. Do not require review of the seven playbook scaffolds or of `cir-000009`
through `cir-000019`; leave them honestly Draft or Proposed and explicitly
excluded. Add the Playbook ontology entity. Ratify the project registry. Register
AlienIntent as `P007` with the repository unchanged. Record the intentional
public-repository deviation. Normalize Strategic Initiatives and register the `SI`
class. Dispose of `deployment_discipline.md` explicitly. Version label `v1.0`.

**Execution.** EOS `WO-000013`, Agent-Ready READY before execution. Outcome:

- **EOS v1.0 ratified** by `DR-000007`, with a durable version register naming
  inclusions and exclusions. The version scheme itself is new EOS machinery.
- **All three v0.2 documents survived substantive review** (`REVIEW-000004`) and
  were adopted. The ten Agentic Development Discipline rules are Adopted policy
  and bind AlienIntent. Their Candidate Principles table was *not* adopted: two of
  its seven entries carry no evidence and fail the document's own inclusion
  criterion.
- **`deployment_discipline.md` excluded.** Reviewed on merit and found not
  required as authority for AlienIntent; its subject is manual-versus-CI
  deployment gates, not AlienIntent's per-BIU capability model. The G31
  "engineering discipline" citation is withdrawn.
- **`ADR-0006`** adds Playbook and Playbook Entry to the ontology, with a bounded
  `Directed (review pending)` provisional state that cannot enter an approved EOS
  version while unresolved — closing the root cause rather than the symptom.
- **`ADR-0007`** registers the public-repository exception. ADR-0001 is superseded
  in part on visibility only; the private-substrate rule stands.
- **`DR-000008`** registers the `SI` record class and normalizes initiative
  statuses to ontology vocabulary.
- **AlienIntent registered as `P007`** in the ratified project registry.
- **Nothing unreviewed was promoted.** Seven placeholders remain `Draft`, eleven
  CIRs remain `Proposed`, all excluded by name.

**AlienIntent conformance.** Recorded in
[eos-conformance-manifest.md](eos-conformance-manifest.md) against EOS v1.0,
including per-rule conformance against the ten Adopted discipline rules — all ten
conform — and two ADR-0004 translation entries for the word collisions on
`readiness`/`READY` and `vertical`/`BIU`.

**Chief Architect review: PASS.** EOS `REVIEW-000005-chief-architect-eos-v1-normalization.md`,
2026-09-19, approves the normalization architecture, accepts EOS v1.0 as
AlienIntent's canonical baseline, confirms no architectural conflict with FD-03
automatic-release-ON, and records **FD-06 as complete**.

**G31 is PASS.** Gate counts move to 3 PASS / 0 DEFERRED BY FOUNDER / 31 BLOCKED.

**Not authorized by this decision:** any Python implementation or implementation
BIU, any Node or FactoryChecks change, promotion of any excluded EOS material, or
any push or publication.

## No implied deferral or implementation authorization

No mandatory gate item has been deferred by Founder authority. Accepting a recommendation authorizes only the named design refinements. A first Python implementation BIU remains prohibited until every mandatory item is PASS or explicitly deferred with scope/reason/authority and a final gate report records that result. Even then, create and assess that BIU before execution.
