#!/usr/bin/env python3
"""FX-B4 citation integrity check (WO-220507, B4 successor program mailbox path proof).

FX-B4 discharges B4 through its alternative-discharge clause by citing retained programme
records; nothing is re-executed against an operational target and no mailbox is built. This
script re-checks only what the citations depend on: the message-duty records in
program-state.json, the messages directory, the Director closure addendum and its commit
ancestry, a re-evaluation of ProgramState.terminal_state() with the code and state of the
closure commit, and the DAG/requirements/contract/ledger text cited as authority. It reads
git objects only and never writes outside --output. Run from the repository root.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = "docs/operations/post-wave1-program"
STATE = f"{PROGRAM}/program-state.json"
REPORT = f"{PROGRAM}/reports/FINAL-REPORT.md"
DIRECTOR = "tools/orchestration/director.py"
CLOSURE = "352fa9d7fce76b661ca98bebca0adec7a00a13df"  # PROGRAM_COMPLETE, landed and remotely verified
ADDENDUM = "89389fd21bd1d3e388730f90cddec6e95a2eacc6"  # adds the Director closure addendum; parent is CLOSURE
ADDENDUM_HEADING = "## Director closure addendum"
MESSAGE_TASKS = ("POSTW1-BRIDGE-000", "POSTW1-LEARN-002")
MESSAGE_FILES = ["POSTW1-BRIDGE-000-request.md", "POSTW1-LEARN-002-review-request.md"]
# First materialized Wave 2 BIU Issue, read from the GitHub API on 2026-09-27:
# https://github.com/AlienLogicLab/alienintent/issues/69 (WO-220101), created_at below.
FIRST_WAVE2_BIU_ISSUE_CREATED = "2026-09-22T11:04:25Z"
TEXT_CITATIONS = (
    ("dag_r2_title_in_technical_plan", "docs/evidence/wave2-technical-plan.md", 120,
     "| R2 | Replacement gate: Program Director mailbox bridge waiter | R1, B4 |"),
    ("bootstrap_m13_reject", "docs/evidence/wave2-specified-requirements.md", 63,
     "| BOOTSTRAP-M13 | No | Program Director mailbox bridge waiter replacement: REJECT as permanent product requirement"),
    ("bootstrap_m17_reject", "docs/evidence/wave2-specified-requirements.md", 67,
     "| BOOTSTRAP-M17 | No | Local Program Director bootstrap orchestration role replacement: REJECT permanent productization"),
    ("runtime_contract_no_competing_role", "docs/operations/factory-director-runtime-contract.md", 15,
     "Do not create a competing role such as Program Director, resident coordinator or"),
    ("task_ledger_bridge_000", f"{PROGRAM}/task-ledger.md", 29,
     "| POSTW1-BRIDGE-000 | 0 | DONE | MEDIUM | claude-bootstrap-coordinator | PASS |"),
    ("task_ledger_learn_002", f"{PROGRAM}/task-ledger.md", 40,
     "| POSTW1-LEARN-002 | 2 | DONE | MEDIUM | codex-fresh | PASS |"),
)
ADDENDUM_CLAIMS = (
    "**Amendment §15 completion conditions, as of `352fa9d7fce76b661ca98bebca0adec7a00a13df`:**",
    "6. Repository changes landed and remotely verified — `352fa9d7` pushed to `origin/main`",
    "7. No temporary worktree or task left without a durable disposition",
    "8. Terminal state — **`PROGRAM_COMPLETE`**, computed by `ProgramState.terminal_state()`",
)
# Packet acceptance.bounded_commands[2], as amended at 240f7b25ffe9b44962caf5299364b32e6e826510.
PACKET_JQ = '.tasks["POSTW1-BRIDGE-000"], .tasks["POSTW1-LEARN-002"]'
DECISION_RECORD = "docs/decisions/2026-09-26-wave2-bounded-operational-authority-delegation.md"


def run(command):
    done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {"command": command, "exit_status": done.returncode,
            "stdout_sha256": "sha256:" + sha256(done.stdout.encode()).hexdigest(),
            "stdout": done.stdout}


def check(checks, name, expected, observed, **detail):
    checks.append({"check": name, "expected": expected, "observed": observed,
                   "result": "PASS" if expected == observed else "FAIL", **detail})


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout


def show(rev, path):
    """File text at `rev`; empty when the path is absent there, so dependent checks FAIL."""
    done = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else ""


def load(rev, path, default):
    text = show(rev, path)
    return json.loads(text) if text else default


def utc(commit):
    seconds = int(git("show", "-s", "--format=%ct", commit))
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def section(text, heading):
    start = text.find(heading)
    if start < 0:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end < 0 else text[start:end]


def terminal_state(rev):
    """Evaluate ProgramState.terminal_state() with the code and the state file of `rev`."""
    source, recorded = show(rev, DIRECTOR), show(rev, STATE)
    if not (source and recorded):
        return {"terminal_state": None, "blocking_founder_decisions": None,
                "founder_decisions_required": None, "task_count": None, "missing_at_revision": True}
    with tempfile.TemporaryDirectory() as tmp:
        code, state = Path(tmp, "director.py"), Path(tmp, "program-state.json")
        code.write_text(source)
        state.write_text(recorded)
        name = f"_fx_b4_director_{rev[:12]}"
        spec = importlib.util.spec_from_file_location(name, code)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module  # dataclass decorators resolve their module here
        spec.loader.exec_module(module)
        program = module.ProgramState(state)
        return {"terminal_state": program.terminal_state(),
                "blocking_founder_decisions": [t["task_id"] for t in program.blocking_founder_decisions()],
                "founder_decisions_required": [t["task_id"] for t in program.founder_decisions_required()],
                "task_count": len(program.tasks())}


def message_refs(state):
    return sorted(t["task_id"] for t in state["tasks"].values()
                  if "/messages/" in (t.get("prompt_path") or "") + json.dumps(t.get("artifact_refs") or []))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="release baseline commit")
    parser.add_argument("--invocation", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    baseline = git("rev-parse", "--verify", args.baseline + "^{commit}").strip()
    checks, observations = [], []

    # Acceptance 1: both programme messages recorded DONE/PASS at the baseline (and at closure).
    for rev, label in ((baseline, "baseline"), (CLOSURE, "closure")):
        tasks = load(rev, STATE, {"tasks": {}})["tasks"]
        for task_id in MESSAGE_TASKS:
            task = tasks.get(task_id) or {}
            check(checks, f"{task_id}_done_pass_at_{label}", {"status": "DONE", "review_status": "PASS"},
                  {"status": task.get("status"), "review_status": task.get("review_status")},
                  revision=rev, path=STATE, command=["jq", f'.tasks["{task_id}"] | {{status, review_status}}', STATE])
    # The packet's bounded jq command (amended at 240f7b2), run literally against the baseline's state file.
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "program-state.json").write_text(show(baseline, STATE))
        done = subprocess.run(["jq", "-c", PACKET_JQ, "program-state.json"], cwd=tmp, capture_output=True, text=True)
    printed = [json.loads(line) for line in done.stdout.splitlines() if line.strip()]
    check(checks, "packet_bounded_jq_command_at_baseline", [0, [{"status": "DONE", "review_status": "PASS"}] * 2],
          [done.returncode, [{k: (t or {}).get(k) for k in ("status", "review_status")} for t in printed]],
          revision=baseline, command=["jq", "-c", PACKET_JQ, STATE])

    listing = run(["git", "ls-tree", "--name-only", f"{baseline}:{PROGRAM}/messages"])
    check(checks, "messages_directory_exactly_two_files_at_baseline", MESSAGE_FILES,
          sorted(listing["stdout"].split()), command=listing["command"], exit_status=listing["exit_status"])
    state_at_baseline = load(baseline, STATE, {"tasks": {}})
    check(checks, "only_bridge_000_task_references_messages_dir_at_baseline", ["POSTW1-BRIDGE-000"],
          message_refs(state_at_baseline), revision=baseline, path=STATE)

    # Acceptance 2 (amended): closure is ancestral; its only child adds the Director closure addendum.
    for name, commit in (("closure", CLOSURE), ("addendum", ADDENDUM)):
        result = run(["git", "merge-base", "--is-ancestor", commit, baseline])
        check(checks, f"{name}_is_ancestor_of_baseline", 0, result["exit_status"], command=result["command"])
    at_closure = run(["git", "show", f"{CLOSURE}:{REPORT}"])
    observations.append({"observation": "packet_bounded_git_show_closure_report", "command": at_closure["command"],
                         "exit_status": at_closure["exit_status"], "stdout_sha256": at_closure["stdout_sha256"],
                         "director_closure_addendum_present": ADDENDUM_HEADING in at_closure["stdout"],
                         "note": "The addendum is not in the closure commit's tree; its only child adds it "
                                 "(packet criterion 2 as amended). Checked below."})
    check(checks, "addendum_commit_parent_is_closure", CLOSURE,
          git("show", "-s", "--format=%P", ADDENDUM).strip(), commit=ADDENDUM)
    children = sorted(line.split()[0] for line in git("rev-list", "--parents", baseline).splitlines()
                      if CLOSURE in line.split()[1:])
    check(checks, "addendum_commit_is_only_child_of_closure_at_baseline", [ADDENDUM], children,
          command=["git", "rev-list", "--parents", baseline], note="children of the closure reachable from the baseline")
    at_addendum = run(["git", "show", f"{ADDENDUM}:{REPORT}"])
    observations.append({"observation": "packet_bounded_git_show_addendum_report", "command": at_addendum["command"],
                         "exit_status": at_addendum["exit_status"], "stdout_sha256": at_addendum["stdout_sha256"],
                         "director_closure_addendum_present": ADDENDUM_HEADING in at_addendum["stdout"]})
    check(checks, "addendum_absent_at_closure_present_at_addendum_commit", [False, True],
          [ADDENDUM_HEADING in at_closure["stdout"], ADDENDUM_HEADING in show(ADDENDUM, REPORT)])
    report_last_change = git("log", "-1", "--format=%H", baseline, "--", REPORT).strip()
    check(checks, "final_report_unchanged_since_addendum_at_baseline", ADDENDUM, report_last_change,
          path=REPORT, baseline_report_sha256="sha256:" + sha256(show(baseline, REPORT).encode()).hexdigest())
    addendum = section(show(baseline, REPORT), ADDENDUM_HEADING)
    check(checks, "addendum_states_cited_conditions", [True] * len(ADDENDUM_CLAIMS),
          [claim in addendum for claim in ADDENDUM_CLAIMS], claims=list(ADDENDUM_CLAIMS),
          addendum_sha256="sha256:" + sha256(addendum.encode()).hexdigest())
    for name, commit in (("closure", CLOSURE), ("addendum", ADDENDUM)):
        committed = utc(commit)
        check(checks, f"{name}_committed_before_first_wave2_biu_issue", True,
              committed < FIRST_WAVE2_BIU_ISSUE_CREATED, commit=commit, committed_utc=committed,
              first_wave2_biu_issue_created_utc=FIRST_WAVE2_BIU_ISSUE_CREATED)

    # The recorded computation, reproduced with the closure commit's own code and state.
    at_close = terminal_state(CLOSURE)
    check(checks, "terminal_state_recomputed_at_closure", {"terminal_state": "PROGRAM_COMPLETE",
          "blocking_founder_decisions": []}, {k: at_close[k] for k in ("terminal_state", "blocking_founder_decisions")},
          revision=CLOSURE, detail=at_close)
    # The same computation at the baseline is recorded, not asserted: the state file gained post-closure tasks.
    at_base = terminal_state(baseline)
    closure_ids = set(load(CLOSURE, STATE, {"tasks": {}})["tasks"])
    added = sorted((t for t in state_at_baseline["tasks"].values() if t["task_id"] not in closure_ids),
                   key=lambda t: t["task_id"])
    observations.append({"observation": "terminal_state_recomputed_at_baseline", "revision": baseline, **at_base,
                         "tasks_added_after_closure": [
                             {k: t.get(k) for k in ("task_id", "phase", "status", "critical_path", "assigned_actor",
                                                    "prompt_path", "created_at")} for t in added]})
    check(checks, "post_closure_tasks_reference_no_message", [],
          [t["task_id"] for t in added if message_refs({"tasks": {t["task_id"]: t}})], count=len(added))
    check(checks, "post_closure_tasks_created_after_addendum", True,
          all(t["created_at"] > utc(ADDENDUM).replace("Z", "+00:00") for t in added),
          addendum_committed_utc=utc(ADDENDUM))

    # Acceptance 3: DAG R2 naming and BOOTSTRAP-M13/M17 dispositions; supporting authority text.
    nodes = {n["id"]: n for n in load(baseline, "docs/evidence/wave2-dependency-dag.json", {"nodes": []})["nodes"]}
    r2, b4 = nodes.get("R2", {}), nodes.get("B4", {})
    check(checks, "dag_r2_node", {"title": "Replacement gate: Program Director mailbox bridge waiter",
                                  "depends_on_includes_b4": True},
          {"title": r2.get("title"), "depends_on_includes_b4": "B4" in r2.get("depends_on", [])},
          path="docs/evidence/wave2-dependency-dag.json")
    check(checks, "dag_b4_node", {"title": "Successor program mailbox path proof", "node_kind": "external_proof_prerequisite",
                                  "proof_fixtures": ["FX-B4"]},
          {k: b4.get(k) for k in ("title", "node_kind", "proof_fixtures")},
          path="docs/evidence/wave2-dependency-dag.json")
    for name, path, line, prefix in TEXT_CITATIONS:
        lines = show(baseline, path).splitlines()
        text = lines[line - 1] if len(lines) >= line else None
        check(checks, name, True, bool(text and text.startswith(prefix)), path=path, line=line, text=text)
    check(checks, "authority_delegation_decision_record_present", True,
          bool(git("ls-tree", "--name-only", baseline, DECISION_RECORD).strip()), path=DECISION_RECORD)

    failed = [c["check"] for c in checks if c["result"] != "PASS"]
    report = {"record_kind": "CitationIntegrityCheck", "schema_version": "1", "fixture_id": "FX-B4",
              "invocation": args.invocation, "baseline": baseline,
              "script": "tools/evidence/fx_b4_evidence.py", "checks": checks, "observations": observations,
              "failed": failed, "exit_status": 1 if failed else 0}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "citation-check.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": len(checks), "failed": failed}))
    return report["exit_status"]


if __name__ == "__main__":
    sys.exit(main())
