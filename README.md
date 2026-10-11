# AlienIntent

**Intent-preserving autonomous software engineering.**

AlienIntent is an open-source project from **Alien Logic Lab** exploring a harder version of autonomous software development:

> Can AI workers produce software without acquiring the authority to reinterpret the intent they were given?

Most coding-agent systems optimize for producing code. AlienIntent is being designed around a stricter objective: preserve product intent from capture through implementation, independent verification, review, and closure.

## The workflow

AlienIntent's target lifecycle is:

```text
CAPTURE → SPECIFY → PLAN → TASKS → READY
        → PRODUCER → VERIFIER → REVIEWER → CLOSURE → DONE
```

The first half compiles product intent into bounded executable work. The second half executes that work under deterministic authority.

**READY is the boundary between unresolved meaning and executable construction.**

By the time work reaches a PRODUCER, architectural ownership, legal state transitions, capabilities, invariants, acceptance criteria, and evidence obligations must already be resolved. The PRODUCER's job is to fill a deliberately shaped hole in the architecture—not redesign the system while implementing it.

## V3 direction

AlienIntent V3 is being built around a small **Rust deterministic core** with a model-facing exterior.

The core idea is simple:

> **Cognition proposes. The deterministic domain kernel disposes.**

Where practical, important rules are not given to models as instructions. They are encoded as types, capabilities, state transitions, dependency boundaries, or deterministic gates that workers cannot bypass.

The Rust core is intended to own:

- domain entities, value objects, aggregates, and state machines;
- authority and capability boundaries;
- legal lifecycle transitions;
- deterministic policy and invariant enforcement;
- requirement and evidence provenance;
- candidate custody and closure legality.

Model-facing components may perform cognition and propose artifacts, but proposals become canonical only through the deterministic core.

## Build the box first

V3 begins with a deliberately small milestone:

> **Can an untrusted model violate a BIU's deterministic construction contract?**

Before building the larger autonomous factory, AlienIntent will build and adversarially test the confinement boundary itself.

Success is not that a model behaves.

Success is that the model tries to violate the contract and cannot.

## Domain-driven architecture

AlienIntent is designed around Domain-Driven Design and Hexagonal Architecture.

The goal is not decorative folder structure. Domain ownership and invariants should be explicit and mechanically protected where possible:

- bounded contexts own their domain meaning;
- aggregates own legal state transitions;
- semantic identities use semantic types;
- ports define permitted capabilities;
- infrastructure does not acquire domain authority;
- cross-context dependencies are explicit and constrained;
- invalid states should be difficult or impossible to represent.

## Requirement evidence

AlienIntent does not treat test count as a quality metric.

The intended evidence chain is:

```text
Requirement
  → Acceptance Criterion
  → Domain Invariant / Behavior
  → Implementation
  → Discriminating Evidence
```

A passing test is useful only when it establishes something the requirement actually requires.

## Repository model

This repository is the **curated public representation of AlienIntent**.

Active engineering, private design history, operational evidence, worker artifacts, credentials, and internal continuity records are intentionally kept outside the public repository. Public source, releases, documentation, and contribution surfaces are published here deliberately.

That separation is part of the product's trust model, not an accident of development.

## Status

AlienIntent V3 is in early architecture and confinement development. The public repository will grow as components are ready for deliberate publication.

Expect interfaces and architecture to evolve before the first stable release.

## Contributing

Thoughtful technical criticism is welcome, especially around:

- deterministic confinement of AI coding workers;
- DDD and architecture fitness enforcement;
- capability-based worker boundaries;
- requirement-to-evidence traceability;
- adversarial verification;
- Rust typestate and domain modeling;
- autonomous software-factory reliability.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).

---

**AlienIntent by Alien Logic Lab**
