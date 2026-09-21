#!/usr/bin/env python3
"""PY-10 proven-red matrix — remove each guard and observe its proof fail.

SWF-24: a check that cannot fail is not evidence. SWF-23 §4b step 2: coverage
of a changed path must be able to go red when that path breaks. For every guard
PY-10 adds — and for every PY-09B or PY-06 path PY-10 changed — this harness
copies the tree, breaks exactly that path, runs the test that names it, and
requires the test to go red. A guard whose test still passes without it is
reported as a failure of this harness, not as a success.

    python3 tools/live/py10_proven_red.py           # human readable
    python3 tools/live/py10_proven_red.py --json    # retained evidence

Nothing here touches the working tree: every mutation is applied to a copy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
COPIED = ("src", "tests", "tools", "pyproject.toml")
SUITE = "tests/composition/test_sandbox_run_profile.py"

# guard name -> (file, exact source to break, replacement, test that must go red)
GUARDS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "upstream_descriptor_completeness",
        "src/alienintent/composition/sandbox_run_profile.py",
        '    if not identity or not contract_path or not digest:\n        raise BacklogRejected("Project item does not carry a complete BIU descriptor")\n',
        "",
        f"{SUITE}::test_an_incomplete_upstream_descriptor_is_refused",
    ),
    (
        "contract_document_field_closure",
        "src/alienintent/composition/sandbox_run_profile.py",
        '    unknown = sorted(set(document) - set(_CONTRACT_FIELDS) - {"task", "notes"})\n    if unknown:\n        raise BacklogRejected(f"BIU contract document carries an unknown field: {unknown[0]}")\n',
        "",
        f"{SUITE}::test_a_contract_document_carrying_an_unknown_field_is_refused",
    ),
    (
        "ready_entry_time_is_the_fifo_key",
        "src/alienintent/composition/sandbox_run_profile.py",
        '        observed.sort(key=lambda item: (item.status_updated_at or "", item.item_id))\n',
        "",
        f"{SUITE}::test_equal_priority_work_is_ordered_by_the_moment_its_status_became_ready",
    ),
    (
        "status_change_time_is_observed_upstream",
        "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
        "ProjectV2ItemFieldSingleSelectValue { name updatedAt field",
        "ProjectV2ItemFieldSingleSelectValue { name field",
        f"{SUITE}::test_the_project_query_asks_for_everything_the_live_snapshot_depends_on",
    ),
    (
        "upstream_descriptor_is_observed_upstream",
        "src/alienintent/execution_coordination/adapters/github_projects_v2.py",
        "... on DraftIssue { id title body }",
        "... on DraftIssue { id }",
        f"{SUITE}::test_the_project_query_asks_for_everything_the_live_snapshot_depends_on",
    ),
    (
        "contract_names_the_imported_work_item",
        "src/alienintent/composition/sandbox_run_profile.py",
        '        if contract.identity != identity:\n            raise BacklogRejected("BIU contract document does not name the imported work item")\n',
        "",
        f"{SUITE}::test_a_contract_document_naming_other_work_is_refused",
    ),
    (
        "upstream_and_contract_dependencies_agree",
        "src/alienintent/composition/sandbox_run_profile.py",
        '        if tuple(contract.dependencies) != tuple(row.get("dependencies") or ()):\n            raise BacklogRejected("upstream dependency edges disagree with the BIU contract")\n',
        "",
        f"{SUITE}::test_dependency_edges_that_disagree_with_the_contract_are_refused",
    ),
    (
        "per_item_contract_resolution",
        "src/alienintent/execution_coordination/adapters/github_work_management.py",
        "        resolved = self._contract(row)\n",
        "        resolved = self._contract({**row, \"contract\": \"biu/SB-01.json\", \"identity\": \"SB-01\"})\n",
        f"{SUITE}::test_each_imported_item_carries_its_own_contract",
    ),
    (
        "readiness_digest_matches_the_contract",
        "src/alienintent/execution_coordination/domain/release.py",
        '    if request.readiness_digest != request.contract.content_digest:\n        raise ValueError("stale readiness reference")\n',
        "",
        f"{SUITE}::test_a_readiness_digest_that_no_longer_matches_the_contract_refuses_release",
    ),
    (
        "projection_targets_the_imported_item",
        "src/alienintent/composition/sandbox_run_profile.py",
        "        item = self.item_ids.get(identity)\n",
        "        item = self.item_ids.get(identity) or identity\n",
        f"{SUITE}::test_projecting_work_no_live_item_is_bound_to_is_refused",
    ),
    (
        "decision_request_is_read_back",
        "src/alienintent/composition/sandbox_run_profile.py",
        '        if observed.item_id != item or observed.title != title:\n            return DeliveryHealth(False, "decision notification projection unconfirmed")\n',
        "",
        f"{SUITE}::test_a_decision_request_the_project_answers_differently_is_not_reported_delivered",
    ),
    (
        "repository_file_answer_names_the_requested_path",
        "src/alienintent/execution_coordination/adapters/github_repository_api.py",
        '        if document.get("path") != path or document.get("type") != "file":\n            raise RepositoryRejected("observed content is not the requested repository file")\n',
        "",
        f"{SUITE}::test_a_repository_file_answer_naming_another_path_is_refused",
    ),
    (
        "correlation_becomes_a_valid_refname",
        "src/alienintent/invocation_runtime/adapters/git_worktree.py",
        '        branch = f"invocation/{ref_safe(invocation_id)}"',
        '        branch = f"invocation/{invocation_id}"',
        f"{SUITE}::test_a_coordinator_correlation_becomes_a_branch_git_accepts",
    ),
    (
        "one_candidate_branch_per_invocation",
        "src/alienintent/invocation_runtime/application/real_worker.py",
        "        return self._branch(invocation) if callable(self._branch) else self._branch",
        '        return "candidate/shared"',
        f"{SUITE}::test_successive_invocations_publish_to_their_own_branches_and_read_back_separately",
    ),
    (
        "one_read_back_workspace_per_invocation",
        "src/alienintent/invocation_runtime/application/real_worker.py",
        '        return self._verifier_root / f"producer-{invocation.correlation_id}"',
        "        return self._verifier_root",
        f"{SUITE}::test_successive_invocations_publish_to_their_own_branches_and_read_back_separately",
    ),
    (
        "one_capability_grant_per_invocation",
        "src/alienintent/invocation_runtime/application/real_worker.py",
        "        return self._grant(invocation) if callable(self._grant) else self._grant",
        '        return self._grant(WorkerInvocation(invocation.work_identity, "fixed-grant")) if callable(self._grant) else self._grant',
        f"{SUITE}::test_the_profile_drains_a_prioritised_backlog_with_a_dependency_and_an_escalation",
    ),
    (
        "worker_is_told_its_invocation",
        "src/alienintent/invocation_runtime/adapters/cli_worker.py",
        '        return self._environment | {"ALIENINTENT_INVOCATION_ID": invocation_id, "ALIENINTENT_ROLE": str(role)}',
        "        return dict(self._environment)",
        f"{SUITE}::test_the_worker_is_told_which_invocation_it_is_and_inherits_no_publication_credential",
    ),
    (
        "worker_environment_is_stated_not_inherited",
        "src/alienintent/composition/sandbox_run_profile.py",
        '    inherited = {name: os.environ[name] for name in ("PATH", "HOME", "LANG", "LC_ALL", "TERM", "SHELL", "USER") if name in os.environ}',
        "    inherited = dict(os.environ)",
        f"{SUITE}::test_the_stated_worker_environment_excludes_the_control_plane_credential",
    ),
    (
        "autonomous_start_is_gated_on_doctor",
        "src/alienintent/composition/sandbox_run_profile.py",
        "        return isinstance(self.doctor, InstallationDoctor) and self.doctor.run().ready",
        "        return True",
        f"{SUITE}::test_autonomous_start_is_gated_on_the_live_doctor",
    ),
    (
        "custody_is_rechecked_before_verify",
        "src/alienintent/execution_coordination/application/local_artifact_custody.py",
        "    advertised = subprocess.run([\"git\", \"ls-remote\", remote, f\"refs/heads/{branch}\"], check=False, capture_output=True, text=True)\n    if advertised.returncode or advertised.stdout.split()[:1] != [revision]:\n        raise CandidateUnavailable(\"candidate revision is not published at the requested branch\")\n",
        "",
        "tests/invocation_runtime/test_runtime.py::test_control_plane_rejects_reachable_remote_without_the_exact_advertised_revision",
    ),
    (
        "a_dependency_gates_its_dependent",
        "src/alienintent/execution_coordination/application/factory_coordinator.py",
        "        return (self._is_automatic(item) or self._is_released(item.identity)) and all(self._is_done(dep) for dep in item.dependencies)",
        "        return self._is_automatic(item) or self._is_released(item.identity)",
        f"{SUITE}::test_the_profile_drains_a_prioritised_backlog_with_a_dependency_and_an_escalation",
    ),
    (
        "a_lost_effect_is_parked_not_repeated",
        "src/alienintent/execution_coordination/application/factory_coordinator.py",
        "            outcome = self._worker.read_back(WorkerInvocation(identity, reservation.owner))\n            if outcome is None:\n                if not self._park_unknown_effect(item, reservation):\n                    return False\n                continue\n",
        "            outcome = self._worker.read_back(WorkerInvocation(identity, reservation.owner))\n            if outcome is None:\n                self._store.release(self._profile, reservation.scope, reservation.key, reservation.owner, reservation.fence)\n                continue\n",
        f"{SUITE}::test_a_crash_mid_dispatch_parks_the_unknown_effect_rather_than_re_executing_it",
    ),
)


def _prepare(scratch: Path) -> Path:
    tree = scratch / "tree"
    tree.mkdir()
    for name in COPIED:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, tree / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
        else:
            shutil.copy2(source, tree / name)
    return tree


def run() -> list[dict]:
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="py10-proven-red-") as scratch_name:
        tree = _prepare(Path(scratch_name))
        originals = {path: (tree / path).read_text() for _, path, _, _, _ in GUARDS}
        for guard, path, removed, replacement, test in GUARDS:
            target = tree / path
            original = originals[path]
            if removed not in original:
                results.append({"check": guard, "ok": False, "detail": f"guard source not found in {path}; the matrix is stale"})
                continue
            intact = _pytest(tree, test)
            target.write_text(original.replace(removed, replacement, 1))
            broken = _pytest(tree, test)
            target.write_text(original)
            results.append({
                "check": guard,
                "ok": intact.returncode == 0 and broken.returncode != 0,
                "detail": (
                    f"{test.rsplit('::', 1)[1]}: exit {intact.returncode} with the guard, "
                    f"exit {broken.returncode} with it broken in {path.rsplit('/', 1)[1]}"
                    + (" (124: the broken path never terminated inside the bound)" if broken.returncode == 124 else "")
                ),
            })
    return results


PER_TEST_TIMEOUT_SECONDS = 120


def _pytest(tree: Path, test: str) -> subprocess.CompletedProcess[str]:
    """Run one test under an external wall-clock bound.

    Some guards, once broken, do not make the drain fail — they make it never
    finish. The coordinator has no terminal handling for a non-success worker
    outcome, so a break that turns every dispatch `ineligible` re-dispatches
    the same item forever. A timeout is therefore a red result, not a harness
    error: the test did not pass.
    """
    try:
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test],
            cwd=tree, capture_output=True, text=True, check=False, timeout=PER_TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess([], returncode=124, stdout="", stderr=f"exceeded {PER_TEST_TIMEOUT_SECONDS}s")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="PY-10 proven-red matrix")
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args(argv)

    results = run()
    failed = [result for result in results if not result["ok"]]
    if arguments.json:
        print(json.dumps({"ok": not failed, "checks": results}, indent=1))
    else:
        for result in results:
            print(f"{'PASS' if result['ok'] else 'FAIL'}  {result['check']}\n      {result['detail']}")
        print(f"\n{len(results) - len(failed)}/{len(results)} guards proven red" + ("" if not failed else f" — {len(failed)} NOT PROVEN"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
