# Python self-building 00 — bind assessed text to its work contract

**Status:** Proposed first hand-fed code task. Independent adversarial review found no remaining blocker to Agent Ready. Founder design approval and assessment of this exact text remain pending; no PRODUCER is released.
**Plan source:** The [self-building sequence](python-self-building-candidate-sequence.md) joins Python's existing preparation and live execution paths. The six-task sandbox already ran prepared work; the first missing publication input is proof that the task text and contract are exactly what the latest assessment checked. Saving those bytes in Git is separate.

## One result and exact call

Add `UpstreamIntegration.publication_input(compiled: CompilationCandidate, identity: str, decisions: tuple[str, ...]) -> AssessedPublicationInput | Hold | LintHold`. The returned frozen value has these fields: `identity: str`, `contract: BiuContract`, `text: str`, `proof_plan: tuple[str, ...]`, `attempt_id: str`, `input_fingerprint: str`, `text_digest: str`, and `raw_ref: Ref`. Use the existing `Hold` for binding refusals with a specific reason; propagate the existing current-readiness hold when it applies. The work identity is the explicit method argument, checked against the contract; it is not inferred from a title.

This result is a snapshot for a later repository publisher. It is not permission to implement or a durable publication receipt. The new binding code makes no Git, Project, Issue, worker or role-assignment changes. The existing readiness `current()` call may retain lint or applicability audit records; do not suppress those existing writes or claim this call is storage-free.

## Required read and comparison

1. Derive `candidate = self.candidate(compiled, identity, decisions)` and `plan = self.proof_plan(compiled, identity)`. Both existing helpers use `next(...)` and can raise `StopIteration` for a missing unit; catch that case and return a hold. An empty or malformed plan also holds. Require nonempty `candidate["text"]` as an exact string. Reconstruct `BiuContract` with `context_assembly.domain.compilation.contract_from_payload`; malformed content holds.
2. Call `self.current(candidate, plan)`; continue only on `ReadinessEligibility`. Fetch `self.profile.readiness_consumer.latest(identity)`. That attempt entry has `attempt_id`, `input_fingerprint`, `input_sha256`, `contract_digest`, `raw_ref` and `outcome`; it has **no identity field**. The lookup key supplies its identity.
3. Compare the caller's identity to the contract identity. Compare eligibility's identity, attempt, fingerprint and contract digest to the caller's identity, latest entry's attempt/fingerprint/digest and reconstructed contract digest. Compare `digest(candidate["text"])` to latest `input_sha256`. Require latest outcome `READY` and a present `raw_ref`. No missing field may be coerced to a passing value.
4. Retrieve `consumer.raw(identity, attempt_id)`, require its returned reference to equal latest `raw_ref`, and convert it with `ref_from_document`. Require `Ref.logical_id == f"readiness/{identity}/{attempt_id}/raw"` and the configured project/profile identities. Hold on missing, unreadable or mismatched evidence. The returned text may be a base64 representation; do not treat it as original bytes or reassess its meaning.
5. Re-derive `candidate` and `proof_plan` from `compiled`, then run `current(new_candidate, new_plan)` and re-read `latest(identity)` immediately before returning. Hold if text, contract payload/digest, plan, eligibility or the selected latest attempt/outcome/raw reference changed. The frozen `CompilationCandidate` contains a mutable `body`, so merely calling `current()` on the first candidate would miss an in-memory text change. This result remains a snapshot; the later publisher must rebind immediately before writing and fence concurrent changes.

## Acceptance proof

- A real compiled candidate and its latest applicable READY attempt return the stated frozen value. The text digest matches the retained attempt; the contract digest matches the contract, eligibility and latest entry; the exact raw receipt can be retrieved. Repeating unchanged inputs yields the same value.
- Change **only** task text while leaving the contract and readiness fingerprint unchanged: hold. This test must fail if the new text comparison is removed, because the existing readiness fingerprint does not include text.
- Separately change or remove work identity, proof plan, attempt identity, fingerprint, contract digest, latest outcome, text digest or raw reference: hold. An older READY attempt never substitutes for a later attempt. An inaccessible raw receipt holds.
- Simulate a latest-attempt change or an in-memory change to the compiled text between the first and last reads: hold. Existing preparation and readiness tests remain passing. No live GitHub or worker test is required.

## Ownership and limits

The composition method orchestrates existing preparation and retained-consumer reads. A small preparation application helper may own the frozen value and exact comparisons; it must not import GitHub or Git classes inward. Edit only these areas and focused tests. Reuse existing digest, contract reconstruction and `Ref` conversion. Do not add durable storage, a cache, a new assessment rule or historical scanning; latest-attempt access is bounded. The existing audit writes follow their existing retention policy.

The PRODUCER uses an isolated workspace at the assigned repository revision and publishes its exact candidate revision and checks. A distinct REVIEWER retrieves that revision and challenges the comparisons, race test, code quality, domain ownership, duplication and resource lifetime. A different CLOSURE instance lands only accepted content and verifies landed behavior. Their temporary branches and workspaces have owners, bounds and cleanup rules. A need for a new external write or broader behavior returns to design review.
