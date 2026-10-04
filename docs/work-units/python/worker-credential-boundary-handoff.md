# Handoff for WORKER-CREDENTIAL-BOUNDARY (work item 7efccee9-13f0-4905-a0a1-e80bc2faa748)

Attached to the assessed packet `docs/work-units/python/worker-credential-boundary.md` at packets `7ae59a6a5a62bc741138b70ab27ff442593dbec1` (sha256 507a267a…),
assessment `readiness/7efccee9-13f0-4905-a0a1-e80bc2faa748/3b2d38df-384c-4be0-bf2d-6cb970955ba1/raw` (READY). Founder implementation approval 2026-10-04. Binding on the PRODUCER and the VERIFIER.

- Do not modify the live machine: create no Unix user, write no sudoers file, set no ACL, change no permission outside
  temporary test folders. `tools/live/setup_worker_user.sh` and `tools/live/worker_boundary_check.py` are written and
  dry-run tested only; the Founder runs them.
- Landing stays disabled. The factory App's permissions are unchanged. A passing worker boundary does not complete the
  credential-separation prerequisite: Factory Director cognition is separate later work.
- From the revision 3 review: set `GIT_DIR` explicitly on control-plane git calls that reach the remote, as well as
  `GIT_COMMON_DIR`; check 6(e) also plants a `config.worktree` and shows it is not read.
- Verdict files: first line exactly `ACCEPT` or `REJECT`, naming the work item and the full candidate SHA.

## Revision 6 (structural ownership split, Founder decision B)
- Build fresh from main against packet revision 6. Candidates a388f16, 71b88a8 and 0faf472 are retired; do not reuse
  their branch. Reusing small, reviewed pieces of hardening is fine only where revision 6 still calls for them.
- The round 2 checklist (`~/.local/state/alienintent/manual/worker-boundary-verification/round2-checklist.md`) and its
  BLOCKING rule bind the VERIFIER.
- The setup script's final checks also assert that the packets clone's `.git/config` holds no credential, URL user
  information, `http.*.extraheader` or `url.*.insteadOf` (Agent Ready note on revision 6, attempt 0e9b282a).
- Check 8(c) needs a genuinely registered, approved work item at proof time, or it is recorded as unresolved.

## Revision 7 (bounded context export, after the live proof)
- Canonical evidence stays private. Do not weaken `LocalEvidenceRepository` or its `UNSAFE_ROOT` check. Workers get
  only `<launch>/exports/<c>/context.json` (section 0.6b). The setup grants nothing on the databases, the evidence
  repository or the registry configuration, and restores owner-only modes after removing old grants.
- Build fresh from main against revision 7. Candidates up to 1f1e1e3 are retired; reuse only reviewed pieces that
  revision 7 still calls for.
- Checklist additions for revision 7 are in the round 2 checklist.

## Live-proof repairs (2026-10-04)
- 7ca5f54: the setup's `unreachable` check judged by path type (verdict-7ca5f54.md).
- 156ef20: the worker clone and fetch give `safe.directory` to upload-pack (`--no-local` for the clone). The proof
  keeps bounded, redacted diagnostics, and a 422 from 8(d) is UNRESOLVED (verdict-156ef20.md).
- Packet wording to correct at the next packet revision: section at worker-credential-boundary.md:150 still says
  `--no-hardlinks`; the code uses `--no-local` with the upload-pack exception.
- Known, not fixed: prepare_home's `.gitconfig` names the packets clone without `/.git`. It is unused now that the
  clone carries its own exception.

## Revision 8 (persistent worker-owned Codex login)
- Build on 156ef20 (branch producer/worker-boundary-r7-7efccee9). Its other live checks passed (a, b, e, f, g).
- The only substantive change: one shared `prepare_worker_session`; `CODEX_HOME=<launch>/worker/auth/codex`; the
  login check as the worker in `prepare`; cleanup of all but auth.json; no login file is ever read or copied.
- The Founder runs the one-time worker `codex login` after the VERIFIER accepts, never before.
