# Work unit: READY selection, release gate and configurable WIP admission

**Label:** `READY-SELECTION-RELEASE-GATE-WIP-ADMISSION` (a document label; the permanent id is allocated when this draft is registered).
**Status:** Draft revision 1 for independent review, 2026-10-03. Not approved, not assessed, not released.
**Position on the path:** unit 6b of the Founder's split of row 6 (6a authorization consistent with launch — landed `main` `16d3156`; 6b this unit; 6c worker launch, worker instructions, context delivery and shared model routing).
**Roles:** one PRODUCER (self-reviews the complete diff); one fresh VERIFIER on the exact candidate; a separate CLOSURE owner lands it.

## 0. The whole design (plain English)

The existing `FactoryCoordinator` already selects the next eligible READY work item, runs the release gate before a PRODUCER, and records each work item's workflow transitions (IMPLEMENT → VERIFY → REVIEW → ACCEPT → DONE, and VERIFY → IMPLEMENT on rejection) in its own store. Nothing connects it to the work registry, and it has no limit on how many work items are in progress at once: it serializes only one running invocation per repository (`factory_coordinator.py` line 287). This unit:
1. **Connects** the work registry's READY view to the existing coordinator through the existing release gate, on the work registry's store, with the release gate checking the starting revision in the same repository and release point that `work authorize` checks.
2. **Adds configurable WIP admission:** a work item takes one WIP slot when it is first admitted to IMPLEMENT and keeps it through every PRODUCER and VERIFIER cycle until it is DONE or terminally stopped. WIP counts work items, not worker processes. The limit is read from the shared configuration source; 1 is the starting setting and the design supports N.
3. **Records IMPLEMENT and VERIFY cycle counts** in the coordinator's existing transitions, and `work display` shows them from that state.

Worker launching, worker instructions, context delivery and model routing stay in unit 6c: this unit composes the coordinator with a worker supplied by its caller.

## 1. Configurable WIP admission

- **What is counted.** One WIP slot per work item in progress — from its first admission to IMPLEMENT until it reaches DONE or a terminal outcome (`failure`, `timeout`, `authority-block`, `blocked-by-authority`, `cancelled-by-operator`, `cancelled-by-decision`). Moving the work item from PRODUCER to VERIFIER, a VERIFY rejection back to IMPLEMENT, and REVIEW/ACCEPT/CLOSURE invocations all keep the same slot.
- **Atomic reservation.** One new store operation, `acquire_within(profile, scope, owner, limit)` on the `OperationalStore` port and `SQLiteOperationalStore`, does in one `BEGIN IMMEDIATE` transaction: if `owner` already holds a reservation in `scope`, return it; else if the number of reservations in `scope` is at least `limit`, raise the existing `ReservationRejected`; else insert one reservation with the first free key `slot-1`, `slot-2`, … and a new fence, exactly as `acquire` does. Two simultaneous admissions therefore can never both take the last free slot.
- **Where.** In `FactoryCoordinator._run`, for a PRODUCER invocation of a work item that holds no WIP slot yet, after the release gate passes and before the existing per-repository reservation: `acquire_within(profile, "wip", "work:<identity>", limit)`. A refusal returns the existing `StopReason.CAPACITY_UNAVAILABLE`; the work item stays eligible for a later run. A work item that already holds its slot is never admitted again.
- **Release.** When the coordinator records DONE or a terminal outcome for the work item, it releases that work item's WIP reservation with its fence, in the same step that records the result.
- **The limit.** Read from the shared configuration source on every admission: `~/.config/alienintent/factory-director-host.json` key `wipLimit`, with the same rules the Node runtime applies (`bin/alienintent.mjs` lines 30–40): not a positive integer, missing file or unreadable → no admission (`WIP_LIMIT_UNAVAILABLE`); the coordinator receives it as a callable `wip_limit() -> int | None` supplied by composition. A coordinator built without `wip_limit` (the sandbox and other existing profiles) keeps its current behaviour exactly.
- **Lowering the limit** stops new admissions while the number of held slots is at or above the new limit; it never releases or stops a slot already held.
- **Restart.** `_recover` keeps `wip` reservations owned by `work:<identity>` as durable admissions (today it refuses to start on any reservation that is not a per-repository launch): for each, a work item already at DONE or a terminal outcome has its slot released; any other keeps it and counts toward the limit. Because admission first checks whether the owner already holds a slot, restart never admits a work item twice.
- **Solve for N** (`docs/architecture/alienintent-40-architecture-recommendations.md` line 15; architecture authority A3) is preserved: choosing the best concurrency level is separate work; this unit only enforces the configured limit.

## 2. READY selection and the release gate for the work registry

`WorkRegistry.coordinator(worker, artifacts)` (`composition/work_registry.py`, present when the `github` and `readiness` entries are) returns a `FactoryCoordinator` with: the readiness store, `work = WorkRegistry.ready_view`, the caller's `worker` and `artifacts` (supplied by unit 6c), `profile = "registry"`, `automatic_release = False` (a registry work item starts only with its release record), the existing `ReleasePreconditionGate` on `StoredReleaseAuthorizations(<readiness store>, "registry")`, and `wip_limit`. The release gate's `GitRevisionResolver` maps the READY row's `repository` (the GitHub repository) to the clone of the pointer's repository, and its release point is that repository's configured `default_branch` — the same repository and release point `work authorize` checks, so authorization and launch cannot disagree on the starting revision.

## 3. Cycle counts

`ExecutionState` (`execution_coordination/domain/lifecycle.py`) gains `implement_cycles` and `verify_cycles`, set by the existing `transition`: a new state (first entry to IMPLEMENT) has `implement_cycles = 1`; the `rework` transition (VERIFY → IMPLEMENT) adds 1 to `implement_cycles`; the `verify` transition (IMPLEMENT → VERIFY) adds 1 to `verify_cycles`. They are encoded and decoded with the coordinator's state and change only with a recorded transition: retries, duplicate events, restarts and display repairs never change them, because none of them commits a transition. `work display` renders, for a work item the registry coordinator has state for, one more body line `IMPLEMENT cycles: <n> · VERIFY cycles: <m>` read from that state through a callable supplied by composition; a work item with no coordinator state renders exactly as today.

## 4. Exact permitted files

Production: `src/alienintent/execution_coordination/ports/operational_store.py` and `src/alienintent/execution_coordination/adapters/sqlite_store.py` (`acquire_within`), `src/alienintent/execution_coordination/application/factory_coordinator.py` (admission, release, recovery, count encoding), `src/alienintent/execution_coordination/domain/lifecycle.py` (counts in `ExecutionState` and `transition`), `src/alienintent/composition/work_registry.py` (`coordinator`, limit reader, count reader for display), `src/alienintent/context_assembly/domain/work_link.py` and `src/alienintent/context_assembly/application/work_link.py` (the count line). Tests: `tests/execution_coordination/test_operational_store.py`, `tests/execution_coordination/test_factory_coordinator.py`, `tests/composition/test_work_registry.py`, `tests/context_assembly/test_work_link.py`, `tests/composition/test_lifecycle_capstone.py` (only if the new state fields require it).

## 5. Acceptance checks (each names the wrong implementation it catches)

1. **Work items, not processes.** With limit 1, work item A admitted and moved PRODUCER → VERIFIER → rejected → PRODUCER keeps one slot throughout; B is refused `CAPACITY_UNAVAILABLE` until A is DONE or terminal, then admitted. Catches a slot freed between PRODUCER and VERIFIER.
2. **Atomic admission.** Two admissions interleaved inside `acquire_within`'s caller with one free slot → exactly one reservation; the other is refused. Catches a check-then-reserve race.
3. **N.** With limit 3, three work items are admitted and the fourth is refused; changing the shared file's `wipLimit` takes effect at the next admission. Catches a hard-coded 1.
4. **Lowering.** Three held slots, limit lowered to 1 → no new admission; the three continue to their outcomes; admission resumes only when fewer than 1 slot is held. Catches stopping running work or admitting above the new limit.
5. **Limit unavailable.** Missing file, non-positive or non-integer `wipLimit` → no admission, answered `WIP_LIMIT_UNAVAILABLE`. Catches a default limit.
6. **Restart.** A store with held `wip` slots and no per-repository reservation: a new coordinator starts, keeps the slots, admits no work item twice, and releases the slot of a work item already DONE. Catches recovery that refuses to start or duplicates admissions.
7. **Release gate for registry work items.** A READY-view work item with a valid release record passes the release gate on the registry store with the pointer repository's clone and default branch; without a release record, with another starting revision, or with an unreachable one, it is refused `authority-block` and nothing is launched. Catches a gate on the wrong store, repository or release point.
8. **Cycle counts.** Rework twice → `implement_cycles = 3`, `verify_cycles = 2`; a retried PRODUCER attempt, a duplicate outcome, a coordinator restart and a `work display` repair change neither; `work display` shows the line from the coordinator state and an item with no state renders as before. Catches counts changed outside transitions or computed by the display.
9. **Unchanged profiles.** The sandbox and other existing coordinator tests pass unchanged; the test files above and `check_architecture.py --check all` pass.

## 6. Excluded

Launching workers for the work registry, worker instructions, context delivery and model routing (unit 6c); changing the release gate's rules; choosing the best WIP level (Solve for N); board Status projection; changing `work_item.state`; changing earlier packets.

## 7. Review record

**Revision 1 (2026-10-03).** First draft, against `main` `16d3156`, with the Founder's direction: WIP counts active work items, not worker processes; admission reserves capacity atomically; restart recovers existing reservations without duplicates; cycle counts reuse the coordinator's transitions; worker launching and context delivery stay in unit 6c.
