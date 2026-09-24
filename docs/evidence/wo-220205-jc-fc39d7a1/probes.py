from copy import deepcopy
import json
from tests.context_assembly.test_design_admission import DesignAdmissionTests, contract, review, KEY, PROFILE
from alienintent.context_assembly.domain.design_admission import ReviewAdmitted, ReviewRefused, Stale

case = DesignAdmissionTests()
case.setUp()
try:
    profile = case.profile(name="replay")
    report = profile.design.inspect(contract(), 0)
    old_review = review(report)
    assert isinstance(profile.design.record_review(KEY, old_review, 1), ReviewAdmitted)
    moved = {**deepcopy(report.vector), "requirements": {KEY: "sha256:" + "b" * 64}}
    assert isinstance(profile.design.check(KEY, moved), Stale)
    assert not profile.design_readiness.admit(KEY, report.vector).admitted
    reinspection = profile.design.inspect(contract(), 3)
    replay = profile.design.record_review(KEY, deepcopy(old_review), 4)
    print(json.dumps({"probe": "stale-review-after-reinspection", "same_report_digest": report.digest == reinspection.digest,
        "replayed_result": type(replay).__name__, "ready": profile.design_readiness.admit(KEY, report.vector).admitted,
        "history": [e for e, _ in profile.design.history(KEY)]}), flush=True)

    profile = case.profile(name="empty")
    doc = contract()
    doc["fields"]["security"] = {"value": []}
    empty = profile.design.inspect(doc, 0)
    print(json.dumps({"probe": "empty-required-field", "status": empty.status, "holds": [h.reason_code for h in empty.holds]}), flush=True)
finally:
    case.doCleanups()
