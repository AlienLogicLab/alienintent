# Actor-launch liveness reconciliation — SWF-29

Date: 2026-09-20. Status: **Founder decision — binding**. Part 1 is temporary and expiring; part 2 is durable product authority.
Source: direct Founder instruction, and [PROP-2026-0006](../proposals/PROP-2026-0006-deterministic-actor-launch-liveness-reconciliation.md) (`authority_level: founder`, `requested_priority: P0`, `requested_wave: 2`).

## Motivating incident

During PY-06 the BIU transitioned to `VERIFY` after the producer successfully published candidate `d9537d1e`. The triggering webhook delivery never arrived, so no VERIFIER was launched. The dispatcher and tunnel stayed healthy, the candidate was published and retrievable, and no worker crashed. The BIU sat inert for ~28 minutes until the coordinator was asked to inspect it; an authorized operator transition regenerated the event and the verifier started immediately.

> Durable lifecycle state required an actor, but no corresponding actor existed and no deterministic mechanism detected the inconsistency.

## Part 1 — Temporary bootstrap liveness responsibility

The bootstrap coordinator is explicitly authorized and responsible for enforcing the 5-minute actor-launch rule until the canonical Python capability exists. The operative rule, procedure, hard rules and evidence obligations are recorded in **[docs/operations.md § Bootstrap liveness reconciliation (temporary)](../operations.md)**.

Summary: IMPLEMENT expects a PRODUCER, VERIFY expects a VERIFIER, ACCEPT expects the required closure action where the contract requires closure work. Every 5 minutes, only active nonterminal BIUs already known to the coordinator are inspected — never a backlog query for new work. A state at least 5 minutes old with no matching active invocation, pending claim/effect, or correlated completion awaiting projection is classified `LIVENESS_GAP` and reconciled through the narrowest already-authorized idempotent mechanism, with durable evidence.

**This responsibility expires when the canonical Python liveness capability (SF-REQ-056) replaces it.** It must not silently become permanent architecture — the same rule applied to SWF-21 and enforced against SWF-26.

For PY-06 specifically, the running verifier/worker is not disturbed; the motivating incident was already recovered before this rule took effect.

### Duplicate prevention: what actually guarantees it, and what does not

The watcher's evidence check (no active invocation, no lane claim, no live worker, nothing newer than the grace window) **reduces unnecessary re-emissions; it does not by itself prevent duplicates.** A delayed original delivery can still arrive after the check and before the re-emission is processed.

**What does prevent duplication** is the Node bootstrap's own claim identity — the **lane** `repository#issue:ROLE`:

- the fresh-claim path performs a **synchronous check-and-reserve**, carrying the invariant *"no await may separate the lane guard and save"* (`src/runtime/dispatcher.mjs`), so two deliveries cannot both pass the guard;
- the FOUNDER_EXCEPTION recovery path **re-reads durable state after its awaits**, explicitly so that *"competing operator deliveries cannot reserve two workers"*;
- a second event for an already-claimed lane is rejected with `ACTIVE_INVOCATION_EXISTS`.

**Known limitations, recorded rather than implied away:**

1. **Delivery-id dedupe does not cover re-emission.** `state.deliveries` is keyed on `x-github-delivery`; a re-emitted transition carries a *new* delivery id, so the original and the re-emission are distinct deliveries. Only the lane claim collapses them.
2. **Prevention is single-process.** The lane guard consults an in-memory map alongside durable state; a second dispatcher instance would not share it, and the state file is not fenced across processes. This bootstrap runs exactly one dispatcher, which is what makes the guarantee hold.
3. **The watcher cannot close the window itself.** It re-verifies the lane claim immediately before transitioning to narrow it, and verifies afterwards that exactly one claim exists, logging `DUPLICATE_SUSPECTED` if not — detection, not prevention.
4. **Status re-emission is not idempotent in its own right.** It is idempotent only because the dispatcher refuses a second claim for a claimed lane.

SF-REQ-056 requires the canonical Python capability to make recovery idempotent and fenced by durable correlation/effect identity, which is what closes this properly. Until then the guarantee is the bootstrap's, not the watcher's.

## Part 2 — PROP-2026-0006 canonicalized as SF-REQ-056

### Overlap analysis

- **SF-REQ-001 continuous factory execution** (#3, P0, Wave 1) — states the *goal* ("continuously executes until the eligible backlog is exhausted, blocked, or requires human authority"). A liveness gap violates that goal but SF-REQ-001 defines no state→actor consistency check, grace period or reconciliation obligation.
- **SF-REQ-008 crash-safe execution** (#10, P0, Wave 1) — supplies the *mechanisms* this capability reuses: inbox/effect-intent/outbox, expected versions, fencing, idempotency and reconciliation. Its subject is preserving state across crashes and restarts, not detecting an actor that was never launched when no crash occurred.

### Why a new requirement rather than an amendment

Amendment was preferred and was assessed first. It is rejected for one decisive reason: **SF-REQ-001 and SF-REQ-008 are both Wave 1 and already partly implemented** (PY-04 landed the coordinator loop, PY-05 the durable ingress). Folding a Wave 2 obligation with ten acceptance criteria into a Wave 1 requirement would create exactly the retrofit ambiguity PROP-2026-0006 forbids — it explicitly does not retrofit running Wave 1 BIUs. A separate requirement keeps one clear canonical owner for the capability and a clean wave boundary. SF-REQ-001 and SF-REQ-008 are **not amended** and are cross-referenced instead.

### Binding semantics preserved in SF-REQ-056

- no nonterminal lifecycle state may depend indefinitely on one transient delivery;
- state→expected-actor/effect consistency is deterministically checked;
- 5 minutes is the temporary bootstrap grace period; canonical Python grace is configurable;
- recovery is idempotent/fenced and duplicate-safe;
- this is liveness reconciliation, not work-discovery polling;
- permanent recovery must not depend on status toggling;
- meaningful negative-control / proven-red evidence is required.

### Placement

**SF-REQ-056**, Priority **P0**, Wave **2**, CAPTURE, under this Founder authority. No BIU is created and no implementation is authorized.

## Scope

No live Wave 1 lifecycle state is otherwise changed, no Node/B-DISP product semantics are altered, and no running invocation is disturbed.
