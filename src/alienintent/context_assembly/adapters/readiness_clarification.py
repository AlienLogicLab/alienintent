"""Agent Ready owner clarifications as existing Decision Inbox questions (SF-REQ-035); no default answer."""
from alienintent.context_assembly.ports.readiness import ClarificationChannel
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.escalation import DecisionRecord, HumanDecisionRequired

PREFIX = "upstream-question:readiness-clarify:"


class InboxClarifications(ClarificationChannel):
    """Each owner clarification is registered verbatim; U9 makes no materiality judgment of its own."""

    def __init__(self, inbox: DecisionInbox, profile: str, project: str, required_actor: str) -> None:
        self._inbox, self._profile, self._project, self._actor = inbox, profile, project, required_actor

    def open(self, identity: str, attempt_id: str, index: int, question: str) -> str:
        work_item = f"{PREFIX}{identity}:{attempt_id}:{index}"
        self._inbox.register(HumanDecisionRequired(
            self._profile, self._project, work_item, 0, question,
            f"Agent Ready returned CLARIFY for {identity} (attempt {attempt_id})", ("resolve", "defer"),
            ("resolve records the owner answer; the unit is then reassessed as a fresh attempt",
             "defer keeps the unit held with no assessment"),
            "answer from the authority record; no default answer is assumed", (identity,),
            ("SF-REQ-015 readiness CLARIFY route",),
            "the unit stays held; no implementation is authorized",
            (f"resolve releases only the CLARIFY hold of attempt {attempt_id}; release stays a separate gate",)))
        return work_item

    def resolved(self, work_item: str) -> str | None:
        try:
            recorded = self._inbox.show(work_item)
        except KeyError:
            return "NOT_REGISTERED"
        if not isinstance(recorded, DecisionRecord):
            return "AWAITING_DECISION"
        submission, event = recorded.submission, recorded.event
        if submission.actor != self._actor or event.actor != submission.actor:
            return "AUTHORITY_HOLD"
        if submission.choice != "resolve":
            return "DECISION_NOT_RESOLVE"
        return None
