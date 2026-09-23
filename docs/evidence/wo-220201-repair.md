# WO-220201 repair contract and execution record

## Authority and admission

Issue #76 release 5792028317 and verifier rejection 5792448036 authorize the two
bounded repairs. Invocation: AlienLogicLab/alienintent#76:PRODUCER:3f47a296-d48a-40bf-8dd7-6878e2261fa6.
Morty / morty-worker owns runtime-managed branch
`b-disp/2348449f-b04b-4db0-8d2b-b634927d90d4` in its assigned isolated worktree.
Clean admission baseline and remote main: `901d17444aa0aa1e5098017c3726d0d0daad1442`.
Fetched prior candidate `e5cbf50c19a059c5db05c749cbdba7db21b0dc8f` and advanced
this branch by fast-forward. Existing evidence is preserved verbatim. Active profile
binds #76 to 3 cycles and 1 replacement per phase. No other repository or live action.

## Replacement proof pinned before repair

Retain the original FX-U1 contract, exact 17-document 56/53 sets/forms/locators,
all 10 discrimination controls, retirement/history/local-hold/CAS proofs, and prior
raw evidence. No prior evidence is removed or superseded; these proofs extend it.

Add regression assertions for balanced and escaped Markdown destination parentheses,
exact label and following-token columns, malformed labels, and incomplete destinations.
Valid destinations contribute no identifiers; malformed labels still hold their span.
Add cross-format link-set permutation/duplicate assertions: one revision, both links,
stable authority/dependencies, no stale downstream links solely due to order; actual
link changes still create a revision and stale links.

Commands: `rtk proxy python3 -m pytest -q tests/context_assembly/test_inventory.py`
(red before repair, green after); `rtk proxy python3 -m pytest -q`;
`rtk proxy node scripts/check.mjs all`;
`rtk proxy python3 tools/fitness/check_architecture.py --root src/alienintent --check all`;
`rtk proxy env PYTHONPATH=src python3 tools/evidence/fx_u1_evidence.py --output /tmp/wo-220201-repair-fx --invocation AlienLogicLab/alienintent#76:PRODUCER:3f47a296-d48a-40bf-8dd7-6878e2261fa6`.
Pin two additional independent mutations reverting the repairs. Expect 12/12 controls
with intact/restored exit 0 and fault assertion failures. Retain schema from original
contract with accurate current invocation, command/status/raw-log digest and source
digests. Full suites must exit 0. Token/cost UNKNOWN. Publish branch and exact SHA;
retain runtime-managed resources for independent verifier and BIU closure.

## Internal review repair

A read-only reviewer reproduced a regression in the first repair: literal parentheses
inside angle-delimited destinations were incorrectly balanced. Added a failing
regression before repair, then taught the scanner to respect the angle-delimited
boundary. Both targeted tests now pass, including opening and closing literal
parentheses. Full validation is rerun against the final implementation; intermediate
runs are not final source proof. The original candidate evidence remains untouched.

Follow-up review also exercised leading whitespace before angle destinations and
single/double quoted titles containing parentheses. Those variants were reproduced
red, then covered by destination/title states. Final read-only review at
`c25c378115881bf6e3e2d48504cce20cdc19e067` found no remaining bounded findings and
independently reran both regression tests (2 passed, exit 0).

## Final validation

- Full Python suite at final implementation: 482 passed in 72.47s, exit 0.
- Node checks: runtime 332/332, preflight PASS, RAI 18/18, policy 3/3, exit 0.
  Node inputs were unchanged by the later Python-only boundary repair.
- Architecture fitness at final implementation: PASS, exit 0.
- Original proof, initial/final FX-U1 artifacts and predecessor evidence remain
  byte-for-byte unchanged relative to the prior published candidate.
- Durable runtime readback binds this exact invocation and worktree resource;
  active count one, systemd supervision with 7200000 ms runtime limit.

Portable final proof is retained under `wo-220201-fx-u1/repair/`; operational
SQLite state stays outside the repository. The pre-repair red log records exactly
2 failures and 13 passes. Intermediate runs in /tmp are diagnostic only and do
not substitute for final source-bound proof. Tokens and cost remain UNKNOWN.

## Custody disposition

Runtime-managed candidate remains retained for fresh independent verification and
BIU closure. It is not LANDED or accepted; verifier retrieval is the next gate.
Only the assigned candidate branch is published. No main push, lifecycle mutation,
deployment, live operation, other-repository mutation, or bootstrap retirement.

Final FX-U1: **12/12 controls discriminate**, 36 intact/fault/restored observations,
exit 0. Original 10 controls plus independent reversions of both repairs. Report binds
implementation `c25c378115881bf6e3e2d48504cce20cdc19e067` and exact source digests.
Raw-log hashes, digest-addressed evidence objects and implementation hashes verify.
Historical exact sets/forms/locators still pass (56 referenced, 53 defined).
Raw logs retain original whitespace; source/document whitespace checks pass.
