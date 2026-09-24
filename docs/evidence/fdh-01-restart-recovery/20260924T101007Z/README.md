# FDH-01 host restart/recovery test: 2026-09-24

**Verdict: PASS.** Same episode, same lease ownership, new host process, zero duplicate launches, and a normal
exit and reconciliation afterwards.

The test was directed by the Founder. It restarted the Factory Director Host service **while a Director episode
held the lease**. The trigger was Director inbox entry `restart-test-status-note-20260924T101007Z`, which asked
for a completion note on #83.

| Pass criterion (pre-registered) | Result | Evidence |
|---|---|---|
| 1. The same live episode D survives the restart | D `factory-director-2fedb264…` (pid 300296) was alive before the 10:10:45Z restart. The restarted host saw it alive at 10:10:58Z. It exited on its own at about 10:12:03Z, roughly 75 s after the restart. systemd kept its processes in the unit's cgroup (`KillMode=process`: "left-over process … Ignoring"). | `01-episode-D.txt`, `02-host-before.txt`, `03-unit-journal.txt`, `04-history-after-restart.jsonl` |
| 2. The host MainPID changes | 144770 → 300506, unit active | `02-host-before.txt`, `03-restart.txt` |
| 3. `lease.json` byte-identical while D lives | sha256 `982f701e…` before and after the restart | `02-lease-before.sha256`, `04-lease-after.sha256` |
| 4. The restarted host emits only `DIRECTOR_EPISODE_ACTIVE` for D; no second launch | One `DIRECTOR_EPISODE_ACTIVE` record for D; **0** launch records for any other episode | `05-history-since-restart.jsonl` |
| 5. After D exits, the new host records the exit and decides correctly | 10:12:05Z `DIRECTOR_EPISODE_EXITED` for D, then `NO_ELIGIBLE_AUTHORIZED_WORK`, which is correct because #91/#92 are at CAPTURE and there are no claims or inbox entries. The lease was rewritten only then, with status `EXITED`. | `05-exit-D.json`, `05-lease-after-exit.json` |

D's work was also completed: a completion note on #83 and the inbox receipt. D's own output is
`subtype: success`, `is_error: false`, 12 turns (`06-output-D.json`). All original units are still active (`07-units.txt`).

## Observations (recorded, not failures)

- **R-1, exit status after a restart.** The restarted host is not D's parent process, so it cannot read D's exit
  code. It recorded `exit_reason: PROCESS_EXITED` rather than `EXIT_0`. D's output shows it succeeded. This is a
  truthful "code unknown" for any episode that survives a host restart. It could be improved by reading the retained
  episode stdout's success marker. It does not affect control.
- **R-2, lease ownership after exit.** The post-exit lease keeps the *launching* host's id
  (`fdh-b2ea99…`) rather than the restarted host's. That is consistent with the lease belonging to the host that
  launched the episode. The observing session had predicted otherwise, and the prediction was wrong. The Founder's
  assertion (no mutation while D lives) is unaffected.
- **Observer check race.** `04-after.txt` says "D not alive". The observer's check ran in the seconds between D's
  normal exit (about 10:12:03Z) and the host observing it (10:12:05Z). The host's own records are authoritative.
