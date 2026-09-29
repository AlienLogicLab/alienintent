"""R6 rejects a formally authorized release when other preconditions are absent."""

import importlib.util
from pathlib import Path


def load_gate():
    path = Path(__file__).with_name("release_admission.py")
    spec = importlib.util.spec_from_file_location("old_release_admission", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_formal_authority_alone_does_not_admit():
    gate = load_gate()
    facts = {
        "status": "READY", "agent_ready": "READY",
        "receipt": {"disposition": "READY", "work_unit_id": "WO-220511", "input_sha256": "b" * 64},
        "work_unit_sha256": "b" * 64, "baseline": "a" * 40, "baseline_resolves": True, "baseline_ancestral": True,
        "body": "", "open_dependencies": [], "active_invocations": [], "held": False,
        "wip_limit": 1, "active_claims_total": 0,
        "priority_reconciliation": {"status": "ALREADY_MATCHED"},
    }
    assert gate.admit(facts) == []
    invalid = facts | {"agent_ready": None}
    assert [failure["check"] for failure in gate.admit(invalid)] == ["agent_ready"]
    assert gate.admit(facts) == []


def test_r6_requires_all_negative_cases_and_zero_invalid_launches():
    import fx_r6_release_gate as r6

    cases = [{"case": name, "expected_worker_starts": 0,
              "observed_worker_starts": 0, "matches_expected": True}
             for name in r6.REQUIRED_NEGATIVE_CASES]
    assert r6.check_cases(cases) == []
    cases[0]["observed_worker_starts"] = 1
    assert r6.check_cases(cases) == [cases[0]["case"]]
    assert r6.check_cases(cases[1:]) == [cases[0]["case"]]
