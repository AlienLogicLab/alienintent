#!/usr/bin/env python3
"""FDH-01 intact/fault/restored discrimination using isolated source copies.

Each control mutates one real line of the candidate adapter or host in a temporary copy,
then runs the named acceptance test three times: intact (must pass), fault (must fail as
a test failure, pytest exit 1) and restored (must pass). Run with PYTHONPATH=src from the repository root.
"""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from alienintent.evidence_learning.adapters.local_evidence_repository import LocalEvidenceRepository
from alienintent.evidence_learning.domain.records import Header, Observation
from alienintent.evidence_learning.domain.refs import Ref

ROOT = Path(__file__).resolve().parents[2]
INVOCATION = "AlienLogicLab/alienintent#89:PRODUCER:27e3cc45-3fb2-4c15-8270-6e7f0ac58238"
BASELINE = "70fa7148939dfcebbcef73d858f9f481869d7214"
CONTRACT = "docs/work-units/wave2/FDH-01.md"
ADAPTER = "tools/orchestration/factory_director_inputs.py"
HOST = "tools/orchestration/factory_director_host.py"
INPUT_TESTS = "tools/orchestration/test_factory_director_inputs.py::"
HOST_TESTS = "tools/orchestration/test_factory_director_host.py::"
FAIL_CLOSED = INPUT_TESTS + "test_malformed_or_unavailable_source_fails_closed"
STATE_READ = '        return validate_runtime_state(_read_json(state_file, "runtime state file"), repository)'
STATE_DEFAULTED = ('        try:\n            raw = json.loads(state_file.read_text())\n'
                   '        except Exception:\n            raw = {"active": {}}\n'
                   '        return validate_runtime_state(raw, repository)')
HOLDS_READ = '        return validate_holds(_read_json(config.founder_hold_record, "Founder-hold record"))'
HOLDS_DEFAULTED = ('        try:\n            return validate_holds(_read_json(config.founder_hold_record, '
                   '"Founder-hold record"))\n        except SourceUnavailable:\n            return {}')

# (control, file, exact original, mutation, pytest node id). Criterion 2 first, one per source fault.
CONTROLS = [
    ("board-read-failure-swallowed", ADAPTER,
     '            raise SourceUnavailable(f"Project board read failed: {exc}"[:300]) from exc',
     '            return {}', FAIL_CLOSED + "[board-incomplete]"),
    ("non-issue-item-ignored", ADAPTER,
     '            raise SourceUnavailable(f"non-Issue item on the Project: {row!r}"[:240])',
     '            continue', FAIL_CLOSED + "[board-non-issue-item]"),
    ("state-file-missing-defaulted", ADAPTER, STATE_READ, STATE_DEFAULTED, FAIL_CLOSED + "[state-file-missing]"),
    ("state-file-unparsable-defaulted", ADAPTER, STATE_READ, STATE_DEFAULTED,
     FAIL_CLOSED + "[state-file-unparsable]"),
    ("hold-record-absent-defaulted", ADAPTER, HOLDS_READ, HOLDS_DEFAULTED, FAIL_CLOSED + "[hold-record-absent]"),
    ("hold-record-unparsable-defaulted", ADAPTER, HOLDS_READ, HOLDS_DEFAULTED,
     FAIL_CLOSED + "[hold-record-unparsable]"),
    ("inbox-absent-defaulted", ADAPTER,
     '        raise SourceUnavailable(f"Director inbox directory is absent: {inbox}")',
     '        return (), frozenset()', FAIL_CLOSED + "[inbox-directory-absent]"),
    # Criterion 3: hold and inbox semantics.
    ("hold-idles-everything", ADAPTER,
     '        founder_decision_pending=bool(held) and not unheld and not attention and not inbox,',
     '        founder_decision_pending=bool(held),',
     INPUT_TESTS + "test_hold_on_some_ready_items_does_not_idle_while_another_ready_item_is_unheld"),
    ("hold-covers-ready-only", ADAPTER,
     '    unheld = {issue: reason for issue, reason in reasons.items() if issue not in holds}',
     '    unheld = {issue: reason for issue, reason in reasons.items()'
     ' if issue not in holds or reason != "eligible:READY"}',
     INPUT_TESTS + "test_held_unclaimed_implement_issue_does_not_make_control_required"),
    ("inbox-receipts-ignored", ADAPTER, '    return tuple(sorted(entries - receipts)), acknowledgements',
     '    return tuple(sorted(entries)), acknowledgements',
     INPUT_TESTS + "test_pending_inbox_entry_launches_despite_holds_and_its_receipt_stops_it"),
    # Criterion 4: continuity with a fresh episode id and lease.
    ("successor-reuses-episode-id", HOST, '        episode_id = f"factory-director-{uuid.uuid4().hex}"',
     '        episode_id = lease["episode_id"] if lease else f"factory-director-{uuid.uuid4().hex}"',
     HOST_TESTS + "test_continuity_a_exits_fresh_b_launches_then_b_exits_and_host_idles"),
    ("full-wip-suppresses-director-control", HOST,
     '        if not values.executable_capacity and not values.director_only_control():',
     '        if not values.executable_capacity:',
     HOST_TESTS + "test_director_only_control_launches_even_when_worker_wip_is_full"),
    # Criterion 5: fresh sessions and isolation.
    ("claude-session-continued", HOST, '            return [self.executable, "-p", "--no-session-persistence",',
     '            return [self.executable, "-p", "--continue",',
     HOST_TESTS + "test_no_command_resumes_or_continues_a_conversation[claude]"),
    ("codex-session-persisted", HOST, '        return [self.executable, "exec", "--ephemeral", "--json",',
     '        return [self.executable, "exec", "resume", "--last", "--json",',
     HOST_TESTS + "test_no_command_resumes_or_continues_a_conversation[codex]"),
    ("isolation-check-disabled", HOST, '        if require_isolated and not self._is_linked_worktree():',
     '        if False:', HOST_TESTS + "test_launcher_refuses_a_workdir_that_is_not_a_linked_worktree"),
    ("provider-model-not-recorded", HOST,
     '        self._record(result, exit_reason=prior_exit, provider=episode.provider, requested_model=episode.model,',
     '        self._record(result, exit_reason=prior_exit, provider=None, requested_model=None,',
     HOST_TESTS + "test_continuity_a_exits_fresh_b_launches_then_b_exits_and_host_idles"),
    # Repairs from independent review 1.
    ("escalation-receipt-ignored", ADAPTER,
     '        if not done and escalation_receipt_id(key, entry) not in acknowledgements:', '        if not done:',
     INPUT_TESTS + "test_escalation_is_resolved_by_a_director_receipt_for_that_exact_escalation"),
    ("assessment-provenance-ignored", ADAPTER,
     '        if not isinstance(author, str) or author.lower() not in operators:', '        if False:',
     INPUT_TESTS + "test_assessment_marker_counts_only_from_an_authorized_operator"),
    ("foreign-repository-item-accepted", ADAPTER, '        if row.get("repository") != materialization.REPO:',
     '        if False:', INPUT_TESTS + "test_other_inconsistent_sources_also_fail_closed[foreign-repository-item]"),
    ("unreadable-pause-means-unpaused", ADAPTER,
     '            raise SourceUnavailable(f"pause flag cannot be checked: {exc}") from exc', '            return False',
     INPUT_TESTS + "test_unreadable_pause_location_fails_closed_rather_than_unpaused"),
    ("crash-loop-guard-removed", HOST, '            if retry and self.clock() < retry:', '            if False:',
     HOST_TESTS + "test_repeated_fast_exits_back_off_instead_of_relaunching_every_second"),
    ("unleased-child-kept", HOST, '            child.kill()\n', '            pass\n',
     HOST_TESTS + "test_pre_bind_launch_failure_kills_the_child_and_does_not_block_later_launches"),
    # Repairs from independent review 2.
    ("done-escalation-still-attention", ADAPTER,
     '        done = repository == materialization.REPO and number.isdigit() and board.get(int(number)) == "DONE"',
     '        done = False', INPUT_TESTS + "test_escalation_for_an_issue_that_reached_done_is_resolved"),
    ("foreign-editor-trusted", ADAPTER,
     '        if editor is not None and (not isinstance(editor, str) or editor.lower() not in operators):',
     '        if False:', INPUT_TESTS + "test_marker_in_an_operator_comment_edited_by_someone_else_is_ignored"),
    ("streak-survives-idle", HOST, '            if idle in IDLE_REASONS:\n                self._reset_failure_streak()',
     '            pass', HOST_TESTS + "test_failure_streak_resets_when_the_factory_goes_idle"),
    ("progress-counted-as-crash", HOST,
     '                  or (runtime < FAST_EXIT_SECONDS and unchanged))', '                  or runtime < FAST_EXIT_SECONDS)',
     HOST_TESTS + "test_short_clean_episodes_that_changed_state_are_not_crashes"),
    ("launch-failure-not-counted", HOST, '                                            "failure_streak": streak + 1,',
     '                                            "failure_streak": 0,', HOST_TESTS + "test_repeated_launch_failures_back_off"),
    ("late-exit-unrecorded", HOST,
     '            # It exited after this reconcile\'s observation: record and count it like any exit.\n            self._observe_exit(values)',
     '            pass', HOST_TESTS + "test_an_exit_between_observation_and_lease_check_is_still_recorded_and_counted"),
    # Repairs from independent review 3.
    ("projection-used-as-progress", HOST,
     '        return published if published is not None else json.dumps(asdict(values), sort_keys=True)',
     '        return json.dumps(asdict(values), sort_keys=True)',
     HOST_TESTS + "test_short_episodes_that_advance_durable_state_under_the_same_projection_are_progress"),
    ("brief-idle-cancels-back-off", HOST, '        if retry and self.clock() < retry:\n            return\n', '',
     HOST_TESTS + "test_a_brief_idle_does_not_cancel_a_pending_back_off"),
    ("unknown-editor-trusted", ADAPTER, '        if editor is None and comment.get("lastEditedAt"):', '        if False:',
     INPUT_TESTS + "test_marker_in_an_edited_comment_with_an_unknown_editor_is_ignored"),
    ("permission-mode-unchecked", HOST, '        if permission_mode not in PERMISSION_MODES[provider]:', '        if False:',
     HOST_TESTS + "test_permission_mode_must_belong_to_the_configured_provider[codex-bypassPermissions]"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--invocation", default=INVOCATION)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    repository = LocalEvidenceRepository(args.output / "evidence", "AlienLogicLab/alienintent", "fdh-01")
    contract = ROOT / CONTRACT
    definition_ref = Ref("AlienLogicLab/alienintent", "fdh-01", "FDH-01-contract",
                         "sha256:" + sha256(contract.read_bytes()).hexdigest(), "repository:" + CONTRACT)
    observations = []

    def run(root, name, phase, test, applications):
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        completed = subprocess.run(cmd, cwd=root, env=env, capture_output=True, timeout=120)
        raw = completed.stdout + completed.stderr
        filename = name + "-" + phase + ".log"
        (args.output / filename).write_bytes(raw)
        # pytest exit 1 means tests ran and failed; 2+ (collection or usage errors) is not discrimination.
        expected = "exit 1 with a FAILED test" if phase == "fault" else "exit 0"
        observation = {"schema_version": 1, "fixture": "FDH-01", "control": name, "phase": phase,
                       "command": cmd, "expected": expected, "exit_status": completed.returncode,
                       "raw_output_sha256": sha256(raw).hexdigest(), "raw_output": filename,
                       "application_count": applications}
        logical = name + "/" + phase
        value = json.dumps(observation, sort_keys=True)
        record = Observation(Header("AlienLogicLab/alienintent", "fdh-01", logical, sha256(value.encode()).hexdigest(),
                                    (definition_ref,), "private"), definition_ref, logical,
                             "pytest-real-mutated-copy", (), value, None, "Morty", args.invocation,
                             "sha256:" + sha256(raw).hexdigest())
        observation["observation_ref"] = asdict(repository.put(record))
        observations.append(observation)
        print(name, phase, completed.returncode, flush=True)
        return completed.returncode, raw

    with tempfile.TemporaryDirectory(prefix="fdh-01-") as tmp:
        root = Path(tmp)
        for directory in ("tools/orchestration", "tools/live", "docs/operations", "config"):
            shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns("__pycache__"))
        outcomes = []
        for name, path, old, new, test in CONTROLS:
            target = root / path
            original = target.read_text()
            count = original.count(old)
            if count != 1:
                raise RuntimeError(f"{name}: expected exactly one mutation site, got {count}")
            intact, _ = run(root, name, "intact", test, 0)
            target.write_text(original.replace(old, new))
            fault, raw = run(root, name, "fault", test, count)
            target.write_text(original)
            restored, _ = run(root, name, "restored", test, 0)
            outcomes.append({"control": name, "test": test, "discriminated":
                             intact == 0 and fault == 1 and b"\nFAILED " in raw and restored == 0})
    files = [ROOT / p for p in (ADAPTER, HOST, "tools/orchestration/test_factory_director_inputs.py",
                                "tools/orchestration/test_factory_director_host.py",
                                "tools/orchestration/test_factory_director_docs.py",
                                "docs/operations/factory-director-runtime-contract.md",
                                "docs/operations/factory-director-host-live-proof.md",
                                "tools/orchestration/factory-director-episode.md")]
    report = {"schema_version": 1, "fixture": "FDH-01", "baseline": BASELINE, "invocation": args.invocation,
              "candidate_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "contract_sha256": sha256(contract.read_bytes()).hexdigest(),
              "implementation_files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in files},
              "tokens": None, "cost": None,
              "measurement_reason": "UNKNOWN: invocation billing telemetry unavailable to the worker",
              "controls": outcomes, "observations": observations, "verdict": "independent verifier pending"}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(o["discriminated"] for o in outcomes) else 1


if __name__ == "__main__":
    sys.exit(main())
