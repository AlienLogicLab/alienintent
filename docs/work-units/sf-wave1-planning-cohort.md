# Wave 1 planning cohort — SPECIFY preparation

Date: 2026-09-19. Status: **planning preparation only** — no BIUs, no implementation. Findings resolved by [Wave 1 Founder decisions](../decisions/2026-09-19-software-factory-wave1-founder-decisions.md); PLAN proposal in [sf-wave1-plan.md](sf-wave1-plan.md).
Source: `docs/decisions/alienintent-software-factory-plan.md` (Founder-approved, authoritative); packet `docs/work-units/codex-materialize-alienintent-software-factory-backlog.md`.

Cohort (Project Status = PLAN since 2026-09-19; was SPECIFY): SF-REQ-001–010 (#3–#12), SF-REQ-034 P0 minimum (#13), SF-REQ-035 (#14), SF-REQ-038 (#16).
Goal: the minimum needed for AlienIntent to consume a prioritized READY BIU backlog continuously without human per-BIU triggering.

## Founder decision — resolved (SWF-01)

Where Wave 1 is implemented was the open question. The plan's "existing execution machinery" (Wave 1 outcome) appeared to conflict with Architecture Authority §42 ("Node is frozen except for critical bootstrap fixes"). **Resolved:** Wave 1 is implemented in canonical Python. The Node bootstrap only executes the BIUs that build it. Node changes are limited to §42 critical bootstrap repairs.

## Authority map

Abbreviations:
- AA: `docs/architecture/alienintent-architecture-authority-2026-09-19.md`
- FD01: `docs/decisions/2026-09-19-alienintent-work-management-execution-authority.md`
- FD26: `docs/decisions/2026-09-19-pre-python-gate-founder-decisions-fd02-fd06.md`
- `PG/` = `docs/architecture/pre-python-gate/`

The PG documents are labelled candidate design, but `PG/gate-reclassification.md` classifies them as category A/B inputs.

| Req | Existing authority | Gaps to specify |
|---|---|---|
| 001 Continuous execution | AA §10, FD26 FD-03 (auto-release default ON), PG/work-and-release, PG/event-ingress (no backlog polling) | Loop continuation and stop conditions; keeping the READY candidate set current without polling |
| 002 READY scheduling | Plan §READY scheduling; FD01 item 1 (WM owns priority); PG/scheduling-and-recovery | Priority representation via the WM ACL; FIFO definition; upstream vs. internal dependency reading |
| 003 Solve for N | AA §1, §19; PG/scheduling-and-recovery; PG/configuration-and-installation | Independence/safe-parallelism policy; whether verifier invocations count toward the mutating limit |
| 004 Rolling refill | Plan; PG/scheduling-and-recovery (successor/reservation rules) | Refill trigger event; multi-instance refill races |
| 005 WM port | FD01; PG/hexagonal-contracts (WorkManagement port, ACLs); AA §8, §29; PG/domain-model | Port signatures; priority/dependency read ops; GitHub Projects field mapping |
| 006 HumanDecisionRequired | **Plan only**; adjacent: AA §45, PG/work-and-release, FD26 FD-05 | Event schema; "affected work" propagation; domain-model placement |
| 007 Candidate custody | AA §5, §7; PG/domain-model (Candidate); PG/capabilities-and-assurance; PG/persistence-and-evidence | Retrievable custody location; VERIFY-entry guard; N-repo identity |
| 008 Crash safety | FD26 FD-05; AA §16, §18; PG/event-ingress; PG/persistence-and-evidence | Inbox/outbox/effect-intent schema; fencing; store conformance scenarios |
| 009 Deterministic kernel | Plan; PG/control-plane; FD26 FD-03; AA §21, §22, §39 | Check proving no LLM mutates canonical state; budget reservation/settlement contract |
| 010 BIU contract | PG/work-and-release (BIU record/guards); AA §13; FD26 FD-03 | Machine-readable schema/version; non-goals, custody and requirement-link fields; WM serialization |
| 034 Control Plane (P0 min) | AA §36, §37 (CLI minimum); PG/control-plane | Which operations constitute the "P0 minimum" is undefined |
| 035 Decision Inbox | **Plan only**; adjacent: PG/control-plane, PG/persistence-and-evidence | Persistence class; decision-submit command; unblock rule; notification adapter port |
| 038 Doctor | AA §35, §36, §38; PG/control-plane; PG/configuration-and-installation; PG/hexagonal-contracts | Provider/transport probes; doctor output contract; gating of autonomous start |

## Notes

- SF-REQ-037 (installer): **resolved (SWF-04).** It stays in CAPTURE / Wave 6. "P0 minimum" means installability is an architectural constraint from the beginning; the installer product is not Wave 1 work.
- SF-REQ-006 / SF-REQ-035 have no separate architecture records. **Resolved (SWF-05):** the plan is sufficient product authority, and architecture work designs them during PLAN.
- FD-06: **resolved (SWF-06).** Stale "blocked" wording is corrected in the decision and pre-python-gate records.
