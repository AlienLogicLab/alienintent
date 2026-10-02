# Python self-building 01 — publish assessed work into the live queue

**Status:** Design under revision after independent review. The Founder has not approved it. The earlier Agent Ready result assessed different text and cannot release this version.

## Purpose

Take one prepared, assessed work item and make it available to the Python factory without changing its instructions, losing its assessment, creating duplicate work, or giving it permission that nobody granted. The current Python preparation path and live Project reader are separate. A sandbox completed six manually seeded tasks; it did not prove this handoff.

The Founder has stopped the effort to finish Issue #125 under Node. Its incomplete live recovery proof remains incomplete. A separate owner is shutting down Node. Before hand-fed work, read back whether any old claim or external change remains uncertain and ensure there is only one active writer. Do not wait for #125 to say DONE or claim that it passed its missing proof.

## Terms and responsibilities

- The **work instructions** are the exact task content the assessment evaluated. The design must identify those bytes, their fixed version, and how the executable contract corresponds to them. A digest alone is a fingerprint, not the instructions.
- The **assessment** says those particular instructions are sufficiently prepared. It does not grant permission to start implementation. The existing release check separately needs an explicit authorization tied to the exact starting version.
- The **Issue** is the durable work record in the repository; the **Project item** is its board entry. The design proposes a real Issue rather than a temporary Project note because the current queue and later closure need a stable identity and history. This is a GitHub adapter choice, not a universal product rule.
- **READY** means the item may be considered by the scheduler. It must not be written until the associated content, assessment, authorization, Project identity, priority and dependencies are demonstrably coherent. A READY label alone must not bypass the independent release check.

## Required inputs before implementation can be specified

Name the authoritative location and exact version of the original requirement, approved design, proof plan, decisions, assessed task text, resulting execution contract, assessment receipt, dependencies and priority. Name the owner who grants release authorization and the record the existing check consumes. Define how a changed source invalidates an assessment and how the preparation service is called with its original candidate and proof plan; the Issue comment alone is insufficient.

The previous draft assumed the execution contract had already been saved to an exact repository version and independently checked. That is a prerequisite for this particular publisher design, but it is not established by the current first work unit. For hand-fed work, a person may arrange an independently checked fixed copy. For true self-preparation, the preceding publication work must be designed and built. Whether these steps should be combined or split needs a new small-work assessment. No Founder approval is requested for the unexplained phrase “independently landed contract.”
## Candidate behavior to finish designing

1. Record an intent with a stable work identity before an external create. Recover a lost response by searching that exact marker within the intended repository or Project. Zero matches may permit a retry after reconciliation; more than one match is a conflict. Never blindly create again.
2. Retrieve the exact saved version of the instructions and execution contract. Compare their identities, contents, fingerprints, dependencies and assessment inputs with the authoritative preparation records. Specify the mapping between human task text and canonical contract data.
3. Create or find one Issue, attach it to the intended Project, attach the assessment receipt, and set priority. Read each change back against its stable Issue and Project identities. The Issue number, Issue identity and Project entry identity are different values.
4. Immediately before making work available, check whether the relevant requirement, design, decisions, proof plan or task text changed since assessment. This is what the old phrase “upstream references” meant. Check only those known versions or change signals; do not repeatedly search all historical work. A change holds this item until it is reassessed.
5. Mark it READY only after those checks and release authorization succeed, then read it back. This order limits the chance that the scheduler sees unfinished work. The scheduler must independently recheck validity and authorization when it actually releases a worker; the label and its timestamp do not prove either.

The precise storage fields, change signals, retry rule, permission owner and readback interface remain design work. Do not hand this text to an implementer as if those choices were settled. The publisher must not start a worker.

## Reader defect found by independent review

The present Project query asks for the first 50 entries, not the 50 most relevant tasks, and has no page continuation. The current reader can mistake that partial response for a complete Project. The present contract read uses the default repository version, ignores a proposed pinned version, and does not check the assessment identity. These are genuine gaps, not completed prerequisites.

For publication of one item, look up that Issue and its Project entry directly. For scheduling, design a complete bounded view of eligible work, using a change feed or targeted query if the provider supports it; if a response is incomplete, hold instead of declaring it complete. Avoid a full history scan for each release. A separate reader change may be the smallest sensible work unit.

## Role assignment and review

Use **PRODUCER**, **VERIFIER**, **REVIEWER** and **CLOSURE** for responsibilities. Any model may fill a role and users may rename or extend roles. One authoritative role assignment source must be supplied to all consumers at launch and whenever it changes through a documented bridge interface; cognition receives deterministic role, capability, identity and relevant state information rather than guessing. The interface, update delivery, failure behavior, and treatment of a running assignment change need a separate design. Never hardcode model names in this publisher.

The PRODUCER works in an isolated temporary directory. A separate REVIEWER instance checks its exact candidate for intent, design, code quality, duplicated behavior, security and observed outcomes. A distinct CLOSURE instance accepts the independent verdict, lands the accepted content, proves the result and completes the work. The VERIFIER performs the workflow's independent verification where required. Each temporary object has an owner, bound and safe cleanup rule. Distinct instances and duties remain necessary even if one model is assigned to several roles.

## Approval status

The independent review found this packet too broad and underspecified for approval. Next, split or finish the fixed-instructions publication, the narrow live publisher and the reader/authorization work; identify each authoritative input and owner; assess the exact revised work units with Agent Ready. The Founder has not approved this first design or authorized its release.
