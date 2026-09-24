"""Independent JC regression probes. Run from the candidate root with PYTHONPATH=src:."""
from copy import deepcopy
import unittest
from tests.context_assembly.test_design_admission import DesignAdmissionTests, contract, review, KEY
from alienintent.context_assembly.domain.design_admission import ReviewAdmitted, ReviewRefused, Stale

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.fixture = DesignAdmissionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.profile = self.fixture.profile()
        self.report = self.profile.design.inspect(contract(), 0)
        self.old_review = review(self.report)
        self.assertIsInstance(self.profile.design.record_review(KEY, self.old_review, 1), ReviewAdmitted)

    def invalidate_and_reinspect(self):
        moved = {**deepcopy(self.report.vector), "requirements": {KEY: "sha256:" + "b" * 64}}
        self.assertIsInstance(self.profile.design.check(KEY, moved), Stale)
        self.assertFalse(self.profile.design_readiness.admit(KEY, self.report.vector).admitted)
        report = self.profile.design.inspect(contract(), 3)
        self.assertEqual(report.digest, self.report.digest)
        self.assertFalse(self.profile.design_readiness.admit(KEY, report.vector).admitted)
        return report

    def test_old_review_cannot_reverify_invalidated_design(self):
        self.invalidate_and_reinspect()
        result = self.profile.design.record_review(KEY, deepcopy(self.old_review), 4)
        print("old review after invalidation:", type(result).__name__,
              "ready:", self.profile.design_readiness.admit(KEY, self.report.vector).admitted, flush=True)
        self.assertIsInstance(result, ReviewRefused,
                              "A review predating invalidation must not satisfy fresh independent reverification")
        self.assertFalse(self.profile.design_readiness.admit(KEY, self.report.vector).admitted)

    def test_new_independent_invocation_can_reverify(self):
        report = self.invalidate_and_reinspect()
        fresh = review(report, reviewer=("JC", "fresh-reviewer-invocation-2"))
        self.assertIsInstance(self.profile.design.record_review(KEY, fresh, 4), ReviewAdmitted)
        self.assertTrue(self.profile.design_readiness.admit(KEY, report.vector).admitted)

    def test_duplicate_review_without_invalidation_is_idempotent(self):
        self.assertIsInstance(self.profile.design.record_review(KEY, deepcopy(self.old_review), 2), ReviewAdmitted)
        self.assertEqual(len(self.profile.design.history(KEY)), 2)
        self.assertTrue(self.profile.design_readiness.admit(KEY, self.report.vector).admitted)

if __name__ == "__main__":
    unittest.main(defaultTest="FreshnessTests", verbosity=2)
