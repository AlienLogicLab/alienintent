"""Translate existing Decision Inbox records into source-bound question resolutions."""
from alienintent.context_assembly.domain.ambiguity import Finding
from alienintent.context_assembly.ports.decision_resolution import DecisionResolution, QuestionChannel
from alienintent.control_plane.application.decision_inbox import DecisionInbox
from alienintent.execution_coordination.domain.escalation import DecisionRecord, HumanDecisionRequired


class DecisionInboxQuestions(DecisionResolution, QuestionChannel):
    def __init__(self, inbox: DecisionInbox, profile: str) -> None:
        self._inbox, self._profile = inbox, profile

    def open(self, finding: Finding, work_item: str) -> None:
        self._inbox.register(HumanDecisionRequired(
            self._profile, finding.project, work_item, 0, finding.question, finding.blocked_reason,
            ("resolve", "defer"),
            ("resolve records the referenced authority answer and releases only this question's hold",
             "defer keeps the affected branch held"),
            "answer from the authority record; no default answer is assumed",
            finding.affected, ("SF-REQ-012 upstream preparation hold",),
            "the affected requirement branch stays held; unrelated requirements remain preparable",
            (f"resolve clears only finding {finding.finding_id} at revision {finding.requirement_revision}",)))

    def validate(self, finding: Finding, work_item: str, decision: DecisionRecord) -> str | None:
        submission, event = decision.submission, decision.event
        if submission.work_item != work_item or event.work_item != work_item:
            return "FINDING_MISMATCH"
        if submission.actor != finding.required_actor or event.actor != submission.actor:
            return "AUTHORITY_HOLD"
        if submission.choice != "resolve":
            return "DECISION_NOT_RESOLVE"
        try:
            recorded = self._inbox.show(work_item)
        except KeyError:
            return "AUTHORITY_HOLD"
        if recorded != decision:
            return "AUTHORITY_HOLD"  # Only a durably admitted inbox decision is attributable.
        return None
