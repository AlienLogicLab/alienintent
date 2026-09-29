# Python self-building 00 — save assessed work as a fixed repository version

**Status:** Proposed first hand-fed implementation unit, drawn from the first missing step in the [self-building sequence](python-self-building-candidate-sequence.md). Founder design review and Agent Ready assessment of this exact text are pending. No PRODUCER has been released.
**Baseline:** Pin the current `main` commit at assignment; during design, `main` was `734d65bb5b9ef46c69fd22d1be7756188a3dc083`.

## Required result

Given one prepared unit that the existing readiness service still finds eligible, save its execution contract and the exact task text that was assessed in an isolated Git candidate. After independent review and closure, return the repository commit and paths that contain those exact bytes. The later live-queue publisher can use these fixed references. This is the first unpublished output between the working Python preparation path and real execution; do not rebuild the compiler or assessment service.

## Inputs and authority

Use `UpstreamIntegration.candidate(compiled, identity, decisions)`, its `proof_plan`, and `current(candidate, proof_plan)`. Continue only for a current `ReadinessEligibility` whose identity, attempt, input fingerprint and contract digest match the candidate and reconstructed `BiuContract`. The assessment is preparation evidence, not implementation permission. Retain the exact canonical unit text assessed by Agent Ready and the reference to its raw receipt. A changed requirement, design, decision or proof plan holds before publication.

The configured target repository and a caller-owned isolated workspace are inputs. The caller supplies an exact starting commit and publication authority; do not read process environment or choose a repository, baseline or credential inside the domain service. Only the CLOSURE role may integrate accepted candidate content into the target branch. The PRODUCER publishes a candidate branch for independent review, never writes directly to the target branch.

## Small implementation boundary

- Add an application operation in preparation/context assembly that produces a deterministic publication bundle: the existing `BiuContract.canonical_payload()`, the exact assessed unit text, assessment attempt/fingerprint/receipt reference, proof-plan digests and current source/design/decision references. Validate identity, contract digest, assessed-text digest and eligibility together. Do not invent a second readiness judgment.
- Use an injected repository-writing boundary to place the bundle in the caller's isolated workspace at configured, work-identity-qualified paths. The contract file contains only the flat contract payload that the existing live reader already parses; a companion manifest maps it to the assessed text and evidence. Reject an existing path with different content; identical content is a no-op. Path components are validated, and writes cannot escape the workspace.
- Reuse existing Git candidate publication and independent readback behavior where applicable. The returned result names the exact commit, both paths, contract digest, assessment attempt and fingerprint. It is only a candidate until a separate REVIEWER accepts and CLOSURE lands precisely that content; the final repository commit must be read back before downstream queue publication.
- Do not create an Issue, attach a Project entry, write READY, start a worker, change role assignments or alter scheduling. The version-bound reader is the next [candidate task](PY-SELF-01R.md), followed by the [live queue handoff](PY-SELF-01.md).

## Acceptance proof

1. In an isolated temporary repository, one current assessed candidate produces contract bytes that reconstruct the same `BiuContract` and content digest, plus the exact text whose digest the assessment retained. An independent checkout of the published candidate reads the same bytes at the returned commit.
2. A changed requirement, design, decision, proof plan, assessed text, contract or assessment identity holds before any repository write. Missing receipt or mismatched target repository also holds. A passing assessment alone cannot trigger a live work release.
3. Repeating the same request cannot add a different artifact or silently overwrite a path. A conflicting publication for the same work identity holds with both versions identified; interruption before or after a candidate push is reconciled by exact commit and content readback, never by blind duplicate creation.
4. Recorded tests use the real preparation output and a local temporary Git remote; no live GitHub mutation. The independent REVIEWER verifies output bytes, path confinement, refusal behavior, candidate retrieval, resource cleanup and the applicable feature regression checks.

## Resource and review rules

The operation owns no unbounded in-memory history. The caller owns its temporary workspace and branch with a disk/time bound, retained evidence and cleanup on completion, rejection or interruption. Repository artifacts are durable only after accepted closure and follow repository retention. If disk is full, writing fails closed and preserves the earlier bytes. Do not swallow an unknown publication outcome.

The PRODUCER works on this packet only in an isolated directory, publishes its exact candidate branch/commit, and records checks. A separate REVIEWER instance retrieves that commit and inspects architecture, Python quality, duplicate mechanisms, resource lifetime, proof strength and slop. A different CLOSURE instance lands and reads back accepted content and records the final commit. These are roles, not hardcoded model names. A design gap or requested scope change returns for review rather than being decided during implementation.
