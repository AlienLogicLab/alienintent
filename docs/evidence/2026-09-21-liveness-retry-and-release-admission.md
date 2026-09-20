# Bootstrap evidence — judgment-required liveness retry, and incomplete release authorization

Date: 2026-09-21. Two incidents on 2026-09-20 during PY-07's release. Both are recorded because each
exposed a rule that was correct as written and wrong in effect. No lifecycle state was changed to
produce this record, and the running PY-07 invocation was not disturbed.

## Incident 1 — liveness retried a completed effect awaiting judgment

| Time (UTC) | Event |
|---|---|
| 16:54:46 | Coordinator moved PY-07 (#55) READY → IMPLEMENT under SWF-21 |
| 16:55:08 | Dispatcher launched PRODUCER `5185a4b3…` |
| 16:56:35 | Producer posted `RESULT=FOUNDER_EXCEPTION` — the Issue said implementation was not authorized and no baseline was named — and exited |
| 16:56:38 | Observer recorded the outcome, `requires_model_judgment: true`. Nobody was notified |
| 17:04:41 | Liveness watch: nonterminal state, no running actor, age > grace → `LIVENESS_GAP`, trigger re-emitted |
| 17:05:55 | Second producer refused identically |
| 17:06:09 | Observer recorded the second `FOUNDER_EXCEPTION` |

Nothing malfunctioned. The rule could not distinguish **"the actor never launched"** — a missing
effect, which is what liveness exists to repair — from **"the actor ran, finished, and returned a
result only a human can act on"**. Left alone it would have relaunched a producer every grace period
against a condition no number of retries could resolve.

> **Liveness reconciliation repairs missing effects; it must not retry completed effects whose result
> requires judgment.**

**Fixed** in [SWF-29](../decisions/2026-09-20-liveness-reconciliation.md): a completed correlated
outcome is evidence the actor *did* launch; a judgment-required outcome (`FOUNDER_EXCEPTION`,
`HumanDecisionRequired`, and the other blocking classes) suppresses recovery for that lane, creates or
retains a durable attention item, and waits. Recovery resumes only after explicit resolution —
acknowledgement of the attention item — or supersession by a newer non-judgment outcome.

Deterministic check implemented in the bootstrap watch (`judgment_suppression`): `FOUNDER_EXCEPTION`
recorded + no active actor + age > 5 min now yields `LIVENESS_SUPPRESSED` and an attention item,
never another producer. `test_liveness_suppression.py` — 8 tests, including that an older judgment
outcome does not block after newer progress, and that the suppression names the **same** attention
item the observer created rather than minting a second view of it.

## Incident 2 — incomplete release authorization produced two correct refusals

The release itself was the defect. The coordinator performed READY → IMPLEMENT without the release
record that PY-02…PY-06 each carried:

- **no named baseline** — the producer had nothing authoritative to build from, and a previous
  incident had already established that a producer must not select a baseline for itself;
- **contradictory durable text** — the Issue body still read *"Implementation is **not** authorized by
  this Issue. Release remains an explicit authority step."*

Both producers were **right to refuse**. The failure was upstream of them. Work proceeded only after
an explicit release record naming baseline `6c3f8432129892f11d182e713102e63cf0aa9b56` was posted and
the stale wording superseded; the third producer ran without refusing.

**Fixed** as an amendment to **SF-REQ-002 READY scheduling** ([#4](https://github.com/AlienLogicLab/alienintent/issues/4)),
with the bootstrap checklist in [SWF-21](../decisions/2026-09-20-wave1-release-coordinator.md):
implementation explicitly authorized; exact baseline named; baseline resolves; baseline reachable from
the intended release point; no stale unauthorized wording without a superseding record; no worker
launched until all pass. **A failed check is a refusal, not a warning.**

Implemented as `release_admission.py`, covered by `test_release_admission.py` (14 tests). Two live
validations:

```
$ python3 release_admission.py 56        # PY-08, not yet released
REFUSED: do not transition and do not launch a worker.
  - status_ready: Project status is 'TASKS'; release starts from READY.
  - implementation_authorized: No release record explicitly authorizes IMPLEMENT for this BIU.
  - authority_wording_consistent: The Issue still states implementation is not authorized, …
  - dependencies_satisfied: Open dependencies: [55].
```

Replayed against PY-07 exactly as it stood at 16:54, the gate refuses on `implementation_authorized`
and `authority_wording_consistent` — **the two grounds the producers themselves cited**. Run against
PY-07 now, every record check passes (baseline resolves, ancestral, wording consistent); the only
refusals are that it is already released and already running.

## What neither incident required

**No new Product Requirement.** SF-REQ-002 owns release admission and SF-REQ-056 already owns
canonical liveness reconciliation; both were amended. SWF-21 and SWF-29 carry the bootstrap-level
rules and remain explicitly temporary.

## Common shape

Both failures are the same shape as the activation gap recorded in
[SWF-27](../decisions/2026-09-20-persistent-control-plane-bounded-coordinator-episodes.md): a
deterministic mechanism behaving exactly as specified, on a condition its specification did not
distinguish. The remedy in each case is not a smarter daemon but a sharper boundary — *this is a
missing effect* versus *this is a completed effect awaiting judgment*, and *this BIU is eligible*
versus *this release is fully recorded*.
