#!/usr/bin/env python3
"""AlienIntent local Program Director — orchestration intelligence, not product authority.

Operates the post-Wave-1 closure/learning/Wave-2-design program defined in
`docs/operations/alienintent-post-wave1-to-wave2-program-plan.md`, under the routing policy
in `docs/operations/alienintent-local-program-director-intelligent-routing.md`.

Hard boundaries, from both documents:

- It is **not** AlienIntent product execution authority. It never releases a BIU, never
  changes Project lifecycle state, and its task states are program states that must never be
  confused with BIU lifecycle states (enforced in `ProgramState.upsert_task`).
- Model memory is never authority. Repository evidence and canonical AlienIntent authority are.
- It recommends; it does not decide Founder authority.

Routing exists to spend intelligence only where intelligence is required:

    Tier 0  deterministic tooling   — facts, counts, identity, ancestry, schema, replay
    Tier 1  cheapest capable model  — bounded extraction/classification/drafting
    Tier 2  Codex GPT-6 Astra       — substantial technical analysis, design, code-aware work
    Tier 3  Claude bootstrap coord. — only where its lived Wave 1 context has unique value
    Tier 4  fresh independent       — high-risk work where author bias actually matters
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

REPO = Path("/mnt/d/Projects/alienintent")
DEFAULT_STATE = REPO / "docs/operations/post-wave1-program/program-state.json"

FIVE_QUESTIONS = (
    "can_deterministic_tooling_do_this",
    "cheapest_model_likely_to_succeed_first_pass",
    "minimum_context_required",
    "does_this_need_independent_review",
    "evidence_that_would_trigger_escalation",
)

# Program task states. Deliberately disjoint from AlienIntent BIU lifecycle states.
PROGRAM_STATES = {"PLANNED", "READY", "RUNNING", "REVIEW", "REPAIR", "BLOCKED",
                  "FOUNDER_DECISION_REQUIRED", "DONE", "SUPERSEDED"}
# Actively open work. An earlier phase in one of these stops later phases from being offered.
_IN_PROGRESS = {"RUNNING", "REVIEW", "REPAIR"}
# The phases the autonomous execution amendment approves, section 1. PROGRAM_COMPLETE requires
# all of them, not merely an empty task queue: unseeded phases produce no open work, and an
# empty queue would otherwise read as completion.
APPROVED_PHASES = tuple(str(i) for i in range(3, 15))
BIU_LIFECYCLE_STATES = {"CAPTURE", "SPECIFY", "PLAN", "TASKS", "READY_BIU", "IMPLEMENT",
                        "VERIFY", "REVIEW_BIU", "ACCEPT", "DONE_BIU"}
_FORBIDDEN_AS_PROGRAM_STATE = {"CAPTURE", "SPECIFY", "PLAN", "TASKS", "IMPLEMENT", "VERIFY", "ACCEPT"}


class Tier(Enum):
    DETERMINISTIC = 0
    CHEAP_MODEL = 1
    CODEX_PRIMARY = 2
    CLAUDE_COORDINATOR = 3
    FRESH_REVIEWER = 4


class RiskClass(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Task types whose value comes specifically from lived Wave 1 participation.
# Note: bootstrap_retirement_review is deliberately NOT here. The program plan routes it to
# Codex with coordinator review, and that is right: the coordinator is the participant whose
# bootstrap is being retired, so authoring its own retirement audit is the authorship conflict
# Phase 2 identified. Lived context is supplied as evidence, not as authorship.
_COORDINATOR_ONLY = {
    "historical_cross_check", "bootstrap_control_review",
    "missing_incident_identification", "incident_interpretation_review",
    "closure_evidence_review",
}
# High-risk work where the author must not also be the reviewer.
_FRESH_REVIEWER_TASKS = {"design_verification", "independent_design_review"}
_CHEAP_TASKS = {"extract_fields", "summarize_bounded_evidence", "classify_against_taxonomy",
                "tabulate_packet", "low_risk_draft"}
_DETERMINISTIC_TASKS = {"verify_sha_reachability", "compare_counts", "validate_schema",
                        "locate_identifiers", "regenerate_deterministic_report",
                        "check_head_matches_remote", "detect_stale_references",
                        "run_proven_red_checks"}

_RISK_BY_TASK = {
    "metadata_index_update": RiskClass.LOW, "factual_evidence_correction": RiskClass.LOW,
    "regenerate_deterministic_report": RiskClass.LOW, "doc_synchronization": RiskClass.LOW,
    "extract_fields": RiskClass.LOW,
    "learning_consolidation": RiskClass.MEDIUM, "requirement_owner_reconciliation": RiskClass.MEDIUM,
    "process_matrix": RiskClass.MEDIUM, "evidence_reconciliation": RiskClass.MEDIUM,
    "operational_policy_analysis": RiskClass.MEDIUM,
    "design_contract": RiskClass.HIGH, "design_verification": RiskClass.HIGH,
    "lifecycle_semantics": RiskClass.HIGH, "split_replan_design": RiskClass.HIGH,
    "bootstrap_retirement_review": RiskClass.HIGH, "requirement_weakening": RiskClass.HIGH,
    "security_model": RiskClass.HIGH, "founder_recommendation": RiskClass.HIGH,
    "closure_evidence_review": RiskClass.HIGH,
}


def classify_risk(task_type: str) -> RiskClass:
    return _RISK_BY_TASK.get(task_type, RiskClass.MEDIUM)


@dataclass
class RoutingDecision:
    task_type: str
    risk: RiskClass
    tier: Tier
    actor: str
    model: str | None
    review_required: bool
    rationale: str
    questions: dict = field(default_factory=dict)

    def as_record(self) -> dict:
        return {"task_type": self.task_type, "risk_class": self.risk.value,
                "tier": self.tier.name, "chosen_actor": self.actor, "model": self.model,
                "review_required": self.review_required, "rationale": self.rationale,
                "five_questions": self.questions}


def route(task_type: str, risk: RiskClass, deterministic_possible: bool,
          bounded_input: bool = False, codex_model: str | None = None) -> RoutingDecision:
    """Choose the cheapest actor capable of succeeding first-pass.

    Deterministic tooling wins whenever it can settle the question — including for HIGH
    risk, because risk raises the review bar, not the need for a model to count things.
    """
    model = codex_model or resolved_codex_model()

    if deterministic_possible or task_type in _DETERMINISTIC_TASKS:
        tier, actor, chosen_model = Tier.DETERMINISTIC, "deterministic-tooling", None
        why = ("Settleable by git/schema/parsers/tests. Never spend model intelligence proving "
               "what deterministic tooling establishes reliably.")
        review = False
    elif task_type in _FRESH_REVIEWER_TASKS:
        # Deliberately NOT `model`. This tier exists to be a different provider from the author,
        # so labelling it with the resolved Codex model asserts the reviewer was the thing it was
        # chosen not to be. A dispatched session auditing the programme's own state caught Phase
        # 10's routing claiming gpt-6-astra while the retained provenance showed fresh Claude.
        # The Director knows the provider differs; it does not resolve the reviewer's model.
        tier, actor, chosen_model = Tier.FRESH_REVIEWER, "fresh-independent-reviewer", None
        why = ("High-impact work where author bias matters; reviewer must not be the author, and "
               "must not be recorded as carrying the author's model.")
        review = True
    elif task_type in _COORDINATOR_ONLY:
        tier, actor, chosen_model = Tier.CLAUDE_COORDINATOR, "claude-bootstrap-coordinator", None
        why = ("Requires lived Wave 1 operational context that durable artifacts alone do not "
               "supply. Its memory is a locator; durable evidence decides disagreements.")
        review = risk is RiskClass.HIGH
    elif bounded_input and task_type in _CHEAP_TASKS:
        tier, actor, chosen_model = Tier.CHEAP_MODEL, "cheap-bounded-model", None
        why = "Narrow bounded extraction against an explicit schema; no architecture judgment."
        review = risk is RiskClass.HIGH
    else:
        tier, actor, chosen_model = Tier.CODEX_PRIMARY, "codex-fresh", model
        why = ("Substantial code-aware/technical work; Codex is the configured primary analyst "
               "and fresh context avoids inheriting participant bias.")
        review = risk is not RiskClass.LOW

    return RoutingDecision(
        task_type=task_type, risk=risk, tier=tier, actor=actor, model=chosen_model,
        review_required=review, rationale=why,
        questions={
            "can_deterministic_tooling_do_this":
                "yes" if tier is Tier.DETERMINISTIC else "no — irreducible reasoning remains",
            "cheapest_model_likely_to_succeed_first_pass":
                chosen_model or actor,
            "minimum_context_required":
                "task contract, canonical authority references, bounded evidence paths, output schema, non-goals",
            "does_this_need_independent_review":
                f"{'yes' if review else 'no'} (risk {risk.value})",
            "evidence_that_would_trigger_escalation":
                "structurally invalid result, disagreement with durable evidence, or an authority gap",
        })


def resolved_codex_model(config: Path = Path.home() / ".codex/config.toml") -> str:
    """Resolve the configured model rather than hardcoding it (bootstrap requirement)."""
    try:
        for line in config.read_text().splitlines():
            s = line.strip()
            if s.startswith("model") and "=" in s and not s.startswith("model_"):
                return s.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "UNKNOWN"


class ProgramState:
    """Durable program state. Reconstructed from disk on every start."""

    def __init__(self, path: Path | str = DEFAULT_STATE) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {"current_phase": None, "completed_phases": [], "tasks": {},
                    "program": "post-wave1-to-wave2", "updated_at": None}

    def _save(self) -> None:
        self._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        tmp = self.path.with_suffix(".json.partial")
        tmp.write_text(json.dumps(self._data, indent=1, sort_keys=True) + "\n")
        Path.replace(tmp, self.path)

    # --- phases ---------------------------------------------------------------

    def current_phase(self) -> str | None:
        return self._data.get("current_phase")

    def set_phase(self, phase: str) -> None:
        self._data["current_phase"] = phase
        self._save()

    def complete_phase(self, phase: str) -> None:
        if phase not in self._data["completed_phases"]:
            self._data["completed_phases"].append(phase)
        self._save()

    # --- tasks ----------------------------------------------------------------

    def upsert_task(self, task_id: str, *, phase: str, title: str, actor: str, status: str,
                    risk: str, prompt_path: str | None = None, artifact_refs=None,
                    review_status: str | None = None, blockers=None,
                    resulting_commit: str | None = None, routing: dict | None = None,
                    critical_path: bool | None = None, subdecisions=None) -> None:
        if status in _FORBIDDEN_AS_PROGRAM_STATE or status not in PROGRAM_STATES:
            raise ValueError(
                f"{status!r} is not a program task state. Program states are {sorted(PROGRAM_STATES)}; "
                "BIU lifecycle states must never be used here.")
        existing = self._data["tasks"].get(task_id, {})
        subs = list(subdecisions) if subdecisions is not None else list(existing.get("subdecisions") or [])
        # A Founder-decision bundle is only as closed as its least-closed part. Declaring the
        # bundle DONE while a subdecision is OPEN would hide a live decision behind a closed one.
        if status == "DONE" and any(str(s.get("status", "")).upper() == "OPEN" for s in subs):
            raise ValueError(
                f"{task_id} cannot be DONE: subdecisions still OPEN — "
                f"{[s.get('id') for s in subs if str(s.get('status','')).upper() == 'OPEN']}")
        self._data["tasks"][task_id] = {
            **existing,
            "task_id": task_id, "phase": phase, "title": title, "assigned_actor": actor,
            "status": status, "risk_class": risk, "prompt_path": prompt_path,
            "artifact_refs": list(artifact_refs or existing.get("artifact_refs") or []),
            "review_status": review_status if review_status is not None else existing.get("review_status"),
            "blockers": list(blockers or existing.get("blockers") or []),
            "resulting_commit": resulting_commit or existing.get("resulting_commit"),
            "routing": routing or existing.get("routing"),
            "critical_path": critical_path if critical_path is not None
                             else existing.get("critical_path"),
            "subdecisions": subs,
            "created_at": existing.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def task(self, task_id: str) -> dict | None:
        return self._data["tasks"].get(task_id)

    def tasks(self) -> list[dict]:
        return sorted(self._data["tasks"].values(), key=lambda t: (t["phase"], t["task_id"]))

    def founder_decisions_required(self) -> list[dict]:
        return [t for t in self.tasks() if t["status"] == "FOUNDER_DECISION_REQUIRED"]

    def blocking_founder_decisions(self) -> list[dict]:
        """Decisions that actually halt phase progression.

        Autonomous execution amendment §4: a decision affecting only one branch must not
        globally stall the program; only a critical-path decision halts progression. An
        unmarked decision counts as critical — defaulting the other way would let the program
        walk past a decision nobody had classified.
        """
        return [t for t in self.founder_decisions_required()
                if t.get("critical_path") is not False]

    def terminal_state(self) -> str | None:
        """The amendment's two terminal states, or None while the run continues.

        §15: the Program Director reports only PROGRAM_COMPLETE or FOUNDER_DECISION_REQUIRED.
        Mid-run is neither, and must not be reported as either.
        """
        if self.blocking_founder_decisions():
            return "FOUNDER_DECISION_REQUIRED"
        open_work = [t for t in self.tasks()
                     if t["status"] not in ("DONE", "SUPERSEDED", "FOUNDER_DECISION_REQUIRED")]
        if open_work:
            return None
        done = set(self._data.get("completed_phases") or [])
        if not set(APPROVED_PHASES) <= done:
            return None  # phases remain; an empty queue is not completion
        return "PROGRAM_COMPLETE"

    def next_task(self) -> dict | None:
        """The next unblocked task. A pending Founder decision stops the program.

        Work in progress earlier in the program also stops it. Observed live: with Phase 2 in
        REPAIR after independent review, this offered the Phase 6 task, which would have had an
        operator start a later phase over an open repair.
        """
        if self.blocking_founder_decisions():
            return None
        for t in self.tasks():
            if t["status"] in ("READY", "PLANNED"):
                return t
            if t["status"] in _IN_PROGRESS:
                return None  # earlier work is actively open; nothing later is next
            # BLOCKED and SUPERSEDED are skipped: they hold no actor and stall nothing else.
        return None
