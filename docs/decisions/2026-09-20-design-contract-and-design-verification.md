# Design Contract and Design Verification — SWF-25

Date: 2026-09-20. Status: **Founder decision — binding workflow/architecture semantics**, with one open scope decision recorded below.
Source: [PROP-2026-0002](../proposals/PROP-2026-0002-design-contract-and-design-verification.md), submitted by the Founder 2026-09-20 (`authority_level: founder`, `proposal_type: workflow_architecture`).
Canonical requirement: **SF-REQ-051**.

## Principle

> **Close every decision that affects product meaning, architecture, trust, persistence, interfaces, or verification before implementation begins. Leave only local implementation choices open.**

## Workflow semantics

```text
Requirement / Proposal → SPECIFY → DESIGN → DESIGN VERIFICATION → PLAN / decomposition
   → BIU Contract → Agent-Ready → READY → IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE
```

**DESIGN and DESIGN VERIFICATION are semantic sub-stages, not visible Project lanes.** They exist initially as artifacts and gates inside SPECIFY/PLAN. The lifecycle vocabulary of Architecture Authority §9 is unchanged and no Project field is altered by this record.

## Design Contract

A first-class artifact containing, where applicable: requirements satisfied; product behavior affected; bounded contexts/modules affected; domain ownership; architecture impact; invariants; public interfaces; persistence/data changes; dependency direction; external-system boundaries; failure behavior; recovery behavior; idempotency expectations; security/privacy constraints; capabilities required; observability requirements; explicit design decisions; deferred implementation-local decisions; acceptance criteria; verification strategy; evidence obligations; non-goals.

**Design depth is proportional to the change.** Trivial changes do not acquire bureaucracy.

## Design authority boundary

The implementation worker **may** decide: function decomposition; local helpers; variable naming; internal control flow; minor refactoring inside the approved boundary.

The implementation worker **must not** independently decide: bounded-context ownership; new services/databases/queues; public API semantics; persistence strategy; security/privacy model; architecture direction; product behavior; verification obligations; acceptance-criteria reinterpretation.

If such a decision remains unresolved, **the BIU is not ready**.

## Design Verification

Before BIU decomposition or release, the Design Contract is verified against: EOS; project architecture authority; DDD boundaries; Hexagonal dependency direction; ACL boundaries; Ubiquitous Language; existing ADRs and Founder decisions; security/privacy rules; canonical existing mechanisms; consistency with requirements; compatibility with existing interfaces; unnecessary mechanism/complexity; observability and recovery expectations.

**Mechanical-first**, consistent with SWF-24:

> **If a design rule can be checked mechanically, verify it mechanically before model or human review spends intelligence on it.**

Mechanical examples: forbidden dependency direction; illegal bounded-context references; vendor concepts in domain; invalid interface dependencies; duplicate mechanism introduction; schema compatibility constraints. Remaining design judgment is independently reviewed.

## Relationship to BIU and Agent-Ready

A BIU is **derived from** an approved Design Contract and does not reopen approved design decisions. It carries design references, fixed decisions, allowed implementation freedom, boundaries, completion criteria and evidence obligations.

Agent-Ready should eventually confirm not only BIU completeness but that required design exists, design verification passed, no unresolved design authority remains, and implementation-local freedom is clearly bounded. That extension is part of SF-REQ-051 and is not built now.

## Relationship to existing authority

- **Architecture Authority §9** lifecycle semantics — unchanged; DESIGN remains a sub-stage.
- **§44** remaining pre-Python design work — this names the missing gate between requirements and BIUs.
- **§45** Founder escalation — the "must not decide" list mirrors what already requires Founder review.
- **SF-REQ-010 BIU contract model** — the BIU already carries fixed decisions and boundaries; the Design Contract is their upstream source.
- **SF-REQ-012 ambiguity detection**, **SF-REQ-013 requirements → BIU compilation**, **SF-REQ-015 BIU lint / Agent-Ready** — the compiler path this gate feeds.
- **SF-REQ-048 minimum necessary work** and **SF-REQ-049 convergent repair** — bounded freedom and preserved proof.
- Plan §ZhangHanDong/agent-spec borrowings — "contract linting before implementation" and fixed technical decisions are the same lineage.

## Open decisions — not decided here

1. **Effective scope.** Whether the Design Contract / Design Verification gate applies to the remaining Wave 1 BIUs (PY-05 through PY-10, already authored and Agent-Ready assessed), or only from Wave 2 onward. Applying it to Wave 1 would require design contracts for six existing BIUs before release and would slow the current sequence; deferring it leaves Wave 1 on its approved plan. **Founder input required.** Until decided, Wave 1 proceeds unchanged under its approved contracts.
2. **Visible lifecycle states.** Whether DESIGN and DESIGN VERIFY eventually become visible Project lifecycle states rather than sub-stages. Explicitly deferred by the proposal; not blocking.

## Scope

No implementation. No BIU created from this record. No Project lane or field changed. The running Wave 1 factory is not interrupted. FactoryChecks is untouched.
