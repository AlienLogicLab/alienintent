# FDH-01 live continuity proof: 2026-09-24

**Verdict: PASS.** All twelve steps have evidence. No HOLD was recorded, and no existing continuity mechanism was retired.

This follows the procedure in `docs/operations/factory-director-host-live-proof.md` at `06e7e0c`. The Factory Director
authorized it on Issue #89. The workload was real factory work: #81 (WO-220203) and then #83 (BRD-83), in the Founder's
order, which a Director inbox handoff relayed to the episodes. The session that authorized the proof only observed from
step 1 onward.

| Step | Result | Evidence |
|---|---|---|
| 0 / 0a | FDH-01 landed (`a233e9e`, containing `b0c66a7`). Dedicated linked worktree. Holds `[]`. Inbox handoff written. Adapter dry run: `authoritative_state: true`, control required by #81 and #83. | `00-*`, `0a-*` |
| 1 | Episode A `factory-director-eeb12163…` launched 08:07:23Z on `claude` / `claude-opus-5-5`. | `01-lease-A.json`, `01-history.jsonl` |
| 2 | Fresh-session argv (`-p --no-session-persistence`, no resume). A released #81: native receipt, `RELEASED —` record citing the inbox handoff, gate ADMITTED, READY→IMPLEMENT. It also left a queue note on #83 for its successor. | `02-cmdline-A.txt`, `02-A-comments.txt`, `02-readback.txt` |
| 3 | A exited `EXIT_0` after 274.5 s. Usage measured, model `PROVIDER_REPORTED`, cost $1.26. Inbox receipt written. | `03-exit-A.json`, `03-inbox-after-A.txt` |
| 4 | No non-worker event on #81 or #83 between A's exit and B's launch. Hold record byte-identical to 0a. | `04-*` |
| 5 | Host relaunched with `PRIOR_EPISODE_EXITED_CONTROL_REMAINS` at 09:05:12Z. Diagnostics: `{"83": "eligible:READY"}`, 0 claims. | `05-diagnostics.json`, `05-relaunch.json` |
| 6 | Episode B `factory-director-7e7fbb7b…` has a new episode id and a new pid. | `06-lease-B.json`, `06-lease-diff.txt` |
| 7 | Same fresh-session argv; no resume or continue flag. | `07-cmdline-B.txt` |
| 8 | B reconstructed state from durable records only: #81 DONE (`474343a`), the processed inbox entry, the board, the contract and gate hashes, and the credential probe. Session ids differ (A `a94d236a…`, B `e10b26fd…`). | `08-output-A.json`, `08-output-B.json` |
| 9 | B identified #83 (BRD-83) as the next authorized action, per the Founder's order and the selection rules. | `09-issue.txt`, `08-output-B.json` |
| 10 | B released #83. Read-back: #83 at IMPLEMENT. PRODUCER claim started 09:08:46Z. | `10-readback.txt` |
| 11 | B exited `EXIT_0` after 269.8 s. Usage measured, model `PROVIDER_REPORTED`, cost $1.16. | `11-exit-B.json` |
| 12 | Host repeated correctly: idle `WIP_INTENTIONALLY_FULL`, agreeing with diagnostics (nothing requires control, 1 active claim). Zero crash-loop or launch-failure records. | `12-*` |
| 13 | All original units still active. `self-hosting.json` unchanged since 0a. No HOLDs. | `13-*`, `SHA256SUMS` |

## Findings and deviations (recorded, none invalidating)

- **P1, deployment:** the systemd user unit's `PATH` did not include `~/.local/bin`, so the host failed closed
  (`AUTHORITATIVE_STATE_UNAVAILABLE`) and no episode ran. It was fixed by adding `PATH` to
  `factory-director-host.env`. The procedure's env instructions should list `PATH`. Evidence: `01a-first-attempt-history.jsonl`.
- **P2, predicate edge (fail-safe), seen twice:** during worker handoffs the adapter briefly saw 2 active claims
  against a WIP limit of 1. `wip_intentionally_full` requires claims *equal* to the limit, so the host recorded
  `EXECUTION_CAPACITY_UNAVAILABLE` (REFUSED) instead of idle. No launch occurred. Candidate follow-up: treat claims ≥ limit as full.
  Evidence: `P2-diagnostics-0855.json`.
- **Step 5 timing:** the procedure expects relaunch within seconds of the prior exit, assuming control still remains.
  After A exited, control did *not* remain (the WIP was full), so the host idled correctly. B launched when state
  changed: #81 DONE at 09:03:09Z, claim released at 09:04:15Z, relaunch at 09:05:12Z. The same promise, detecting a
  continuing need without prompting, is demonstrated, triggered by a state change rather than the exit.
- **Step 4 identity caveat:** Founder and Director episodes act through the same GitHub identity (`sanookdu`), so
  authorship alone cannot separate them. The timeline in the window was empty of non-worker events, and the observing
  session posted nothing.
- **Step 13 unit diff:** besides the host unit, the diff shows `alienintent-a3f3a38….service`. That is the transient
  supervised unit of #83's PRODUCER, which B's release started, not a replacement.

## Consequence

The Factory Director Host has now shown the continuity mechanism under real workload. A Director episode ends; the
host detects a continuing need with no Founder input; a fresh episode with no conversation history reconstructs state
from durable records, advances the correct authorized action, and exits; and the host repeats. Under the replacement-safety
rule, the session-bound continuity mechanism may now be retired **only by an explicit decision**. This proof does not
retire anything.
