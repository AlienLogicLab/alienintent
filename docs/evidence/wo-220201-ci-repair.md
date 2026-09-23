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
