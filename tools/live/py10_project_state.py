#!/usr/bin/env python3
"""Read the sandbox Project back after the run, through the shipped adapter.

Scope §4 asks for projection delivery health and final states. Delivery health
as the coordinator computes it lives in the process that raised the escalation,
so the durable form of the same fact is read here from the Project itself: the
lifecycle state each BIU was projected into, and the decision request each
escalation was projected as, both observed from outside the run that wrote them.

    python3 tools/live/py10_project_state.py --evidence <dir>

The adapter used is `GitHubProjectsV2Directory`, so every read is routed through
`ProjectAddress.resolve` and no Project but the configured one is addressed.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))

from py10_sandbox import Redactor, credentials, document, state_root, write_json  # noqa: E402

from alienintent.composition.sandbox_profile import compose_profile  # noqa: E402
from alienintent.composition.sandbox_run_profile import ProjectDecisionNotifier, descriptor_from_body  # noqa: E402
from alienintent.execution_coordination.adapters.github_projects_v2 import GitHubProjectsV2Directory  # noqa: E402
from alienintent.installation.adapters.urllib_github_transport import UrllibGitHubTransport  # noqa: E402


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read the sandbox Project back after the run")
    parser.add_argument("--evidence", type=Path, default=None)
    arguments = parser.parse_args(argv)

    record = document()
    redact = Redactor(record)
    profile = compose_profile(record)
    projects = GitHubProjectsV2Directory(profile.project_address(), UrllibGitHubTransport(), credentials(record).authorization)
    schema = projects.schema()

    work, decisions, other = [], [], []
    for item in projects.items():
        entry = {"item": item.item_id, "title": item.title, "status": item.status,
                 "priority": item.priority, "status_updated_at": item.status_updated_at}
        if str(item.title or "").startswith(ProjectDecisionNotifier.PREFIX):
            decisions.append(entry | {"context": item.body})
            continue
        try:
            entry["biu"] = descriptor_from_body(item.body).identity
            work.append(entry)
        except Exception:  # noqa: BLE001 - anything else is simply not seeded work
            other.append(entry)

    observation = {
        "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project": schema.project_id, "project_number": schema.project_number, "title": schema.title,
        "lifecycle_projections": sorted(work, key=lambda entry: entry.get("biu", "")),
        "decision_request_projections": decisions,
        "other_items": other,
        "addressed": sorted(set(projects.addressed)),
        "definition": "the Project as it stands after the run, read through the same adapter the run projected with; "
                      "the lifecycle state of each BIU and the decision request raised for it are both durable here",
    }
    write_json((arguments.evidence or (state_root() / "evidence")) / "project-final.json", redact(observation))
    print(f"{len(work)} lifecycle projections, {len(decisions)} decision requests, addressed {observation['addressed']}")
    for entry in observation["lifecycle_projections"]:
        print(f"  {entry.get('biu')}  {entry['status']}  priority {entry['priority']}  at {entry['status_updated_at']}")
    for entry in decisions:
        print(f"  {entry['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
