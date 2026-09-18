#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
preflight="$root/scripts/worker-preflight"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

command="$tmp/invoke"
cat > "$command" <<'WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
role="$1"; shift
case "$role" in
 producer) name=Producer; email=producer-worker@example.test; login=producer-worker; worktree="$BDISP_PREFLIGHT_WORKTREE_PRODUCER" ;;
 verifier) name=VERIFIER; email=verifier-github@example.test; login=verifier-worker; worktree="$BDISP_PREFLIGHT_WORKTREE_VERIFIER" ;;
 *) exit 2 ;;
esac
if [[ "${1:-}" == --profile ]]; then worktree="$worktree/other-profile"; shift 2; fi
node -e 'console.log(JSON.stringify({worktree:process.argv[1],gitName:process.argv[2],gitEmail:process.argv[3],githubLogin:process.argv[4],ghConfigDir:"/tmp/synthetic-config",executables:{githubCli:process.argv[5]}}))' "$worktree" "$name" "$email" "$login" "$(command -v gh)" | "$BDISP_PREFLIGHT" "$@"
WRAPPER
chmod +x "$command"
export BDISP_PREFLIGHT="$preflight"

make_repo() {
  local path="$1" name="$2" email="$3"
  git init -q --initial-branch=main "$path"
  git -C "$path" config user.name "$name"
  git -C "$path" config user.email "$email"
  git -C "$path" commit --allow-empty -qm baseline
  git init -q --bare --initial-branch=main "$path-origin"
  git -C "$path" remote add origin "$path-origin"
  git -C "$path" branch -M main
  git -C "$path" push -qu origin main
  git -C "$path" branch --set-upstream-to=origin/main main >/dev/null
}

make_repo "$tmp/producer" Producer producer-worker@example.test
make_repo "$tmp/verifier" VERIFIER verifier-github@example.test
mkdir -p "$tmp/producer-bin" "$tmp/verifier-bin"
make_gh() {
  local path="$1" login="$2"
  cat > "$path/gh" <<EOF
#!/usr/bin/env bash
case " \$* " in
  *" api user "*) printf '${login}\\n' ;;
  *" repos/sample/widget "*) printf 'sample/widget\\n' ;;
  *"viewerCanUpdate"*) printf 'true\\n' ;;
  *" graphql "*) printf 'WRITE\\n' ;;
  *) exit 22 ;;
esac
EOF
  chmod +x "$path/gh"
}
make_gh "$tmp/producer-bin" producer-worker
make_gh "$tmp/verifier-bin" verifier-worker

base_env=(
  "BDISP_PREFLIGHT_WORKTREE_PRODUCER=$tmp/producer"
  "BDISP_PREFLIGHT_WORKTREE_VERIFIER=$tmp/verifier"
)

run() { (cd "$tmp/producer" && env "${base_env[@]}" PATH="$tmp/producer-bin:$PATH" "$@"); }

run_worker() {
  local worktree="$1" worker="$2" bin="$3"
  shift 3
  (cd "$worktree" && env "BDISP_PREFLIGHT_WORKTREE_PRODUCER=$worktree" "BDISP_PREFLIGHT_WORKTREE_VERIFIER=$worktree" PATH="$bin:$PATH" "$command" "$worker" --json "$@")
}

output="$(run "$command" producer --json)"
grep -q '"safe_to_start":true' <<<"$output"
grep -q '"github":"VERIFIED"' <<<"$output"

output="$(cd "$tmp/producer" && env "${base_env[@]}" PATH="$tmp/producer-bin:$PATH" GH_CONFIG_DIR="$tmp/producer-config" "$command" producer --repository sample/widget --issue 101 --json)"
grep -q '"gh_path":"'"$tmp"'/producer-bin/gh"' <<<"$output"
grep -q '"github_login":"producer-worker"' <<<"$output"
grep -q '"repository_access":"VERIFIED"' <<<"$output"
grep -q '"issue_comment_write":"VERIFIED"' <<<"$output"

output="$(cd "$tmp/verifier" && env "${base_env[@]}" PATH="$tmp/verifier-bin:$PATH" GH_CONFIG_DIR="$tmp/verifier-config" "$command" verifier --repository sample/widget --issue 101 --json)"
grep -q '"gh_path":"'"$tmp"'/verifier-bin/gh"' <<<"$output"
grep -q '"github_login":"verifier-worker"' <<<"$output"
grep -q '"repository_access":"VERIFIED"' <<<"$output"
grep -q '"issue_comment_write":"VERIFIED"' <<<"$output"

make_repo "$tmp/local-ahead" Producer producer-worker@example.test
git -C "$tmp/local-ahead" commit --allow-empty -qm local-ahead
output="$(run_worker "$tmp/local-ahead" producer "$tmp/producer-bin" || true)"
grep -q '"classification":"LOCAL_AHEAD"' <<<"$output"
grep -q '"ahead":"1"' <<<"$output"
grep -q '"behind":"0"' <<<"$output"

make_repo "$tmp/remote-ahead" Producer producer-worker@example.test
git clone -q "$tmp/remote-ahead-origin" "$tmp/remote-ahead-writer"
git -C "$tmp/remote-ahead-writer" config user.name Producer
git -C "$tmp/remote-ahead-writer" config user.email producer-worker@example.test
git -C "$tmp/remote-ahead-writer" commit --allow-empty -qm remote-ahead
git -C "$tmp/remote-ahead-writer" push -q origin main
git -C "$tmp/remote-ahead" fetch -q origin
output="$(run_worker "$tmp/remote-ahead" producer "$tmp/producer-bin" || true)"
grep -q '"classification":"REMOTE_AHEAD"' <<<"$output"
grep -q '"ahead":"0"' <<<"$output"
grep -q '"behind":"1"' <<<"$output"

make_repo "$tmp/diverged" Producer producer-worker@example.test
git -C "$tmp/diverged" commit --allow-empty -qm local-diverged
git clone -q "$tmp/diverged-origin" "$tmp/diverged-writer"
git -C "$tmp/diverged-writer" config user.name Producer
git -C "$tmp/diverged-writer" config user.email producer-worker@example.test
git -C "$tmp/diverged-writer" commit --allow-empty -qm remote-diverged
git -C "$tmp/diverged-writer" push -q origin main
git -C "$tmp/diverged" fetch -q origin
output="$(run_worker "$tmp/diverged" producer "$tmp/producer-bin" || true)"
grep -q '"classification":"DIVERGED"' <<<"$output"
grep -q '"ahead":"1"' <<<"$output"
grep -q '"behind":"1"' <<<"$output"

make_repo "$tmp/no-upstream" Producer producer-worker@example.test
git -C "$tmp/no-upstream" branch --unset-upstream
output="$(run_worker "$tmp/no-upstream" producer "$tmp/producer-bin" || true)"
grep -q '"classification":"NO_UPSTREAM"' <<<"$output"

make_repo "$tmp/wrong-git-identity" Producer producer-worker@example.test
git -C "$tmp/wrong-git-identity" config user.name VERIFIER
output="$(run_worker "$tmp/wrong-git-identity" producer "$tmp/producer-bin" || true)"
grep -q '"classification":"WRONG_IDENTITY"' <<<"$output"
grep -q '"git_name":"VERIFIER"' <<<"$output"

if (cd "$tmp/verifier" && env "${base_env[@]}" PATH="$tmp/verifier-bin:$PATH" GH_TOKEN=founder-token "$command" verifier --repository sample/widget --issue 101 --json) >/dev/null 2>&1; then
  echo "ambient GitHub token unexpectedly passed" >&2
  exit 1
fi

if run "$command" unknown --json >/dev/null 2>&1; then
  echo "unknown worker unexpectedly passed" >&2
  exit 1
fi

output="$(run "$command" producer --profile b-disp --json || true)"
grep -q '"classification":"WRONG_WORKTREE"' <<<"$output"

output="$(cd "$tmp/producer" && env "${base_env[@]}" BDISP_PREFLIGHT_WORKTREE_PRODUCER="$tmp/wrong" "$command" producer --json || true)"
grep -q '"classification":"WRONG_WORKTREE"' <<<"$output"

printf 'dirty\n' > "$tmp/producer/dirty"
output="$(run "$command" producer --json || true)"
grep -q '"classification":"UNEXPLAINED"' <<<"$output"
rm "$tmp/producer/dirty"

make_gh "$tmp/producer-bin" wrong-worker
output="$(run "$command" producer --json || true)"
grep -q '"github":"WRONG_IDENTITY"' <<<"$output"

printf '#!/usr/bin/env bash\nexit 23\n' > "$tmp/producer-bin/gh"
chmod +x "$tmp/producer-bin/gh"
output="$(run "$command" producer --json || true)"
grep -q '"github":"UNVERIFIABLE"' <<<"$output"

# Disposable admission checks use the exact canonical store and baseline resource.
make_gh "$tmp/producer-bin" producer-worker
git -C "$tmp/producer" remote set-url origin https://github.com/sample/widget.git
git -C "$tmp/producer" worktree add -q --detach "$tmp/invocation" HEAD
node --input-type=module - "$preflight" "$tmp" <<'RESOURCE_TEST'
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
const [preflight, directory] = process.argv.slice(2);
const worktree = `${directory}/invocation`;
const baselineCommit = execFileSync('git', ['-C', worktree, 'rev-parse', 'HEAD'], {encoding:'utf8'}).trim();
const worker = { worktree, role:'PRODUCER', invocationId:'owned-invocation', gitName:'Producer', gitEmail:'producer-worker@example.test', githubLogin:'producer-worker', ghConfigDir:'/tmp/synthetic-config', executables:{githubCli:`${directory}/producer-bin/gh`}, resource:{ path:worktree, invocationId:'owned-invocation', role:'PRODUCER', repository:'sample/widget', issue:101, repositoryStore:`${directory}/producer`, baselineCommit, baselineRef:'refs/remotes/origin/main' } };
const run = input => {
  const result = spawnSync(process.execPath, [preflight,'--repository','sample/widget','--issue','101','--json'], {cwd:worktree,input:JSON.stringify(input),encoding:'utf8'});
  return { status:result.status, ...JSON.parse(result.stdout) };
};
assert.equal(run(worker).safe_to_start,true);
for (const patch of [{path:directory},{invocationId:'another-invocation'},{role:'VERIFIER'},{repository:'other/repo'},{issue:102},{repositoryStore:`${directory}/verifier`}]) {
  const result = run({...worker,resource:{...worker.resource,...patch}});
  assert.equal(result.status,1);
  assert.equal(result.classification,'WRONG_REPOSITORY');
}
assert.equal(run({...worker,resource:{...worker.resource,baselineCommit:'0'.repeat(40)}}).classification,'WRONG_BASELINE');
assert.equal(run({...worker,worktree:`${directory}/producer`}).classification,'WRONG_WORKTREE');
execFileSync('git',['-C',worktree,'remote','set-url','origin','https://github.com/other/repo.git']);
assert.equal(run(worker).classification,'WRONG_REPOSITORY');
RESOURCE_TEST

echo "worker-preflight tests: PASS"
