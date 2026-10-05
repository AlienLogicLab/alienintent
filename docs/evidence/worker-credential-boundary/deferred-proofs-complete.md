# WORKER-CREDENTIAL-BOUNDARY: the two deferred live proofs passed

- Work item `7efccee9-13f0-4905-a0a1-e80bc2faa748`, candidate `2078b37084c6ed11b64f72606101c4d6c1589818`, landed on
  `main` `723f162` (`landing-2078b37.md`).
- **8(c2) PASS** (`proof-c2.jsonl`, sha256 `d672fc63476a8eaf74052a6b5aa366d0f56510160d6fdc8993c02dba689cd4c5`): run with `--package` on the bounded export of a real factory
  launch, `registry/launch/exports/launch:8427eb3d-401e-4f4a-8d7c-12abd979c211:2/context.json`, whose PRODUCER ran as
  `alienintent-worker`; the context command reprinted exactly that package from the export only, and the canonical
  evidence repository stayed unreadable to the worker. 8(a), 8(b), 8(c1) (two consecutive native Codex invocations),
  8(e), 8(f) and 8(g) passed in the same run; 8(d) was then still UNRESOLVED on the expected 422.
- **8(d) PASS** (`proof-8d.jsonl`, sha256 `a46419fcb48fa715ccb7e115ef81eade1d09b657a4202c87c6115375e9002a34`): after the Founder granted the App `contents: write` and the
  protected-main bypass, the unchanged check minted through the Landing Authority's own InstallationCredentials a token
  with exactly `{"contents": "write", "metadata": "read"}`, repository selection `selected`, and the evidence root's
  mode unchanged.
- Claim boundary: a pass proves the worker credential boundary only. It does not prove the Factory Director boundary.
  No confidentiality between worker sessions is claimed.
