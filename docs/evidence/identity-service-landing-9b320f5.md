# Identity service landing record (9b320f5)

Unit: IDENTITY-SERVICE-AND-COMPILER-CONNECTION. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `9b320f5bb02241a1fca855f95b33551489f19d2f` (branch `producer/identity-service-ddff1ac`). It is round-1 candidate `ba3f33cd` plus one repair commit.
- Merge base: `origin/main` `7901011d599aceb0347a1efbef42cb02d2bbcfc0`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/identity-service-and-compiler-connection.md` at `ddff1ac46df6263654d549ff6157a12b51b7d988` (revision 14). The landed code cites this path, so the file was added to `main` byte-for-byte from that commit (blob `8640648279786d175a5e4f2145d5ddf3a81ff8b1`). Nothing else from the design branch was merged.

## Approvals (private records, outside the repo; paths only)

- Agent Ready: READY for packet `ddff1ac`. Record directory: `~/.local/state/alienintent/manual/identity-service-agent-ready-ddff1ac/`.
- Founder implementation approval: `~/.local/state/alienintent/manual/identity-service-agent-ready-ddff1ac/implementation-approval.json`.

## Independent verification

| Round | Candidate | Verdict | Suite | Fitness | Feature regressions | Record |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `ba3f33cd` | REJECT (two required section 17 negative checks not caught: one pointer transaction, and database-level `UNIQUE(request_ref)`; plus a ROLLBACK error-masking fix) | 1479 passed, 4 skipped | PASS | passed (3 packs) | `~/.local/state/alienintent/manual/identity-service-verification/round1-ba3f33c/verdict-ba3f33c.md` |
| 2 | `9b320f5b` | ACCEPT (round-1 findings 1–4 closed; no blocking findings) | 1481 passed, 4 skipped | PASS | passed (3 packs) | `~/.local/state/alienintent/manual/identity-service-verification/round2-9b320f5/verdict-9b320f5.md` |

Verifier commands (round 2):

- `python3 -m pytest -q -p no:cacheprovider`
- `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`
- `python3 tools/verification/run_feature_regressions.py --base 7901011 --candidate 9b320f5bb02241a1fca855f95b33551489f19d2f --receipt <scratch>/regress-receipt.json`

## Settled dispositions

- **(a) `RefPublisher` port.** `RefPublisher` in `src/alienintent/context_assembly/ports/work_item_repository.py` and `SourceControlRefPublisher` in `src/alienintent/composition/work_registry.py` are the packet's section 6 publishing boundary. They do not change behaviour: the adapter only turns a `PacketRef` into a `PublishRef` and calls the one `publish_refs` operation. They exist because the existing test `tests/context_assembly/test_ambiguity.py::test_upstream_composition_has_no_worker_path` forbids any `context_assembly` module from importing `invocation_runtime`. A direct import, as the packet first wrote it, would have failed that test.
- **(c) Two extra failure codes.** `TAG_WRITE_FAILED` (the database committed but the tag was not set; repeat the request) and `TRANSACTION_HELD` (register or import_completed with a pointer was called inside a transaction the caller already holds; the call is refused and writes nothing) are kept. They are additions to the packet's section 11 failure list.
- **(h) Live wiring is a follow-up.** Building a live profile with a `WorkRegistry` is outside this unit's permitted files and acceptance checks. It is a follow-up item.
- **(i) Stale evidence controls are a follow-up.** Stale controls in `tools/evidence/fx_u8_evidence.py` and `tools/evidence/fx_a_evidence.py` are outside this unit. They are a follow-up item.

Also follow-up, all non-blocking: verifier round 2 findings N1–N4, and round 1 low findings 5–8 (see the round 2 verdict, section 7).

## Landing checks

The closure owner ran the full suite, the architecture fitness check and the feature regressions again on the final merged tree before pushing. The results are in the merge report to the Founder; any new failure would have stopped the push.
