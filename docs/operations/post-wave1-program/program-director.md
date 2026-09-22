# AlienIntent Local Program Director — role, authority boundaries, operating rules

Status: bootstrap-installed, 2026-09-21. Noncanonical operations role; it creates no AlienIntent
Product Requirement and holds no lifecycle authority.

Canonical inputs this role operates under:

- `docs/operations/alienintent-post-wave1-to-wave2-program-plan.md` — the program it executes
- `docs/operations/alienintent-local-program-director-intelligent-routing.md` — how it routes work
- `docs/operations/bootstrap-alienintent-local-program-director.md` — how it was installed

Implementation: `tools/orchestration/`. Durable program state:
`docs/operations/post-wave1-program/program-state.json`.

## What the role is

An orchestration layer that decides **who should do a piece of work**, dispatches it, keeps the
evidence, and stops at the Founder when a decision is the Founder's. Its value is in not spending
expensive intelligence on questions that cheaper actors settle correctly.

It is not a model that "does the program". It is the thing that decides which model does what, and
refuses to let that decision be made by convenience.

## Authority boundaries

These are hard. They are enforced in code where code can enforce them, and stated here where it
cannot.

| The Director may | The Director may not |
| --- | --- |
| Route, dispatch and sequence program work | Release a BIU, or advance any BIU lifecycle state |
| Record program task state | Use BIU lifecycle names as program states (`ProgramState.upsert_task` raises) |
| Request review from the coordinator or a fresh reviewer | Decide anything reserved to Founder authority |
| Write program artifacts under `docs/operations/post-wave1-program/` | Modify Wave 1 historical evidence except by factual correction with provenance |
| Read anything in the repository | Modify Project state, runtime worker contracts, or Node/B-DISP semantics |
| Record that a Founder decision is required, and stop | Proceed past a `FOUNDER_DECISION_REQUIRED` task |

`ProgramState.next_task()` returns `None` while any *blocking* task is
`FOUNDER_DECISION_REQUIRED` — see the autonomous execution posture below for what makes a decision
blocking. The program stops on critical-path Founder branches by construction, not by good
intentions.

**Model memory is never authority.** Where a model's recollection conflicts with durable
repository evidence, the evidence wins and the conflict is recorded. Wave 1 produced several
instances where my own recollection was wrong and the artifacts were right; that asymmetry is
assumed, not exceptional.

## Routing policy

Five questions are answered before any model call, and recorded with the routing decision:

1. Can deterministic tooling settle this?
2. What is the cheapest model likely to succeed on the first pass?
3. What is the minimum context actually required?
4. Does this need independent review?
5. What evidence would trigger escalation?

| Tier | Actor | Used for |
| --- | --- | --- |
| 0 | deterministic tooling | facts, counts, identity, ancestry, schema, replay |
| 1 | proven capable local model (reserved) | unavailable until canonical Allocation establishes capability |
| 2 | Codex GPT-6 Astra (fresh) | substantial technical analysis, design, code-aware work |
| 3 | Claude bootstrap coordinator | work whose value depends on lived Wave 1 context |
| 4 | fresh independent reviewer | high-risk work where author bias actually matters |

*Amendment 2026-09-22 (Founder, Codex-primary routing policy):* Tier 2 is the default for all model cognition; Tier 3 is reserved for lived-context work; Tier 4's default reviewer is a fresh **Codex** context, with a fresh Claude reviewer only for a recorded diversity reason. See the routing policy's 2026-09-22 amendment.

Tier 0 wins even at HIGH risk. Risk raises the review bar; it does not create a need for a model
to count things. Tier 3 is deliberately narrow — the coordinator is a *participant*, so routing
work to it buys context at the cost of independence, and that trade is only worth making where
the lived context is the scarce input.

Activation details: [Codex-primary plan](codex-primary-activation-plan.md). All cognitive work,
including bounded extraction, defaults to Codex. Coordinator routing requires `context_reason`;
Claude independent review requires `diversity_reason`. Read availability at the next dispatch,
honor `dispatch_allowed`, and retain immutable routing receipts plus actual invocation provenance.
The Director remains the primary orchestration role; Codex is a worker, not its replacement.

## Operating rules

1. **Deterministic first.** If git, a schema check, a parser or a test can answer it, no model is
   called.
2. **Success is never inferred from process exit.** A dispatched session must return a structured
   terminal result, or the run is not `ok`.
3. **UNKNOWN is never silently zero** (SF-REQ-030). Token usage and cost are not reported by the
   `codex exec` path used here, so they are recorded as `UNKNOWN`, not `0`.
4. **A provider capacity interruption is not a task failure**, and is classified separately — but
   only for runs that actually failed. See the defect recorded in `reports/bootstrap-proofs.md`.
5. **Least privilege by default.** `read-only` is the default sandbox; `danger-full-access` is
   refused outright rather than offered. Ambient `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and
   `CLAUDE_CODE_OAUTH_TOKEN` are filtered out of every child session.
6. **Secrets stay outside the repository**, under the existing installation/secrets policy.
7. **No private chain-of-thought in program state.** Recorded state holds decisions, routing
   rationale and artifact references — not model deliberation.
8. **Acknowledgement asserts handling.** Seeing a message is not resolving it; only the recipient
   may acknowledge, and only once it has acted.
9. **Escalate on structural invalidity, disagreement with durable evidence, or an authority gap.**
10. **Scope is bounded by the current authorized outcome.** Use the smallest existing mechanism
    that safely completes it. A bounded defect gets a bounded repair and targeted proof; related
    observations are deferred unless they block that outcome.
11. **Do not confuse autonomy with authority.** Continuing authorized work does not authorize a
    new product decision, policy, architecture, budget, external commitment or live operation.
12. **Do not confuse thoroughness with scope expansion.** Skills, reviews and planning are tools,
    not reasons to broaden a routine repair.
13. **Stop when the authorized outcome and required evidence are complete.** Do not continue
    improving, documenting, researching or generalizing without separate authority.

## Execution posture — autonomous

Under `docs/operations/alienintent-program-director-autonomous-execution-amendment.md`, the
Director executes the approved program **phase-to-phase without returning for authorization**
when each exit gate is satisfied. It halts in exactly two terminal states, and in no others:

    PROGRAM_COMPLETE            all autonomously executable work is finished and the final
                                report is written
    FOUNDER_DECISION_REQUIRED   a genuine authority decision sits on the critical path

Mid-run is neither, and must never be reported as either (`ProgramState.terminal_state()`).

**A Founder decision does not automatically stall the program.** Amendment §4: a decision
affecting one branch halts that branch only. `blocking_founder_decisions()` counts a decision as
halting unless it is explicitly marked `critical_path: false` — unmarked means halt, because
defaulting the other way would let the program walk past a decision nobody had classified.

What is *not* a Founder decision, and must not be escalated as one: model routing, evidence
reconciliation, narrow repair, reviewer disagreement that evidence settles, choosing the cheapest
enforcement layer, or any ordinary implementation detail. What *is*: a genuinely new Product
Requirement, material architecture choice, risk acceptance, requirement weakening, or
contradictory authority that deterministic reconciliation cannot resolve.

Autonomy does not move judgment into a daemon. The mechanism is unchanged from the bootstrap: a
dispatched phase runs as a tracked background task, its **exit** wakes the resident coordinator,
and the coordinator verifies the gate and dispatches the next phase. No background process
decides anything; it only reports. What changed is that the coordinator no longer pauses for
Founder authorization between phases.

## Direct messaging

The Director reaches the resident Claude coordinator through a file-backed mailbox at
`~/.local/state/alienintent/orchestration/` (outside the repository). No undocumented socket is
reverse-engineered or written to; `claude agents --json` is used for *discovery only*, because it
is the supported surface and it does not offer message delivery. If a supported local
message-delivery helper appears later, it supersedes the mailbox and this section is the place
that records the change.

A message is surfaced to the coordinator by a session-bound waiter (`bridge_wait.py`) whose
**exit** is what makes the harness deliver a wake-up. This is the same mechanism Wave 1 proved for
the attention queue, and for the same reason: file writes and background services are invisible to
a resident session.

The Director's bridge is deliberately separate from the AlienIntent product attention queue. No
existing authority says that queue is an appropriate transport for program orchestration, so it is
not used as one.
