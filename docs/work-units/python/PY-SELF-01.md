# Python self-building 01 — hand assessed work to the live work queue

**Status:** Candidate work unit; requires a fresh Agent Ready assessment before implementation.
**Source:** Founder direction on 2026-09-29; canonical Python self-building plan.
**Baseline:** Pin the current main revision at release. Work in an isolated workspace.

## Required outcome

Take one work unit that the existing Python preparation path has produced and Agent Ready has assessed as ready, and make it available to the existing Python live runner without hand-editing a GitHub Project item or copying a digest by hand. Preserve the exact requirement, approved design, work contract, assessment, dependencies and priority. The runner must accept the same work unit once and must refuse stale or unproved inputs.

This connects existing code. `UpstreamIntegration` currently ends at readiness eligibility and does not write the live work queue. `SandboxRunProfile` already reads and runs Project items with a work contract and readiness digest. PY-10 already proved the latter path on a separate sandbox. Do not recreate either subsystem.

## Permitted work and design ownership

- Add the smallest outward-facing handoff between the preparation path and the existing GitHub work adapter. The existing preparation/assessment service owns the meaning of ready; the existing coordinator owns release, scheduling and execution; GitHub remains a projected work surface.
- Record the immutable assessed contract and its source identity at a retrievable revision. Write the Project descriptor, dependency and priority fields through the existing adapter; read them back before making the item executable.
- Reuse the current persistence and effect controls for repeat requests, stale input, partial writes and unknown external outcomes. Hold safely if the Project or repository readback cannot prove the intended identity.
- Revalidate the assessment against the exact current contract at handoff. A ready assessment makes the item eligible for separate release checks; it never launches a worker by itself.

## Outside this work unit

No new requirement writer, design reviewer, assessment rubric, coordinator, worker provider or state store. No Node service change. No automatic new-requirement intake, model-based planning, landing/closure redesign, or broad interface work. No live execution in the production profile as part of this implementation unit.

## Acceptance

1. Given one approved design and a current Agent Ready result for an exact work contract, the handoff creates one live work item with the same contract identity, source links, dependencies, priority and assessment fingerprint. A fresh runner readback sees it as eligible; a release still passes the existing separate guards.
2. Repeating the same handoff has one observable item and no duplicate effect.
3. Changing the work contract, requirement or approved design after assessment refuses the handoff until reassessed. A fabricated, stale, incomplete or failed assessment never becomes ready.
4. A failed or ambiguous Project/repository write holds with a typed reason and recoverable evidence; a later readback resolves it without creating a duplicate.
5. An unrelated ready item remains eligible while this item is held. Source-to-contract obligations and explicit non-goals survive the handoff.
6. Tests prove the failure cases can actually turn red. Record exact input, assessment and Project readback identities and bounded resource behavior.

## Claude implementation and Codex review

Claude implements only after the candidate packet is assessed ready and released against an exact baseline. Claude records the design choice, reused components, changed paths, checks, resource owners and candidate revision. Before Codex reviews, the candidate must be published and independently retrievable at its exact revision.

Codex reviews in a fresh workspace. It checks requirement and design fit, domain ownership and inward dependency direction, Python typing/error/resource practices, duplicate mechanisms, overbuilt abstractions, secret exposure, stale/fake evidence, test quality and the negative cases above. A passing test suite is insufficient. Findings return to Claude with previously proven behavior and evidence preserved; only an independently accepted revision may land.

## Assessment request

Assess whether this is one independently verifiable unit. If the real handoff requires a separate design authority decision or the Project write and repository custody cannot be reviewed together, return a split or clarification with the exact boundary. Do not infer approval from this draft.
