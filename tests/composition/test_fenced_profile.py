"""Real composed local lane; legacy kernel is not silently adopted."""
from dataclasses import replace

import pytest

from tests.execution_coordination.test_fenced_store import AUTHORITY, PROFILE
from alienintent.execution_coordination.ports.operational_store import ReservationRejected


def test_composed_delivery_and_unknown_reconciliation(tmp_path):
    """Incorrect wiring must not bypass guarded claim or real persisted readback."""
    from alienintent.composition.fenced_profile import FencedProfile
    from alienintent.execution_coordination.ports.fenced_store import GuardVector, ReconciliationPending
    profile = FencedProfile(tmp_path / 'store.sqlite', name=PROFILE, clock=lambda: 100)
    store = profile.store
    store.commit(PROFILE, 'authority', 0, AUTHORITY)
    locks = store.acquire_many(PROFILE, (('lane', 'job'),), 'worker-1')
    vector = GuardVector((('job', 0), ('authority', 1)), 'authority', 1, 'worker-1')
    store.commit_guarded(PROFILE, 'job', 0, vector, locks, {}, 'e1', {'message': 'one'})
    post = replace(vector, versions=(('job', 1), ('authority', 1)))
    assert profile.executor.execute(PROFILE, 'e1', locks, post).effect_id == 'e1'
    with pytest.raises(ReservationRejected):
        profile.executor.execute(PROFILE, 'e1', locks, post)
    vector = post
    store.commit_guarded(PROFILE, 'job', 1, vector, locks, {}, 'e2', {'message': 'two'})
    post = replace(vector, versions=(('job', 2), ('authority', 1)))
    store.claim_guarded(PROFILE, 'e2', locks, post)
    restarted = FencedProfile(store.path, name=PROFILE, clock=lambda: 100)
    assert isinstance(restarted.executor.reconcile(PROFILE, 'e2', locks), ReconciliationPending)
    store.consume_guarded(PROFILE, 'e2', locks, post)
    assert restarted.executor.reconcile(PROFILE, 'e2', locks).effect_id == 'e2'
