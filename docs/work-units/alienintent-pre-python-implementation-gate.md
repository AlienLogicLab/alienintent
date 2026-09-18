# AlienIntent — Pre-Python Implementation Gate

**Date:** 2026-09-19
**Status:** Binding implementation gate

No substantial canonical Python implementation may begin until these artifacts exist and are Founder-approved or explicitly delegated:

- [ ] Product Intent
- [ ] Ubiquitous Language v1
- [ ] bounded-context model
- [ ] Hexagonal Architecture / ports-and-adapters specification
- [ ] Anti-Corruption Layer rules
- [ ] Python engineering standard
- [ ] BIU/domain execution model
- [ ] lifecycle semantics and external mapping rules
- [ ] automatic-release policy model
- [ ] verifier-independence / assurance-policy model
- [ ] capability/authority model, including live deployment authority
- [ ] optional sandbox/container model
- [ ] event-ingress port and direct-webhook/outbound-relay adapters
- [ ] no-polling / async integration rule
- [ ] internal event model and once-only processing semantics
- [ ] concurrency/cancellation/retry policy
- [ ] provider capability/routing contract
- [ ] cheapest-capable / local-first routing policy
- [ ] Context Engineering v1 carried forward
- [ ] memory/state/evidence separation carried forward
- [ ] operational-state persistence design
- [ ] Engineering Trajectory / Quality Evidence persistence design
- [ ] community-learning contribution model
- [ ] cost/token governance
- [ ] operator Control Plane application model
- [ ] control-plane presentation adapters (CLI/web as approved)
- [ ] adapter versioning/extensibility model
- [ ] configuration and SecretProvider model
- [ ] installer/bootstrap design
- [ ] observability model
- [ ] EOS inheritance/contribution mechanism
- [ ] architecture fitness rules
- [ ] Node→Python coexistence/conformance strategy
- [ ] Python Sovereignty acceptance criteria

## Binding rules

- DDD, Hexagonal Architecture, Anti-Corruption Layers, Python best practices, and EOS are mandatory.
- Convention over configuration.
- Solve for N; optimize N=1.
- Polling is prohibited unless explicitly approved as an exception.
- Merge is not a lifecycle state.
- PRODUCER/VERIFIER are domain roles; external identities are deployment policy.
- BIU remains the bounded implementation artifact until Ubiquitous Language work explicitly changes it.
- Agents may be granted dangerous capabilities, including live deployment authority, when the BIU requires them.
- Sandboxing is optional/configurable.
- Context Engineering, memory separation, trajectory evidence, Quality Evidence, and community learning are existing architecture inputs, not rediscovery tasks.
- The operator Control Plane is first-class architecture, not an optional dashboard.
- Existing Node AlienIntent is the bootstrap implementation; Python replaces it only after Python Sovereignty.
