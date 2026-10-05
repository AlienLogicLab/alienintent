ACCEPT

Verifier: fresh, narrow, read-only. Work item 7efccee9-13f0-4905-a0a1-e80bc2faa748 (WORKER-CREDENTIAL-BOUNDARY).
Candidate 7ca5f549e04c7ccaa92f7ec0c496f5a8e6780a69 on e826721. Worktree
/home/netmarine/.local/state/alienintent/manual/producer-worker-boundary-r7-7efccee9: HEAD is 7ca5f54 and the tree
was clean before and after the checks.

## 1. Only the final-check meaning changed

`git diff e826721 7ca5f54` touches two files only:
- /home/netmarine/.local/state/alienintent/manual/producer-worker-boundary-r7-7efccee9/tools/live/setup_worker_user.sh (+5 -2)
- /home/netmarine/.local/state/alienintent/manual/producer-worker-boundary-r7-7efccee9/tests/composition/test_worker_launch.py (+31, one new helper and one new test)

The only script change is the body of `unreachable()`, at
tools/live/setup_worker_user.sh:152-158. No setfacl, chmod, install or sudoers line changed (lines 61-131). No other check
changed (lines 135-151 and 159-173).

The new rule:
- A folder (`[ -d ]`, :153-154): unreachable only if the worker can neither `ls -a` it nor pass `test -x`. Correct.
- A file, including a symlink, even a broken one (`[ -e ] || [ -L ]`, :155-156): unreachable only if the worker fails
  `test -r` AND `head -c1`. Looking up the name is allowed now. This is the fix.
- Absent (:157): an `if` where no branch runs returns 0, so the path counts as unreachable. Correct.

Path types I looked at:
- Symlink to a folder: `-d` follows it, so the folder rule runs, and `ls`/`test -x` also follow it. Correct.
- Symlink to a file: `test -r`/`head` follow it. Correct.
- Broken symlink: counts as unreachable, which is true now. The evidence paths also go through `private_evidence`
  (:159-164), which rejects any symlink.
- FIFO or device: the file rule runs. `head` runs only after `test -r` has failed, so it cannot block on a FIFO. This is
  better than before, when `head` ran first.
- Absent to the root shell but present to the worker: `runuser` shares root's mount namespace, so I see no real case.
- Minor, does not block: the file rule checks only read access. A write-only file (for example mode 0602, or an ACL
  `-w-`) would pass, and so would a socket the worker could connect to. The old check never tested write access
  either. It only failed every file "by accident", through `ls`. The setup actions at :94-98 (`setfacl -b` + `chmod 0600`
  on the configuration, both databases and their sidecars) remove all worker access anyway. If wanted later, adding
  `! as_worker test -w "$1"` to :156 would close this. It is not needed for this candidate.

## 2. The live boundary is not weakened

- The same paths are checked: configuration, every database, every -wal/-shm sidecar, the evidence folder and
  evidence/objects (:165-169). That list did not change. `private_evidence` (:170) did not change.
- Nothing new gives the worker access to the configuration, the databases or the evidence repository. The dry-run output
  (below) is byte-identical between the two commits.
- The worker gets only `--x` on parent folders (:109-124). It gets no ACL on the registry files.

## 3. Tests and dry run

- `python3 -m pytest -q tests/composition/test_worker_launch.py` (run through rtk): 59 passed, 0 failed. The new test ran
  because I am not root.
- Setup dry run without root, with the exact arguments given: both e826721 and 7ca5f54 exit 0, and `cmp` reports the two
  outputs as IDENTICAL (82 lines, ending "dry run: nothing changed"). Scratch files are in /tmp/claude-1000/wbv7/
  (old.sh, new.sh, old.out, new.out). new.sh matches the tracked file in the worktree.
- The new test against e826721's script: it fails at test_worker_launch.py:1503, `assert _unreachable(private_file)`.
  That is the reported live bug, a 0000 file whose name `ls` can find. The same test passes against 7ca5f54's script.
  Harness: /tmp/claude-1000/wbv7/test_old_script.py.

## What I did not check

- I did no real (non-dry) setup run, used no sudo, and did not run `runuser` as the real worker. The new test uses the
  current user in place of the worker.
- I did not read the live file modes or ACLs on the registry, and I read no key, database, evidence or secret contents.
- I did not run the full test suite. I ran only tests/composition/test_worker_launch.py.
