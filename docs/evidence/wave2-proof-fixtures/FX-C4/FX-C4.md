# FX-C4 — monitor ticks and scan health

**Owner:** `WO-220304` / DAG node `C4` (`monitor_health_core`), Issue #96.
**Proof level:** `LOCAL_COMPOSED_OR_MECHANICAL`. **Live proof:** `NOT_ESTABLISHED`.

This is a disposable local service/inspection fixture for the pinned FX-C4 proof
packet in `docs/work-units/wave2/WO-220304.md` (sha256
`9cdc643d3f699a6adc7446d78459663ca30561f87bf4a9d04225562962c9036a`). It does not
host, supervise, restart or alert on anything, and it performs no live action. The
host remains unassigned (`R1-GAP-MONITOR-HOST`).

## Implemented surface

- `control_plane/domain/monitor_health.py`: `MonitorPolicy` (I only, positive and
  finite, with a `policy_digest`), `MonitorHealth` (exactly the
  `#/shared_contracts/monitor_liveness` record fields), `HealthStatus` and the pure
  ordered `classify` rule.
- `control_plane/ports/monitor_health.py`: `MonitorHealthPort.read(profile) ->
  MonitorHealth | None | Unavailable` and the versioned repository port. Labelled
  deviation from the pinned `MonitorHealth | Unavailable`: `None` means "no record"
  (classified UNVERIFIED `NO_RECORD`). `Unavailable` is kept for an unreadable
  store, schema or history, so the pinned rule can tell these cases apart.
- `control_plane/application/monitor_health.py`: `MonitorService.start`, `tick`,
  `scan_started`, `scan_finished(outcome)` and read-only `inspect`.
- `control_plane/adapters/monitor_health_repository.py`: immutable
  `monitor-history` observations in the S1 evidence repository first, then the
  versioned `monitor:<profile>` pointer by `SQLiteOperationalStore` CAS.
- `execution_coordination/ports/scan_progress.py`: the scan-progress port owned by
  execution coordination (`ScanOutcome` COMPLETE/FAILED/EVIDENCE_HOLD). C4 drives it
  from an injected fake scanner only.
- `composition/control_plane_profile.py`: `MonitorProfile`; `AttentionProfile` is
  unchanged. Constructing the profile starts nothing.

## Pinned local choices

- Times are integer UTC microseconds since the Unix epoch from an injected clock.
  `None` is an absent clock, a raising clock is unreadable, and any other non-integer
  or negative reading is invalid. All are UNVERIFIED and refuse writes. Boundaries
  are exact: `2*I` is computed as a `Fraction`.
- `SCAN_AGE_FROM_LAST_COMPLETION` (U3): `now - last_scan_completed_at > 2*I` is
  STALE, and exactly `2*I` is in bound. `next_scan_due` is recorded and is not used
  for classification. A generation with no completed scan (or no tick) yet is
  measured from its `started_at`.
- U4 order: store unreadable (`Unavailable`) → absent/unreadable/invalid clock → no
  record → policy digest mismatch → clock earlier than the latest persisted
  observation (U5) are UNVERIFIED; then tick-age STALE; then scan-age STALE; then
  STARTED/FAILED/EVIDENCE_HOLD latest scan is DEGRADED; otherwise HEALTHY.
- Writes use the same U5 reference. A tick, scan or restart with a clock earlier
  than the latest persisted observation is refused with `CLOCK_REGRESSION`, and
  nothing is written.
- `scan_finished` requires a started attempt. Only COMPLETE advances
  `last_scan_completed_at`. FAILED and EVIDENCE_HOLD keep their error as
  `last_error`. `active_work` is retained in the history observation and never
  affects health.
- Restart (`start` on an existing record) allocates a new injected `instance_id`
  and `generation + 1`. The history chain continues across generations, so earlier
  observations remain readable. A service writes only to the instance/generation it
  started. A service that never started, or whose instance was superseded, is
  refused (`NOT_STARTED` / `STALE_INSTANCE`), so a stale process cannot keep a newer
  generation looking healthy. Inspection needs no started instance.
- A missing, schema-incompatible or malformed pointer, or a broken history object,
  reads as `Unavailable` and is classified UNVERIFIED. It never raises out of `inspect`.
- `LOCAL_EPISODE_END_STAND_IN` (U2): an episode ends by discarding every
  service/activation object (the monitor profile and an attention profile holding a
  model-launch spy) and reopening from the store. The pointer, version and history
  must be identical, and the spy count must be 0. This is not C3 EpisodeControl.
  `MonitorProfile` accepts no activation capability, so no monitor code path can
  reach the spy. The zero count is a measured local observation of that
  composition; it is not provider telemetry.

## Commands

Run all commands under `rtk proxy` with `PYTHONPATH=src` from a clean checkout of the candidate.

1. `python3 -B -m pytest -q tests/control_plane/test_monitor_health.py`
2. `python3 -B tools/evidence/fx_c4_evidence.py --output /tmp/fx-c4-<run-id> --invocation <exact-invocation>`. The output directory must be new.
3. `python3 -B -m pytest -q`; `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`; `python3 -B -m pytest -q tests/test_architecture_fitness.py`; `node scripts/check.mjs all`.

Command 2 runs command 1 and every command in 3. It then applies each control in
`CONTROLS` exactly once in a disposable source copy, recording intact 0, fault 1
with the named assertion, and restored 0. There are the 18 pinned controls plus
`stale_instance_accepted`, which the producer added after preparatory review. The
`adapter_import_added` control uses the architecture check instead of pytest. Finally it performs a
composed readback of the `monitor:` aggregate and the `monitor-history` objects.

## Evidence

In this directory, following the FX-C1 conventions:

- `execution-record.json`: `ProofFixtureExecution`, `schema_version: 1`.
- `run-report.json`: maps each acceptance clause to node ids, and holds the composed readback.
- `proven-red.json`: the 19 controls with their intact, fault and restored results.
- `observations/`, named by sha256 and written with `xb`.
- `digest-manifest.json`.

Any dirty source, failed command, non-discriminating control or missing readback
is recorded as a HOLD, never as a PASS. Tokens, cost and provider calls are `null`
with reason `UNKNOWN`. `development-run/` holds a pre-commit run whose source was
dirty. It is kept as history, and it is not acceptance evidence.

## Preparatory review

Before the source was committed, a separate read-only reviewer found one important
issue: writes were not bound to the writer's own instance. After a restart, a
superseded process could keep ticking the new generation and make it look HEALTHY.
The reviewer also found several minor issues:

- a malformed pointer raised out of `inspect`;
- the zero/NaN policy cases never reached `start()`;
- the port's `None` return and the spy's reach were not documented.

All of these are repaired above and covered by `test_stale_instance_cannot_write`,
`test_malformed_pointer_unverified` and the revised `test_policy_invalid_blocks_start`.
This review is preparatory. It is not the fresh BIU verifier verdict.
