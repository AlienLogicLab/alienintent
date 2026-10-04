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
