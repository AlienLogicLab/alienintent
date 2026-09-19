# Founder decisions required before gate admission

Status: proposals, not decisions. No choice below has been adopted. The user authorized inventory and candidate design work, not silent decisions under Authority §45. Existing 45 Founder-resolved directions remain binding; these questions fill gaps in concrete contracts rather than reopen those directions.

## FD-01 — Canonical work/lifecycle authority

**Required decision:** where authoritative Work Item/BIU lifecycle state resides in the canonical system, and how external work-management changes become authorized transitions.

**Why now:** neutral domain concepts alone do not settle source-of-truth. Current Node uses exact GitHub Project status as operational authority; older interface contracts require external Issues. This choice affects persistence, event concurrency, recovery, Control Plane, offline behavior and migration. G03/G04/G05/G07–G09/G15/G21/G25/G33 cannot be adopted coherently without it.

**Options/tradeoffs:**

1. External work-management lifecycle remains authoritative; AlienIntent holds execution state and validated projections. Closer to Node and existing operator workflow, but repository-free/multiple-vendor concepts and offline recovery must live with vendor limitations and external availability.
2. AlienIntent owns canonical Work Item/BIU lifecycle; external systems submit intents and display projections. Strong domain autonomy and consistent N-adapter behavior, but introduces synchronization/conflict/migration obligations and changes operational authority.
3. Configurable authority per profile. Accommodates both but doubles important consistency and recovery cases before the first Python implementation; not recommended as the initial model.

**Recommendation:** option 2 for the canonical Python design, with explicit expected-version/authorized-command reconciliation and preservation of Node's external authority until cutover. This is a recommendation, not an inference from 'AlienIntent owns concepts.'

**Consequences:** external UI edits may be rejected/reconciled rather than directly becoming authoritative lifecycle truth. Migration must import identities/versions and prevent two writers. A conflict policy must be completed after selection.

**If approved:** revise the candidate work, ACL, persistence, event and Control Plane contracts consistently and assess the bounded revision BIUs before execution. No Python implementation, live cutover or external synchronization is authorized. If option 1 is chosen, refine projection/current-authority readback instead.

## FD-02 — Domain boundary proposal

**Required decision:** accept or revise the five logical contexts proposed in domain-model.md: Work Coordination, Execution, Context Assembly, Evidence and Learning, Installation; Control Plane remains application orchestration over them.

**Why now:** Authority §41 explicitly requires an approved bounded-context model before package structure. No approved AlienIntent context map was found.

**Options/tradeoffs:** proposed five logical boundaries localize invariants without services; a coarser Work/Execution + supporting services model is simpler initially but risks mixing authority/context/evidence lifetimes; a separate Learning context now adds an explicit seam but additional cross-context contracts before real learning implementations.

**Recommendation:** five logical contexts, keeping trajectory/measurement/learned-policy models separate within Evidence and Learning; split Learning only when independent behavior justifies it. No microservices or package names are implied.

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

**Consequences:** state changes and effect intents must commit atomically within their authority boundary; multi-instance reservations cannot rely on process-local locks. FD-01 determines where lifecycle truth participates.

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
