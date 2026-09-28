# FX-B8 — attention waiter and resident tenure preparation

Status: LOCAL_PREPARATION_ONLY for WO-220511/#134. Predecessor WO-220602/#131 remains TASKS under a Founder hold; no successor operational attention path or B8-specific tenure owner disposition is bound.

Authority reconciliation: the binding [2026-09-26 Wave 2 delegation](../../decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md) disposes POSTW1-DECIDE-006A, SWF-21_SCOPE_DISPOSITION and ATTENTION_ACTIVATION_AUTHORITY for approved replacement work within its bounds; Windows notification is not required. The B8-specific resident tenure decision and #131's held replacement-path predicate remain to be checked against exact owner records. This pin does not assert those are closed.

## Executable local probes

Run from the repository root at the recorded source SHA. These commands use disposable stores and injected time; they do not demonstrate an authorized operational handoff:

```sh
python3 -m pytest -q tests/control_plane/test_episode_control.py
python3 -m pytest -q tests/control_plane/test_attention_acknowledgement.py
```

Record exact exit codes and case results. The first suite discriminates age, transitions, block duration, contradiction, authority revision, deadline/restart, bounded usage and epoch renewal. The second discriminates durable pending, seen versus resolved, duplicate handling, judgment suppression, and restart. The semantic truth of a contradiction and human receipt still require independent judgment.

Local observation on 2026-09-28 at code baseline `4fd779843a951bbed3ca7ad09dc4a26e469e054f`: first command exit 0, 55 passed; second command exit 0, 15 passed. No operational probe was run.

## Required intact, fault, restored operational contrast

After #131's accepted replacement-path proof and explicit owner dispositions: (1) inventory pending/unresolved product attention and separate programme mailbox duties at an agreed checkpoint; (2) deliver one authorized harmless attention through the successor and read back handling exactly once; (3) interrupt delivery and restart the successor, requiring durable pending identity and suppression; (4) trigger each bounded tenure exit, including an independent timer and a relevant vector change, then reconstruct in fresh context with equivalent authority and no lost duties; (5) restore and read back both wake-up paths, monitor health, checkpoint and incumbent continuity. The successor target, exact live command, budget, and authority are **UNBOUND**. No operational case has run.

## Evidence record

Retain `FX-B8/<run-id>/execution-record.json` with `proof_level`, source/candidate/fixture SHA, #131 receipt and candidate SHA, target/profile/policy digest, command and exit status, before/after pending and handled identity sets, programme mailbox count, delivery and handling counts, tenure epoch/deadline/revision, authority vector, monitor readback, old-waiter readback, and independent verdict ref. Preserve raw observations by SHA-256, `digest-manifest.json`, and `proven-red.json`. An absent count or readback is `UNKNOWN`, never zero.
