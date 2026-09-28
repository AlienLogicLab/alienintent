"""FX-B3P (WO-220611): the canonical call site refuses every failed SWF-21 precondition and an
exhausted attributable budget with zero worker launches, and admits the valid controls with one."""
from pathlib import Path
import contextlib
import io
import json
import sys

sys.path[:0] = [str(Path(__file__).resolve().parent)]

import fx_b3p_release_preconditions as fixture  # noqa: E402


def _cases():
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = fixture.main([])
    record = json.loads(buffer.getvalue())
    assert status == 0 and record["all_match"]
    assert record["label"].startswith("LOCAL_REAL_STACK")
    return {case["case"]: case for case in record["cases"]}


def test_every_failed_precondition_and_exhausted_budget_launches_zero_actors():
    cases = _cases()
    refused = {
        "p1-no-release-record": "implementation-authorized",
        "p1-record-does-not-authorize": "implementation-authorized",
        "p2-no-exact-baseline": "baseline-named",
        "p3-null-baseline": "baseline-resolves",
        "p3-absent-baseline": "baseline-resolves",
        "p4-unreachable-baseline": "baseline-reachable",
        "p5-unsuperseded-denial": "authority-wording-consistent",
        "budget-exhausted": "admit_release",
        "budget-unallocated": "admit_release",
        "budget-dimension-unallocated": "admit_release",
    }
    for name, check in refused.items():
        assert cases[name]["observed_worker_starts"] == 0, name
        assert cases[name]["observed_refused_by"] == check, name
        assert cases[name]["recorded_correlation"] == "release", name


def test_valid_controls_launch_exactly_one_actor():
    cases = _cases()
    for name in ("positive-control", "p5-superseded-denial", "budget-allocated"):
        assert cases[name]["observed_worker_starts"] == 1, name
        assert cases[name]["observed_refused_by"] is None, name


def test_contrast_profiles_without_the_inputs_keep_the_prior_observed_behaviour():
    cases = _cases()
    assert cases["contrast-ungated-no-record"]["observed_worker_starts"] == 1
    assert cases["contrast-unmetered-dimension"]["observed_worker_starts"] == 1
