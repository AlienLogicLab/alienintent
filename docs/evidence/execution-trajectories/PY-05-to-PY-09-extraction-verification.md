# PY-05 to PY-09 extraction verification

> **Terminal reconciliation notice — Superseded by:** [Wave 1 Closure Manifest](../wave1-closure-manifest.md) and [evidence reconciliation](../wave1-evidence-reconciliation.md) for terminal counts, timestamps and comparisons. This document is retained as historical observation/interpretation at its original capture boundary; it is not the current Wave 1 aggregate. No historical hypothesis becomes a terminal causal conclusion.


SF-REQ-030 requires that derived evidence reconcile against its sources, that contradictory derived evidence fail deterministic consistency verification rather than be silently normalized, and that the consistency verification **itself** carry discriminating negative-control evidence. This record is that verification.

Capture boundary **2026-09-21T02:45:00Z**.

PY-09 was live throughout, and the repository moved under the extraction: `main` advanced from `9797a3ac` to `bd2d1b79` and then `56fa7051` while these artifacts were being written, all by the live Wave 1 loop and a parallel coordinator session. An earlier draft of this record declared a 02:10Z boundary; PY-09's cycle-4 provider-capacity interruption occurred inside that window and is now captured. The boundary is stated as a single instant because a record of a live BIU must say what it did and did not see, not because the BIU stopped.

## The checker

`~/.local/share/alienintent-bootstrap/trajectory_consistency.py`, alongside the two generators that produce the artifacts it checks:

```
python3 ~/.local/share/alienintent-bootstrap/py05_py09_trajectory.py <repo-root>
python3 ~/.local/share/alienintent-bootstrap/py05_py09_quality.py    <repo-root>
python3 ~/.local/share/alienintent-bootstrap/trajectory_consistency.py <repo-root>
python3 ~/.local/share/alienintent-bootstrap/trajectory_consistency.py <repo-root> --negative-controls
```

These live outside the repository, matching the precedent set by the `wave1-repair-cycles.json` extractor. They are bootstrap tooling, not product code; the canonical capability belongs to SF-REQ-030.

## Result

```
Consistency verification over PY-05, PY-06, PY-07, PY-08, PY-09
  checks run: 2652
  PASS: derived Quality Evidence reconciles with its trajectories, timestamps are
  consistent, UNKNOWN is preserved, and Git identity checks out.
```

## What is checked

**Schema.** Every event carries the eight v1-required fields, `schema_version == "1.0"`, a non-empty `evidence_refs`, the right `biu_id`, and an `event_id` unique within its file.

**Timestamps.** `started_at <= ended_at`. Every source-observed timestamp is at or before the record's `recorded_at` — the exact defect `v1-observed-gaps-from-PY-04.md` recorded, where a batch placeholder predated the events it claimed to record. Release precedes every candidate publication; a candidate is published before it is verified; DONE follows ACCEPT.

**Reconciliation.** Each derived measure recomputed from the trajectory: verifier cycles, repair cycles, `RETURN_TO_IMPLEMENT` controls, producer attempts, closure invocations, liveness incidents, operator interventions, authority interruptions, proof and behavioural regressions, supersessions, attention items, convergence assessments, per-cycle blocking and decisive finding counts, per-cycle test counts, the findings-by-class sum against the total, verification elapsed seconds against the invocation records, release-to-DONE and ACCEPT-to-DONE intervals, and the `first_pass_accepted`, `landed` and `done` flags against the presence of the events that would justify them.

**UNKNOWN discipline.** For each BIU a list of metrics the durable sources cannot supply — provider/model identity, token usage, cost, PY-05 and PY-06 attention coverage, and every terminal PY-09 measure — must remain non-numeric. Any scoped `0` must carry a `scope` or `definition`. `unknown_metrics` and `evidence_refs` must be non-empty.

**Git identity.** Each accepted candidate exists, is reachable from `origin/main`, and is a parent of a two-parent merge whose `src`/`tests` diff against the accepted SHA is empty.

## Negative controls

SWF-24 applies to this checker: a check that cannot fail is not evidence. Ten mutations, each of which must turn the run red.

| Mutation | Result | First failure |
|---|---|---|
| derived count altered (`verifier_cycles` + 1) | **RED** | `verifier_cycles = 8 but trajectory yields 7` |
| UNKNOWN telemetry replaced by numeric `0` (`token_usage`) | **RED** | `token_usage is expressed as a number (0); missing telemetry must stay UNKNOWN, never 0` |
| UNKNOWN telemetry replaced by `{"value": 0}` (`cost`) | **RED** | same rule, object form |
| impossible timestamp (`recorded_at` before the event it records) | **RED** | `py08-024-done ended_at (2026-09-21T01:00:45Z) is later than recorded_at` |
| verdict reordered before its candidate publication | **RED** | `attempt 7 verified before its candidate was published` |
| `evidence_refs` emptied | **RED** | `py08-001-release has empty evidence_refs` |
| per-cycle finding count altered to the `wave1-repair-cycles.json` figure | **RED** | `[12,14,11,10,8,7,0] but trajectory yields [12,14,11,10,8,3,0]` |
| per-cycle test count altered | **RED** | `[…,154,999] but trajectory yields […,154,158]` |
| Founder decision downgraded to a coordinator classification | **RED** | `PY-09: human_decisions_required = 1 but trajectory yields 0` |
| an observed provider-capacity failure reported as `0` | **RED** | `PY-09: provider_capacity_failures = 0 but trajectory yields 1` |

All ten red. The checks can fail.

One check was rewritten because it could not. A first version of the human-decision reconciliation compared PY-05–PY-08's `human_decisions_required` against itself, which is exactly the defect this cohort's verifiers rejected eleven times. It was replaced with a reconciliation against an explicit `founder_decision` flag on `HUMAN_DECISION_RECORDED` events, which distinguishes a coordinator classification from a decision only a human could make — and the ninth negative control above proves the replacement can fail.

## Three defects the checker found in this extraction

All three were in the author's first draft and all three were repaired before this record was written. They are recorded because a consistency check that never caught anything would be indistinguishable from one that cannot.

1. `PY-08 blocking_findings_count 48 != sum(by_cycle) 58` — the total had been written from a distinct-defect intuition while the series counted per-cycle reports. Repaired by fixing the total to 58 and restating the definition: a finding carried into a later cycle is counted again in that cycle.
2. `PY-08 test_count_by_cycle […] but trajectory yields [None, …]` — the cycle-1 verification event omitted the verifier's reproduced count. The verifier did observe it (`pytest -q → 132 passed`, re-run on the candidate commit). Repaired in the trajectory.
3. A tautological check, found by inspection rather than by the run: see the note under the negative-control table.

## An inconsistency in an adjacent artifact — not repaired here

[`../wave1-repair-cycles.json`](../wave1-repair-cycles.json) and its markdown, committed at `9797a3a` by a parallel bootstrap extraction, disagree with the verifier reports in several places. The extractor's own documentation already states that findings counts are readable for only 40% of cycles and that it records `null` rather than `0` when it cannot read them, which is the right default. The disagreements are in the cycles it *did* read:

| Record | Dataset | Verifier report | Note |
|---|---|---|---|
| PY-08 cycle 7 (`8f85513b`) | `findings_total: 7` | **3** (`Y2`, `Y4`, `Z1`) | the coordinator's own series reads `14 → 11 → 10 → 8 → 3` |
| PY-06 cycle 5 (`a7549b38`) | `findings_total: 5` | **2** (`J1`, `J2`) | 5 is the count of `H1–H5`, the *prior* cycle's findings, discussed in that report's "disposition of prior findings" section |
| PY-06 cycle 6 (`e6607486`) | `findings_total: 2` | **0** — it is the ACCEPT | 2 is `J1`/`J2`, reported closed |

The cause is the same in each case: counting finding identifiers wherever they appear in a report, including in the sections where a verifier lists prior findings it is reporting as **closed**. A carried-finding identity (see [the schema extension note](../schema/v1-extensions-from-PY-05-to-PY-09.md), open item 2) would remove the ambiguity.

The dataset is not modified by this extraction — it is another session's artifact and its author has been informed. The per-cycle figures in `PY-05.jsonl` … `PY-09.jsonl` are independently transcribed from the verifier reports and are the ones the consistency check enforces.

## Active work was not disturbed

PY-09 was live throughout. This extraction was read-only against every live resource:

- no Project status changed; no Issue was opened, closed, commented on or edited;
- no worker was started, stopped or restarted; no invocation was interfered with;
- no BIU contract, release record or assessment was modified;
- no candidate branch was touched; no worktree was created or removed;
- no attention item was acknowledged or consumed;
- `~/.local/state/alienintent/` was read only; nothing under it was written, and the retained worktree holding PY-09's interrupted partial work was not read into, entered, cleaned or reset;
- the only `gh` calls were `GET` on issues and their comments.

Git writes are confined to the documentation artifacts listed in this record, under normal Repository Change Closure. No existing evidence artifact was overwritten; `PY-05-release-snapshot.md` gained a supersession note and is otherwise unchanged, and `wave1-repair-cycles.json` was not modified.

Events that occurred inside the extraction window and are recorded as observations, none of them affected by it: PY-09 verifier `923ee4d9` completed; producer `e84d12a0` started, exhausted its provider quota and died; the coordinator posted a convergence assessment, a capacity diagnosis and a recovery authorization; producer `9979bdcc` started on a different provider adapter and was still running at the boundary. A parallel coordinator session also landed three documentation commits on `main`.
