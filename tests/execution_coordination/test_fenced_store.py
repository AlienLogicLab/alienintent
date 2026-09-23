"""FX-S2: real SQLite admission, ownership, consumer and crash boundaries."""
from dataclasses import replace
from pathlib import Path
import json
import os
import signal
import subprocess
import sys

import pytest

from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.operational_store import ReservationRejected, StaleFence, VersionConflict

PROFILE = 'fx-s2'
AUTHORITY = {'schema_version': 1, 'epoch': 1, 'invocation': 'worker-1', 'active': True, 'expires_at': 200}


def setup_store(path, clock=lambda: 100):
    from alienintent.execution_coordination.ports.fenced_store import GuardVector
    store = SQLiteOperationalStore(path, clock=clock)
    store.commit(PROFILE, 'authority', 0, AUTHORITY)
    store.commit(PROFILE, 'premise', 0, {'schema_version': 1})
    locks = store.acquire_many(PROFILE, (('repository', 'repo'), ('lane', 'job')), 'worker-1')
    vector = GuardVector((('job', 0), ('authority', 1), ('premise', 1)), 'authority', 1, 'worker-1')
    return store, locks, vector


def intent(store, locks, vector, effect='effect-1'):
    return store.commit_guarded(PROFILE, 'job', 0, vector, locks, {'schema_version': 1, 'status': 'prepared'}, effect, {'kind': 'local-delivery', 'value': 'one'})


def claimed(tmp_path):
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    intent(store, locks, vector)
    post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
    effect = store.claim_guarded(PROFILE, 'effect-1', locks, post)
    return store, locks, post, effect


def test_guarded_api_is_additive(tmp_path):
    """Missing extension must fail without removing legacy store support."""
    store = SQLiteOperationalStore(tmp_path / 'store.sqlite')
    assert callable(getattr(store, 'commit_guarded', None))
    assert store.commit_with_effect('legacy', 'job', 0, {}, 'old', {}) == 1
    assert store.claim_effect('legacy', 'old').identity == 'old'
    store.confirm_effect('legacy', 'old', 'legacy-receipt')


def test_same_database_guarded_roundtrip_and_dedup(tmp_path):
    """Dropping consumer dedup or durable receipt loses effectively-once delivery."""
    store, locks, post, effect = claimed(tmp_path)
    assert effect.payload == {'kind': 'local-delivery', 'value': 'one'}
    receipt = store.consume_guarded(PROFILE, 'effect-1', locks, post)
    other = SQLiteOperationalStore(store.path, clock=lambda: 100)
    assert other.consume_guarded(PROFILE, 'effect-1', locks, post) == receipt
    assert other.readback_guarded(PROFILE, 'effect-1') == receipt
    assert receipt.effect_id == 'effect-1' and receipt.invocation == 'worker-1'
    confirmation = other.confirm_guarded(PROFILE, 'effect-1', locks, receipt)
    assert confirmation.effect_id == 'effect-1'
    assert other.confirm_guarded(PROFILE, 'effect-1', locks, receipt) == confirmation
    for lock in locks:
        other.release(PROFILE, lock.scope, lock.key, lock.owner, lock.fence)
    assert store.recovery_reservations(PROFILE) == ()


@pytest.mark.parametrize('boundary', ['intent', 'claim'])
def test_stale_fence_rejected(tmp_path, boundary):
    """Removing the owner/fence check admits a forged reservation."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    stale = (replace(locks[0], fence=locks[0].fence + 1), *locks[1:])
    if boundary == 'intent':
        with pytest.raises(StaleFence):
            intent(store, stale, vector)
        assert store.read_state(PROFILE, 'job') == (0, {})
        assert store.pending_effects(PROFILE) == ()
    else:
        intent(store, locks, vector)
        post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
        with pytest.raises(StaleFence):
            store.claim_guarded(PROFILE, 'effect-1', stale, post)
        assert len(store.pending_effects(PROFILE)) == 1


@pytest.mark.parametrize('boundary', ['intent', 'claim', 'consume'])
def test_stale_vector_rejected(tmp_path, boundary):
    """Removing vector admission sends effects based on obsolete premises."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    if boundary != 'intent':
        intent(store, locks, vector)
        vector = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
    if boundary == 'consume':
        store.claim_guarded(PROFILE, 'effect-1', locks, vector)
    store.commit(PROFILE, 'premise', 1, {'schema_version': 1, 'changed': True})
    with pytest.raises(VersionConflict):
        if boundary == 'intent':
            intent(store, locks, vector)
        elif boundary == 'claim':
            store.claim_guarded(PROFILE, 'effect-1', locks, vector)
        else:
            store.consume_guarded(PROFILE, 'effect-1', locks, vector)
    assert store.readback_guarded(PROFILE, 'effect-1') is None


@pytest.mark.parametrize('change', [{'active': False}, {'epoch': 2}, {'invocation': 'other'}, {'expires_at': 100}, {'expires_at': float('nan')}, {'schema_version': 99}])
def test_invalid_authority_rejected(tmp_path, change):
    """Ignoring revocation, tenure or schema permits unauthorized intent."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    store.commit(PROFILE, 'authority', 1, {**AUTHORITY, **change})
    vector = replace(vector, versions=(('job', 0), ('authority', 2), ('premise', 1)))
    with pytest.raises(ReservationRejected):
        intent(store, locks, vector)
    assert store.read_state(PROFILE, 'job') == (0, {})


@pytest.mark.parametrize('boundary', ['claim', 'consume'])
def test_expired_authority_cannot_claim_or_deliver(tmp_path, boundary):
    """A delayed sender cannot use authority after expiry even if revisions match."""
    now = [199.999]
    store, locks, vector = setup_store(tmp_path / 'store.sqlite', lambda: now[0])
    intent(store, locks, vector)
    post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
    if boundary == 'consume':
        store.claim_guarded(PROFILE, 'effect-1', locks, post)
    now[0] = 200
    with pytest.raises(ReservationRejected):
        if boundary == 'claim':
            store.claim_guarded(PROFILE, 'effect-1', locks, post)
        else:
            store.consume_guarded(PROFILE, 'effect-1', locks, post)
    assert store.readback_guarded(PROFILE, 'effect-1') is None
    for lock in locks:
        with pytest.raises(ReservationRejected):
            store.release(PROFILE, lock.scope, lock.key, lock.owner, lock.fence)
    with pytest.raises(ReservationRejected):
        store.acquire(PROFILE, 'lane', 'job', 'replacement')


def test_forged_receipt_cannot_confirm(tmp_path):
    """Removing correlation admits a caller-authored or another effect's receipt."""
    store, locks, post, _ = claimed(tmp_path)
    receipt = store.consume_guarded(PROFILE, 'effect-1', locks, post)
    for forged in (replace(receipt, effect_id='other'), replace(receipt, invocation='other'), replace(receipt, digest='sha256:' + '0' * 64)):
        with pytest.raises(ReservationRejected):
            store.confirm_guarded(PROFILE, 'effect-1', locks, forged)
    assert len(store.unresolved_effects(PROFILE)) == 1


def test_confirmation_requires_receipt_and_retained_fences_but_allows_expiry(tmp_path):
    """Completion readback remains possible after tenure without authorizing a resend."""
    store, locks, post, _ = claimed(tmp_path)
    assert store.readback_guarded(PROFILE, 'effect-1') is None
    receipt = store.consume_guarded(PROFILE, 'effect-1', locks, post)
    expired = SQLiteOperationalStore(store.path, clock=lambda: 201)
    with pytest.raises(StaleFence):
        expired.confirm_guarded(PROFILE, 'effect-1', (replace(locks[0], fence=9), *locks[1:]), receipt)
    assert expired.confirm_guarded(PROFILE, 'effect-1', locks, receipt).effect_id == 'effect-1'


@pytest.mark.parametrize('operation', ['commit', 'receive', 'apply', 'intent', 'claim', 'confirm', 'mark', 'park', 'authorize'])
def test_adopted_lane_refuses_all_legacy_bypasses(tmp_path, operation):
    """A single legacy path would defeat guarded-lane adoption."""
    store, locks, post, _ = claimed(tmp_path)
    store.record_receipt(PROFILE, 'event', 'digest', 'job')
    calls = {
        'commit': lambda: store.commit(PROFILE, 'job', 1, {}),
        'receive': lambda: store.receive(PROFILE, 'event2', 'digest', 'job', 1, {}),
        'apply': lambda: store.apply_receipt(PROFILE, 'event', 1, {}, 'other', {}),
        'intent': lambda: store.commit_with_effect(PROFILE, 'job', 1, {}, 'other', {}),
        'claim': lambda: store.claim_effect(PROFILE, 'effect-1'),
        'confirm': lambda: store.confirm_effect(PROFILE, 'effect-1', 'forged'),
        'mark': lambda: store.mark_effect_unknown(PROFILE, 'effect-1'),
        'park': lambda: store.park_unknown_effect(PROFILE, 'effect-1', 1, {}),
        'authorize': lambda: store.authorize_unknown_effect(PROFILE, 'effect-1', 'job', 1, {}),
    }
    with pytest.raises(ReservationRejected):
        calls[operation]()
    assert store.read_state(PROFILE, 'job')[0] == 1
    assert len(store.unresolved_effects(PROFILE)) == 1


def test_adoption_refuses_existing_pending_legacy_effect(tmp_path):
    """Adopting around old pending work would leave an unguarded participant."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    store.commit_with_effect(PROFILE, 'job', 0, {}, 'old', {})
    vector = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
    with pytest.raises(ReservationRejected):
        store.commit_guarded(PROFILE, 'job', 1, vector, locks, {}, 'new', {})
    store.claim_effect(PROFILE, 'old')  # failed adoption must not half-adopt


def test_multi_reservation_contention_is_atomic_and_preserves_retained_owner(tmp_path):
    """Partial lock acquisition must roll back without releasing retained owners."""
    store, locks, _, _ = claimed(tmp_path)
    with pytest.raises(ReservationRejected):
        store.acquire_many(PROFILE, (('zz', 'free'), ('lane', 'job'), ('aa', 'free')), 'replacement')
    assert store.recovery_reservations(PROFILE) == locks
    acquired = store.acquire_many('other', (('z', '2'), ('a', '1')), 'other-worker')
    assert [(r.scope, r.key) for r in acquired] == [('a', '1'), ('z', '2')]
    assert store.recovery_reservations(PROFILE) == locks


def test_duplicate_identity_rolls_back_another_lane(tmp_path):
    """Global profile effect uniqueness must not partially advance another lane."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    intent(store, locks, vector)
    other = replace(vector, versions=(('other-job', 0), ('authority', 1), ('premise', 1)))
    with pytest.raises(ReservationRejected):
        store.commit_guarded(PROFILE, 'other-job', 0, other, locks, {}, 'effect-1', {})
    assert store.read_state(PROFILE, 'other-job') == (0, {})
    assert store.commit(PROFILE, 'other-job', 0, {}) == 1


def test_claim_cannot_omit_a_vector_component(tmp_path):
    """Refreshing or weakening a stored vector must not reauthorize stale intent."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    intent(store, locks, vector)
    omitted = replace(vector, versions=(('job', 1), ('authority', 1)))
    with pytest.raises(ReservationRejected):
        store.claim_guarded(PROFILE, 'effect-1', locks, omitted)
    assert len(store.pending_effects(PROFILE)) == 1


def _child_env():
    return {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[2] / 'src') + os.pathsep + str(Path(__file__).resolve().parents[2])}


CHILD = '''
import sys, os, signal
from pathlib import Path
from dataclasses import replace
from tests.execution_coordination.test_fenced_store import PROFILE, intent
from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
from alienintent.execution_coordination.ports.fenced_store import GuardVector
from alienintent.execution_coordination.ports.operational_store import ReservationRejected, VersionConflict
store = SQLiteOperationalStore(Path(sys.argv[1]), clock=lambda: 100)
locks = store.recovery_reservations(PROFILE)
vector = GuardVector((('job', 0), ('authority', 1), ('premise', 1)), 'authority', 1, 'worker-1')
post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
mode = sys.argv[2]
if mode.startswith('race-'):
    print('ready', flush=True)
    sys.stdin.readline()
    try:
        if mode == 'race-intent': intent(store, locks, vector)
        elif mode == 'race-claim': store.claim_guarded(PROFILE, 'effect-1', locks, post)
        elif mode == 'race-consume': store.consume_guarded(PROFILE, 'effect-1', locks, post)
        print('accepted', flush=True)
    except (ReservationRejected, VersionConflict): print('refused', flush=True)
    raise SystemExit(0)
def kill(): os.kill(os.getpid(), signal.SIGKILL)
if mode == 'before-intent':
    original = store._save_guard_record
    def interrupted(*args, **kwargs):
        original(*args, **kwargs)
        kill()
    store._save_guard_record = interrupted
intent(store, locks, vector)
if mode == 'after-intent': kill()
store.claim_guarded(PROFILE, 'effect-1', locks, post)
if mode == 'after-claim': kill()
store.consume_guarded(PROFILE, 'effect-1', locks, post)
if mode == 'after-consume': kill()
store.readback_guarded(PROFILE, 'effect-1')
if mode == 'after-readback': kill()
'''


@pytest.mark.parametrize('boundary', ['intent', 'claim', 'consume'])
def test_two_processes_compete_on_same_database(tmp_path, boundary):
    """Without atomic admission two real processes could both claim an effect."""
    path = tmp_path / 'race.sqlite'
    store, locks, vector = setup_store(path)
    if boundary != 'intent':
        intent(store, locks, vector)
    if boundary == 'consume':
        post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
        store.claim_guarded(PROFILE, 'effect-1', locks, post)
    children = [subprocess.Popen([sys.executable, '-c', CHILD, str(path), 'race-' + boundary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=_child_env()) for _ in range(2)]
    try:
        for child in children:
            assert child.stdout.readline().strip() == 'ready'
        for child in children:
            child.stdin.write('go\n')
            child.stdin.flush()
        outcomes = []
        for child in children:
            out, err = child.communicate(timeout=10)
            assert child.returncode == 0, err
            outcomes.append(out.strip())
        assert sorted(outcomes) == (['accepted', 'accepted'] if boundary == 'consume' else ['accepted', 'refused'])
        assert store.read_state(PROFILE, 'job')[0] == 1
        if boundary == 'consume':
            # Exactly one durable consumer row despite two accepted deduplicated sends.
            assert len(store.list_states(PROFILE, '__fenced__:["consumer"')) == 1
            assert store.readback_guarded(PROFILE, 'effect-1') is not None
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
                child.wait()


@pytest.mark.parametrize('boundary', ['before-intent', 'after-intent', 'after-claim', 'after-consume', 'after-readback'])
def test_sigkill_keeps_unknown_ownership_and_consumer_readback(tmp_path, boundary):
    """Crashes must not lose intent, leak locks, or repeat accepted delivery."""
    path = tmp_path / 'crash.sqlite'
    store, locks, vector = setup_store(path)
    child = subprocess.run([sys.executable, '-c', CHILD, str(path), boundary], capture_output=True, text=True, env=_child_env(), timeout=10)
    assert child.returncode == -signal.SIGKILL, child.stderr
    reopened = SQLiteOperationalStore(path, clock=lambda: 100)
    assert reopened.recovery_reservations(PROFILE) == locks
    if boundary == 'before-intent':
        assert reopened.read_state(PROFILE, 'job') == (0, {})
        assert reopened.pending_effects(PROFILE) == ()
        intent(reopened, locks, vector)
    post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
    if boundary in ('before-intent', 'after-intent'):
        reopened.claim_guarded(PROFILE, 'effect-1', locks, post)
    else:
        with pytest.raises(ReservationRejected):
            reopened.claim_guarded(PROFILE, 'effect-1', locks, post)
    for lock in locks:
        with pytest.raises(ReservationRejected):
            reopened.release(PROFILE, lock.scope, lock.key, lock.owner, lock.fence)
    receipt = reopened.readback_guarded(PROFILE, 'effect-1')
    if boundary in ('after-consume', 'after-readback'):
        assert receipt is not None
        assert reopened.consume_guarded(PROFILE, 'effect-1', locks, post) == receipt
        reopened.confirm_guarded(PROFILE, 'effect-1', locks, receipt)
        assert reopened.unresolved_effects(PROFILE) == ()
    else:
        assert receipt is None  # unknown sends are held, not silently resent
        assert len(reopened.unresolved_effects(PROFILE)) == 1


def test_receipt_cannot_cross_profiles_with_identical_local_identities(tmp_path):
    """Receipt correlation must include profile, not just effect/invocation/fences."""
    from alienintent.execution_coordination.ports.fenced_store import GuardVector
    store, locks, post, _ = claimed(tmp_path)
    receipt = store.consume_guarded(PROFILE, 'effect-1', locks, post)
    other = 'another-profile'
    store.commit(other, 'authority', 0, AUTHORITY)
    store.commit(other, 'premise', 0, {})
    other_locks = store.acquire_many(other, (('repository', 'repo'), ('lane', 'job')), 'worker-1')
    vector = GuardVector((('job', 0), ('authority', 1), ('premise', 1)), 'authority', 1, 'worker-1')
    store.commit_guarded(other, 'job', 0, vector, other_locks, {}, 'effect-1', {'kind': 'local-delivery', 'value': 'one'})
    store.claim_guarded(other, 'effect-1', other_locks, post)
    other_receipt = store.consume_guarded(other, 'effect-1', other_locks, post)
    with pytest.raises(ReservationRejected):
        store.confirm_guarded(other, 'effect-1', other_locks, receipt)
    assert other_receipt != receipt


def test_delayed_original_sender_cannot_act_after_completed_reassignment(tmp_path):
    """A stale sender must not deliver or confirm after a fence advances."""
    store, locks, post, _ = claimed(tmp_path)
    receipt = store.consume_guarded(PROFILE, 'effect-1', locks, post)
    store.confirm_guarded(PROFILE, 'effect-1', locks, receipt)
    for lock in locks:
        store.release(PROFILE, lock.scope, lock.key, lock.owner, lock.fence)
    next_locks = store.acquire_many(PROFILE, tuple((r.scope, r.key) for r in locks), 'worker-2')
    assert all(r.fence == 2 for r in next_locks)
    with pytest.raises(StaleFence):
        store.consume_guarded(PROFILE, 'effect-1', locks, post)
    with pytest.raises(StaleFence):
        store.confirm_guarded(PROFILE, 'effect-1', locks, receipt)
    assert store.readback_guarded(PROFILE, 'effect-1') == receipt


@pytest.mark.parametrize('boundary', ['claim', 'consume'])
def test_revoked_authority_suppresses_dispatch_even_with_refreshed_vector(tmp_path, boundary):
    """Suppression is durable authority.active=False; updating revisions cannot bypass it."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    intent(store, locks, vector)
    post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
    if boundary == 'consume':
        store.claim_guarded(PROFILE, 'effect-1', locks, post)
    store.commit(PROFILE, 'authority', 1, {**AUTHORITY, 'active': False})
    refreshed = replace(post, versions=(('job', 1), ('authority', 2), ('premise', 1)))
    with pytest.raises(ReservationRejected, match='inactive'):
        if boundary == 'claim':
            store.claim_guarded(PROFILE, 'effect-1', locks, refreshed)
        else:
            store.consume_guarded(PROFILE, 'effect-1', locks, refreshed)
    assert store.readback_guarded(PROFILE, 'effect-1') is None
    assert store.recovery_reservations(PROFILE) == locks


def test_legacy_claim_is_blocked_while_guarded_intent_still_pending(tmp_path):
    """Status rejection alone would miss a legacy claim before guarded dispatch."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    intent(store, locks, vector)
    with pytest.raises(ReservationRejected):
        store.claim_effect(PROFILE, 'effect-1')
    assert len(store.pending_effects(PROFILE)) == 1


def test_missing_clock_refuses_new_guarded_dispatch_without_losing_ownership(tmp_path):
    """Legacy store construction must not silently assume authority is unexpired."""
    store, locks, vector = setup_store(tmp_path / 'store.sqlite')
    unclocked = SQLiteOperationalStore(store.path)
    with pytest.raises(ReservationRejected):
        intent(unclocked, locks, vector)
    assert store.read_state(PROFILE, 'job') == (0, {})
    assert store.recovery_reservations(PROFILE) == locks
