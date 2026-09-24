# BRD-83 — Complete Issue #83: version-controlled release-admission reader

This is the remaining bounded work of existing Issue **#83**, "Repair GitHub Project board visibility and
command path", executed through #83's own lifecycle. It is not a Wave 2 DAG node and adds no new Issue.

Baseline: `origin/main` @ `5d3d14a`.

## Intent

The release-admission gate must read a BIU's readiness evidence from the durable source, and must work for
any BIU identifier. That removes the need for the manual native-receipt comment. This closes #83's first
observed regression, which the Factory Director reconciliation of 2026-09-24 recorded as NOT MET.

## Authority

- Issue #83: its scope, its acceptance criteria and its "Observed regression" paragraph.
- Founder direction 2026-09-24: finish #83 using #83 itself, through the normal lifecycle.

## Current state (evidence)

- The gate lives **outside the repository**: `~/.local/share/alienintent-bootstrap/release_admission.py`
  (sha256 `fb8758cecb4db13073be71e39f37c77250b018406d7c968e45d1fa57231b9b1b`). Its tests are in
  `test_release_admission.py` (sha256 `e8000ad29d07d6a6064a7f4982b760ca957376e9d518991b8c8497a2954e5e4e`,
  23 tests, all passing). No repository artifact governs or tests it.
- `WORKDIR` is hard-coded to the shared checkout, and assessment records are read with `Path.read_text()`
  from its working tree. A record landed on `origin/main` but not yet present in that checkout is invisible.
- `WAVE2_RECORD` matches only `WO-\d{6}` record paths, and `biu_from_body` only `PY-NN[A-Z]?` and `WO-NNNNNN`.
  Any other BIU, such as ARP-01 or FDH-01, falls back to the native-receipt comment.
- Observed 2026-09-24: `release_admission.py 80` and `81` returned `agent_ready=None`, although both
  have native READY records committed on `main`. Their Issue bodies do not cite the record path.

## Scope (bounded extent)

1. **Bring the gate under version control.** Add `tools/live/release_admission.py` and
   `tools/live/test_release_admission.py`. The first commit copies both files **verbatim**, matching the
   sha256 values above, so custody is checkable. Later commits carry the changes.
2. **Read from the release point.** Resolve assessment records with `git show <release-point>:<path>`,
   where the release point defaults to `origin/main`, instead of reading the working tree. Derive the
   repository root rather than hard-coding a path. A record present only in the working tree must not
   be used.
3. **Recognise any BIU identifier.** Treat any path of the form
   `docs/evidence/wave2-readiness-assessments/<ID>.<stamp>.assessment.json` in the Issue body or a
   Director release record as a readiness record. `<ID>` is a single path segment of letters, digits and
   hyphens. Reject path traversal and any other directory. Keep the Wave 1 `PY-NN[A-Z]?` path unchanged.
4. **Unchanged:** the SWF-21 admission conditions in `admit()`, the native-receipt comment
   fallback, and the CLI contract (`release_admission.py <issue> [release-point]`, exit 0 admits,
   exit 1 refuses).

## Non-goals

- Changing any admission condition, the dispatcher, the materialization tool or Project state.
- Removing the native-receipt fallback.
- Switching live operations to the repository copy. That is a Factory Director action after landing.
- Editing any Issue body, and any other bootstrap module.

## Acceptance criteria

1. The first candidate commit adds both files byte-identical to the pinned sha256 values. The 23 existing
   tests pass in the repository location.
2. A record committed at the release point but absent from the working tree is found, and its
   disposition used. A record present only in the working tree is **not** used.
3. Records for `ARP-01`, `FDH-01` and `WO-220202` identifiers are recognised from the body or the release record.
   A path with `..`, a `/` inside the identifier, or a different directory is rejected.
4. The native-receipt comment fallback behaves exactly as before.
5. Issue #83 AC3 is met by an offline, disposable fixture: a temporary git repository with a release-point
   commit and fake `gh` responses. There is no live Project or Issue mutation.
6. Each new rejection or refusal test is shown failing against a deliberately permissive variant before
   passing.
7. `node scripts/check.mjs all` exits 0. The evidence and orchestration Python suites show no new failure.
   The known baseline failure `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`
   is non-hermetic: it reads the live `~/.codex/config.toml`. It is dispositioned as in ARP-01 and must
   not be modified here.

## Verification obligations

An independent VERIFIER retrieves the exact candidate SHA in its own worktree and re-runs criteria 1–7. It
applies each negative control, and records the commands, exit statuses and counts.

For #83 closure, the VERIFIER also performs the independent review that #83's landed repair never
received: `62b85e0` and `aa2b263` (merged in `13cac4e`), read against #83 AC2 and AC4. It reports findings
with file and line references. This review is read-only; it does not reopen landed code unless it finds a
defect.

## Evidence obligations

- Retain the candidate branch and full SHA, the commands, exit codes, test counts and negative-control
  counts.
- Record the verbatim-import digests.

## Execution packet and allocation

- PRODUCER Morty on Claude; independent VERIFIER JC on Codex (Founder routing policy, 2026-09-24).
- Concurrency 1.
- 3 execution cycles and 1 replacement per phase, bound in `execution.biuLimits` for #83 before release.
- Wall-clock bounded by systemd supervision.

Landing: SWF-19. Merge the accepted candidate branch directly into `main`, preserving the accepted SHA.
**Do not open a pull request.** AlienIntent does not use pull requests.

Release authority is not granted by this document.

## Stop and escalation

Stop on:

- a digest mismatch on import;
- a source revision mismatch;
- unavailable evidence;
- a failing discriminating probe;
- any need to change an admission condition.

Scope questions go to the Factory Director.
