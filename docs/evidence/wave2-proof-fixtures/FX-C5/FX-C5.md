# FX-C5 — independently supervised monitor host (WO-220305, SF-REQ-053/056)

**Owner:** `WO-220305` / DAG node `C5` (`supervised_monitor_host`), Issue #114, under the existing SWF-27 /
SF-REQ-053 ownership of persistent deterministic monitoring.
**Proof level:** `LOCAL_COMPOSED_OR_MECHANICAL`. **Live proof:** `NOT_ESTABLISHED`.

- **Contract input:** `docs/work-units/wave2/WO-220305.md`, sha256
  `eced974bf8636a135f1c7cf26933d58c8acef2b8599f01da332dc01daf047d23`. This is the exact input of the native READY
  assessment `WO-220305.2026-09-25T115944.821126Z`.
- **Proof packet:** `docs/evidence/wave2-execution-packets/WO-220305.proof-packet.md`, sha256
  `21342f10c315f099042c9f6bc21da58a9620ffe6b8a2d0962d82604a9581a361`.
- **Release baseline:** `9cf86c959e60163631d49cefa778ad9bf40ff0fb` (Factory Director RELEASED record on Issue #114,
  2026-09-26T05:04:59Z).

## Predecessors composed unchanged

| BIU | Fixture | Accepted candidate | Landing merge |
|---|---|---|---|
| WO-220304 (#96, C4, declared dependency) | FX-C4 | `4c806feb8456c68a590b1482ae340338b7d47c7d` | `3285c9e087b78909501995a662a008e9e0565dc5` |
| WO-220306 (#112, L1, composed scanner) | FX-L1 | `3cac3912ff7f7d17648fc8dcee4ab7195baaefc8` | `1753fde3638c26e47f33d793e59d11a6799ce74b` |

The harness checks that each candidate and landing merge is an ancestor of this candidate. C1 attention enters
through the unchanged `AttentionProfile`. No predecessor source file changes in this BIU.

## What is hosted, and by whom

- **The monitor/scanner process** (`python -m alienintent.composition.monitor_host host`) composes the unchanged
  C4 `MonitorProfile` and L1 `LivenessProfile` over the profile root. It starts C4 generation `n+1` using its launch
  id as the instance id. It starts the L1 reconciler, which reopens durable intents without launching anything, and
  then ticks and scans every `I`.
- **The supervisor** is the per-user systemd manager. It is external to the model session and to the host. The host
  runs as a transient unit `alienintent-monitor-<sha256(profile, host_invocation)[:32]>.service` under `app.slice`.
  The unit is `Type=exec`, `Restart=no`, `KillMode=control-group`, `SendSIGKILL=yes`, and launched with `env -i`.
  This follows the same manager-identity and cgroup discipline as `src/runtime/systemd-supervision.mjs`.
- **The observer** is a manager-owned timer (`alienintent-monitor-observer-<key>.timer`). It runs one `observe`
  every `observe_seconds`. `observe` reads the unit from the manager and reads the durable C4 health record
  externally. It never uses a self-report. On failure it raises one durable alert per failed launch.
- **Restart** is `restart` under an explicit `HostGrant`. The grant names the actor, the host authority, the exact
  unit and monitor invocation, the failed launch id and its alert. Restart never happens automatically: there is no
  nonterminal retry and no budget reset.

`control_plane/domain/monitor_host.py` holds the values and the ordered `detect` rule.
`control_plane/application/monitor_supervision.py` holds `launch`, `observe` and `restart`. The adapters are
`systemd_host_manager.py` (the manager), `monitor_host_repository.py` (the supervisor-owned `monitor-host:<profile>`
record: immutable history first, then a CAS pointer in `monitor-host.sqlite`) and `monitor_host_alerts.py`.

## Pinned local choices

- **Attribution.** The ownership record binds the profile, monitor invocation, unit, description, manager identity
  (uid, boot id, manager start, cgroup), owned cgroup, configuration digest, grant digest and launch id. The first
  observation binds the manager's `InvocationID`; later observations must match it. The C4 record's `instance_id` is
  the launch id, so each generation is attributable to exactly one supervised launch.
- **Hosting.** The host refuses before opening any store unless the ownership record names its launch id
  (`HOST_NOT_OWNED`) and its own `/proc/self/cgroup` is the owned unit's cgroup (`HOST_OUTSIDE_OWNED_UNIT`). A model
  session, a profile constructor or a shell background waiter therefore cannot host the monitor.
- **Detection order** (`detect`):
  1. Identity refusal: unit binding, invocation, cgroup or properties mismatch.
  2. Dead unit: not loaded, not `active/running`, or the manager changed.
  3. Startup window: within `startup_seconds`, and no owned generation yet.
  4. Instance attribution: `INSTANCE_NOT_OWNED`, `GENERATION_NOT_CONTINUOUS`.
  5. C4 health: `STALE` or `UNVERIFIED` fails. `DEGRADED` is scan health and does not raise a host alert.

  A running unit is not health. A stalled (SIGSTOPped) host keeps its unit active, and only the C4 record read
  externally shows it. At exactly `2*I` it is still in bound (the C4 rule).
- **Alert.** The alert is a C1 `JUDGMENT` attention item. Its origin is stable per launch, so every observer of the
  same failed launch names one item. A restart never resolves it: resolution stays with `alert_authority`.
- **Pending state preserved across restart.** The restarted host reopens the same stores, so all of the following
  hold:
  - C4 generation continues `n -> n+1`, and earlier `monitor-history` observations stay an unchanged prefix.
  - L1 known-active records and the persisted liveness policy are identical.
  - The alert stays `PENDING`.
  - A superseded host process cannot write (`STALE_INSTANCE`).
- **Configuration.** `SupervisionConfig` holds mode `systemd`, the monitor invocation, absolute executables, the
  existing root and source directories, positive finite `G/I/C`/startup/stop/observe durations, host actors and
  authorities. It is validated before any unit or record mutation. The manager probe (`MANAGER_UNAVAILABLE`) is also
  checked before any mutation. A configuration naming another invocation cannot observe or restart the host
  (`BINDING_MISMATCH`).
- **Labels:**
  - `REAL_USER_SYSTEMD_MANAGER_LOCAL`: the composed probe used this workstation's per-user manager.
  - `FAKE_MANAGER_FOR_NEGATIVE_CONTROLS`: the controls run on an in-memory manager model.
  - `RESTART_REQUIRES_GRANT_NO_AUTOMATIC_RETRY`.
  - `DOCTOR_CONFIGURATION_SURFACE_NOT_ADDED`: no Doctor check is added. Installation/Doctor configuration stays
    with SF-REQ-037/038. C5 holds on its own supervision configuration and the manager probe only.

## Probes

| Failure class | Mechanical (`tests/control_plane/test_monitor_host.py`) | Composed, real manager (`test_monitor_host_systemd.py`) |
|---|---|---|
| 1. Supervisor external and attributable | `test_launch_binds_the_owned_unit_to_the_monitor_invocation`, `test_host_refuses_to_run_outside_its_owned_unit`, `test_constructing_the_supervisor_launches_nothing` | launch binds `InvocationID` and generation 1; running `host` from the test (session) process exits 3 `HOST_OUTSIDE_OWNED_UNIT` |
| 2. Terminate or stall → detection/alert → restart preserves generation and pending state | `test_stalled_host_is_detected_externally_and_restart_preserves_generation_and_pending_state`, `test_terminated_host_is_detected_from_the_unit_before_health_goes_stale` | SIGSTOP → timer observer alerts `HEALTH_STALE:TICK_OVERDUE` with the unit still `active/running` → granted restart → generation 2. SIGKILL → `UNIT_FAILED_FAILED_SIGNAL` → generation 3. Pending state identical, both alerts `PENDING` |
| 3. Wrong identity refused; no duplicate or substitution | `test_restart_with_wrong_identity_is_refused` (unit, invocation, launch, alert, actor, authority), `test_restart_of_a_healthy_host_or_duplicate_launch_is_refused`, `test_observation_of_a_substituted_unit_or_instance_is_refused`, `test_monitor_instance_not_launched_by_the_supervisor_is_refused` | restart naming another launch → `RESTART_LAUNCH_MISMATCH`, stalled unit untouched |
| 4. Missing/invalid configuration holds before launch/restart | `test_missing_or_invalid_configuration_holds_before_launch` (missing, unparsable, non-systemd mode, missing invocation, zero interval, empty actors, relative executable, absent root), `test_supervisor_without_configuration_or_manager_holds_before_any_mutation`, `test_restart_under_a_changed_configuration_holds` | — |

## Discriminating controls (`tools/evidence/fx_c5_evidence.py`)

There is one control per material failure class. Class 2 has two, because it names two distinct invariants:
external detection and preservation. Each control is applied exactly once in a disposable copy, and the harness
records intact 0 → fault 1 with the named assertion → restored 0.

| Control | Class | Mutation | Fails |
|---|---|---|---|
| `host_outside_unit_accepted` | 1 | drop the host's owned-cgroup check | `test_host_refuses_to_run_outside_its_owned_unit` |
| `stall_trusts_running_unit` | 2 | ignore STALE/UNVERIFIED health when the unit runs | stalled-host test |
| `restart_clean_start` | 2 | a restarted host opens a fresh monitor store | stalled-host test ("restart must continue the generation…") |
| `grant_identity_unchecked` | 3 | drop the grant unit/invocation comparison | `test_restart_with_wrong_identity_is_refused` |
| `non_systemd_mode_accepted` | 4 | accept any supervision mode | `test_missing_or_invalid_configuration_holds_before_launch` |

## Commands

All commands run with `PYTHONPATH=src:.`.

1. `python3 -B -m pytest -q tests/control_plane/test_monitor_host.py`
2. `python3 -B -m pytest -q tests/control_plane/test_monitor_host_systemd.py`. A skip is a HOLD.
3. The pinned initial commands:
   - `python3 -m pytest -q tests/control_plane/test_monitor_health.py tools/orchestration/test_factory_director_host.py`
   - `node --test test/systemd-supervision.test.mjs`
4. The terminal checks:
   - `python3 -B tools/fitness/check_architecture.py --root src/alienintent --check all`
   - `python3 -B -m pytest -q tests/test_architecture_fitness.py`
   - `python3 -B -m pytest -q`. This is compared with the admission baseline in a disposable worktree.
   - `node scripts/check.mjs all`
5. `python3 -B tools/evidence/fx_c5_evidence.py --output <new dir> --invocation <exact invocation>`. The harness runs
   all of the above and must run on a clean committed candidate.

## Evidence

The evidence lives beside this file: `execution-record.json` (`ProofFixtureExecution`), `run-report.json` (the
acceptance mapping and the composed readback from the real manager), `proven-red.json`, `observations/` and
`digest-manifest.json`. A missing measurement or readback is a HOLD, never a PASS. Tokens, cost and provider calls
are `null` with an `UNKNOWN` reason. The independent verdict is `PENDING_FRESH_BIU_VERIFIER`.

## Non-claims

- No bootstrap monitor/observer service is retired, reconfigured or replaced. No unit is installed or enabled
  persistently. The fixture's transient units are removed at the end of the run.
- No live operational G+I, cutover, sovereignty or retirement claim is made from this local/composed proof. It runs
  on one workstation's per-user systemd manager.
- No Doctor or installation configuration is added (SF-REQ-037/038). No new nonterminal retry semantics or budget
  reset is introduced.
