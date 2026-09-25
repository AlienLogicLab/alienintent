"""FX-L1: known-active liveness reconciliation over real SQLite, C1 attention and C4 monitor health.

Local/composed proof only: fake UTC-microsecond clock, local guarded journal
consumer, no provider, host or live workload.
"""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
G, I, C = 300 * SECOND, 60 * SECOND, 90 * SECOND
PROFILE = "fixture"
BIU = "WO-L1"
DIGEST = "sha256:" + "c" * 64
AUTHORITY = "authority:dispatch"
JUDGE = "founder-judgment"
ROOT = Path(__file__).resolve().parents[2]


class Clock:
    def __init__(self, now=T0):
        self.now = now

    def __call__(self):
        return self.now


def revision(generation=1):
    return f"{DIGEST}:generation:{generation}"


def build(root, clock, *, policy="default", monitor=True, lane="producer", generation=1):
    from alienintent.composition.control_plane_profile import AttentionProfile, MonitorProfile
    from alienintent.composition.liveness_profile import LivenessProfile
    from alienintent.control_plane.domain.attention import ResolverGrant
    from alienintent.control_plane.domain.monitor_health import MonitorPolicy
    from alienintent.execution_coordination.domain.liveness import LivenessPolicy
    attention = AttentionProfile(root, project="project", name=PROFILE, invocation="fx-l1",
        clock=lambda: "2026-09-26T00:00:00Z", next_id=lambda: "attempt-1",
        resolvers=(ResolverGrant("director", JUDGE, BIU, revision(generation), lane),))
    ids = iter(f"monitor-{n}" for n in range(1, 100))
    health = MonitorProfile(root, project="project", name=PROFILE, invocation="fx-l1", policy=MonitorPolicy(60),
                            clock=clock, next_id=lambda: next(ids)) if monitor else None
    return LivenessProfile(root, project="project", name=PROFILE,
                           policy=LivenessPolicy() if policy == "default" else policy, clock=clock,
                           attention=attention, monitor=health, required_authority=JUDGE)


def grant(profile, *, active=True):
    version, _ = profile.store.read_state(PROFILE, AUTHORITY)
    profile.store.commit(PROFILE, AUTHORITY, version, {"schema_version": 1, "active": active, "epoch": 1,
                         "invocation": "dispatcher-1", "expires_at": T0 / SECOND + 10 ** 6})


def known(stage="IMPLEMENT", generation=1, entered=T0, **changes):
    from alienintent.execution_coordination.domain.liveness import KnownActive
    candidate = None if stage == "IMPLEMENT" else "candidate:abc"
    return replace(KnownActive(BIU, "repo:alienintent", DIGEST, stage, generation, entered, AUTHORITY, True,
                               candidate), **changes)


def started(tmp_path, clock, active=None, **options):
    p = build(tmp_path, clock, **options)
    grant(p)
    if active is not False:
        p.journal.enter(active or known())
    if p.reconciler.progress is not None:
        p.reconciler.progress.start()
    p.reconciler.start()
    return p


def scan(p, clock, now):
    clock.now = now
    if p.reconciler.progress is not None:
        p.reconciler.progress.tick()
    return p.reconciler.scan()


def kinds(report):
    return [e.kind for e in report.events]


def consumers(p):
    """Every durable guarded consumer outcome: the effective actions actually taken."""
    return [s for _, _, s in p.store.list_states(PROFILE, '__fenced__:["consumer",')]


def outcome(identity, kind, sequence, generation=1, role="producer"):
    from alienintent.execution_coordination.domain.liveness import CorrelatedOutcome
    return CorrelatedOutcome(identity, BIU, generation, role, kind, sequence)


def expected(p, active=None, role="producer"):
    from alienintent.execution_coordination.domain.liveness import expected_effects
    return next(e for e in expected_effects(PROFILE, active or known()) if e.role_key == role)


# ---- policy (fixed choices) -------------------------------------------------------------

def test_policy_defaults_and_digest():
    from alienintent.execution_coordination.domain.liveness import LivenessPolicy
    policy = LivenessPolicy()
    assert (policy.grace_seconds, policy.interval_seconds, policy.confirmation_seconds) == (300, 60, 90)
    assert policy.digest() != LivenessPolicy(301).digest()


@pytest.mark.parametrize("policy", [None, 0, -1, float("nan"), float("inf"), "300"])
def test_policy_invalid_blocks_startup(tmp_path, policy):
    from alienintent.execution_coordination.domain.liveness import LivenessHold, LivenessPolicy
    with pytest.raises(LivenessHold, match="POLICY_(MISSING|INVALID)"):
        build(tmp_path, Clock(), policy=None if policy is None else LivenessPolicy(policy))
    assert not (tmp_path / "liveness.sqlite").exists(), "a blocked startup must not open the liveness store"


def test_policy_digest_persisted_at_start(tmp_path):
    p = started(tmp_path, Clock())
    _, body = p.store.read_state(PROFILE, "liveness-policy:" + PROFILE)
    assert body["policy_digest"] == p.reconciler.policy.digest()
    assert body["policy"] == {"grace_seconds": 300, "interval_seconds": 60, "confirmation_seconds": 90}


# ---- AC-01 grace and detection bound ----------------------------------------------------

@pytest.mark.parametrize("offset,recovers", [(-1, False), (0, True)], ids=["below", "at"])
def test_grace_boundary(tmp_path, offset, recovers):
    clock = Clock()
    p = started(tmp_path, clock)
    report = scan(p, clock, T0 + G + offset)
    if recovers:
        assert kinds(report) == ["liveness.gap", "liveness.recovery_intent", "liveness.readback_confirmed"], \
            "at exactly G a missing expected effect yields one recovery intent"
        assert len(consumers(p)) == 1
    else:
        assert kinds(report) == ["liveness.no_action"] and report.events[0].reason == "WITHIN_GRACE", \
            "before G nothing is recovered"
        assert consumers(p) == []


@pytest.mark.parametrize("grace,interval,phase", [(300, 60, 17), (120, 30, 29), (300, 60, 0)])
def test_detection_bound_g_plus_i(tmp_path, grace, interval, phase):
    from alienintent.execution_coordination.domain.liveness import LivenessPolicy
    clock = Clock()
    p = started(tmp_path, clock, policy=LivenessPolicy(grace, interval, 90))
    detected = None
    for k in range(40):
        report = scan(p, clock, T0 + (phase + k * interval) * SECOND)
        if "liveness.recovery_intent" in kinds(report):
            detected = clock.now
            break
        assert consumers(p) == []
    assert detected is not None and detected - T0 >= grace * SECOND
    assert detected - T0 <= (grace + interval) * SECOND, "under a progressing clock detection is within G + I"
    assert len(consumers(p)) == 1


def test_bound_claim_requires_healthy_monitor(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    assert scan(p, clock, T0 + SECOND).bound_claim == "G_PLUS_I_CLAIMED"
    clock.now = T0 + 2 * I + 2 * SECOND  # monitor tick and scan now overdue
    report = p.reconciler.scan()
    assert report.bound_claim.startswith("WITHDRAWN:"), "a scan must not claim G+I on unhealthy monitor evidence"
    (tmp_path / "unmonitored").mkdir()
    unmonitored = started(tmp_path / "unmonitored", clock, monitor=False)
    assert unmonitored.reconciler.scan().bound_claim == "WITHDRAWN:UNVERIFIED:MONITOR_UNBOUND"


def test_scan_progress_reported_to_monitor(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    scan(p, clock, T0 + SECOND)
    record = p.reconciler.progress.repository.read(PROFILE)
    assert record.last_scan_outcome == "COMPLETE" and record.last_scan_completed_at == T0 + SECOND


# ---- AC-02 correlated evidence yields no recovery ----------------------------------------

def _active_invocation(p):
    p.journal.record_invocation(known(), "invocation-1", True)


def _pending_intent(p):
    version, _ = p.store.read_state(PROFILE, "liveness-active:" + BIU)
    assert type(p.admission.intend(known(), version, expected(p), "original-delivery:d-1")).__name__ == "Intent"


def _unknown_within_c(p):
    version, _ = p.store.read_state(PROFILE, "liveness-active:" + BIU)
    intent = p.admission.intend(known(), version, expected(p), "original-delivery:d-1")
    p.store.claim_guarded(PROFILE, intent.effect_key, intent.reservations, intent.vector)


def _completion_awaiting_projection(p):
    p.journal.record_outcome(outcome("outcome-1", "SUCCESS", 1))


def _confirmed(p):
    version, _ = p.store.read_state(PROFILE, "liveness-active:" + BIU)
    assert type(p.admission.admit(known(), version, expected(p), "original-delivery:d-1")).__name__ == "Admitted"


def _legacy_launch(p):
    p.store.commit_with_effect(PROFILE, "execution:" + BIU, 0, {"stage": "IMPLEMENT"}, "launch:WO-L1:1",
                               {"correlation": "launch:WO-L1:1", "work": BIU, "role": "producer"})


CASES = {
    "active_invocation": (known(), _active_invocation, "ACTIVE_INVOCATION"),
    "pending_effect": (known(), _pending_intent, "PENDING_EFFECT"),
    "unknown_within_confirmation_bound": (known(), _unknown_within_c, "PENDING_EFFECT"),
    "completion_awaiting_projection": (known(), _completion_awaiting_projection, "COMPLETED_AWAITING_PROJECTION"),
    "confirmed_effect": (known(), _confirmed, "COMPLETED_AWAITING_PROJECTION"),
    "legacy_launch_pending": (known(), _legacy_launch, "LEGACY_EFFECT_PENDING"),
    "accept_without_closure": (known("ACCEPT"), None, "ACCEPT_NO_OUTSTANDING_CLOSURE"),
    "review": (known("REVIEW"), None, "NO_EXPECTED_EFFECT"),
    "terminal": (known("DONE"), None, "NO_EXPECTED_EFFECT"),
}


@pytest.mark.parametrize("case", CASES)
def test_correlated_evidence_yields_no_recovery(tmp_path, case):
    active, prepare, reason = CASES[case]
    in_flight = case in ("pending_effect", "unknown_within_confirmation_bound")
    clock = Clock(T0 + G if in_flight else T0)
    p = started(tmp_path, clock, active)
    if prepare is not None:
        prepare(p)
    before = consumers(p)
    # An in-flight intent is observed within C; past C it is resumed, never relaunched.
    for now in ((T0 + G + C - SECOND,) if in_flight else (T0 + G, T0 + 2 * G + SECOND, T0 + 5 * G)):
        report = scan(p, clock, now)
        assert kinds(report) == ["liveness.no_action"] and report.events[0].reason == reason, \
            f"{case} must yield no recovery invocation"
    assert consumers(p) == before


def test_pending_unsent_intent_past_c_executes_by_canonical_claim(tmp_path):
    clock = Clock(T0 + G)
    p = started(tmp_path, clock)
    _pending_intent(p)
    report = scan(p, clock, T0 + G + C)
    assert kinds(report) == ["liveness.readback_confirmed"], "no second intent; the durable one is claimed"
    assert len(consumers(p)) == 1 and p.store.pending_effects(PROFILE) == ()


def test_accept_recovers_each_missing_required_closure_effect(tmp_path):
    clock = Clock()
    active = known("ACCEPT", closure_actions=("merge", "cleanup"))
    p = started(tmp_path, clock, active)
    report = scan(p, clock, T0 + G)
    assert kinds(report).count("liveness.recovery_intent") == 2
    assert sorted(c["outcome"]["payload"]["role_key"] for c in consumers(p)) == ["closure:cleanup", "closure:merge"]
    assert "liveness.recovery_intent" not in kinds(scan(p, clock, T0 + 3 * G))


@pytest.mark.parametrize("offset,status", [(-1, "no_action"), (0, "evidence_hold")], ids=["below", "at"])
def test_unknown_effect_holds_at_confirmation_bound(tmp_path, offset, status):
    """Unknown outcome is a readback hold at C, never fabricated absence or a resend."""
    clock = Clock(T0 + G)
    p = started(tmp_path, clock)
    _unknown_within_c(p)
    report = scan(p, clock, T0 + G + C + offset)
    assert kinds(report) == ["liveness." + status], "unknown evidence must hold rather than launch"
    assert consumers(p) == []
    assert p.store.unresolved_effects(PROFILE), "the unknown effect keeps its ownership"
    if status == "evidence_hold":
        _, hold = p.store.read_state(PROFILE, "liveness-hold:" + BIU)
        assert hold["reason"] == "READBACK_PENDING"
        assert report.outcome == "EVIDENCE_HOLD"


def test_unknown_effect_with_durable_receipt_confirms_by_readback(tmp_path):
    clock = Clock(T0 + G)
    p = started(tmp_path, clock)
    version, _ = p.store.read_state(PROFILE, "liveness-active:" + BIU)
    intent = p.admission.intend(known(), version, expected(p), "original-delivery:d-1")
    p.store.claim_guarded(PROFILE, intent.effect_key, intent.reservations, intent.vector)
    p.store.consume_guarded(PROFILE, intent.effect_key, intent.reservations, intent.vector)
    report = scan(p, clock, T0 + G + C)
    assert kinds(report) == ["liveness.readback_confirmed"]
    assert len(consumers(p)) == 1 and p.store.recovery_reservations(PROFILE) == ()


def test_unavailable_observation_is_evidence_hold(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    p.store.commit(PROFILE, "liveness-invocation:" + BIU, 0, {"schema_version": 2})
    report = scan(p, clock, T0 + 2 * G)
    assert kinds(report) == ["liveness.evidence_hold"] and report.events[0].reason.startswith("OBSERVATION_UNAVAILABLE")
    assert consumers(p) == []


# ---- AC-03 delayed original, contenders and restart ---------------------------------------

CHILD = r"""
import json, sys
sys.path.insert(0, sys.argv[1] + '/tests/execution_coordination')
from pathlib import Path
from test_liveness_reconciliation import Clock, build, expected, known, PROFILE, BIU
clock = Clock(int(sys.argv[3]))
p = build(Path(sys.argv[2]), clock)
version, _ = p.store.read_state(PROFILE, 'liveness-active:' + BIU)
result = p.admission.admit(known(), version, expected(p), 'original-delivery:' + sys.argv[4])
print(json.dumps({'type': type(result).__name__, 'reason': getattr(result, 'reason', None)}))
"""


def delayed_original(root, now, delivery):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    child = subprocess.run([sys.executable, "-c", CHILD, str(ROOT), str(root), str(now), delivery],
                           capture_output=True, text=True, env=env, timeout=60)
    assert child.returncode == 0, child.stderr
    return json.loads(child.stdout.strip().splitlines()[-1])


def test_race_delayed_original_contenders_and_restart(tmp_path):
    """One effective authorized action and correlated readback; stale claims refused."""
    from alienintent.execution_coordination.domain.liveness import Gap
    clock = Clock(T0 + G)
    first = started(tmp_path, clock)
    lifecycle = first.store.read_state(PROFILE, "liveness-active:" + BIU)
    second = build(tmp_path, clock, monitor=False)  # one monitor writer; contenders only reconcile
    second.reconciler.start()
    a, b = first.reconciler.inspect(known()), second.reconciler.inspect(known())
    assert isinstance(a, Gap) and isinstance(b, Gap), "both reconcilers see the same gap"
    assert a.missing == b.missing
    effect = a.missing[0]
    intent = first.admission.intend(known(), lifecycle[0], effect, "liveness-scan")
    assert type(intent).__name__ == "Intent"
    refused = second.admission.admit(known(), lifecycle[0], effect, "liveness-scan")
    assert (type(refused).__name__, refused.reason) == ("Refused", "RESERVED"), "a competing claim is refused"
    # Crash between durable intent and effect completion; a fresh process reopens it.
    del first
    restarted = build(tmp_path, clock, monitor=False)
    reopened = restarted.reconciler.start()
    assert [type(r).__name__ for r in reopened] == ["Admitted"]
    duplicate_scan = second.reconciler.scan()
    assert "liveness.recovery_intent" not in kinds(duplicate_scan)
    late = delayed_original(tmp_path, T0 + G + 2 * SECOND, "d-17")
    assert late == {"type": "Refused", "reason": "EFFECT_IDENTITY_USED"}, "delayed original must not act again"
    assert "liveness.recovery_intent" not in kinds(restarted.reconciler.scan())
    records = consumers(restarted)
    assert len(records) == 1, "exactly one effective authorized action"
    receipt = restarted.store.readback_guarded(PROFILE, effect.effect_key)
    assert receipt is not None and receipt.effect_id == effect.effect_key and receipt.invocation == "dispatcher-1"
    assert restarted.store.pending_effects(PROFILE) == () and restarted.store.unresolved_effects(PROFILE) == ()
    assert restarted.store.recovery_reservations(PROFILE) == ()
    assert restarted.store.read_state(PROFILE, "liveness-active:" + BIU) == lifecycle, "no status toggling"


def test_stale_lifecycle_snapshot_refused(tmp_path):
    clock = Clock(T0 + G)
    p = started(tmp_path, clock)
    version, _ = p.store.read_state(PROFILE, "liveness-active:" + BIU)
    old = known()
    p.journal.enter(known("VERIFY", generation=2, entered=T0 + G))
    result = p.admission.admit(old, version, expected(p, old), "liveness-scan")
    assert (type(result).__name__, result.reason) == ("Refused", "STALE_SNAPSHOT")
    assert consumers(p) == []


# ---- AC-04 / AC-05 judgment suppression and resolution ------------------------------------

def judged(tmp_path, clock, kind="FOUNDER_EXCEPTION", **options):
    """The original launch ran outside the fenced journal (e.g. bootstrap); only its judgment outcome is known."""
    p = started(tmp_path, clock, **options)
    p.journal.record_outcome(outcome("outcome-1", kind, 1))
    return p


@pytest.mark.parametrize("kind", ["FOUNDER_EXCEPTION", "HUMAN_DECISION_REQUIRED", "AUTHORITY_BLOCK"])
def test_completed_judgment_suppresses_relaunch_indefinitely(tmp_path, kind):
    clock = Clock()
    p = judged(tmp_path, clock, kind)
    for n in (1, 2, 5, 20, 100):
        report = scan(p, clock, T0 + n * G)
        assert kinds(report) == ["liveness.suppressed"], "a completed judgment outcome must suppress relaunch"
    assert consumers(p) == [], "no relaunch after any number of grace periods"
    items = p.judgment.attention.list_pending()
    assert len(items) == 1, "one attributable durable attention item is created and retained"
    assert (items[0].origin.kind, items[0].origin.event_identity, items[0].origin.producer) == \
        ("JUDGMENT", "outcome-1", "liveness-reconciler")
    assert report.events[0].attention == items[0].identity


def recorded_resolution(p, item, **changes):
    from alienintent.control_plane.domain.attention import Resolution
    from alienintent.evidence_learning.domain.records import Header, Observation, canonical_bytes
    decision = replace(Resolution("director", JUDGE, item.origin.work_revision, item.origin.lane, item.version,
                                  item.origin.source_ref), **changes)
    body = {"item_identity": item.identity, "actor": decision.actor, "authority": decision.authority,
            "work_revision": decision.work_revision, "lane": decision.lane, "expected_version": decision.expected_version}
    record = Observation(Header("project", PROFILE, "resolution:" + item.identity, str(item.version),
        (item.history_ref,)), item.history_ref, item.identity, "attention-resolution", (item.history_ref,),
        canonical_bytes(body).decode(), None, decision.actor, "authorized-consumer")
    evidence = p.judgment.attention.repository.evidence
    return replace(decision, decision_ref=evidence.put(record))


def test_seen_only_leaves_suppression(tmp_path):
    clock = Clock()
    p = judged(tmp_path, clock)
    scan(p, clock, T0 + G)
    item = p.judgment.attention.list_pending()[0]
    p.judgment.attention.seen(item.identity, "director", item.version)
    assert kinds(scan(p, clock, T0 + 3 * G)) == ["liveness.suppressed"], "SEEN is not RESOLVED"
    assert consumers(p) == []


def test_valid_resolution_permits_reinspection_only(tmp_path):
    clock = Clock()
    p = judged(tmp_path, clock)
    scan(p, clock, T0 + G)
    service = p.judgment.attention
    item = service.list_pending()[0]
    service.resolve(item.identity, recorded_resolution(p, item))
    report = scan(p, clock, T0 + 3 * G)
    assert kinds(report) == ["liveness.no_action"] and report.events[0].reason == "COMPLETED_AWAITING_PROJECTION", \
        "resolution permits reinspection, never an unconditional retry"
    assert consumers(p) == []
    # A relaunch needs the canonical new-generation transition, which reinspection then honours.
    p.journal.enter(known(generation=2, entered=T0 + 3 * G))
    assert "liveness.recovery_intent" in kinds(scan(p, clock, T0 + 4 * G))
    assert len(consumers(p)) == 1


def test_newer_nonjudgment_outcome_permits_reevaluation(tmp_path):
    clock = Clock()
    p = judged(tmp_path, clock)
    assert kinds(scan(p, clock, T0 + G)) == ["liveness.suppressed"]
    p.journal.record_outcome(outcome("outcome-2", "SUCCESS", 2))
    report = scan(p, clock, T0 + 2 * G)
    assert kinds(report) == ["liveness.no_action"] and report.events[0].reason == "COMPLETED_AWAITING_PROJECTION"
    assert len(p.judgment.attention.list_pending()) == 1, "reevaluation does not auto-resolve attention"


def test_out_of_lane_resolution_keeps_suppression(tmp_path):
    from alienintent.control_plane.domain.attention import AttentionHold
    clock = Clock()
    p = judged(tmp_path, clock)
    scan(p, clock, T0 + G)
    service = p.judgment.attention
    item = service.list_pending()[0]
    with pytest.raises(AttentionHold, match="WRONG_ACTOR|WRONG_LANE"):
        service.resolve(item.identity, recorded_resolution(p, item, lane="verifier"))
    assert kinds(scan(p, clock, T0 + 2 * G)) == ["liveness.suppressed"]


def test_stale_resolution_keeps_suppression(tmp_path):
    clock = Clock()
    p = judged(tmp_path, clock)
    scan(p, clock, T0 + G)
    service = p.judgment.attention
    older = service.list_pending()[0]
    p.journal.record_outcome(outcome("outcome-2", "HUMAN_DECISION_REQUIRED", 2))
    scan(p, clock, T0 + 2 * G)
    service.resolve(older.identity, recorded_resolution(p, older))
    report = scan(p, clock, T0 + 3 * G)
    assert kinds(report) == ["liveness.suppressed"], "a resolution of an older outcome cannot lift a newer judgment"
    assert report.events[0].attention != older.identity
    assert consumers(p) == []


# ---- AC-06 canonical path and holds ------------------------------------------------------

@pytest.mark.parametrize("case,reason", [("authority_inactive", "AUTHORITY_UNAVAILABLE"),
                                         ("budget_unknown", "BUDGET_UNAVAILABLE"),
                                         ("custody_missing", "CUSTODY_UNAVAILABLE")])
def test_missing_authority_budget_or_custody_records_hold(tmp_path, case, reason):
    clock = Clock()
    active = {"authority_inactive": known(), "budget_unknown": known(budget_admitted=False),
              "custody_missing": known("VERIFY", candidate=None)}[case]
    p = started(tmp_path, clock, active)
    if case == "authority_inactive":
        grant(p, active=False)
    report = scan(p, clock, T0 + G)
    assert kinds(report) == ["liveness.gap", "liveness.evidence_hold"] and report.events[-1].reason == reason
    _, hold = p.store.read_state(PROFILE, "liveness-hold:" + BIU)
    assert hold["reason"] == reason, "a durable hold is recorded instead of a speculative launch"
    assert consumers(p) == [] and p.store.pending_effects(PROFILE) == ()


def test_recovery_uses_canonical_effect_path_without_status_toggling(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock)
    lifecycle = p.store.read_state(PROFILE, "liveness-active:" + BIU)
    scan(p, clock, T0 + G)
    (record,) = consumers(p)
    effect = expected(p)
    assert record["effect_id"] == effect.effect_key and record["outcome"]["payload"]["kind"] == "liveness-canonical-effect"
    _, lane = p.store.read_state(PROFILE, "liveness-lane:" + effect.effect_key)
    assert (lane["source"], lane["generation"], lane["role_key"]) == ("liveness-scan", 1, "producer")
    assert p.store.read_state(PROFILE, "liveness-active:" + BIU) == lifecycle
    assert not hasattr(p.reconciler, "journal"), "the reconciler holds no lifecycle writer"


def test_scanner_cannot_create_generation(tmp_path):
    from alienintent.execution_coordination.domain.liveness import LivenessHold
    p = started(tmp_path, Clock())
    with pytest.raises(LivenessHold, match="GENERATION_NOT_ADVANCED"):
        p.journal.enter(known("VERIFY"))


def test_effect_key_excludes_delivery_and_scan_time():
    from alienintent.execution_coordination.domain.liveness import effect_key
    base = known()
    assert effect_key(PROFILE, base, "producer") == effect_key(PROFILE, replace(base, entered_at=T0 + G), "producer")
    assert effect_key(PROFILE, base, "producer") != effect_key(PROFILE, replace(base, generation=2), "producer")
    assert effect_key(PROFILE, base, "producer") != effect_key("other", base, "producer")


def test_unknown_record_outside_known_active_is_not_discovered(tmp_path):
    clock = Clock()
    p = started(tmp_path, clock, active=False)
    p.journal.record_outcome(outcome("outcome-1", "SUCCESS", 1))
    assert scan(p, clock, T0 + 10 * G).events == (), "scans only already-known active records"
