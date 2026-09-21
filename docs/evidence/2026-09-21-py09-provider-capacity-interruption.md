# PY-09 provider-capacity interruption and alternate-provider recovery

Date: 2026-09-21. Wave 1 bootstrap evidence. No Product Requirement is created by this record.

## What happened

| | |
|---|---|
| Invocation | `AlienLogicLab/alienintent#57:PRODUCER:e84d12a0-696b-4d82-842a-7c425747b364` |
| Started → ended | `02:06:56Z` → `02:12:46Z` (**350 s**) |
| Provider | `codex`, funding profile `provider-default` |
| Provider message | `turn.failed` — *"You've hit your usage limit … try again at 6:22 PM"* |
| Recorded outcome | **`DURABLE_RESULT_MISSING`** — no result marker was ever posted |
| Work at interruption | suite at `33 passed, 2 failed`, mid-edit on `tests/installation/test_doctor.py` |
| Partial work | worktree `63097907-ffb9-411c-a59c-d353c09e8a7e` — `doctor.py`, `test_doctor.py`, `test_doctor_evidence.py`, **65 insertions / 60 deletions**, uncommitted |

The producer was working normally on exactly the cycle-3 verification findings when its provider quota
ran out. This is the SWF-09 condition in practice: token and monetary budgets are **measured**, not
hard-enforced, for CLI providers, so exhaustion arrives as a dead invocation rather than a clean
budget refusal.

**Classification: provider-capacity interruption.** Not an implementation rejection, not a repair-cycle
failure, and not counted as a failed repair cycle. Cycle 4 continued; it did not restart.

## The suppression rule earned its keep

This is the first real case where the [SWF-29 amendment](../decisions/2026-09-20-liveness-reconciliation.md)
prevented a provider-burning retry loop rather than a hypothetical one.

`DURABLE_RESULT_MISSING` is a judgment-required outcome, so liveness reconciliation was **suppressed**
for the lane: `judgment_suppression` returned `ATTENTION_WAIT (DURABLE_RESULT_MISSING)` and the watch
did not re-emit the lifecycle trigger. Without it, PY-09 sat in `IMPLEMENT` with no actor and an
expired grace period — precisely the shape that fires recovery. Every five minutes for the nine hours
until the quota reset, a producer would have launched, hit the same wall within minutes, and died.

**No relaunch loop occurred.** The attention item stayed open, unacknowledged, for the duration.

### `SEEN != RESOLVED`

The rule only works because acknowledgement carries meaning:

```
SEEN          != RESOLVED
ACKNOWLEDGED  == RESOLVED / SUPERSEDED
```

The coordinator saw the item immediately — the wake-up bridge delivered it within ~30 seconds — and
deliberately did **not** acknowledge it, because seeing a blocked condition does not unblock it.
Acknowledgement came only after the provider change was valid, a replacement producer could actually
launch, and the preserved worktree was confirmed ready. Current attention semantics state that
acknowledgement lifts suppression; they do not say in so many words that acknowledgement *asserts
resolution*. Recorded here as evidence for later reconciliation rather than changing live Wave 1
semantics mid-incident.

## Recovery

Founder authorization, 2026-09-21: route the replacement PRODUCER through the already-configured
`claude` adapter rather than waiting ~9 hours for the quota reset.

| | Before | After |
|---|---|---|
| adapter | `codex` | **`claude`** |
| executablePath | `…/bin/codex` | `…/bin/claude` |
| permissionMode | `danger-full-access` | `bypassPermissions` |
| authenticationProfile | `existing-codex-login` | `existing-claude-login` |
| fundingProfile | `provider-default` | `claude-subscription` |

Unchanged: the worker's GitHub identity (`morty-worker`), its Git identity, its own `gh` configuration
and shim directories, `knownChanges`, and the entire VERIFIER configuration (`jc-worker`, `claude`,
separate invocation, separate worktree). Verifier independence rests on separate invocation, identity,
workspace and fresh context — not on billing separation.

**Scope of the authorization:** this PY-09 recovery only. It does not redefine the default producer
provider, and does not change PY-09's scope, contract, acceptance criteria, baseline or cycle number.
The previous provider block is recorded above and the pre-change profile is retained at
`~/.config/alienintent/self-hosting.json.bak-20260921T0220Z`.

**Recovery sequence and outcome:**

1. Partial work confirmed present, unowned, with its unique content intact.
2. Profile edited; **the first edit was rejected** — the loader validates worker objects against a
   fixed key set, so an added `_providerChangeProvenance` key failed closed with
   `invalid config.workers.PRODUCER`. Correct behaviour on the loader's part; provenance belongs in
   this record, not in the profile. Key removed, profile accepted.
3. Dispatcher restarted with no active invocation; App preflight passed; current PID clean.
4. Continuation record posted to the Issue **before** any producer could start, naming the preserved
   worktree, the cycle-3 findings, §4b, and the provider-capacity notice.
5. Replacement producer **`9979bdcc-adaf-4b5a-9847-265e6556645e`**, pid 823528, running `claude -p`,
   started `02:21:36Z` — after the continuation record.
6. **Duplicate check: exactly one lane claim for `#57`, exactly one live worker process** on the host.
   The resume came from the dispatcher's own restart reconciliation, not from liveness re-emission.
7. Attention items acknowledged only then.

## Defect found in the coordinator's own tooling

The restart produced a **second** attention item for the same underlying event. During reconciliation
the dispatcher re-recorded the existing diagnostic with a fresh `at` timestamp; attention identity
anchors on that timestamp, so one invocation's single failure minted two items. Harmless here — both
were acknowledged, one as superseded — but it is a real dedupe weakness: identity should anchor on the
invocation plus its start, which do not change, rather than on a field the dispatcher may rewrite.

## Learning questions raised, not answered here

Recorded for the learning loop; **no Product Requirement is created** and any generalized capability
goes through normal proposal authority.

1. Should provider-capacity exhaustion carry a **typed durable outcome** instead of degrading into a
   generic `DURABLE_RESULT_MISSING`? The generic class forced a log read to distinguish "worker died"
   from "worker was cut off".
2. Should AlienIntent support **policy-authorized provider failover** for an interrupted producer,
   rather than requiring an operator decision and a service restart?
3. How should **partial-work continuity** interact with provider rerouting? The replacement producer
   gets a fresh worktree and must be told in prose where the previous work lives.
4. Can quota or capacity be **detected before invocation** where provider APIs expose it, so a BIU is
   not released into a provider that cannot finish it?
5. How should provider-capacity interruptions affect **factory-yield metrics and repair-cycle
   accounting**? This one must not count as a repair cycle, and the current dataset has no field for it.
6. Does **SWF-09** need refinement so measured-only CLI budgets are distinguishable from enforceable
   ones at release time, rather than discovered at exhaustion?

A seventh, from the recovery itself: producer and verifier now share one Claude subscription, so
exhausting it would stall **both** roles rather than one. Acceptable for a bounded recovery; it is a
single point of failure if the arrangement outlives it.
