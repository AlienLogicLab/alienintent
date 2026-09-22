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

## Lifecycle role of VERIFY and REVIEW (Founder clarification, 2026-09-21)

This clarifies the lifecycle significance of the principle above. It adds no
Product Requirement, no lifecycle state, no implementation obligation and no
retrofit onto a released BIU.

Canonical meaning:

> **VERIFY proves what AlienIntent already knows how to check. REVIEW discovers
> what AlienIntent does not yet know how to check. Deterministic failure-class
> promotion converts suitable REVIEW discoveries into future VERIFY capability.**

*Terminology (2026-09-22, Founder decisions v0.1): the product-native term for this mechanism is
**deterministic failure-class promotion**. The concept was informed by the external "Gap Trap"
project; that name is attribution, not AlienIntent Ubiquitous Language, and is not used as a
canonical noun or verb. Historical programme artifacts that carry the name are unchanged.*

Shorthand:

> **REVIEW explores; VERIFY accumulates.**

### VERIFY — accumulated mechanically enforceable knowledge

VERIFY is the factory's accumulated mechanically enforceable knowledge. Where
applicable it includes deterministic tests; architecture and quality fitness
rules; invariants; state-machine constraints; schema checks; admission gates;
evidence-consistency checks; negative controls; proven-red checks; and known
mechanically expressible failure classes.

VERIFY grows by accumulation. Every promoted check is knowledge the factory no
longer pays model cognition to rediscover.

### REVIEW — the discovery frontier

REVIEW is the primary lifecycle stage for novel, non-mechanized engineering
judgment: novel engineering-quality failures; not-yet-mechanized failure classes;
architecture and design coherence; simplicity; maintainability; unintended
coupling; semantic fit to the authorized intent; suspicious behaviour no
deterministic rule yet captures; other context-sensitive qualitative judgment;
and the learning candidates that feed promotion.

**REVIEW is not merely a second pass over VERIFY.** Its purpose is to apply
engineering intelligence where deterministic knowledge ends.

### The frontier must keep moving

> REVIEW must not become a permanent checklist of recurring mechanizable defects.

When a REVIEW finding is sufficiently generalizable, materially useful and
mechanically expressible, AlienIntent assesses it for deterministic promotion
through this decision / SF-REQ-050.

Promotion is **incomplete** until the new mechanism carries discriminating
evidence that a meaningful violation causes it to fail. The proven-red, mutation
and negative-control requirements stated above apply in full and are not weakened
by this clarification.

> A successful promotion should reduce future cognitive work.

> If the same mechanically expressible defect keeps being rediscovered in REVIEW
> across BIUs, that is evidence of a learning-loop failure, an incomplete
> promotion, or ineffective enforcement — not merely an unlucky BIU.

PY-08 is the worked example already in the record. Five repair cycles traded
defects while two contract obligations went unattempted — AC 4's proof that
`explain` reproduces the kernel's own decision, and the verification
requirements' negative-control and backdoor coverage. Sequencing exactly that
proof first closed the loop in a single cycle with no fresh defect.
[SWF-23 §4b](2026-09-20-convergent-repair-monotonic-progress.md) turned that
lesson into verification-first repair sequencing and carried it into the
unreleased PY-09 and PY-10 contracts rather than retrofitting released PY-08.
That is this movement in miniature: a judgment repeatedly rediscovered at REVIEW
became a stated, sequenced obligation. Making it deterministic — a check that
fails when a changed path lacks discriminating coverage — is the promotion
SF-REQ-050 owns and has not yet built.

Not every REVIEW finding must become deterministic. Some engineering judgment may
remain qualitative indefinitely; such a finding is retained as an explicit
qualitative review heuristic rather than discarded or forced into a check it
cannot support. Promotion remains authority-controlled (SF-REQ-032) and
independent review is not replaced.

The long-term target is therefore **not** that everything becomes VERIFY:

```text
everything reliably mechanizable becomes VERIFY
REVIEW remains the moving frontier of engineering judgment
```

REVIEW should become **more valuable, not larger**. Its value rises because known
repetitive checks migrate out of it, leaving cognitive capacity for the defects
that are still novel.

### Wave 1 bootstrap does not collapse the distinction

The Node bootstrap currently combines mechanical verification and qualitative
review in a single VERIFIER invocation; REVIEW is not a separately dispatched
worker lane; and verifier `ACCEPT` routes to ACCEPT rather than REVIEW. That is a
Wave 1 bootstrap implementation limitation and convenience, recorded in
[operations](../operations.md#lifecycle-semantics). **It does not collapse the
canonical semantic distinction between VERIFY and REVIEW.** This clarification
wires no REVIEW worker and changes no current dispatch, result routing, lifecycle
state or released BIU contract.

## Effective scope

This states what already counts as sufficient evidence under existing contract language — Architecture Authority §39, SF-REQ-018's requirement that fitness checks have negative controls proving they can fail, and each Wave 1 BIU's "executable proof" verification requirement. It is **not** a new obligation retroactively imposed on accepted evidence, and it does not reopen accepted BIUs.

Promotion of findings into VERIFY checks is a **capability to be built** (SF-REQ-050), not something Wave 1 implements now. No current implementation BIU is expanded to implement it.

## Relationship to existing authority

- **SF-REQ-018 architecture conformance** — already requires negative controls for fitness checks; this generalizes the standard beyond architecture rules.
- **SF-REQ-014 mechanical test obligations** — derives obligations before implementation; this promotes *discovered* classes afterwards.
- **SF-REQ-032 learning proposals, not autonomous policy mutation** — promotion is a proposal requiring authority, never automatic.
- **SF-REQ-049 / SWF-23 convergent repair** — once a class is mechanized, future BIUs stop relying on agents remembering the lesson.
- **SF-REQ-020 fake-DONE prevention**, **SF-REQ-024 factory yield**.

## The learning loop and its existing owners

The loop this decision participates in is reconstructible from existing canonical
authority:

```text
EXECUTE
   ↓  OBSERVE
   ↓  REVIEW — qualitative discovery
   ↓  GENERALIZE the learning or failure class
   ↓  identify the canonical authority that owns it
   ↓  assess mechanizability
   ├─ mechanizable → build deterministic trap/control
   │                 → prove red / negative control
   │                 → promote into VERIFY
   │                 → ratchet and preserve the achieved property
   └─ otherwise    → retain an explicit qualitative review heuristic
   ↓  future execution
   ↓  observe effectiveness / recurrence
   ↓  strengthen, revise or supersede under authority
```

No stage gains a new owner here. Each already belongs to an existing requirement
or decision; this record cross-references rather than restates them.

| Loop stage | Canonical owner |
|---|---|
| execution observation / trajectory | SF-REQ-029 Engineering Trajectory (#44) |
| derived quality evidence and its consistency verification | SF-REQ-030 Quality Evidence (#45) |
| REVIEW qualitative discovery and learning candidates | lifecycle authority: [FD-01](2026-09-19-alienintent-work-management-execution-authority.md), [work-and-release](../architecture/pre-python-gate/work-and-release.md), and this section |
| learning candidate becoming an authority-gated proposal | SF-REQ-032 learning proposals, not autonomous policy mutation (#47) |
| mechanizability assessment, deterministic trap, proven-red evidence, promotion into VERIFY | this decision / SF-REQ-050 (#61) |
| negative controls proving architecture fitness checks can fail | SF-REQ-018 architecture conformance (#29) |
| mechanical obligations derived *before* implementation | SF-REQ-014 (#20) |
| preserving achieved behaviour and proof across repair cycles | [SWF-23](2026-09-20-convergent-repair-monotonic-progress.md) / SF-REQ-049 (#60) |
| effectiveness, recurrence and yield measurement | SF-REQ-024 factory yield (#35), through the metrics listed below |

### Enforcement strength, and why "documented" is not "learned"

> **Documentation is weaker than enforcement.**

A rule may be `DOCUMENTED`, `PROMPTED`, `MECHANICALLY CHECKED`, `PROVEN RED`,
`GATED` or `STRUCTURALLY ENFORCED`. These are descriptive strength labels for
assessing a promotion, not required enum values and not a new schema. Recording a
rule is the weakest of them: a documented rule that no mechanism can fail on is
exactly the non-discriminating evidence this decision exists to reject.

> A learning-loop success should eventually reduce the model cognition required to
> rediscover known defects.

The metrics below already carry that effectiveness signal — recurrence after
promotion, verifier findings avoided, deterministic catches, false positives and
negatives, tokens and time saved, and time from discovery to mechanization. They
extend SF-REQ-024; no telemetry subsystem is introduced here.

## Measurement (future yield metrics)

`review_findings_promoted_to_verify`, `proven_red_coverage_rate`, `mechanically_enforced_binding_rules`, `deterministic_catch_rate`, `recurrence_rate_after_promotion`, `verifier_findings_avoided_after_promotion`, `verifier_tokens_saved_after_promotion`, `verifier_time_saved_after_promotion`, `false_positive_rate_by_rule`, `false_negative_incidents_by_rule`, `time_from_failure_discovery_to_mechanization`.

Missing telemetry is **UNKNOWN**, never zero. No telemetry subsystem is built during Wave 1 (SWF-18).

**Attribution caveat for Wave 1 data.** Several of these metrics presuppose that a
finding can be attributed to REVIEW or to VERIFY. Wave 1's Node bootstrap cannot
make that attribution: it combines mechanical verification and qualitative review
in a single VERIFIER invocation, so a Wave 1 rejection count means *combined
verifier rejections*, not VERIFY failures and not REVIEW discoveries. Any dataset
derived from Wave 1 execution must say so rather than presenting the figure as
either. Attributable measurement of `review_findings_promoted_to_verify`,
`verifier_findings_avoided_after_promotion` and the recurrence metrics requires the
distinction to be observable in the record — through a separately dispatched REVIEW
lane or per-finding classification within the combined invocation. Neither exists
today, and this decision does not create either. Until one does, those metrics are
**UNKNOWN** for Wave 1 rather than derivable from rejection counts.

## Non-goals

Not every REVIEW judgment becomes deterministic. No automatic policy promotion without authority. Independent review is not replaced. No new lifecycle state. Wave 1 execution is not blocked.
