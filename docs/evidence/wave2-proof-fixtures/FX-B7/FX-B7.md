# FX-B7 — Installation launch-command migration proof (WO-220510, Issue #129)

Status: **PINNED before implementation** by PRODUCER invocation
`AlienLogicLab/alienintent#129:PRODUCER:3a666278-98c5-4311-9776-73e4f4ff3ee3` (worker Morty),
admission baseline `5b5fbf6` (`origin/main`, Director RELEASED record on Issue #129). This contract
is committed before any tool or evidence change. Later commits may add evidence but may not weaken
these probes. Changing them needs the authority that owns node B7.

## Governing inputs

- Work unit: `docs/work-units/wave2/WO-220510.md`. Agent Ready READY record
  `docs/evidence/wave2-readiness-assessments/WO-220510.2026-09-26T202412.297347Z.assessment.json`,
  input SHA-256 `150905b3bd30585e2d5d7a434959e00721a19564bfcb9c6fd8868b853164212c`.
- Execution packet: `docs/evidence/wave2-execution-packets/WO-220510.packet.json` and `.allocation.json`.
  DAG node B7. Candidate contract sha256 `35468dc69e46c60363b9a4a72ced9b45e6fdd105ca8941b8075e1e0464e59453`.
- Requirement: `docs/evidence/wave1-bootstrap-retirement-matrix.json#/transition_plan/15`
  (step 16, mechanism "b-disp command compatibility alias", `execution_status: NOT_EXECUTED`).
- Authority: `docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md`
  (Founder decision `WAVE2_BOUNDED_OPERATIONAL_AUTHORITY_DELEGATION`) disposes
  INSTALLATION_MIGRATION_AUTHORITY and POSTW1-DECIDE-006A for this BIU's own extent. The Director
  RELEASED record on Issue #129 authorizes IMPLEMENT only. It grants no release, live operation or
  alias retirement.
- Predecessor: WO-220501 / FX-B0 (Issue #116, DONE). Its manifest
  `docs/evidence/wo-220501-fx-b0/bootstrap-custody-manifest.json` is re-checked at this baseline
  before use.

## Terms

| Term | Meaning |
|---|---|
| Canonical command | `alienintent`, i.e. `bin/alienintent.mjs` (`package.json#/bin/alienintent`). |
| Alias | `b-disp`, i.e. `bin/b-disp.mjs` (`package.json#/bin/b-disp`), a one-line re-import of the canonical entry point. |
| Launch reference | A place that a supervisor, scheduler, shell or AlienIntent integration reads to start a program, and that names the canonical command or the alias as the program it starts. |
| Persisted identities | B-DISP protocol markers (`<!-- B-DISP: ... -->`), `b-disp/<uuid>` branch/resource identities, `b-disp-ownership` records, the `b-disp` worker profile name, and the runtime state lanes/resources/history. None of these is a command launch, and none may be renamed. |

## Coverage method (pinned)

Enumeration is by **launch surface**, not by a fixed file list. Every surface is scanned through
its own discovery rule, and each surface reports one of `SCANNED` or `UNKNOWN` (with reason). The
surfaces are:

| Id | Surface | Discovery rule |
|---|---|---|
| `systemd-user-paths` | systemd user unit search path | every file under each directory reported by `systemd-analyze --user unit-paths` |
| `systemd-system-paths` | systemd system unit search path | every file under each directory reported by `systemd-analyze unit-paths` |
| `systemd-user-loaded` | loaded user units, including transient | `ExecStart`/`ExecStartPre`/`ExecStartPost`/`ExecReload`/`ExecStop` of every unit from `systemctl --user list-units --all` |
| `processes` | running processes | `/proc/<pid>/cmdline` of every process |
| `cron` | cron tables | `crontab -l`, `/etc/crontab`, `/etc/cron.d/*` |
| `shell-startup` | login and interactive shell startup | `~/.profile`, `~/.bash_profile`, `~/.bash_login`, `~/.bashrc`, `~/.bash_aliases`, `~/.zshrc`, `~/.zprofile`, `/etc/profile`, `/etc/profile.d/*`, `/etc/bash.bashrc` |
| `xdg-autostart` | desktop autostart | `~/.config/autostart/*`, `/etc/xdg/autostart/*` |
| `path-executables` | executables on PATH | every directory on the running runtime's PATH and on the login PATH, plus the Node global `bin` and `lib/node_modules` |
| `alienintent-config` | AlienIntent installation configuration | every file under `~/.config/alienintent`, excluding the `secrets/` credential directory by credential boundary |
| `bootstrap-root` | external bootstrap scripts | every file under `~/.local/share/alienintent-bootstrap`, excluding interpreter caches |
| `wsl-boot` | WSL boot command | `/etc/wsl.conf` |
| `windows-startup` | Windows logon start | per-user and all-users Startup folders under `/mnt/c` |
| `windows-run-keys` | Windows Run/RunOnce registry | `reg.exe query` of HKCU and HKLM `Run` and `RunOnce` |
| `windows-tasks` | Windows Task Scheduler | every file under `C:\Windows\System32\Tasks`, decoded as UTF-16 or UTF-8 |

Repository files are **not** installation surfaces. They are reported separately as
`repository_references`, for information only, because a later retirement BIU needs them.

## Classification (pinned)

Each line on a surface is split into tokens. A token whose basename is `alienintent` or
`alienintent.mjs` is a **canonical** reference. A token equal to `b-disp`, or whose basename is
`b-disp` or `b-disp.mjs`, is an **alias** reference. Tokens such as `b-disp/<uuid>`, `b-disp-morty`
and `B-DISP:` are neither: they are persisted identities or unrelated names. A reference is a
**launch** when it sits in a launch position: a systemd `Exec*` directive, a process argv, a cron
command, a shell startup line, a Windows start entry, or a configured AlienIntent executable/
launcher field. Otherwise it is a non-launch reference.

The result classes are `CANONICAL_LAUNCH`, `ALIAS_LAUNCH`, `CANONICAL_REFERENCE` and
`ALIAS_REFERENCE`.

## Migration (pinned)

- Only an `ALIAS_LAUNCH` on a file surface is migrated. The migration replaces the alias token with
  the canonical token for the same checkout and changes nothing else.
- `migrate` refuses unless it is given the recorded authority document and it is `--apply`d.
- Before each rewrite it retains the original bytes and records before/after sha256. `rollback`
  restores the retained bytes exactly. A plan with zero alias launches produces an explicit
  `NO_MIGRATION_REQUIRED` receipt, backed by the coverage record. It is never a bare PASS.

## Operational readback (pinned)

This runs on the authorized target: the live AlienIntent installation on the producing host, which
is the unit that launched this invocation. For every loaded unit with a `CANONICAL_LAUNCH`:

- the unit is `active/running`;
- `/proc/<MainPID>/cmdline` names the canonical entry point;
- the entry point's realpath resolves inside the configured `repositoryStore`;
- the entry point file is the canonical module, not a re-export of the alias.

Readback observations are retained as raw files with sha256 references.

## Preservation (pinned)

The pass takes a snapshot before the inventory and another after the readback. Each snapshot covers:

- the key sets of runtime state `resources`, `closures`, `founderExceptions`, `deliveries`,
  `diagnostics` (lanes) and `active`;
- the B-DISP marker patterns in the installed `src/github/authority.mjs` and
  `src/runtime/dispatcher.mjs`;
- the `b-disp/<resourceId>` branch rule in the installed `src/runtime/worktree-manager.mjs`.

The after-snapshot must be a superset of the before-snapshot. The runtime is live, so identities
may be added but never renamed or dropped. The marker patterns must be byte-identical. Only
digests and counts are retained, never state contents.

## Probes

| Probe | Expected |
|---|---|
| B7-01 coverage | Every pinned surface is present. Each is `SCANNED`, or `UNKNOWN` with a reason. |
| B7-02 enumeration | Every canonical/alias reference is listed with surface, location, launch flag and class. |
| B7-03 migration | Every `ALIAS_LAUNCH` has a migration and rollback receipt, or the plan is empty and records `NO_MIGRATION_REQUIRED`. Migration without authority is refused. |
| B7-04 readback | Every canonical launch unit passes operational readback. There is at least one. |
| B7-05 preservation | The after-snapshot is a superset of the before-snapshot, and the markers are identical. |
| B7-06 retirement hold | `alias_retirement` is `HELD` when any surface is `UNKNOWN` or any `ALIAS_LAUNCH` remains. Otherwise it is `COVERAGE_COMPLETE_RETIREMENT_NOT_AUTHORIZED_HERE`. It is never `RETIRED` or `AUTHORIZED`. |
| B7-07 predecessor | The FX-B0 checker and its focused tests pass at this baseline. Live rediscovery drift is recorded, not repaired. |

## Negative controls (intact / fault / restored, each applied once)

Each control runs on a disposable fixture host. These controls are LOCAL; they prove that the gate
discriminates, not operational acceptance.

| Control | Fault | Gate must report |
|---|---|---|
| `alias_launch_injected` | add a unit with `ExecStart=... bin/b-disp.mjs ...` | `alias_launch` and retirement `HELD` |
| `surface_unreadable` | make a surface unreadable | `coverage_unknown` and retirement `HELD` |
| `surface_dropped` | remove a surface from the coverage record | `coverage_incomplete` |
| `readback_alias_process` | running MainPID argv names `bin/b-disp.mjs` | `readback` |
| `identity_dropped` | drop a resource identity / alter a B-DISP marker after migration | `preservation` |
| `retirement_claimed` | set `alias_retirement` to `RETIRED` | `retirement_claim` |
| `rollback_incomplete` | skip restoring one migrated file | `rollback` |

## Evidence

Evidence is written to `docs/evidence/wave2-proof-fixtures/FX-B7/operational-run/<UTC>/`. It holds
the inventory, the migration receipt, the readback, the before and after preservation snapshots,
the controls, the predecessor re-check, raw observations under `objects/`, and a
`digest-manifest.json`. Missing measurements are holds, never zero or PASS. Token and cost
telemetry that is not exposed to the producer is recorded as UNKNOWN.

## Non-claims

- No alias retirement, release, live operation or production change is authorized or performed.
- `bin/b-disp.mjs` and `package.json#/bin/b-disp` stay (KEEP_UNTIL_REPLACED).
- The LOCAL controls do not satisfy operational acceptance. Only the operational run does, and only
  after the independent VERIFIER's verdict.
