# FX-B2 diagnostic, not an acceptance receipt

Issue: AlienLogicLab/alienintent#125, WO-220505. Producer invocation:
`AlienLogicLab/alienintent#125:PRODUCER:1963eb88-128d-42c9-abc8-c6e6ac4495da`.
Baseline at admission: `47b3a4221466eb69401b3641d17d99fe7d96e850`.
Mechanics source revision: `c8bdb246c1a4958abddcabae636b54bbf1d3d459`.
Isolated root:
`/home/netmarine/.local/state/alienintent/fx-b2/1963eb88-128d-42c9-abc8-c6e6ac4495da/profile`.
Capture command:
`python3 tools/live/fx_b2_capture.py --root /home/netmarine/.local/state/alienintent/fx-b2/1963eb88-128d-42c9-abc8-c6e6ac4495da/profile --output docs/evidence/wave2-proof-fixtures/FX-B2/diagnostic-1963eb88 --source-sha c8bdb246c1a4958abddcabae636b54bbf1d3d459`.
Capture exit status: `0`.
Immutable observation: `observations/dc9163e0bddc97985f6f845a638012bad2502d3fcffe31cbe260e513ff161533`, SHA-256 of canonical JSON.
The three `*-evidence/objects` directories retain the objects referenced by the captured state.

## Observations

- The isolated host ran under a real `systemd --user` unit. A concurrent launch refused with `HOST_ALREADY_OWNED` (exit 2); an observer invocation from outside the owned cgroup refused with `HOST_OUTSIDE_OWNED_UNIT` (exit 3). The isolated host and timer were stopped after the diagnostic; both subsequently read `inactive`. The incumbent `alienintent-liveness.service` stayed active throughout.
- Captured state has 17 durable scan reports. One scan records `liveness.gap`, `liveness.recovery_intent`, and `liveness.readback_confirmed`, with `G_PLUS_I_CLAIMED`; the effect ledger has one confirmed effect. Eleven subsequent scans record `liveness.suppressed` for the second generation's `FOUNDER_EXCEPTION` correlated outcome. A C1 `JUDGMENT` item and its attributable resolution are retained in the attention evidence objects. The resolution did not produce another recovery effect.
- The initial authority seed lacked `expires_at` at host launch. It was corrected only after the process started. This violates the pinned **prelaunch** admission boundary, even though later mechanics executed. The entire run is therefore diagnostic and cannot pass phase 1.
- Delayed delivery and restart duplicate safety (FX-B2 step 5) was not exercised. No real #125 lane gap, Project recovery effect, or phase-2 real outcome readback occurred. This record cannot satisfy SF-REQ-056-AC-08 or support SWF-29 retirement.

## Candidate code and remaining work

The candidate adds durable scan reports and a guarded, read-only capture/preflight/launch helper. Focused host/helper tests passed 38/38 after the read-only and child import-path repairs. The required real dispatcher observation and fenced Project adapter are still absent: the current `LivenessProfile` uses local `StoreEffectObservation` and guarded SQLite effect admission only. The real #125 `PRODUCER` lane remained actively owned by this invocation in `state.json`; no real gap was manufactured by altering dispatcher-owned state. The bound phase-2 window was never opened, so no bootstrap stop or external recovery mutation was attempted.

The single terminal Issue result comment must carry the candidate branch and SHA. The current dispatcher keeps this producer active until that result is routed, then can advance the Project state and dispatch the verifier. A phase-2 gap in this same handoff cannot be observed and included in that same terminal comment from this active producer without an explicit handoff schedule or detached authorized observer. Director disposition of that execution sequence and a fresh producer allocation are needed; the engineering adapter and both phases' discriminating proof remain work to do. This diagnostic does not request a Founder product-decision change.
