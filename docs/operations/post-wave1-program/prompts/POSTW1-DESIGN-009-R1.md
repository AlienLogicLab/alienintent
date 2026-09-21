# POSTW1-DESIGN-009-R1 — repair four material design findings

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, solely to revise
`docs/evidence/wave2-design-contracts.json` and its `.md` companion.

## 1. What happened

Your design contracts passed the mechanical checker: all nineteen fields present, no decisions
deferred, every bounded context real, enforcement opportunities named. Phase 10 then put them in
front of a **fresh Claude session with no prior context**, read-only, independent of both you and
the coordinator. It returned `REPAIR_REQUIRED` with four MATERIAL findings and four ADVISORY.

The full verdict is `docs/evidence/wave2-design-verification.json`. Read it first. It read the
actual source — it checked your store claims against the real port and confirmed
`acquire/release`, `commit_with_effect`, `claim_effect`, `confirm_effect` exist and do not
validate a passed fence, as you stated. Its concerns are not misreadings.

Two things it got right that the checker structurally could not see: a design can satisfy every
field and still narrow a requirement, and an enforcement opportunity can be named without the
rule it enforces existing anywhere.

## 2. The four MATERIAL findings — all must be resolved

**DV-1 — SF-REQ-039 changes the shared execution kernel.** The design does not merely add an
offline harness: it requires role-by-role orchestration replacing
`FactoryCoordinator._completed_for_outcome`, a composed role router, and a new
`OutcomeEvidencePort`. A production capability is being introduced inside a test-proof
requirement, with no owner and no live-path probe — offline scenarios would pass while the
sandbox profile holds on every producer success.

Resolve by naming the requirement and owner for canonical multi-role orchestration and for
`RoleOutcomeRecord` emission on the real worker path — **or** record it as an explicit authority
gap returned to SPECIFY. Do not create a Product Requirement to close it.

**DV-2 — SF-REQ-013 is silently narrowed.** Making an externally supplied "authorized allocation"
a mandatory input that carries unit_key, BIU identity, obligation extents, capabilities, budgets,
dependency edges and closure duties means the allocation *is* the BIU. That turns a P1
"compile requirements into BIUs" into "validate a hand-authored allocation", and leaves the
Wave 2A outcome dependent on an unowned upstream step.

Resolve by recording the allocation source as an explicit authority gap on SF-REQ-013 and
returning the question to SPECIFY — either name the owner and interface that produces
allocations, or state that SF-REQ-013 must derive the decomposition itself. Choose on the
evidence and say which.

**DV-3 — an enforcement check whose rule exists nowhere.** `051-architecture-boundary` proposes a
fitness fixture for context import-direction and port compatibility, but no contract states the
permitted direction graph. The implementer would have to invent the rule the deterministic check
enforces. That is the discipline of Phase 9 violated at one remove, and your own design creates
`context_assembly -> execution_coordination` and `execution_coordination -> context_assembly`
coupling without stating whether both are permitted.

Resolve by stating the allowed context dependency direction as a fixed design decision —
explicitly including whether `execution_coordination` may depend on `context_assembly` types and
how `evidence_learning` adapters may reach `installation`/`composition`.

**DV-4 — the identifier grammar is unpinned.** SF-REQ-011 must recognise requirement identifiers
in three prose forms, yet no field pins the grammar; `ubiquitous_language` says only "existing
SF-REQ identifier, never generated from wording". The verifier calls this "the PY-09B failure
verbatim, one layer up", and it is right: an implementer writes `SF-REQ-\d{3}`, a later
identifier with a suffix or a different prefix is silently dropped, and the counts fixture still
passes.

Resolve by fixing the recognised identifier grammar as an explicit design decision, requiring an
unrecognised shape to yield a **typed** UNVERIFIED/conflict record rather than a silent omission,
and adding a non-conforming-identifier fixture. Phase 5 already settled a BIU-identifier grammar
(`\A(?:(?:PG|PY)-[0-9]{2}|WO-[0-9]{6})(?:[A-Z])?\Z`) and established that identity must never be
derived from sorting; be consistent with it where the same reasoning applies.

## 3. The bootstrap-assumption candidate — address it explicitly

The verifier found no bootstrap machinery adopted as architecture, and said so. It raised one
weak candidate: **the 3600 s maximum episode age coincides exactly with the bootstrap waiter's
3600 s timeout and carries no provenance statement**, while SF-REQ-056 explicitly disclaims its
analogous 300 s value as "not a claim that historical values are canonical".

Either give the 3600 s value a provenance statement, or disclaim it the way SF-REQ-056 disclaims
its own. A threshold inherited from temporary bootstrap machinery and presented as architecture is
precisely what Phase 6 exists to prevent.

## 4. The four ADVISORY findings

Address them or record why not. They do not block, but silently dropping them is not an option.

## 5. Scope

Revise the two design-contract files only. Do not create, amend or weaken any Product
Requirement — recording an authority gap is in scope; closing one is not. Do not modify the
verification artifact, prior deliverables, Wave 1 evidence, lifecycle state, Project state or
worker contracts. Do not `git commit`, push, or use the network.

## 6. Acceptance

```
python3 tools/evidence/check_design_contracts.py docs/evidence/wave2-design-contracts.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Both must still pass. Note that the checker passing is what let these four defects through, so
it is a floor you must clear, not evidence that the repair worked.

**If you disagree with a finding, say so in `DISPUTED` with your reasoning and leave it
unrepaired.** Three predecessors disputed a check and were upheld each time; a fourth disputed a
Director prework claim and was upheld. A wrong finding accepted silently is worse than a disputed
one.

## 7. Terminal report — this block only

```
DV1_RESOLVED=<how, one line>
DV2_RESOLVED=<how, one line>
DV3_RESOLVED=<how, one line>
DV4_RESOLVED=<how, one line>
EPISODE_AGE_PROVENANCE=<stated | disclaimed>
ADVISORY_ADDRESSED=<n of 4> ADVISORY_DECLINED=<n>
NEW_AUTHORITY_GAPS=<n>
REQUIREMENTS_CREATED=<must be 0>
DESIGN_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
