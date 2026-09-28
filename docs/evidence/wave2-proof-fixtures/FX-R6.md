# FX-R6 — Release-admission preparation pin

Status: preparation only; the existing release-admission protection remains in force.
Prepared by Factory Director episode `factory-director-67482e852e5c455ba653cfad249963a3` on 2026-09-28.

## Bound target

The proof target is the existing canonical live-profile prelaunch boundary exercised by the real AlienLogicLab/
alienintent Project #1 path. The fixture must use a disposable labelled probe and the configured execution profile,
with read-back of the Project item and host runtime state. It must not retire or bypass
`tools/live/release_admission.py`, launch a worker on an invalid case, or alter unrelated Project items.

## Pinned cases

For each case, the producer records the gate decision before any actor launch and the exact application count:

1. intact valid release preconditions: admission may proceed only for the labelled probe;
2. each of the six existing release preconditions absent or invalid: refusal and zero actor launches;
3. eligibility absent or invalid: refusal and zero actor launches;
4. formal release-authority closure without the required preconditions: refusal and zero actor launches;
5. restored valid probe: the exact Project and runtime read-back is reconciled, with old protection still present.

No case permits old-mechanism retirement. A missing precondition, target readback, budget dimension, or actor
count is `UNKNOWN`/HOLD rather than PASS.

## Evidence shape

The output directory is `docs/evidence/wave2-proof-fixtures/FX-R6/<run-id>/` and contains
`execution-record.json`, `observations/<sha256>`, `digest-manifest.json`, `proven-red.json`, `readback.json`, and
an independent verdict receipt. The record must bind the candidate SHA, profile/config digest, Project item,
runtime-state digest, command, exit status, and old-protection readback separately.

## Executable fixture pin — 2026-09-28

Source: `tools/live/fx_r6_release_gate.py` reuses the proven B3 canonical Project #1
fixture. It runs through `GitHubProfileComposition` with only the worker process
scripted to `authority-block`. Its own disposable draft Project items are deleted
and read back; unrelated items must have identical before/after digests. The
existing `tools/live/release_admission.py` remains present and unchanged.

Before the live run, execute:

```bash
rtk proxy pytest -q tools/live/test_fx_r6_release_gate.py tools/live/test_fx_b3_release_admission_proof.py
```

With the configured `~/.config/alienintent/self-hosting.json` profile, run once:

```bash
rtk proxy python3 tools/live/fx_r6_release_gate.py --out docs/evidence/wave2-proof-fixtures/FX-R6/<run-id>
```

The wrapper invokes `python3 tools/live/fx_b3_release_admission_proof.py --target production
--out <run-dir>/live`. The exact executed argv and exit code go in `execution-record.json`.
Inputs are the configured profile (digest only), current host runtime state (before/after
digests), source HEAD, `origin/main`, the B3 case table, and the old gate's committed
source. The valid case must yield one scripted launch; every named negative case must
yield zero launches. The old gate control must pass intact, refuse with Agent Ready
missing despite formal release authority, and pass again restored. Both checks and
the committed file digest must read back unchanged after the run.

The run directory retains `execution-record.json`, `readback.json`, `proven-red.json`,
`digest-manifest.json`, `independent-verdict.json`, the raw `live/` fixture observations,
and command stdout/stderr. `independent-verdict.json` records PENDING until the fresh
verifier issues its own verdict. The candidate commit SHA is recorded on Issue #138
after the evidence commit because a commit cannot embed its own SHA. A missing case,
counter, profile, state, readback or cleanup is a failure, never inferred zero or PASS.
