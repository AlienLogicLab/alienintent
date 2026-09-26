# FX-B5 status — WO-220508 (Issue #128)

Recorded by PRODUCER invocation `AlienLogicLab/alienintent#128:PRODUCER:ce1a2eae-a310-483e-af55-0362eaf166cf`
(worker Morty), from admission baseline `62e693932dcbd6b6583a1d37b172f4b418af9256`. Operational
readback completed by PRODUCER invocation
`AlienLogicLab/alienintent#128:PRODUCER:81597f6b-79c4-4954-a6cd-ed1f9d15058a` (worker Morty).

**Overall: LOCAL proof COMPLETE; OPERATIONAL readback `OPERATIONAL_READBACK_COMPLETE`
(run `operational/20260926T204718Z`).** The operational result rests on the named human's own
acknowledgement on the operational root. No agent made that acknowledgement. Acceptance itself
remains for the independent VERIFIER.

## Pinned contract and candidate

| Record | Commit |
|---|---|
| Contract `FX-B5.md`, pinned before any source change | `e15a9d8` |
| Implementation, local probes, evidence runner, operational tool and regression pack | `e52cfdb004f51c87cfa4d911204a25f3276e9a3c` |

What the implementation adds:

- `AttentionService.acknowledge` and the `Acknowledgement` record.
- The operator surface `python -m alienintent.composition.attention_inbox`.
- The feature-regression pack `human-attention-acknowledgement`.

What it does not add: a notification channel, a Windows notification, an activation executor or
an external effect.

## LOCAL proof (label: LOCAL; never operational acceptance)

- Command:
  ```
  PYTHONPATH=src:. python3 -B tools/evidence/fx_b5_evidence.py --output /tmp/fx-b5-20260926T124502Z --invocation "AlienLogicLab/alienintent#128:PRODUCER:ce1a2eae-a310-483e-af55-0362eaf166cf"
  ```
- Source candidate: `e52cfdb`.
- Result: exit 0 and `run_state=COMPLETE`, with no holds.
- Probes: B5-01 through B5-10 all PASS.
- Controls: all four were applied once each (application count 1), and each discriminated between
  intact, fault and restored.
  - `delivery_counts_as_receipt`
  - `acknowledger_unchecked`
  - `duplicate_acknowledgement`
  - `acknowledgement_resolves`
- Retained at `local-run/20260926T124502Z/`, containing `execution-record.json`, `proven-red.json`,
  `run-report.json`, `digest-manifest.json` and `observations/`.

## Regression and suite readback (candidate `e52cfdb`)

- Feature regressions:
  ```
  python3 -B tools/verification/run_feature_regressions.py --base 62e693932dcbd6b6583a1d37b172f4b418af9256 --candidate HEAD --receipt /tmp/fx-b5-feature-regressions.json
  ```
  Exit 0 and `passed: true`. The selected packs were `local-bounded-control-capstone`,
  `supervised-monitor-host` and `human-attention-acknowledgement`. Receipt digest
  `sha256:21b337825b8ad5b659317446a4d8d27d3b977d63741b5a4b4bc2656bbf86e16b`; manifest digest
  `sha256:4ad5b63dc0b913dba9e0cc656184d0495515385c71bb2b274059886ed51dcaea`. Following the
  WO-220502 custody precedent, the receipt is not tracked. The invocation runtime regenerates it
  for the exact candidate before VERIFY.
- Full suite, `python3 -B -m pytest -q -p no:cacheprovider`: 25 failed, 1180 passed, 4 skipped.
  - Every failure is in `tests/evidence_learning/test_proof_planning.py`, which this BIU does not touch.
  - That file shows the same 25 failures at baseline `62e6939` (25 failed, 26 passed), so no new
    failure was introduced.
- Architecture check, `tools/fitness/check_architecture.py --root src/alienintent --check all`: PASS.

## OPERATIONAL target (authorized: the existing Python attention surface)

- Operational root (outside the repository): `~/.local/state/alienintent/fx-b5/attention`.
- Profile: `fx-b5-operational`. Named human acknowledger: `sanookdu`, the Founder.
- Prepared idempotently with:
  ```
  python3 -B tools/live/fx_b5_operational.py prepare --acknowledger sanookdu --invocation <above>
  ```
  No notification, no activation.

  | Kind | Identity | Version | Status |
  |---|---|---|---|
  | JUDGMENT | `attention:ff18a00138eaaa725e2ee26bf56be0f85f574572959278b029896c0e0fd0a053` | 1 | PENDING |
  | DONE | `attention:961de2349200a4690761383436513a06c443abed9f589c07a3f9de187db8e679` | 1 | PENDING |

- Readback immediately after prepare: `HOLD` / `HUMAN_ACKNOWLEDGEMENT_ABSENT` (exit 2). It is retained
  at `operational/*-prepared-hold/readback.json`. Both items are in the pending queue and neither is
  acknowledged.

### Human acknowledgement step (human only; performed)

The named human, and only that person, acknowledges the JUDGMENT item from a shell in a checkout
of the candidate:

```
PYTHONPATH=src python3 -B -m alienintent.composition.attention_inbox --config ~/.local/state/alienintent/fx-b5/attention/attention-inbox.json list
PYTHONPATH=src python3 -B -m alienintent.composition.attention_inbox --config ~/.local/state/alienintent/fx-b5/attention/attention-inbox.json acknowledge attention:ff18a00138eaaa725e2ee26bf56be0f85f574572959278b029896c0e0fd0a053 --actor sanookdu --expected-version 1 --statement "<your own acknowledgement text>"
```

Acknowledging the DONE item is optional.

A later PRODUCER cycle then runs the readback and retains it:

```
python3 -B tools/live/fx_b5_operational.py readback --output docs/evidence/wave2-proof-fixtures/FX-B5/operational/<UTC ts>
```

The expected result is `OPERATIONAL_READBACK_COMPLETE`, binding the item, the acknowledgement and
the PENDING→SEEN `ACKNOWLEDGED` transition with rehashed immutable refs. That PRODUCER cycle then
publishes the candidate for VERIFY.

## OPERATIONAL readback — `OPERATIONAL_READBACK_COMPLETE`

The Founder, `sanookdu`, acknowledged the JUDGMENT item at `2026-09-26T20:25:11.958225+00:00` with
the statement "I authorize 128". The Factory Director independently checked that record against the
operational store before removing the hold (Issue #128, comment 2026-09-26T20:30:20Z). This
PRODUCER cycle did not write to the operational root. It only read it back.

- Command, from candidate checkout `0d2030500d4172e1d52990d8d76afd290325ea92` (candidate
  `f72947d` merged with `origin/main` `fb437f4`, which changes docs only):
  ```
  PYTHONPATH=src python3 -B tools/live/fx_b5_operational.py readback --output docs/evidence/wave2-proof-fixtures/FX-B5/operational/20260926T204718Z
  ```
- Result: exit 0, `result=OPERATIONAL_READBACK_COMPLETE`, `holds=[]`, read at
  `2026-09-26T20:47:18.767531+00:00`. Retained at `operational/20260926T204718Z/readback.json`,
  sha256 `3c70ecfc74f0000eb2708af20961ef8a858b44616b6be04e44c6a319a1971410`, as recorded in its
  `digest-manifest.json`.
- The readback binds three things:

  | Binding | Readback |
  |---|---|
  | Item | JUDGMENT `attention:ff18a001…a053`; origin matches; `item_bound=true` |
  | Acknowledgement | actor `sanookdu`, who is the configured human (`actor_is_configured_human=true`); acknowledged version 1 through history ref `sha256:58826a15…7f0c`; `receipt_equals_entry=true` |
  | Transition | version 1 `CREATED`/PENDING to version 2 `ACKNOWLEDGED`/SEEN; both evidence objects present, with `rehash_matches=true` (current `sha256:2a18ebef…a40`) |

- Queue state:
  - Both items are still in the pending queue. The JUDGMENT item is SEEN and not RESOLVED, so
    suppression is intact. The DONE item is PENDING and unacknowledged, which the contract allows.
  - There is exactly one `ACKNOWLEDGED` entry, so there are zero duplicates.
  - There are no other attention identities.
- Feature regressions at candidate `0d20305`:
  ```
  python3 -B tools/verification/run_feature_regressions.py --base 62e693932dcbd6b6583a1d37b172f4b418af9256 --candidate HEAD --receipt /tmp/…
  ```
  Exit 0 and `passed: true`. The packs were `local-bounded-control-capstone`,
  `supervised-monitor-host` and `human-attention-acknowledgement`. The receipt is not tracked; the
  runtime regenerates it for the exact candidate.

Non-claims are unchanged: no release, cutover, retirement, Windows notification, replacement channel
or unattended activation.
