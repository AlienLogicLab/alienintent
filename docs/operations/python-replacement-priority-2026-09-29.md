# Python replacement: remaining-work handoff

Date: 2026-09-29. Purpose: organize existing requirements and BIUs for the first
milestone, **a Python implementation capable of replacing the AlienIntent Node
factory**, followed by a separately verified single-writer cutover. This is a
priority overlay, not a new lifecycle decision or a claim that any live proof is
complete. The [canonical v2 design](../architecture/alienintent-factory-v2-formal-design.md)
controls implementation. Reuse existing Python code only after checking it
against that design; do not port the Node state machine or expand its ledger.
The Founder's current plan is to shut down the Node factory for offline Python
work. That is an intentional **pause**, distinct from claiming that replacement
or retirement has passed its live acceptance gates.

## What is known now

- Remote `main` was `c74baf2699c5614b084d7c354290e0a5e148bf27` at inventory.
  The REST Issues API identified the open Issues below. The Project GraphQL API
  returned a rate-limit error, so lanes beyond the exact recent runtime readbacks
  are **unverified** and must be refreshed before release decisions.
- At the last local runtime readback, #147 VERIFIER and #150 PRODUCER held active
  claims. #149 had no active claim and its Founder hold had been removed after
  [the controlled-live-closure grant](https://github.com/AlienLogicLab/alienintent/issues/149#issuecomment-5888786913),
  but ACCEPT-to-DONE was not yet read back. #125 has a retained Producer A
  `FOUNDER_EXCEPTION` and a parked candidate. These are custody facts for a safe
  shutdown, not tickets to hand-clear or silently abandon.
- [The existing cutover decision](../decisions/2026-09-27-python-only-alienintent-factory-cutover.md)
  requires more than stopping `alienintent.service`: runtime, supervision,
  admission, observation, liveness, attention, checkpoint, mailbox, launch
  commands and external bootstrap duties must have proven Python ownership.
  The [cutover inventory audit](../evidence/python-only-cutover-node-inventory-audit-20260927.md)
  and its [correction](../evidence/2026-09-27-python-cutover-steps-1-2-4-5-disposition.md)
  are the starting custody maps.

## Priority and dependencies: one BIU in process

Preparation may organize several packets, but execution WIP is **one BIU**.
Do not treat multiple role claims for one BIU, or the absence of a Node claim,
as proof that the Project and external effects are settled. Existing Issue
priorities and the [Wave 2 dependency DAG](../evidence/wave2-dependency-dag.json)
remain binding; this table orders the *replacement milestone*, with its
prerequisites before its live gates.

| Order | Existing work | Completion needed for this milestone |
|---|---|---|
| 0 — preserve custody before shutdown | #149 closure; active #147 and #150; #125 parked candidate; #138 unknown-outcome resource | Stop admissions, allow or explicitly fence owned work, record exact claims/results/effects and a recoverable checkpoint. Do not assert DONE or kill active workers from Project status alone. Carry unresolved items into the Python backlog with stable identities. |
| 1 — v2 durable kernel | PY-02/03/04 as prior capability evidence; SF-REQ-001/002/003/004/008/009 (#3–6, #10–11); #146 supply invariant; #147/SF-REQ-057 | Implement one SQLite WAL canonical state, legal transitions, indexed current projection, priority/dependency/WIP=1 scheduler, READY preparation, durable requirement intake, typed blockers, idempotent effects, verified checkpoint/segment retention and crash recovery. No routine historical replay or unbounded resource growth. #147's current candidate must be assessed before reuse. |
| 2 — offline full lifecycle | PY-06/07 and WO-220401/402/403, then #121/WO-220404; #118/WO-220307 | Demonstrate independent Producer→Verifier→ACCEPT→DONE, candidate custody, bounded repair, decisions, no-silent-idle, restart and failure handling with provider-free fixtures. Use the formal v2 safety/liveness properties S1–S12 and L1–L5 as acceptance, with targeted antipattern/resource review. |
| 3 — Python external boundaries | PY-05/08/09/09B prior capability evidence; B0/WO-220501, E1/WO-220502, E2/WO-220503; #127/B4; #130/R1; #129/B7 | Bind authenticated GitHub ingress/projection, operator commands, profile/worker custody, effect readback, bounded Director episode/mailbox, install/start and reversible one-writer migration to the v2 kernel. The external Python bootstrap scripts need per-component successor or retained-custody decisions. |
| 4 — live replacement proofs after Python starts | #124/B1, #125/B2, #126/B3, #128/B5; #131/R2; #134/B8; #132/B6 | Use one named real profile and one writer to prove trajectory, liveness, release admission, attention, mailbox and reversible sovereignty. #125's current two-cycle packet relies on a live real lane; adapt/reassess its target and schedule for Python rather than pretending the offline build satisfied it. Preserve its parked candidate as evidence, not an accepted result. |
| 5 — retire old duties | #135/R3, #136/R4, #137/R5, R6/WO-220606, #139/R7; R8/WO-220608; B9/WO-220512; R9/WO-220609 | Read back replacements and complete the gates before removing Node/bootstrap authority, compatibility alias or Director bootstrap role. R8, B9 and R9 have candidate BIUs but no materialized Issue in the current inventory; materialize and assess them when their prerequisites are ready. |

The ordered proof chain is B2→R3, B1→R4, B3→R6, R3+R4+B8→R5,
B1+B2+B3+B5+E2→B6, and R3+R4+R5+R6+B6→R7. R8 depends on B7;
R9 depends on R2, B8 and B9. These are the named gates in the existing DAG,
not permission to skip its other prerequisites.

## Requirement disposition for prioritization

- **Must work for the first Python replacement:** P0 factory execution and
  custody requirements #3–16 (P5 polish portions of #13/#15 may remain later),
  #62/SF-REQ-051 design contracts, #64/SF-REQ-053 control plane,
  #67/SF-REQ-056 liveness, #147/SF-REQ-057 intake, and the safety-critical
  P1/P2 extents needed by the named BIUs: #17–23, #28–34, #59–61.
  This is an implementation/acceptance mapping, not a blanket re-release of
  already completed predecessor BIUs.
- **Preparation or later product expansion:** #24–27 (external artifact and
  prototype intake), #37–39 (creation tools), #63/#66 (convergence/proposal
  intake), #35–36 (metrics/replay), #40–49 (provider economics, trajectory,
  learning and dashboard) remain open requirements. Preserve them in the
  backlog; include an extent in this milestone only where a named gate or
  binding v2 safety property actually depends on it. SF-REQ-029/#44's observer
  replacement duty is such an extent; its Node-ledger implementation split
  #143→#144→#145 needs reassessment against the Python canonical ledger.
- **Node-only maintenance after planned shutdown:** #133 and #149–152 are
  custody/closure records or old-runtime defects. Preserve accepted fixes and
  unresolved evidence; do not make further Node redesign a prerequisite to v2.
  #146 and #147 express product invariants and carry forward into Python.

## Gates that must remain visible

1. **Offline complete** means a fresh Python profile can consume a prioritized
   READY backlog through independently verified DONE in a repeatable local
   fixture, recover from restart, and stay within declared disk/memory/worktree
   budgets. It does **not** mean Node is retired or live effects are proved.
2. **Cutover ready** means exact active-work/effect reconciliation, verified
   checkpoint and rollback, `doctor` pass, operational predecessor proofs,
   installation command inventory and one-writer authority. Do not run Node and
   Python as writers for the same profile.
3. **Node retired** means the live Python readbacks pass, #139/R7 plus R8/R9/B9
   and predecessor retirement gates close, no AlienIntent Node launcher or
   required Node alias remains, and rollback custody is retained. Unrelated
   developer tools using Node are outside this milestone.

The prior cutover audit identifies open decisions around the temporary
PRODUCER-on-Claude provider exception, general attention activation and
resident coordinator tenure. Resolve each against current Founder instructions
before its dependent live gate. The Windows notification exclusion and
expired PY-04 mutation gate are already disposed in the cited audit correction;
do not re-open them without new evidence.

## Next working packet

Start with the **v2 durable kernel / scheduler** in row 1 as one bounded BIU,
using [the work-packet template](../templates/work-packet.md). Pin the exact
repository baseline and the existing PY-02/03/04 interfaces. Record object
ownership, retention, high-water behavior, crash cleanup, measured admission
cost as history grows and an independent antipattern/slop review. Then perform
row 2 offline lifecycle proof. Do not spend model or test budget on all
historical Node suites to validate a Python-only slice.
