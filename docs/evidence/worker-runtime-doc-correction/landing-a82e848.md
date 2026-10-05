# Exceptional manual landing: WORKER-RUNTIME-DOC-CORRECTION candidate a82e848

- Candidate: `a82e848173e5b18489e31a9afdfeba5aa32a6ccc`, produced by the factory's PRODUCER for work item `8427eb3d-401e-4f4a-8d7c-12abd979c211`
  (correlation `launch:8427eb3d-401e-4f4a-8d7c-12abd979c211:2`, run as `alienintent-worker`), published to
  `candidate/launch-8427eb3d-401e-4f4a-8d7c-12abd979c211-2` with independent read-back.
- Landed by fast-forward of `main` from `759b5dbb3e625d08d5b3f7ec4409660279104d01` (the candidate's parent and the release record's starting
  revision), so the candidate SHA is preserved. No pull request.
- Independent VERIFIER (correlation `launch:8427eb3d-401e-4f4a-8d7c-12abd979c211:4`, run as `alienintent-worker`):
  verdict `accept`, no findings, for revision `a82e848173e5b18489e31a9afdfeba5aa32a6ccc` (`verifier-verdict.json`, sha256 `f3c1ba21a035952efdf1b04f91cd0f2397d640bb182bea2f827e4ff5d7dfa2df`); passing feature-regression
  receipt for base `759b5dbb3e625d08d5b3f7ec4409660279104d01` and this candidate (`verifier-feature-regressions.json`, sha256 `0cdf4ee8d1479e0c386bd714ac2da77ed62c32bfcd273e5c5003b87f29e9c192`). Both are the
  worker's own result files, copied unchanged. `journal-8427eb3d.jsonl` holds the invocation journal entries.
- Deterministic content proof (no model invocation): applying the packet's five exact replacements
  (`docs/work-units/python/worker-runtime-doc-correction-r5.md` section 2) to `759b5dbb3e625d08d5b3f7ec4409660279104d01` gives byte-identical files to
  the candidate; the candidate changes only the two authorized documents.
- **Why manual:** normal factory ACCEPT and CLOSURE were impossible. The packet's `required_evidence` held free-text
  values that are not evidence ids the coordinator can observe (`factory_coordinator.py` evaluate_verdict over
  `artifact-verified` and `independent-verifier-accepted`; `verdict.py`: "required trusted evidence is missing").
  The coordinator therefore recorded `rework` after the VERIFIER's genuine accept. This was not a VERIFIER rejection
  and not a defect in the candidate.
- **Not recorded:** no ACCEPT, CLOSURE or DONE event is recorded for `8427eb3d`; its factory history stays as it is
  (IMPLEMENT/rework, then the Founder's operator cancellation). The work item is not DONE.
- The PRODUCER's bounded export is kept outside the repository at
  `registry/launch/exports/launch:8427eb3d-401e-4f4a-8d7c-12abd979c211:2/context.json` (sha256 `be18278a3fa8888b5cd7903e3307d89a42bff936eea62573e6636cf1adf170bf`) for check 8(c2).
- Founder decision 2026-10-05: land a82e848 without another VERIFIER invocation, as an exceptional manual landing
  with provenance. Debt: LIFECYCLE-SATISFIABILITY / READY-REACHABILITY.
