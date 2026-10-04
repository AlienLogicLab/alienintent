# Handoff for AUTOMATED-CLOSURE (work item 0677f8bb-71c2-4c62-8b4a-d0e5318ba689)

Attached to the assessed packet `docs/work-units/python/automated-closure.md` at packets `49f1958723a4275436de7dadb58e9d1fa4c38b59` (sha256 df153d8c…),
assessment `readiness/0677f8bb-71c2-4c62-8b4a-d0e5318ba689/21e13a72-0b61-4ebc-b514-9c4e0c47fc8f/raw` (READY). Founder implementation approval 2026-10-04 (manual release path). Binding on the PRODUCER and
the VERIFIER. The packet text is not changed.

- Landing stays disabled. Do not set `"landing": true` anywhere outside test fixtures. The factory App permission
  change is not authorized, and the App's recorded permissions show no `contents` access.
- Operating-system credential separation is a separate later unit. Check 7 proves the code path only; claim nothing more.
- Byte-for-byte preservation is required for free-text contracts (`closure-not-automated`), unscoped minting without
  the new keywords (the sandbox profile), and the sandbox and K2 profiles. Run their existing tests unchanged.
- Confirm every interface the packet names at `789240c` before relying on it. A mismatch is a stop condition.
- The fake token endpoint answers with the requested permissions; real GitHub scoping is proved only in check 17.
- Verdict files: the first line is exactly `ACCEPT` or `REJECT`, with nothing else on it, and the file names the
  work item and the full candidate SHA.
