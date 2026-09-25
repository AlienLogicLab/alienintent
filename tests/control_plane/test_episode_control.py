"""FX-C3 (SF-REQ-053-AC-02/AC-03): bounded episodes and stale-command refusal.

Real durable SQLite store and S1 evidence over the FX-C2 seed; injected integer-microsecond
clocks, timer and usage source; no provider, model, network or host. The scripted usage source
is a labelled local substitute (U-8) and does not close LRN-023.
"""
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SECOND = 1_000_000
T0 = 1_790_000_000 * SECOND
OBJECTIVE = "item-verify"
BLOCKED = "item-blocked"
CYCLE = ("review", "rework", "verify")


class Clocks:
    """Injected UTC anchor (read once per process) and monotonic microseconds."""

    def __init__(self, utc=T0, mono=0):
        self.utc, self.mono = utc, mono


class Timer:
    def __init__(self):
        self.armed = []

    def arm(self, objective, epoch, deadline_us):
        self.armed.append((objective, epoch, deadline_us))


class LaunchSpy:
    count = 0

    def launch(self, *_):
        self.count += 1
        raise AssertionError("no model launch permitted")


class ScriptedUsage:
    """LOCAL_SUBSTITUTE_USAGE_SOURCE: a scripted same-invocation evidence adapter (U-8)."""

    def __init__(self, mode, used=1.0, limit=10.0):
        self.mode, self.used, self.limit, self.calls = mode, used, limit, []

    def read(self, invocation_id, check_id):
        from alienintent.control_plane.domain.episode import Unavailable, Usage
        self.calls.append((invocation_id, check_id))
        if self.mode == "unavailable":
            return Unavailable("injected: source unavailable")
        if self.mode == "prior_check":
            return Usage(invocation_id, "check:0:0", self.used, self.limit)
        if self.mode == "wrong_invocation":
            return Usage("another-invocation", check_id, self.used, self.limit)
        return Usage(invocation_id, check_id, self.used, self.limit)


def grants():
    from alienintent.control_plane.domain.episode import OperatorGrant
    return tuple(OperatorGrant("director", "authority-1", o) for o in (OBJECTIVE, BLOCKED, "item-implement"))


def episode_profile(root, clocks, *, invocation="fx-c3-a", policy=None, usage=None, timer=None):
    from alienintent.composition.control_plane_profile import EpisodeProfile
    from alienintent.control_plane.domain.episode import TenurePolicy
    return EpisodeProfile(root, project="project", name="fixture", invocation=invocation,
                          monotonic=lambda: clocks.mono, utc_clock=lambda: clocks.utc, timer=timer or Timer(),
                          policy=policy or TenurePolicy(), usage=usage, operators=grants())


def start(profile, objective=OBJECTIVE):
    return profile.episodes.begin(objective, actor="director", provider="claude", model="model-1",
                                  authority="authority-1", objective_revision="rev-1")


@pytest.fixture
def world(tmp_path):
    from tests.context_assembly.test_context_reconstruction import seed
    root = tmp_path / "profile"
    root.mkdir()
    seed(root)
    return root


def result(profile, action, effect, *, objective=OBJECTIVE, work=None, epoch=None, invocation=None):
    from alienintent.control_plane.ports.episode import CoordinatorResult
    from tests.context_assembly.test_context_reconstruction import candidate
    record = profile.repository.load(objective)[1]
    pointer = profile.context.pin()
    view = profile.context.reconstruct(pointer)
    work = work or objective
    return CoordinatorResult(objective, work, record.epoch if epoch is None else epoch,
                             record.invocation if invocation is None else invocation, pointer, action,
                             view.document["lifecycle"][work]["version"], effect,
                             candidate() if action == "verify" else None)


def snapshot(root):
    """Byte-level operational state: every aggregate and effect row."""
    with sqlite3.connect(root / "attention.sqlite") as connection:
        aggregates = connection.execute("SELECT profile, identity, version, state FROM aggregates ORDER BY 1, 2").fetchall()
        effects = connection.execute("SELECT * FROM effects ORDER BY 1, 2").fetchall()
    return aggregates, effects


def record_of(profile, objective=OBJECTIVE):
    return profile.repository.load(objective)[1]


def assert_ended(profile, root, cause, objective=OBJECTIVE):
    """Ended with the exact cause; the same epoch's next result is refused with no store mutation."""
    from alienintent.control_plane.ports.episode import Refused
    record = record_of(profile, objective)
    assert (str(record.state), str(record.cause)) == ("ENDED", cause), f"expected ENDED {cause}, got {record.state} {record.cause}"
    attempt = result(profile, "review" if objective == OBJECTIVE else "verify", "after-end", objective=objective)
    before = snapshot(root)
    outcome = profile.episodes.submit(attempt)
    assert isinstance(outcome, Refused) and outcome.reason == "NOT_ACTIVE", outcome
    assert snapshot(root) == before, "an expired episode must not make authoritative changes"


def admit(profile, count, *, start_index=0):
    from alienintent.control_plane.ports.episode import Admitted
    outcomes = []
    for index in range(start_index, start_index + count):
        outcomes.append(profile.episodes.submit(result(profile, CYCLE[index % 3], f"effect-{index}")))
    assert all(isinstance(o, Admitted) for o in outcomes), outcomes
    return outcomes


def last_event(profile, objective=OBJECTIVE):
    return profile.repository.history(objective)[-1]["event"]


# -- numeric limits (U-2: reaching ends) --------------------------------------------------------

@pytest.mark.parametrize("case", ["below", "at"])
def test_age_limit(world, case):
    clocks = Clocks()
    profile = episode_profile(world, clocks)
    start(profile)
    clocks.mono = 3600 * SECOND - (1 if case == "below" else 0)
    profile.episodes.tick(OBJECTIVE)
    if case == "below":
        assert str(record_of(profile).state) == "ACTIVE", "one microsecond below 3600 s the episode stays ACTIVE"
    else:
        assert_ended(profile, world, "AGE_LIMIT")


@pytest.mark.parametrize("count", [31, 32, 33])
def test_transition_limit(world, count):
    from alienintent.control_plane.ports.episode import Refused
    profile = episode_profile(world, Clocks())
    start(profile)
    admit(profile, min(count, 32))
    record = record_of(profile)
    if count == 31:
        assert (str(record.state), record.transitions) == ("ACTIVE", 31), "31 admitted transitions stay ACTIVE"
        return
    assert record.transitions == 32 and str(record.cause) == "TRANSITION_LIMIT", "the 32nd admission reaches the limit"
    if count == 33:
        attempt = result(profile, CYCLE[32 % 3], "effect-32")
        before = snapshot(world)
        outcome = profile.episodes.submit(attempt)
        assert isinstance(outcome, Refused) and outcome.reason == "NOT_ACTIVE", "the 33rd result is refused"
        assert snapshot(world) == before


@pytest.mark.parametrize("case", ["below", "at"])
def test_blocked_limit(world, case):
    clocks = Clocks()
    profile = episode_profile(world, clocks)
    record = start(profile, BLOCKED)
    assert record.blocked_since_us == T0, "U-3: the objective's own item is blocked with no authorized action"
    clocks.mono = 300 * SECOND - (1 if case == "below" else 0)
    profile.episodes.tick(BLOCKED)
    if case == "below":
        assert str(record_of(profile, BLOCKED).state) == "ACTIVE", "just below 300 s blocked stays ACTIVE"
    else:
        assert_ended(profile, world, "BLOCKED_LIMIT", BLOCKED)


def test_unblock_resets_only_blocked_interval():
    from alienintent.control_plane.domain.episode import EpisodeRecord, blocked, next_blocked_since
    document = {"blocked_set": [{"work": "a"}], "authorized_next_action_set": [{"work": "b"}]}
    assert blocked(document, "a") and not blocked(document, "b")
    fields = {f: 0 for f in EpisodeRecord.__dataclass_fields__}
    record = EpisodeRecord(**{**fields, "blocked_since_us": 5, "transitions": 7})
    assert next_blocked_since(record, True, 9) == 5 and next_blocked_since(record, False, 9) is None
    assert replace(record, blocked_since_us=None).transitions == 7


def test_one_bius_only(world):
    from alienintent.control_plane.ports.episode import Refused
    profile = episode_profile(world, Clocks())
    start(profile)
    attempt = result(profile, "verify", "second-biu", work="item-implement")
    before = snapshot(world)
    outcome = profile.episodes.submit(attempt)
    assert isinstance(outcome, Refused) and outcome.reason == "ONE_BIU"
    assert snapshot(world) == before and record_of(profile).objective == OBJECTIVE


# -- immediate causes (U-5, U-6) ----------------------------------------------------------------

@pytest.mark.parametrize("case", ["terminal", "objective", "authority", "provider", "model", "explicit", "context_exhausted"])
def test_immediate_end(world, case):
    profile = episode_profile(world, Clocks())
    record = start(profile)
    episodes = profile.episodes
    changes = {"objective": "rev-2", "authority": "authority-2", "provider": "codex", "model": "model-2"}
    if case in changes:
        episodes.observe(OBJECTIVE, case, changes[case])
    elif case == "explicit":
        episodes.end(OBJECTIVE, epoch=record.epoch, actor="director")
    else:
        episodes.signal(OBJECTIVE, case, "durable-event:1")
    expected = {"terminal": "TERMINAL_OUTCOME", "objective": "OBJECTIVE_CHANGE", "authority": "AUTHORITY_CHANGE",
                "provider": "PROVIDER_CHANGE", "model": "MODEL_CHANGE", "explicit": "EXPLICIT_REQUEST",
                "context_exhausted": "CONTEXT_EXHAUSTED"}[case]
    assert_ended(profile, world, expected)


def test_unchanged_identity_and_uncheckable_source(world):
    from alienintent.control_plane.domain.episode import EpisodeHold
    profile = episode_profile(world, Clocks())
    start(profile)
    profile.episodes.observe(OBJECTIVE, "provider", "claude")
    assert str(record_of(profile).state) == "ACTIVE", "the bound identity is not a change"
    with pytest.raises(EpisodeHold) as hold:
        profile.episodes.observe(OBJECTIVE, "authority", None)
    assert hold.value.reason == "SOURCE_UNCHECKABLE"


# -- state vector and competing results (AC-03) -------------------------------------------------

def test_state_vector_mismatch(world):
    from alienintent.control_plane.ports.episode import Refused
    profile = episode_profile(world, Clocks())
    start(profile)
    attempt = result(profile, "review", "stale-effect")
    version, inbox = profile.store.read_state("fixture", "decision-inbox")
    profile.store.commit("fixture", "decision-inbox", version, {"open": {}})  # a newer authoritative change
    newer = profile.store.read_state("fixture", "decision-inbox"), profile.store.read_state("fixture", "factory:" + OBJECTIVE)
    outcome = profile.episodes.submit(attempt)
    assert isinstance(outcome, Refused) and outcome.reason == "STALE_VECTOR" and "decision-inbox" in outcome.detail
    assert str(record_of(profile).cause) == "STALE_VECTOR"
    assert (profile.store.read_state("fixture", "decision-inbox"),
            profile.store.read_state("fixture", "factory:" + OBJECTIVE)) == newer, "newer state is byte-equal"


def test_obsolete_revision_refused(world):
    from alienintent.control_plane.ports.episode import Admitted, Refused
    from alienintent.execution_coordination.ports.fenced_store import GuardVector
    from alienintent.execution_coordination.ports.operational_store import Reservation, VersionConflict
    profile = episode_profile(world, Clocks())
    start(profile)
    current, obsolete = result(profile, "review", "effect-current"), result(profile, "rework", "effect-obsolete")
    assert isinstance(profile.episodes.submit(current), Admitted)
    target = "factory:" + OBJECTIVE
    # The S2 fence refuses the obsolete vector independently of the episode service.
    record = record_of(profile)
    entries = profile.context.entries(obsolete.manifest_ref)
    vector = GuardVector((*entries, (record.aggregate, profile.repository.load(OBJECTIVE)[0])), record.aggregate,
                         record.epoch, record.invocation)
    with pytest.raises(VersionConflict):
        profile.store.commit_guarded("fixture", target, dict(entries)[target], vector, (Reservation(*record.reservation),),
                                     {"stage": "IMPLEMENT"}, "effect-direct", {})
    newer = snapshot(world)
    outcome = profile.episodes.submit(obsolete)
    assert isinstance(outcome, Refused) and outcome.reason == "STALE_VECTOR", outcome
    after = snapshot(world)
    assert [r for r in after[0] if r[1] == target] == [r for r in newer[0] if r[1] == target], "no overwrite of newer state"
    assert after[1] == newer[1] and not [e for e in after[1] if e[1] == "effect-obsolete"], "no effect row"


@pytest.mark.parametrize("case", ["blocked_item", "unoffered_action"])
def test_current_revision_still_authority_checked(world, case):
    from alienintent.control_plane.ports.episode import Refused
    profile = episode_profile(world, Clocks())
    objective = BLOCKED if case == "blocked_item" else OBJECTIVE
    start(profile, objective)
    attempt = result(profile, "verify" if case == "blocked_item" else "accept", "effect-authority", objective=objective)
    before = snapshot(world)
    outcome = profile.episodes.submit(attempt)
    assert isinstance(outcome, Refused) and outcome.reason == "AUTHORITY_REFUSED", \
        "a current-revision result still requires authority"
    assert snapshot(world)[1] == before[1] and [r for r in snapshot(world)[0] if r[1].startswith("factory:")] == \
        [r for r in before[0] if r[1].startswith("factory:")], "no mutation"
    assert str(record_of(profile, objective).state) == "ACTIVE"


def _run(*argv):
    environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONDONTWRITEBYTECODE": "1",
                   "PYTHONPATH": os.pathsep.join((str(ROOT / "src"), str(ROOT)))}
    completed = subprocess.run([sys.executable, "-B", "-m", "tests.control_plane.episode_process", *argv], cwd=ROOT,
                               env=environment, text=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=120)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_competing_epochs_cannot_overwrite(world):
    common = ("--root", str(world))
    first = _run("begin", *common, "--invocation", "fx-c3-epoch-1", "--utc", str(T0), "--action", "review",
                 "--effect", "effect-epoch-1")
    second = _run("renew", *common, "--invocation", "fx-c3-epoch-2", "--utc", str(T0 + SECOND), "--action", "rework",
                  "--effect", "effect-epoch-2")
    assert (first["record"]["epoch"], second["record"]["epoch"]) == (1, 2)
    before = snapshot(world)
    stale = _run("submit", *common, "--invocation", "fx-c3-epoch-1", "--utc", str(T0 + 2 * SECOND),
                 "--result", json.dumps(first["result"]))
    assert (stale.get("outcome"), stale.get("reason")) == ("REFUSED", "STALE_EPOCH"), stale
    assert snapshot(world) == before, "epoch n+1 state is byte-equal after the epoch-n result"
    current = _run("submit", *common, "--invocation", "fx-c3-epoch-2", "--utc", str(T0 + 3 * SECOND),
                   "--result", json.dumps(second["result"]))
    assert current["outcome"] == "ADMITTED", current
    # The S2 authority fence refuses the old epoch on its own as well.
    from alienintent.execution_coordination.adapters.sqlite_store import SQLiteOperationalStore
    from alienintent.execution_coordination.ports.fenced_store import GuardVector
    from alienintent.execution_coordination.ports.operational_store import Reservation, ReservationRejected
    store = SQLiteOperationalStore(world / "attention.sqlite", clock=lambda: (T0 + 4 * SECOND) / SECOND)
    version = store.read_state("fixture", "episode:" + OBJECTIVE)[0]
    target = store.read_state("fixture", "factory:" + OBJECTIVE)[0]
    vector = GuardVector(((f"episode:{OBJECTIVE}", version), (f"factory:{OBJECTIVE}", target)), f"episode:{OBJECTIVE}",
                         1, "fx-c3-epoch-1")
    reservation = Reservation(*second["record"]["reservation"])
    with pytest.raises(ReservationRejected, match="inactive or mismatched epoch/authority|reservation"):
        store.commit_guarded("fixture", f"factory:{OBJECTIVE}", target, vector,
                             (replace(reservation, owner="fx-c3-epoch-1"),), {}, "effect-old-direct", {})


# -- contradiction judgments (operator-owned; admission only) ----------------------------------

@pytest.mark.parametrize("case", ["accepted", "stale_epoch", "stale_vector", "unauthorized", "missing_refs",
                                  "unresolvable_ref", "empty_rationale"])
def test_contradiction(world, case):
    from alienintent.control_plane.domain.episode import AcceptedContradiction, ContradictionJudgment, InvalidJudgment
    profile = episode_profile(world, Clocks())
    start(profile)
    judgment = ContradictionJudgment("director", OBJECTIVE, 1, profile.episodes.vector_digest(OBJECTIVE),
                                     ("factory:" + OBJECTIVE, "decision-inbox"),
                                     "the release record and the factory record authorize conflicting actions",
                                     ("fixture:operator-note-1",))
    if case == "stale_vector":
        profile.episodes.tick(OBJECTIVE)
    judgment = {"accepted": judgment, "stale_vector": judgment,
                "stale_epoch": replace(judgment, epoch=2), "unauthorized": replace(judgment, actor="intruder"),
                "missing_refs": replace(judgment, conflicting_refs=()),
                "unresolvable_ref": replace(judgment, conflicting_refs=("factory:no-such-item",)),
                "empty_rationale": replace(judgment, rationale="  ")}[case]
    outcome = profile.episodes.record(judgment)
    if case == "accepted":
        assert isinstance(outcome, AcceptedContradiction)
        assert_ended(profile, world, "CONTRADICTION")
        return
    assert outcome == InvalidJudgment(case.upper()), f"expected InvalidJudgment({case.upper()}), got {outcome}"
    record = record_of(profile)
    assert (str(record.state), record.accepted_contradictions) == ("ACTIVE", 0), "an invalid judgment cannot end tenure"


# -- context usage ------------------------------------------------------------------------------

def test_usage_unbound(world):
    from alienintent.control_plane.domain.episode import TenurePolicy
    clocks = Clocks()
    profile = episode_profile(world, clocks, policy=TenurePolicy(max_transitions=2))
    record = start(profile)
    assert str(record.usage_binding) == "UNBOUND"
    profile.episodes.tick(OBJECTIVE)
    event = last_event(profile)
    assert (event["usage_binding"], event["usage"], event["usage_detail"]) == ("UNBOUND", None, "UNBOUND"), \
        "UNBOUND is recorded explicitly, never as zero or measured-safe usage"
    assert str(record_of(profile).state) == "ACTIVE", "a missing usage binding alone does not end tenure"
    admit(profile, 2)
    assert str(record_of(profile).cause) == "TRANSITION_LIMIT", "other limits still enforce under UNBOUND"
    aged = episode_profile(world, clocks, invocation="fx-c3-b")
    aged.episodes.begin(OBJECTIVE, actor="director", provider="claude", model="model-1", authority="authority-1",
                        objective_revision="rev-1")
    clocks.mono = 3600 * SECOND
    aged.episodes.tick(OBJECTIVE)
    assert str(record_of(aged).cause) == "AGE_LIMIT", "the age limit still enforces under UNBOUND"


@pytest.mark.parametrize("case", ["below", "at"])
def test_usage_bound_threshold(world, case):
    from alienintent.control_plane.domain.episode import TenurePolicy, UsageBinding
    usage = ScriptedUsage("valid", used=7.999999 if case == "below" else 8.0, limit=10.0)
    profile = episode_profile(world, Clocks(), policy=TenurePolicy(usage=UsageBinding.BOUND), usage=usage)
    start(profile)
    profile.episodes.tick(OBJECTIVE)
    assert usage.calls == [("fx-c3-a", "check:1:1")], "the sample is requested for this invocation and check"
    if case == "below":
        assert str(record_of(profile).state) == "ACTIVE"
    else:
        assert_ended(profile, world, "CONTEXT_USAGE_LIMIT")


@pytest.mark.parametrize("case", ["unavailable", "prior_check", "wrong_invocation", "nan_used", "negative_used",
                                  "zero_limit", "inf_limit"])
def test_usage_bound_invalid(world, case):
    from alienintent.control_plane.domain.episode import TenurePolicy, UsageBinding
    used, limit = {"nan_used": (float("nan"), 10.0), "negative_used": (-1.0, 10.0), "zero_limit": (1.0, 0.0),
                   "inf_limit": (1.0, float("inf"))}.get(case, (1.0, 10.0))
    usage = ScriptedUsage(case if case in {"unavailable", "prior_check", "wrong_invocation"} else "valid", used, limit)
    profile = episode_profile(world, Clocks(), policy=TenurePolicy(usage=UsageBinding.BOUND), usage=usage)
    start(profile)
    profile.episodes.tick(OBJECTIVE)
    cause, detail = {"unavailable": ("CONTEXT_USAGE_UNAVAILABLE", "unavailable"),
                     "prior_check": ("CONTEXT_USAGE_UNAVAILABLE", "prior-check"),
                     "wrong_invocation": ("CONTEXT_USAGE_INVALID", "wrong-invocation"),
                     "nan_used": ("CONTEXT_USAGE_INVALID", "invalid-used"),
                     "negative_used": ("CONTEXT_USAGE_INVALID", "invalid-used"),
                     "zero_limit": ("CONTEXT_USAGE_INVALID", "invalid-limit"),
                     "inf_limit": ("CONTEXT_USAGE_INVALID", "invalid-limit")}[case]
    assert last_event(profile)["usage_detail"] == detail
    assert_ended(profile, world, cause)


def test_policy_validation():
    from alienintent.control_plane.domain.episode import InvalidPolicy, TenurePolicy, UsageBinding
    assert TenurePolicy().document() == {"max_age_s": 3600, "max_transitions": 32, "max_blocked_s": 300,
                                         "max_accepted_contradictions": 1, "usage": "UNBOUND", "threshold": None}
    assert TenurePolicy(usage=UsageBinding.BOUND).threshold == 0.8
    for bad in ({"max_age_s": 0}, {"max_transitions": 1.5}, {"max_blocked_s": True}, {"threshold": 0.8},
                {"usage": "BOUND", "threshold": float("nan")}, {"usage": "BOUND", "threshold": 1.5}, {"usage": "X"}):
        with pytest.raises(InvalidPolicy):
            TenurePolicy(**bad)


def test_bound_policy_requires_source(world):
    from alienintent.control_plane.domain.episode import InvalidPolicy, TenurePolicy, UsageBinding
    with pytest.raises(InvalidPolicy):
        episode_profile(world, Clocks(), policy=TenurePolicy(usage=UsageBinding.BOUND))


# -- timer, clocks, restart ---------------------------------------------------------------------

def test_deadline_timer_independent_of_model(world):
    clocks, timer, spy = Clocks(), Timer(), LaunchSpy()
    profile = episode_profile(world, clocks, timer=timer)
    start(profile)
    assert timer.armed == [(OBJECTIVE, 1, T0 + 3600 * SECOND)], "the injected timer is armed at the persisted deadline"
    clocks.mono = 3600 * SECOND
    profile.episodes.tick(OBJECTIVE)
    assert str(record_of(profile).cause) == "AGE_LIMIT" and spy.count == 0


def test_monotonic_regression_holds(world):
    from alienintent.control_plane.domain.episode import EpisodeHold
    clocks = Clocks(mono=10 * SECOND)
    profile = episode_profile(world, clocks)
    start(profile)
    clocks.mono = 5 * SECOND
    with pytest.raises(EpisodeHold) as hold:
        profile.episodes.tick(OBJECTIVE)
    assert hold.value.reason == "CLOCK_REGRESSION"


@pytest.mark.parametrize("case", ["expired", "regression"])
def test_restart_utc_deadline(world, case):
    common = ("--root", str(world), "--invocation", "fx-c3-a")
    began = _run("begin", *common, "--utc", str(T0 + 10 * SECOND), "--action", "review", "--effect", "effect-restart")
    assert began["record"]["deadline_us"] == T0 + 3610 * SECOND, "the UTC deadline is persisted"
    if case == "expired":
        reopened = _run("tick", *common, "--utc", str(T0 + 3610 * SECOND))
        assert (reopened["record"]["state"], reopened["record"]["cause"]) == ("ENDED", "AGE_LIMIT")
        return
    before = snapshot(world)
    reopened = _run("tick", *common, "--utc", str(T0))
    assert (reopened["status"], reopened.get("reason")) == ("HOLD", "CLOCK_REGRESSION")
    submitted = _run("submit", *common, "--utc", str(T0), "--result", json.dumps(began["result"]))
    assert (submitted["status"], submitted.get("reason")) == ("HOLD", "CLOCK_REGRESSION"), "no admission on regression"
    assert snapshot(world) == before and reopened["record"]["state"] == "ACTIVE"


# -- renewal and replacement --------------------------------------------------------------------

def test_no_automatic_renewal(world):
    from alienintent.control_plane.domain.episode import EpisodeHold
    clocks = Clocks()
    profile = episode_profile(world, clocks)
    record = start(profile)
    profile.episodes.end(OBJECTIVE, epoch=record.epoch, actor="director")
    clocks.mono = 3600 * SECOND
    profile.episodes.tick(OBJECTIVE)
    ended = record_of(profile)
    assert (str(ended.state), ended.epoch) == ("ENDED", 1), "ending never starts a new epoch"
    with pytest.raises(EpisodeHold) as hold:
        profile.episodes.begin(OBJECTIVE, actor="intruder", provider="claude", model="model-1",
                               authority="authority-1", objective_revision="rev-1")
    assert hold.value.reason == "UNAUTHORIZED" and record_of(profile) == ended


def test_renewal_new_epoch_retains_budget(world):
    profile = episode_profile(world, Clocks())
    record = start(profile)
    admit(profile, 2)
    profile.episodes.end(OBJECTIVE, epoch=record.epoch, actor="director")
    renewed = start(profile)
    assert (renewed.epoch, renewed.epochs, renewed.admitted_total, renewed.transitions) == (2, 2, 2, 0), \
        "an authorized new epoch carries budget accounting and never resets it"
    assert renewed.manifest_ref != record.manifest_ref, "the new epoch reconstructs fresh context"


def test_replacement_equivalence(world):
    from alienintent.composition.control_plane_profile import ContextProfile
    predecessor = episode_profile(world, Clocks(), invocation="fx-c3-predecessor")
    first = start(predecessor)
    predecessor.episodes.end(OBJECTIVE, epoch=first.epoch, actor="director")
    del predecessor
    successor = episode_profile(world, Clocks(T0 + SECOND), invocation="fx-c3-successor")
    second = start(successor)
    assert second.manifest_ref == first.manifest_ref, "the same durable state pins the same manifest"
    independent = ContextProfile(world, project="project", name="fixture", invocation="fx-c3-independent")
    reconstructed = independent.context.reconstruct(second.manifest_ref)
    assert first.context_digest == second.context_digest == reconstructed.digest, \
        "the successor reconstructs equal authorized_next_action_set/blocked_set/lifecycle (C2)"


def test_expiry_does_not_cancel_admitted(world):
    from alienintent.control_plane.domain.episode import EpisodeHold
    from alienintent.execution_coordination.ports.operational_store import StoreUnavailable
    profile = episode_profile(world, Clocks())
    record = start(profile)
    def interrupted(*_):
        raise StoreUnavailable("injected: consumer outcome unavailable")
    profile.store.consume_guarded = interrupted
    (admitted,) = admit(profile, 1)
    assert admitted.delivery == "UNKNOWN"
    profile.episodes.end(OBJECTIVE, epoch=record.epoch, actor="director")
    assert [e.identity for e in profile.store.unresolved_effects("fixture")] == ["effect-0"], \
        "the admitted effect stays unknown; nothing fabricates its cancellation"
    reservation = profile.store.recovery_reservations("fixture")
    assert [(r.scope, r.key, r.owner) for r in reservation] == [("episode-work", OBJECTIVE, "fx-c3-a")]
    with pytest.raises(EpisodeHold) as hold:
        start(episode_profile(world, Clocks(), invocation="fx-c3-b"))
    assert hold.value.reason == "RESERVATION_RETAINED"


def test_episode_profile_composed(world):
    from alienintent.evidence_learning.domain.records import ref_from_document
    profile = episode_profile(world, Clocks())
    record = start(profile)
    admit(profile, 1)
    profile.episodes.tick(OBJECTIVE)
    ended = profile.episodes.end(OBJECTIVE, epoch=record.epoch, actor="director")
    version, pointer = profile.store.read_state("fixture", "episode:" + OBJECTIVE)
    assert (pointer["active"], pointer["epoch"], pointer["invocation"], pointer["deadline_utc_us"]) == \
        (False, 1, "fx-c3-a", T0 + 3600 * SECOND)
    history = profile.repository.history(OBJECTIVE)
    assert [h["event"]["action"] for h in history] == ["BEGIN", "CHECK", "ADMIT", "CHECK", "END"]
    assert history[-1]["record"] == ended.document()
    assert profile.evidence.get(ref_from_document(pointer["history_ref"]), frozenset({"private"})).header.revision == str(version)
    reopened = episode_profile(world, Clocks(T0 + SECOND), invocation="fx-c3-reader")
    assert reopened.repository.load(OBJECTIVE) == (version, ended)
