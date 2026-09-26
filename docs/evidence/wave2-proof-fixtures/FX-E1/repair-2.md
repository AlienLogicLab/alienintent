# FX-E1 repair 2 — sandbox verification kit, after run `20260926T100920Z` held

Run `20260926T100920Z` (source `4fb01d7`, after [repair 1](repair-1.md)) is
retained unchanged at [`runs/20260926T100920Z/proof-run.json`](runs/20260926T100920Z/proof-run.json).
Its disposition is **HOLD**. E1-6 and E1-7 held again: both BIUs stopped at `VERIFY` with
`outcome=failure`. Every other predicate passed, including E1-3: 167 processes over
3548 samples showed 0 Node, and the 147-module closure was all stdlib or alienintent.

## Cause — a sandbox fixture drift, not a transport defect

Before any verifier process starts, the shipped `CliWorkerProvider.run(VERIFIER)`
runs the **target repository's own** `tools/verification/run_feature_regressions.py`
against `tools/verification/feature_regressions.json` in the retrieved candidate tree
(`_feature_regressions`). If either file is absent, it returns `failure` (exit 2). The sandbox
repository was provisioned and seeded in Wave 1, before that gate existed
(`4a9a3b6 fix(verify): accumulate feature regression gates`). It carries neither
file, so no verifier could run there. Repair 1's worker change never executed. The
control plane behaved as designed and did not accept an unverified candidate.

Nothing in the Python transport, ingress, store or coordinator is repaired here.

## Repair (FX-E1 seeding and worker; no `src/` change)

1. FX-E1 seeding now installs or confirms the sandbox's verification kit in the same commit
   as the contracts. That is the same operator route PY-10 used to install
   `worker/run.sh`, under the sandbox's existing SWF-08 authority:
   - `tools/verification/run_feature_regressions.py`: the shipped runner, byte for byte;
   - `tools/verification/check_notes.py`: from `tools/live/fx_e1_sandbox_check_notes.py`, a real pack. A candidate may
     change only `docs/` notes, and each note opens with its BIU heading and carries exactly one bullet;
   - `tools/verification/feature_regressions.json`: registers that one pack (`sandbox-note-shape`).
   The seed phase records each file's digest.
2. The worker's VERIFIER branch writes only `.alienintent/verdict.json`. The
   regression receipt is the adapter's own, written from the runner above, and the
   worker no longer touches it.

Checked offline before this commit with the shipped
`CliWorkerProvider.run(VERIFIER)` over a local bare repository carrying the kit.
The pack ran and passed, the process result was `success`, and the shipped `read_verdict` returned `accept`.

Unchanged: predicates, pinned identification, authority scope, live target.
