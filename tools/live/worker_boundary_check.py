#!/usr/bin/env python3
"""WORKER-CREDENTIAL-BOUNDARY acceptance check 8: the real-use proof, Founder-run after tools/live/setup_worker_user.sh.

It records (a)-(g) of the packet, each PASS, FAIL or UNRESOLVED, as JSON lines on standard output, and exits 0 only
when every item passes. (a), (b) and (f) run commands as the worker through the one sudo rule; (c1), with
--provider-argv (a codex call) and --home (<launch>/worker/home), runs two consecutive real Codex invocations as the
worker with the same persistent CODEX_HOME <launch>/worker/auth/codex, each first passing the same worker-run login
check as LaunchPreparation.prepare and then prepared by the candidate's own prepare_worker_session (this tool holds no
preparation code), then checks, by a stat run as the worker, that the store's auth.json is a regular worker-owned file
of mode 0600, and that the Founder's ~/.codex/auth.json kept its inode, size and modification time (stat only, never
opened); (c2) runs, as the worker, the context command of a real launch's bounded export
(--package <launch>/exports/<invocation>/context.json), checks it re-prints exactly that package and that the
canonical evidence repository stays unreadable to the worker, and is UNRESOLVED without one, so the proof then does
not pass; (d) mints a landing-scoped installation token as the Founder through the Landing Authority's own
InstallationCredentials only, built from the `github` entry without a WorkRegistry, a readiness store or an evidence
repository, and records that the evidence root's mode is unchanged (partial: the landing path itself waits for row
8's check 17); (e) and (g) use a temporary launch folder and remote under
--scratch, never the registry's own. With --dry-run it only prints the steps and changes nothing.

A pass proves the worker credential boundary only. It does not prove the Factory Director boundary, and it is not
the final protected-main landing authorization. All worker sessions share one Unix user: no confidentiality between
worker sessions is claimed (a credential and authority boundary, not containment).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import tempfile
import threading
import time

WORKER = "alienintent-worker"
STEPS = {
    "a": "as the worker, reading the App key fails; the registry configuration, the work and readiness databases "
         "and the readiness evidence repository (including objects/) are neither readable nor traversable; the "
         "evidence repository's own privacy check still passes as the Founder",
    "b": "as the worker, no gh login, git credential helper, SSH key or token variable; each credential file "
         "unreadable; an installation-token mint fails; sudo -n -l fails",
    "c1": "two consecutive real Codex invocations as the worker, each with a fresh HOME and the same persistent "
          "CODEX_HOME <launch>/worker/auth/codex, both succeed; the store's auth.json is a regular worker-owned 0600 "
          "file; the Founder's ~/.codex/auth.json is never opened and is unchanged",
    "c2": "the context_command returns, from the bounded export only, the real package of a registered, approved "
          "work item, while the canonical evidence repository stays unreadable to the worker",
    "d": "as the Founder, the Landing Authority mints a landing-scoped token through its own InstallationCredentials "
         "only, building no WorkRegistry, readiness store or evidence repository (partial)",
    "e": "a worker-owned repository with planted refs, replace refs, alternates, .git file, commondir, config and "
         "config.worktree does not affect the next import, diff or publication",
    "f": "the worker's session and process group match the sudo pid; cancel leaves no worker process of it",
    "g": "a finished worker's workspace is removed by the normal cleanup through the sudo rule",
}
CREDENTIAL_FILES = (".git-credentials", ".netrc", ".gitconfig", ".config/gh/hosts.yml", ".ssh/id_rsa",
                    ".ssh/id_ed25519", ".codex/auth.json", ".claude/.credentials.json")


def record(step: str, status: str, **facts: object) -> bool:
    print(json.dumps({"check": f"8({step})", "status": status, "claim": STEPS[step], **facts}, sort_keys=True))
    return status == "PASS"


TAIL_LIMIT = 2000


def _tail(data: bytes | str) -> str:
    """The last TAIL_LIMIT characters of a command's output, with token-like text replaced by [REDACTED] (the worker
    diagnostics' own rule). Only diagnostics: a 40- or 64-hex object name stays readable."""
    from alienintent.invocation_runtime.domain.diagnostics import redact
    text = data.decode(errors="replace") if isinstance(data, bytes) else data
    return redact(text)[-TAIL_LIMIT:]


def _guarded(step: str, check, *arguments) -> bool:
    """Run one check; a check that raises is recorded FAIL with its reason, and the proof goes on."""
    try:
        return check(*arguments)
    except Exception as error:  # noqa: BLE001 - recorded, never raised
        return record(step, "FAIL", error=_tail(f"{type(error).__name__}: {error}"))


def as_worker(argv: list[str], environment: dict[str, str] | None = None, **options) -> subprocess.CompletedProcess:
    from alienintent.invocation_runtime.adapters.cli_worker import run_as_worker
    return run_as_worker(WORKER, environment or {"HOME": f"/var/lib/{WORKER}"}, argv, **options)


def _canonical(configuration: Path, project: str) -> list[Path]:
    """The canonical stores no worker may reach, read from the configuration document (parsed only, nothing opened)."""
    from alienintent.composition.work_registry import load_project_configuration
    loaded = load_project_configuration(configuration, project)
    evidence = loaded.readiness.evidence_root
    return [configuration, loaded.database, loaded.readiness.database, evidence, evidence / "objects"]


def _reachable(paths: list[Path]) -> list[str]:
    """The paths the worker can read or traverse: a file's first byte, a folder's listing or a cd into it."""
    probe = ('for p; do if [ -d "$p" ]; then { ls -a -- "$p" || cd -- "$p"; } >/dev/null 2>&1 && echo "$p"; '
             'else head -c1 -- "$p" >/dev/null 2>&1 && echo "$p"; fi; done')
    answer = as_worker(["sh", "-c", probe, "sh", *map(str, paths)])
    return answer.stdout.decode(errors="replace").splitlines()


def _evidence_private(configuration: Path, project: str) -> str | None:
    """LocalEvidenceRepository's own privacy check, as the Founder: None when it passes, else the hold's reason."""
    from alienintent.composition.work_registry import load_project_configuration
    from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
    loaded = load_project_configuration(configuration, project)
    try:
        LocalEvidenceRepository(loaded.readiness.evidence_root, project, "registry")
    except Exception as error:  # noqa: BLE001 - recorded, never raised
        return str(getattr(error, "reason_code", None) or type(error).__name__)
    return None


def check_a(key: Path, configuration: Path, project: str) -> bool:
    key_read = as_worker(["head", "-c1", str(key)])
    reachable = _reachable(_canonical(configuration, project))
    privacy = _evidence_private(configuration, project)
    ok = key_read.returncode != 0 and not reachable and privacy is None
    return record("a", "PASS" if ok else "FAIL", key_read_returncode=key_read.returncode,
                  reachable_by_worker=reachable, evidence_privacy_hold=privacy)


def check_b(key: Path, founder_home: Path) -> bool:
    gh = as_worker(["sh", "-c", "command -v gh >/dev/null && gh auth status"])
    helper = as_worker(["git", "config", "--global", "--get-regexp", "^credential"])
    variables = as_worker(["env"]).stdout.decode(errors="replace")
    tokens = [line.split("=", 1)[0] for line in variables.splitlines()
              if any(word in line.split("=", 1)[0] for word in ("TOKEN", "KEY", "SECRET", "GH_", "GITHUB"))]
    readable = [name for name in CREDENTIAL_FILES
                if (founder_home / name).exists() and as_worker(["head", "-c1", str(founder_home / name)]).returncode == 0]
    mint = as_worker([sys.executable, "-c", "import sys; open(sys.argv[1], 'rb').read()", str(key)])
    sudo = as_worker(["sudo", "-n", "-l"])
    ok = gh.returncode != 0 and helper.returncode != 0 and not tokens and not readable and mint.returncode != 0 \
        and sudo.returncode != 0
    return record("b", "PASS" if ok else "FAIL", gh_returncode=gh.returncode, helper_returncode=helper.returncode,
                  token_variables=tokens, readable_credential_files=readable, mint_returncode=mint.returncode,
                  sudo_list_returncode=sudo.returncode)


def _founder_login(founder_home: Path) -> tuple[int, int, int] | None:
    """The Founder's ~/.codex/auth.json inode, size and modification time, by stat only (never opened)."""
    try:
        facts = os.stat(founder_home / ".codex" / "auth.json")
    except FileNotFoundError:
        return None
    return facts.st_ino, facts.st_size, facts.st_mtime_ns


def check_c1(provider_argv: list[str] | None, home: Path | None, founder_home: Path, configuration: Path,
             project: str) -> bool:
    """Two consecutive real Codex invocations as the worker with the same persistent CODEX_HOME
    `<launch>/worker/auth/codex` (home being `<launch>/worker/home`). Each first passes the same worker-run login
    check as LaunchPreparation.prepare (`worker_login_present`) and is then prepared by the candidate's own
    `prepare_worker_session`; this tool holds no preparation code of its own and never reads or copies a login file."""
    from alienintent.composition import work_registry
    if not provider_argv or home is None:
        return record("c1", "UNRESOLVED", reason="needs --provider-argv and --home (<launch>/worker/home)")
    if not any(Path(word).name == work_registry.WORKER_PROVIDER for word in provider_argv):
        return record("c1", "FAIL", reason="--provider-argv must be a codex call (the one provider with a "
                                           "persistent worker login)")
    loaded = work_registry.load_project_configuration(configuration, project)
    packets = loaded.repositories[loaded.packets_repository].clone
    worker, launch = home.parent, home.parent.parent
    store = worker / "auth" / "codex"
    environment = {"HOME": str(home), "TMPDIR": str(worker / "tmp"), "CODEX_HOME": str(store)}
    founder_before = _founder_login(founder_home)
    invocations: list[dict[str, object]] = []
    for _ in range(2):
        if not work_registry.worker_login_present(WORKER, environment, store):
            return record("c1", "FAIL", reason=f"worker provider login missing: {store}", invocations=invocations)
        work_registry.prepare_worker_session(WORKER, environment, packets, launch / "intake.git")
        session = as_worker(provider_argv, environment, input=b"Reply with the single word OK.\n", timeout=600)
        entry: dict[str, object] = {"returncode": session.returncode}
        if session.returncode:
            entry |= {"stdout_tail": _tail(session.stdout), "stderr_tail": _tail(session.stderr)}
        invocations.append(entry)
    stat = as_worker(["stat", "-c", "%U:%a:%F", "--", str(store / "auth.json")], environment)
    owner, _, rest = stat.stdout.decode(errors="replace").strip().partition(":")
    mode, _, kind = rest.partition(":")
    auth = {"owner": owner, "mode": mode, "type": kind}
    unchanged = _founder_login(founder_home) == founder_before
    ok = all(entry["returncode"] == 0 for entry in invocations) and stat.returncode == 0 \
        and auth == {"owner": WORKER, "mode": "600", "type": "regular file"} and unchanged
    return record("c1", "PASS" if ok else "FAIL", provider=work_registry.WORKER_PROVIDER, codex_home=str(store),
                  invocations=invocations, auth_json=auth, founder_login_unchanged=unchanged)


def check_c2(package: Path | None, home: Path | None, configuration: Path, project: str) -> bool:
    if package is None or not package.is_file() or package.parent.parent.name != "exports":
        return record("c2", "UNRESOLVED", reason="no bounded export of a genuinely registered, approved work item "
                                                 "(--package <launch>/exports/<invocation>/context.json)")
    document = json.loads(package.read_text(encoding="utf-8"))
    command = document["context_command"]
    environment = dict(command["environment"]) | ({"HOME": str(home)} if home else {})
    answer = as_worker(list(command["argv"]), environment)
    try:
        returned = json.loads(answer.stdout)
    except ValueError:
        returned = None
    exported = "--export" in command["argv"] and str(package) in command["argv"] \
        and "--profile-factory" not in command["argv"] \
        and set(command["environment"]) == {"ALIENINTENT_WORK_IDENTITY", "ALIENINTENT_ROLE", "ALIENINTENT_CORRELATION"}
    reachable = _reachable(_canonical(configuration, project))
    ok = answer.returncode == 0 and returned == document and document.get("status") == "PACKAGE" and exported \
        and not reachable
    return record("c2", "PASS" if ok else "FAIL", context_returncode=answer.returncode,
                  identity=document.get("identity"), package_matches=returned == document, export_mode=exported,
                  reachable_by_worker=reachable)


def check_d(configuration: Path, project: str) -> bool:
    """The Landing Authority built over its own InstallationCredentials from the `github` entry alone (the same
    `WorkRegistry._credentials` construction the registry gives it, called without building a WorkRegistry, a
    readiness store or an evidence repository), minting through those credentials only. The evidence root is only
    stat-ed before and after, never opened."""
    from alienintent.composition.landing_authority import LANDING_PERMISSIONS, LandingAuthority
    from alienintent.composition.work_registry import WorkRegistry, load_project_configuration
    from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport
    loaded = load_project_configuration(configuration, project)
    github, evidence = loaded.github, loaded.readiness.evidence_root
    if github is None:
        return record("d", "FAIL", error="no github entry")
    before = os.stat(evidence).st_mode
    authority = LandingAuthority(WorkRegistry._credentials(github, UrllibGitHubTransport(), LANDING_PERMISSIONS),
                                 github.repository, "main", lambda _: None, lambda _: None)
    try:
        token = authority._credentials.token()
    except Exception as error:  # noqa: BLE001 - recorded, never raised
        reason = _tail(f"{type(error).__name__}: {error}")  # the credentials' own message; it never holds a token
        if str(error) == "github answered 422 where 201 was required":
            return record("d", "UNRESOLVED", error=reason, partial=True,
                          reason="the installation does not grant the landing scope (contents: write); this waits "
                                 "for the Founder's App permission decision, which this unit does not make")
        return record("d", "FAIL", error=reason, partial=True)
    unchanged = os.stat(evidence).st_mode == before
    ok = dict(token.permissions) == LANDING_PERMISSIONS and token.repository_selection == "selected" and unchanged
    return record("d", "PASS" if ok else "FAIL", permissions=dict(token.permissions), partial=True,
                  evidence_root_mode_unchanged=unchanged)


def _founder(*argv: str) -> None:
    subprocess.run(list(argv), check=True, capture_output=True)


def _scratch_launch(scratch: Path) -> tuple[Path, Path, Path, str]:
    """A temporary bare remote, a Founder-owned packets clone and a launch folder laid out as the setup lays out the
    real one: worker-owned worker, results and handoff (0711), made as the worker through the sudo rule;
    Founder-owned intake.git, intake-bundles and landing (0700); read and traverse only (access and default) for the
    worker on the packets clone and intake.git; traverse only on launch and on the scratch root."""
    root = Path(tempfile.mkdtemp(prefix="worker-boundary-", dir=scratch))
    _founder("setfacl", "-m", f"u:{WORKER}:--x", str(root))
    remote, packets, launch = root / "remote.git", root / "packets", root / "launch"
    identity = ["-c", "user.name=proof", "-c", "user.email=proof@alienintent.invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(packets)], check=True)
    (packets / "f").write_text("base\n")
    subprocess.run(["git", "-C", str(packets), "add", "f"], check=True)
    subprocess.run(["git", "-C", str(packets), *identity, "commit", "-qm", "base"], check=True)
    subprocess.run(["git", "-C", str(packets), "remote", "add", "origin", str(remote)], check=True)
    subprocess.run(["git", "-C", str(packets), "push", "-q", "origin", "main"], check=True)
    base = subprocess.run(["git", "-C", str(packets), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    launch.mkdir(mode=0o755)
    os.chmod(launch, 0o755)
    # Without root the worker can make its folders only with write on launch, given for this step and then
    # narrowed to traverse only, as the setup leaves it.
    _founder("setfacl", "-m", f"u:{WORKER}:-wx", str(launch))
    try:
        for name in ("worker", "results", "handoff"):
            made = subprocess.run(["sudo", "-n", "-u", WORKER, "--", "env", "-i", "PATH=/usr/bin:/bin", "mkdir",
                                   "-m", "0711", "--", str(launch / name)], capture_output=True, check=False)
            if made.returncode:
                raise OSError(f"the worker cannot make launch/{name}: {made.stderr.decode(errors='replace')}")
    finally:
        _founder("setfacl", "-m", f"u:{WORKER}:--x", str(launch))
    for name in ("intake.git", "intake-bundles", "landing"):
        (launch / name).mkdir(mode=0o700)
        os.chmod(launch / name, 0o700)
    for path in (packets, launch / "intake.git"):
        _founder("setfacl", "-R", "-m", f"u:{WORKER}:r-X", str(path))
        _founder("find", str(path), "-type", "d", "-exec", "setfacl", "-d", "-m", f"u:{WORKER}:r-X", "{}", "+")
    return remote, packets, launch, base


def check_e_g(scratch: Path) -> bool:
    from alienintent.invocation_runtime.adapters import git_source_control, git_worktree
    failures: list[dict[str, object]] = []
    def recorded(run):  # keeps the last failed worker command's return code and bounded, redacted stderr
        def run_and_record(user, environment, argv, **options):
            result = run(user, environment, argv, **options)
            if result.returncode:
                failures[:] = [{"command": " ".join(argv[:2]), "returncode": result.returncode,
                                "stderr_tail": _tail(result.stderr)}]
            return result
        return run_and_record
    for module in (git_worktree, git_source_control):
        if hasattr(module, "run_as_worker"):
            module.run_as_worker = recorded(module.run_as_worker)
    try:
        return _check_e_g(scratch)
    except Exception as error:  # noqa: BLE001 - recorded, never raised
        record("e", "FAIL", error=_tail(f"{type(error).__name__}: {error}"), worker_failure=failures[-1:])
        return record("g", "UNRESOLVED", reason="8(e) did not complete")


def _check_e_g(scratch: Path) -> bool:
    from alienintent.invocation_runtime.adapters.git_source_control import IntakeSourceControl
    from alienintent.invocation_runtime.adapters.git_worktree import WorkerCloneAdapter
    remote, packets, launch, base = _scratch_launch(scratch)
    environment = {"HOME": str(launch / "worker" / "home"), "GIT_AUTHOR_NAME": "w", "GIT_AUTHOR_EMAIL": "w@x.invalid",
                   "GIT_COMMITTER_NAME": "w", "GIT_COMMITTER_EMAIL": "w@x.invalid"}
    workspaces = WorkerCloneAdapter(packets, launch / "worker", launch / "results", WORKER, environment)
    source = IntakeSourceControl(packets, "origin", launch, WORKER, pwd.getpwnam(WORKER).pw_uid, environment,
                                 dict(os.environ), workspaces)
    workspace = workspaces.allocate("proof", "proof", base)
    path = str(workspace.path)
    plant = (f"cd {path} && echo candidate > f && git add f && git commit -qm candidate && "
             f"git update-ref refs/heads/main {base} && mkdir -p .git/refs/replace && "
             f"git rev-parse HEAD > .git/refs/replace/{base} && echo /nonexistent > .git/objects/info/alternates && "
             f"git config remote.origin.url /evil.git && git config url./evil.git.insteadOf {remote} && "
             f"git config core.hooksPath /tmp && printf '[core]\\n\\tfsmonitor = /tmp/x\\n' > .git/config.worktree")
    planted = as_worker(["sh", "-c", plant], environment)
    claimed = source.revision(workspace.path)
    ref = source.hand_over("proof", workspace.path, claimed, base)
    # After the bundle (as the offline test does): a commondir and a .git file pointing elsewhere are planted too.
    as_worker(["sh", "-c", f"cd {path} && echo /nonexistent > .git/commondir && mkdir -p sub && "
                           f"echo 'gitdir: /nonexistent' > sub/.git"], environment)
    candidate = source.publish_intake("proof", "candidate/proof", claimed, launch / "verifier" / "producer-proof")
    published = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/candidate/proof"],
                               capture_output=True, text=True, check=False).stdout.strip()
    intake_refs = subprocess.run(["git", "--git-dir", str(launch / "intake.git"), "for-each-ref",
                                  "--format=%(refname)"], capture_output=True, text=True, check=False).stdout.split()
    ok_e = planted.returncode == 0 and published == claimed and intake_refs == [ref] \
        and candidate.locator.endswith(f"@{claimed}") and not Path("/evil.git").exists()
    passed = record("e", "PASS" if ok_e else "FAIL", claimed=claimed, published=published, intake_refs=intake_refs)
    workspaces.cleanup(workspace, None)
    return record("g", "PASS" if not os.path.lexists(workspace.path) else "FAIL", workspace=path) and passed


def check_f() -> bool:
    from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
    from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership
    from alienintent.invocation_runtime.domain.runtime import InvocationRole
    uid = pwd.getpwnam(WORKER).pw_uid
    ownership = ProcOwnership(worker_uid=uid)
    results = Path(tempfile.mkdtemp(prefix="worker-boundary-results-"))
    provider = CliWorkerProvider("proof", lambda *_: (["sh", "-c", "sleep 60 & sleep 60"], ""), (), "explicit",
                                 frozenset({"wall-clock", "cancellation"}), {"HOME": f"/var/lib/{WORKER}"},
                                 ownership=ownership, worker_user=WORKER, results=results,
                                 regression_base=lambda _: None)
    thread = threading.Thread(target=provider.run, args=("proof-f", InvocationRole.PRODUCER, Path("/"), 120))
    thread.start()
    time.sleep(2)
    process = provider._active.get("proof-f")
    sudo_pid = None if process is None else process.pid
    observed = () if sudo_pid is None else ownership.owned_work("proof-f", None, session=sudo_pid) or ()
    sessions = set()
    for pid in observed:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        sessions.add((int(fields[2]), int(fields[3])))  # (process group, session)
    result = provider.cancel("proof-f", "proof")
    thread.join(30)
    left = () if sudo_pid is None else ownership.owned_work("proof-f", None, session=sudo_pid)
    ok = bool(observed) and sessions == {(sudo_pid, sudo_pid)} and result.quiescent and left == ()
    return record("f", "PASS" if ok else "FAIL", sudo_pid=sudo_pid, observed=list(observed),
                  groups_and_sessions=sorted(sessions), cancel=result.kind, left=left)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--configuration", type=Path, required=True, help="the registry project configuration")
    parser.add_argument("--project", required=True)
    parser.add_argument("--key", type=Path, required=True, help="the factory App's private key file")
    parser.add_argument("--package", type=Path,
                        help="a real launch's bounded export <launch>/exports/<invocation>/context.json")
    parser.add_argument("--provider-argv", help="JSON list: one real codex call run twice as the worker for 8(c1)")
    parser.add_argument("--home", type=Path, help="the worker HOME 8(c1) has prepare_worker_session recreate "
                                                  "(<launch>/worker/home)")
    parser.add_argument("--scratch", type=Path, default=Path(tempfile.gettempdir()),
                        help="where the temporary remote, packets clone and launch folder of 8(e) and 8(g) go")
    parser.add_argument("--dry-run", action="store_true", help="print the steps only")
    arguments = parser.parse_args(argv)
    if arguments.dry_run:
        for step, claim in STEPS.items():
            print(f"8({step}): {claim}")
        print("dry run: nothing run")
        return 0
    founder_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    provider = json.loads(arguments.provider_argv) if arguments.provider_argv else None
    results = [_guarded("a", check_a, arguments.key, arguments.configuration, arguments.project),
               _guarded("b", check_b, arguments.key, founder_home),
               _guarded("c1", check_c1, provider, arguments.home, founder_home, arguments.configuration,
                        arguments.project),
               _guarded("c2", check_c2, arguments.package, arguments.home, arguments.configuration, arguments.project),
               _guarded("d", check_d, arguments.configuration, arguments.project),
               _guarded("e", check_e_g, arguments.scratch), _guarded("f", check_f)]
    print(json.dumps({"claim_boundary": "worker credential boundary only; not the Factory Director boundary; not the "
                                        "protected-main landing authorization; no confidentiality between worker sessions is claimed",
                      "passed": all(results)}))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
