# Bootstrap AlienIntent Local Program Director

You are the current long-running Claude bootstrap coordinator for AlienIntent.

The Founder is moving the browser ChatGPT orchestration role into the local environment so that the post-Wave-1 program can be operated locally without the Founder manually relaying prompts between ChatGPT, Codex and this Claude coordinator.

Repository:

    /mnt/d/Projects/alienintent

## Objective

Create the smallest reliable local orchestration layer that provides a persistent **AlienIntent Program Director** role.

The Program Director is not a new product capability and must not be confused with the canonical AlienIntent coordinator architecture. It is temporary post-Wave-1 operating infrastructure used to execute the already-approved closure / learning / Wave-2-design program.

The Program Director must be able to:

1. reconstruct its state from durable local/repository artifacts;
2. launch fresh Codex sessions for bounded tasks;
3. prefer Codex GPT-6 Astra for primary analysis/design work;
4. request independent review from Claude;
5. communicate directly with this existing bootstrap coordinator without requiring the Founder to relay messages;
6. track task state and artifacts durably;
7. stop/restart without losing the program;
8. avoid becoming execution authority for BIU lifecycle state.

Do not redesign AlienIntent to achieve this.

## Governing operating model

Current role split:

    Local Program Director
        owns orchestration of post-Wave-1 analytical/design program

    Codex GPT-6 Astra
        primary analyst
        primary artifact author
        primary designer/planner

    Claude bootstrap coordinator
        historical cross-check
        independent critic
        adversarial reviewer
        bootstrap authority/operations expert

Neither model's conversational memory is authority.
Repository evidence and canonical AlienIntent authority remain authoritative.

## Current program

The Program Director must durably encode this ordered program:

    Phase 0  Wave 1 Closure Manifest
    Phase 1  Final evidence reconciliation
    Phase 2  Wave 1 Learning Consolidation
    Phase 3  Gap Trap Graduation Audit
    Phase 4  Agent-Ready Outcome Completeness Audit
    Phase 5  BIU Split / Replan Process Design
    Phase 6  Bootstrap Retirement / Transition Audit
    Phase 7  Final Wave 1 Retrospective + Architecture Reconciliation
    Phase 8  Wave 2 SPECIFY
    Phase 9  Wave 2 Design Contracts
    Phase 10 Wave 2 Design Verification
    Phase 11 Wave 2 PLAN / dependency DAG
    Phase 12 Wave 2 BIU decomposition
    Phase 13 Agent-Ready assessments
    Phase 14 Founder approval
    then Wave 2 execution

Phase 0 + Phase 1 have already been completed by a fresh Codex GPT-6 Astra session and are currently undergoing / awaiting independent Claude review.

Do not redo completed work merely because the Program Director starts fresh.

## Required local artifacts

Create a small orchestration area, preferably:

    tools/orchestration/
    docs/operations/post-wave1-program/

or the nearest existing convention if repository instructions require something else.

At minimum create durable artifacts equivalent to:

    program-director.md
        role, authority boundaries, operating rules

    program-state.json
        current phase
        task IDs
        task status
        assigned actor
        prompt/artifact references
        review status
        blockers
        timestamps
        resulting commit/SHA
        no private chain-of-thought

    task-ledger.md
        human-readable program status

    prompts/
        immutable or versioned prompts actually sent to workers/reviewers

    reports/
        worker final reports or references to canonical repo artifacts

Do not duplicate canonical project evidence if references are sufficient.

## Codex launcher

Implement a small local launcher/wrapper around the installed Codex CLI.

Use the installed CLI's actual help/configuration to determine supported syntax.
Do not guess command-line flags.

The current OpenAI CLI supports non-interactive `codex exec`; use that mechanism for fresh bounded sessions after validating the locally installed version.

Requirements:

- launch from `/mnt/d/Projects/alienintent`;
- use fresh sessions by default;
- prefer the locally configured **GPT-6 Astra** model for primary tasks;
- use the minimum required sandbox:
    - read-only for audit/review tasks where possible;
    - workspace-write only for authorized artifact-writing tasks;
- capture:
    - prompt identity/path;
    - start/end;
    - exit status;
    - final response;
    - repository SHA before/after;
- do not infer success from process exit alone;
- require a structured terminal report or task-specific completion condition;
- filter ambient credentials that should not leak into child sessions;
- never silently use `danger-full-access` merely for convenience;
- preserve stderr/stdout separately where useful.

Do not hard-code undocumented model syntax. Discover it from the installed CLI/config and record the resolved invocation.

## Claude review launcher

Do NOT replace the current bootstrap coordinator with new one-off Claude sessions when the task specifically calls for historical/bootstrap review.

The Program Director needs two Claude paths:

A. CURRENT BOOTSTRAP COORDINATOR
   - direct request/reply channel to this running coordinator;
   - used for historical cross-check, bootstrap review, and operations knowledge.

B. FRESH CLAUDE REVIEW SESSION
   - optional independent clean-context reviewer where historical participation is undesirable.

For fresh Claude sessions, use the installed Claude Code CLI only after inspecting its actual local help/configuration.
Filter ambient `ANTHROPIC_API_KEY` when subscription authentication is intended; Wave 1 already proved that an ambient API key can override subscription login.

## Direct bridge to the current Claude bootstrap coordinator

This is the critical piece.

First inspect the CURRENT environment and determine what supported mechanism already exists for peer/session messaging.

Evidence from Wave 1 shows that Claude sessions have exchanged messages and exposed a local peer/socket mechanism. Do not reverse-engineer or write directly to an undocumented socket protocol if a supported helper/tool already exists.

Preferred order:

1. reuse an existing supported peer-message helper if one exists;
2. reuse an existing session/agent bridge mechanism if documented locally;
3. otherwise implement the smallest explicit bridge outside Git:
   `~/.local/state/alienintent/orchestration/`

Fallback bridge requirements:

    inbox/
    outbox/
    acknowledgements/

Messages are immutable JSON records written atomically.

Minimum message schema:

    message_id
    correlation_id
    sent_at
    from_role
    to_role
    message_type
    task_id
    subject
    body_path or body
    requires_reply
    reply_to
    handled_at
    status

Use stable identity, never observation timestamp, as dedupe identity.

The current Claude coordinator should run a small session-bound tracked waiter similar to the proven attention-waiter pattern:
- waits for a new unhandled Program Director message;
- prints a concise summary;
- exits successfully so the Claude harness wakes this resident session;
- coordinator processes the message;
- writes a durable reply;
- re-arms.

The Program Director can then wait for the correlated reply.

Do not put decision logic in the bridge.
It transports requests/replies only.

The bridge must not use the AlienIntent product attention queue unless existing authority explicitly says that queue is appropriate. Keep post-Wave-1 orchestration messages separate from product/runtime attention.

## Program Director behavior

The Program Director must:

1. Read `AGENTS.md`, repository operations authority, program state and current Git state on start.
2. Determine the next unblocked program task.
3. Choose actor:
   - Codex primary by default.
   - Claude independent review where required.
4. Generate/save the exact task prompt before launch.
5. Launch one bounded worker session.
6. Verify terminal result structurally.
7. Verify repository effects where applicable.
8. Request independent review when the program phase requires it.
9. Reconcile review findings.
10. Update program-state and ledger.
11. Stop at Founder decisions instead of inventing authority.
12. Never release BIUs or change Project lifecycle unless separately authorized under canonical AlienIntent authority.

## Immediate first task after bootstrap

Do NOT start Phase 2 automatically.

The existing Phase 0+1 Codex result must first receive the planned independent Claude review.

The Program Director's first orchestrated action is therefore:

    TASK: Wave 1 Closure/Evidence Independent Review
    ACTOR: current Claude bootstrap coordinator
    INPUT:
        Codex closure/evidence artifacts at current main
    OUTPUT:
        PASS
        PASS_WITH_QUALIFICATIONS
        or REPAIR_REQUIRED

Only after that review is closed may the Program Director schedule Phase 2.

## Founder decisions

The local Program Director must surface Founder decisions through a durable `FOUNDER_DECISION_REQUIRED` program task and stop the affected branch of work.

It may continue unrelated analytical work if dependencies allow.

It must not decide:
- new Product priority;
- new Wave assignment;
- material architecture direction;
- unresolved security/deployment policy;
- requirement weakening;
- whether a genuinely new Product Requirement should be adopted.

It may recommend.

## Independence rules

For primary-author + reviewer pairs:

- reviewer must read authoritative evidence directly;
- reviewer must not receive author's private reasoning;
- final reports/artifacts are allowed;
- disagreement is resolved from evidence, not model seniority;
- Claude memory is a locator, not authority;
- Codex fresh-context ignorance is useful evidence of durability gaps.

## Repository closure

Any repository changes made to bootstrap this local orchestration role must follow Repository Change Closure.

Prefer one narrow docs/tooling change.

Do not modify:
- Wave 1 historical evidence except factual correction;
- lifecycle state;
- Project state;
- runtime worker contracts;
- Node/B-DISP semantics;
- Wave 2 requirements as part of the orchestration bootstrap.

## Validation

Prove end-to-end with a harmless synthetic orchestration task:

1. Program Director sends a synthetic review request to the current Claude coordinator.
2. Claude coordinator is awakened through the chosen bridge.
3. Claude writes a correlated reply.
4. Program Director receives it.
5. No duplicate message is processed.
6. Restart the Program Director and prove it reconstructs task state.
7. Launch a harmless read-only fresh Codex session through the wrapper and capture its terminal report.
8. No lifecycle or Product state changes.

Do not call the bootstrap complete until both Codex spawning and Claude direct messaging are proven.

## Report

Report:

- artifacts created;
- Codex launcher path and validated invocation shape;
- how GPT-6 Astra selection is resolved;
- Claude fresh-session launcher path if created;
- direct bridge mechanism selected;
- whether an existing peer mechanism was reused or fallback mailbox created;
- current Claude coordinator endpoint/identity without exposing secrets;
- synthetic round-trip proof;
- restart/reconstruction proof;
- permission/sandbox defaults;
- current program-state;
- first real task queued;
- final repo SHA / remote read-back;
- confirmation no AlienIntent lifecycle/Product state was modified.
