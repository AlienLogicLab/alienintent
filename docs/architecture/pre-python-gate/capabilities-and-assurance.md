# Capabilities And Assurance — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-06](../../work-units/pre-python-gate/PG-06.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Required independence
VERIFIER uses a separate invocation, owned isolated worktree, independently assembled authoritative requirements and immutable candidate/evidence, and separate provenance. Producer private reasoning/session state is unavailable by default. Acceptance cannot be the producer approving its own output. Separate provider/model/account/machine can strengthen assurance but are not mandatory. REVIEW remains qualitative even when performed by the same independent verifier invocation after mechanical checks.

## Binding authority envelope direction (FD-03)
A grant binds profile, BIU version, invocation/role, issuer/authority reference, target repository/environment, allowed operation/resources, expiry/termination condition, budget and policy version. Launch and capability use check that envelope; revocation fences new actions, cancels owned work safely and records any already-completed effects. External credentials are implementation bindings, not authority by themselves. Deploy/DB migration/config rotation/service restart/cloud changes are allowed when explicitly needed and granted; each records action/result and post-change verification.

Use sensible capability profiles/conventions plus explicit BIU-specific additions, avoiding needless per-operation permission bureaucracy. The default verifier profile allows assigned evidence/source reads, specified verification commands, generated output in its evidence/workspace area and attributable result publication. A BIU requiring shell, network, cloud API, database migration, service-control, live deployment or other powerful authority carries an explicit purpose/target addition and preserves immutable reviewed-candidate semantics. Credentials remain implementation bindings, not authority by themselves.

## Optional isolation
Trusted unsandboxed execution is valid if configured. Linux-native containers are preferred when isolation is enabled, with Docker-compatible backends supported. Backend unavailability cannot silently lower configured assurance. Credential delivery is scoped and evidence redacted whether sandboxed or not. Container choice cannot substitute for spend controls.

## Failure cases
A grant for staging cannot mutate production. A verifier receiving changed candidate bytes cannot publish ACCEPT for the old digest. Revoked publication authority denies the comment/result operation, preserving local evidence and a truthful blocker. Stronger policies may require an additional human decision; no LOW/NORMAL/HIGH bureaucracy or mandatory separate GitHub accounts is introduced. FD-03 approves this direction; exact profile catalogues and enforcement mechanisms remain design work.

## Traceability and acceptance

- **G10 — verifier-independence / assurance-policy model**: Separate invocation/worktree/context/provenance and immutable candidate prevent self-approval; assurance can strengthen controls without mandatory account/provider differences. Sources: Authority §§4,5,11; worker-runner/worktree manager; Issue1 JC proof.
- **G11 — capability/authority model, including live deployment authority**: Grant records name BIU/worker/target/actions/limits/expiry/revocation; authorized live changes require post-action evidence; rejected/cross-target actions have defined behavior. Sources: Authority §§13–14,45; bootstrap-only JC exception (not canonical model).
- **G12 — optional sandbox/container model**: Unsandboxed trusted and Linux-native/container-backed policies are explicit; capabilities and credential handling remain controlled; sandbox failure never silently falls back. Sources: Authority §12; no dedicated sandbox design.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
