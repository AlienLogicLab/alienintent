# WO-220201 historical corpus CI repair

## Authority and admission

Issue #76 release 5792028317 and return-to-IMPLEMENT comment 5792670883
bound this repair to CI access to the exact historical corpus. Invocation:
`AlienLogicLab/alienintent#76:PRODUCER:486061b7-3bae-41c2-98c5-cc54adce99de`.
Morty / morty-worker owns runtime resource and branch
`b-disp/cabbf3f6-a7ad-4af5-8cf9-40b06de6babc`. Clean admission at
`901d17444aa0aa1e5098017c3726d0d0daad1442`, matching remote main;
fast-forwarded to accepted candidate `4a2276592d5e579b57c8277e27ef01c6ecf61ebe`.
Runtime records match this invocation, IMPLEMENT, WIP one, systemd supervision;
active profile retains three cycles and one replacement per phase.

## Proof pinned before configuration repair

Remote Python run 35844555733 fails the two historical inventory tests because
checkout depth one lacks `d83e87e6f2bb4ff90ff4f4f0e3940582f8d5c998`.
The adapter reads exact Git blobs from that revision. Fetch full history with
checkout `fetch-depth: 0`; do not change parser, manifest, tests or assertions.

Reproduce in a disposable depth-one clone of the prior candidate using
`python3 -m pytest -q tests/context_assembly/test_inventory.py -k
"historical_exact_manifest or source_scope_digest_and_provenance"`:
expect two failures with missing historical blobs. Fetch full history via
`git fetch --unshallow origin`, rerun the identical tests, expect two passes.
Record commands, exit codes, counts and log hashes. Remove the disposable clone
after verification. Run full Python, architecture fitness and Node checks on the
candidate; require exit zero. Publish and observe both remote CI workflows on the
exact candidate before submitting VERIFY. Independent review remains required.

Preserve all existing source, tests and evidence byte-for-byte: original/repair
proof, exact 17-document 56/53 sets/forms/locators, twelve controls, history,
retirement, local holds and CAS proof. Prior acceptance and passing local checks
remain historical observations; they never established passing remote CI.
No evidence is superseded. Replacement proof concerns checkout prerequisites only.

## Boundaries and disposition

Only the assigned candidate branch may be pushed. No main push, merge, deployment,
live operation, bootstrap retirement, other-repository or lifecycle changes.
Runtime-managed resources remain retained for fresh verifier retrieval and BIU
closure. Tokens and cost UNKNOWN.

## Observed local validation

Proof pin commit: `13f13bc` precedes the workflow change.
Only the workflow and this record differ from accepted candidate `4a227659`;
all prior implementation, tests, tools and evidence remain byte-for-byte unchanged.

- Depth-one clone of prior candidate: two historical tests fail, exit 1;
  both fail on missing pinned Git blobs (git show exit 128).
- `git fetch --unshallow origin`: exit 0. Identical two tests then pass,
  13 deselected, exit 0. No files changed in the reproduction clone.
- `python3 -m pytest -q`: 482 passed in 63.82s, exit 0.
- `node scripts/check.mjs all`: runtime 332/332, preflight PASS, RAI 18/18,
  policy 3/3, exit 0.
- `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`:
  PASS, exit 0. `git diff --check`: exit 0.
- Read-only internal review: no blocking findings; pinned corpus revision is
  ancestral. Fresh independent BIU verification remains required.

Diagnostic logs are outside the worktree at `/tmp/wo-220201-ci-486061b7/`.
The disposable reproduction clone was DISCARDED and removed after confirming
clean state and exact prior candidate HEAD. Its logs remain available locally.
The runtime-owned candidate is retained for BIU retrieval/closure.
Remote CI outcomes on the published exact SHA will be recorded in the invocation
Issue comment; local results alone do not establish remote success.

Log SHA-256:

- `shallow-red.log`: `0cc80d7c3ea4920e6b0c751fda2344203305c468948553808dc6376f59620e42`
- `fetch.log`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `full-history-green.log`: `f53c267d3e430997303d8ff448ce6e094df047afdd36a7e9b3afacb1e9989624`
- `python.log`: `8ad85f7c81b9be1376d6151e836be8542159491c60cd8f4463701dda4e49114f`
- `node.log`: `9aedbc4162a98e7e231ae8b76f2765e55aba8a0d780e057ee9b02fe469ba5e61`
