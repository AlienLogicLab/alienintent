# FX-E2 repair 1 — pinned assertion order (run `20260926T213920Z` held)

The run at source `52b9f03` held with `CONTROL_NOT_DISCRIMINATING` for two controls. It is retained unchanged
under `local-run/20260926T213920Z/`. All ten probes passed, and five of the seven controls discriminated.

| Control | What the fault run showed | Cause |
|---|---|---|
| `checkpoint_unverified` | Exit 1: `Failed: DID NOT RAISE CutoverHold` from an earlier `pytest.raises` | The fault **was** detected, but by an unlabelled check that ran before the pinned `a tampered checkpoint must hold` assertion. |
| `rollback_replays_python_effect` | Exit 1: `AssertionError` on `completed_by_python == {...}` | The fault **was** detected, but by an unlabelled assertion that ran before the pinned `a lane Python completed must not be re-dispatchable after rollback`. |

In both cases the fault was caught. The pinned discrimination rule also requires the failure to be
reported through the pinned assertion text, and here it was not.

**Repair (test ordering only):** in `tests/execution_coordination/test_one_writer_cutover.py`, the pinned
assertion is now evaluated first. For E2-04, both `verify` and `rollback` report through the pinned
message. For E2-08, the re-dispatchability assertions come before the result-shape assertion. Every
original check is kept.

Not changed: no `src/` change, and no probe, control, needle or pinned assertion text in `FX-E2.md`
or `tools/evidence/fx_e2_evidence.py`.
