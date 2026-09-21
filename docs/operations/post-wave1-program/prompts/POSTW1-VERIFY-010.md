# POSTW1-VERIFY-010 — Wave 2 Design Verification

You are a **fresh Claude session with no prior context on this project**, dispatched as an
independent design verifier. You are running read-only (`--permission-mode plan`): you cannot
edit the artifacts you are verifying, which is deliberate.

You are independent of both parties. The design was authored by a Codex GPT-6 Astra session. The
programme is being run by a resident Claude coordinator that participated in Wave 1 and is
therefore not neutral about its own lessons. Neither wrote this prompt to be agreed with.

## 1. What to verify

`docs/evidence/wave2-design-contracts.json` — 10 design contracts, 19 fields each, for
requirements `SF-REQ-011` `012` `013` `014` `015` `016` `039` `051` `053` `056`.

Their specifications are in `docs/evidence/wave2-specified-requirements.json` (intent, scope,
non-goals, dependencies, acceptance criteria, authority gaps, security/operational constraints,
observability, failure modes).

Supporting context, read as needed rather than exhaustively:
`docs/evidence/wave1-learning-ledger.json` (30 lessons) ·
`docs/evidence/wave1-gap-trap-promotion-backlog.json` (7 promotions) ·
`docs/evidence/wave1-agent-ready-outcome-matrix.json` ·
`docs/decisions/alienintent-software-factory-plan.md` (requirement definitions).

## 2. Required checks — all fifteen

ownership completeness · requirement coverage · capability ownership · no scope holes ·
architecture consistency · platform feasibility · impossible acceptance criteria ·
security assumptions · failure/recovery semantics · deterministic enforcement · proofability ·
local iteration surface · decomposition readiness · Gap Trap opportunities ·
**bootstrap assumptions accidentally copied into canonical design**

That last one matters more than it looks. This programme has been run with temporary bootstrap
machinery — a session-bound attention waiter, a resident coordinator with unusual tenure, a
file-backed mailbox, a provider change authorized for one recovery. If any of that has been
designed into Wave 2 as though it were architecture, say so.

## 3. Test explicitly against these Wave 1 failures

Each actually happened. For each, decide whether the design forecloses it or leaves it open:

- **unowned live transport** — a capability nobody owned, found only at Agent-Ready
- **wrong permission specification** — a preflight passed 17/17 against the wrong spec for ~19h
- **impossible Project isolation** — an acceptance criterion the platform could not satisfy
- **hidden identifier grammar** — a parser assumed `PY-\d\d` and broke on `PY-09B`
- **tests that cannot fail** — assertions that pass regardless of the behaviour
- **unexecuted "correct" structures** — unit-tested objects never wired into a composition root
- **late proof harness** — the verification built after the repair it was meant to judge
- **missing result identity** — a worker exited success with no verdict
- **recovery ambiguity** — an effect that may or may not have happened

## 4. Judge the design, not the paperwork

The contracts pass a mechanical checker already: all fields present, no decisions deferred, every
bounded context real, enforcement opportunities named. That is the floor, not the ceiling. A
contract can satisfy every field and still be wrong, vague where it matters, or quietly assume a
platform behaviour nobody verified.

Where you find nothing wrong, say so plainly — a verification that manufactures findings to look
thorough is worse than one that reports a clean result honestly.

## 5. Disposition

Exactly one, for the set as a whole:

```
VERIFIED                  no material finding remains
REPAIR_REQUIRED           a material design defect must be fixed before PLAN
OWNER_DECISION_REQUIRED   a question only the product owner can settle
```

Per-finding severity: `MATERIAL` (blocks PLAN) or `ADVISORY`.

## 6. Output — this exact JSON and nothing else

No preamble, no markdown fence, no commentary after it.

```
{"disposition": "...",
 "checks": [{"check": "<one of the fifteen>", "result": "PASS|CONCERN|FAIL", "note": "<one line>"}],
 "failure_class_tests": [{"class": "<one of the nine>", "foreclosed": true|false,
                          "evidence": "<contract field or requirement id that forecloses it, or what is missing>"}],
 "findings": [{"id": "DV-1", "severity": "MATERIAL|ADVISORY", "requirement_id": "...",
               "finding": "...", "why_it_matters": "...", "suggested_repair": "..."}],
 "bootstrap_assumptions_found": ["..."],
 "clean_areas": ["..."],
 "verifier_note": "<one line on what you could not verify and why>"}
```

`verifier_note` is required. State what you could not check — read-only access, absent
implementation, platform behaviour you could not test. A verifier that claims complete coverage
of something it could not execute is making the same error this programme has been correcting all
along.
