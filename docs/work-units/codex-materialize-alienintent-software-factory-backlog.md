# Codex Work Packet — Materialize the AlienIntent Software Factory Requirements Backlog

## Purpose

Load the Founder-approved software-factory requirements into AlienIntent's authoritative Work Management system without turning them into implementation BIUs prematurely.

## Authoritative input

Use the Founder-approved software-factory plan containing requirements `SF-REQ-001` through `SF-REQ-047`.

Install it into the repository at:

`/mnt/d/Projects/alienintent/docs/product/alienintent-software-factory-plan.md`

if it is not already present there.

## Required outcome

Create Product Issues in:

`AlienLogicLab/alienintent`

for requirements `SF-REQ-001` through `SF-REQ-047`.

Add them to the AlienIntent GitHub Project.

These are Product Requirements / Product Issues, not implementation BIUs.

Do not directly implement them.

## Priority

Preserve each requirement's declared priority.

Materialize in priority order:
1. P0
2. P1
3. P2
4. P3
5. P4
6. P5

Within a priority class, preserve numerical requirement order unless an explicit dependency requires otherwise.

## Required Issue content

Each Product Issue must include:
- requirement ID;
- title;
- product requirement statement;
- rationale/intended outcome where present;
- priority;
- known dependencies;
- source product-plan reference;
- explicit marker that this is a Product Requirement, not a BIU;
- statement that implementation decomposition must occur through AlienIntent's planning/BIU process.

Do not invent implementation details.

## Lifecycle placement

Default new Product Requirements to:

`CAPTURE`

Move to `SPECIFY` only when the requirement is already explicit enough under existing authority.

Do not move Product Requirements directly to READY.

Do not create implementation BIUs merely to clear the queue.

## Implementation waves

Record these six waves:
- Wave 1 — continuous factory control loop
- Wave 2 — requirements become normal input
- Wave 2B — frontier creation-tool intake
- Wave 3 — raise factory yield
- Wave 4 — reduce cost
- Wave 5 — learn
- Wave 6 — productize installation/operations

Use existing Project metadata/issue relationships if already supported.

Do not invent a new dependency mechanism merely for this task. If current Work Management cannot express a dependency cleanly, record it in the Issue body and report the limitation.

## Immediate planning cohort

Do not attempt all requirements at once.

The addition of SF-REQ-041 through SF-REQ-047 must not change the current Wave 1 execution priority.

The immediate planning cohort is Wave 1 / P0, specifically the minimum work required for AlienIntent to consume a prioritized READY BIU backlog continuously without human per-BIU triggering.

Prepare those Product Requirements for SPECIFY/PLAN.

Do not implement them in this task.

## Authority

Priority is Founder/Product input.

AlienIntent does not invent or reprioritize product work.

If two READY BIUs later have equal or absent priority, default scheduling is FIFO / next READY.

## Founder decision rule

Do not silently make new product or architecture decisions.

If preparing a requirement for BIU decomposition exposes a real unresolved decision, surface it clearly.

Routine decomposition inside existing authority is delegated.

## Output report

Return:
1. number of Product Issues created;
2. Issue number/title/requirement ID;
3. priority;
4. Project lifecycle state;
5. dependencies recorded;
6. duplicates/conflicts with existing backlog;
7. any requirement that could not be materialized accurately;
8. immediate Wave 1 planning cohort;
9. explicit confirmation that no implementation was performed.

Do not modify FactoryChecks.
Do not start implementation in this task.


## Frontier creation-tool intake sequencing

Requirements SF-REQ-041 through SF-REQ-047 are strategically approved planning work.

Do not allow them to derail Wave 1.

Sequence:
1. complete Wave 1 continuous factory control loop;
2. establish core Requirements IR / Requirements→BIU compilation in Wave 2;
3. then schedule Wave 2B generic Artifact Intake;
4. only then add provider-specific adapters where stable interfaces justify them.

Generic Git/archive/file intake is preferred before vendor-specific integration.

Do not implement UI scraping of Google AI Studio, Codex, Claude, or another provider as a canonical integration.
