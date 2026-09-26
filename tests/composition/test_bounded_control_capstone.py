"""FX-C (WO-220307, SF-REQ-053-AC-04): local bounded-control integration capstone.

C3 bounded coordinator episodes, C1 durable attention, C4 monitor health and L1 liveness
reconciliation composed by `BoundedControlProfile` over one FX-C2 seeded profile root, the
real SQLite store/guarded consumer/readback and one injected fake UTC-microsecond clock. No
provider, model, network, host or supervisor. A local PASS is not operational acceptance.

Reconstruction-equality predicate (`authorized_view`): the pinned manifest ref, the canonical
digest of the reconstructed document, and its `authorized_next_action_set`, `blocked_set`,
`pending_attention` and `lifecycle` are equal. They are compared across the ended context, the
fresh context and an independent OS process that shares only the durable store.
"""
import gc
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
G, I, C = 300 * SECOND, 60 * SECOND, 90 * SECOND
PROFILE = "fixture"
OBJECTIVE = "item-verify"
DIGEST = "sha256:" + "c" * 64
DISPATCH = "authority:dispatch"
JUDGE = "founder-judgment"
ROOT = Path(__file__).resolve().parents[2]
STORES = ("attention.sqlite", "liveness.sqlite", "monitor.sqlite")


class Clock:
    def __init__(self, now=T0):
        self.now = now

    def __call__(self):
        return self.now


class Timer:
    def __init__(self):
        self.armed = []

    def arm(self, objective, epoch, deadline_us):
        self.armed.append((objective, epoch, deadline_us))


class LaunchSpy:
    """Attention activation stays unbound: any launch is a failure (SF-REQ-053-AC-06)."""
    count = 0

    def launch(self, item):
        self.count += 1
        return "unexpected"


@pytest.fixture
def world(tmp_path):
    from tests.context_assembly.test_context_reconstruction import seed
    root = tmp_path / "profile"
    root.mkdir()
    seed(root)
    return root


def revision(generation=1):
    return f"{DIGEST}:generation:{generation}"


def known(generation=1, entered=T0):
    from alienintent.execution_coordination.domain.liveness import KnownActive
    return KnownActive(OBJECTIVE, "repo:alienintent", DIGEST, "VERIFY", generation, entered, DISPATCH, True,
                       "candidate:" + OBJECTIVE)


def verifier_effect():
    from alienintent.execution_coordination.domain.liveness import expected_effects
    (effect,) = expected_effects(PROFILE, known())
    return effect


def compose(root, clock, invocation, *, timer=None, spy=None):
    from alienintent.composition.bounded_control_profile import BoundedControlProfile
    from alienintent.control_plane.domain.attention import ResolverGrant
    from alienintent.control_plane.domain.episode import OperatorGrant, TenurePolicy
    from alienintent.control_plane.domain.monitor_health import MonitorPolicy
    from alienintent.execution_coordination.domain.liveness import LivenessPolicy
    return BoundedControlProfile(root, project="project", name=PROFILE, invocation=invocation, clock=clock,
        tenure=TenurePolicy(), liveness=LivenessPolicy(), monitor=MonitorPolicy(60), timer=timer or Timer(),
        operators=(OperatorGrant("director", "authority-1", OBJECTIVE),),
        resolvers=(ResolverGrant("director", JUDGE, OBJECTIVE, revision(), "verifier"),),
        required_authority=JUDGE, activation=spy)


def begin(p):
    return p.episode.episodes.begin(OBJECTIVE, actor="director", provider="claude", model="model-1",
                                    authority="authority-1", objective_revision="rev-1")


def open_first(root, clock, **options):
    """Epoch 1: the dispatcher stand-in grants liveness authority, the canonical lifecycle
    stand-in enters the VERIFY generation, monitor and reconciler start, the episode begins."""
    p = compose(root, clock, "coordinator-epoch-1", **options)
    version, _ = p.liveness.store.read_state(PROFILE, DISPATCH)
    p.liveness.store.commit(PROFILE, DISPATCH, version, {"schema_version": 1, "active": True, "epoch": 1,
                            "invocation": "dispatcher-1", "expires_at": T0 / SECOND + 10 ** 6})
    p.liveness.journal.enter(known())
    p.monitor.monitor.start()
    p.liveness.reconciler.start()
    record = begin(p)
    assert (record.epoch, str(record.state)) == (1, "ACTIVE")
    return p


def scan(p, clock, now):
    clock.now = now
    p.monitor.monitor.tick()
    return p.liveness.reconciler.scan()


def kinds(report):
    return [e.kind for e in report.events]


def consumers(p):
    """Every durable guarded consumer outcome in the liveness store: the effective actions taken."""
    return [s for _, _, s in p.liveness.store.list_states(PROFILE, '__fenced__:["consumer",')]


def result(p, action, effect, *, epoch=None, invocation=None):
    from alienintent.control_plane.ports.episode import CoordinatorResult
    record = p.episode.repository.load(OBJECTIVE)[1]
    pointer = p.episode.context.pin()
    view = p.episode.context.reconstruct(pointer)
    return CoordinatorResult(OBJECTIVE, OBJECTIVE, record.epoch if epoch is None else epoch,
                             record.invocation if invocation is None else invocation, pointer, action,
                             view.document["lifecycle"][OBJECTIVE]["version"], effect)


def snapshot(root):
    """Durable state of every composed store: every row of every table (aggregates, effects, receipts,
    reservations, fences) plus every file of every evidence repository under the profile root."""
    rows = {}
    for name in STORES:
        if (root / name).exists():
            with sqlite3.connect(root / name) as connection:
                tables = [t for (t,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1")]
                rows[name] = {t: connection.execute(f'SELECT * FROM "{t}" ORDER BY 1').fetchall() for t in tables}
    rows["evidence"] = sorted((str(f.relative_to(root)), f.read_bytes()) for f in root.glob("*-evidence/**/*") if f.is_file())
    return rows


def store_rows(root, name, table):
    return snapshot(root)[name][table]


def authorized_view(manifest_ref, document, document_digest):
    return json.loads(json.dumps({
        "manifest_ref": manifest_ref, "digest": document_digest,
        **{key: document[key] for key in ("authorized_next_action_set", "blocked_set", "pending_attention", "lifecycle")}}))


def reconstruct(p):
    pointer = p.episode.context.pin()
    view = p.episode.context.reconstruct(pointer)
    return authorized_view(view.manifest_ref, view.document, view.digest)


INDEPENDENT = r"""
import json, sys
from pathlib import Path
from alienintent.composition.control_plane_profile import ContextProfile
from alienintent.context_assembly.domain.reconstruction import digest
context = ContextProfile(Path(sys.argv[1]), project="project", name="fixture", invocation="fx-c-independent").context
reference = context.pin()
document = dict(context.reconstruct(reference).document)
print(json.dumps({"manifest_ref": reference, "digest": digest(document), **{k: document[k] for k in
      ("authorized_next_action_set", "blocked_set", "pending_attention", "lifecycle")}}))
"""


def reconstruct_independently(root):
    """A separate OS process with no memory of any episode: it shares only the durable store."""
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1",
                   "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
    child = subprocess.run([sys.executable, "-B", "-c", INDEPENDENT, str(root)], cwd=ROOT, env=environment,
                           text=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=120)
    assert child.returncode == 0, child.stderr
    return json.loads(child.stdout)


def judgment_items(attention):
    return [i for i in attention.list_pending() if i.origin.work_ref == OBJECTIVE]


def works(entries):
    return {entry["work"] for entry in entries}


def run_monitor(p, clock, until):
    """The composed service loop under fake time: one tick and one scan every I."""
    reports = []
    while clock.now + I <= until:
        reports.append(scan(p, clock, clock.now + I))
    return reports


# ---- class 1 + class 4: episode end during duplicate/delayed outcomes -------------------------

def test_episode_end_during_duplicate_and_delayed_outcomes(world):
    """A fresh context reconstructs identical authorized actions, one effect/readback survives the
    episode end, and the stale epoch cannot send."""
    from alienintent.control_plane.ports.episode import Admitted, Refused
    clock = Clock()
    first = open_first(world, clock)
    effect = verifier_effect()
    assert kinds(scan(first, clock, T0 + G - 10 * SECOND)) == ["liveness.no_action"]
    ended_view = reconstruct(first)
    assert {("item-verify", "review"), ("item-verify", "rework")} <= \
        {(a["work"], a["action"]) for a in ended_view["authorized_next_action_set"]}
    # In flight at the end: the epoch-1 coordinator's computed result and its dispatched verifier.
    delayed_result = result(first, "review", "coordinator:review-epoch-1")
    clock.now = T0 + G - 5 * SECOND
    lifecycle, _ = first.liveness.store.read_state(PROFILE, "liveness-active:" + OBJECTIVE)
    in_flight = first.liveness.admission.intend(known(), lifecycle, effect, "original-delivery:coordinator-epoch-1")
    assert type(in_flight).__name__ == "Intent", in_flight
    clock.now = T0 + G - 4 * SECOND
    ended = first.episode.episodes.end(OBJECTIVE, epoch=1, actor="director")
    assert (str(ended.state), str(ended.cause)) == ("ENDED", "EXPLICIT_REQUEST")
    assert str(first.monitor.monitor.inspect().status) == "HEALTHY", "monitor operation continues after the episode ends"

    # Duplicate and delayed outcomes arrive after the end.
    report = scan(first, clock, T0 + G)
    assert (kinds(report), report.events[0].reason) == (["liveness.no_action"], "PENDING_EFFECT"), \
        "a duplicate recovery during the episode end must not create a second intent"
    duplicate = first.liveness.admission.admit(known(), lifecycle, effect, "original-delivery:duplicate")
    assert (type(duplicate).__name__, duplicate.reason) == ("Refused", "RESERVED")
    before = snapshot(world)
    late = first.episode.episodes.submit(delayed_result)
    assert isinstance(late, Refused) and late.reason == "NOT_ACTIVE", "the ended epoch cannot send its delayed result"
    assert snapshot(world) == before, "a refused stale-epoch result writes nothing in any composed store"
    assert consumers(first) == [] and "coordinator:review-epoch-1" not in \
        [row[1] for row in store_rows(world, "attention.sqlite", "effects")], "the delayed result was never sent"

    # The coordinator context is discarded; a fresh context shares only the durable stores.
    del first
    gc.collect()
    clock.now = T0 + G + C
    fresh = compose(world, clock, "coordinator-epoch-2")
    fresh_view = reconstruct(fresh)
    assert fresh_view == ended_view == reconstruct_independently(world), \
        "a fresh context reconstructs the identical authorized bounded-control state"

    # The fresh context reopens the admitted intent by canonical claim; nothing is cancelled or re-created.
    fresh.monitor.monitor.start()
    reopened = fresh.liveness.reconciler.start()
    assert [(type(r).__name__, r.effect_key, r.source) for r in reopened] == [("Admitted", effect.effect_key, "readback")]
    delivered = fresh.liveness.admission.deliver(in_flight, "original-delivery:coordinator-epoch-1")
    assert type(delivered).__name__ == "Held" and delivered.reason.startswith("DELIVERY_REFUSED"), \
        "the delayed original delivery cannot act after the fenced completion"
    again = fresh.liveness.admission.admit(known(), lifecycle, effect, "original-delivery:late")
    assert (type(again).__name__, again.reason) == ("Refused", "EFFECT_IDENTITY_USED")
    report = scan(fresh, clock, T0 + G + C + SECOND)
    assert (kinds(report), report.events[0].reason) == (["liveness.no_action"], "COMPLETED_AWAITING_PROJECTION")
    assert report.bound_claim == "G_PLUS_I_CLAIMED"
    records = consumers(fresh)
    assert len(records) == 1, "exactly one effective authorized action across the episode end and restart"
    receipt = fresh.liveness.store.readback_guarded(PROFILE, effect.effect_key)
    assert receipt is not None and (receipt.effect_id, receipt.invocation) == (effect.effect_key, "dispatcher-1")
    assert fresh.liveness.store.pending_effects(PROFILE) == () == fresh.liveness.store.unresolved_effects(PROFILE)
    assert fresh.liveness.store.recovery_reservations(PROFILE) == ()

    # A new epoch is an explicit authorized begin over the same reconstructed context.
    record = begin(fresh)
    assert (record.epoch, record.epochs, record.admitted_total) == (2, 2, 0)
    assert (record.manifest_ref, record.context_digest) == (fresh_view["manifest_ref"], fresh_view["digest"])
    straggler = compose(world, clock, "coordinator-epoch-1")
    forged = result(fresh, "review", "coordinator:forged")
    before = snapshot(world)
    for sender, attempt in ((fresh, delayed_result), (straggler, delayed_result), (straggler, forged)):
        outcome = sender.episode.episodes.submit(attempt)
        assert isinstance(outcome, Refused) and outcome.reason == "STALE_EPOCH", "a stale epoch cannot send"
    assert snapshot(world) == before, "epoch 2 state is byte-equal after every stale-epoch attempt"
    sent = [row[1] for row in store_rows(world, "attention.sqlite", "effects")]
    assert not {"coordinator:review-epoch-1", "coordinator:forged"} & set(sent), "no stale-epoch effect was sent"
    current = fresh.episode.episodes.submit(result(fresh, "review", "coordinator:review-epoch-2"))
    assert isinstance(current, Admitted) and current.delivery == "CONFIRMED", \
        "the reconstructed action is exactly what the current epoch may send"


# ---- class 2: durable attention survives and completed judgment suppresses recovery -----------

def test_judgment_attention_survives_episode_end_and_suppresses_recovery(world):
    from tests.execution_coordination.test_liveness_reconciliation import recorded_resolution
    from alienintent.control_plane.ports.episode import Refused
    from alienintent.execution_coordination.domain.liveness import CorrelatedOutcome
    clock, timer, spy = Clock(), Timer(), LaunchSpy()
    first = open_first(world, clock, timer=timer, spy=spy)
    unjudged = reconstruct(first)
    # The verifier ran outside the fenced journal; its judgment outcome is observed twice.
    clock.now = T0 + 10 * SECOND
    outcome = CorrelatedOutcome("verifier-outcome-1", OBJECTIVE, 1, "verifier", "HUMAN_DECISION_REQUIRED", 1)
    for _ in range(2):
        first.liveness.journal.record_outcome(outcome)
    reports = [scan(first, clock, T0 + G), scan(first, clock, T0 + G + I)]
    assert [kinds(r) for r in reports] == [["liveness.suppressed"]] * 2
    (item,) = judgment_items(first.liveness.judgment.attention)
    assert (item.origin.kind, item.origin.event_identity, item.origin.lane) == ("JUDGMENT", "verifier-outcome-1", "verifier")
    assert [r.events[0].attention for r in reports] == [item.identity] * 2, "duplicate observation keeps one item identity"
    judged = reconstruct(first)
    assert item.identity in [a["identity"] for a in judged["pending_attention"]], \
        "judgment attention must be durable in the store every fresh context reconstructs"
    assert OBJECTIVE in works(judged["blocked_set"]) and OBJECTIVE not in works(judged["authorized_next_action_set"])

    # The episode observes the judgment block; the injected timer ends tenure at the blocked limit.
    blocked = first.episode.episodes.tick(OBJECTIVE)
    assert blocked.blocked_since_us == T0 + G + I and (OBJECTIVE, 1, T0 + G + I + 300 * SECOND) in timer.armed
    run_monitor(first, clock, T0 + G + I + 240 * SECOND)
    clock.now = T0 + G + I + 300 * SECOND - 1
    assert str(first.episode.episodes.tick(OBJECTIVE).state) == "ACTIVE", "just below the blocked limit tenure holds"
    clock.now = T0 + G + I + 300 * SECOND
    ended = first.episode.episodes.tick(OBJECTIVE)
    assert (str(ended.state), str(ended.cause)) == ("ENDED", "BLOCKED_LIMIT")
    after_end = scan(first, clock, clock.now + I)
    assert kinds(after_end) == ["liveness.suppressed"] and after_end.bound_claim == "G_PLUS_I_CLAIMED", \
        "monitor and liveness operation continue after the model episode ends"

    del first
    gc.collect()
    clock.now = T0 + 3 * G
    fresh = compose(world, clock, "coordinator-epoch-2", spy=spy)
    assert [i.identity for i in judgment_items(fresh.attention.attention)] == [item.identity], \
        "attention survives restart with its identity"
    assert reconstruct(fresh) == judged == reconstruct_independently(world), \
        "the fresh context reconstructs the judged state the ended episode saw, including the pending item"
    fresh.monitor.monitor.start()
    fresh.liveness.reconciler.start()
    for n in (3, 5, 20, 100):
        report = scan(fresh, clock, T0 + n * G)
        assert kinds(report) == ["liveness.suppressed"] and report.events[0].attention == item.identity, \
            "completed judgment suppresses recovery after the episode ended and the context restarted"
    assert consumers(fresh) == [], "no relaunch after any number of grace periods"
    assert [i.identity for i in judgment_items(fresh.attention.attention)] == [item.identity]

    # The next epoch reconstructs the same block and cannot act on the judged item.
    record = begin(fresh)
    assert record.epoch == 2 and record.blocked_since_us == clock.now
    refused = fresh.episode.episodes.submit(result(fresh, "review", "coordinator:review-while-judged"))
    assert isinstance(refused, Refused) and refused.reason == "AUTHORITY_REFUSED"

    # A valid matching resolution permits reinspection only; it never relaunches.
    service = fresh.attention.attention
    service.resolve(item.identity, recorded_resolution(fresh.liveness, service.show(item.identity)))
    report = scan(fresh, clock, clock.now + I)
    assert (kinds(report), report.events[0].reason) == (["liveness.no_action"], "COMPLETED_AWAITING_PROJECTION")
    assert consumers(fresh) == []
    resolved = reconstruct(fresh)
    assert resolved["authorized_next_action_set"] == unjudged["authorized_next_action_set"], \
        "resolution restores the identical authorized actions"
    assert spy.count == 0, "no model launch anywhere in the composed path"


# ---- class 3: stopped/stale/degraded monitor evidence is never a healthy claim ----------------

def test_stopped_scans_surface_stale_or_degraded_never_healthy(world):
    from alienintent.execution_coordination.ports.operational_store import StoreUnavailable
    clock = Clock()
    first = open_first(world, clock)
    assert [r.bound_claim for r in run_monitor(first, clock, T0 + 2 * I)] == ["G_PLUS_I_CLAIMED"] * 2
    clock.now += SECOND
    first.episode.episodes.end(OBJECTIVE, epoch=1, actor="director")
    assert scan(first, clock, T0 + 3 * I).bound_claim == "G_PLUS_I_CLAIMED", "the monitor survives the ended episode"

    # The old context's ticker and scanner stop with it.
    del first
    gc.collect()
    clock.now = T0 + 5 * I + SECOND
    fresh = compose(world, clock, "coordinator-epoch-2")
    before = snapshot(world)
    health = fresh.monitor.monitor.inspect()
    assert (str(health.status), health.reason) == ("STALE", "TICK_OVERDUE"), "a stopped monitor surfaces STALE"
    assert snapshot(world) == before, "inspection is read-only"
    fresh.liveness.reconciler.start()
    unrecorded = fresh.liveness.reconciler.scan()
    assert unrecorded.bound_claim.startswith("WITHDRAWN:PROGRESS_UNRECORDED:"), unrecorded.bound_claim

    # Restart a monitor generation; its ticker then stops while scans keep running.
    restarted = fresh.monitor.monitor.start()
    assert restarted.generation == 2
    assert scan(fresh, clock, clock.now + SECOND).bound_claim == "G_PLUS_I_CLAIMED"
    clock.now += 2 * I + SECOND
    stopped_ticks = fresh.liveness.reconciler.scan()
    assert stopped_ticks.outcome == "COMPLETE"
    assert stopped_ticks.bound_claim == "WITHDRAWN:STALE:TICK_OVERDUE", \
        "a scan must never claim G+I while the monitor's ticks have stopped"

    # A failed scan and a scan that never finishes are DEGRADED; stopped scans become STALE.
    fresh.monitor.monitor.tick()
    reconciler = fresh.liveness.reconciler
    def unavailable():
        raise StoreUnavailable("injected: known-active store unavailable")
    reconciler.known_active = unavailable
    failed = reconciler.scan()
    assert (failed.outcome, failed.bound_claim) == ("FAILED", "WITHDRAWN:DEGRADED:SCAN_FAILED")
    del reconciler.known_active
    clock.now += SECOND
    fresh.monitor.monitor.scan_started()  # the scanner dies mid-scan
    health = fresh.monitor.monitor.inspect()
    assert (str(health.status), health.reason) == ("DEGRADED", "SCAN_STARTED")
    for _ in range(3):
        clock.now += I
        fresh.monitor.monitor.tick()
    health = fresh.monitor.monitor.inspect()
    assert (str(health.status), health.reason) == ("STALE", "SCAN_OVERDUE"), "stopped scans surface STALE"
    assert fresh.liveness.reconciler.bound_claim() == "WITHDRAWN:STALE:SCAN_OVERDUE"
    recovered = scan(fresh, clock, clock.now + SECOND)
    assert (recovered.outcome, recovered.bound_claim) == ("COMPLETE", "G_PLUS_I_CLAIMED"), \
        "only a fresh tick and a completed scan restore health"


# ---- composition boundary ---------------------------------------------------------------------

def test_constructing_the_composition_starts_nothing(world):
    from alienintent.composition.bounded_control_profile import BoundedControlProfile
    from alienintent.control_plane.domain.episode import TenurePolicy
    from alienintent.control_plane.domain.monitor_health import MonitorHold
    from alienintent.execution_coordination.domain.liveness import LivenessHold, LivenessPolicy
    clock = Clock()
    seeded = snapshot(world)
    p = compose(world, clock, "coordinator-epoch-1")
    constructed = snapshot(world)
    assert set(seeded) == {"attention.sqlite", "evidence"}
    assert (constructed["attention.sqlite"], constructed["evidence"]) == (seeded["attention.sqlite"], seeded["evidence"])
    assert all(not any(rows for table, rows in constructed[name].items() if table != "operational_schema")
               for name in ("liveness.sqlite", "monitor.sqlite")), "constructing opens the stores and writes nothing"
    assert p.episode.repository.load(OBJECTIVE) == (0, None) and not p.liveness.reconciler.started
    health = p.monitor.monitor.inspect()
    assert (str(health.status), health.reason) == ("UNVERIFIED", "NO_RECORD")
    # Missing policy blocks startup: liveness at construction, the monitor at start.
    options = dict(project="project", name=PROFILE, invocation="coordinator-epoch-1", clock=clock,
                   tenure=TenurePolicy(), timer=Timer(), operators=(), resolvers=(), required_authority=JUDGE)
    with pytest.raises(LivenessHold, match="POLICY_MISSING"):
        BoundedControlProfile(world, liveness=None, monitor=None, **options)
    with pytest.raises(MonitorHold, match="POLICY_MISSING"):
        BoundedControlProfile(world, liveness=LivenessPolicy(), monitor=None, **options).monitor.monitor.start()
    assert snapshot(world) == constructed
