# POSTW1-GAPTRAP-003-R1 — one label, two records

Fresh Codex GPT-6 Astra. `workspace-write`, solely to edit
`docs/evidence/wave1-gap-trap-promotion-backlog.json` and its `.md` companion. Smallest possible
repair; change nothing else.

## The finding

Coordinator review of your backlog: the promotions and the eleven declines stand, and the
declines are well-reasoned — recurrence of 1, `proven_red: no`, or genuine semantic judgment,
each with a revisit condition. No promotion is challenged.

One label is wrong in a way that will propagate. `suspected_classes` uses a single `UNSUPPORTED`
status for two materially different findings:

- **BIU identifier parser assumptions** — genuinely unsupported. RAW-090 is HYPOTHESIS and D8 is
  participant testimony. Correct as it stands. (For the record, and not a reason to change the
  status: the coordinator confirms the incident happened, but the tooling that held the defect
  lives outside the repository, so durable evidence cannot establish it. Participant memory is
  not authority. Your call is upheld against the participant's own recollection.)

- **config validation before service restart** — *not* unsupported. LRN-021 carries
  `proven_red: yes` and `enforcement_level: DETERMINISTIC_GATE`; the loader demonstrably rejected
  the unsupported key fail-closed. Your own `finding` text says this. The class is **established
  and already owned**; it is outside the 18 only because ALREADY_GRADUATED records were not in
  the candidate set. Labelling it `UNSUPPORTED` tells a Phase 14 reader the evidence does not
  establish the class, which is the opposite of what the evidence shows.

You were right not to invent a promotion for a record outside your candidate set. The repair is
to the label, not to the judgment.

## The repair

1. Introduce a status that distinguishes the two cases. Use `ALREADY_OWNED` for the config
   validation class, keep `UNSUPPORTED` for the BIU identifier parser class, and keep `CONFIRMED`
   for the six confirmed classes.
2. Add a short `status_basis` to every `suspected_classes` entry stating why it holds that
   status — for `ALREADY_OWNED`, name the owner and the proven-red evidence; for `UNSUPPORTED`,
   state what evidence would be required.
3. Update the `.md` companion and any summary field that counts unsupported classes, so the
   counts match the records.

Do not change any promotion, any decline, any candidate field, or any reasoning text beyond what
these three items require.

## Acceptance

```
python3 tools/evidence/check_gap_trap_backlog.py    # must still exit 0
python3 tools/evidence/check_wave1.py --negative-controls   # must still pass
```

Do not edit either checker. If you dispute this finding, say so in `DISPUTED` and leave the
artifact unchanged — the previous phase's dispute was upheld and found a real defect in the
checker, so disputing is a wanted outcome, not a failure to comply.

## Out of scope

No re-derivation, no new candidates, no requirement creation, no Learning Ledger edits, no
lifecycle/Project/worker-contract changes, no commit, no network, no Phase 4.

## Terminal report — this block only

```
CONFIRMED=<n>
ALREADY_OWNED=<n>
UNSUPPORTED=<n>
PROMOTIONS_UNCHANGED=yes|no
DECLINES_UNCHANGED=yes|no
BACKLOG_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED=<or NONE>
NOTES=<one line, or NONE>
```
