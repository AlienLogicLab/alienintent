# POSTW1-DESIGN-009 — Wave 2 Design Contracts

Fresh Codex GPT-6 Astra. Repository root, `workspace-write`, for the deliverables in §5.
**Risk: HIGH.** Phase 10 is independent Design Verification by a **fresh reviewer who is not
you** — write for that reader.

## 1. Objective

Define the intended architecture **before** BIU decomposition, for the ten requirements Phase 8
selected: `SF-REQ-011` `SF-REQ-012` `SF-REQ-013` `SF-REQ-014` `SF-REQ-015` `SF-REQ-016`
`SF-REQ-039` `SF-REQ-051` `SF-REQ-053` `SF-REQ-056`.

Specifications are in `docs/evidence/wave2-specified-requirements.json` — intent, scope,
non-goals, dependencies, acceptance criteria, authority gaps, security and operational
constraints, observability and failure modes are already settled there. Do not re-specify; design.

## 2. The discipline that decides this phase

> Do not let implementation agents make material design decisions.
> Design must be explicit enough that **implementation becomes local execution rather than
> architecture invention**.

Wave 1 paid for the failure twice, and both are in the ledger. PY-06's `RetrySchedule` and
`ReservationBook` were unit-tested and never wired into a composition root — the design did not
say who composed them, so nobody did (LRN-002). PY-09B's permission expectation and its passing
17/17 preflight shared one wrong premise for roughly nineteen hours, because the consumer contract
was never made explicit (LRN-014).

So: anything you leave to the implementer, the implementer will decide. Record bounded choices
under `implementation_local_freedom` (naming, internal helper decomposition, local ordering).
Anything material — persistence engine, identity scheme, concurrency model, failure semantics,
port boundaries — belongs in the contract. `deferred_to_implementation` must be empty, and the
checker enforces it.

## 3. Bind to the architecture that exists

`docs/operations/post-wave1-program/prework/POSTW1-DESIGN-009-inputs.json` lists the bounded
contexts present in the repository today: Python `composition`, `context_assembly`,
`control_plane`, `evidence_learning`, `execution_coordination`, `installation`,
`invocation_runtime`; Node `alienintent`, `config`, `domain`, `github`, `providers`, `runtime`.

Bind each contract to one of these, or name a new context **with justification**. A design that
invents a parallel structure is unimplementable against the codebase it governs.

## 4. Deterministic enforcement is part of the design, not an afterthought

Every contract must name at least one `deterministic_enforcement_opportunity`. Prefer extending
what already runs: `tests/test_architecture_fitness.py` executes in CI and carries a
deliberate-violation test proving each check can fail. Phase 3 promoted seven gates into existing
layers and proposed **zero** new ones — a design that finds no enforcement opportunity has not
looked.

Where a contract covers semantics a Phase 3 promotion already addresses
(`docs/evidence/wave1-gap-trap-promotion-backlog.json`), reference the promotion rather than
inventing a second control for the same thing.

## 5. Per contract — all nineteen fields

```
bounded_context  domain_owner  ubiquitous_language  ports  adapters  state  transitions
identities  persistence  concurrency  failure_modes  recovery  evidence  observability
security  operator_surface  non_goals  architecture_fitness
deterministic_enforcement_opportunities
```

Plus `requirement_id`, `deferred_to_implementation` (must be empty), and optionally
`implementation_local_freedom` and `new_context_justification`.

`non_goals`, `concurrency` and `security` may truthfully answer "none"; the rest may not.

## 6. Deliverables

- `docs/evidence/wave2-design-contracts.json` (authoritative), with `contracts`,
  `required_requirements` (the ten ids), and provenance
- `docs/evidence/wave2-design-contracts.md` (prose companion)

## 7. Unratified and pending — design against, do not assume

`SF-REQ-056` is `AUTHORED_IN_THIS_PHASE` and **not ratified** (`POSTW1-DECIDE-008A`). Design it as
specified and mark the contract as depending on ratification. Five amendments remain pending
(`POSTW1-DECIDE-007A`); where a contract depends on one, say so rather than assuming it lands.

## 8. Acceptance

```
python3 tools/evidence/check_design_contracts.py docs/evidence/wave2-design-contracts.json
python3 tools/evidence/check_wave1.py --negative-controls
```

Enforces: all nineteen fields present and substantive; `deferred_to_implementation` empty; bounded
context known or justified; every selected requirement covered; at least one deterministic
enforcement opportunity per contract.

Do not edit any checker. If you believe a check is wrong, say so in `DISPUTED` and leave it
failing.

## 9. Out of scope

Do not begin Phase 10 verification, decompose into BIUs, or write implementation code. Do not
create, amend or weaken any requirement. Do not modify prior deliverables, Wave 1 evidence,
lifecycle state, Project state or worker contracts. Do not `git commit`, push, or use the network.

## 10. Terminal report — this block only

```
CONTRACTS=<n of 10>
NEW_CONTEXTS_PROPOSED=<n> JUSTIFIED=<n>
DEFERRED_DECISIONS=<must be 0>
ENFORCEMENT_OPPORTUNITIES=<n total> REUSING_PHASE3_PROMOTIONS=<n>
RATIFICATION_DEPENDENT=<ids>
AMENDMENT_DEPENDENT=<ids>
DESIGN_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
