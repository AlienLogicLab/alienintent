#!/usr/bin/env python3
"""Seed the PY-10 proof backlog into the sandbox repository and Project.

Scope §2: at least three READY BIUs, two of equal priority, at least one
dependency, and one BIU constructed to raise a genuine `HumanDecisionRequired`.
Seeding a READY backlog is the proof's own setup. AC 14 forbids a human moving
an individual BIU into IMPLEMENT, and nothing here ever writes any status but
READY — the retained record below states every status this tool wrote.

    python3 tools/live/py10_seed_backlog.py --apply            # seed
    python3 tools/live/py10_seed_backlog.py --apply --reset    # clear first, then seed
    python3 tools/live/py10_seed_backlog.py --reset-only       # leave the Project empty

Every identity written to the evidence passes through the redaction boundary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py10_sandbox import (  # noqa: E402
    SEEDS,
    WORKER_PROTOCOL,
    WORKER_RUN,
    Redactor,
    SeedWriter,
    credentialed_git_environment,
    credentials,
    document,
    git,
    seed_body,
    seed_title,
    state_root,
    write_json,
)

from alienintent.composition.sandbox_profile import compose_profile  # noqa: E402
from alienintent.composition.sandbox_run_profile import contract_from_document  # noqa: E402
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory  # noqa: E402
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport  # noqa: E402

READY_SPACING_SECONDS = 2.0
STATUSES_WRITTEN_BY_SEEDING = ("READY",)


def publish_seed_content(record: dict, token: str) -> str:
    """Commit the worker entry point and the BIU contract documents to the sandbox."""
    environment = credentialed_git_environment(record, token)
    repository = str(record["repository"])
    with tempfile.TemporaryDirectory(prefix="py10-seed-") as scratch:
        checkout = Path(scratch) / "checkout"
        git("clone", "--quiet", f"https://github.com/{repository}.git", str(checkout), environment=environment)
        (checkout / "worker").mkdir(exist_ok=True)
        (checkout / "worker" / "run.sh").write_text(WORKER_RUN, encoding="utf-8")
        (checkout / "worker" / "PROTOCOL.md").write_text(WORKER_PROTOCOL, encoding="utf-8")
        (checkout / "biu").mkdir(exist_ok=True)
        for contract_document in SEEDS:
            write_json(checkout / "biu" / f"{contract_document['identity']}.json", contract_document)
        (checkout / "docs").mkdir(exist_ok=True)
        (checkout / "docs" / ".gitkeep").write_text("", encoding="utf-8")
        git("add", "-A", cwd=checkout, environment=environment)
        if git("status", "--porcelain", cwd=checkout, environment=environment).stdout.strip():
            git(
                "-c", "user.name=AlienIntent PY-10 seeding", "-c", "user.email=py10@alienintent.invalid",
                "commit", "--quiet", "-m", "PY-10: seed the live proof backlog",
                cwd=checkout, environment=environment,
            )
            git("push", "--quiet", "origin", "HEAD:refs/heads/main", cwd=checkout, environment=environment)
        return git("rev-parse", "HEAD", cwd=checkout, environment=environment).stdout.strip()


def clear_project(projects: GitHubProjectsV2Directory) -> list[str]:
    return [projects.delete_item(item.item_id) for item in projects.items()]


def seed_project(projects: GitHubProjectsV2Directory, writer: SeedWriter) -> list[dict]:
    """Create one READY item per seeded BIU, in the order the proof requires.

    The equal-priority pair is spaced in real time: Projects v2 records a
    single-select value's change time to the second, and the FIFO key is that
    time, so two items made READY inside the same second would be ordered by
    the deterministic fallback rather than by the fact under test.
    """
    seeded = []
    for index, contract_document in enumerate(SEEDS):
        identity = contract_document["identity"]
        item = projects.add_draft_item(seed_title(contract_document), seed_body(contract_document))
        writer.set_field(item, "Priority", contract_document["task"]["priority"])
        writer.set_field(item, "Status", "READY")
        observed = projects.read_status(item)
        seeded.append({
            "identity": identity, "item": item, "priority": observed.priority, "status": observed.status,
            "ready_since": observed.status_updated_at, "contract": f"biu/{identity}.json",
            "readiness_digest": contract_from_document(contract_document).content_digest,
            "dependencies": list(contract_document["dependencies"]),
            "required_capabilities": list(contract_document["required_capabilities"]),
            "seed_order": index,
        })
        time.sleep(READY_SPACING_SECONDS)
    return seeded


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Seed the PY-10 proof backlog")
    parser.add_argument("--apply", action="store_true", help="create the seeded backlog")
    parser.add_argument("--reset", action="store_true", help="remove every existing Project item first")
    parser.add_argument("--reset-only", action="store_true", help="remove every existing Project item and stop")
    parser.add_argument("--evidence", type=Path, default=None)
    arguments = parser.parse_args(argv)

    record = document()
    redact = Redactor(record)
    profile = compose_profile(record)
    address = profile.project_address()
    transport = UrllibGitHubTransport()
    minted = credentials(record)
    projects = GitHubProjectsV2Directory(address, transport, minted.authorization)
    writer = SeedWriter(address, transport, minted.authorization)

    result: dict[str, object] = {
        "profile": profile.profile, "repository": profile.repository, "project": profile.project_reference,
        "statuses_written_by_seeding": list(STATUSES_WRITTEN_BY_SEEDING),
    }
    if arguments.reset or arguments.reset_only:
        result["removed"] = clear_project(projects)
    if arguments.reset_only:
        print(json.dumps(redact(result), indent=1))
        return 0
    if not arguments.apply:
        parser.error("pass --apply to seed, or --reset-only to clear")

    result["seed_revision"] = publish_seed_content(record, minted.token().value)
    result["seeded"] = seed_project(projects, writer)
    result["addressed"] = sorted(set(projects.addressed) | set(writer.addressed))
    result["recorded_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    write_json(arguments.evidence or (state_root() / "evidence" / "seed.json"), redact(result))
    print(json.dumps(redact(result), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
