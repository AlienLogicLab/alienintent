# POSTW1-GAPTRAP-003 — Gap Trap Graduation Audit

Fresh Codex GPT-6 Astra session, dispatched by the AlienIntent local Program Director under
Founder authorization. Working directory is the repository root. Sandbox is `workspace-write`,
escalated from the `read-only` default solely to write the two deliverables in §6.

## 1. The principle this phase serves

> VERIFY proves what AlienIntent already knows how to check.
> REVIEW discovers what AlienIntent does not yet know how to check.
>
> REVIEW explores; VERIFY accumulates.

Your objective: identify recurring known failure classes that should **stop consuming REVIEW and
model cognition**, because a machine can settle them.

The failure mode to guard against is not under-promotion. It is **over-promotion**: a gate that
was never shown to fail is a prose reminder wearing a gate's clothing, and it consumes the review
budget it was supposed to free. Promoting twelve weak checks is worse than promoting four real
ones. Not every candidate should be promoted, and saying so is a result, not a shortfall.

## 2. Deterministic prework — already done, do not redo

The Director settled these before dispatching you, so you spend no tokens rediscovering them:

- **`docs/operations/post-wave1-program/prework/POSTW1-GAPTRAP-003-candidates.json`** — the 18
  in-scope candidates, derived from the ledger as `disposition ∈ {GAP_TRAP_PROMOTION,
  STRENGTHEN_EXISTING_OWNER}` and `mechanizable ∈ {yes, partial}`. Each already carries its
  current owner, owner_fit, enforcement_level, proven_red status, originating BIUs, evidence refs,
  and a one-line sketch of what a deterministic check would assert.
- **`docs/operations/post-wave1-program/prework/POSTW1-GAPTRAP-003-enforcement-layers.json`** —
  the ten enforcement layers that already exist in this repository, with paths and runners.

Read both first. Your job is judgment about promotion, not inventory.

Full context remains `docs/evidence/wave1-learning-ledger.json` (30 records, authoritative).

## 3. Per-candidate field contract

For each candidate you promote:

```
learning_id                      must be one of the 18 (Phase 3 promotes lessons, never invents)
failure_class
cheapest_enforcement_layer       an existing layer name, or "NEW:<name>" + new_layer_justification
deterministic_rule               what the check asserts, precisely enough to implement
violation_fixture                the input/state that must make it fail
proven_red_method                how you would demonstrate it failing before trusting it
advisory_or_blocking             ADVISORY | BLOCKING
canonical_owner                  SF-REQ-### / SWF-## / explicit ownership gap
expected_cognitive_work_removed  the reviewer or model work that disappears once implemented
effectiveness_metric             what number tells you it worked
```

**Cheapest layer wins.** An architecture-fitness assertion already running in CI beats a new
bespoke gate. `NEW:` is permitted but must be argued — a new layer is a standing cost.

**BLOCKING requires a proven-red method and a violation fixture.** If you cannot say how the check
would be demonstrated failing, it is ADVISORY. This is enforced mechanically (§5), and demoting to
ADVISORY is a perfectly good answer.

**`expected_cognitive_work_removed` must name real work.** If no reviewer or model effort
disappears, the promotion adds a gate and buys nothing — do not promote it.

## 4. Candidates you decline

Put them in a separate `not_promoted` array with `learning_id`, `reason`, and
`revisit_condition`. Declining is a legitimate outcome for: classes that are genuinely
judgment-bound, classes where the deterministic rule would have an unacceptable false-positive
rate, and classes whose evidence does not actually establish recurrence.

## 5. High-priority classes — confirm, do not assume

The program plan names these as *suspected*. Evidence must confirm each before you promote it:

- non-discriminating tests; correct-but-unexecuted paths; proof harness missing before repair;
- baseline/result identity; BIU identifier parser assumptions;
- config validation before service restart; effect verification after command intent;
- attention/effect stable identity.

If the evidence does not support one, say so. A suspected class that the evidence does not
establish is a finding.

## 6. Deliverables

Follow existing conventions — authoritative JSON plus a prose Markdown companion that adds no
facts the JSON lacks:

- `docs/evidence/wave1-gap-trap-promotion-backlog.json`
- `docs/evidence/wave1-gap-trap-promotion-backlog.md`

Include a provenance block: generating actor `codex/gpt-6-astra`, task `POSTW1-GAPTRAP-003`,
repository HEAD read, and input paths opened. Keep `summary.promotions` equal to the number of
entries in `candidates`.

## 7. Acceptance — the checker exists already

```
python3 tools/evidence/check_gap_trap_backlog.py docs/evidence/wave1-gap-trap-promotion-backlog.json
```

It enforces: all ten required fields; every `learning_id` traceable to the 18; the enforcement
layer known or declared `NEW:` with justification; BLOCKING backed by proven-red method and
violation fixture; every promotion removing real cognitive work; valid enum values; and summary
consistency. It treats `"none — <why>"` as absence, not as content.

Do not edit the checker or its tests. **If you believe a check is wrong, say so in
`DISPUTED_CHECKS` and leave it failing.** In the previous phase you disputed a check rather than
editing it, the dispute was upheld, and a real defect in the checker was found as a result. That
outcome is wanted, not tolerated.

Also confirm `python3 tools/evidence/check_wave1.py --negative-controls` still passes.

## 8. Out of scope

- **Do not implement any check.** This phase produces a backlog, not code.
- Do not begin Phase 4 (Agent-Ready Outcome Completeness Audit).
- Do not create, amend or weaken any Product Requirement.
- Do not modify the Learning Ledger, Wave 1 evidence, lifecycle state, Project state, worker
  contracts or Node/B-DISP semantics.
- Do not `git commit`, `git push`, or use the network.

## 9. Terminal report — this block and nothing else

```
CANDIDATES_CONSIDERED=18
PROMOTED=<n>
NOT_PROMOTED=<n>
BLOCKING=<n> ADVISORY=<n>
LAYERS_USED=<comma-separated existing layer names>
NEW_LAYERS_PROPOSED=<n>
SUSPECTED_CLASSES_CONFIRMED=<n of 8>
SUSPECTED_CLASSES_UNSUPPORTED=<list, or NONE>
BACKLOG_CHECK=PASS|FAIL
WAVE1_CHECK=PASS|FAIL
DISPUTED_CHECKS=<or NONE>
NOTES=<one line, or NONE>
```
