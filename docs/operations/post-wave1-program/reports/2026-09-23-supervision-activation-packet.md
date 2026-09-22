# Bootstrap duration supervision — live activation packet (prepared, not applied)

Date: 2026-09-23. Prepared by: resident bootstrap coordinator, for the S1 admission hold
(`FACT-S1-ADMISSION-008`, `2026-09-22-s1-admission-budget-hold.md`). Scope rule 10–13 of the
Program Director role apply: this packet activates one landed repair with the smallest existing
mechanism; nothing else.

## What is already done (FACT)

- Source repair landed on `main`: `803782d` / merge `ce89c69` — `execution.supervision`
  (systemd transient units, positive duration, owned-process-tree cancellation/custody).
- Deterministic regressions: `node scripts/check.mjs all` exit 0 on `main` at `ce89c69` (this host).
- Disposable host proof on this host: `node --test test/host/systemd-supervision.mjs` → PASS
  (`client-death-live-parent`, `client-death-orphan-setsid`, `HOST_PROOF_PASS`), systemd 255, user
  manager reachable, `/usr/bin/systemd-run`, `/usr/bin/systemctl`, `/usr/bin/env` present.
- Live profile `~/.config/alienintent/self-hosting.json` has **no** `execution.supervision` block:
  supervision is not active; the bootstrap still spawns workers unbounded (`operations.md` §
  supervision: "source repair alone does not activate supervision").
- Idle guard at preparation time: `state.json#/active` = []; Project #1 has 0 items in
  IMPLEMENT/VERIFY/REVIEW/ACCEPT; dispatcher PID 1206384 active since 2026-09-22 23:26 +07. Must
  be re-checked immediately before the restart.

## Installation-only diff (exact)

Add to `~/.config/alienintent/self-hosting.json` under `execution` (no other key changes):

```json
"supervision": {
  "mode": "systemd",
  "runtimeMilliseconds": 7200000,
  "startupMilliseconds": 120000,
  "stopGraceMilliseconds": 300000,
  "systemdRun": "/usr/bin/systemd-run",
  "systemctl": "/usr/bin/systemctl",
  "env": "/usr/bin/env"
}
```

Total allowance per invocation = startup 2 min + runtime 120 min + stop grace 5 min = **127 min**.

## Numeric allocation — evidence, not assumption

| Observation | Duration |
|---|---|
| WO-220101 PRODUCER (cycle 1, S0 implementation incl. fixture execution) | ≈ 27 min (12:32:14Z → 12:59:35Z) |
| WO-220101 VERIFIER (independent re-execution of every pinned command) | ≈ 8 min |
| WO-220101 post-ACCEPT closure PRODUCER | ≈ 6 min |
| Wave 1 PY-NN invocations | UNKNOWN — trajectories carry no start/end pairs (0 measurable) |

120 min runtime is ≈ 4.4× the longest observed Wave 2 invocation. It is a hard cap on runaway
execution (SWF-09 "hard-enforced … wall-clock duration"), not a performance target; a hit cap is
a terminal receipt with no new retry entitlement (operations.md). The number is a **budget value
no authority has set**; that is why this packet is prepared and not applied.

## Rollback and post-activation checks

1. Backup: copy `self-hosting.json` → `self-hosting.before-supervision.json` (same dir, mode 600).
2. Re-check idle guard (active claims empty, no in-flight Project items, no registered worker PID).
3. Apply the diff; `systemctl --user restart alienintent.service`; confirm `ActiveState=active`,
   new `MainPID`, journal shows the profile accepted (strict validation: any schema error fails
   startup — rollback = restore backup and restart).
4. `python3 -m alienintent doctor` (or the existing pre-autonomy doctor) reports no FAIL/UNAVAILABLE.
5. First supervised invocation (S1 PRODUCER) is observed: transient unit created, receipt
   persisted; no manual intervention.
6. Rollback at any failed step: restore the backup, restart, record the receipt.

## Authority

- Repair authority: AA §42 / SWF-01 critical bootstrap exception (established by the S1 hold
  record and its independent review).
- **Activation authority: not established.** It sets a budget value (Founder §13 "material
  budget authority") and changes live operation of the bootstrap profile plus a service restart
  (standing instruction: do not change profiles or restart services without authority). The
  alternative — an S1-only exception to hard duration enforcement — is a risk acceptance, also
  the Founder's. One decision is requested; nothing is applied until it is given.

## After activation (delegated, SWF-35 path)

Bind the WO-220102 packet at the then-current baseline → native Agent Ready assessment → create
the Project issue at READY → `release_admission.py` → READY → IMPLEMENT under SWF-35 → dispatcher.
