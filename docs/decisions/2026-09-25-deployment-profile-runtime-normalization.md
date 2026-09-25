# Deployment Profile and Runtime Normalization

Date: 2026-09-25. Status: **Founder decision — binding**.

## Decision

AlienIntent will implement the current Founder environment first while designing the runtime contract for multiple deployment environments (**Solve for N**).

The first implementation target is the Founder's current AlienIntent host. Generalization must not delay making that environment reliable, inspectable and efficient.

> **Standardize the physical environment wherever practical. Configure unavoidable host differences deterministically. Hide the remainder behind stable capability interfaces. Never make ordinary cognition rediscover infrastructure.**

Linux/container isolation is a preferred mechanism for physical standardization when operationally appropriate. Different deployment profiles may use different physical arrangements, but routine Factory Director cognition must see the same logical capability surface.

## Deployment-profile completeness rule

> **A deployment profile is complete only when routine Factory Director operation requires no environmental discovery.**

Routine Factory Director operation must not need to discover:

- where Agent Ready is installed;
- which Python or virtual environment to use;
- where the AlienIntent repository or required workspaces are;
- which GitHub credentials/configuration are authoritative;
- how to invoke the configured local-model runtime;
- where canonical factory tools, proof runners or control-plane commands live;
- which configured capability implementation is authoritative.

If ordinary Director cognition must answer one of those questions by broad filesystem search, ad hoc shell exploration or host-specific inference, the deployment profile is incomplete.

## Layered normalization strategy

AlienIntent may combine multiple mechanisms according to operational requirements:

1. **Physical/runtime standardization** — Linux, containers and fixed filesystem/tool layouts where practical.
2. **Installation-time configuration** — explicit bindings for differences that cannot or should not be standardized, including credentials, repository identity, external endpoints, mounts and hardware.
3. **Deterministic adapters and capability resolution** — convert host-specific implementations into stable factory capabilities.
4. **Typed capability surface** — routine cognition requests semantic operations rather than rediscovering commands, paths or invocation syntax.
5. **Diagnostic escape surface** — broad shell/system discovery is reserved for tasks whose explicit purpose is environment diagnosis or repair.

Containers and adapters are complementary. A container removes avoidable environmental variance; configuration resolves necessary variance; adapters hide the remaining variance.

## N=1 implementation, N-capable architecture

The immediate deployment profile is the Founder's current host. Its concrete paths, services, credentials/config locations, model runtime and supported factory tools should be resolved deterministically during installation/configuration.

The architecture must nevertheless permit later profiles such as:

- a fully containerized local factory;
- a contained control plane with external GPU/model capabilities;
- another workstation or server;
- cloud-hosted or remote capabilities;
- multiple concurrent factory instances.

The stable logical capability contract must not depend on those physical arrangements.

A useful conformance question is:

> **Could the same Factory Director episode packet and action plan run unchanged across supported deployment profiles?**

If not, host/environment knowledge is leaking into cognition.

## Determinism-before-cognition rule

For routine control work:

> **Determinism decides when cognition is allowed to become involved; cognition does not decide whether determinism should have been used.**

Mechanically knowable facts and stable capability discovery belong outside the model. Cognition should receive normalized authoritative state and the operations it is permitted to request.

If a deterministic capability exists for an operation, the Director should consume the stable capability rather than locate or reconstruct its implementation.

Ordinary Factory Director operation must not silently degrade into systems administration because a command, path or tool binding was omitted from the deployment profile.

## Evidence and maturity

The 2026-09-25 starvation-recovery episode exposed the motivating failure: a frontier-model Director spent substantial time on a broad `find /` search for Agent Ready even though Agent Ready already existed on the host. The search was unnecessary environmental rediscovery and was manually terminated without stopping the Director episode.

This incident is evidence for runtime normalization, not authorization for a broad redesign before factory flow is restored.

A useful Factory Director maturity measure is:

> **Percentage of Factory Director episodes completed without arbitrary filesystem or shell discovery.**

Supporting measurements may include typed-capability completion rate, general-shell fallback rate, environment-discovery tool calls/tokens, capability lookup failures, missing-configuration failures and host-specific-knowledge incidents. Instrumentation should be added only when it produces actionable information and must not starve normal factory operation.

## Priority

This decision supports, and does not supersede, the standing operating priorities:

1. keep the factory producing high-quality, working code;
2. prevent the input pipeline from starving;
3. harden the factory opportunistically from observed operational evidence.

Implement the smallest useful profile normalization for the current host first. Generalize only as additional deployment requirements become real.
