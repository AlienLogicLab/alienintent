# Context And Memory — Pre-Python candidate

Date: 2026-09-19. Status: CANDIDATE DESIGN; not Founder-approved or implementation authority.
BIU: [PG-10](../../work-units/pre-python-gate/PG-10.md), Agent-Ready READY before drafting.
Binding inputs: [Architecture Authority](../alienintent-architecture-authority-2026-09-19.md) and [Pre-Python Gate](../../work-units/alienintent-pre-python-implementation-gate.md).

## Context Engineering v1 carried forward
Reuse B-DISP near-term-scope §§4–6 and canonical-architecture role/phase compiler; do not rediscover the six types: instructions, knowledge, memory, examples, tools, guardrails. Each selected source has identity/version/digest/provenance, applicability, access classification and retrieval reason. A context manifest records BIU/invocation/role/phase, policy version, selected source references, budgets and omitted/unavailable material.

Static context is small: current role, authority, essential invariants and repository constraints. Dynamic context loads relevant architecture/source/evidence/examples and reviewed versioned skills on demand. Bounded retrieval favors relevance and preserves source references; it does not dump whole repositories or trajectories. Guardrails with deterministic meaning belong in enforcement, not only prose. Tools carry purpose, authority, version and conditions. Missing required authoritative context blocks execution; truncation cannot silently remove a hard constraint.

PRODUCER receives implementation continuity; closure receives accepted candidate, acceptance and remaining obligations; VERIFIER receives independently assembled requirements, immutable candidate/diff and proof criteria, excluding producer private reasoning; operator receives current authority, resource ownership and truthful known/unknown diagnostics.

## Separate classes
Operational state owns active invocations/reservations/recovery. Task context owns the per-invocation manifest and relevant working evidence. Engineering knowledge owns reviewed project lessons. Organizational knowledge maps to EOS knowledge governance. Trajectory owns observable history. Quality Evidence owns derived measurements/findings/outcomes. Learned policy owns reviewed versioned proposals/decisions. These classes may share physical storage but not identity, authority, lifetime or retrieval rules.

## Observable acceptance
The same candidate/requirements assembled for verifier excludes producer session narrative. Replacing a source version changes manifest provenance and invalidates affected authority, not silently caches stale context. Measure context bytes/tokens, repeated reads, reconstruction overhead, quality outcomes and cost by policy version. Correlation is not proof that a context policy caused improvement. No private chain-of-thought collection or generic memory bucket.

## Traceability and acceptance

- **G19 — Context Engineering v1 carried forward**: Six context kinds, static/dynamic split, role/phase selection, versions/provenance, budgets, skills and measurements are carried forward with independent verifier inputs. Sources: B-DISP near-term-scope §§4–6; canonical-architecture context compiler.
- **G20 — memory/state/evidence separation carried forward**: Operational state, task context, engineering knowledge, organizational knowledge, trajectory, Quality Evidence and learned policy have separate ownership/lifetimes/retrieval. Sources: Authority §25; near-term-scope §4.3; trajectory source §17.

Assessment method: provide this entire candidate plus the cited authority/EOS/Node evidence and these criteria to Agent-Ready; classify missing criteria or conflicting authority explicitly, repair and reassess. READY is BIU readiness, not design approval. Concrete scenarios above are design checks; no Python executable proof exists. See [source inventory](inventory.md), [reconciliation](authority-reconciliation.md), and [Founder decisions](founder-decisions.md).
