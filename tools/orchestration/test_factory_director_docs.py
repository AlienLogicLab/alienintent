"""FDH-01 criterion 6: the runtime contract, live-proof procedure and episode prompt."""
from pathlib import Path
import json
import re
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from factory_director_host import DirectorInputs, FactoryDirectorHost, InMemoryDirectorLauncher  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/operations/factory-director-runtime-contract.md"
LIVE_PROOF = ROOT / "docs/operations/factory-director-host-live-proof.md"
PROMPT = ROOT / "tools/orchestration/factory-director-episode.md"
TERMINAL_REASONS = ("NO_ELIGIBLE_AUTHORIZED_WORK", "WIP_INTENTIONALLY_FULL", "FOUNDER_DECISION_PENDING",
                    "FACTORY_PAUSED")


@pytest.mark.parametrize("heading", [
    "Role and mission", "Continuous-control invariant", "Terminal conditions and checkpoints",
    "Director continuity fault", "Startup reconstruction procedure", "Authority boundaries",
    "One-owner mutation rule", "Forward-only rules", "Durable state the host reads", "Activation predicate",
    "Replacement-safety rule", "Episode exit"])
def test_runtime_contract_covers_every_scope_3_item(heading):
    assert re.search(rf"^## \d+\. {re.escape(heading)}$", CONTRACT.read_text(), re.MULTILINE), heading


def test_runtime_contract_states_the_invariants_verbatim():
    text = CONTRACT.read_text()
    for phrase in ("maintain flow aggressively; expand scope conservatively",
                   "A model episode never owns the decision",
                   "no conversation history", "DIRECTOR_CONTINUITY_FAULT",
                   "checkpoints, not terminal conditions",
                   "may not disable or retire an operating capability",
                   "One work item → one owner → one mutable workspace",
                   "P0 priority", *TERMINAL_REASONS):
        assert phrase in text, phrase
    assert len(re.findall(r"^\| [1-5] \|", text, re.MULTILINE)) == 5


def test_runtime_contract_documents_every_source_path_and_schema():
    text = CONTRACT.read_text()
    example = json.loads((ROOT / "config/factory-director-host.example.json").read_text())
    for key in ("founderHoldRecord", "pauseFlag", "directorInbox"):
        assert example[key].replace("/home/netmarine", "~") in text, key
    for phrase in ('{"schemaVersion": 1, "holds": [', "processed/<id>.json", "presence only", "`wipLimit`",
                   "paths.stateFile", "project_materialization.py", "AGENT_READY_ASSESSMENT", "**fail closed**"):
        assert phrase in text, phrase
    assert example["wipLimit"] == 1


def test_documented_idle_precedence_is_the_order_the_host_applies(tmp_path):
    section = CONTRACT.read_text().split("**Idle-reason precedence**", 1)[1]
    documented = re.findall(r"^\d\. `([A-Z_]+)`", section, re.MULTILINE)
    base = dict(authoritative_state=True, eligible_authorized_work=True, executable_capacity=True,
                attention_required=False, pending_director_inbox=False, lifecycle_requires_selection=False,
                wip_intentionally_full=False, founder_decision_pending=False, explicit_pause=False)
    layers = [dict(authoritative_state=False), dict(explicit_pause=True), dict(founder_decision_pending=True),
              dict(wip_intentionally_full=True), dict(eligible_authorized_work=False), dict(executable_capacity=False)]
    observed = []
    for index in range(len(layers)):
        values = dict(base)
        for layer in layers[index:]:
            values.update(layer)
        if index == 4:
            values["executable_capacity"] = True
        host = FactoryDirectorHost(tmp_path / str(index), lambda v=values: DirectorInputs(**v),
                                   InMemoryDirectorLauncher())
        observed.append(host.reconcile().reason)
    assert documented == observed


def test_episode_prompt_points_to_the_contract_rather_than_restating_it():
    prompt = PROMPT.read_text()
    assert "docs/operations/factory-director-runtime-contract.md" in prompt
    assert "{{EPISODE_ID}}" in prompt
    assert len(prompt) < 1000
    for restated in (*TERMINAL_REASONS, "Founder-hold", "processed/", "WIP", "SWF-19"):
        assert restated not in prompt, restated


def live_proof_blocks():
    return re.findall(r"```bash\n(.*?)```", LIVE_PROOF.read_text(), re.DOTALL)


def test_live_proof_has_every_one_of_the_twelve_steps_with_commands_and_evidence():
    text = LIVE_PROOF.read_text()
    steps = re.findall(r"^### (\d+)\. (.+)$", text, re.MULTILINE)
    assert [int(number) for number, _ in steps] == list(range(1, 13))
    for number, _ in steps:
        body = text.split(f"### {number}. ", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
        assert "```bash" in body and "Evidence:" in body, number
    for required in ("does not authorize this proof", "Nothing is\nretired", "replacement-safety", "PAUSE", "SHA256SUMS", "HOLD"):
        assert required in text, required


@pytest.mark.parametrize("index", range(len(live_proof_blocks())))
def test_every_live_proof_command_block_is_valid_bash(index):
    block = live_proof_blocks()[index].replace("<issue>", "1").replace("<new-state>", "READY") \
        .replace("<state-after-B>", "READY").replace("<FDH-01-landed-sha>", "HEAD")
    result = subprocess.run(["bash", "-n"], input=block, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr


def test_live_proof_names_only_files_that_exist_or_are_installed():
    text = LIVE_PROOF.read_text()
    for relative in set(re.findall(r"(?<![\w./-])(?:tools|docs|config)/[\w./-]+\.(?:py|sh|md|json)", text)):
        assert (ROOT / relative).exists(), relative
    installer = (ROOT / "tools/orchestration/install_factory_director_host.sh").read_text()
    for installed in set(re.findall(r"factory-director-host/([\w.-]+\.(?:py|md))", text)):
        assert installed in installer, installed


def test_installer_the_procedure_calls_directly_is_committed_executable():
    staged = subprocess.run(["git", "ls-files", "-s", "tools/orchestration/install_factory_director_host.sh"],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert staged.startswith("100755 "), staged


def test_live_proof_commands_survive_errexit_where_a_nonzero_status_is_expected():
    for block in live_proof_blocks():
        for line in block.splitlines():
            if re.match(r"\s*diff ", line):
                assert line.rstrip().endswith("|| true"), line
    text = LIVE_PROOF.read_text()
    assert "set -euo" not in text and "set -e\n" not in text  # errexit would close the operator's shell
    step_one = text.split("### 1. ", 1)[1].split("### 2. ", 1)[0]
    assert "wait_for " in step_one and "sleep 5\ncp" not in step_one


def test_live_proof_wait_helpers_run_against_a_real_history_file(tmp_path):
    setup = live_proof_blocks()[0]
    helpers = setup[setup.index("wait_for() {"):setup.index("export REPO=")]
    history = tmp_path / "history.jsonl"
    history.write_text(json.dumps({"reason": "DIRECTOR_EPISODE_EXITED", "episode_id": "a", "exit_reason": "EXIT_0"})
                       + "\n" + json.dumps({"reason": "NO_ELIGIBLE_AUTHORIZED_WORK", "episode_id": None}) + "\n")
    script = (f"set -uo pipefail\nPROOF={tmp_path}\nHOST_STATE={tmp_path}\n{helpers}\n"
              "seq() { echo 1; }; sleep() { :; }\n"
              "exited a | jq -r .exit_reason\n"
              "wait_for 'exit of a' exited a && echo found-a\n"
              "wait_for 'exit of b' exited b || echo missing-b\n")
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True)
    assert result.stdout.split() == ["EXIT_0", "found-a", "HOLD:", "timed", "out", "waiting", "for", "exit",
                                     "of", "b", "missing-b"], result.stderr
    assert (tmp_path / "HOLDS.txt").read_text() == "HOLD: timed out waiting for exit of b\n"
