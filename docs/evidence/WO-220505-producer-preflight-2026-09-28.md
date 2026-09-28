# WO-220505 producer preflight: real-lane proof hold

## Identity and authority

- Invocation: `AlienLogicLab/alienintent#125:PRODUCER:67f257ad-2d0a-47ab-ab61-bec5adeaefad` (Morty).
- Repository and release baseline: `AlienLogicLab/alienintent`, `af1f2daa96d9fa62624e94a7b428d3b52c645365`.
- Assignment: Issue #125, `docs/work-units/wave2/WO-220505.md`, Founder YES comment 5872218295, READY receipt comment 5873006116, IMPLEMENT release comment 5873015705.
- This record is a source and host preflight at 2026-09-28 15:23 UTC. It is not FX-B2 execution, a live-lane receipt, an independent verdict, or SF-REQ-056-AC-08 proof.

## Observations

| Check | Command / source | Observed result |
| --- | --- | --- |
| Baseline | `rtk git rev-parse HEAD origin/main`; `rtk proxy git ls-remote origin refs/heads/main` | All three identified `af1f2daa96d9fa62624e94a7b428d3b52c645365`. |
| Worktree | `rtk git status --porcelain=v1` | Empty before this record was written. |
| Worker identity | `rtk git config user.name`; `rtk git config user.email`; `rtk gh api user --jq .login` | `Morty`; `morty-worker@factorychecks.com`; `morty-worker`. |
| Bootstrap | `rtk proxy env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user is-active alienintent-liveness.service` | Exit 0, `active`. No stop/start was attempted. |
| Dispatcher lane | Read-only `jq` selection of `active` in `~/.local/state/alienintent/state.json` | Exactly one active key, `AlienLogicLab/alienintent#125:PRODUCER`, with this invocation. No other active key at that read. This is a momentary observation, not a phase-2 window admission. |
| FX-B2 profile | `rtk proxy ls -la /home/netmarine/.local/state/alienintent/fx-b2` | Exit 2, directory absent. No profile was provisioned or launched. |

The initial plain `systemctl --user is-active` returned exit 1, `Failed to connect to bus: No medium found`, because this worker process lacks `XDG_RUNTIME_DIR` and `DBUS_SESSION_BUS_ADDRESS`. The explicit user-bus environment above returned `active`; the initial result is not evidence that systemd or the bootstrap is unavailable.

## Blocking source mismatch

The phase-2 fixture says `monitor_host` will inspect the real `state.json` lane and perform a real `gh project item-edit` recovery on Issue #125 (`WO-220505.md`, steps 3-4). The source at the release baseline does not provide that path:

1. `src/alienintent/composition/monitor_host.py` constructs `LivenessProfile` under the configured profile root. `src/alienintent/composition/liveness_profile.py:77-80` binds its observations, lifecycle journal and admission to `root/liveness.sqlite`.
2. `src/alienintent/execution_coordination/adapters/liveness_observations.py:24-80` observes only records in that fenced store. Its lifecycle writer is explicitly a local stand-in (`:81-99`). It does not read the Node dispatcher's `active` map or Project #1.
3. `src/alienintent/execution_coordination/application/liveness.py:74-84,148-154` says the consumer is a local guarded journal with no remote provider bound, and `deliver` calls that local executor. A guarded SQLite receipt therefore cannot establish a real `gh project item-edit` action or Project readback.

These are the specific boundaries that prevent the pinned phase-2 procedure from proving its real-lane predicate. The profile is also not provisioned for phase 1. Starting the phase-2 grace window, stopping the bootstrap, or manufacturing a real gap before a wired, discriminating path exists would expose the live lane without a proven replacement. No live service, Project item, dispatcher state, credential, or other repository was mutated in this preflight.

## Required next implementation and proof

Keep Issue #125 in its current lifecycle until this packet is disposed. Within WO-220505's existing authority, bind a read-only, generation-correlated observation adapter to the real #125 dispatcher and Project state, and a single fenced effect consumer to the exact existing Project mutation with durable readback. Prove refusal before mutation for absent evidence, stale generation, duplicate effect identity, simultaneous writer and unavailable readback. Revise the fixture so the isolated phase-1 cases have independent probe identities and controllable restart timing, then demonstrate intact/fault/restored discrimination. Only after that should an actor prepare the bounded real-lane window with bootstrap stop/start cleanup, exact before/after Project and runtime readbacks, and an independent verifier on the exact candidate SHA. Preserve the bootstrap and all earlier evidence; a local receipt must remain labelled local.

Disposition for this invocation: `FOUNDER_EXCEPTION` due to a failed deterministic source preflight and unavailable real-lane proof, not an assertion that Founder intent is undecided. The candidate branch carrying this packet is retained for Factory Director disposition under BIU custody; it is not a VERIFY candidate or authority to merge, deploy or retire the bootstrap.
