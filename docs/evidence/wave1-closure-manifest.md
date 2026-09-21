# Wave 1 Closure Manifest

Authority: the Founder-directed Phase 0 + Phase 1 evidence reconciliation; governing lifecycle remains Project Status under SWF-31. This manifest freezes the observed terminal boundary; it issues no new work verdict.

**Wave 1 terminal SHA: `10cc81620511af56befbb6140504d1991bb02846`.** This is PY-10 landing, not the later evidence-publication commit. All eleven accepted candidates are retained ancestors. Final dispatcher DONE: `2026-09-21T12:18:17.618Z`; final Issue closure: `2026-09-21T12:21:51Z`. Capture: `2026-09-21T14:04:28.291848+00:00`.

| BIU / Issue | Final state | Rejections | Verdicts / cycles | First-pass | Tests |
|---|---|---:|---:|---|---:|
| [PY-01 #2](https://github.com/AlienLogicLab/alienintent/issues/2) | DONE / CLOSED | 2 | 3 / 3 | False | 6 |
| [PY-02 #50](https://github.com/AlienLogicLab/alienintent/issues/50) | DONE / CLOSED | 1 | 2 / 2 | False | 23 |
| [PY-03 #51](https://github.com/AlienLogicLab/alienintent/issues/51) | DONE / CLOSED | 1 | 2 / 2 | False | 40 |
| [PY-04 #52](https://github.com/AlienLogicLab/alienintent/issues/52) | DONE / CLOSED | 9 | 10 / 10 | False | 65 |
| [PY-05 #53](https://github.com/AlienLogicLab/alienintent/issues/53) | DONE / CLOSED | 2 | 3 / 3 | False | 87 |
| [PY-06 #54](https://github.com/AlienLogicLab/alienintent/issues/54) | DONE / CLOSED | 4 | 5 / 5 | False | 110 |
| [PY-07 #55](https://github.com/AlienLogicLab/alienintent/issues/55) | DONE / CLOSED | 5 | 6 / 6 | False | 129 |
| [PY-08 #56](https://github.com/AlienLogicLab/alienintent/issues/56) | DONE / CLOSED | 6 | 7 / 7 | False | 158 |
| [PY-09 #57](https://github.com/AlienLogicLab/alienintent/issues/57) | DONE / CLOSED | 3 | 4 / 4 | False | 209 |
| [PY-09B #68](https://github.com/AlienLogicLab/alienintent/issues/68) | DONE / CLOSED | 0 | 1 / 1 | True | 308 |
| [PY-10 #58](https://github.com/AlienLogicLab/alienintent/issues/58) | DONE / CLOSED | 0 | 1 / 1 | True | 344 |

## Boundary and totals

11 executed BIUs; **2 first-pass accepted (PY-09B and PY-10)**; **33 combined verifier rejections**; 44 formal verdicts / reconstructed execution cycles. PY-01 through PY-08: **0/8** first-pass; PY-01 through PY-09: **0/9**. No causal conclusion is made.

All eleven Project items are DONE and Issues CLOSED. No remaining member is release-eligible. Runtime active map is empty for this population; all recorded resource entries have exitedAt and none of their PIDs exists at capture. A retained worktree resource label RUNNING is not a running invocation. Runtime-managed branches/worktrees remain governed by SWF-30, not this evidence task.

Known capacity interruptions: 2 execution incidents (PY-03 closure, PY-09 producer); Agent-Ready provider failover is separately recorded. FOUNDER_EXCEPTION totals below count protocol markers, not a claim that each required new authority. Control-plane incidents and inserted/replanned work: see [reconciliation](wave1-evidence-reconciliation.md). PY-09B is the sole inserted Wave 1 BIU, authorized by SWF-33; PY-10 was replanned before release.

## Per-BIU authority, identity and timestamps

### PY-01 — Python S0: enforceable architecture skeleton coexisting with Node

- Issue: [2](https://github.com/AlienLogicLab/alienintent/issues/2); Project item `PVTI_lADOEcrpC84Bj5i_zg7tE2I`; final **DONE / CLOSED**.
- Requirements (contract extent): "UNKNOWN". PY-01 is governed by architecture authority; no SF-REQ mapping declared in its contract.
- Declared predecessors: none. Native blocked-by read-back: empty.
- Agent-Ready: **READY**, rework locality HIGH.
- Accepted candidate: `b07ea94768e794702aa2b6bbc038d764b08ee3ea`; merge: `ab08449a0fac8d25374a80f4361a4023509118b1`.
- Combined verifier rejections: 2; FOUNDER_EXCEPTION markers: 1.
- ACCEPT marker: `2026-09-19T10:35:00Z`; DONE marker: `2026-09-19T10:54:46Z`; dispatcher DONE: `2026-09-19T10:54:51.347Z`; Issue closure: `2026-09-19T10:59:10Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/2#issuecomment-5741087648), [closure](https://github.com/AlienLogicLab/alienintent/issues/2#issuecomment-5741232248), [trajectory](execution-trajectories/PY-01.jsonl), [Quality Evidence](quality/PY-01-quality-evidence.json).

### PY-02 — Execution domain kernel (pure)

- Issue: [50](https://github.com/AlienLogicLab/alienintent/issues/50); Project item `PVTI_lADOEcrpC84Bj5i_zg7x1_0`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-010", "extent": "Primary — the machine-readable contract model"}, {"id": "SF-REQ-002", "extent": "Selection policy as a pure function"}, {"id": "SF-REQ-003", "extent": "Limit model (global/profile/repository)"}, {"id": "SF-REQ-007", "extent": "The `CandidateRef` model and VERIFY-entry guard; retrieval mechanics are PY-04 (local artifact) and PY-06 (source control)"}, {"id": "SF-REQ-009", "extent": "Deterministic lifecycle/policy core and its fitness proof"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-01. Native blocked-by read-back: PY-01.
- Agent-Ready: **READY**, rework locality LOW.
- Accepted candidate: `8689771b9fccb9f86c7fdcc2e9d4f571408765f2`; merge: `ab4efe54df752a4d7a35f047054435a24a21ddaf`.
- Combined verifier rejections: 1; FOUNDER_EXCEPTION markers: 1.
- ACCEPT marker: `2026-09-20T02:37:28Z`; DONE marker: `2026-09-20T03:14:14Z`; dispatcher DONE: `2026-09-20T03:14:20.229Z`; Issue closure: `2026-09-20T03:31:11Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747096363), [closure](https://github.com/AlienLogicLab/alienintent/issues/50#issuecomment-5747257998), [trajectory](execution-trajectories/PY-02.jsonl), [Quality Evidence](quality/PY-02-quality-evidence.json).

### PY-03 — Durable operational store

- Issue: [51](https://github.com/AlienLogicLab/alienintent/issues/51); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2BA`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-008", "extent": "Primary — durable state, once-only effects, recovery"}, {"id": "SF-REQ-003", "extent": "Atomic reservations with fencing"}, {"id": "SF-REQ-004", "extent": "Durable reservation release that a refill can observe"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-02. Native blocked-by read-back: PY-02.
- Agent-Ready: **READY**, rework locality HIGH.
- Accepted candidate: `c3ba58d980aeceafa483d8cc9b8edc4fb4238a5e`; merge: `d8f80e1722848116f2139728fe5f67da3af8dd0b`.
- Combined verifier rejections: 1; FOUNDER_EXCEPTION markers: 1.
- ACCEPT marker: `2026-09-20T04:11:07Z`; DONE marker: `2026-09-20T06:23:12Z`; dispatcher DONE: `2026-09-20T06:23:18.806Z`; Issue closure: `2026-09-20T06:27:00Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5747544877), [closure](https://github.com/AlienLogicLab/alienintent/issues/51#issuecomment-5748104520), [trajectory](execution-trajectories/PY-03.jsonl), [Quality Evidence](quality/PY-03-quality-evidence.json).

### PY-04 — Offline continuous factory loop (walking skeleton)

- Issue: [52](https://github.com/AlienLogicLab/alienintent/issues/52); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2B4`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-001", "extent": "Primary — the control loop, offline; live proof is PY-10"}, {"id": "SF-REQ-004", "extent": "Primary"}, {"id": "SF-REQ-002", "extent": "Policy applied in the loop"}, {"id": "SF-REQ-003", "extent": "Capacity/WIP enforcement in the loop"}, {"id": "SF-REQ-005", "extent": "The port shape only; the GitHub adapter is PY-05"}, {"id": "SF-REQ-007", "extent": "Contributing — the local-artifact custody path proven under SWF-12; PY-06 remains primary for production/source-control custody"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-03. Native blocked-by read-back: PY-03.
- Agent-Ready: **READY**, rework locality LOW.
- Accepted candidate: `03896f6267e06cd9a52afe4ab63dee32d221c538`; merge: `0170af0b3d995935835c8b7790341f93b5b23eb4`.
- Combined verifier rejections: 9; FOUNDER_EXCEPTION markers: 2.
- ACCEPT marker: `2026-09-20T12:19:39Z`; DONE marker: `2026-09-20T12:26:19Z`; dispatcher DONE: `2026-09-20T12:26:25.430Z`; Issue closure: `2026-09-20T12:31:12Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749754285), [closure](https://github.com/AlienLogicLab/alienintent/issues/52#issuecomment-5749787226), [trajectory](execution-trajectories/PY-04.jsonl), [Quality Evidence](quality/PY-04-quality-evidence.json).

### PY-05 — GitHub Work Management adapter and webhook ingress

- Issue: [53](https://github.com/AlienLogicLab/alienintent/issues/53); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2C4`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-005", "extent": "Primary — port plus first (GitHub Projects) adapter"}, {"id": "SF-REQ-001", "extent": "Event-driven freshness of the READY view"}, {"id": "SF-REQ-008", "extent": "Ingress custody: durable receipt before acknowledgment"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-03, PY-04. Native blocked-by read-back: PY-03, PY-04.
- Agent-Ready: **READY**, rework locality LOW.
- Accepted candidate: `761bc21c5c861317c88d3db16bb7de05425f329b`; merge: `5b617a3efaaa0fd74a02efc4263860e821548c40`.
- Combined verifier rejections: 2; FOUNDER_EXCEPTION markers: 0.
- ACCEPT marker: `2026-09-20T13:35:31Z`; DONE marker: `2026-09-20T13:40:36Z`; dispatcher DONE: `2026-09-20T13:40:41.916Z`; Issue closure: `2026-09-20T13:43:21Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/53#issuecomment-5750136613), [closure](https://github.com/AlienLogicLab/alienintent/issues/53#issuecomment-5750162413), [trajectory](execution-trajectories/PY-05.jsonl), [Quality Evidence](quality/PY-05-quality-evidence.json).

### PY-06 — Invocation runtime and candidate custody

- Issue: [54](https://github.com/AlienLogicLab/alienintent/issues/54); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2D8`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-007", "extent": "Primary — enforced in the control plane, not worker instructions"}, {"id": "SF-REQ-009", "extent": "Capability grants and fail-closed budgets"}, {"id": "SF-REQ-003", "extent": "Per-invocation workspace isolation"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-04, PY-05, PY-02, PY-03. Native blocked-by read-back: PY-04, PY-05.
- Agent-Ready: **READY**, rework locality MEDIUM.
- Accepted candidate: `e660748686ffaf66340e44760dc88c898f35a0ff`; merge: `896c0fe567fd022622500ee56f5d51a4e34032ec`.
- Combined verifier rejections: 4; FOUNDER_EXCEPTION markers: 1.
- ACCEPT marker: `2026-09-20T15:52:59Z`; DONE marker: `2026-09-20T15:58:54Z`; dispatcher DONE: `2026-09-20T15:58:59.927Z`; Issue closure: `2026-09-20T21:48:03Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/54#issuecomment-5750872643), [closure](https://github.com/AlienLogicLab/alienintent/issues/54#issuecomment-5750903886), [trajectory](execution-trajectories/PY-06.jsonl), [Quality Evidence](quality/PY-06-quality-evidence.json).

### PY-07 — HumanDecisionRequired and Decision Inbox

- Issue: [55](https://github.com/AlienLogicLab/alienintent/issues/55); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2Fc`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-006", "extent": "Primary"}, {"id": "SF-REQ-035", "extent": "Primary — application service and durable decisions; CLI surface is PY-08"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-04, PY-05. Native blocked-by read-back: PY-04, PY-05.
- Agent-Ready: **READY**, rework locality LOW.
- Accepted candidate: `9caaa71f89aeac3fdecd2cc0ef3ad566ca96ebf2`; merge: `946e3cc0b17951f561632f3e6474a715f541302d`.
- Combined verifier rejections: 5; FOUNDER_EXCEPTION markers: 2.
- ACCEPT marker: `2026-09-20T19:54:17Z`; DONE marker: `2026-09-20T19:58:37Z`; dispatcher DONE: `2026-09-20T19:58:44.009Z`; Issue closure: `2026-09-20T21:48:06Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/55#issuecomment-5752257418), [closure](https://github.com/AlienLogicLab/alienintent/issues/55#issuecomment-5752283995), [trajectory](execution-trajectories/PY-07.jsonl), [Quality Evidence](quality/PY-07-quality-evidence.json).

### PY-08 — Operator Control Plane CLI (P0 minimum)

- Issue: [56](https://github.com/AlienLogicLab/alienintent/issues/56); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2Hk`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-034", "extent": "The **P0 minimum** only; the P5 polish scope stays open (Wave 6)"}, {"id": "SF-REQ-035", "extent": "Operator surface over the PY-07 service"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-07. Native blocked-by read-back: PY-07.
- Agent-Ready: **READY**, rework locality MEDIUM.
- Accepted candidate: `b76d639ec8eb8449ed0baf4515c01689d77e68c5`; merge: `2c179e5e25ddefffe11690046948a4bc53e8e2a3`.
- Combined verifier rejections: 6; FOUNDER_EXCEPTION markers: 1.
- ACCEPT marker: `2026-09-21T00:53:07Z`; DONE marker: `2026-09-21T01:00:34Z`; dispatcher DONE: `2026-09-21T01:00:41.420Z`; Issue closure: `2026-09-21T01:03:00Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/56#issuecomment-5754017466), [closure](https://github.com/AlienLogicLab/alienintent/issues/56#issuecomment-5754059192), [trajectory](execution-trajectories/PY-08.jsonl), [Quality Evidence](quality/PY-08-quality-evidence.json).

### PY-09 — Doctor and pre-autonomy validation

- Issue: [57](https://github.com/AlienLogicLab/alienintent/issues/57); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2Io`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-038", "extent": "Primary"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-05, PY-06, PY-08. Native blocked-by read-back: PY-05, PY-06, PY-08.
- Agent-Ready: **READY**, rework locality LOW.
- Accepted candidate: `24cdd64f0dc565d537052cedca8c3341503359b1`; merge: `85b606037e144e977c1bc1f7b0aa795d97e19d83`.
- Combined verifier rejections: 3; FOUNDER_EXCEPTION markers: 0.
- ACCEPT marker: `2026-09-21T03:30:36Z`; DONE marker: `2026-09-21T03:38:15Z`; dispatcher DONE: `2026-09-21T03:38:22.332Z`; Issue closure: `2026-09-21T03:40:19Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/57#issuecomment-5755009604), [closure](https://github.com/AlienLogicLab/alienintent/issues/57#issuecomment-5755058363), [trajectory](execution-trajectories/PY-09.jsonl), [Quality Evidence](quality/PY-09-quality-evidence.json).

### PY-09B — Live GitHub transport and projection substrate

- Issue: [68](https://github.com/AlienLogicLab/alienintent/issues/68); Project item `PVTI_lADOEcrpC84Bj5i_zg748m4`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-005", "extent": "The first **live** GitHub adapter behind the existing port"}, {"id": "SF-REQ-007", "extent": "Live repository access sufficient for custody against the sandbox"}, {"id": "SF-REQ-038", "extent": "The live transport probes `doctor` needs to establish readiness"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-09, PY-05, PY-06, PY-08. Native blocked-by read-back: empty.
- Agent-Ready: **READY**, rework locality MEDIUM.
- Accepted candidate: `3bc361e6ae313285b8364a0f8ececa593c997d86`; merge: `93dd8b1078a26b157df316bd21e8510ea4d86156`.
- Combined verifier rejections: 0; FOUNDER_EXCEPTION markers: 0.
- ACCEPT marker: `2026-09-21T10:27:29Z`; DONE marker: `2026-09-21T10:34:24Z`; dispatcher DONE: `2026-09-21T10:34:30.544Z`; Issue closure: `2026-09-21T10:36:42Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/68#issuecomment-5759003341), [closure](https://github.com/AlienLogicLab/alienintent/issues/68#issuecomment-5759083753), [trajectory](execution-trajectories/PY-09B.jsonl), [Quality Evidence](quality/PY-09B-quality-evidence.json).

### PY-10 — Wave 1 live proof on the dedicated sandbox

- Issue: [58](https://github.com/AlienLogicLab/alienintent/issues/58); Project item `PVTI_lADOEcrpC84Bj5i_zg7x2K4`; final **DONE / CLOSED**.
- Requirements (contract extent): [{"id": "SF-REQ-001", "extent": "Live end-to-end proof"}, {"id": "SF-REQ-002", "extent": "Live"}, {"id": "SF-REQ-003", "extent": "WIP = 1 demonstrated live"}, {"id": "SF-REQ-004", "extent": "Live"}, {"id": "SF-REQ-005", "extent": "Live against a real GitHub Project"}, {"id": "SF-REQ-006", "extent": "Live"}, {"id": "SF-REQ-007", "extent": "Live, before VERIFY"}, {"id": "SF-REQ-008", "extent": "Live restart mid-run"}, {"id": "SF-REQ-009", "extent": "Live"}, {"id": "SF-REQ-010", "extent": "Live"}, {"id": "SF-REQ-034", "extent": "Operated live"}, {"id": "SF-REQ-035", "extent": "Live decision recorded"}, {"id": "SF-REQ-038", "extent": "Live gate before start"}]. Extent is the contract contribution, not a declaration that the entire Product Requirement is DONE.
- Declared predecessors: PY-09B, PY-05, PY-06, PY-08, PY-09. Native blocked-by read-back: PY-05, PY-06, PY-08, PY-09, PY-09B.
- Agent-Ready: **READY**, rework locality MEDIUM.
- Accepted candidate: `04bc54bada9c1e5a0ec3758f05dc9a3c82ab4190`; merge: `10cc81620511af56befbb6140504d1991bb02846`.
- Combined verifier rejections: 0; FOUNDER_EXCEPTION markers: 0.
- ACCEPT marker: `2026-09-21T12:11:25Z`; DONE marker: `2026-09-21T12:18:10Z`; dispatcher DONE: `2026-09-21T12:18:17.618Z`; Issue closure: `2026-09-21T12:21:51Z`.
- Evidence: [ACCEPT](https://github.com/AlienLogicLab/alienintent/issues/58#issuecomment-5760269849), [closure](https://github.com/AlienLogicLab/alienintent/issues/58#issuecomment-5760356977), [trajectory](execution-trajectories/PY-10.jsonl), [Quality Evidence](quality/PY-10-quality-evidence.json).

## Verification and limitations

[Machine-readable manifest](wave1-closure-manifest.json), [retained source observations](wave1-source-observations.json), [consistency report](wave1-consistency-report.md), [yield snapshot](wave1-yield-snapshot.md). Requirements retain their scoped contribution: this is not full Product Requirement completion or Python Sovereignty. UNKNOWN telemetry is not zero. No Wave 2 design, learning consolidation or implementation is authorized by this record.

Authority qualification: PY-09B/PY-10 Claude producer use is corroborated, but an extension of the PY-09-only recovery authorization is UNKNOWN. See [late-arriving evidence](wave1-evidence-reconciliation.md#late-arriving-participant-evidence-and-provider-authority-qualification). This manifest does not ratify operational authority.
