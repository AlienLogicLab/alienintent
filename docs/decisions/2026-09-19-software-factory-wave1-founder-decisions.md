# Software-factory Wave 1 — Founder decisions

Date: 2026-09-19. Status: **Founder decision — binding**.
Source: direct Founder instruction resolving the Wave 1 preparation findings in [the Wave 1 planning cohort note](../work-units/sf-wave1-planning-cohort.md).
Scope: product-plan interpretation, Work Management representation and documentation. This record authorizes Wave 1 PLAN only. It does not authorize implementation.

## SWF-01 — Wave 1 implementation target

Wave 1 is implemented in the canonical Python AlienIntent architecture. Wave 1 capabilities are **not** implemented in the frozen Node bootstrap.

The Node bootstrap remains the temporary control plane that executes the Python implementation BIUs until Python Sovereignty (Architecture Authority §43). Node may change only under Architecture Authority §42, for critical bootstrap repairs needed to keep that temporary control plane operational.

In [the software-factory plan](alienintent-software-factory-plan.md), "existing execution machinery" means "the current Node bootstrap may execute the BIUs that build Wave 1." It does not mean "implement Wave 1 factory capabilities in Node."

## SWF-02 — Durable documents

The authoritative plan is `docs/decisions/alienintent-software-factory-plan.md`. The materialization packet is `docs/work-units/codex-materialize-alienintent-software-factory-backlog.md`. The Wave 1 planning cohort note is `docs/work-units/sf-wave1-planning-cohort.md`.

No byte-identical duplicate authority is maintained. `docs/product/alienintent-software-factory-plan.md` is a pointer only.

## SWF-03 — Project Priority and Wave fields

The GitHub Project carries a single-select **Priority** field (P0–P5), populated from the Founder-declared priority labels. Priority remains Founder/Product input; AlienIntent never invents it. The labels are retained.

A **Wave** field carries roadmap/grouping metadata. Wave is not execution priority. Dependencies continue to use GitHub's native blocked-by relationships; no other dependency mechanism is introduced.

## SWF-04 — SF-REQ-037 installer

SF-REQ-037 stays in CAPTURE / Wave 6. "P0 minimum / P5 polish" means:

- installability is an architectural constraint from the beginning;
- the installer product itself is not a Wave 1 implementation requirement.

Earlier bootstrap/configuration capabilities are implemented only when another authorized BIU requires them.

## SWF-05 — SF-REQ-006 and SF-REQ-035

The approved software-factory plan gives sufficient product authority for SPECIFY/PLAN of HumanDecisionRequired, the Decision Inbox, affected-work blocking, independent-work continuation, durable decision recording and automatic unblocking/resumption. Missing architecture records do not constitute a Founder decision. Planning surfaces only genuinely consequential unresolved authority, security or product decisions.

## SWF-06 — FD-06

FD-06 is **resolved**. EOS v1.0 normalization and AlienIntent conformance are complete (EOS `DR-000007`; [EOS conformance manifest](../architecture/pre-python-gate/eos-conformance-manifest.md)). Stale references to FD-06 as blocked are corrected as documentation normalization only, which is not a Wave 1 prerequisite.

## SWF-07 — Next step

Wave 1 continues from SPECIFY into PLAN for SF-REQ-001–010, SF-REQ-034 (P0 minimum), SF-REQ-035 and SF-REQ-038. The objective is the shortest coherent path to continuous consumption of a prioritized READY backlog, subject to priority, dependency eligibility, WIP, execution capacity and real human-authority blockers. The deliverable is a proposed dependency DAG and BIU decomposition for review. Nothing is implemented.
