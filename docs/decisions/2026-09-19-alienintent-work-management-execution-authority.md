# FD-01 — Work Management and Execution authority boundary

Date: 2026-09-19. Status: **Founder decision — binding**.
Source: direct Founder instruction in this session. Scope: canonical design contracts only; no Python implementation or operational cutover.

## Founder decision (verbatim)

1. The configured external Work Management Provider is canonical for product/work-management state, including:
   - CAPTURE
   - SPECIFY
   - PLAN
   - TASKS
   - READY
   - prioritization
   - product ownership/business context

2. AlienIntent becomes canonical for execution-control state once a READY BIU is explicitly released for execution, including:
   - execution authorization
   - IMPLEMENT
   - VERIFY
   - REVIEW
   - ACCEPT
   - closure
   - DONE
   - invocation/worker/retry/recovery state
   - Engineering Trajectory
   - Quality Evidence
   - execution capabilities and cost/routing evidence

3. The explicit release of a READY BIU is the authority boundary between the Work Management bounded context and the AlienIntent Execution bounded context.

4. AlienIntent may project execution state back into the external work management system so the user sees one coherent lifecycle. Those downstream fields are projections of AlienIntent state, not a second execution authority.

5. AlienIntent may import upstream Work Items through the Work Management port/ACL, but the imported representation does not become canonical product-backlog state.

6. This ownership split is architectural, not configurable. Individual vendors and lifecycle mappings remain configurable through adapters.

## Supersession and limits

This resolves FD-01 by rejecting the earlier whole-lifecycle alternatives and recommendation in the gate packet at commit 7b16e0ba1acc2a20b959476bbac0a36f0342d22d. Neither AlienIntent-owned canonical product backlog nor a configurable ownership switch is adopted. That earlier proposal remains historical Git evidence, not current authority.

Architecture Authority §10 remains in force: release may be issued by an authorized human when automatic release is OFF or explicitly generated under an authorized policy when ON. Explicit release is an attributable boundary event/command, not a new mandatory-human-only rule. READY by itself does not release work.

The ownership decision is approved. FD-02–FD-05 are now binding in [the related Founder decision record](2026-09-19-pre-python-gate-founder-decisions-fd02-fd06.md); FD-06 remains blocked pending EOS normalization. Detailed handoff, conflict, projection and transaction mechanisms remain subject to contract completion and the gate. The Node bootstrap remains unchanged operational authority until an independently approved migration/cutover. Its current external-Project execution authority is a protected bootstrap mechanism, not the canonical target ownership model.

## Refined contract and verification pointers

- [Domain ownership](../architecture/pre-python-gate/domain-model.md)
- [Release and lifecycle](../architecture/pre-python-gate/work-and-release.md)
- [Work Management port/ACL](../architecture/pre-python-gate/hexagonal-contracts.md)
- [Ingress and projection events](../architecture/pre-python-gate/event-ingress.md)
- [Persistence and evidence](../architecture/pre-python-gate/persistence-and-evidence.md)
- [Control Plane](../architecture/pre-python-gate/control-plane.md)
- [Conformance and migration](../architecture/pre-python-gate/conformance-and-sovereignty.md)
- [PG-17 assessed revision BIU](../work-units/pre-python-gate/PG-17.md)
