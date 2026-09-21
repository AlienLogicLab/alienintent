# Wave 1 terminal evidence reconciliation

Authority: the Founder-directed Phase 0 + Phase 1 closure/evidence task. Source boundary:
`10cc81620511af56befbb6140504d1991bb02846`, the PY-10 landing. This record changes no
Product Requirement, BIU acceptance, lifecycle, Issue state, worker configuration or
live operation. It does not perform Learning Consolidation or Wave 2 design.

The [closure manifest](wave1-closure-manifest.md) is the current terminal projection.
The [source capture](wave1-source-observations.json) retains paginated GitHub Issue
bodies/comments/dependency reads, complete Project reads, sandbox ref comparisons,
and an allowlisted export of runtime evidence. Local absolute paths in published
comments are normalized; original body hashes are retained. Credentials, profiles,
worker logs and operational state remain outside the repository. Selected provider
terminal records are evidence excerpts, not copies of the logs or private reasoning.

## Work packet and authority read

- Intent: freeze the terminal population/boundary, finish missing terminal evidence,
  reconcile derived datasets, demonstrate a consistency checker can fail, and LAND.
- Starting checkout: clean `main`, HEAD and refreshed `origin/main` both `10cc816…`.
  Git author `netmarine <sanuk.du@gmail.com>`; GitHub reader/publisher `sanookdu`;
  configured remote `AlienLogicLab/alienintent`.
- Permitted changes: evidence documents/data and bounded offline evidence tooling.
  Existing runtime-managed resources are neither this task's temporary state nor
  authorized cleanup targets. No temporary task branch or worktree was needed.
- Authority read: AGENTS, docs README, operations, forward-momentum, governing
  directive and work-packet template; SF-REQ-016/017/020/021/022/024/029/030/032 in
  the canonical software-factory plan; SF-REQ-049/050/052 in their canonical
  decisions; SWF-21/23/24/27/29/30/31/32/33/34; approved Wave 1 DAG and contracts.
- Validation: exact Issue/verdict identities; Git ancestry; independent source
  review; all v1 trajectories/quality schemas; consistency checks with negative
  controls; retained live-proof checker and fresh read-only sandbox read-back.
- Disposition authorized by this task: validate → commit → push `main` → read back.
  The evidence-publication commit is distinct from the frozen terminal SHA.

Independent read-only review found three derivation/checking defects, all repaired:
the PY-04 presumptive-candidate promotion, incomplete early timing caveat, and
ancestry negative controls that initially exercised only cross-file mismatches.
The reviewer confirmed the repairs and reran the checker: 1,075 checks, zero
failures, 13/13 negative controls killed. The separate Claude review requested by
the Founder remains subsequent independent review, not claimed here.

Fresh retained-proof verification also exited 0 with 17/17 checks:
`rtk proxy python3 tools/live/py10_verify_evidence.py --evidence docs/evidence/py10 --live --json`.
Here `--live` compares redaction against local installation values; it does not
re-execute the proof or remotely verify branches. Separate read-only GitHub
captures provide the Project/ref read-back. No paid provider call or live run was
started by this task.

## Definitions and inventory

### Late-arriving participant evidence and provider authority qualification

Before publication, HEAD and refreshed origin/main both advanced to
`3bb5a9524425469f76f9b7bc29af3386ca179b6e`, adding only the noncanonical
[coordinator self-assessment](2026-09-21-coordinator-self-assessment-wave1.md) and
[bootstrap expiry inventory](2026-09-21-bootstrap-expiry-inventory.md). Both are
preserved unchanged. The terminal implementation boundary remains `10cc816…`.
Their MEMORY-ONLY statements and causal hypotheses are not adopted as facts.

The inventory reports continued Claude PRODUCER use beyond the PY-09-only
recovery authorization. The scope restriction is independently recorded in
[Issue #57 comment 5754575853](https://github.com/AlienLogicLab/alienintent/issues/57#issuecomment-5754575853).
Local producer terminal records independently corroborate the later provider:

| BIU | Producer invocation | Terminal modelUsage key | Complete log SHA-256 |
|---|---|---|---|
| PY-09B | `952f9794-b9af-4064-8b8e-79c901d16384` | `claude-opus-5[1m]` | `f2d9cd97da5cafe47daade41b978ef5488f40bc891fb7cbfeb0f279e1d78279e` |
| PY-10 | `1c9deab2-917d-48d8-87bd-0f56fb7ca2a9` | `claude-opus-5[1m]` | `f4699b154b742d0d01bd5ae04247b3d0748d02b2b638d241ef99b171239b2277` |

Source location: the installation's `logs/AlienLogicLab%2Falienintent%23<issue>%3APRODUCER%3A<invocation>.log`;
allowlisted fields read from JSON `type=result` records, both `subtype=success`,
`is_error=false`. No private reasoning was copied. These are provider observations,
not acceptance verdicts. List-price partial usage is not subscription billing or
end-to-end cost.

**Unresolved authority qualification:** no durable extension or ratification of
the PY-09-only provider authorization was found in the captured Issue records.
The later provider use is confirmed; any separate authorization is UNKNOWN.
This evidence task cannot ratify it or revert operational configuration. Preserve
the independently recorded first-pass ACCEPT/DONE facts with this qualification;
do not retroactively rewrite lifecycle state. Bootstrap retirement proposals remain
participant proposals, not decisions made in this session.

Observation is not verdict. A provider exit, test count, candidate SHA or verifier
finding is an observation. The authenticated independent verifier's ACCEPT marker
is a verdict. Dispatcher closure completion plus Project DONE is a lifecycle fact;
Issue CLOSED is the later bookkeeping projection. Historical checks are not claimed
as fresh executions of eleven candidate revisions.

Both current v1 JSON schemas permit additional properties; neither schema changed.
Every BIU now has a trajectory JSONL, trajectory summary, Quality Evidence JSON and
Quality Evidence Markdown. Before this task: PY-02…PY-08 had all four; PY-09 had
all four **interim**; PY-01 lacked this four-artifact set; PY-09B lacked it; PY-10
had sandbox-run trajectory/quality artifacts but lacked its own terminal lifecycle
set. PY-10 sandbox-run artifacts remain a separate scope and are not superseded.

Historical JSONL entries remain intact except explicit terminal-aggregation
supersession metadata and omission of invalid optional null `ended_at` and
`parent_candidate` values (PY-06/PY-07/PY-09). Each omitted null is documented in
its record; no timestamp or candidate was invented. Historical summaries are
available at the frozen Git revision.
Quality JSON retains its old measurement under `superseded_measurement`; it is
excluded from terminal aggregates. Old mixed repair rows remain under
`superseded_records`, also excluded. Old comparison/extraction documents explicitly
point to the terminal replacement.

This reconciliation supersedes terminal claims in the historical
[PY-02/PY-03 comparison](quality/PY-02-vs-PY-03.md),
[PY-02/PY-03/PY-04 comparison](quality/PY-02-vs-PY-03-vs-PY-04.md),
[PY-05…PY-09 comparison](quality/PY-05-through-PY-09.md),
[extraction verification](execution-trajectories/PY-05-to-PY-09-extraction-verification.md),
[PY-04 inventory](execution-trajectories/PY-04-evidence-inventory.md), and
[interim incident report](wave1-factory-incidents-and-learning-PY-05-to-PY-09.md).
Their historical observations and interpretations are retained, not promoted to
new terminal verdicts or new learning conclusions.

`repair_finding_groups` counts report-local directed/headed groups, with per-report
definitions. It is neither an all-open-finding count nor necessarily a count of
decisive blockers. Carried findings may occur in multiple report rows, but no
unique-defect total is inferred. At ACCEPT, zero means no remaining blocking repair;
non-blocking observations may remain. `findings_total` and `unique_findings` stay
UNKNOWN when the source lacks a complete enumeration under those definitions.

## Terminal BIU population and DAG reconciliation

FACT: eleven executed BIUs, PY-01…PY-10 plus PY-09B. All eleven Project #1 items
are DONE and Issues CLOSED. Project identity `PVT_kwDOEcrpC84Bj5i_`; both Project
captures have `hasNextPage=false`. Accepted candidates are all reachable from their
named merges, the terminal SHA and refreshed `origin/main`. No member remains
release-eligible. At capture, active Wave 1 lanes are empty, every retained resource
has an exit timestamp, and none of its recorded worker PIDs exists.

The contract/release DAG is more precise than the older outline diagram: PY-05
depends on PY-03 **and PY-04**; PY-06 depends on PY-04 **and PY-05**; PY-07 depends
on PY-04/PY-05, though release followed PY-06. PY-09B follows PY-05/PY-06/PY-08/PY-09;
PY-10 follows those plus PY-09B. The manifest preserves declared and native edges
separately, including transitive predecessors where the contract names them.

**Projection gap, not silently repaired:** PY-09B's native blocked-by API returns
an empty list, while its contract and [release record](https://github.com/AlienLogicLab/alienintent/issues/68#issuecomment-5758348400)
explicitly name four predecessors. All were DONE before release. PY-10's Issue body
also retains older predecessor/baseline wording; its final contract, native links
and [release record](https://github.com/AlienLogicLab/alienintent/issues/58#issuecomment-5759231468)
include PY-09B and baseline `693fef995f03ab3eca43cb74ad5692cdcd69ffcf`.
No Issue or dependency was edited in this task.

PY-01 names architecture authority rather than SF-REQ identifiers. Its manifest
requirement mapping is UNKNOWN, with that explanation; no retrospective requirement
mapping is invented. Other rows retain the contract's exact contribution extent,
not a claim that each entire requirement is complete.

## PY-09: terminal history replaces the interim boundary

The old capture at `2026-09-21T02:45:00Z` was legitimately IN_FLIGHT. It is now
superseded for terminal measurement, not recharacterized as a false observation.

| Execution cycle | Candidate | Work verdict | Python tests |
|---|---|---|---:|
| 1 | `57826f021a4a1839b5639bd433e47f78d296610f` | REJECT | 173 |
| 2 | `c1674ffc…` (full identity in source report) | REJECT | 183 |
| 3 | `c9563214…` (full identity in source report) | REJECT | 189 |
| 4 | `24cdd64f0dc565d537052cedca8c3341503359b1` | ACCEPT | 209 |

The terminal result is **three rejections, four execution cycles, four verifier
verdicts**, with five verifier invocations because one produced no verdict.
Merge `85b606037e144e977c1bc1f7b0aa795d97e19d83`; worker DONE signal
`03:38:15Z`; dispatcher DONE `03:38:22.332Z`; Issue closure `03:40:19Z`, all
2026-09-21. Fitness PASS and Node exit 0 are independently recorded in the
[ACCEPT report](https://github.com/AlienLogicLab/alienintent/issues/57#issuecomment-5755009604).
The final verifier retains a non-blocking missing proof for `doctor.py:154`;
ACCEPT is not zero residual observations.

**Capacity interruption:** Codex PRODUCER `e84d12a0-696b-4d82-842a-7c425747b364`,
allocated `02:06:56.346Z`, exited `02:12:46.870Z`. Its retained log ends with
`turn.failed` / usage limit. No durable result marker. Resource
`63097907-ffb9-411c-a59c-d353c09e8a7e` retained partial work in doctor source and
two tests, reported as +65/-60. This is a provider incident, not a repair rejection.

**Real SWF-29 suppression:** the liveness record at `02:20:07.366243Z` observes
IMPLEMENT, no invocation/live PID, state age **441s** against **300s** grace,
and `ATTENTION_WAIT (DURABLE_RESULT_MISSING)` linked to `att-ede4efa1e3ad`.
It records `LIVENESS_SUPPRESSED`, not a re-emitted trigger. The unresolved attention
item is why no repeated quota-burning launch occurred during this interval.

**Failover:** Claude PRODUCER `9979bdcc-adaf-4b5a-9847-265e6556645e`, allocated
`02:21:37.058Z`, exited `02:57:52.713Z`, published the cycle-4 candidate. Same
cycle, new attempt, no intervening verifier rejection. Provider provenance and
partial-work preservation are in the [incident record](2026-09-21-py09-provider-capacity-interruption.md).

**Ordering correction:** the incident narrative says continuation was posted before
launch. GitHub timestamps the [continuation comment](https://github.com/AlienLogicLab/alienintent/issues/57#issuecomment-5754575853)
at `02:21:38Z`, **0.942s after** resource allocation. It does not prove pre-launch
comment publication. Founder authorization is reported; its exact instant is
UNKNOWN. This correction does not infer missing authorization from clock ordering.

**No-verdict verifier:** `f5ca7bab-0687-4f03-9cdf-a44b505b36e1`, allocated
`02:57:37.677Z`, exited `03:03:29.309Z`. Provider result: `subtype=success`,
`is_error=false`, 39 turns, “I'll pick this up when the sweep lands.” No B-DISP
verdict exists. Fresh verifier `a9953577-9b4b-4cd5-8cb6-13cba39f2fa2` allocated
`03:11:48.355Z` reviewed the same candidate and accepted at `03:30:36Z`.
Both are cycle 4. Provider invocation success != work verdict.

The incident also records attention dedupe on rewritable timestamps, a regression
in the liveness attention anchor, and a false recovery failure from the 25-second
sample. These are control-plane incidents, not additional BIU repair cycles.

## PY-09B: inserted prerequisite, first-pass accepted

Origin: PY-10 SPLIT_RECOMMENDED at `85b6060`, then SWF-33 creates PY-09B and
SWF-34 resolves the impossible Project-token isolation requirement. Separate
assessment versions remain available in Git and in trajectory references:

| Retaining revision | Disposition | Reason / resolution |
|---|---|---|
| `d35928d` | NEEDS_CLARIFICATION | token-level Project isolation impossible; SWF-34 |
| `d01bc38` | NEEDS_CLARIFICATION | live custody requires missing `contents:write` |
| `d3f54eb` | READY | corrected permissions and real custody proof; locality MEDIUM |

The environmental proof has **three states**, retained separately:

1. [Wrong expected contract](py10-preflight-2026-09-21-pre-contents-grant.json): 17/17 pass.
2. [Correct expected contract, unchanged installation](py10-preflight-2026-09-21-negative-control.json):
   real failure on **2 of 17**, the App and installation permission checks.
3. [Corrected installation](py10-preflight-2026-09-21-post-contents-grant.json): 17/17 pass.

The two failures are not “2/17 passing.” Discriminating check correctness does not
imply specification correctness. Live clone/commit/push/fresh-clone identity and
tree read-back are documented in the sandbox operations record; the later Python
implementation independently re-proved custody through its actual adapters.

Release `09:32:44Z`, baseline `d3f54ebe120ab435b483b1cf60120b16ae3d706d`.
Producer `952f9794-b9af-4064-8b8e-79c901d16384` publishes
`3bc361e6ae313285b8364a0f8ececa593c997d86` at `10:17:00Z`.
Verifier `ca6f87d5-9c03-4daf-ad1b-0740936ae5da` ACCEPT at `10:27:29Z`,
**zero REJECTs**. [Independent report](https://github.com/AlienLogicLab/alienintent/issues/68#issuecomment-5759003341):
308 Python tests, fitness PASS, Node 310+18+2, live transport 35/35, proven-red
13/13. Merge `93dd8b1078a26b157df316bd21e8510ea4d86156`; dispatcher DONE
`10:34:30.544Z`; Issue closed `10:36:42Z` (2026-09-21).

Live scope includes token acquisition/refresh, exact permission set, private repo
read, custody, Project resolution, fenced projection/read-back, authenticated
ingress/replay, profile composition, doctor and redaction. Repository isolation is
permission-enforced; Project targeting is configuration-enforced. No claim that
the token cannot reach another organization Project is made. Non-blocking verifier
observations (constant liveness GET, transient token argv exposure, partly
corroborating live projection check) remain disclosed; no acceptance is reopened.

## PY-10: capstone lifecycle and independently corroborated run

Readiness assessments remain separate: **BLOCKED** (`c32830b`, unprovisioned
sandbox/predecessors), **SPLIT_RECOMMENDED** (`1f16b81`, unowned transport/coupled
proof), **READY** (`693fef9`, accepted PY-09B substrate, locality MEDIUM).
The final assessment was against `93dd8b1`; its retention commit/release baseline
is `693fef995f03ab3eca43cb74ad5692cdcd69ffcf`. They are distinct identities.

SWF-21 release record `10:44:48Z` names that baseline and passed admission.
Producer `1c9deab2-917d-48d8-87bd-0f56fb7ca2a9` published
`04bc54bada9c1e5a0ec3758f05dc9a3c82ab4190` at `12:01:44Z`.
Verifier `a4491349-2844-4f91-b554-137d14a9a8fe` ACCEPT at `12:11:25Z`,
**zero REJECTs**. Terminal merge `10cc816…`; DONE `12:18:17.618Z`;
Issue closure `12:21:51Z` (2026-09-21).

Run window **11:47:34Z–11:52:04Z**, repository
`AlienLogicLab/alienintent-sandbox`, Project #2 `PVT_kwDOEcrpC84BkIEX`.
The run artifacts and independent verifier establish:

- Six seeded BIUs, all DONE; six candidate branches, each independently read back.
  Fresh GitHub API comparisons again show one commit ahead of sandbox main and
  only that BIU's note changed. Both decision-request items still exist.
- SB-02/SB-03 (P1) dispatched in READY order (`11:47:01Z`, `11:47:09Z`);
  SB-04 waited until its lower-priority blocker SB-05 completed.
- WIP ceiling 1 over **34 samples**, plus a refused independent slot acquisition;
  four BIUs drained in one command. Sampling is not continuous contention telemetry.
- SIGKILL while holding `launch:SB-01:0`; unknown effect parked instead of blind
  retry. Independent work continued. Two attributable decisions resumed SB-01/SB-06.
  No duplicate **published external effect** is evidenced; this is not proof that
  the killed invocation did no computation before its replacement.
- AC14: seed writes READY; 13 successful operator commands plus the killed `run`
  contain no manual IMPLEMENT action. This is scoped transcript evidence, not an
  exhaustive GitHub administrative audit history.
- AC16: producer-retained production before/after identity/state digests match,
  67 items, unchanged Project `updatedAt=10:45:23Z`; Node ingress observations and
  tunnel-config mtime unchanged. The independent verifier explicitly lacked
  production `read:project`, so did **not** re-derive the historic digest. The
  separately retained production observer log has **zero events** in the run
  window. That corroborates absence of observed lifecycle activity, not absence
  of all possible writes. The production PY-10 producer itself was active during
  the run; “no active invocation” is true at this closure capture, not throughout
  the proof window.
- AC17: independent verifier generic-secret scan plus actual-value scan; the
  retained checker rerun here passes **17/17**, including actual-value redaction.
  Its `--live` flag searches private values locally; it does not itself re-read
  GitHub, despite the tool's introductory wording. Fresh remote proof above is a
  separate read-only API observation. No proof run or sandbox mutation was repeated.
- Historical final checks: **344 Python tests**, architecture fitness PASS,
  **310 runtime + 18 RAI + 2 policy Node tests**, preflight PASS; **22/22** guards
  proven red, independently reproduced by the verifier. Landing tree is identical
  to the accepted candidate.

**Resolved branch-count contradiction:** coordinator closure comment
[5760402013](https://github.com/AlienLogicLab/alienintent/issues/58#issuecomment-5760402013)
says seven candidates “plus a repair cycle.” Retained proof, independent verifier
and current remote agree on **six candidates plus main = seven total branches**.
There is no seventh candidate or verifier rejection supporting that sentence.
The comment remains immutable provenance; this manifest supersedes its derived count.

Accepted residual limitations remain facts: non-terminal worker outcomes may
redispatch indefinitely (run bounded by harness); worker read-back is in memory;
Project lifecycle projection occurs at completion; sandbox dependencies use
contract/draft descriptors rather than native blocked-by. Scope-table omission of
test support and omission of killed `run` from the successful-command transcript
remain disclosed. No change is made to resolve product limitations here.

## Repair data and timestamp corrections

| Source / defect | Terminal disposition |
|---|---|
| PY-04 quality: 9 formal verifier cycles | **10 verdicts: 9 REJECT + 1 ACCEPT**. Producer self-review/FOUNDER_EXCEPTION is not an independent verifier rejection. |
| PY-04 summary: DONE 12:31:12Z | That is Issue closure; dispatcher DONE is **12:26:25.430Z**. |
| PY-04 verdict 9 candidate identity | **UNKNOWN**. Report 5749643685 explicitly rejects timestamp correlation as identification. `f95199e6698dcb6b3858ae5e169a30a7fb130fd2` is retained only as `presumptive_reviewed_tree`, not established custody. |
| PY-08 legacy row “cycle 7, 3 open” | Sixth verdict; old index included authority interruption. **5 open IDs Y2/Y4/Y7/Y8/Z1; 3 directed repairs Y2/Y4/Z1; 2 decisive unmet-AC groups Y2/Y4**. |
| PY-08 ACCEPT zero | Zero blocking repairs only. Y7/Y8 and new non-decisive observations remain. |
| PY-06 late UNKNOWN counts / closed findings double-counted | Explicit report headings support **F9/G6/H5/J2** groups across four rejects; final ACCEPT closes blockers. Legacy row 5 is J1/J2 (2), row 6 ACCEPT is zero blockers, not all observations. |
| PY-07 3/5 versus 2/3 in cycles 2/3 | Different populations: all numbered headings include residual/minor observations; directed acceptance groups are 2/3. Per-source scope is now explicit; no unique defect sum. |
| PY-09 interim totals and null end time | Terminal events appended; old boundary preserved and superseded. Provider failover and verifier retry remain cycle 4. |
| PY-09 “continuation comment before launch” | Not supported by timestamp ordering; allocation precedes posted comment by 0.942s. Exact Founder authorization instant UNKNOWN. |
| PY-10 seven candidate branches | Six candidates plus main; no extra repair-cycle evidence. |
| Legacy 310 versus 330 Node counts | Runtime group 310 versus aggregate 310+18+2=330; do not compare different scopes as a regression. PY-01's recorded runtime count was 309. |

Per-report source URLs, exact invocation identities and counts are in
[repair JSON](wave1-repair-cycles.json). Current results: **33 combined verifier
rejections**, 44 verdicts/cycles, 11 accepted BIUs, **2 first-pass** (PY-09B/PY-10).
PY-01…PY-08 were 0/8; including PY-09, 0/9. No causal interpretation follows.

## Incidents, exceptions and remaining UNKNOWN telemetry

Nine FOUNDER_EXCEPTION protocol markers: PY-01 1, PY-02 1, PY-03 1, PY-04 2,
PY-06 1, PY-07 2, PY-08 1; zero in PY-05/PY-09/PY-09B/PY-10. This does not mean
nine genuine missing-authority decisions. Published sources distinguish landing
authority (PY-01/02), custody transfer (PY-04 SWF-22), unfinished work/escalation,
invalid or missing release admission records (PY-06/07), and provider interruption.
PY-09's provider-change authorization is an operator decision without a worker
FOUNDER_EXCEPTION marker. SWF-34 is a pre-release Founder clarification, not a repair.

Known execution capacity interruptions: PY-03 closure and PY-09 IMPLEMENT. The
Agent-Ready provider-failover episode is separately preserved in its incident
document and assessment histories, not included in verifier-rejection counts.

Control-plane incidents are sourced in the retained earlier trajectories and the
Wave 1 incident record: missing VERIFY delivery for PY-06; observer-to-attention
activation gap; retrying judgment-blocked PY-07; stale Issue closure projections;
PY-08 launch gap; PY-09 no-verdict, attention dedupe/anchor and recovery-sampling
defects. Unique global incident count is UNKNOWN: diagnostic repeats are not new
incidents, and the historic taxonomy does not supply a disjoint enumeration.

UNKNOWN remains explicit for end-to-end comparable tokens/cost, full provider/model
provenance, unique findings/regressions across repeated reports, escaped defects,
mechanical VERIFY versus qualitative REVIEW attribution, exact early release
transition times, the precise pre-launch Founder authorization instant in PY-09,
and exhaustive independent reproduction of the historical production Project digest.
Partial known costs in old quality records remain available, not converted to totals.

The external dependency-projection gap and immutable narrative discrepancies are
dispositioned above; they are not unresolved contradictions within the terminal
derived dataset. Accepted product limitations remain open observations. A future
review can reproduce this dataset without trusting this session; it must not treat
the checker as a new acceptance verdict or as proof of unrecorded facts.
