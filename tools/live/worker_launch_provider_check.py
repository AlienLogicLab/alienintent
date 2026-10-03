#!/usr/bin/env python3
"""Unit 6c-2 acceptance check 10: the real-provider check of the registry worker launch.

The Founder runs this in a separate terminal (a provider call nested inside Claude Code hangs). It covers only the
routes the live routing file gives PRODUCER and VERIFIER, read once, read-only; when both resolve to the same route it
runs once, as PRODUCER, and that evidence also counts for the VERIFIER route (the verdict format is covered offline).
Each run goes through `CliWorkerProvider.run` with the registry composition's command callable
(`LaunchPreparation.command`, built at run time with `provider_command`) and `worker_environment`, on isolated data:

- a throwaway local repository and bare remote holding the feature-regression runner files, its own temporary state
  (databases, evidence folder and a virtual environment whose `alienintent` script is this checkout), never the
  permanent work registry;
- a tiny fixed context package, delivered by `LaunchPreparation.deliver` as a launch delivers one;
- a temporary HOME holding only the configured provider's own login files, copied from the login source; no gh or git
  credentials, SSH keys, App key or API key. A missing login file fails the check; the HOME is never widened. The
  temporary HOME is deleted at the end.

It prints one PASS or FAIL line per item of check 10 and writes everything to the output folder (`report.txt`,
`report.json` and one folder per run). Exit status 0 only when every line passes. No permanent record is written.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from alienintent.composition.model_routing import provider_command, resolve_route, routing_path  # noqa: E402
from alienintent.composition.sandbox_run_profile import PROVIDER_DIMENSIONS, worker_environment  # noqa: E402
from alienintent.composition.work_registry import (  # noqa: E402
    WORK_CONTEXT_PROFILE, LaunchPreparation, project_configuration)
from alienintent.context_assembly.adapters.work_item_repository import SQLiteWorkItemRepository  # noqa: E402
from alienintent.context_assembly.application.work_context import ContextCommand  # noqa: E402
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore  # noqa: E402
from alienintent.execution_coordination.domain.custody import CandidateRef  # noqa: E402
from alienintent.execution_coordination.ports.worker_provider import WorkerInvocation  # noqa: E402
from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider  # noqa: E402
from alienintent.invocation_runtime.adapters.git_source_control import GitSourceControl  # noqa: E402
from alienintent.invocation_runtime.adapters.git_worktree import GitWorktreeAdapter  # noqa: E402
from alienintent.invocation_runtime.adapters.process_ownership import ProcOwnership  # noqa: E402
from alienintent.invocation_runtime.application.real_worker import read_verdict  # noqa: E402
from alienintent.invocation_runtime.domain.runtime import VERDICT_PATH, InvocationRole  # noqa: E402

# Each provider's own login files, relative to HOME: the only files the temporary HOME holds.
LOGIN_FILES = {"codex": (".codex/auth.json",), "claude": (".claude/.credentials.json",)}
DEFAULT_OUTPUT = Path.home() / ".local/state/alienintent/manual/worker-launch-real-provider"
PROJECT, REPOSITORY = "AlienLogicLab/worker-launch-check", "worker-launch-check"
IDENTITY = "worker-launch-check-10"  # No work item has this id: the read-only profile answers a named hold.
CONTRACT_DIGEST = "sha256:" + sha256(b"worker-launch-check-10").hexdigest()
VERIFICATION = ("tools/verification/run_feature_regressions.py", "tools/verification/feature_regressions.json")
COMMITTER = ("-c", "user.name=Check 10", "-c", "user.email=check10@alienintent.invalid", "-c", "commit.gpgsign=false")
# Names an API key, token or publication credential would use; none may reach the worker.
CREDENTIAL = re.compile(r"(API_KEY|TOKEN|SECRET|PASSWORD|GIT_CONFIG|SSH_AUTH_SOCK|GH_|GITHUB_)", re.IGNORECASE)


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Report:
    def __init__(self, output: Path) -> None:
        self.output, self.lines = output, []

    def line(self, name: str, passed: bool, detail: str) -> bool:
        self.lines.append({"check": name, "passed": passed, "detail": detail})
        print(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}", flush=True)
        return passed

    def note(self, text: str) -> None:
        self.lines.append({"note": text})
        print(f"NOTE  {text}", flush=True)

    def finish(self) -> int:
        passed = all(entry.get("passed", True) for entry in self.lines) and any("check" in e for e in self.lines)
        verdict = f"CHECK 10: {'PASS' if passed else 'FAIL'}"
        print(verdict, flush=True)
        text = "\n".join(f"{'PASS' if e['passed'] else 'FAIL'}  {e['check']}: {e['detail']}" if "check" in e
                         else f"NOTE  {e['note']}" for e in self.lines)
        (self.output / "report.txt").write_text(text + "\n" + verdict + "\n")
        (self.output / "report.json").write_text(json.dumps({"passed": passed, "lines": self.lines}, indent=1) + "\n")
        return 0 if passed else 1


def installed_checkout(state: Path) -> Path:
    """A virtual environment where this checkout is installed the way an editable install does (a .pth naming its
    `src` and the `alienintent` console script): the executable the package's `context_command` names."""
    venv = state / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True)
    python = venv / "bin" / "python"
    purelib = subprocess.run([python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                             capture_output=True, text=True, check=True, env={}).stdout.strip()
    Path(purelib, "alienintent-checkout.pth").write_text(f"{ROOT / 'src'}\n")
    script = venv / "bin" / "alienintent"
    script.write_text(f"#!{python}\nimport sys\nfrom alienintent.control_plane.adapters.cli import main\n"
                      "sys.exit(main())\n")
    script.chmod(0o755)
    return script


def throwaway_project(state: Path) -> tuple[Path, Path, str]:
    """A local clone and bare remote with a README and the feature-regression runner files on main."""
    remote, clone = state / "remote.git", state / "clone"
    git(state, "init", "-q", "--bare", "-b", "main", str(remote))
    git(state, "init", "-q", "-b", "main", str(clone))
    (clone / "README.md").write_text("Throwaway repository of the unit 6c-2 real-provider check.\n")
    for relative in VERIFICATION:
        (clone / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, clone / relative)
    git(clone, "add", "README.md", *VERIFICATION)
    git(clone, *COMMITTER, "commit", "-qm", "throwaway baseline")
    git(clone, "remote", "add", "origin", str(remote))
    git(clone, "push", "-q", "origin", "main")
    return clone, remote, git(clone, "rev-parse", "HEAD")


def read_only_configuration(state: Path, clone: Path) -> Path:
    """The configuration the read-only worker profile opens: empty work and `readiness` databases of its own."""
    path = state / "project.json"
    document = {"schema_version": 1, "projects": {PROJECT: {
        "database": str(state / "work.sqlite"),
        "repositories": {REPOSITORY: {"clone": str(clone), "remote": "origin", "default_branch": "main",
                                      "packets_branch": "alienintent/work-packets"}},
        "packets": {"repository": REPOSITORY, "directory": "work-packets"},
        "profiles": {"check": str(state / "profile.sqlite")},
        "readiness": {"database": str(state / "readiness.sqlite"), "evidence_root": str(state / "evidence"),
                      "executable": str(state / "agent-ready-not-used"), "provider": "claude"}}}}
    path.write_text(json.dumps(document, indent=1))
    configuration = project_configuration(document, PROJECT)
    SQLiteWorkItemRepository(configuration.database, configuration.repositories)
    SQLiteOperationalStore(state / "readiness.sqlite")
    SQLiteOperationalStore(state / "profile.sqlite")
    (state / "evidence" / "objects").mkdir(parents=True, mode=0o700)
    (state / "evidence").chmod(0o700)  # the evidence repository refuses a folder others can read
    return path


def login_home(provider: str, source: Path, report: Report, role: str) -> Path | None:
    """A temporary HOME holding only `provider`'s own login files; None (a failed line) when one is missing."""
    missing = [relative for relative in LOGIN_FILES[provider] if not (source / relative).is_file()]
    if missing:
        report.line(f"{role} authentication", False, f"login file missing: {', '.join(str(source / m) for m in missing)}"
                    f"; {provider} cannot run with only its own login files here, and the HOME is not widened")
        return None
    home = Path(tempfile.mkdtemp(prefix="alienintent-check10-home-"))
    for relative in LOGIN_FILES[provider]:
        target = home / relative
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        shutil.copyfile(source / relative, target)
        target.chmod(0o600)
    return home


def home_files(home: Path) -> list[str]:
    return sorted(str(path.relative_to(home)) for path in home.rglob("*") if path.is_file())


def run_role(role: str, number: int, route: dict[str, str], state: Path, output: Path, clone: Path, remote: Path,
             baseline: str, command: ContextCommand, source: Path, wall_clock: float, report: Report) -> None:
    invocation_id = f"launch:{IDENTITY}:{number}"
    evidence = output / role.lower()
    evidence.mkdir()
    nonce = uuid.uuid4().hex
    candidate = None
    if role == "PRODUCER":
        workspace = GitWorktreeAdapter(clone, state / "workspaces").allocate(invocation_id, IDENTITY, baseline).path
    else:
        branch = "candidate/check-10"
        git(clone, "checkout", "-q", "-b", branch)
        (clone / "check10.txt").write_text("candidate of the real-provider check\n")
        git(clone, "add", "check10.txt")
        git(clone, *COMMITTER, "commit", "-qm", "check 10 candidate")
        revision = git(clone, "rev-parse", "HEAD")
        git(clone, "push", "-q", "origin", branch)
        git(clone, "checkout", "-q", "main")
        candidate = CandidateRef.source_revision("sha256:" + sha256(revision.encode()).hexdigest(),
                                                 f"git:{remote}#{branch}@{revision}")
        workspace = state / f"verifier-{number}"
        GitSourceControl().retrieve_for_verification(candidate, workspace)
    preparation = LaunchPreparation(None, state / "context", REPOSITORY)  # deliver and command need no records
    answer, nonce_file = state / "context" / f"{invocation_id}.context-answer.json", state / "context" / f"{invocation_id}.nonce"
    steps = [f"1. Run your context_command once and save its standard output, unchanged, to the file {answer}."]
    if role == "PRODUCER":
        steps += ["2. Create the file check10.txt in your working directory containing exactly the value of this "
                  "package's `nonce` field, and commit it with git (message: check 10).",
                  "3. Write a short self-review of your diff to the file the instruction text names."]
    else:
        steps += [f"2. Write exactly the value of this package's `nonce` field to the file {nonce_file}.",
                  "3. Check that the candidate commit adds check10.txt, and write .alienintent/verdict.json as the "
                  "instruction text states (verdict accept if it does)."]
    package = {"status": "PACKAGE", "identity": IDENTITY, "label": "CHECK-10", "role": role, "attempt": number,
               "nonce": nonce, "goal": "Prove the worker launch wiring with one tiny change.",
               "instructions": {"text": "\n".join(steps)}, "starting_revision": baseline,
               "context_command": command.document(IDENTITY, role, invocation_id,
                                                   None if candidate is None else candidate.locator, CONTRACT_DIGEST)}
    invocation = WorkerInvocation(IDENTITY, invocation_id, CONTRACT_DIGEST, role, candidate)
    preparation.deliver(invocation, package, route)
    home = login_home(route["provider"], source, report, role)
    if home is None:
        return
    try:
        listed = home_files(home)
        environment = worker_environment(state) | dict(command.environment) | {"HOME": str(home)}
        (state / "worker-tmp").mkdir(exist_ok=True)
        process = CliWorkerProvider(route["provider"], preparation.command, (), "explicit", PROVIDER_DIMENSIONS,
                                    environment=environment, ownership=ProcOwnership())
        argv, text = preparation.command(invocation_id, InvocationRole(role), workspace)
        (evidence / "argv.json").write_text(json.dumps(argv, indent=1) + "\n")
        (evidence / "instruction-text.txt").write_text(text)
        (evidence / "environment-names.json").write_text(json.dumps(sorted(environment), indent=1) + "\n")
        (evidence / "home-files.json").write_text(json.dumps(listed, indent=1) + "\n")
        print(f"... running the {role} ({route['provider']} {route['model']}) in {workspace}; wall clock {wall_clock}s",
              flush=True)
        try:
            result = process.run(invocation_id, InvocationRole(role), workspace, wall_clock)
        except Exception as error:  # noqa: BLE001 - a launch that cannot start is this check's failure
            report.line(f"{role} provider start", False, f"the run raised {type(error).__name__}: {error}")
            return
        stdout, stderr = process.outputs.get(invocation_id, ("", ""))
        (evidence / "stdout-tail.txt").write_text(stdout)
        (evidence / "stderr-tail.txt").write_text(stderr)
        (evidence / "result.json").write_text(json.dumps({"kind": result.kind, "exit_code": result.exit_status,
                                                          "quiescent": result.quiescent}, indent=1) + "\n")
    finally:
        shutil.rmtree(home, ignore_errors=True)  # the copied login files never stay on disk
    started = result.kind == "success" and result.exit_status == 0
    report.line(f"{role} provider start", started and argv == provider_command(route, workspace),
                f"{result.kind}, exit {result.exit_status}; argv {' '.join(argv[1:])}"
                + ("" if started else f"; stderr tail: {stderr[-600:]!r}"))
    if role == "PRODUCER":
        shown = subprocess.run(["git", "show", "HEAD:check10.txt"], cwd=workspace, capture_output=True, text=True)
        report.line(f"{role} package read", shown.returncode == 0 and shown.stdout.strip() == nonce,
                    "the committed check10.txt holds the package's nonce, which only the package file names"
                    if shown.returncode == 0 and shown.stdout.strip() == nonce else f"check10.txt: {shown.stdout.strip()!r}")
    else:
        found = nonce_file.read_text().strip() if nonce_file.is_file() else None
        report.line(f"{role} package read", found == nonce, f"nonce file {'matches' if found == nonce else repr(found)}")
    try:
        answered = json.loads(answer.read_text())
    except (OSError, ValueError) as error:
        answered = {"unreadable": type(error).__name__}
    shutil.copyfile(answer, evidence / "context-answer.json") if answer.is_file() else None
    named = answered.get("status") == "PACKAGE" or (answered.get("status") == "HOLD" and bool(answered.get("reason")))
    report.line(f"{role} context command", named,
                f"the read-only profile answered {answered.get('status')} {answered.get('reason', '')}".strip()
                if named else f"no package or named hold: {json.dumps(answered)[:300]}")
    if role == "PRODUCER":
        head = git(workspace, "rev-parse", "HEAD")
        on_top = head != baseline and subprocess.run(["git", "merge-base", "--is-ancestor", baseline, head],
                                                     cwd=workspace).returncode == 0
        review = preparation.self_review_path(invocation_id)
        reviewed = review.is_file() and bool(review.read_text().strip())
        if reviewed:
            shutil.copyfile(review, evidence / "self-review.md")
        report.line(f"{role} commit and self-review", on_top and reviewed,
                    f"commit {head[:12]} on top of {baseline[:12]}: {on_top}; self-review file: {reviewed}")
    else:
        verdict = read_verdict(workspace / VERDICT_PATH, candidate)
        report.line(f"{role} verdict", verdict.kind in {"accept", "reject"},
                    f".alienintent/verdict.json read as {verdict.kind}")
    leaked = sorted(name for name in environment if CREDENTIAL.search(name))
    report.line(f"{role} authentication", started and not leaked and listed == sorted(LOGIN_FILES[route["provider"]]),
                f"provider ran with HOME holding only {listed} and no API key or token variable"
                if not leaked else f"credential variables present: {leaked}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=Path, help="a new folder for the output (default: a timestamped folder "
                                                    f"under {DEFAULT_OUTPUT})")
    parser.add_argument("--login-source", type=Path, default=Path.home(),
                        help="the HOME the provider's own login files are copied from (default: your HOME)")
    parser.add_argument("--wall-clock", type=float, default=900, help="seconds each provider run may take")
    args = parser.parse_args(argv)
    output = args.output or DEFAULT_OUTPUT / f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    output.mkdir(parents=True, exist_ok=False)
    report = Report(output)
    print(f"Output folder: {output}", flush=True)
    path = routing_path()
    routes: dict[str, dict[str, str]] = {}
    for role in ("PRODUCER", "VERIFIER"):
        try:
            routes[role] = resolve_route(role, path)
        except (OSError, ValueError, TypeError, AttributeError) as error:
            report.line(f"{role} route", False, f"{path}: {type(error).__name__}: {error}")
    if len(routes) != 2:
        return report.finish()
    (output / "routes.json").write_text(json.dumps({"routing_file": str(path), **routes}, indent=1) + "\n")
    runs = ["PRODUCER"] if routes["PRODUCER"] == routes["VERIFIER"] else ["PRODUCER", "VERIFIER"]
    for role in ("PRODUCER", "VERIFIER"):
        report.note(f"{role} route from {path}: {routes[role]['provider']} {routes[role]['model']} "
                    f"({routes[role]['permissionMode']}, {routes[role]['executable']})")
    if runs == ["PRODUCER"]:
        report.note("PRODUCER and VERIFIER resolve to the same route: one run, as PRODUCER; its evidence also counts "
                    "for the VERIFIER route, and the verdict format is covered offline")
    state = output / "state"
    state.mkdir()
    executable = installed_checkout(state)
    clone, remote, baseline = throwaway_project(state)
    configuration = read_only_configuration(state, clone)
    command = ContextCommand(str(executable), WORK_CONTEXT_PROFILE, {
        "ALIENINTENT_PROJECT_CONFIGURATION": str(configuration.resolve()), "ALIENINTENT_PROJECT": PROJECT})
    for number, role in enumerate(runs):
        run_role(role, number, routes[role], state, output, clone, remote, baseline, command, args.login_source,
                 args.wall_clock, report)
    return report.finish()


if __name__ == "__main__":
    raise SystemExit(main())
