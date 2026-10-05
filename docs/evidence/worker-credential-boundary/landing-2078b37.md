# WORKER-CREDENTIAL-BOUNDARY landing record (candidate 2078b37)

- Work item: `7efccee9-13f0-4905-a0a1-e80bc2faa748`. It stays **open**: 8(c2) and 8(d) are deferred live proofs.
- Candidate: `2078b37084c6ed11b64f72606101c4d6c1589818` (branch producer/worker-boundary-r7-7efccee9, commits e826721, 7ca5f54, 156ef20, 2078b37).
- Packet: revision 8, `docs/work-units/python/worker-credential-boundary.md`, sha256 `a1948d434c49763fbf6a3ef973c95612dbb7325dbc83199decfda4828ed5ae74`; published on
  alienintent/work-packets at `df6986c7e2a668839eee195035f7e091de57f1ff`, assessed READY (attempt
  `7e9e436f-7662-498b-a80c-ac580417145c`).
- VERIFIER verdicts (all ACCEPT, fresh sessions, exact SHAs): verdict-e826721.md, verdict-7ca5f54.md,
  verdict-156ef20.md, verdict-2078b37.md.
- Founder-run live proof on 2078b37 (proof-2078b37.jsonl, sha256 3919bf1b44ccefad4d470646decc7da422dc48bc9848a52cf14b4d4969d62e40):
  8(a) PASS; 8(b) PASS; 8(c1) PASS (two consecutive real Codex invocations, both return code 0, worker-owned 0600
  auth.json, Founder login unchanged); 8(c2) UNRESOLVED; 8(d) UNRESOLVED (`github answered 422 where 201 was
  required`); 8(e) PASS; 8(f) PASS; 8(g) PASS.
- Founder 2026-10-05: with exactly this result, the implementation is technically accepted for landing to main.
- 8(d) UNRESOLVED: expected GitHub 422 because the Founder has not authorized the App's landing permission. This is
  an explicit dependency on the later protected-main authority decision, not evidence of a worker-boundary defect.
  Any response other than the specifically recognized 422 remains FAIL.
- 8(c2) UNRESOLVED: a sequencing dependency. It needs this implementation on main and one genuine launched work item.
- Claim boundary: a pass proves the worker credential boundary only. It does not prove the Factory Director
  boundary, and it is not the protected-main landing authorization. No confidentiality between worker sessions is
  claimed.
- Next: one small, genuine, approved work item for 8(c2); then the Founder's App-permission decision; then 8(d)
  rerun exactly.
