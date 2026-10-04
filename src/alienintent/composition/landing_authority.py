"""The Landing Authority: deterministic code that alone uses a landing-scoped App token, for one exact ordered push.

It is built only when the registry's `github` entry sets `"landing": true`. It holds its own InstallationCredentials,
minted with exactly `LANDING_PERMISSIONS` for the one repository. `land(order)` checks the coordinator record (ACCEPT,
the order's candidate), the requested actions, the merge and record commits in the order's landing clone, the remote
default branch head (still the order's base), the order against the last journaled `closure-ordered` event of its
correlation, and the minted token's scope as GitHub reports it. Only then does it run one `git push <url>
<record>:refs/heads/<default branch>`, with the token only in that process's environment (`http.extraheader` through
`GIT_CONFIG_COUNT`), credential helpers and hooks off, no prompt and no force. It answers only `pushed` or
`refused:<reason>`; the token is never stored, logged, journaled or returned. The caller trusts neither answer.
"""
from __future__ import annotations

from base64 import b64encode
from collections.abc import Callable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess

from alienintent.installation.application.installation_credentials import InstallationCredentials

LANDING_PERMISSIONS = {"contents": "write", "metadata": "read"}
MERGED_TO_MAIN, LANDING_RECORD = "merged-to-main", "landing-record"
PUSHED = "pushed"


@dataclass(frozen=True)
class LandingOrder:
    identity: str
    candidate: str
    correlation: str
    base: str
    merge: str
    record: str
    record_path: str
    clone: Path
    actions: tuple[str, ...]
    attempt: int


def git_environment(home: Path) -> dict[str, str]:
    """No user or system git configuration, no stored credential and no prompt."""
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_TERMINAL_PROMPT": "0", "LANG": "C"}


class LandingAuthority:
    def __init__(self, credentials: InstallationCredentials, repository: str, default_branch: str,
                 accepted: Callable[[str], str | None], ordered: Callable[[str], Mapping[str, object] | None],
                 push_url: str | None = None) -> None:
        self._credentials, self._repository, self._branch = credentials, repository, default_branch
        self._accepted, self._ordered = accepted, ordered
        self._push_url = push_url or f"https://github.com/{repository}.git"

    def land(self, order: LandingOrder) -> str:
        reason = self._refusal(order)
        if reason is not None:
            return f"refused:{reason}"
        try:
            token = self._credentials.token()
        except Exception:  # noqa: BLE001 - no token, no push
            return "refused:credential-unavailable"
        if dict(token.permissions) != LANDING_PERMISSIONS or token.repository_selection != "selected":
            return "refused:credential-scope"
        header = "Authorization: Basic " + b64encode(f"x-access-token:{token.value}".encode()).decode()
        environment = git_environment(order.clone) | {
            "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "http.extraheader", "GIT_CONFIG_VALUE_0": header,
            "GIT_CONFIG_KEY_1": "credential.helper", "GIT_CONFIG_VALUE_1": ""}
        try:
            pushed = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "--quiet", self._push_url,
                                     f"{order.record}:refs/heads/{self._branch}"], cwd=order.clone, env=environment,
                                    capture_output=True, check=False, timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            return "refused:push"
        return PUSHED if pushed.returncode == 0 else "refused:push"

    def _refusal(self, order: LandingOrder) -> str | None:
        if self._accepted(order.identity) != order.candidate:
            return "not-accepted"
        if MERGED_TO_MAIN not in order.actions or LANDING_RECORD not in order.actions:
            return "actions"
        journaled = self._ordered(order.correlation)
        expected = {"base": order.base, "merge": order.merge, "record": order.record, "record_path": order.record_path,
                    "attempt": order.attempt, "actions": list(order.actions)}
        recorded = journaled.get("order") if isinstance(journaled, Mapping) else None
        if not isinstance(recorded, Mapping) or journaled.get("work_identity") != order.identity \
                or journaled.get("candidate") != order.candidate \
                or {key: recorded.get(key) for key in expected} != expected:
            return "order-unjournaled"
        git = lambda *args: self._git(order.clone, *args)  # noqa: E731
        if git("rev-list", "--parents", "-n", "1", order.merge).split()[1:] != [order.base, order.candidate]:
            return "merge-parents"
        if git("rev-parse", f"{order.merge}^{{tree}}") != git("rev-parse", f"{order.candidate}^{{tree}}"):
            return "merge-tree"
        if git("rev-list", "--parents", "-n", "1", order.record).split()[1:] != [order.merge]:
            return "record-parent"
        if git("diff-tree", "--no-commit-id", "--name-status", "-r", order.merge, order.record) \
                != f"A\t{order.record_path}":
            return "record-changes"
        head = git("ls-remote", self._push_url, f"refs/heads/{self._branch}").split("\t")[0]
        if head != order.base:
            return "base-moved"
        return None

    @staticmethod
    def _git(clone: Path, *args: str) -> str:
        try:
            result = subprocess.run(["git", *args], cwd=clone, env=git_environment(clone), capture_output=True,
                                    check=False, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return result.stdout.decode(errors="replace").strip() if result.returncode == 0 else ""
