# AlienIntent operations

## Install and configure

Use Node 24.15.0 on Linux. The public executable is `alienintent`; `b-disp` remains
a temporary compatibility alias. From a source checkout, run
`node bin/alienintent.mjs --help` without credentials.

Copy `config/profile.example.json` into a private installation directory and replace
its synthetic values. Keep the private profile, App key, webhook secret, runtime
state and worker logs outside the repository. Never publish credentials.

The supported installation has one organization-owned repository and Project V2,
one organization-owned GitHub App installed on that same organization, and one
running profile. Configure the existing Status field with this exact ordered lifecycle:
CAPTURE → SPECIFY → PLAN → TASKS → READY → IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE.
All ten names are required in `project.statusNames`; the App preflight verifies one
Status field, the complete ordered option set and complete field pagination. Missing,
ambiguous or unsupported options fail closed. Display-name casing is normalized.
Do not create a competing Status field. Preserve existing option IDs when updating it.
The Project lifecycle is broader than the execution engine: only IMPLEMENT, VERIFY
and ACCEPT dispatch workers. The other states do not implicitly launch or promote work.

App access is restricted to the configured repository and the
permissions and webhook events enforced by App preflight. Worker and authorized
operator GitHub identities must be separate from the App identity.

Each worker needs its Git identity, GitHub login/configuration directory, GitHub
shim directory, provider executable, provider authentication HOME, permission mode
and funding profile. Codex and Claude adapters are supported. `claude-subscription`
checks subscription authentication; `provider-default` does not impose that policy.
Install `scripts/worker-gh` as executable `gh` in each configured shim directory.
The launcher filters ambient App/provider secrets and uses explicit executable paths.

Execution-enabled profiles require a canonical `paths.repositoryStore`, a separate
`paths.worktreeRoot`, and `repository.baselineRef`. Provision and update the canonical
store separately: the dispatcher does not fetch or clone. Its origin must exactly
match the configured repository. Both ordinary and bare canonical stores are supported;
a linked worker checkout cannot serve as the store. Permanent role worktree paths
are rejected. Keep log/evidence directories outside disposable worktrees.

The **PY-10 live-proof sandbox** is a separate installation with its own repository, Project,
profile, tunnel, port and (pending) App identity. Its provisioned resource identities are recorded in
[operations/py10-sandbox.md](operations/py10-sandbox.md). Nothing in this installation may reference it,
and it may not reference anything here.

## Start and reconcile

Run `node bin/alienintent.mjs --config <private-profile.json>` within the installation's
authorized live scope. `--preflight-only` validates App access and exits before
workflow-state creation. `--once` reconciles startup state and exits.

With execution disabled the runtime does not run worker preflight or launch workers.
It can still handle durable results and mutate Project/local state during
reconciliation. Execution disabled is not a globally read-only mode.

The signed webhook path admits only configured repository/Project events. Normal
progression uses authenticated Issue results and dispatcher Project transitions;
the operator is not a message relay.

## Lifecycle semantics

| State | Meaning |
|---|---|
| CAPTURE | Initial product, problem or work intent |
| SPECIFY | Requirements, constraints and acceptance criteria |
| PLAN | Approach and decomposition |
| TASKS | Materialize bounded work units |
| READY | Sufficiently specified, dependency-resolved, Agent-Ready assessed, eligible for explicit release |
| IMPLEMENT | Producer execution |
| VERIFY | Deterministic/mechanical verification |
| REVIEW | Qualitative engineering judgment; not necessarily a separately dispatched lane |
| ACCEPT | Accepted engineering result / authority decision |
| DONE | Operational closure complete |

READY describes the readiness contract; this correction does not wire a new
Agent-Ready assessment or automatic release mechanism into the Node dispatcher.
There is no MERGE state. Merge/landing is a repository operation performed during
closure after ACCEPT on the path to DONE, when authorized by the work packet.
The bootstrap's existing VERIFY worker and result routing are unchanged; the full
board vocabulary does not introduce a separate REVIEW worker or new handoff.

## Result protocol and lifecycle

The compatibility marker remains:
`<!-- B-DISP: INVOCATION=<exact-id> RESULT=VERIFY -->`.
Producer IMPLEMENT work posts exactly one permitted terminal Issue result.
Verifier `ACCEPT` routes to the Project's `Accept` option, not `Review`.
Verifier REJECT returns to IMPLEMENT. REVIEW is not a dispatched lane and MERGE is
not a workflow state. The author, repository, Issue, invocation, allowed result and
timestamp must match. stdout, chat and process exit do not supply workflow authority.

Before a fresh result changes workflow state, the current Project status must match
the admitted phase. Mismatches record `STALE_RESULT` without transitioning the item.
Previously persisted exact transition intents can confirm a target already reached
after interruption. Startup settles pending transitions before admitting the next phase.

The producer handles closure in ACCEPT, including all authorized landing,
publication/deployment and operational obligations. Only completion permits
`RESULT=DONE`. An authority block uses `RESULT=FOUNDER_EXCEPTION` and retains the
phase. Material implementation changes require `CONTROL=RETURN_TO_IMPLEMENT` and
fresh independent verification. Markers use the same exact invocation grammar.

Human exception recovery requires `operator.authorizedGithubLogins`. The event must
also follow the exception timestamp, change from a different status and match the
current remote status. Worker/App identities cannot act as operators.

## Bootstrap liveness reconciliation (temporary)

**Status: temporary bootstrap responsibility, Founder-authorized 2026-09-20 ([SWF-29](decisions/2026-09-20-liveness-reconciliation.md)). It expires when the canonical Python liveness capability (SF-REQ-056) replaces it.**

The Node bootstrap advances a BIU only on event delivery. A dropped delivery therefore leaves durable lifecycle state that requires an actor with no actor running, no error, and no retry. Until the canonical capability exists, the bootstrap coordinator enforces this rule.

**Rule.** When an active BIU enters a lifecycle state that requires an actor or effect, the expected invocation/effect must appear within **5 minutes**.

| Lifecycle state | Expected |
|---|---|
| IMPLEMENT | PRODUCER invocation |
| VERIFY | VERIFIER invocation |
| ACCEPT | required closure action, where the BIU contract requires closure work |

**This is liveness reconciliation, not backlog polling.** Every 5 minutes the coordinator inspects **only active, nonterminal BIUs it already knows**. It never queries Work Management to discover new READY work.

**Procedure**, per applicable BIU: identify current lifecycle state; determine the expected actor/effect; check for an active invocation; check pending claim, reservation, effect or outbox evidence where available; check for a recently completed correlated invocation or effect that may be awaiting projection; if matching evidence exists, do nothing; if none exists and the state is less than 5 minutes old, do nothing; if none exists and the state is at least 5 minutes old, classify **`LIVENESS_GAP`**, recover through the narrowest already-authorized idempotent mechanism, and record the detection, the evidence checked, the recovery and its result durably.

**Judgment-required outcomes suppress recovery ([SWF-29 amendment](decisions/2026-09-20-liveness-reconciliation.md)).**
A completed correlated outcome is evidence the actor **did** launch. If that outcome is
`FOUNDER_EXCEPTION`, `HumanDecisionRequired` or another judgment-required blocking result, the watch
records `LIVENESS_SUPPRESSED`, ensures a durable attention item exists, and **does not re-emit the
lifecycle trigger** — no matter how long no actor has been running. Recovery resumes only after the
item is acknowledged or a newer non-judgment outcome supersedes it.

> Liveness reconciliation repairs missing effects; it must not retry completed effects whose result
> requires judgment.

**Hard rules.**

- Never create a duplicate invocation merely because a webhook appears late. **The watcher's evidence check alone does not guarantee this**: it re-verifies the lane claim immediately before transitioning and verifies afterwards that exactly one claim exists, but prevention rests on the dispatcher's lane claim (`repository#issue:ROLE`, synchronous check-and-reserve). Delivery-id dedupe does **not** cover a re-emission, which carries a new delivery id, and the guarantee is single-process. See [SWF-29](decisions/2026-09-20-liveness-reconciliation.md) for the full limitations.
- Never interfere with an invocation that is active, pending or correlated.
- Never poll the backlog for new work.
- Never alter Node/B-DISP product semantics.
- Never let this bootstrap rule silently become permanent architecture.

**Recovery in the bootstrap is an authorized operator status re-emission.** That is evidence of the required outcome, not the canonical mechanism; SF-REQ-056 explicitly forbids status toggling as the permanent design.

**Evidence.** Each detection appends a durable record to `~/.local/state/alienintent/coordinator-liveness.jsonl` and posts an attributable comment on the affected Issue, carrying BIU identity, lifecycle state, expected actor, state age, evidence checked, duplicate-prevention evidence, recovery action and result.

## Coordinator-independent monitoring (temporary bootstrap)

Deterministic monitoring must not depend on a model coordinator session being alive
([SWF-27 bootstrap evidence](decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md)).

| `systemd --user` unit | Role | Decides? | Durable output |
|---|---|---|---|
| `alienintent-liveness.service` | 5-minute actor-launch reconciliation (SWF-29) | acts only under the SWF-29 rule | `~/.local/state/alienintent/coordinator-liveness.jsonl` |
| `alienintent-observer.service` | lifecycle observation | no — observes only | `~/.local/state/alienintent/coordinator-observations.jsonl` |

Scripts live in `~/.local/share/alienintent-bootstrap/` and are owned by the bootstrap operator, not by
any session. Each service is a single instance (`flock` on a lock file under the state directory) and
restarts on failure. Observations carry BIU identity, observed lifecycle state, timestamp, expected
actor, the transition or anomaly, any recovery already taken, and `requires_model_judgment` — so a new
coordinator filters on that flag rather than replaying history. A coordinator checkpoint is kept at
`~/.local/state/alienintent/coordinator-checkpoint.md`.

Both services are temporary bootstrap infrastructure: the liveness service expires with SWF-29 when
SF-REQ-056 lands, and the observer expires when the canonical control plane records its own trajectory
(SF-REQ-029). Neither changes Node/B-DISP semantics.

Control: `systemctl --user {status,restart,stop} alienintent-liveness alienintent-observer`.

### Attention queue — observation to coordinator attention (temporary bootstrap)

Observation alone does not reach anyone. PY-06 reached DONE, was observed correctly, and nothing
notified or activated a coordinator; the factory idled until the Founder said so by hand
([SWF-27 activation boundary](decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md)).

Both services now route attention-worthy observations through
`~/.local/share/alienintent-bootstrap/attention.py` into an append-only queue at
`~/.local/state/alienintent/coordinator-attention.jsonl`:

```
python3 ~/.local/share/alienintent-bootstrap/attention.py list         # outstanding items
python3 ~/.local/share/alienintent-bootstrap/attention.py show <id>
python3 ~/.local/share/alienintent-bootstrap/attention.py ack <id> --by coordinator --note "..."
```

**A coordinator starting cold reads this first** — it answers what needs judgment, for which BIU, when,
which authority is required, and whether it was handled, without the previous conversation.

| Notifies | Does not notify |
|---|---|
| BIU reaches DONE (next release is coordinator work) | `INVOCATION_ACTIVE` / `INVOCATION_ENDED` churn |
| `FOUNDER_EXCEPTION` | a single verifier rejection — normal repair |
| `LIVENESS_GAP` that recovery did not close | a `LIVENESS_GAP` that recovery closed |
| 3+ verifier rejections on one BIU (convergence doubt, SWF-23) | `VERIFY_TO_VERIFY`, `ACCEPT_TO_ACCEPT` |
| any observation carrying `requires_model_judgment: true` | |

Item identity is the dispatcher's own outcome (invocation plus outcome timestamp), not the moment of
observation, so restarting a daemon cannot re-raise a handled item.

**Notification channel: Windows toast via the WSL host** (`notify_founder.py`, PowerShell). Chosen after
eliminating the alternatives in this environment: `notify-send`/zenity/kdialog and mail/sendmail are not
installed; `wall`/`write` cannot reach a tty at mode 600; and **a GitHub Issue comment does not work as a
Founder notification here, because the only credential authenticates as the Founder's own account and
GitHub does not notify an author of their own comment or self-mention** — it would look delivered and
reach nobody. Delivery is best-effort and never silent: the durable item is written before the attempt,
and every attempt records `delivered` with its channel or its error.

Tests: `python3 -m pytest ~/.local/share/alienintent-bootstrap/ -q` — attention queue, notification channel,
liveness suppression and release admission.

### Attention waiter — the wake-up bridge (temporary Wave 1 bootstrap)

Externalizing monitoring to systemd kept detection and lost the **callback**. Before PY-06, watchers
ran as Claude-tracked background tasks, and a tracked task's *exit* makes the harness deliver a
completion event into the session — that event was the wake-up. A systemd process is invisible to the
harness, so durable attention items accumulated with nobody woken: PY-06's DONE sat 45 minutes, PY-07's
`FOUNDER_EXCEPTION` was never seen, PY-08 never left TASKS for 1h45m.

> While the Wave 1 bootstrap coordinator episode is resident, a session-bound attention waiter bridges
> durable attention events into the Claude harness. Persistent monitoring remains externalized and
> independent of coordinator lifetime.

The bridge is one process, owned by the coordinator session, launched as a **tracked** background task
(never with `&`, which detaches it and restores the original defect):

```
python3 ~/.local/share/alienintent-bootstrap/attention_wait.py
```

It waits on the attention queue with `inotify`, and when an unhandled item appears it prints the
outstanding items and **exits** — the exit is the point. It decides nothing, mutates nothing, and
launches nothing. Exit 0 = something needs judgment; exit 1 = the window closed quietly.

Duplicate protection is by durable item identity: on arming it snapshots the ids already outstanding
and never wakes on those again, so re-arming while items remain open cannot loop. Acknowledged items
never wake anything. Several unhandled items produce one wake-up listing all of them. **Re-arm after
acknowledging**, and the bridge stays live.

The observer and liveness services are untouched by this and remain authoritative for detection. The
bridge expires with the Wave 1 bootstrap, or when canonical coordinator activation (SF-REQ-053)
replaces it.

### Coordinator duty on a rejection — verification-first sequencing

When a repair cycle is rejected, judge the order of the next one before its content
([SWF-23 §4b](decisions/2026-09-20-convergent-repair-monotonic-progress.md)): the required verification
harness must exist, changed paths must carry proof that can actually go red, previously proven criteria
must stay proven, and only then does broad implementation repair belong in the candidate. A cycle that
widens implementation while the harness for what it touches is missing is out of order — say so at the
rejection rather than waiting for the defect it predicts. Binding for PY-09 and PY-10.

### Repair-cycle data (factory yield)

Attention and measurement are separate: the attention queue wakes a coordinator only when judgment is
needed, so it must never decide what gets recorded. Every cycle is measured regardless.

```
python3 ~/.local/share/alienintent-bootstrap/cycle_data.py <issue>... \
  --out docs/evidence/wave1-repair-cycles.json
```

Cycle identity comes from the **B-DISP result markers**, which every BIU carries identically — report
prose does not, and keying on it silently loses most BIUs. Candidate sizes are computed from Git.
Fields that cannot be read reliably are recorded as `null`, never as `0`. Results and their limits:
[wave1-repair-cycles.md](evidence/wave1-repair-cycles.md).

### Release admission gate

Before every READY → IMPLEMENT release, and before any worker is launched:

```
python3 ~/.local/share/alienintent-bootstrap/release_admission.py <issue>
```

It checks the six preconditions of the [SF-REQ-002 admission amendment](decisions/alienintent-software-factory-plan.md)
— implementation explicitly authorized, exact baseline named, baseline resolves, baseline reachable
from the release point, no stale "not authorized" wording without a superseding record — prints each
failure with its reason, and exits non-zero. **A failed check is a refusal to transition, not a
warning.** The checklist is in [SWF-21](decisions/2026-09-20-wave1-release-coordinator.md); the
incident that produced it is in [evidence](evidence/2026-09-21-liveness-retry-and-release-admission.md).

This queue is bootstrap tooling, not the Decision Inbox. The Decision Inbox (SF-REQ-035, PY-07) owns
durable authority decisions; this owns making a coordinator aware that judgment is needed. It expires
when SF-REQ-053 activation and the Decision Inbox land.

## Worktrees and recovery

Repository-changing tasks outside the BIU lifecycle also require explicit
closure. Follow [Repository change closure](operations/forward-momentum.md#repository-change-closure):
LANDED, DISCARDED, or PARKED with a durable owner/content/blocker/next-action
record. This task-level rule does not replace the runtime-managed invocation
resource retention and cleanup rules below.

Each invocation pins the configured baseline commit and allocates a fresh UUID
worktree and branch. Git identity is isolated through per-worktree configuration.
Preflight verifies the assigned checkout, invocation, canonical store, origin,
baseline, Git/GitHub identity, Issue write access and repository-state evidence.

Follow the [governing directive](migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md)
and [repository-state guidance](operations/forward-momentum.md). Known authorized
changes require exact path/status/content evidence in `knownChanges`, including
staged content and task authority. Unexpected changes and conflicts still block.

Ownership metadata records each invocation's resource and lifecycle. Cleanup waits
for process exit and terminal handling, removes only the exact registered clean
owned worktree, and retains its branch, ownership marker and logs. Dirty/ignored
content, switched branches, ownership mismatches and uncertain process liveness
retain resources for diagnosis. Cleanup never forces removal or adopts unknown
worktrees. Worktrees share Git objects and the host account; they are not OS sandboxes.

### Candidate worktree retention (SWF-30)

A local candidate worktree is **operational cache, not evidence**, once all seven conditions of the
[SF-REQ-007 amendment](decisions/2026-09-20-candidate-worktree-retention.md) hold: known identity,
durably published candidate, independently retrievable, read-back confirmed, no active invocation,
no uncommitted unique content, no BIU/evidence policy requiring local retention. Then it may be
removed as routine cleanup.

Durably published means **continuing** reachability — a remote reference whose retention is at least
as strong as the evidence obligation. A branch about to be deleted does not qualify. So: **never
delete the `b-disp/<uuid>` remote branch that keeps a removed worktree's candidate retrievable**,
and never remove a worktree whose candidate is reachable from no remote ref. Failing any condition
means retention. Removal uses `git worktree remove`, which deregisters; `rm -rf` leaves the
registration behind and converts finite noise into a permanent `registered worktree missing`
diagnostic.

The `b-disp-ownership` metadata directory and `b-disp/<uuid>` resource branches remain
compatibility identifiers. Do not rename them or rewrite state for naming purity.
Private state validation checks unresolved lane repository/role identities and
recorded worker identities before App access. Preserve persisted aliases and exact
invocation IDs. Legacy invocations without recorded identity require explicit
operator-authorized `compatibility.legacyInvocationIdentities` attribution; it cannot
reassign an old result to a new worker. Completed history remains unchanged.

## Verification and limits

Run `npm test` for Node regression, preflight and policy checks. Provider adapter tests
use bounded fixtures; they do not prove a specific live installation. Record live
App, signed-event, worker, verification, closure and restart evidence separately.

Project item/field reads remain bounded to the first 100 entries and require explicit
`hasNextPage=false`; incomplete and GraphQL-error responses fail closed. There is no
arbitrary status mapping or comprehensive recovery engine. Restart liveness uses
PIDs without durable process-start identity, so PID reuse can retain resources
conservatively. RAI remains unwired.
