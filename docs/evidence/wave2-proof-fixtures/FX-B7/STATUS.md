# FX-B7 status — WO-220510 (B7), Issue #129

Producer: Morty (`claude-opus-5-5`), invocation
`AlienLogicLab/alienintent#129:PRODUCER:3a666278-98c5-4311-9776-73e4f4ff3ee3`.
Candidate branch: `b-disp/5fb59763-dbf7-4607-b44c-8026458d1deb`.

**Result: OPERATIONAL run complete, no holds. It still awaits the independent VERIFIER verdict.**

The run found zero `b-disp` alias launches across all 14 pinned installation surfaces. The migration
plan is therefore empty and the receipt is `NO_MIGRATION_REQUIRED`. No installation file was changed.
The canonical `alienintent` launch was read back on the live unit. Alias retirement is
`COVERAGE_COMPLETE_RETIREMENT_NOT_AUTHORIZED_HERE`: coverage is complete, but retiring the alias
still needs its own separately authorized BIU.

## Repair 1 (verifier REJECT of `59a6c9c`)

Verifier `AlienLogicLab/alienintent#129:VERIFIER:c1023844-fa8b-44c7-9b7b-c1bfe5146690` passed every fresh check
on `59a6c9c`. It rejected the candidate only because `.alienintent/feature-regressions.json` was absent from the
published tree. Under the landed custody rule, that receipt is written into the verifier's checkout and is never
tracked (see [FX-B7.md](FX-B7.md#feature-regression-receipt-custody)). Committing it would be invalid: it would
name a parent SHA and could never validate against the commit carrying it. Repair 1
(`AlienLogicLab/alienintent#129:PRODUCER:d13eaf36-4fb8-43c0-85d9-c24b97daae9f`) states that rule in the pinned
contract. It records the PRODUCER receipt for the new published SHA on Issue #129. It leaves the tool, tests,
regression pack and the retained operational run `20260926T221756Z` unchanged. That run's source candidate
remains `07d80af`.

## Pins

| Item | Value |
|---|---|
| Fixture contract | `docs/evidence/wave2-proof-fixtures/FX-B7/FX-B7.md`, pinned in `1167e9e` before any implementation |
| Admission baseline | `5b5fbf6` (`origin/main`, Director RELEASED record) |
| Source candidate at run | `07d80af7640fbe5b2dc1aeec54df93f7371dffd7` (tool, tests and regression pack; clean tree) |
| Authority | `docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md` (INSTALLATION_MIGRATION_AUTHORITY, POSTW1-DECIDE-006A disposed) |
| Operational target | host `ALIENLAPTOP`, systemd user unit `alienintent.service`, profile `~/.config/alienintent/self-hosting.json`, repositoryStore `/mnt/d/Projects/alienintent` |
| Installed checkout HEAD | `5efe484`, an ancestor of `origin/main` that is 50 commits behind. `bin/` and the marker sources are identical to `origin/main`. |
| Run | `operational-run/20260926T221756Z/`; `digest-manifest.json` sha256 `122e2ff03846b6cec66bcbac253c376bf6fd27f859d68393ab94c6b980a88a77` |

## Command

```
python3 -B tools/live/installation_launch.py run \
  --output docs/evidence/wave2-proof-fixtures/FX-B7/operational-run/20260926T221756Z \
  --invocation "AlienLogicLab/alienintent#129:PRODUCER:3a666278-98c5-4311-9776-73e4f4ff3ee3" \
  --authority docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md
```

The command exited 0 with `holds: []`. It ran without `--apply`: the plan was empty, so there was
nothing to apply.

## Probes

| Probe | Result | Evidence |
|---|---|---|
| B7-01 coverage | PASS. All 14 surfaces were `SCANNED`, none `UNKNOWN`. | `inventory.json#/surfaces` |
| B7-02 enumeration | PASS | `inventory.json#/references` |
| B7-03 migration | PASS (`NO_MIGRATION_REQUIRED`, empty plan) | `migration-receipt.json` |
| B7-04 readback | PASS | `readback.json` |
| B7-05 preservation | PASS. No identity is missing and the markers are identical. | `preservation-{before,after,check}.json` |
| B7-06 retirement hold | PASS (`COVERAGE_COMPLETE_RETIREMENT_NOT_AUTHORIZED_HERE`) | `inventory.json#/alias_retirement` |
| B7-07 predecessor | PASS. The FX-B0 check, the live `--root` rediscovery and 7 tests all exited 0. | `execution-record.json#/commands` |

### Coverage (records scanned / locations)

| Surface | Records | Locations |
|---|---|---|
| systemd-user-paths | 1227 | 89 |
| systemd-system-paths | 10410 | 496 |
| systemd-user-loaded | 24 | 19 |
| processes | 65 | 65 |
| cron | 38 | 5 |
| shell-startup | 599 | 16 |
| xdg-autostart | 24 | 3 |
| path-executables | 2790 | 2790 |
| alienintent-config (excluding `secrets/`) | 2812 | 31 |
| bootstrap-root (excluding interpreter caches) | 6526 | 27 |
| wsl-boot | 5 | 1 |
| windows-startup | 74 | 7 |
| windows-run-keys | 27 | 4 |
| windows-tasks | 13449 | 312 |

### Launch references found (entry points)

| Class | Surface | Location | Program |
|---|---|---|---|
| CANONICAL_LAUNCH | systemd-user-paths | `~/.config/systemd/user/alienintent.service` `ExecStart` | `/mnt/d/Projects/alienintent/bin/alienintent.mjs` |
| CANONICAL_LAUNCH | systemd-user-loaded | `alienintent.service` | same |
| CANONICAL_LAUNCH | processes | MainPID `2324102` | same |
| CANONICAL_LAUNCH | alienintent-config | `alienintent.service.before-path-correction`, an inactive backup that no loader reads | `/mnt/d/Projects/b-disp/bin/alienintent.mjs`. The command is canonical. The old checkout path only looks like the alias. |
| ALIAS_REFERENCE (non-launch, name only) | alienintent-config | same backup, `WorkingDirectory=/mnt/d/Projects/b-disp` | a directory name, not a command |

There are **zero ALIAS_LAUNCH references.** All other canonical hits are name-only: repository
slugs `AlienLogicLab/alienintent`, `repository.name` in profile backups, and the checkout path.
Classification is deliberately conservative. For example, `worker_credential_probe.sh` passes the
repository name to `gh api graphql`, and that counts as a canonical launch-position token. Such
over-reporting cannot hide an alias launch.

### Readback (`alienintent.service`)

| Check | Observed |
|---|---|
| Unit state | `active/running`; loaded from `~/.config/systemd/user/alienintent.service`; running since 2026-09-27 03:40:43 +07 |
| MainPID `2324102` argv | `/home/netmarine/.local/bin/node /mnt/d/Projects/alienintent/bin/alienintent.mjs --config /home/netmarine/.config/alienintent/self-hosting.json` |
| Entry realpath | inside repositoryStore; sha256 `ac781570…946ae9`; not a re-export of the alias |
| Alias entry point `bin/b-disp.mjs` | present (KEEP_UNTIL_REPLACED), sha256 `5e228a76…7f812` |

This invocation was itself launched by that unit, through its `systemd-run` worker supervision.

### Preservation

Snapshots were taken at 22:17:56Z and 22:17:59Z. The counts were:

| Identity | Count |
|---|---|
| resources | 268 |
| closures | 48 |
| deliveries | 844 |
| diagnostics lanes | 92 |
| founderExceptions | 12 |
| active | 1 |

No identity is missing. The marker lines are identical: the B-DISP result/control markers in
`src/github/authority.mjs` and `src/runtime/dispatcher.mjs`, and the `b-disp/<resourceId>` branch
rule in `src/runtime/worktree-manager.mjs`. Nothing was renamed.

### Negative controls (LOCAL, each applied once, intact/fault/restored)

All 9 controls discriminate:

- `alias_launch_injected`
- `surface_unreadable`
- `surface_dropped`
- `readback_alias_process`
- `identity_dropped`
- `marker_altered`
- `retirement_claimed`
- `migration_without_authority`
- `rollback_incomplete`

The per-control results are in `controls.json`.

## Repository references (information for a later retirement BIU; not installation)

The following repository files still name the alias. They were not changed.

| File | Reference |
|---|---|
| `package.json` | `bin.b-disp` |
| `test/app-cli.test.mjs:15,27` | `bin/b-disp.mjs` |
| `test/cli.test.mjs:89` | alias name |
| `test/self-hosting.test.mjs:33` | `bin/b-disp.mjs` |

## Observations carried forward (no action taken)

- `alienintent.service` has `UnitFileState=disabled`: it is running, but it has no
  `default.target.wants` link. A host restart would not start it automatically. Changing that is a
  service change outside B7.
- The installed checkout is 50 commits behind `origin/main`. The launch entry point and the marker
  sources are unchanged across that range.
- `fc-experiment-b-dispatcher.service` belongs to a separate project (factorychecks). Its
  `b-disp-morty` directory name is not the alias.

## Limits and non-claims

- This is a point-in-time readback on the producing host. A verifier on another host can rerun the
  focused proof and the controls. Live rediscovery needs this host.
- The entry-point sha256 is the file on disk. The unit process loaded that module at its start
  time.
- No alias retirement, release, live operation, unit change or reinstall was performed or is
  authorized. `bin/b-disp.mjs` and `package.json#/bin/b-disp` stay.
- Token and cost telemetry is not exposed to the producer: UNKNOWN, not zero.
