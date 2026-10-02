"""The repository adapter's Issue reads and writes (`work link`, `work display`), driven by recorded answers.

Only the transport is recorded; the request paths, payloads, expected statuses and error types run as they run live.
"""
from __future__ import annotations

import json

import pytest

from alienintent.execution_coordination.adapters.github_repository_api import GitHubRepositoryApi
from alienintent.execution_coordination.ports.repository_directory import RepositoryRejected, RepositoryUnavailable
from alienintent.installation.ports.github_transport import TransportResponse
from tests.support.live_github import SANDBOX_REPOSITORY, RecordedTransport

ISSUES = f"https://api.github.com/repos/{SANDBOX_REPOSITORY}/issues"


def issue(number: int, **fields) -> dict:
    return {"number": number, "node_id": f"I_{number}", "title": "t", "body": "b", "state": "open", **fields}


class Sending(RecordedTransport):
    """Recorded answers; also keeps each request body sent."""

    def __init__(self, answers) -> None:
        super().__init__(answers)
        self.sent: list[tuple[str, str, dict | None, dict]] = []

    def request(self, method, url, headers, body=None) -> TransportResponse:
        self.sent.append((method, url, json.loads(body) if body else None, dict(headers)))
        return super().request(method, url, headers, body)


def api(**answers) -> tuple[GitHubRepositoryApi, Sending]:
    transport = Sending(answers)
    return GitHubRepositoryApi(SANDBOX_REPOSITORY, transport, lambda: {"Authorization": "token recorded"}), transport


def test_an_issue_is_read_by_number():
    repository, transport = api(**{"/issues/7": issue(7)})
    assert repository.issue(7)["node_id"] == "I_7"
    assert transport.calls == [("GET", f"{ISSUES}/7")]


@pytest.mark.parametrize("answer", [(404, {"message": "Not Found"}), (410, {"message": "Gone"}),
                                    issue(7, pull_request={"url": "x"})])
def test_a_missing_issue_and_a_pull_request_are_both_rejected(answer):
    """The caller answers ISSUE_NOT_FOUND for both; removing the pull-request check must fail this."""
    repository, _ = api(**{"/issues/7": answer})
    with pytest.raises(RepositoryRejected):
        repository.issue(7)


def test_an_answer_for_another_issue_or_a_failing_status_is_unavailable():
    for answer in (issue(8), (500, {"message": "x"}), {"number": 7}):
        repository, _ = api(**{"/issues/7": answer})
        with pytest.raises(RepositoryUnavailable):
            repository.issue(7)


def test_create_posts_title_and_body_and_requires_201():
    repository, transport = api(**{"/issues": (201, issue(3))})
    assert repository.create_issue("T", "B")["number"] == 3
    method, url, payload, headers = transport.sent[0]
    assert (method, url, payload) == ("POST", ISSUES, {"title": "T", "body": "B"})
    assert headers["Content-Type"] == "application/json" and headers["Authorization"] == "token recorded"
    repository, _ = api(**{"/issues": (200, issue(3))})
    with pytest.raises(RepositoryUnavailable):
        repository.create_issue("T", "B")


def test_update_and_close_patch_exactly_their_fields_and_require_200():
    repository, transport = api(**{"/issues/3": issue(3)})
    repository.update_issue(3, "T", "B")
    repository.close_issue(3, "B\n\nDuplicate of #1; closed by AlienIntent work link.")
    assert [(m, u, p) for m, u, p, _ in transport.sent] == [
        ("PATCH", f"{ISSUES}/3", {"title": "T", "body": "B"}),
        ("PATCH", f"{ISSUES}/3", {"state": "closed", "state_reason": "not_planned",
                                  "body": "B\n\nDuplicate of #1; closed by AlienIntent work link."})]
    repository, _ = api(**{"/issues/3": (201, issue(3))})
    with pytest.raises(RepositoryUnavailable):
        repository.update_issue(3, "T", "B")


def test_recent_issues_reads_one_page_newest_first_and_skips_pull_requests():
    repository, transport = api(**{"per_page=100": [issue(3), issue(2, pull_request={"url": "x"}), issue(1)]})
    assert [entry["number"] for entry in repository.recent_issues(100)] == [3, 1]
    assert transport.calls == [("GET", f"{ISSUES}?state=all&sort=created&direction=desc&per_page=100")]
