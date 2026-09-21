# Wave 1 decomposition amendment — the live transport prerequisite (SWF-33)

Date: 2026-09-21. Status: **Founder decision — binding**. Amends the PY-02…PY-10 decomposition
approved by [SWF-08–11](2026-09-20-wave1-plan-approval-d1-d2.md).
Source: direct Founder instruction, on the evidence of PY-10's 2026-09-21 Agent-Ready reassessment.

## What the evidence said

PY-10's fresh reassessment at baseline `85b6060` returned **`SPLIT_RECOMMENDED`**, rework locality
**`HIGH`**, and named two decomposition defects — not implementation findings:

1. **The first live GitHub transport capability is owned by no Wave 1 BIU.** Installation-token
   acquisition, live repository access, Projects v2 read, fenced projection write, a resident webhook
   ingress bound to the configured host and port, webhook signature handling, live `doctor` transport
   probes, and the sandbox profile composition that binds them — every predecessor deferred these to
   PY-10, and **PY-10's own Scope does not name them either**. Under SWF-20 / SF-REQ-048, unnamed work
   is a verification finding, which leaves an implementer choosing between under-delivering and failing
   REVIEW for scope expansion.
2. **PY-10 as written is one coupled live proof across fourteen criteria with no local iteration
   surface.** A defect surfacing at criterion 11 invalidates the coherent run and forces a full re-seed
   and re-run, with real provider spend each time.

> **Provisioning the sandbox satisfied environmental prerequisites. It did not implement the canonical
> live transport capability required to exercise it.**

That distinction is the whole of the first defect. The sandbox is real, verified and preflight-clean —
and nothing in canonical Python yet knows how to talk to it.

The second defect is supported by this factory's own measured history rather than by intuition:
**no completed Wave 1 implementation BIU has ever been accepted first-pass** — 0 of 7 accepted BIUs,
with rejections ranging 1 to 9 per BIU
([repair-cycle data](../evidence/wave1-repair-cycles.md)). A capstone whose every defect requires a
complete, expensive reseed is the wrong shape when a smaller independently testable boundary can be
established first.

## The decision

**Split. PY-10 is not broadened.**

One bounded preceding Wave 1 BIU — **PY-09B** — owns the minimum missing capability, and PY-10 consumes
an already-proven substrate.

| | Proves |
|---|---|
| **PY-09B** | The sandbox's live GitHub transport and projection substrate works and is independently verifiable. |
| **PY-10** | The complete canonical Python factory executes the approved Wave 1 live proof **using that already-proven substrate**. |

PY-10 remains the Wave 1 capstone. Its acceptance criteria are **not weakened**: only implementation
responsibility now owned by PY-09B is removed, while the obligation to consume and verify the transport
inside the integrated live proof is retained. **The split reduces rework locality without reducing the
total proof obligation.**

### Why `PY-09B`

The repository's existing convention for inserted planning units is a letter suffix on the unit it
follows — Wave **2B** was inserted between Wave 2 and Wave 3 by the same method. `PY-09B` follows PY-09,
precedes PY-10, renumbers nothing, and sorts correctly between them. PY-01…PY-09 are untouched.

### Iteration surface — the second defect

PY-09B must not become another one-shot live run. Its verification is locally repeatable wherever
practical: fixture-backed and deterministic checks for protocol and projection logic, **bounded** live
checks for credentials, installation, ingress and Project access, and proven-red negative controls on
the guards that matter (SWF-24). PY-10 then enters its final live proof with transport defects already
removed from the likely failure surface.

## Authority and scope

This amends Wave 1 planning authority only. **No new Product Requirement is created** — PY-09B carries
requirements SF-REQ-005, SF-REQ-007 and SF-REQ-038, all of which already exist and already own this
capability's semantics. Priority and Wave are inherited, not invented: every Wave 1 BIU is P0/Wave 1.

Neither the earlier `BLOCKED` nor the current `SPLIT_RECOMMENDED` disposition is treated as READY.
PY-10 is released only on a fresh `READY` disposition assessed against the then-current baseline with
PY-09B complete, and only through normal SWF-21 admission.

Nothing in Node/B-DISP changes, no completed BIU is reopened, and no manual proof shortcut is created.

## Follow-on: the isolation standard (SWF-34)

PY-09B's own Agent-Ready assessment then found that the contract as drafted demanded a property GitHub
cannot provide — proof that the sandbox token reaches only Project #2, which `organization_projects`
makes impossible. Resolved by [SWF-34](2026-09-21-sandbox-isolation-standard.md): repository isolation
permission-enforced, Project isolation configuration-enforced, PY-10 AC 16 compensating. No PY-10
acceptance criterion changed.

## Evidence preserved

The Claude reassessment and its provider-failover provenance are retained as the evidence that caused
this amendment: [Agent-Ready provider failover](../evidence/2026-09-21-agent-ready-provider-failover.md)
and `docs/work-units/python/PY-10.assessment.json`. The failover changed the assessment's provenance,
not its semantics — and the non-READY result it produced was honoured exactly as a codex result would
have been. Had the assessment not been re-run, PY-10 would have been released into a contract with an
unowned first-of-kind implementation surface.
