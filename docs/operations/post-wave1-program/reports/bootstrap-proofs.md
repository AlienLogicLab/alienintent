# Local Program Director — bootstrap report and proofs

Date: 2026-09-21. Author: resident Claude bootstrap coordinator (`alienintent-1c`).
Scope: the bootstrap defined in `docs/operations/bootstrap-alienintent-local-program-director.md`.

The bootstrap's own completion bar is quoted and honoured: *"Do not call the bootstrap complete
until both Codex spawning and Claude direct messaging are proven."* Both are proven below, with
the commands and outputs that prove them.

## 1. Artifacts created

| Path | What it is |
| --- | --- |
| `tools/orchestration/director.py` | Routing policy, risk classes, durable `ProgramState` |
| `tools/orchestration/codex_session.py` | Bounded fresh Codex session launcher |
| `tools/orchestration/bridge.py` | File-backed Director ↔ coordinator mailbox |
| `tools/orchestration/bridge_wait.py` | Session-bound waiter that wakes the resident coordinator |
| `tools/orchestration/director_cli.py` | Operator surface: `status route ask await codex whoami` |
| `tools/orchestration/test_{bridge,director,codex_session}.py` | 49 tests, all passing |
| `docs/operations/post-wave1-program/program-director.md` | Role, authority boundaries, operating rules |
| `docs/operations/post-wave1-program/program-state.json` | Durable program state |
| `docs/operations/post-wave1-program/task-ledger.md` | Human-readable ledger |
| `docs/operations/post-wave1-program/prompts/`, `messages/`, `reports/` | Dispatch inputs and captured outputs |

## 2. Codex launcher path and validated invocation shape

Binary: `/home/netmarine/.local/bin/codex`, **codex-cli 0.155.1**. The invocation shape was
*discovered* from `codex exec --help` on the installed CLI, not guessed:

```
codex exec --cd <dir> --ephemeral --sandbox <mode> --model <model> \
           --output-last-message <file> -            # prompt on stdin
```

`--ephemeral` keeps each dispatch a genuinely fresh, unpersisted session.

## 3. How GPT-6 Astra selection is resolved

Resolved at call time from `~/.codex/config.toml` (`model = "gpt-6-astra"`) by
`director.resolved_codex_model()`, never hardcoded, and the resolved value is recorded with every
run. If the config cannot be read the resolver returns `UNKNOWN` rather than guessing a default.

## 4. Claude fresh-session launcher

**Not created.** Nothing in the program yet requires a fresh Claude session, and Tier 4 work
(`design_verification`) has not been dispatched. Recording this as absent rather than implying
coverage that does not exist. When Tier 4 is first dispatched, `claude -p --permission-mode plan`
is the read-only equivalent already established during Wave 1.

## 5. Direct bridge mechanism, and whether a peer mechanism was reused

**A fallback mailbox was created; no existing peer mechanism was reusable.**

The bootstrap instruction was explicit: *do not reverse-engineer or write directly to an
undocumented socket protocol if a supported helper/tool already exists.* I looked for the
supported helper first. `claude agents --json` exists and works, but it is a **discovery**
surface — it enumerates sessions and reports identity; it offers no message delivery. There is no
supported CLI by which an external process sends a message into a running Claude session. The
session's Unix socket was left untouched.

That absence is what justifies the fallback, not convenience. The mailbox lives at
`~/.local/state/alienintent/orchestration/{inbox,outbox,acknowledgements}` — outside the
repository, consistent with the installation/secrets policy. Publication is atomic via
`Path.replace`. Every envelope carries `message_id`, `correlation_id`, `sent_at`, `from_role`,
`to_role`, `message_type`, `task_id`, `subject`, `body`, `requires_reply`, `reply_to`,
`handled_at`, `status`.

The AlienIntent product attention queue was deliberately **not** used: no existing authority says
that queue is appropriate for program orchestration traffic.

## 6. Current Claude coordinator endpoint / identity

Resolved live by `director_cli.py whoami` (discovery only, no secrets):

```
name      : alienintent-1c
cwd       : /mnt/d/Projects/alienintent
status    : busy
pid       : 117505
```

The session identifier is a local handle recorded in the message envelope; it is not a credential
and no token, key or installation identifier is stored in or reachable from the bridge.

## 7. Synthetic round-trip proof

Ordering matters and was chosen so the wake-up is causal rather than coincidental: **the waiter
was armed before the message was sent.**

1. `bridge_wait.py --timeout 1800 --poll 3` armed as a Claude-tracked background task.
2. Director sent a real coordinator-only question (`POSTW1-BRIDGE-000`), not a ping — a transport
   proven only on `"hello"` is not proven on anything that matters:
   `message_id=msg-19a89162e828`, `correlation_id=cor-957146bd3a1b`.
3. The waiter **exited**, which is what makes the harness deliver a completion event into the
   resident session. It reported the message and acknowledged nothing — acknowledgement asserts
   *handled*, which only the coordinator may assert.
4. The coordinator answered from lived context and published a correlated reply:
   `msg-65e441295fe6`, `correlation_id=cor-957146bd3a1b` — identical to the request.
5. `director_cli.py await --request msg-19a89162e828` returned that reply, body intact.
6. **No duplicate delivery:** re-arming the waiter after handling returned
   `"no Program Director mail in this window"` with exit 1; `pending()` for the coordinator is
   empty; the request's status is `handled` with `handled_at` set.

The Founder relayed nothing at any step.

A detail worth keeping: the identity the Director resolved before sending
(`session 98be9ff8-7334-433b-86cf-c9b80a665408`) is the session that actually woke and replied.
The bridge addressed the coordinator it reached.

## 8. Restart / reconstruction proof

Run from `/tmp` in a brand-new interpreter with no inherited memory, reading only disk:

```
current phase : 1R
completed     : ['0', '1']
next task     : POSTW1-LEARN-002 - Wave 1 Learning Consolidation
phase-0 proofs: [('POSTW1-BRIDGE-000','DONE','PASS'), ('POSTW1-SMOKE-000','DONE','PASS')]
request       : msg-19a89162e828 handled -> claude-bootstrap-coordinator
reply         : msg-65e441295fe6 correlation match: True
still pending : []
```

Program state and the full correlated conversation both survive process death. `ProgramState`
writes through a `.json.partial` temporary and `Path.replace`, so a crash mid-write cannot leave a
torn state file.

## 9. Permission and sandbox defaults

- Default sandbox `read-only`; `workspace-write` permitted only when explicitly requested.
- `danger-full-access` is **refused** — `ValueError`, not a warning. Never silently escalated for
  convenience.
- `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN` are stripped from every
  child environment. Wave 1 established that an ambient key silently overrides subscription
  authentication.
- No secrets are written into the repository.

## 10. Defect found and fixed during the bootstrap

Recording this because the bootstrap's value depends on the launcher's verdicts being trustworthy,
and this one was not.

**Symptom.** The first live smoke run exited 0 and produced a correct terminal report, and the
launcher classified it `ok: false, failure_class: PROVIDER_CAPACITY_INTERRUPTION`.

**Cause.** Precedence. `_CAPACITY_MARKERS` (`"usage limit"`, `"quota"`, `"rate limit"`,
`"insufficient credits"`) were matched against stderr *before* exit code and terminal message were
considered. The marker that matched was **`quota`** — and it appeared in Codex's own narration,
echoed to stderr, because the document it was summarizing is *about* Wave 1's provider-capacity
incident.

**The general lesson**, which is worth more than the fix: a keyword scan over a model's own
transcript misfires whenever the subject matter is the keyword. Capacity markers describe *why* a
run failed; they must never decide *whether* it failed.

**Fix.** Outcome is determined first; markers only refine the explanation of a run already known to
have failed. Two regression tests were written first and watched fail
(`test_a_successful_run_is_not_reclassified_by_a_capacity_warning_in_stderr`,
`test_capacity_classification_still_applies_when_the_run_actually_failed`). Suite: 49 passing.

**Not a near miss in the safe direction.** Left unfixed this would have reported healthy Codex work
as provider failure — inflating apparent provider unreliability with fabricated incidents, exactly
the kind of contamination Wave 1's evidence discipline exists to prevent.

## 11. Codex spawn proof

After the fix, re-run live against the real prompt:

```
exit_code : 0
ok        : true
model     : gpt-6-astra   sandbox: read-only
terminal  : BIUS=11 / FIRST_PASS=2 / UNKNOWN_EXAMPLE=end-to-end tokens/cost
token_usage / cost : UNKNOWN   (not reported by this path; never recorded as 0)
```

The terminal values are independently correct: Wave 1 closed with 11 BIUs, 2 first-pass
acceptances, and end-to-end tokens/cost is a genuine UNKNOWN in the closure evidence. Success was
established from the structured terminal report, not from process exit.

## 12. Current program state

```
program        : post-wave1-to-wave2
current phase  : 1R        completed: 0, 1
codex model    : gpt-6-astra
POSTW1-BRIDGE-000    ph0   DONE     MEDIUM  claude-bootstrap-coordinator
POSTW1-SMOKE-000     ph0   DONE     LOW     codex-fresh
POSTW1-REVIEW-001    ph1R  DONE     HIGH    claude-bootstrap-coordinator
POSTW1-LEARN-002     ph2   READY    MEDIUM  codex-fresh
POSTW1-BOOTSTRAP-006 ph6   PLANNED  HIGH    codex-fresh
```

No task is `FOUNDER_DECISION_REQUIRED`, so the program is not currently stopped on a Founder
branch.

## 13. First real task queued

`POSTW1-LEARN-002 — Wave 1 Learning Consolidation`, routed and recorded before dispatch:

```
tier    : CODEX_PRIMARY (2)    actor: codex-fresh    model: gpt-6-astra
risk    : MEDIUM              review_required: true
rationale: substantial code-aware technical work; fresh context avoids inheriting participant bias
```

It is routed to Codex rather than to me on purpose. I am a Wave 1 participant; consolidating the
lessons of a wave I helped run is precisely the work where my context is worth less than my bias
costs. It is queued, not dispatched — dispatch awaits the Founder.

## 14. Confirmation: no AlienIntent lifecycle or Product state was modified

Verified, not assumed:

- No BIU lifecycle state was read as mutable or written. Program task states are disjoint from BIU
  lifecycle states, and `ProgramState.upsert_task` **raises** on a BIU lifecycle name.
- No GitHub Project state was changed; no Issue was opened, closed or edited.
- No Product Requirement was created, amended or weakened.
- No Wave 1 historical evidence was altered.
- No runtime worker contract, dispatcher profile, provider configuration or Node/B-DISP semantics
  was touched.
- All Codex activity ran `--sandbox read-only`.

Everything the bootstrap wrote is additive: new files under `tools/orchestration/` and
`docs/operations/post-wave1-program/`.
