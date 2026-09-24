"""Independent read-only candidate probes; all mutations use disposable fixture state."""
from tests.evidence_learning.test_proof_planning import (
    ProofPlanningTests, REQUIREMENT, PROFILE, JUDGMENT, PlanHold, ProofPlan)

def remove_judgment(mapping):
    mapping['predicates'] = [p for p in mapping['predicates']
                             if p['predicate_key'] != 'mapping-faithfulness-judgment']

for mode in ('intact', 'structured-empty-history', 'restored', 'first-derivation'):
    fixture = ProofPlanningTests()
    fixture.setUp()
    try:
        if mode != 'first-derivation':
            before = fixture.derive()
            assert isinstance(before, ProofPlan) and before.obligation(JUDGMENT)
            proofs = fixture.profile().proofs
            version, original = proofs.read(REQUIREMENT)
            if mode == 'structured-empty-history':
                erased = dict(original, history=[], plan_ref=None, plan_digest=None)
                proofs.store.commit(PROFILE, proofs.aggregate(REQUIREMENT), version, erased)
                print(mode, 'current_after_erasure=', proofs.current(REQUIREMENT))
        fixture.remap(remove_judgment)
        result = fixture.derive()
        print(mode, type(result).__name__, getattr(result, 'reason_code', ''),
              'prior=', getattr(result, 'prior_plan_digest', None),
              'judgment_present=', bool(result.obligation(JUDGMENT)) if isinstance(result, ProofPlan) else 'N/A')
        if mode in ('intact', 'restored'):
            assert isinstance(result, PlanHold) and result.reason_code == 'PRIOR_OBLIGATION_DROPPED'
        else:
            assert isinstance(result, ProofPlan) and result.obligation(JUDGMENT) is None
    finally:
        fixture.doCleanups()
