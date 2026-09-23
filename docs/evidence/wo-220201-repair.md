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
