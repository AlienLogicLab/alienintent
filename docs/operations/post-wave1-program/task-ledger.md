# Post-Wave-1 program — task ledger

Human-readable projection of `program-state.json`. The JSON is authoritative; this file exists so
the program can be read without running anything. Regenerate the table from
`director_cli.py status` rather than editing task rows by hand.

Program task states — `PLANNED READY RUNNING REVIEW REPAIR BLOCKED FOUNDER_DECISION_REQUIRED DONE
SUPERSEDED` — are deliberately disjoint from AlienIntent BIU lifecycle states. A row here never
describes a BIU's lifecycle.

Regenerated from the authoritative JSON during 2026-09-22 recovery; historical
review notes remain observations, not current release authority.

## Ledger

| Task | Ph | Status | Risk | Actor | Review | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| FACT-ARCLOSE-001 | F1 | BLOCKED | HIGH | claude-bootstrap-coordinator | R2 ACCEPT (codex gpt-6-astra, fresh, read-only) | Agent Ready publication/provenance closure: independent review of 64725f9, repair, publish prerequisite + UL, Issue #1 status |
| FACT-BACKLOG-003 | F2 | DONE | LOW | deterministic | PASS (read-only gh inventory) | GitHub Project #1 inventory: 10 Wave 2 requirement issues at CAPTURE (P0: 051/053/056; P1: 011-016, 039); Wave 1 SF-REQ issues remain at TASKS with PY BIUs DONE |
| FACT-BIU-007 | F5 | DONE | HIGH | claude-bootstrap-coordinator | ACCEPT preserved; Codex ACCEPT-only closure DONE; live Project DONE; Issue closed under SWF-31; exact-merge CI success; closure resource REMOVED | WO-220101 (S0): allocation decision + execution packet + work-unit doc; fresh native Agent Ready assessment; Project issue; release ask |
| FACT-DV-005 | F4 | DONE | HIGH | fresh-reviewer | R4 REPAIR_REQUIRED (codex fresh): DV-16/19 material, DV-17/18 advisory — PARKED as planning evidence per Founder direction 2026-09-22; S0 confirmed unchanged in all rounds | Independent Design Verification of the Wave 2 re-SPECIFY (A+B) and of the Founder decision-bundle classification |
| FACT-RECON-002 | F2 | DONE | HIGH | codex-fresh | coordinator cross-check: consistent with deterministic stale set; accepted as input to re-SPECIFY | Wave 2 reconciliation delta: SF-REQ-011/013/015/039 Phase 8/9 artifacts vs 2026-09-22 amendments; S0 impact |
| FACT-SELECT-006 | F5 | DONE | MEDIUM | deterministic | PASS (plan graph read; S0 is the dependency-free root every chain needs) | Founder redirect 2026-09-22: incremental Wave 1 execution model; select next bounded unit deterministically (target SF-REQ-053 P0; chain S0→S1→S2→C1; next BIU WO-220101) |
| FACT-SPECIFY-004A | F3 | DONE | HIGH | codex-fresh | Director verification: 5/5 checkers PASS, pytest 161; independent DV pending (FACT-DV-005); landed on main as planning evidence (not verified as a whole design) | Re-SPECIFY SF-REQ-011/013 + contracts + shared_contracts + DAG predicates (session A) |
| FACT-SPECIFY-004B | F3 | DONE | HIGH | codex-fresh | Director verification: 5/5 checkers PASS, pytest 161; independent DV pending (FACT-DV-005); landed on main as planning evidence (not verified as a whole design) | Re-SPECIFY SF-REQ-015/039 + contracts + U9/U10 + S0 reference refresh (session B) |
| POSTW1-AGENTREADY-004 | 4 | DONE | HIGH | codex-fresh | PASS | Agent-Ready Outcome Completeness Audit |
| POSTW1-BIU-012 | 12 | DONE | HIGH | codex-fresh | PASS | Wave 2 BIU Decomposition |
| POSTW1-BOOTSTRAP-006 | 6 | DONE | HIGH | codex-fresh | PASS | Bootstrap Retirement / Transition Audit |
| POSTW1-BRIDGE-000 | 0 | DONE | MEDIUM | claude-bootstrap-coordinator | PASS | Bootstrap proof: Director-to-coordinator direct message with correlated reply |
| POSTW1-DECIDE-002A | 2 | DONE | HIGH | founder | DECIDED | Founder judgment: accept ownership_gaps=0, and LRN-018 disposition |
| POSTW1-DECIDE-004A | 4 | DONE | HIGH | founder | RESOLVED | Founder: Agent-Ready implementation/schema/CLI owner (G1) and serialization contract owner (G2) |
| POSTW1-DECIDE-005A | 5 | DONE | HIGH | founder | RESOLVED | Founder: amend SF-REQ-013 to own the split/replan transaction (SPLIT-G1) |
| POSTW1-DECIDE-006A | 6 | FOUNDER_DECISION_REQUIRED | HIGH | founder | PARTIALLY_RESOLVED | Founder: 6 NEEDS_DECISION mechanisms plus the PRODUCER-on-Claude reversion |
| POSTW1-DECIDE-007A | 7 | FOUNDER_DECISION_REQUIRED | HIGH | founder | PARTIALLY_RESOLVED | Founder: five Phase 7 amendment recommendations; LRN-022/LRN-023 ownership |
| POSTW1-DECIDE-008A | 8 | FOUNDER_DECISION_REQUIRED | HIGH | founder | PARTIALLY_RESOLVED | Founder: ratify SF-REQ-056, authored in Phase 8 from an id defined nowhere |
| POSTW1-DECIDE-010A | 10 | FOUNDER_DECISION_REQUIRED | HIGH | founder | PARTIALLY_RESOLVED | Founder: five design authority gaps surfaced by verification |
| POSTW1-DECIDE-013A | 13 | FOUNDER_DECISION_REQUIRED | HIGH | founder | PARTIALLY_RESOLVED | Founder: clarification AR13-CQ-001 — authorized allocator and retained execution packet for WO-220101 |
| POSTW1-DESIGN-009 | 9 | DONE | HIGH | codex-fresh | VERIFIED | Wave 2 Design Contracts |
| POSTW1-GAPTRAP-003 | 3 | DONE | MEDIUM | codex-fresh | PASS | Gap Trap Graduation Audit |
| POSTW1-LEARN-002 | 2 | DONE | MEDIUM | codex-fresh | PASS | Wave 1 Learning Consolidation |
| POSTW1-PACKET-014 | 14 | DONE | HIGH | codex-fresh | ACCURACY_CHECKED_AND_REPAIRED | Founder Approval Packet and Final Report |
| POSTW1-PLAN-011 | 11 | DONE | HIGH | codex-fresh | PASS | Wave 2 PLAN / Dependency DAG |
| POSTW1-READY-013 | 13 | DONE | HIGH | codex-fresh | PASS | Agent-Ready Assessment of Wave 2 BIUs |
| POSTW1-RETRO-007 | 7 | DONE | HIGH | codex-fresh | PASS | Final Wave 1 Retrospective + Architecture Reconciliation |
| POSTW1-REVIEW-001 | 1R | DONE | HIGH | claude-bootstrap-coordinator | PASS_WITH_QUALIFICATIONS | Independent Wave 1 Closure/Evidence Review |
| POSTW1-SMOKE-000 | 0 | DONE | LOW | codex-fresh | PASS | Bootstrap proof: launch and capture a fresh Codex session |
| POSTW1-SPECIFY-008 | 8 | DONE | MEDIUM | codex-fresh | PASS | Wave 2 Requirement Inventory + SPECIFY |
| POSTW1-SPLIT-005 | 5 | DONE | HIGH | codex-fresh | PASS | BIU Split / Replan Process Design |
| POSTW1-VERIFY-010 | 10 | DONE | HIGH | fresh-independent-reviewer | VERIFIED | Wave 2 Design Verification |
| FACT-S1-ADMISSION-008 | F5 | BLOCKED | HIGH | program-director | INDEPENDENT REVIEW: enforcement gap upheld; premature Founder gate corrected under AA42/SWF01 | WO-220102 / S1 admission: bounded critical-bootstrap duration repair before execution packet |

## Reading the ledger

- **Review** records whether independent review is *required*, and once complete, its outcome. A
  blank is not a pass.
- A task at `FOUNDER_DECISION_REQUIRED` stops the program: `next_task()` returns `None` while any
  such task exists. That is enforced in `director.py`, not left to discipline.
- `DONE` here means the program task is complete and its artifacts are recorded. It carries no
  AlienIntent lifecycle meaning whatsoever.

## Actor assignment, and why it is not always the most capable model

Assignment answers "who is cheapest to succeed first-pass", with two overrides: deterministic
tooling wins wherever it can settle the question, and high-risk work does not go to its own author.

`POSTW1-LEARN-002` is the clearest case. Consolidating Wave 1's lessons could go to the resident
coordinator, which has the most context — and that is exactly the reason it does not. A wave's
participant writing the wave's lessons produces a story that flatters the telling. It is routed to
a fresh Codex session, with review required.

Conversely `POSTW1-BRIDGE-000` had to go to the coordinator: the question turned on what the
bootstrap mechanisms actually do under live operation, which the durable artifacts describe but do
not convey.

## Provenance

- Program definition: `docs/operations/alienintent-post-wave1-to-wave2-program-plan.md`
- Routing policy: `docs/operations/alienintent-local-program-director-intelligent-routing.md`
- Role and boundaries: `docs/operations/post-wave1-program/program-director.md`
- Bootstrap proofs: `docs/operations/post-wave1-program/reports/bootstrap-proofs.md`
