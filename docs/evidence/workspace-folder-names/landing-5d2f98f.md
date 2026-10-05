# WORKSPACE-FOLDER-NAMES landing record (candidate 5d2f98f)

- Work item: `6e06e5dc-34a6-4125-b69d-bdfce0d850a8`. Packet `docs/work-units/python/workspace-folder-names.md`, sha256 `914222d971ae583a4e24303a7fb9d8c33fa6f497322b1c8356454317678e673c`, published on alienintent/work-packets at `234add9a45172d6437a42104ca12b0160561ea66`, assessed READY
  (attempt `e6ccf6dd-f7f4-423d-b9f6-6d3100c269df`), approved by the Founder 2026-10-05 ("I approve").
- Candidate: `5d2f98f2cbee27ca621027ca8a72e36fbd693b18` (one commit on `5dbaa09d185733a9812dc663f23a251e7eb52bf4`), built outside the factory: its own VERIFIER would have failed on the ':'
  folder names it fixes.
- Fresh VERIFIER: ACCEPT (`verdict-5d2f98f.md`). 199 passed; architecture fitness PASS; the boundary test fails on
  `5dbaa09d185733a9812dc663f23a251e7eb52bf4` with `No module named 'alienintent'` and passes on the candidate; as `alienintent-worker`, the
  feature-regression runner passed in `<launch>/worker/verifier-launch-6e06e5dc-34a6-4125-b69d-bdfce0d850a8-99`.
- Landed by fast-forward of `main` from `5dbaa09d185733a9812dc663f23a251e7eb52bf4`, preserving the candidate SHA. No pull request.
