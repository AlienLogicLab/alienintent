# FDH-01 — Factory Director Host: authoritative activation predicate, provider-neutral episode launch, continuity proof

Bounded bootstrap-infrastructure BIU under **SF-REQ-053** (persistent control plane with bounded
coordinator episodes). It is **not** a Wave 2 DAG node and does not add, remove or reorder any DAG
node; it is prepared as standalone bounded work in the same way as Issue #83. Priority: **P0 core
factory infrastructure** (Founder direction 2026-09-23, reaffirmed 2026-09-24).

Baseline: `origin/main` @ `674b78d2db17`.

## Intent

Make Factory Director continuity structural. A deterministic, non-cognizant host must start a fresh,
bounded Factory Director episode whenever durable factory state says Director cognition is required
and no valid episode holds the Director lease, and must re-evaluate immediately after every episode
exit. A model episode must never own the decision that no further Director episode is required.

## Authority

- SF-REQ-053 scope items 1 and 3 (durable episode context and tenure; fresh-context reconstruction).
- SF-REQ-053 non-goal "unattended authority-bearing model activation **without explicit
  authorization**": explicit authorization is the Founder direction recorded in
  `docs/operations/AlienIntent_Chat_Record_Last_24h_20260923-185454-SGT.md` §13–§16 and the
  Founder instruction of 2026-09-24 to route this harness through the factory. The episode inherits
  exactly the Factory Director's existing authority; the host confers none.
- Provider routing (2026-09-24 Founder direction): Claude is the primary Factory Director provider
  while Codex capacity is rationed; the launcher must support both without code change.

## Prior implementation to preserve and reuse

Branch `feature/factory-director-harness` @ `c14aba15dfc4c951c91c01b57299cfc042092aab`, published
to `origin` on 2026-09-24 so the PRODUCER can retrieve it, contains four commits authored outside
the lifecycle, merged onto `13cac4e`:

- `7dc2b17` add temporary factory director continuity host
- `1947d41` fail closed director host ownership gaps
- `02b62bd` validate factory director host lease records
- `0846cfd` fail closed director host launch handoff

Files: `tools/orchestration/factory_director_host.py`, `tools/orchestration/test_factory_director_host.py`,
`tools/orchestration/install_factory_director_host.sh`, a user systemd unit. The PRODUCER must start
from this branch merged with the current baseline, keep what is valid, and state explicitly anything
it replaces and why. This prior work is evidence input, not accepted work: it has had no independent
verification and does not reduce any obligation below.

## Scope (bounded extent)

1. **Authoritative predicate adapter.** A deterministic, read-only producer of the host's
   `DirectorInputs` projection (all nine booleans), written atomically, derived only from durable
   sources:
   - GitHub Project #1 read through the existing fail-closed read path in
     `tools/live/project_materialization.py` (complete board, one item per Issue, no non-Issue items);
   - the Node runtime state file named by `~/.config/alienintent/self-hosting.json`
     (`paths.stateFile`): `active` claims, `limitEscalations`, `founderExceptions`;
   - a durable Founder-hold record listing the Issue numbers under an unresolved Founder hold;
   - a durable explicit-pause flag;
   - a durable Director inbox directory.

   Mapping (fixed by this contract; the candidate documents it in code and tests):

   | Predicate | True when |
   |---|---|
   | `authoritative_state` | every source above was read successfully and is internally consistent; any read failure, partial board, parse error or schema mismatch makes it false |
   | `eligible_authorized_work` | at least one Issue is in `READY` and not covered by the Founder-hold record, or an Issue is in `IMPLEMENT`/`VERIFY`/`ACCEPT` with no active runtime claim for it |
   | `lifecycle_requires_selection` | an Issue is in `REVIEW`, or an Issue is in `TASKS` with a retained Agent Ready assessment and no READY transition |
   | `attention_required` | the runtime state has an unresolved `limitEscalations` entry |
   | `pending_director_inbox` | the inbox directory contains at least one unprocessed entry |
   | `executable_capacity` | active runtime claims are fewer than the configured WIP limit (1) |
   | `wip_intentionally_full` | active runtime claims equal the WIP limit |
   | `founder_decision_pending` | every item that would otherwise make control required is covered by the Founder-hold record (a hold on some items must not idle the host while other authorized work exists) |
   | `explicit_pause` | the pause flag exists |

   **Control semantics fixed by the Factory Director (2026-09-24, answering the Agent Ready
   owner clarifications on this contract):**

   - *Founder-hold coverage.* A Founder hold covers an Issue in **every** lifecycle state. A held
     Issue is excluded from `eligible_authorized_work` and `lifecycle_requires_selection` whether it
     is in `TASKS`, `READY`, `IMPLEMENT`, `VERIFY`, `REVIEW` or `ACCEPT`, claimed or not.
     `founder_decision_pending` is true exactly when the hold record lists at least one Issue that
     would otherwise make control required, **and** no unheld Issue does, **and**
     `attention_required` and `pending_director_inbox` are both false (those two are not per-Issue
     and are never suppressed by a hold).
   - *Absent sources.* The Founder-hold record and the Director inbox directory are **required**
     sources. An absent hold record or an absent inbox directory makes `authoritative_state` false,
     exactly like an unparsable one. "No holds" is written explicitly as an empty list, and "no
     inbox entries" as an empty directory. The explicit-pause flag is the only presence-only source:
     absent means not paused.
   - *Processed inbox entries.* An inbox entry is a file `<id>.json` directly in the inbox
     directory. It is processed exactly when a receipt `processed/<id>.json` exists beneath the inbox
     directory. Only a Director episode writes receipts. The adapter only reads both. A receipt
     with no matching entry is ignored, and an entry with no receipt is unprocessed.

   Criterion 2 therefore also covers an absent hold record and an absent inbox directory.

   The adapter never infers authority from a process list, never writes to GitHub, the runtime state
   file or the Node configuration, and never releases or transitions any Issue.

2. **Provider-neutral episode launcher.** `ProcessDirectorLauncher` supports `claude` and `codex`
   by configuration (no code change to switch). Each launch is a fresh process with no resumed or
   inherited conversation, the existing linked-worktree isolation check, process-start identity, and
   the episode id substituted into the prompt. Provider and model actually used are recorded in the
   host history, never inferred.

3. **Durable Factory Director runtime contract.** `docs/operations/factory-director-runtime-contract.md`
   as described in the chat record §17: role and mission; continuous-control invariant; the five
   allowed terminal conditions (§15) and the non-terminal checkpoints; the continuity-fault definition
   (§14); startup reconstruction procedure; authority boundaries; one-owner mutation rule; forward-only
   rules; the replacement-safety rule (§16); and that a fresh episode must continue with no
   conversation history. The host's episode prompt is a short pointer to this contract.

4. **Offline continuity proof** in tests using the in-memory launcher and fixture sources: episode
   exits → host re-evaluates → fresh episode launched while control is required; no launch while a
   valid lease is held; idle with the correct reason for each terminal condition; fail closed on each
   malformed source.

5. **Live-proof procedure** (`docs/operations/factory-director-host-live-proof.md`): the exact
   commands and evidence to retain for the twelve-step proof in chat record §16. Executing it is
   **not** part of this BIU (see Non-goals); the procedure must be runnable as written.

## Non-goals

- Retiring, disabling or replacing any existing continuity, observer, liveness or Node runtime
  mechanism. Replacement safety (§16) applies: nothing is retired on the strength of this BIU.
- Executing the live proof, installing or enabling the host service on the live machine, or
  changing `~/.config/alienintent/self-hosting.json`. Those are Factory Director actions after landing.
- Implementing Wave 2 DAG nodes (WO-2203xx, WO-2206xx) or the SF-REQ-053 Python product port.
- Releasing, dispatching or transitioning any Project item; changing Founder holds.
- New lifecycle states, services beyond the one host unit, or approval lanes.

## Dependencies

None open. Uses landed `tools/live/project_materialization.py` (Issue #83 landing `13cac4e`) and the
Node runtime state format at the baseline.

## Acceptance criteria

1. Given fixture sources, the adapter emits exactly the nine predicates with the mapping above; one
   test per predicate proves both a true and a false case.
2. Each malformed or unavailable source (board incomplete or with a non-Issue item, state file missing
   or unparsable, hold record absent or unparsable, inbox directory absent) yields
   `authoritative_state=false` and the host idles with
   `AUTHORITATIVE_STATE_UNAVAILABLE`. Each such test is shown failing against a deliberately broken
   adapter before passing (a check that cannot fail is not evidence).
3. With a Founder hold on some READY items and another READY item unheld, the host launches; with all
   eligible items held, it idles with `FOUNDER_DECISION_PENDING`. A held unclaimed `IMPLEMENT` Issue
   does not make control required. A pending inbox entry without a receipt launches despite holds,
   and the same entry with a `processed/<id>.json` receipt does not.
4. Offline continuity: episode A launched → A exits → next reconcile launches fresh episode B with a
   new episode id and new lease; no second launch while B is live; B exits with no control required →
   host idles with `NO_ELIGIBLE_AUTHORIZED_WORK`.
5. The launcher builds a correct fresh-session command line for both `claude` and `codex`, records the
   provider and model used, and refuses a non-isolated workdir.
6. The runtime contract and live-proof procedure exist, cover every item listed in Scope 3 and 5, and
   the episode prompt references the contract rather than restating it.
7. `node scripts/check.mjs all` exits 0 and the host and adapter Python tests pass at the candidate.

## Verification obligations

Independent VERIFIER retrieves the exact candidate SHA in its own worktree, re-runs criteria 1–7,
applies each negative control in criterion 2, and records command, exit status and counts. It also
checks the adapter is read-only: no GitHub write, no runtime-state or configuration write, no Issue
transition anywhere in the candidate.

## Evidence obligations

- Retain candidate branch and full SHA, commands, exit codes, test counts and negative-control
  application counts. Missing measurements are explicit holds, never zero or PASS.
- Record which prior-branch commits were kept, modified or replaced, with reasons.
- Tokens and cost are measured where the provider exposes them, never assumed zero.

## Execution packet and allocation

Configured PRODUCER and independent VERIFIER; concurrency 1; 3 execution cycles and 1 replacement per
phase (bound in `execution.biuLimits` before release); wall-clock bounded by systemd supervision
(120 min runtime + 2 min startup + 5 min stop grace).

Landing: SWF-19 — merge the accepted candidate branch directly into the baseline branch, preserving
the accepted SHA. **Do not open a pull request.** AlienIntent does not use pull requests.

Release authority is not granted by this document. Release is additionally held behind the open
worker-credential hold recorded on Issues #80 and #81 (worker accounts still hold pull-request write).

## Candidate custody

PRODUCER pins contract, baseline and candidate branch plus full SHA; publishes the candidate to the
configured remote and records the exact branch and SHA on the Issue before RESULT=VERIFY. A fresh
independent VERIFIER retrieves that exact SHA in its own worktree; retrieval and verdict receipts are
retained.

## Stop and escalation

Stop on source revision mismatch, unavailable evidence, a failing discriminating probe, or conflicting
ownership. Scope or authority questions return to the Factory Director; only a genuine Founder-reserved
boundary goes to the Founder. Unrelated improvements are recorded and deferred.
