# AlienIntent — Formal Problem Statement

**Date:** 2026-09-29 (Asia/Bangkok)
**Status:** Founder-directed analysis for requirements and v2 acceptance; this document does not alter existing product authority.
**Scope:** Autonomous agents producing software from authorized product intent. “Slop” here means a result that looks productive or complete while violating intent, engineering quality, evidence, or operational obligations.

## 1. Purpose and desired outcome

AlienIntent's primary purpose is to enable autonomous software-writing agents to deliver **working, high-quality, elegant software that satisfies all authorized requirements and the approved design intent**, without requiring a human to orchestrate every agent session or rescue routine failures. The product must keep agents from drifting, hallucinating, duplicating existing work, implementing the wrong solution, approving their own unsupported claims, and degrading previously proven behavior during repair.

The founding problem arose in FactoryChecks development under the name B-DISP: agents could produce useful code, but could not reliably own unbounded interpretation, architecture, self-verification, workflow state, or project memory. The historical record names lost architectural intent, rediscovered decisions, scope drift, agents redefining tasks, self-grading, excessive token use, humans relaying work between agents and tools, and inadequate durable evidence. The later product promise is **authorized requirements in → verified working software out**.

“Bug-free” is an aspiration, not a finite state a general software system can prove. AlienIntent must instead refuse known failures and unsupported completion claims, enforce the applicable acceptance contract with discriminating tests, independently review residual design and intent risk, verify required operational outcomes, and measure escaped defects. A passing unit suite or a fluent verifier narrative cannot establish absence of all defects.

## 2. Problem boundary

An authorized human or configured product authority supplies intent, priority, architecture/policy constraints, and material decisions. AlienIntent preserves and compiles those obligations, prepares bounded work, admits and supervises agents, verifies exact candidates, controls repair, and reaches truthful operational closure. The agents may propose or implement within their grant; they do not acquire authority to change the target. Product progress is the verified requirement/outcome, not an agent turn, BIU count, commit, merge, or attractive demo.

The following failure modes are distinct. A factory may prevent one and still fail the others.

| ID | Agent-slop problem | Observable failure | Required system outcome |
|---|---|---|---|
| PS-01 | Intent disappears at intake | A Founder request is acknowledged/deferred but never becomes a tracked requirement, or its priority/provenance vanishes. | Retain exact source and active obligation through canonical materialization, supersession or verified DONE. |
| PS-02 | Wrong problem is implemented | Ambiguity is guessed away; a plausible feature does not solve the authorized user need. | Expose missing owner decisions before implementation, preserve design rationale and verify intent fit against the source requirement. |
| PS-03 | Requirements weaken during decomposition | A split BIU omits an acceptance criterion, dependency, non-goal, proof obligation or integration responsibility. | Conserve and trace every authorized obligation across design, plan, BIUs, repair and closure. |
| PS-04 | Architecture and authority drift | A worker silently chooses a service, store, interface, trust boundary, product behavior or acceptance rule. | Close material design decisions before release; mechanically enforce known rules and independently review semantic design fit. |
| PS-05 | Duplicate or invented mechanisms | An agent rebuilds an existing capability, copies logic, creates a second owner or writes a compatibility layer without need. | Discover/reuse authoritative mechanisms, record justified exceptions, reject duplicated authority and needless complexity. |
| PS-06 | Scope and implementation slop | Unrelated edits, speculative abstractions, dead code, broad catches, insecure defaults, vague boilerplate or ornamental tests are accepted. | Bound the change to minimum correct work and require location-specific independent quality findings. |
| PS-07 | Hallucinated facts and fake completion | “Tests passed,” “deployed,” “fixed,” or “DONE” is inferred from prose, stale output, a different SHA, or absent telemetry. | Separate definition, observation and verdict; bind evidence to exact candidate/source/revision and fail closed on unknown facts. |
| PS-08 | Self-verification and weak tests | Producer writes both code and tests that simply mirror it, then approves its own work; checks cannot fail on a meaningful violation. | Independent verifier context/workspace and proven-red negative controls for mechanical claims. |
| PS-09 | Repairs thrash or regress | Each rejection causes broader rewrites, dropped evidence, broken previously passing behavior or renewed requirement interpretation. | Bounded, monotonic repair with a focused remaining-obligations context; preserve proof or explicitly supersede it. |
| PS-10 | Code works only in the happy path | Leaks, unbounded storage/logs, retries, races, failure masking, bad recovery or stale custody emerge after restart or long history. | Prove resource ownership/retention/pressure response and fault/restart behavior, not only a short functional test. |
| PS-11 | Local task passes but product fails | A commit lands while integration, deployment, browser/API behavior, release or SLO obligations are still false or unobserved. | Separate BIU acceptance from product/outcome closure and verify the applicable real-world predicates. |
| PS-12 | Knowledge and mistakes are repeatedly lost | New sessions rediscover architecture, prior decisions, failed approaches and review findings, spending tokens and repeating defects. | Maintain governed project cognition and role-specific current context; promote recurring mechanically testable failures to checks. |
| PS-13 | Human becomes workflow middleware | Founder manually chooses next work, relays agent results, repairs Project status, restarts stalled workers and explains history. | Continuous authorized flow with typed blockers, useful escalation only for real decisions, deterministic recovery and explainable state. |
| PS-14 | Factory optimizes activity rather than yield | Many tasks, retries and tokens produce little verified requirement-conformant software. | Measure accepted outcomes, first-pass quality, rework, escaped defects, time, cost and human intervention per outcome. |
| PS-15 | The factory itself becomes slop | Multiple state interpretations, historical exceptions, ritual checks and sidecars make control unpredictable and expensive. | One understandable deterministic authority path, bounded effects/resources, replayable truth and tests of failure cases. |

## 3. Cross-cutting acceptance principles

1. **Intent conservation:** every acceptance, verification and operational obligation is mapped to a current owner or an explicit supersession. No acknowledgement, task split, status projection or model summary can erase it.
2. **Authority before action:** no agent can silently decide product meaning, architecture, privacy/security, release or evidence policy. An unresolved material decision yields a typed, actionable question.
3. **Exact candidate truth:** definition, observation and verdict remain distinct and identify the source, candidate SHA, environment and policy version. UNKNOWN never becomes PASS, empty, zero or DONE.
4. **Independent, discriminating verification:** run mechanical checks before model judgment; demonstrate meaningful failing controls; assess semantic fit, elegance and maintainability in independent review.
5. **Minimum necessary implementation:** no duplicate authority, speculative mechanism or unrelated edit. Simplicity is a correctness property when it reduces defects and maintenance burden.
6. **Monotonic convergence:** unchanged requirements retain proven behavior and evidence across repair; retries are bounded and failed attempts remain visible.
7. **Operational closure:** only claim DONE after required landing, deployment, publication, readback and product behavior are actually observed.
8. **Continuous learning without self-authority:** classify failures with provenance, turn repeatable ones into versioned deterministic checks, and keep policy promotion under human/configured authority.

## 4. Evaluation model for v2

Evaluate the **whole path from raw authorized intent to verified product outcome**, not just scheduler correctness. A representative adversarial suite should seed: ambiguous requirements; a missing acceptance obligation during split; an existing capability tempting reimplementation; an unauthorized architecture change; plausible but wrong feature behavior; a passing but non-discriminating test; a fabricated test/deployment claim; a repair that regresses a prior property; a long-history resource leak; a provider/worker crash; a stale Project projection; and a missing real-world outcome despite a successful merge. Each case needs source intent, expected refusal/repair behavior, exact evidence and an independent verdict.

At minimum report requirement/outcome coverage, first-pass acceptance, review false acceptance and false rejection, escaped defects, rework cycles, duplicated mechanisms, architecture drift, human interventions, latency and total cognition/compute cost per **verified product outcome**. The release gate must include hard zero-tolerance classes for unauthorized material decisions, untraceable obligations, unverifiable DONE, self-approval and duplicate external effects; aggregate throughput must not mask them. Thresholds for rates and budgets require a separately approved evaluation protocol and baseline rather than invented numbers here.

## 5. Source and authority notes

- Founding reconstruction: `docs/research/alienintent-comprehensive-discussion-record.md`, §§1–7; `docs/strategy/2026-09-20-cognitive-factory-strategy-pre-research.md`, §§1–2.
- Current product requirements: `docs/decisions/alienintent-software-factory-plan.md`, especially SF-REQ-011–024, 029–030, 048–052, 057.
- Binding decisions: `docs/decisions/2026-09-20-design-contract-and-design-verification.md`; `2026-09-20-convergence-assistance-willing-convergence.md`; `2026-09-20-deterministic-failure-class-promotion.md`; `2026-09-28-input-half-product-intent-completeness.md`.
- v2 design: `docs/architecture/alienintent-factory-v2-formal-design.md`, especially §§1, 25, 34.6 and 35.
- This document synthesizes evidence and the Founder's stated purpose on 2026-09-29. It is not a claim that current Python code already satisfies these outcomes.
