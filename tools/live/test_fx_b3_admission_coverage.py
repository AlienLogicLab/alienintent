"""FX-B3 pre-execution coverage probe (WO-220506): pins the observed canonical-call-site behaviour.

These assertions record the coverage finding returned to the scope owner; they are not an
acceptance of that behaviour. If the canonical admission gains the missing coverage, the
probe's expectations become reachable and these assertions must be superseded under the
authority that owns release admission, not weakened here.
"""
from pathlib import Path
import sys

sys.path[:0] = [str(Path(__file__).resolve().parent)]

import fx_b3_admission_coverage as probe  # noqa: E402


def _cases():
    return {case["case"]: case for case in _run()}


def _run():
    import json, io, contextlib
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = probe.main([])
    record = json.loads(buffer.getvalue())
    assert status == (0 if record["all_match"] else 1)
    assert record["label"].startswith("LOCAL_FX_L1_EQUIVALENT")
    return record["cases"]


def test_reachable_refusals_launch_zero_actors():
    cases = _cases()
    assert cases["fxb3-2-positive-control"]["observed_worker_starts"] == 1
    assert cases["fxb3-3-identity-replay"]["observed_worker_starts"] == 1
    for name in ("fxb3-4-policy-source-mismatch", "fxb3-5-readiness-digest-mismatch", "fxb3-7-missing-capability"):
        assert cases[name]["observed_worker_starts"] == 0
        assert cases[name]["recorded_correlation"] == "release"
    for name in ("fxb3-6-unsatisfied-dependency", "eligibility-not-released"):
        assert cases[name]["observed_worker_starts"] == 0
        assert cases[name]["observed_guard"].startswith("not selected")


def test_coverage_gaps_are_observed_not_hidden():
    cases = _cases()
    gaps = [name for name, case in cases.items() if not case["matches_expected"]]
    assert gaps == [
        "fxb3-8-missing-budget-dimension",
        "dag-b3-p1-p2-no-release-record-no-named-baseline",
        "dag-b3-p3-p4-baseline-unresolvable",
        "dag-b3-p5-unsuperseded-denial-wording",
    ]
    assert all(cases[name]["observed_worker_starts"] == 1 for name in gaps)
