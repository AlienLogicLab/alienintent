# POSTW1-LEARN-002 — Wave 1 Learning Consolidation

You are a fresh Codex GPT-6 Astra session dispatched by the AlienIntent local Program Director.
You have no prior conversation with this project. That is deliberate: this task must derive its
lessons from durable evidence, not from lived conversational bias. The resident Claude coordinator
was a Wave 1 *participant* and is therefore the reviewer of this work, not its author.

Working directory is the repository root. Sandbox is `workspace-write`, escalated from the default
`read-only` solely so you can write the two deliverable files named in §6. Write nothing else.

## 1. Objective

Convert scattered Wave 1 incidents and decisions into **one deduplicated Learning Ledger**.

**Do not create new requirements.** Recommending a disposition is in scope; minting a Product
Requirement is not. Duplicate requirement proliferation is the specific failure this phase exists
to prevent.

## 2. Authority and evidence rules

These are not stylistic preferences. Wave 1 established each one the hard way.

1. **Durable evidence decides.** Where any narrative account conflicts with a durable artifact,
   the artifact wins, and you record the conflict rather than silently resolving it.
2. **UNKNOWN is never silently converted to zero** (SF-REQ-030). If a count, timestamp or
   attribution is not established by evidence, the value is the string `UNKNOWN`. A fabricated
   zero is worse than an honest gap.
3. **A check that cannot fail is not evidence** (SWF-24). Apply this to Wave 1's own proofs when
   assessing proof quality, and to any claim you make.
4. **Cite by repository path.** Every `evidence_refs` entry is a path that exists in this
   repository, optionally with a line anchor. Do not cite a document you did not open.
5. Distinguish **FACT** (established by an artifact you read), **INFERENCE** (reasoned from facts,
   with the reasoning stated) and **HYPOTHESIS** (plausible, unverified). Label any non-obvious
   claim in the prose ledger.

## 3. Inputs — enumerated, so you do not have to hunt

Deterministic inventory already performed by the Director; these paths exist:

- **Phase 0+1 accepted evidence boundary** (start here — it is the accepted closure state):
  `docs/evidence/wave1-closure-manifest.md` and `.json`,
  `docs/evidence/wave1-evidence-reconciliation.md`,
  `docs/evidence/wave1-repair-cycles.md` and `.json`,
  `docs/evidence/wave1-consistency-report.md` and `.json`,
  `docs/evidence/wave1-source-observations.json`,
  `docs/evidence/wave1-yield-snapshot.md`,
  `docs/evidence/quality/wave1-cross-biu-comparison.md`
- **Factory incidents and prior learning:**
  `docs/evidence/wave1-factory-incidents-and-learning-PY-05-to-PY-09.md`
- **Coordinator self-assessment (participant evidence, NOT independent review — treat as a
  claimed account to be corroborated against artifacts, not as established fact):**
  `docs/evidence/2026-09-21-coordinator-self-assessment-wave1.md` (defects D1–D9)
- **Bootstrap expiry inventory:** `docs/evidence/2026-09-21-bootstrap-expiry-inventory.md`
- **Decision records (23 files):** `docs/decisions/` — SWF-18 through SWF-34 are the in-scope
  series; the 2026-09-20 and 2026-09-21 dated files carry them, including their amendments.
  Amendments matter: several decisions were *amended* rather than superseded, and the amendment is
  frequently where the lesson lives.
- **Proposal history (8):** `docs/proposals/PROP-2026-0001` … `PROP-2026-0008`, plus `INDEX.md`
- **Agent-Ready history (13):** `docs/work-units/python/PY-0*.assessment.json`,
  `PY-09B.assessment.json`, `PY-09B.assessment.2026-09-21-needs-clarification.json`,
  `PY-10.assessment.json`, and `docs/work-units/pre-python-gate/assessments/`
- **Execution trajectories / quality evidence (26):** `docs/evidence/execution-trajectories/`
- **PY-10 proof and sandbox custody:** `docs/operations/py10-sandbox.md` and the PY-10 evidence
- **Evidence tooling (run it; do not re-implement it):** `tools/evidence/check_wave1.py`,
  `tools/evidence/reconcile_wave1.py`

## 4. Per-lesson field contract

Every material lesson gets exactly these fields:

```
learning_id            LRN-001, LRN-002, … (stable, zero-padded, assigned in this ledger)
failure_class          short stable slug; reuse an existing class name where one exists
originating_BIUs       list of BIU ids (PY-01 … PY-10, PY-09B, PG-*, WO-*)
recurrence_count       integer, or UNKNOWN
first_occurrence       ISO-8601 or UNKNOWN
last_occurrence        ISO-8601 or UNKNOWN
evidence_refs          list of repository paths
existing_owner         SF-REQ-###, SWF-##, a named mechanism, or "NONE — ownership gap"
enforcement_level      DETERMINISTIC_GATE | REVIEW_GATE | DOCUMENTED_ONLY | NONE
mechanizable           yes | no | partial, with one line on what a deterministic check would assert
proven_red             yes | no | UNKNOWN — was the check ever demonstrated to fail?
later_consumption      was the lesson actually consumed by later work? cite where, or "not consumed"
effectiveness_evidence what evidence shows the owning mechanism worked, or "none"
recommended_disposition exactly one bucket from §5
```

## 5. Disposition buckets — exactly one per lesson

```
ALREADY_GRADUATED          a canonical owner exists AND evidence shows it worked
STRENGTHEN_EXISTING_OWNER  an owner exists but is too weak, too late, or unproven
GAP_TRAP_PROMOTION         a recurring trap deserving promotion to a deterministic gate
NEW_CAPABILITY_GAP         no owner exists and no existing owner can reasonably absorb it
BOOTSTRAP_ONLY             an artifact of bootstrap conditions; expires with the bootstrap
```

`ALREADY_GRADUATED` requires *effectiveness evidence*, not merely an owner. An owner that was
never exercised is `STRENGTHEN_EXISTING_OWNER`.

## 6. Deliverable

Follow existing evidence conventions — this repository pairs a machine-readable JSON with a prose
Markdown companion (see `wave1-repair-cycles.json` / `.md`). **Extend the established conventions;
do not invent a parallel format.** Read
`docs/evidence/schema/execution-trajectory-v1.schema.json` and
`docs/evidence/schema/quality-evidence-v1.schema.json` first and mirror their conventions for
identifiers, timestamps, UNKNOWN handling and provenance. This is a new scoped analysis artifact,
not a trajectory — do not force it into either existing schema, but do not contradict them either.

Write exactly two files:

- `docs/evidence/wave1-learning-ledger.json`
- `docs/evidence/wave1-learning-ledger.md`

The JSON is authoritative; the Markdown is its readable companion and must not contain facts the
JSON lacks. Include in the JSON a top-level provenance block recording: generating actor
(`codex/gpt-6-astra`), task id `POSTW1-LEARN-002`, the repository HEAD you read, and the input
paths you actually opened.

## 7. Clusters to test — do NOT assume these are separate lessons

The Founder's explicit instruction is to *test* whether these collapse. Deduplication is the
product of this phase. For each cluster, state whether the members are one lesson or several, and
say why.

- **Proof quality:** tests that cannot fail; unexecuted code paths; proof harness built too late;
  regressions of previously proven behavior.
- **Identity:** candidate identity; baseline identity; effect identity; attention identity;
  terminal result identity; BIU identifier grammar; execution cycle vs invocation.
- **Recovery:** missing actor vs completed blocked effect; liveness suppression; provider capacity;
  partial-work continuity; provider failover; duplicate-safe recovery.
- **Specification correctness:** a valid check against the wrong specification; copied bootstrap
  permission assumptions; impossible acceptance criteria.
- **Decomposition:** SPLIT_RECOMMENDED; unowned capability; split lineage; dependency rewrite;
  requirement conservation.
- **Observability:** provider-adapter log differences; normalized progress signals; buffered vs
  streaming output.

## 8. Coordinator performance — assess structurally

Assess the **structural** risk arising from coordinator-authored contracts, infrastructure,
release artifacts and recovery logic. The coordinator authored work and also judged it; say what
that concentration actually cost, with evidence.

**Do not reduce any conclusion to "be more careful."** That is not a finding. A finding names a
mechanism, a gate, a separation of duties, or an explicit accepted risk.

## 9. Exit gate

Before you finish, verify and state that:

1. Every material lesson has evidence, exactly one owner **or** an explicit ownership gap, and
   exactly one disposition.
2. No two lessons are restatements of each other.
3. No new requirement was created.
4. Both files are internally consistent and every `evidence_refs` path exists.

## 10. Terminal report

Your final message must be this block and nothing else:

```
LESSONS=<integer>
DEDUPED_FROM=<integer raw candidates considered>
DISPOSITIONS=ALREADY_GRADUATED:<n> STRENGTHEN:<n> GAP_TRAP:<n> NEW_GAP:<n> BOOTSTRAP_ONLY:<n>
OWNERSHIP_GAPS=<integer>
CLUSTERS_COLLAPSED=<short list of clusters you merged>
UNKNOWN_FIELDS=<integer count of fields recorded UNKNOWN>
EXIT_GATE=PASS|FAIL
NOTES=<one line, or NONE>
```

## 11. Out of scope — do not do these

- Do not create, amend or weaken any Product Requirement.
- Do not modify any existing file. Write only the two deliverables.
- Do not change lifecycle state, Project state, worker contracts or Node/B-DISP semantics.
- Do not run `git commit`, `git push`, or any network operation.
- Do not begin Phase 3. The Gap Trap Graduation Audit is a separate phase with its own gate.
