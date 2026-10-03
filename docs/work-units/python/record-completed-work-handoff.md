# Handoff for the record-completed-work unit (work item cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0)

Attached to the assessed packet `docs/work-units/python/record-completed-work.md` at packets
`71eb20cf3fc4c90a2ea55e536edef33da475f972` (sha256 06d342ee…), assessment
`readiness/cfd57b7e-c296-4f39-ae8c-7f134e5fa2e0/176e3429-f60d-49b9-915d-ad57a529192c/raw` (READY).
Binding on both the PRODUCER and the VERIFIER. The packet text is not changed.

## 1. Sequence (Founder, 2026-10-03)
1. Real use on a copy of the work registry, run by the Founder, before acceptance (check 5).
2. VERIFIER, then a separate CLOSURE lands the unit.
3. Only after landing: the Founder records 6c-1's completion in the permanent work registry.
4. Then unit 6c-2's real-provider check.

## 2. Unused evidence records (Founder, 2026-10-03)
An evidence record left unreferenced (a different valid request before the row is DONE, or the race in the row
transaction) is never completed-work evidence: only the row's `verification_ref` counts, and the dependency reader
reads that reference only. Keeping or removing such records is a cleanup obligation for a later, explicit
evidence-retention policy. It is not part of this packet; do not add cleanup code here.

## 3. Assessment notes passed on
- First confirm on `main` that the existing evidence repository takes the `work-completion` record with no change
  outside `authorized_scope`; otherwise stop and report.
- The service itself refuses abbreviated SHAs and branch names; the existing resolver accepts them.
- Read the instructions' bytes for the sha256 through the existing `read_packet`; no new git call.
- Dependency precedence: the coordinator record first, the work registry row only when there is none. Test bare DONE
  and conflicting DONE.
- The row update's `WHERE` clause holds the read state, the checked pointer commit and `retired_at IS NULL`.
- 6c-1's real evidence (checked by the REVIEWER and the coordinating session):
  - landing record `docs/evidence/work-context-package-landing-c366884.md` at `a5087d71439792a7e1efd96711cdfa85803049ac`
    names the identity, the full candidate `c36688492487c41aa41aebd4778d54aec7ceeece` and the packet sha256
    `544be3fea4e1edca405da16805e1bd93360bfc6012e343b9fed4190fcffa3ed0`;
  - verdicts `/home/netmarine/.local/state/alienintent/manual/work-context-verification/round1-4580d5b/verdict.md` and
    `.../round2-c366884/verdict.md` (round 2 is the ACCEPT naming the candidate and the identity);
  - approval `/home/netmarine/.local/state/alienintent/registry/approvals/5befff2f-a0dd-4cea-9556-54c33ed86c1b.json`
    (`commit` = the row's pointer `5b25c8390a9fcf672ec6bc6a1ba85547685a8186`).
- The real-use script never opens the permanent `work.sqlite`, `readiness.sqlite` or `readiness-evidence/` for writing.
