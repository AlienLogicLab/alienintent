# FX-S0 — proof fixture for the reusable isolated proof substrate (WO-220101)

Owner node S0 · Issue [#69](https://github.com/AlienLogicLab/alienintent/issues/69) · release SWF-35, baseline `ade44cb93f3f33a570e1cf1b4bda500a79cd95bb`.

The pinned plan is [`FX-S0/fixture-plan.json`](FX-S0/fixture-plan.json); the pinned input is
[`FX-S0/manifest.json`](FX-S0/manifest.json). The plan was committed **before** any adapter or
fixture changed, as the release record requires: it fixes the commands, controlled inputs, expected
observables, negative controls and evidence schema for every predicate of the S0 completion
predicate, and names what the fixture does not claim.

Retained run evidence is written under `FX-S0/` by `tools/evidence/fx_s0_evidence.py` once the
substrate exists; until then the plan's `status` is `PINNED_NOT_EXECUTED` and no result is claimed.
