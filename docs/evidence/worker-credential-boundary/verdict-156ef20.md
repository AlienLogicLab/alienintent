ACCEPT

# VERIFIER verdict: WORKER-CREDENTIAL-BOUNDARY candidate 156ef20

Work item 7efccee9-13f0-4905-a0a1-e80bc2faa748. Candidate 156ef20effa8d0024d6ab89a7bd7c72b31e85e8d, one commit on the accepted 7ca5f54. Repository /home/netmarine/.local/state/alienintent/manual/producer-worker-boundary-r7-7efccee9. HEAD was 156ef20 and the tree was clean before and after (git 2.43.0).

Claim boundary: a pass proves the worker credential boundary only. It does not prove the Factory Director boundary, and it is not the final protected-main landing authorization.

## Findings

1. No boundary weakening. Confirmed.
   - src/alienintent/invocation_runtime/adapters/git_worktree.py:78-82 `_upload_pack` gives `safe.directory` to the upload-pack only, for exactly one path: the source the worker reads. It is used only at :123 (PRODUCER clone of `<packets>/.git`) and :136 (VERIFIER/CLOSURE fetch from the control-plane intake repository). Both run as the worker through `self._worker` (:103-109).
   - The trust goes one way only: the worker trusts a Founder-owned, read-only source. No privileged process trusts anything the worker writes. The command-line `-c safe.directory=` was removed (the test at tests/invocation_runtime/test_git_source_control.py:478-495 checks this).
   - `--no-local` (:123) makes git copy the objects through the pack transport. It sets up no alternates and no hardlinks.
   - The diff does not touch git_source_control.py or landing_authority.py. The control-plane git is unchanged.
   - In tools/live/worker_boundary_check.py:322-326 the commondir and `.git` file plants now happen after the bundle. This does not hide anything. The import reads only the bundle file, so commondir could only have broken the worker's own `bundle create`. That is the worker hurting itself, not a boundary path. The plants that come after still face `publish_intake`, the intake ref check and the published-SHA check (:327-334). The refs, replace, alternates, config, url.insteadOf, hooksPath and config.worktree plants still happen before the hand-over (:316-320).
   - Small text drift, not blocking: the packet docs/work-units/python/worker-credential-boundary.md:150 still says `git clone --no-hardlinks`, but the code now uses `--no-local` plus the upload-pack exception. Fix the packet wording when it is next touched.

2. No new credential exposure. Acceptable.
   - `_tail` (worker_boundary_check.py:60-73) keeps at most 2000 characters. It redacts `Authorization`/`Bearer`/`token`/`password`/`secret`/`api-key` values, `sk-` keys (this covers sk-proj- and sk-ant-), `gh[pousr]_` and `github_pat_` tokens, three-part JWTs, and any opaque run of 48 or more characters. A 40- or 64-hex SHA stays readable.
   - I probed it directly. Caught: bearer headers, sk-ant keys, gho_ tokens, JWTs, password=, x-api-key. Missed: JSON-quoted `"token": "<short opaque>"`, `access_token`/`refresh_token=<short opaque>`, and `OPENAI_API_KEY=<short non-sk value>`. The cause is that `\b` fails after `_` and the pattern does not expect a `"` before the `:`. So these miss only when the value is short and has no known prefix.
   - Why this is acceptable for a 0644 proof.txt: the c1 tails and the 8(e) worker-command tails are output of processes that already run as the worker. They cannot show the worker anything it does not already have. The 8(d) text comes from the Founder's InstallationCredentials. Every CredentialUnavailable message there is a fixed string, or a status code at installation_credentials.py:160. None holds a token.
   - Defence in depth only, not required: also match `_token` and `_key` suffixes and JSON-quoted keys.

3. No GitHub permission change. Confirmed. LANDING_PERMISSIONS is still `{"contents": "write", "metadata": "read"}` (src/alienintent/composition/landing_authority.py:23). check_d still mints with it (worker_boundary_check.py:224) and still requires an exact match for PASS (:236). The diff does not touch landing authorization.

4. 8(d) semantics. Confirmed.
   - Only when `str(error)` exactly equals `github answered 422 where 201 was required` (:230) is the result UNRESOLVED, with a reason naming the Founder's App permission decision (:231-233). Every other failure is FAIL, and the full safe message is now kept (:228, :234).
   - PASS still needs the minted token to read back exactly LANDING_PERMISSIONS (:236), so it cannot pass without contents:write.
   - `record` returns True only for "PASS" (:55-57), and main reports `passed: all(results)` (:397). So the proof as a whole cannot pass while 8(d) is UNRESOLVED.
   - Small caveat: GitHub can return 422 for other reasons, for example a repository not in the installation. The reason text then names the wrong cause. This is safe, because the result is still not a pass. The Founder should read the 8(d) record together with the App permissions.

5. Crash handling. Confirmed. `_guarded` (:76-81) records a FAIL with the bounded, redacted reason and returns False. main wraps every check (:389-394). check_e_g has its own guard (:299-303), which records 8(e) FAIL with the last failed worker command's return code and redacted stderr (:286-298), and 8(g) UNRESOLVED. Tested at tests/composition/test_worker_launch.py (the `_guarded` crash test).

6. Real scratch worker path, run as the given command with the worker sudo rule:
   - 8(e) PASS: claimed = published = 18f4d18c29c142b613a10ad7351d16b7fa6c4d0a, intake_refs = [refs/intake/proof]
   - 8(g) PASS: the workspace was removed through the sudo rule
   - 8(f) PASS: sudo pid 2422173 is both its process group and its session; 3 worker processes were seen; cancel left none
   - Cleanup: the worker `find ... -delete` returned 0, then `rm -rf` of /tmp/worker-boundary-nuq9_u7o and of the 8(f) results folder /tmp/worker-boundary-results-1z1gweq9. No /tmp/worker-boundary-* is left, and no alienintent-worker process is running (pgrep found none).

7. Tests:
   - `python3 -m pytest -q tests/composition/test_worker_launch.py tests/invocation_runtime/test_git_source_control.py`: 83 passed.
   - `python3 tools/fitness/check_architecture.py --root src/alienintent --check all`: PASS, all architecture fitness checks.

## Pending (only the Founder's own run can settle these; not claimed here)

- 8(c1): a real provider session succeeding as the worker. If it fails again, the record now keeps the redacted stdout and stderr tails.
- 8(d): the true GitHub answer to the landing-scoped mint. The records say App 4990774 has no contents permission, so a 422 and UNRESOLVED is expected. That waits for the Founder's App permission decision. The whole proof cannot pass until it is settled.
- 8(a), 8(b), 8(c2), and 8(e)/(g)/(f) on the real launch layout, all in the Founder's full run.

I made no provider call and no GitHub call or token mint. I read no keys, secrets, databases or evidence. I edited no tracked files and pushed nothing. The only setfacl and chmod were the proof's own, inside its /tmp scratch.
