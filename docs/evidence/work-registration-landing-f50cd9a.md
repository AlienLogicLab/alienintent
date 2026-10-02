# Work registration landing record (f50cd9a)

Unit: WORK-REGISTRATION-AND-FAMILY-HISTORY. Landed by direct merge into `main`. No pull request.

## What landed

- Accepted candidate: `f50cd9abaeefa11087ff2d79261d6c3f9e47621d` (branch `producer/work-registration-a133123`). It is round-1 candidate `de5794bb8050534b205c03497ec1c636cd340658` plus one repair commit.
- Merge base: `origin/main` `5020a675a0bd0f08161ab004f0c24f7ee65f33df`. The candidate was merged with `--no-ff`, so the accepted SHA stays in `main`'s history.
- Approved packet: `docs/work-units/python/work-registration-and-family-history.md`, assessed at `a133123915e7c18ce065fee6da4d07e3f92ebb6d`. The file was already on `main` at `5020a67`, byte-for-byte equal to the assessed revision (blob `1d5b3950b2419166de3506549218c275042e1f8f`). The candidate does not change it.

## Approvals (private records, outside the repo; paths only)

- Agent Ready: READY for packet `a133123`. Record directory: `~/.local/state/alienintent/manual/work-registration-agent-ready-a133123/` (`native-result.json`, `owner.json`).
- Founder implementation approval: `~/.local/state/alienintent/manual/work-registration-agent-ready-a133123/implementation-approval.json`.
- Three independent design reviews: `~/.local/state/alienintent/manual/work-registration-agent-ready-a133123/independent-review-*.md`.

## Independent verification

| Round | Candidate | Verdict | Tests (four permitted files) | Fitness | Record |
| --- | --- | --- | --- | --- | --- |
| 1 | `de5794b` | REJECT (B1: a mutation of the digest comparison was not caught by any test) | 92 passed | PASS | `~/.local/state/alienintent/manual/work-registration-verification/round1-de5794b/verdict-de5794b.md` |
| 2 | `f50cd9a` | ACCEPT (B1 closed: the mutation is now caught; no blocking findings) | 93 passed | PASS | `~/.local/state/alienintent/manual/work-registration-verification/round2-f50cd9a/verdict-f50cd9a.md` |

The four permitted test files:

- `tests/context_assembly/test_work_registration.py`
- `tests/context_assembly/test_work_identity_service.py`
- `tests/composition/test_work_registry.py`
- `tests/control_plane/test_cli.py`

Fitness command: `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`

## Follow-ups (all non-blocking)

- Round 1 N1: a moved-pointer mutation is caught by check 1 only.
- Round 1 N2: the CLI `--kind` default repeats `DEFAULT_KIND` instead of using it.
- Round 1 N3: error labels. `work show` on a non-UTF-8 packet reports `invalid-command-arguments`; a bad `--assessment` or a missing `--file` reports `internal-error`.
- Round 1 N4: `work show` takes the write lock.
- Round 2 N1: a comparison that strips trailing whitespace on both sides still passes the tests.

## Landing checks

`origin/main` had not moved since `5020a67` when the candidate was merged. The merged tree is identical to the verified candidate tree (`git diff --quiet f50cd9a HEAD` before this record was added), so the verifier's round 2 results apply to it unchanged. No tests were run again.
