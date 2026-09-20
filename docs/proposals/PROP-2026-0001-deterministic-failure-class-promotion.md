---
proposal_id: PROP-2026-0001
title: Deterministic Failure-Class Promotion / Proven-Red Verification
submitted_by: founder
submitted_at: 2026-09-20
proposal_type: product_requirement
authority_level: founder
status: submitted
---

# Deterministic Failure-Class Promotion / Proven-Red Verification

## Intent

AlienIntent should use model intelligence to discover recurring engineering failure classes, then convert those known failure classes into deterministic verification wherever practical.

Durable principle:

> **Model intelligence discovers failure classes; deterministic verification makes known failure classes cheap, repeatable, and boring.**

## Problem

Repeatedly paying an expensive verifier to rediscover a known mechanically detectable defect wastes time, tokens, and human attention.

Recent PY-04 repair cycles demonstrated a recurring class of evidence failure:

- implementation behavior can be correct;
- a binding rule may appear covered;
- but removing or inverting the mechanism still leaves the suite green.

That means the evidence is non-discriminating.

## Proposed capability

AlienIntent should support promotion of recurring REVIEW/VERIFIER findings into deterministic VERIFY checks.

For every mechanically testable binding rule:

> **Evidence is insufficient unless a meaningful violation causes the applicable check to fail.**

## Promotion lifecycle

```text
REVIEW / VERIFIER discovers failure class
        ↓
failure class recorded with evidence
        ↓
recurrence / materiality assessed
        ↓
mechanizability assessed
        ↓
deterministic check created or strengthened
        ↓
proven-red / mutation / negative-control evidence demonstrates discrimination
        ↓
check promoted into VERIFY
        ↓
future occurrences caught mechanically
```

## Acceptable proof techniques

Possible techniques include:

- proven-red tests;
- mutation testing;
- negative controls;
- rule inversion;
- fault injection;
- fixture mutation;
- boundary-violation fixtures.

The implementation technique is not prescribed by this proposal.

## Required evidence

A promoted rule should retain:

- failure-class identifier;
- originating findings;
- rule definition;
- deterministic check reference;
- proven-red / negative-control evidence;
- promotion authority;
- effective version/date;
- known limitations;
- supersession history.

## Interaction with Convergent Repair

This complements Behavioral Monotonicity and Evidence Monotonicity.

Once a failure class is understood and reliably mechanizable, future BIUs should not depend on agents remembering the lesson.

## Measurement

Candidate metrics:

- review_findings_promoted_to_verify;
- proven_red_coverage_rate;
- mechanically_enforced_binding_rules;
- deterministic_catch_rate;
- recurrence_rate_after_promotion;
- verifier_findings_avoided_after_promotion;
- verifier_tokens_saved_after_promotion;
- verifier_time_saved_after_promotion;
- false_positive_rate_by_rule;
- false_negative_incidents_by_rule;
- time_from_failure_discovery_to_mechanization.

Missing telemetry must remain UNKNOWN, not zero.

## Non-goals

This proposal does not imply:

- every REVIEW judgment becomes deterministic;
- automatic policy promotion without authority;
- replacing independent review;
- a new lifecycle state;
- blocking current Wave 1 execution.

## Desired outcome

Known recurring failure classes become cheap, deterministic VERIFY checks, leaving model intelligence for novel judgment and failure discovery.
