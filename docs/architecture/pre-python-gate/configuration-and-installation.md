# Configuration And Installation — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-14](../../work-units/pre-python-gate/PG-14.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Configuration contract
One service may manage N profiles with N=1 conventions. Each typed profile names isolated operational/evidence namespaces, repositories/work-management mappings, transport, providers, release/assurance/budget policies and workspace/resource limits. Reject ambiguous profile routing, overlapping mutable resources and unknown critical fields. Defaults reduce IDs and paths users must enter; discovery reads and validates immutable IDs instead of guessing. Secrets are references resolved by SecretProvider, not embedded values.

Protected local file references are the simple self-hosted default; environment references, keyrings, Vault/cloud/Kubernetes/enterprise systems are replaceable adapters. Consumers receive only authorized handles/material at the last needed boundary. Diagnostics, generated config and evidence redact values. Rotation records versions and must not silently rebind an active invocation's authority.

## Init/install flow
Plan and present target profile/resources; discover work-management/source identity; obtain explicit repository/environment authorization; select direct webhook or outbound relay; configure worker providers and lifecycle mappings; set release/assurance/budget policy; validate secret references and adapter compatibility; configure service/control surface; run identity, signature/path and health checks; save completion checkpoint. Noninteractive input uses the same schema/guards and refuses missing authority. Re-running init resumes recorded steps rather than creating duplicate Apps/routes/Projects.

A step records owned resources, preconditions, result and reversible compensation. Rollback removes only owned newly-created resources when authorized, preserves preexisting routes/config and reports non-reversible external actions. Upgrade preflight detects active work and incompatible state, checkpoints first and supports rollback where safe. Never silently overwrite a FactoryChecks profile or a shared route.

## Bootstrap evidence
Issue1 required manual App/Project IDs, separate ingress and explicit worker/result permissions. These are real installation pain points, not permanent user requirements. A failed signature or wrong profile cannot become ready merely because HTTP responds. Init completion does not mean Python Sovereignty. FD-03/FD-04 resolve release/security defaults and relay trust before adopting the installation contract. CLI is required; no web deployment is approved or required by this candidate installation flow.

## Traceability and acceptance

- **G28 — configuration and SecretProvider model**: Typed profiles isolate state/queues/workspaces/evidence/secrets; secrets referenced through a port; discovery validates rather than guesses provider IDs. Sources: src/config/profile.mjs; config/profile.example.json; Authority §§31–32.
- **G29 — installer/bootstrap design**: Init/install lifecycle covers discovery/authorization/providers/transport/lifecycle/health, resumable steps and rollback, automation and active-work-safe upgrades. Sources: Authority §§33–34,38; operations.md; historical manual self-hosting setup.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
