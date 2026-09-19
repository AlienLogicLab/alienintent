# Founder decisions FD-02 through FD-06

Date: 2026-09-19. Source: direct Founder instruction. Scope: Pre-Python
architecture/design documentation only. This record authorizes neither Python
implementation nor Node, FactoryChecks, EOS, service, credential, deployment,
GitHub or provider-spend changes.

## FD-02 — binding internal Execution decomposition

Execution Coordination, Invocation Runtime, Context Assembly, Evidence &
Learning, and Installation are modules within AlienIntent Execution initially.
Promote a module to a bounded context only when domain evidence establishes a
distinct language, invariant boundary or ownership model. Control Plane remains
application orchestration, not another state owner.

## FD-03 — binding release, capability and budget policy

Each BIU receives the capabilities legitimately required for its work. Use
sensible capability profiles/conventions plus explicit BIU-specific additions;
do not create unnecessary fine-grained permission bureaucracy. Powerful
authority—including shell, network, cloud API, database migration,
service-control, live deployment and other production capabilities—may be
granted when the BIU requires it.

Required budget controls fail closed. Unknown or unmeasurable consumption is
not zero. If a policy requires an enforceable hard limit and a provider cannot
supply the necessary information or controls, that path is ineligible.

**Automatic release defaults ON and is configurable OFF.** READY means the BIU
passed readiness checks. With automatic release ON, a READY BIU whose release
policy is satisfied proceeds to IMPLEMENT through an attributable policy release.
With it OFF, a human explicitly authorizes that release. Neither path bypasses
readiness checks. This is deployment/profile policy, not hard-coded lifecycle
behavior.

## FD-04 — binding relay trust/custody contract

Events require end-to-end authentication. An outbound relay is transport, not a
trusted domain or security authority. Where an upstream cannot create the
required authenticated event envelope, use a deployer-controlled gateway.

## FD-05 — binding durable effects and multi-instance coordination

Use inbox/effect-intent/outbox processing, expected versions, reservation
fencing, idempotent external effects, and read-back/reconciliation for uncertain
outcomes. Do not adopt full event sourcing merely for this problem. An unknown
external outcome blocks conflicting work; it does not cause blind retry.

## FD-06 — RESOLVED (originally blocked pending EOS normalization)

Status: RESOLVED 2026-09-19: EOS v1.0 (`DR-000007`) is ratified and AlienIntent conformance is recorded in the EOS conformance manifest ([manifest](../architecture/pre-python-gate/eos-conformance-manifest.md); [Wave 1 Founder decisions SWF-06](2026-09-19-software-factory-wave1-founder-decisions.md)). The decision text below is retained as the condition that EOS v1.0 satisfied.

Do not pin the observed revision or use mixed per-document maturity states as
AlienIntent's conformance baseline. EOS is one coherent system/version.
AlienIntent may record inheritance/conformance only after EOS has been audited,
its maturity/status inconsistencies reconciled in EOS itself, and one internally
consistent approved EOS version established.
