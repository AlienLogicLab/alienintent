# REGRESSION-GATE (a38f0cb8-6803-463a-8031-0005f33aef01): landing record

- Work item: `a38f0cb8-6803-463a-8031-0005f33aef01`. Packet `docs/work-units/python/regression-gate.md`, sha256 `e0faa32a8cc6cf1f1f2c197ce5f55d722e80bf3a6095a87c94eb347bd85c93d2`, published on alienintent/work-packets at `f1b1eafa84ee0879915b37d2ceecae1e4c8b23e6`, assessed READY (attempt `d4fb345e-f5bf-4ad5-92f6-a989bc5e60c7`), authorized with baseline `bf3efcc47341549b05ef3ddd86817f598b767cc3`.
- Candidate: `883e4c5c36e73851e62f740fc270bb0e93f20915` (descends from the starting revision `bf3efcc47341549b05ef3ddd86817f598b767cc3`), landed on main by fast-forward, preserving its SHA. No pull request.
- Path: the hand-built maintenance path (Founder 2026-10-06: the factory's own regression gate was the thing under repair).
- Founder approval: "I approve REGRESSION-GATE (a38f0cb8-6803-463a-8031-0005f33aef01) for implementation at pointer f1b1eaf, subject to the exact assessed packet."
- Independent VERIFIER: ACCEPT (`verdict-883e4c5.md`). Whole suite bf3efcc vs 883e4c5 with the VERIFIER's own comparison: 0 findings. Replay cd5314b -> 057fbc1: exactly the 39 recorded findings. Mutations M1-M3: each failed its named test and passed again once reverted.
- Known debt carried to MAIN-GREEN: the 43 tests failing at bf3efcc (39 from 057fbc1, 4 older); test_owned_work.py false failures when two suite runs overlap.
