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
