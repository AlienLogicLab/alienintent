# Post-Wave-1 program — task ledger

Human-readable projection of `program-state.json`. The JSON is authoritative; this file exists so
the program can be read without running anything. Regenerate the table from
`director_cli.py status` rather than editing task rows by hand.

Program task states — `PLANNED READY RUNNING REVIEW REPAIR BLOCKED FOUNDER_DECISION_REQUIRED DONE
SUPERSEDED` — are deliberately disjoint from AlienIntent BIU lifecycle states. A row here never
describes a BIU's lifecycle.

## Ledger

| Task | Ph | Status | Risk | Actor | Review | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| POSTW1-SMOKE-000 | 0 | DONE | LOW | codex-fresh | PASS | Bootstrap proof: fresh Codex session launched and captured |
| POSTW1-BRIDGE-000 | 0 | DONE | MEDIUM | claude-bootstrap-coordinator | PASS | Bootstrap proof: Director→coordinator message with correlated reply |
| POSTW1-REVIEW-001 | 1R | DONE | HIGH | claude-bootstrap-coordinator | PASS_WITH_QUALIFICATIONS | Independent review of Codex's Phase 0+1 closure/evidence pass |
| POSTW1-LEARN-002 | 2 | READY | MEDIUM | codex-fresh | required | Wave 1 Learning Consolidation — queued, not dispatched |
| POSTW1-BOOTSTRAP-006 | 6 | PLANNED | HIGH | codex-fresh | required | Bootstrap retirement review |

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
