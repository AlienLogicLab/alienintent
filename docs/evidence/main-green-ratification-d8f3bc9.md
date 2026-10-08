# Founder ratification and verification evidence: MAIN-GREEN

Companion to the Landing Authority's landing record for this item (that record's commit may add only itself).

- work item: ec72af73-e93c-47e2-b9b5-f8423dbffd2a
- label: MAIN-GREEN
- candidate: d8f3bc9c74f9bffa6fb5838bab3452b9d787ad79
- base: 7286fe36c15625a09e2ffbe5b80e830fa1197931
- merge: dd2ebd6ec0fb20f684ffca5def56702f4d3f3e86
- landing record: docs/evidence/main-green-landing-d8f3bc9.md (commit f7bfcf83bad6dadef0d69de4dd7d9184bd39d40d)
- instructions sha256: 64f915e24749c09d64eefa2ce04547b5aae10f480a0665f2c4d86f3fb4281b64
- verifier correlation: launch:ec72af73-e93c-47e2-b9b5-f8423dbffd2a:2

## Founder ratification (2026-10-08)

The Founder's approval was "subject to the exact assessed packet". The candidate departs from packet section 2.2 in
one fixture-only step. For the dependency case, `seed_invalid_state_for_defense_in_depth_test` rewrites the newly
registered fixture work item's identity to the literal dependency identity before admission. It then deletes that
row, as the packet requires. The Founder ratified it before CLOSURE, in these words:

> I ratify the MAIN-GREEN candidate's fixture-only deviation in `seed_invalid_state_for_defense_in_depth_test`: for
> the dependency defense-in-depth case, the helper rewrites the newly registered fixture Work Item's identity to the
> literal dependency identity before admitting the tested item and deleting that dependency row. This preserves the
> assessed intent: normal satisfiability/admission remains unchanged, the invalid state is created only below
> admission for context-assembly defense-in-depth testing, and no production rule is weakened. This ratification
> applies only to candidate `d8f3bc9`.

The deviation is accepted as a valid realization of the requirement. It is not recorded as debt.

## Verification evidence

- **Regression gate** (control plane, as the worker, before the VERIFIER session): baseline `7286fe3` gave 43 failed,
  2849 passed, 7 skipped; candidate `d8f3bc9` gave 2894 passed, 7 skipped, 0 failed, 0 errors. No finding. Receipt
  `feature-regressions:sha256:edb5c51720cf2adcf31135e5f396d458465db0bbcdf375da4e5082787e2526ca`.
- **VERIFIER** (`launch:ec72af73-e93c-47e2-b9b5-f8423dbffd2a:2`): accept, no findings.
- **Independent whole-suite run** by the Factory Director, as the worker through the factory's own environment:
  2894 passed, 7 skipped.
- **Mutations rerun by the Factory Director** on the exact candidate (the verdict file has no field for them), each
  with `PYTHONDONTWRITEBYTECODE=1`:
  - M1 (restore the worker-port import): `test_no_new_cross_group_import_pair` fails; passes when reverted.
  - M2 (`Cx.packet` inherits `contract_payload`): fails with `AUTHORIZATION_STALE`; passes when reverted.
  - M3 (fixed marker `launch:AC08:1` while another process holds it): fails (`assert (326688,) == ()`); passes when
    reverted, with that process still alive.
  - M4 (skip the direct deletes): exactly refs7, refs8 and refs9 fail; all ten pass when reverted.

Main is green: this is the first end-to-end proof of the whole-suite gate on real repository debt.
