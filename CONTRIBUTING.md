# Contributing to AlienIntent

AlienIntent is under active pre-release development.

This public repository is a curated publication surface. The active engineering repository, internal design history, operational evidence, worker artifacts, credentials, and private continuity records are not public.

## Useful contributions

The most useful public contributions right now are:

- architecture criticism grounded in concrete failure modes;
- adversarial cases that could escape a deterministic worker boundary;
- DDD / Hexagonal Architecture fitness ideas that can be mechanically enforced;
- Rust type-system approaches for preventing illegal lifecycle transitions;
- requirement-to-evidence traceability techniques;
- reproducible defects in published source or releases.

## Issues

Public Issues are an external intake surface. Please describe the behavior, requirement, failure mode, or architectural concern as precisely as possible.

An Issue does not itself grant implementation authority or alter the canonical product plan.

## Pull requests

Do not assume a pull request is the autonomous factory's review mechanism. AlienIntent's execution model uses explicit PRODUCER, VERIFIER, REVIEWER, and CLOSURE stages against exact candidates.

For published source, conventional pull requests may be used where appropriate for human collaboration, but acceptance remains subject to project architecture, requirements, and publication policy.

## Security and private material

Do not submit credentials, tokens, private engineering records, internal filesystem paths, or other sensitive operational material to this repository or its Issues.

If you believe you found a security-sensitive problem, avoid posting exploit details publicly until a private reporting channel is published.

## License

By contributing material accepted into this repository, you agree that it may be distributed under the repository's Apache-2.0 license unless explicitly stated otherwise.
