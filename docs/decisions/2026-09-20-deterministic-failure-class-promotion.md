# Deterministic Failure-Class Promotion / Proven-Red Verification — SWF-24

Date: 2026-09-20. Status: **Founder decision — binding engineering principle**.
Source: [PROP-2026-0001](../proposals/PROP-2026-0001-deterministic-failure-class-promotion.md), submitted by the Founder 2026-09-20 (`authority_level: founder`).
Canonical requirement: **SF-REQ-050**.

**Founder assignment (2026-09-20):** Priority **P1**; Wave **3**. This
assignment does not create a BIU or authorize implementation.

## Durable principle

> **Model intelligence discovers failure classes; deterministic verification makes known failure classes cheap, repeatable, and boring.**

And, for every mechanically testable binding rule:

> **Evidence is insufficient unless a meaningful violation causes the applicable check to fail.**

Deterministic enforcement is not trusted merely because a check exists and passes. A check that cannot fail is not evidence.

## Promotion lifecycle

```text
REVIEW / VERIFIER discovers failure class
        ↓  failure class recorded with evidence
        ↓  recurrence / materiality assessed
        ↓  mechanizability assessed
        ↓  deterministic check created or strengthened
        ↓  proven-red / mutation / negative-control evidence demonstrates discrimination
        ↓  check promoted into VERIFY
future occurrences caught mechanically
```

Acceptable proof techniques include proven-red tests, mutation testing, negative controls, rule inversion, fault injection, fixture mutation and boundary-violation fixtures. No technique is prescribed.

## Evidence a promoted rule retains

Failure-class identifier; originating findings; rule definition; deterministic check reference; proven-red / negative-control evidence; promotion authority; effective version/date; known limitations; supersession history.

For each promoted mutation, proven-red or negative-control check, retain:

- the governing binding rule;
- the semantic violation intentionally introduced;
- applicability conditions;
- expected failing evidence and actual result;
- one result: `KILLED`, `SURVIVED`, or `NOT_APPLIED`;
- for `NOT_APPLIED`, why the mutation could not be applied; and
- implementation/reference and provenance/version of the mutation/check.

`NOT_APPLIED` must never count as `KILLED`. A source-code patch alone is not a
mutation definition: the semantic rule violation being tested must be stated.
The evidence must let a reviewer determine what rule was exercised and why the
observed result follows.

## Effective scope

This states what already counts as sufficient evidence under existing contract language — Architecture Authority §39, SF-REQ-018's requirement that fitness checks have negative controls proving they can fail, and each Wave 1 BIU's "executable proof" verification requirement. It is **not** a new obligation retroactively imposed on accepted evidence, and it does not reopen accepted BIUs.

Promotion of findings into VERIFY checks is a **capability to be built** (SF-REQ-050), not something Wave 1 implements now. No current implementation BIU is expanded to implement it.

## Relationship to existing authority

- **SF-REQ-018 architecture conformance** — already requires negative controls for fitness checks; this generalizes the standard beyond architecture rules.
- **SF-REQ-014 mechanical test obligations** — derives obligations before implementation; this promotes *discovered* classes afterwards.
- **SF-REQ-032 learning proposals, not autonomous policy mutation** — promotion is a proposal requiring authority, never automatic.
- **SF-REQ-049 / SWF-23 convergent repair** — once a class is mechanized, future BIUs stop relying on agents remembering the lesson.
- **SF-REQ-020 fake-DONE prevention**, **SF-REQ-024 factory yield**.

## Measurement (future yield metrics)

`review_findings_promoted_to_verify`, `proven_red_coverage_rate`, `mechanically_enforced_binding_rules`, `deterministic_catch_rate`, `recurrence_rate_after_promotion`, `verifier_findings_avoided_after_promotion`, `verifier_tokens_saved_after_promotion`, `verifier_time_saved_after_promotion`, `false_positive_rate_by_rule`, `false_negative_incidents_by_rule`, `time_from_failure_discovery_to_mechanization`.

Missing telemetry is **UNKNOWN**, never zero. No telemetry subsystem is built during Wave 1 (SWF-18).

## Non-goals

Not every REVIEW judgment becomes deterministic. No automatic policy promotion without authority. Independent review is not replaced. No new lifecycle state. Wave 1 execution is not blocked.
