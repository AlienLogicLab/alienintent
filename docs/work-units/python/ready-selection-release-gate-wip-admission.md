# Work unit: READY selection, release gate and configurable WIP admission

**Label:** `READY-SELECTION-RELEASE-GATE-WIP-ADMISSION` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 2 (work item `cbfd45ee-3020-40ca-853e-d15d3baf82b4`, at CAPTURE) for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** unit 6b of the Founder's split of row 6 (6a authorization consistent with launch — landed `main` `16d3156`; 6b this unit; 6c worker launch, worker instructions, context delivery and shared model routing).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## Contract

```json alienintent-contract
{
 "identity": "cbfd45ee-3020-40ca-853e-d15d3baf82b4",
 "version": "revision-2",
 "intent": "Connect the work registry's READY view to the existing FactoryCoordinator through the existing release gate on the work registry's store, add configurable WIP admission that counts active work items atomically and survives restart, and record IMPLEMENT and VERIFY cycle counts in the coordinator's existing transitions, displayed by work display.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-02: WIP is configurable; 1 is the starting setting; the implementation supports N; Solve for N stays separate.",
  "Founder 2026-10-03: WIP counts active work items, not worker processes; moving PRODUCER to VERIFIER keeps the slot; admission reserves capacity atomically; restart recovers reservations without duplicate admissions.",
  "Founder 2026-10-02: cycle counts belong with the recorded coordinator transitions and are displayed from that state.",
  "Worker launching, worker instructions, context delivery and model routing are unit 6c.",
  "This unit supersedes the path plan section 4A bullet that put cycle counts on work_item: they live in the coordinator state and change in the same commit as the transition.",
  "Founder 2026-10-03: a WIP slot is released only on a recorded DONE or an authorized final stop; the shared wipLimit reaches Python only through runtime configuration injection, with no cached copy."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/ports/operational_store.py",
  "src/alienintent/execution_coordination/adapters/sqlite_store.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/execution_coordination/domain/lifecycle.py",
  "src/alienintent/composition/work_registry.py",
  "src/alienintent/context_assembly/domain/work_link.py",
  "src/alienintent/context_assembly/application/work_link.py",
  "tests/execution_coordination/test_operational_store.py",
  "tests/execution_coordination/test_factory_coordinator.py",
  "tests/composition/test_work_registry.py",
  "tests/context_assembly/test_work_link.py",
  "tests/composition/test_lifecycle_capstone.py"
 ],
 "excluded_scope": [
  "launching workers for the work registry",
  "worker instructions, context delivery and model routing",
  "changing the release gate's rules",
  "choosing the best WIP level",
  "board Status projection",
  "changing work_item.state",
  "changing earlier packets"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "sqlite"
 ],
 "budget_policy": {
  "maximum_attempts": 3
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-9 pass",
  "architecture fitness passes"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation"
 ],
 "required_evidence": [
  "VERIFIER verdict file",
  "landing record on main"
 ],
 "non_goals": [
  "Solve for N concurrency selection",
  "worker launch"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by direct merge preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/python-execution-path-20260930.md row 6 (Founder split 2026-10-02, unit 6b) and section 4A"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "direct merge to main",
  "landing record in docs/evidence",
  "remove temporary PRODUCER and VERIFIER worktrees"
 ],
 "stop_escalation_conditions": [
  "a landed interface does not match the packet",
  "an existing profile's behaviour would change",
  "scope outside the authorized files",
  "a READY work item whose pointer is in a repository other than the packets repository"
 ]
}
```

## 0. The whole design (plain English)

The existing `FactoryCoordinator` already selects the next eligible READY work item, runs the release gate before a PRODUCER, and records each work item's workflow transitions (IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE, and VERIFY → IMPLEMENT on rejection) in its own store. Nothing connects it to the work registry, and it has no limit on how many work items are in progress at once: it serializes only one running invocation per repository (`factory_coordinator.py` line 287). This unit:
1. **Connects** the work registry's READY view to the existing coordinator through the existing release gate, on the work registry's store, with the release gate checking the starting revision in the same repository and release point that `work authorize` checks.
2. **Adds configurable WIP admission:** a work item takes one WIP slot when it is first admitted to IMPLEMENT and keeps it through every PRODUCER and VERIFIER cycle until it is DONE or terminally stopped. WIP counts work items, not worker processes. The limit is read from the shared configuration source; 1 is the starting setting and the design supports N.
3. **Records IMPLEMENT and VERIFY cycle counts** in the coordinator's existing transitions, and `work display` shows them from that state.

Worker launching, worker instructions, context delivery and model routing stay in unit 6c: this unit composes the coordinator with a worker supplied by its caller.

## 1. Configurable WIP admission

- **What is counted.** One WIP slot per work item in progress, from its first admission to IMPLEMENT until it reaches DONE or a **final** outcome: `failure`, `timeout`, `cancelled-by-operator`, `cancelled-by-decision`. `authority-block` and `blocked-by-authority` are holds that a Founder decision can resume (`factory_coordinator.py` lines 647–658, 674–675, 248), so the work item keeps its slot through them; with WIP=1 an authority-blocked work item therefore holds the factory until the Founder authorizes, defers or cancels it. Moving the work item from PRODUCER to VERIFIER, a rejection back to IMPLEMENT, and REVIEW/ACCEPT/CLOSURE invocations all keep the same slot. Escalations, parked unknown effects (recorded as `authority-block`), crashes and restarts never release a slot.
- **WIP N is work items in progress, not parallel workers.** Invocations stay serialized one per repository (the existing reservation, line 287); worker parallelism belongs to unit 6c and Solve for N.
- **Atomic reservation.** One new store operation, `acquire_within(profile, scope, key, owner, limit)` on the `OperationalStore` port and `SQLiteOperationalStore`, does in one `BEGIN IMMEDIATE` transaction: if a reservation with this `key` already exists in `scope` for `owner`, return it; else if `COUNT(*)` of reservations in `scope` is at least `limit`, raise the existing `ReservationRejected`; else insert the reservation with a new fence, exactly as `acquire` does. The coordinator uses scope `wip`, key = the work identity, owner `work:<identity>`. Two simultaneous admissions therefore can never both take the last free slot.
- **Where.** In `FactoryCoordinator._run`, for a PRODUCER invocation of a work item that holds no WIP slot yet, after the release gate passes and before the existing per-repository reservation. A work item already holding its slot is never admitted again and needs no limit to continue. A WIP refusal and an unavailable limit are told apart from the per-repository refusal, which still ends the run exactly as today. Both skip that work item for the rest of the run and the run continues with other eligible work items (admitted ones included). At the end, if any work item was skipped for WIP, the run answers `WIP_LIMIT_UNAVAILABLE` when the limit was unavailable, otherwise `CAPACITY_UNAVAILABLE`; with nothing skipped it answers the existing stop reason.
- **The limit — runtime configuration injection only.** The coordinator receives `wip_limit() -> int | None` from composition. Composition's reader opens and parses `~/.config/alienintent/factory-director-host.json` on every call and returns `wipLimit` only when it is an integer ≥ 1 and not a boolean (the rule of `bin/alienintent.mjs` line 33); it returns `None` for a missing, unreadable or invalid file. It does not read `founderHoldRecord` or `pauseFlag` (not this unit). Nothing in Python stores the value between calls, and there is no default. With `None`, no new work item is admitted and the run answers a new `StopReason.WIP_LIMIT_UNAVAILABLE = "wip-limit-unavailable"`; work items already holding a slot continue. A coordinator built without `wip_limit` (the sandbox and other existing profiles) keeps its current behaviour exactly.
- **Lowering the limit** stops new admissions while the number of held slots is at or above the new limit; it never releases or stops a slot already held.
- **Release.** After the recorded DONE or final outcome is read back — in `_record_result`, in `cancel()` and in `record_decision` (cancel), the three places those outcomes are written — the coordinator releases the work item's `wip` reservation, found through `recovery_reservations` by owner `work:<identity>`, with its fence; nothing is released when none is held. The recorded result and the release are separate transactions; a crash between them is completed by `_recover`.
- **Restart.** In `_recover`, `wip` reservations are handled before the existing launch-owner parsing and do not need the work item in the READY snapshot: it reads only `factory:<identity>`; a work item at DONE or a final outcome has its slot released; any other (including `authority-block` and `blocked-by-authority`) keeps it and counts toward the limit. An admitted work item that leaves the READY view keeps its slot until it reaches DONE or a final outcome. Because admission first checks for the work item's own reservation, restart never admits a work item twice.
- **Solve for N** (`docs/architecture/alienintent-40-architecture-recommendations.md` line 15; architecture authority A3) is preserved: choosing the best concurrency level is separate work; this unit only enforces the configured limit.

## 2. READY selection and the release gate for the work registry

`WorkRegistry.coordinator(worker, artifacts)` (`composition/work_registry.py`, present when the `github` and `readiness` entries are) returns a `FactoryCoordinator` with: the readiness store, `work = WorkRegistry.ready_view`, the caller's `worker` and `artifacts` (supplied by unit 6c), `profile = "registry"`, `automatic_release = False`, the existing `ReleasePreconditionGate` on `StoredReleaseAuthorizations(<readiness store>, "registry")`, and `wip_limit`. A registry work item becomes eligible only through the existing `release_and_start(identity)`, which records the coordinator's `release:<identity>` (EXPLICIT_HUMAN); its caller (unit 6c, or the operator's start command) calls it only for a work item `work authorize` has recorded, and the release gate then re-checks that release record before the PRODUCER. The gate is composed for `configuration.packets_repository`: `GitRevisionResolver({github.repository: repositories[packets_repository].clone})` with release point `repositories[packets_repository].default_branch` — the repository and release point `work authorize` checks for every pointer in the packets repository. A READY work item whose pointer is in another repository is a stop condition.

## 3. Cycle counts

`ExecutionState` (`execution_coordination/domain/lifecycle.py`) gains `implement_cycles: int = 1` and `verify_cycles: int = 0`, added after `contract` so existing positional constructors keep working. The existing `transition` sets them: a new state (first entry to IMPLEMENT) has `implement_cycles = 1`; every recorded `rework` (from VERIFY, REVIEW or ACCEPT, including the one recorded with outcome `failure` when the attempt budget is exhausted) adds 1 to `implement_cycles`; every `verify` transition (IMPLEMENT → VERIFY) adds 1 to `verify_cycles`. `_decode` reads them with `.get`, defaulting to 1 and 0 for older records. They change only in the same commit as a recorded transition: retries, duplicate events, restarts and display repairs never change them.

**Display from the authoritative state.** Composition's count reader reads `factory:<identity>` under profile `registry` on the readiness store and decodes it with the coordinator's own decoder (`_decode` made public as `FactoryCoordinator.decode`); with no record it returns `None`. `render(item, cycles=None)` (`context_assembly/domain/work_link.py`) appends the line `IMPLEMENT cycles: <n> · VERIFY cycles: <m>` only when `cycles` is given. Every caller that renders or compares a work item's display passes the same counts from that reader: `WorkLink` (`_create`, `_display`, through a callable it receives) and `WorkRegistry._ready_row`. After a transition the READY view reports `DISPLAY_DIFFERS` until `repair_displays` writes the new counts — expected. A work item with no coordinator state renders exactly as today.

## 4. Exact permitted files

Production: `src/alienintent/execution_coordination/ports/operational_store.py` and `src/alienintent/execution_coordination/adapters/sqlite_store.py` (`acquire_within`), `src/alienintent/execution_coordination/application/factory_coordinator.py` (admission, release in `_record_result`/`cancel`/`record_decision`, recovery, count encoding, public `decode`, `WIP_LIMIT_UNAVAILABLE`), `src/alienintent/execution_coordination/domain/lifecycle.py` (counts in `ExecutionState` and `transition`), `src/alienintent/composition/work_registry.py` (`coordinator`, limit reader, count reader for display), `src/alienintent/context_assembly/domain/work_link.py` and `src/alienintent/context_assembly/application/work_link.py` (the count line). Tests: `tests/execution_coordination/test_operational_store.py`, `tests/execution_coordination/test_factory_coordinator.py`, `tests/composition/test_work_registry.py`, `tests/context_assembly/test_work_link.py`, `tests/composition/test_lifecycle_capstone.py` (only if the new state fields require it).

## 5. Acceptance checks (each names the wrong implementation it catches)

1. **Work items, not processes.** With limit 1, work item A is admitted and moves PRODUCER → VERIFIER → rejected → PRODUCER keeping one slot; B ranks before A in READY order and is refused, the run continues, and A still completes VERIFY while B waits; after A is DONE, B is admitted. Catches a slot freed between PRODUCER and VERIFIER, and a refusal that stalls admitted work.
2. **Atomic admission.** Two `SQLiteOperationalStore` instances on one database file, racing `acquire_within` with one free slot → exactly one reservation; the other gets `ReservationRejected`. Catches a check-then-reserve race.
3. **N.** With limit 3, three work items are admitted and the fourth is refused; changing the shared file's `wipLimit` takes effect at the next admission. Catches a hard-coded 1.
4. **Lowering.** Three held slots, limit lowered to 1 → no new admission; the three continue to their outcomes; admission resumes only when fewer than 1 slot is held. Catches stopping running work or admitting above the new limit.
5. **Limit unavailable.** Missing file, non-positive, non-integer or boolean `wipLimit` → no admission, answered `WIP_LIMIT_UNAVAILABLE`; a work item already holding a slot continues; a later change to the file is seen at the next admission (nothing cached). Catches a default or a cached limit.
6. **Holds and restart.** An admitted work item at `authority-block` keeps its slot, keeps it across a restart, and still holds it after an authorize decision resumes it at VERIFY. A store with held `wip` slots and no per-repository reservation: a new coordinator starts, keeps the slots (including one whose work item is no longer in the READY snapshot), admits no work item twice, and releases the slot of a work item already DONE or at a final outcome, including after a crash between the recorded result and the release. Catches releasing on resumable holds, recovery that refuses to start, and duplicate admissions.
7. **Release gate for registry work items.** Through `release_and_start`, a READY-view work item with a valid release record passes the release gate on the registry store with the packets repository's clone and default branch; without a release record, with another starting revision or with an unreachable one, it is refused `authority-block` and nothing is launched; without `release_and_start` it is never selected. Catches a gate on the wrong store, repository or release point, and admission without the Founder's release.
8. **Cycle counts.** Rework twice → `implement_cycles = 3`, `verify_cycles = 2`; a retried PRODUCER attempt, a duplicate outcome, a coordinator restart and a `work display` repair change neither; an older record decodes to 1 and 0; `work display` shows the line from the coordinator state, the next READY snapshot after `repair_displays` reports no `DISPLAY_DIFFERS` for that work item, and a work item with no state renders as before. Catches counts changed outside transitions, computed by the display, or a display that differs for ever.
9. **Unchanged profiles.** The sandbox and other existing coordinator tests pass unchanged; the test files above and `check_architecture.py --check all` pass.

## 6. Excluded

Launching workers for the work registry, worker instructions, context delivery and model routing (unit 6c); changing the release gate's rules; choosing the best WIP level (Solve for N); board Status projection; changing `work_item.state`; changing earlier packets.

## 7. Review record

**Revision 2b (2026-10-03).** The REVIEWER's recheck: one sentence states the run's answer for WIP refusals and an unavailable limit, separate from the per-repository refusal.

**Revision 2 (2026-10-03).** The REVIEWER's review of `a4812b4` (FAIL, text only) and the Founder's two points: a slot is released only on DONE or a final outcome, never on resumable holds (`authority-block`, `blocked-by-authority`); the wipLimit reader is injected, reads the file every call, caches nothing; registry work items become eligible through `release_and_start`; a WIP refusal no longer ends the run; one `render(item, cycles)` for every display caller; the release gate is composed for the packets repository; release in all three writers and in recovery; count defaults and the public decoder; reservation key = work identity; WIP N is work items, not parallel workers.

**Revision 1 (2026-10-03).** First draft, against `main` `16d3156`, with the Founder's direction: WIP counts active work items, not worker processes; admission reserves capacity atomically; restart recovers existing reservations without duplicates; cycle counts reuse the coordinator's transitions; worker launching and context delivery stay in unit 6c.
