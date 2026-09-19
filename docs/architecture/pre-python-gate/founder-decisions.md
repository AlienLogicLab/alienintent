# Founder decisions required before gate admission

Status: FD-01 is resolved by binding Founder decision; FD-02–FD-06 remain proposals, not adopted decisions. The user authorized inventory and candidate design work, not silent decisions under Authority §45. Existing 45 Founder-resolved directions remain binding; these questions fill gaps in concrete contracts rather than reopen those directions.

## FD-01 — RESOLVED: Work Management / Execution ownership split

Binding record: [Founder FD-01](../../decisions/2026-09-19-alienintent-work-management-execution-authority.md). Applied by PG-17 after Agent-Ready READY.

The external Work Management Provider owns canonical product/work state through READY, prioritization, product ownership and business context. Explicit release of a READY BIU crosses into AlienIntent-owned execution authorization and IMPLEMENT/VERIFY/REVIEW/ACCEPT/closure/DONE, invocation/worker/retry/recovery, Engineering Trajectory, Quality Evidence, capabilities and cost/routing evidence. Imported upstream views are not a canonical local backlog. External downstream fields are projections only. Ownership is architectural, not configurable; vendors and lifecycle mappings remain configurable.

The earlier recommendation for AlienIntent-owned whole-lifecycle state, and both whole-lifecycle/configurable alternatives, are superseded. Historical text remains at commit 7b16e0ba1acc2a20b959476bbac0a36f0342d22d. This is the Founder's ownership split, not adoption of the earlier option 1 or option 2. No Python implementation or live Node change is authorized. Detailed mechanisms remain candidate where not decided.

## FD-02 — Domain boundary proposal

**Required decision:** refine/approve the internal decomposition under the now-fixed Work Management versus AlienIntent Execution boundary. Candidate responsibilities are Execution Coordination (released BIU/lifecycle), Invocation Runtime, Context Assembly, Evidence and Learning, and supporting Installation; Control Plane remains application orchestration. These are not five already-approved bounded contexts.

**Why now:** FD-01 approves the two authority contexts; Authority §41 still requires concrete internal model/aggregate ownership before package structure. This decision cannot reopen upstream backlog ownership or make the split configurable.

**Options/tradeoffs:** keep the candidate internal responsibilities as modules within the Execution context, minimizing boundaries while preserving distinct models; or promote proven independently evolving submodels to bounded contexts, adding explicit contracts. A separate Learning context now adds a seam but also coordination overhead before real learning implementations. All options preserve FD-01.

**Recommendation:** use the named internal responsibilities as a candidate module decomposition, keeping trajectory/measurement/learned-policy models separate; promote a new bounded context only with a demonstrated language/invariant boundary. No microservices or package names are implied. This revised recommendation follows FD-01 but is not yet adopted.

**Consequences:** invariant owners and dependency directions become binding once approved; ports and fitness rules must conform.

**If approved:** complete the concrete aggregate/port contracts against this partition and finalize UL v1 for review. Not permission to scaffold Python packages. Existing domain/lifecycle terms remain unchanged.

## FD-03 — Default release/capability/budget policy

**Required decision:** approve the candidate per-BIU authority envelope and the initial release default. Confirm fail-closed budget admission when required hard limits cannot be enforced or consumption is unknown.

**Why now:** the bootstrap's shared Claude settings were explicitly excluded from the canonical verifier model. Authority approves powerful capabilities, optional sandboxing and ON/OFF release, but not exact default grants or unspecified cost behavior.

**Options/tradeoffs:** (A) explicit per-BIU grants with default verifier evidence/source reads, specified checks, generated outputs and correlated result; automatic release OFF initially, opt-in ON; reject unbounded budget path. This limits accidental effects but requires init to expose policy. (B) trusted broad worker permissions and automatic release ON by default, with optional restrictions; less setup but greater unintended-effect/spend risk. Sandboxing remains optional in both; no mandatory separate account/provider is proposed.

**Recommendation:** A. Powerful deployment/source operations remain grantable when a BIU requires and authorizes them; the default role is not a permanent capability ceiling. No monetary/token amount is proposed or new paid execution authorized.

**Consequences:** providers without required enforcement are ineligible for that policy, and unknown consumption holds budget rather than treating it as zero. Subscription mode does not waive hard token/cost controls.

**If approved:** refine capability use/revocation, budget reservation/settlement and init policy contracts, then reassess those design BIUs. No actual worker permissions, credentials, services or provider spending change.

## FD-04 — Relay trust/custody contract

**Required decision:** whether the first-class outbound relay may be a trusted authentication/custody adapter, or must be an opaque transport beneath deployment-controlled end-to-end event authentication.

**Why now:** first-class relay support is already approved, but replay cursors, acknowledgment, profile identity, metadata authenticity and credential custody depend on this security boundary. Direct webhook success does not decide it.

**Options/tradeoffs:** a trusted deployer-selected relay adapter can normalize/authenticate events and simplify reconnect, but becomes a sensitive trust/custody component; an opaque relay with end-to-end authenticated profile/event envelopes reduces relay trust but requires a producer/gateway capable of constructing those envelopes and a more explicit installation path. Neither may require an ALL-hosted service.

**Recommendation:** define an end-to-end authenticated event contract with the relay treated as transport; require a deployer-controlled authentication adapter/gateway when the external source cannot supply that envelope. Confirm the resulting installation burden before implementation. Do not assume GitHub's body signature authenticates all copied metadata.

**Consequences:** event-ingress and init must specify custody/ack/replay and credential locations. Delivery failure/delay remains possible; no exactly-once network claim. CLI remains required; web presentation is only a replaceable candidate interface and not an implemented or independently approved deployment.

**If approved:** complete the direct/relay adapter contract and installation sequence for review. No relay deployment, external service commitment, gateway creation or web deployment is authorized.

## FD-05 — Durable effects and multi-instance coordination

**Required decision:** approve the candidate inbox/effect-intent-outbox, expected-version writes and reservation fencing model for SQLite/PostgreSQL conformance, or choose a different consistency model.

**Why now:** SQLite default and PostgreSQL support are already approved. Durable processing effects across crash/external-effect boundaries need a concrete shared contract; Node JSON snapshots are not that design.

**Options/tradeoffs:** inbox/outbox with aggregate versions and fencing provides explicit crash/custody boundaries with moderate schema complexity; full event sourcing provides replay/reconstruction but materially increases event-schema and migration complexity; simpler mutable snapshots are easiest but insufficient without added coordination/effect-reconciliation rules.

**Recommendation:** inbox/outbox plus versions/fencing, without full event sourcing. External effects require idempotency/readback; unknown outcomes block conflicting work instead of blind repeat.

**Consequences:** state changes and effect intents must commit atomically within their authority boundary; multi-instance reservations cannot rely on process-local locks. Resolved FD-01 limits authoritative lifecycle transactions to AlienIntent execution after release; upstream product snapshots and downstream projection receipts remain distinct and cannot overwrite that truth.

**If approved:** refine transaction tables/invariants, effect reconciliation and backend conformance scenarios as design. No schema or Python implementation is authorized.

## FD-06 — EOS conformance baseline

**Required decision:** approve the observed EOS commit 79d769228c266064e71b7ab7f556ea831cfc9537 as the inheritance reference with explicit per-document maturity, including treatment of directed engineering policy whose post-edit review remains pending.

**Why now:** Authority §40 requires an exact conformance version. Observing a checkout does not itself authorize claiming conformance to every file at that commit.

**Options/tradeoffs:** pin this commit and inherit accepted records plus explicitly directed engineering discipline with its pending-review label; inherit accepted-only records until organizational review resolves directed material; nominate another reviewed EOS revision. First option preserves current operating discipline and provenance; second is stricter on ratification but needs an explicit deviation/disposition for directed rules.

**Recommendation:** pin this commit with per-record statuses, inherit accepted records and the explicitly directed discipline without promoting its candidate table or scaffolds. Review future EOS deltas explicitly.

**Consequences:** publish a precise local conformance manifest, not a blanket 'EOS compliant' claim. Contribution remains proposal/review, with no automatic upstream changes.

**If approved:** complete the inheritance manifest and review gate claims against it. No EOS edit, PR, submission or public release is authorized.

## No implied deferral or implementation authorization

No mandatory gate item has been deferred by Founder authority. Accepting a recommendation authorizes only the named design refinements. A first Python implementation BIU remains prohibited until every mandatory item is PASS or explicitly deferred with scope/reason/authority and a final gate report records that result. Even then, create and assess that BIU before execution.
