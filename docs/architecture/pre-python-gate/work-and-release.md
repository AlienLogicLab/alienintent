# Work And Release — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-05](../../work-units/pre-python-gate/PG-05.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## BIU record and guards
A BIU version binds work/parent identity; intent and rationale; authorized scope and exclusions; repository baselines/candidate identities where applicable; dependency DAG; artifact-specific acceptance and verification/review contracts; authority issuer and references; capabilities/target environments; budget and retry policy; context/policy versions; required closure actions; stop/escalation conditions. Mutable external issue text must not silently alter an active version. Authority supersession is explicit, attributable and invalidates affected execution/acceptance.

## Lifecycle and mapping
CAPTURE records intent. SPECIFY resolves requirements/constraints/acceptance. PLAN chooses approach. TASKS materializes bounded units. READY proves sufficient specification and satisfied dependencies. IMPLEMENT runs authorized production. VERIFY establishes mechanical evidence. REVIEW judges qualitative fit. ACCEPT records authorized acceptance of the immutable result. DONE records completed required closure with no known obligations. REVIEW need not launch a separate lane; the Node verifier combines mechanical and qualitative work.

External labels map to these semantics through configured validated ACLs. Unmapped/ambiguous values cannot authorize execution. External display ordering is not transition authority. No MERGE state: landing, deployment and publication are closure operations when required. Changes discovered in closure that alter accepted implementation return to IMPLEMENT and require renewed verification/acceptance; an authority block remains distinguishable from a failure.

## Release policy
Automatic release OFF requires an explicit authorized human release event naming BIU version and current policy. ON requires the configured release policy to authorize it: readiness evidence, satisfied dependencies, available required capabilities/budget, no blocking ambiguity. Both paths create the same release command/correlation and undergo atomic admission; READY alone is never an unrestricted worker launch. The default switch value is part of the Founder-reviewed installation policy, not silently selected here (FD-03).

## Scenarios
Duplicate release for one version reserves at most one active invocation. A changed dependency candidate invalidates dependent readiness when its contract requires that exact candidate. Repository A DONE with B still required does not close the parent Work Item. Issue1 branch-only closure is accepted only because that specific BIU excluded merge/release/deployment. FD-01 governs canonical versus external lifecycle storage; this draft fixes semantic guards, not that choice.

## Traceability and acceptance

- **G07 — BIU/domain execution model**: BIU binds authority, immutable requirements/baseline/candidate, bounded scope, dependencies, capabilities, budget, required evidence and terminal/rework outcomes. Sources: docs/templates/work-packet.md; interface-contracts; B-DISP BIU history.
- **G08 — lifecycle semantics and external mapping rules**: All ten semantic states are defined, mapping is explicit and unambiguous, dispatch is distinct from lifecycle, merge belongs to closure, accepted-result-changing rework invalidates acceptance. Sources: src/domain/lifecycle.mjs; lifecycle correction; reset §§27–30.
- **G09 — automatic-release policy model**: READY is insufficient authorization; ON and OFF have observable guards, authority provenance and deterministic denial; duplicate release cannot double-launch. Sources: Authority §10; Node IMPLEMENT admission (not automatic READY release).

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
