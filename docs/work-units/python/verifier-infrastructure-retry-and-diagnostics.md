# Work unit: a VERIFIER that ends without a verdict is retried, and every worker process leaves durable diagnostics

**Label:** `VERIFIER-INFRASTRUCTURE-RETRY-AND-DIAGNOSTICS` (a document label; permanent id `PENDING-REGISTRATION`).
**Status:** Draft revision 1, 2026-10-09, for independent review. Not registered, not assessed, not released.
**Position on the path:** first on the autonomy critical path (Founder 2026-10-09): VERIFIER-INFRASTRUCTURE-RETRY-AND-
DIAGNOSTICS -> NO-CHANGE re-issue -> PLAN-AUTHORITY-INHERITANCE -> remaining autonomy blockers -> three-item proof.
**Starting revision:** main `bc9a9d8`. Every line number below is at `bc9a9d8`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "PENDING-REGISTRATION",
 "version": "revision-1",
 "intent": "A VERIFIER whose session ends without a valid verdict (its process fails or times out, or it leaves no verdict, a malformed one or one for another revision) made no engineering judgment: the work item stays at VERIFY on the same custodied candidate and the next launch runs a fresh VERIFIER, at most twice in a row, then a typed infrastructure hold. No rejection is counted and no PRODUCER cycle is used; only a valid REJECT is a rejection. Every worker process's exit status, bounded and redacted output tails, provider and command are kept with its outcome in the invocation journal, with the cause they show.",
 "satisfied_requirement_ids": [
  "SF-REQ-002"
 ],
 "fixed_decisions": [
  "Founder 2026-10-09: A VERIFIER process failure without a valid verdict is an infrastructure failure, not an engineering judgment. Preserve the exact candidate and retry verification within a bounded infrastructure-retry policy. Only a valid REJECT verdict counts as verification rejection.",
  "Founder 2026-10-09: retries consume no PRODUCER implementation cycles and are not engineering rejections; retry exhaustion is a typed infrastructure hold, not a fake VERIFIER judgment.",
  "Founder 2026-10-09: persist exit status, bounded stdout/stderr tails and provider metadata for every worker invocation, and classify the outcome as ACCEPT, REJECT, timeout, network/provider failure, authentication failure, launcher/runtime failure, malformed verdict or cancellation; not full transcripts.",
  "A candidate that cannot be retrieved (candidate-unavailable) is a custody refusal, not infrastructure: it still holds (lifecycle capstone check U1).",
  "The redaction rule is the one the live worker-boundary proof already uses (tools/live/worker_boundary_check.py lines 67-79); it moves into the new domain module and the proof imports it, so there is one rule."
 ],
 "authorized_scope": [
  "src/alienintent/execution_coordination/ports/worker_provider.py",
  "src/alienintent/execution_coordination/application/factory_coordinator.py",
  "src/alienintent/invocation_runtime/domain/diagnostics.py",
  "src/alienintent/invocation_runtime/adapters/cli_worker.py",
  "src/alienintent/invocation_runtime/application/real_worker.py",
  "tools/live/worker_boundary_check.py",
  "tests/invocation_runtime/test_worker_diagnostics.py",
  "tests/composition/test_worker_launch.py",
  "tests/execution_coordination/test_role_orchestration.py"
 ],
 "excluded_scope": [
  "the PRODUCER and CLOSURE outcome rules, the regression gate (invocation_runtime/application/regression_gate.py) and RealWorkerProvider._gate",
  "the lifecycle transition rules in execution_coordination/domain/lifecycle.py",
  "read_verdict and the verdict kinds it returns",
  "any contract or schema field (the retry limit is a module constant)",
  "full worker transcripts or any unbounded output in durable state",
  "BASE_MOVED revalidation, plan authority and the NO-CHANGE requirement"
 ],
 "dependencies": [],
 "required_capabilities": [
  "python",
  "filesystem"
 ],
 "budget_policy": {
  "maximum_attempts": 3,
  "hard_wall_clock_seconds": 3600,
  "cancellation_limit": 1
 },
 "retry_policy": "verifier rejection returns to the PRODUCER with the findings; at most 3 cycles",
 "completion_criteria": [
  "acceptance checks 1-8 pass"
 ],
 "verification_obligations": [
  "independent VERIFIER on the exact candidate",
  "each acceptance check fails for its named wrong implementation",
  "the VERIFIER runs mutations M1-M8 of check 8 exactly and records that each makes its named test fail and that reverting makes it pass"
 ],
 "required_evidence": [
  "independent-verifier-accepted"
 ],
 "non_goals": [
  "a backoff between VERIFIER retries: each retry waits for the next launch or the next start() call",
  "retrying a PRODUCER or CLOSURE session differently from today"
 ],
 "candidate_custody_requirements": [
  "candidate commit verified exactly, then landed by the Landing Authority preserving its SHA; no pull request"
 ],
 "release_policy": "explicit-human-off",
 "authority_issuer": "Founder",
 "authority_references": [
  "docs/work-units/python/automated-closure.md"
 ],
 "target_repositories": [
  "AlienLogicLab/alienintent"
 ],
 "baselines": [
  "main"
 ],
 "required_closure_actions": [
  "candidate-published",
  "merged-to-main",
  "landing-record",
  "board-updated",
  "workspaces-cleaned"
 ],
 "stop_escalation_conditions": [
  "a named function or line does not exist at the starting revision",
  "the change would need a lifecycle transition rule change",
  "the whole suite at the candidate has a failed or error test case",
  "scope outside the authorized files"
 ]
}
```

## 1. Why

On 2026-10-09 two candidates of the same requirement (`76c5795`, `105ecc8`) each passed the regression gate (2913
tests, 0 failures) and were then lost because the VERIFIER's session process exited non-zero before writing a verdict.
For the second, kept diagnostics showed a network outage ("workspace routing discovery failed", "error sending request
for url"); for the first the cause is unknown, because the session's output tails live only in memory
(`CliWorkerProvider.outputs`, `cli_worker.py` line 86, filled at line 223) and are gone when `work launch` exits.

Today, at VERIFY (`factory_coordinator.py`, `_advance`, VERIFIER branch, lines 503-505), a process `failure` or
`timeout` becomes the work item's final outcome (`FINAL_OUTCOMES`, line 36), and `verdict-missing`,
`verdict-malformed` and `verdict-miscorrelated` become `authority-block` ("verifier-outcome-not-attributable", lines
506-514). Neither is an engineering judgment on the candidate. The first ends the work item for good; the second needs
the Founder.

## 2. The change

### 2.1 The infrastructure kinds (`execution_coordination/ports/worker_provider.py`, after line 17)

Right after `MISSING_TERMINAL_RESULT = "missing-terminal-result"` add exactly:

```python
# VERIFIER outcomes that carry no engineering judgment: the session ended without a valid verdict (its process failed
# or timed out, or it left no verdict, a malformed one or one for another revision). The coordinator retries the
# VERIFIER on the same candidate; only a valid REJECT is a rejection. A candidate that cannot be retrieved
# (`candidate-unavailable`) is a custody refusal, not infrastructure: it still holds.
VERIFIER_INFRASTRUCTURE = frozenset({"failure", "timeout", "verdict-missing", "verdict-malformed", "verdict-miscorrelated"})
```

### 2.2 The coordinator (`execution_coordination/application/factory_coordinator.py`)

1. Line 23: add `VERIFIER_INFRASTRUCTURE` to the `worker_provider` import, after `VERIFIER`.
2. `CARRIED` (lines 29-30): add `"verifier_retries"` after `"closure_retries"`.
3. After `CLOSURE_RETRY = "closure-retry"` (line 32) add exactly:

```python
# A VERIFIER that ended without a valid verdict: the item stays at VERIFY on the same candidate and the next launch runs
# a fresh VERIFIER, at most VERIFIER_RETRY_LIMIT times in a row; then a typed infrastructure hold.
VERIFIER_RETRY, VERIFIER_RETRY_LIMIT = "verifier-retry", 2
```

4. `start()` (lines 122-128): rename `closed_once` to `once`, replace its comment with the two lines below, and right
   after `result = self._run(item)` (line 128) add the `VERIFIER_RETRY` guard, so the loop reads:

```python
        # CLOSURE runs at most once per item in one call, and a VERIFIER retry waits for the next call: an outage is not
        # spent in one loop.
        once: set[str] = set()
        while (item := self._next_item([ready for ready in items if ready.identity not in skipped
                                        and ready.identity not in once])) is not None:
            producing = self._role(item.identity) == PRODUCER
            if self._role(item.identity) == CLOSURE:
                once.add(item.identity)
            result = self._run(item)
            if self._outcome(item.identity) == VERIFIER_RETRY:
                once.add(item.identity)
```

   The rest of the loop is unchanged.
5. The PRODUCER success return (line 502) becomes, so a new candidate starts with no VERIFIER retries:

```python
            return _Advance(transition(current, current.version, "verify", candidate=verified), "success",
                            {"producer_correlation": invocation.correlation_id, "verifier_retries": 0})
```

6. In the VERIFIER branch, lines 504-505 (`if outcome.kind in {"failure", "timeout"}: return _Advance(current,
   outcome.kind, {})`) become:

```python
            if outcome.kind in VERIFIER_INFRASTRUCTURE:
                return self._retry_verifier(current, prior, outcome.kind)
```

   Everything after it in the branch is unchanged: any other non-`accept`/`reject` kind (`verdict-preexisting`,
   `feature-regressions-missing`, `candidate-unavailable`, `ineligible`, `cancelled`, ...) still holds as
   `verifier-outcome-not-attributable`, and a valid REJECT still goes to `_rework` with source `verifier`.
7. Just before `@staticmethod` / `def _retry_closure` (lines 569-570) add exactly:

```python
    @staticmethod
    def _retry_verifier(state: ExecutionState, prior: dict[str, object], kind: str) -> _Advance:
        """A VERIFIER that ended without a valid verdict made no engineering judgment: the stage stays VERIFY on the same
        custodied candidate, so the next launch runs a fresh VERIFIER. No rejection is counted and no PRODUCER cycle is
        used. After VERIFIER_RETRY_LIMIT retries in a row, a typed infrastructure hold, never a verdict."""
        retries = int(prior.get("verifier_retries", 0) or 0) + 1
        fields: dict[str, object] = {"verifier_retries": retries, "verifier_failure": kind}
        if retries > VERIFIER_RETRY_LIMIT:
            return _Advance(state, "authority-block", fields | {"hold_reason": f"verifier-infrastructure-exhausted:{kind}"},
                            f"The VERIFIER ended without a valid verdict {retries} times in a row (last: {kind}); "
                            "no engineering judgment was made on the candidate.")
        return _Advance(state, VERIFIER_RETRY, fields)

```

   The hold is resumable through the existing `work decide` path: an `authorize` re-admits one more VERIFIER session.

### 2.3 The diagnostics module (new: `invocation_runtime/domain/diagnostics.py`)

Exactly this file:

```python
"""Bounded, durable diagnostics of one worker process, and the cause they show. Pure.

A worker process's exit status, the ends of its output streams and its provider command are kept with the invocation's
outcome in the invocation journal, so the reason a worker ended survives the launcher. The cause is read from those
facts only; it is a label for a person diagnosing, never a verdict, and `unknown` when nothing matches. Every kept
text is redacted first: token-like text becomes [REDACTED] (the rule the live worker-boundary proof already used).
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

TAIL = 4000  # characters kept from the end of each stream
ARGUMENT = 200  # characters kept of each command argument
CAUSES = ("accept", "reject", "timeout", "network-or-provider", "authentication", "launcher-or-runtime",
          "malformed-verdict", "cancellation", "unknown")
_AUTHENTICATION = re.compile(r"\b401\b|\b403\b|unauthori[sz]ed|not logged in|log ?in required|authentication|"
                             r"invalid api key|token (?:has )?expired", re.I)
_NETWORK = re.compile(r"error sending request|timed out|EAI_AGAIN|could not resolve|name resolution|"
                      r"connection (?:refused|reset|closed)|routing discovery failed|reconnecting|rate limit|overloaded|"
                      r"service unavailable|bad gateway|gateway timeout|internal server error", re.I)
_VERDICT = frozenset({"verdict-missing", "verdict-malformed", "verdict-miscorrelated"})
_SECRETS = (re.compile(r"(?i)\b(authorization|bearer|token|password|secret|api[_-]?key)\b([\s:=]+)(?:(?:bearer|basic|token)\s+)?\S+"),
            re.compile(r"\b(sk-[\w-]{8,}|gh[pousr]_\w{16,}|github_pat_\w+|eyJ[\w-]+\.[\w-]+\.[\w-]+)"),
            re.compile(r"(?=[\w+/=-]{48,})(?![0-9a-f]+\b)[\w+/=-]{48,}"))


def redact(text: str) -> str:
    """`text` with token-like text replaced by [REDACTED]; a 40- or 64-hex object name stays readable."""
    text = _SECRETS[0].sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
    for pattern in _SECRETS[1:]:
        text = pattern.sub("[REDACTED]", text)
    return text


def process_diagnostics(command: Sequence[str], kind: str, exit_status: int | None, stdout: str,
                        stderr: str) -> dict[str, object]:
    """The bounded, redacted record of one process: its provider, its command, its result kind and exit status, and
    the last TAIL characters of each stream."""
    return {"provider": Path(command[0]).name if command else None,
            "command": [redact(argument)[:ARGUMENT] for argument in command],
            "process_kind": kind, "exit_status": exit_status,
            "stdout_tail": redact(stdout)[-TAIL:], "stderr_tail": redact(stderr)[-TAIL:]}


def cause(outcome_kind: str, diagnostics: dict[str, object] | None) -> str:
    """The cause of an invocation's outcome, from its kind and its last process's diagnostics."""
    if outcome_kind in {"accept", "reject"}:
        return outcome_kind
    if outcome_kind in {"cancelled", "cancellation"}:
        return "cancellation"
    if outcome_kind == "timeout":
        return "timeout"
    exit_status = None if diagnostics is None else diagnostics.get("exit_status")
    if outcome_kind in _VERDICT and exit_status == 0:
        return "malformed-verdict"
    text = "" if diagnostics is None else f"{diagnostics.get('stdout_tail', '')}\n{diagnostics.get('stderr_tail', '')}"
    if _AUTHENTICATION.search(text):
        return "authentication"
    if _NETWORK.search(text):
        return "network-or-provider"
    if exit_status in {126, 127}:
        return "launcher-or-runtime"
    return "unknown"
```

The cause is a pattern label over redacted tails, for a person diagnosing; the raw (redacted) tails are always kept
beside it, and `unknown` is the default.

### 2.4 The CLI worker records each process (`invocation_runtime/adapters/cli_worker.py`)

1. After the `process_ownership` import (line 15) add
   `from alienintent.invocation_runtime.domain.diagnostics import process_diagnostics`.
2. After `self.outputs: dict[str, tuple[str, str]] = {}` (line 86) add:

```python
        # Per invocation, the bounded diagnostics of its last process (the worker journals them with its outcome).
        self.diagnostics: dict[str, dict[str, object]] = {}
```

3. In `run`, inside `if regression.kind != "success":` (line 207), after `self._completed.add(invocation_id)` add:

```python
                self.diagnostics[invocation_id] = process_diagnostics(["feature-regressions"], regression.kind,
                                                                      regression.exit_status, "", "")
```

4. Right after `argv, text = self._command(invocation_id, role, workspace)` (line 210) add
   `command = list(argv)  # the provider command alone, before any worker-user prefix and its environment`.
5. Right after `self._active[invocation_id] = process` (line 218) add `stdout = stderr = ""` and
   `result: ProcessResult | None = None`. Each of the three `return ProcessResult(...)` statements of the `try:`
   (lines 225, 228, 229) becomes `result = ProcessResult(...)` followed by `return result` (same arguments).
6. In the `finally:` (line 234), right after `self._active.pop(invocation_id, None)` add:

```python
            if result is not None:
                self.diagnostics[invocation_id] = process_diagnostics(command, result.kind, result.exit_status, stdout, stderr)
```

### 2.5 The worker journals them (`invocation_runtime/application/real_worker.py`)

1. Before the `runtime` import (line 17) add `from alienintent.invocation_runtime.domain.diagnostics import cause`.
2. In `start`, just before `self._journal.append({"event": "invocation-outcome"} | attribution | {` (line 284) add:

```python
        # The last process's bounded diagnostics and the cause they show, kept with the outcome so they outlive the
        # launcher (a process adapter without diagnostics records none).
        kept = getattr(self._process, "diagnostics", None)
        process = kept.pop(invocation.correlation_id, None) if isinstance(kept, dict) else None
```

   and add `"process": process, "cause": cause(outcome.kind, process),` as the last entries of that record.

### 2.6 One redaction rule (`tools/live/worker_boundary_check.py`)

Delete `_SECRETS` (lines 67-69) and `import re` (line 31, then unused). `_tail` (line 72) becomes:

```python
def _tail(data: bytes | str) -> str:
    """The last TAIL_LIMIT characters of a command's output, with token-like text replaced by [REDACTED] (the worker
    diagnostics' own rule). Only diagnostics: a 40- or 64-hex object name stays readable."""
    from alienintent.invocation_runtime.domain.diagnostics import redact
    text = data.decode(errors="replace") if isinstance(data, bytes) else data
    return redact(text)[-TAIL_LIMIT:]
```

`TAIL_LIMIT = 2000` stays. The existing test `test_proof_diagnostics_are_bounded_and_redacted_and_a_crashing_check_
is_recorded_not_raised` (`tests/composition/test_worker_launch.py`) proves the rule unchanged.

### 2.7 Existing tests that change: exactly these

- `tests/execution_coordination/test_role_orchestration.py`: add, before `_held` (line 30):

```python
def _retried(fixture, kind: str) -> None:
    """A VERIFIER that left no valid verdict made no judgment: still VERIFY on the same candidate, no decision request."""
    state = fixture.state()
    assert (state.stage, state.outcome, state.record["verifier_failure"]) == (LifecycleStage.VERIFY, "verifier-retry", kind)
    _, inbox = fixture.store.read_state(fixture.profile.name, "decision-inbox")
    assert WORK not in (inbox or {}).get("open", {})

```

  In `test_producer_success_advances_only_to_verify`, line 53 `_held(fixture, LifecycleStage.VERIFY)` becomes
  `_retried(fixture, "verdict-missing")`; its assertion that one `start()` made exactly the invocations
  `[(PRODUCER, "success"), (VERIFIER, "verdict-missing")]` (line 52) stays and now also proves the once-per-call
  guard. In `test_missing_duplicate_stale_or_miscorrelated_role_evidence_holds` (line 210), after `summary =
  fixture.coordinator.start()` the body becomes:

```python
    state = fixture.state()
    assert state.stage is stage and state.completed_closure_actions == frozenset()
    assert all(run["result"] == "success" for run in fixture.process_runs())
    if fault in {"no-verdict", "stale-verdict"}:  # no valid verdict: an infrastructure retry, not a hold
        _retried(fixture, "verdict-missing" if fault == "no-verdict" else "verdict-miscorrelated")
        return
    assert summary.stop_reason.value == "dependencies-or-authority-blocked"
    _held(fixture, stage)
```

- `tests/composition/test_worker_launch.py`, the fake provider `FAKE_PROVIDER`: after `role = os.environ.get(
  "ALIENINTENT_ROLE")` (line 70) add a `verifier_document()` function. It reads the JSON list in the file
  `Path({plan!r}).with_name("verifier-plan.json")` (absent: empty), pops its first step (none: `"accept"`), writes the
  rest back, and: `"exit"` writes `"progress line\n" * 500 + "error sending request for url
  (https://provider.invalid/)\n"` to standard error and exits 1; `"malformed"` returns `{"revision": head, "verdict":
  "maybe", "findings": []}`; `"reject"` returns `{"revision": head, "verdict": "reject", "findings":
  ["VERIFIER-REJECT-FINDING"]}`; otherwise the accept document of today. Both verdict writes (lines 101 and 104) write
  `verifier_document()` instead of the literal accept document. With no plan file every VERIFIER accepts, as today.

No other existing test changes.

## 3. Acceptance checks

New tests in `tests/composition/test_worker_launch.py` (helpers `_verifier_plan(fx, *steps)` writing
`fx.root / "verifier-plan.json"`, `_outcomes(fx, identity, role)` reading the `invocation-outcome` records of
`launch_root(fx.loaded().configuration) / "invocation-journal.jsonl"`, and `_verified(fx, *steps)`: an authorized item
launched through its PRODUCER to VERIFY, then the plan written):

1. **No verdict is retried on the same candidate; diagnostics survive** (`test_a_verifier_that_ends_without_a_verdict_
   is_retried_on_the_same_candidate`, plan `["exit"]`). After one VERIFIER launch: stage VERIFY, outcome
   `verifier-retry`, the same `candidate`, `verifier_retries` 1, `verifier_failure` `failure`, no `rejections`. Its
   journal record has kind `failure`, cause `network-or-provider`, `process.exit_status` 1, `process.stderr_tail` of
   length exactly 4000 ending with `(https://provider.invalid/)\n`, and `process.provider` the fake codex's file name;
   it is read from the journal file by a new registry, after the launching one is gone.
2. **Then a real verdict, without a second PRODUCER** (same test): the next launch reaches ACCEPT on the same
   candidate; `fx.runs`: 1 PRODUCER, 2 VERIFIER; the two VERIFIER causes are `["network-or-provider", "accept"]`.
3. **A valid REJECT is still a rejection** (`test_a_valid_reject_is_still_a_rejection`, plan `["reject"]`): stage
   IMPLEMENT, `rejections` 1, last finding source `verifier`, cause `reject`.
4. **A malformed verdict is retried, not a rejection** (`test_a_malformed_verdict_is_retried_not_a_rejection`, plan
   `["malformed"]`): VERIFY, `verifier-retry`, `verifier_failure` `verdict-malformed`, same candidate, no
   `rejections`, cause `malformed-verdict`.
5. **Exhaustion is a typed infrastructure hold** (`test_verifier_retries_end_in_a_typed_infrastructure_hold`, plan
   `["exit", "exit", "exit"]`): after the first two launches `verifier-retry`; after the third, stage VERIFY,
   `authority-block`, `hold_reason` `verifier-infrastructure-exhausted:failure`, same candidate, no `rejections`,
   1 PRODUCER and 3 VERIFIER runs, and an open decision request whose reason contains "no engineering judgment".
6. **A new candidate starts with no retries** (`test_a_new_candidate_starts_with_no_verifier_retries`, budget
   `maximum_attempts` 3, plan `["exit", "reject", "exit", "exit"]`): after two VERIFIER launches the item is at
   IMPLEMENT; after the PRODUCER, VERIFY with `verifier_retries` 0; the next two launches give `verifier-retry` with
   `verifier_retries` 1 then 2 (not a hold).

New file `tests/invocation_runtime/test_worker_diagnostics.py`:

7. **Bounded, redacted, classified diagnostics**:
   - `test_the_cause_is_read_from_the_outcome_and_its_process`, parametrized over: accept, reject, timeout,
     cancelled -> cancellation; failure with "error sending request for url ...", with
     `{"type":"error","message":"workspace routing discovery failed"}` on stdout, and with "getaddrinfo EAI_AGAIN" ->
     network-or-provider; "HTTP 401 Unauthorized: not logged in" -> authentication; exit 127 "codex: not found" ->
     launcher-or-runtime; `verdict-malformed` and `verdict-missing` with exit 0 -> malformed-verdict;
     "500 passed in 12.0s" -> unknown; no diagnostics -> unknown.
   - `test_the_diagnostics_are_bounded`: command `["/opt/bin/codex", "y " * 500]` keeps 200 characters of the
     second argument; streams of `"out line\n" * 1200 + "END-OUT"` and the same for err keep exactly 4000 characters,
     ending with `END-OUT` / `END-ERR`.
   - `test_the_kept_text_is_redacted`: the secrets of the existing proof test (Bearer, `token=`, `sk-proj-...`,
     `ghs_...`, a JWT) are absent from both tails and the command, `[REDACTED]` present, and a 40-hex SHA kept.
   - `test_the_cli_worker_records_each_process`: a real `CliWorkerProvider` running `python -c` (print `out`, write
     `"err line\n" * 600 + "LAST"` to standard error, exit 3) as PRODUCER records exit status 3, `process_kind`
     `failure`, stdout `out`, a 4000-character stderr tail ending `LAST`, and the interpreter's file name as provider.
   - `test_the_cli_worker_records_a_verifier_stopped_by_its_feature_regressions`: as VERIFIER (which runs the feature
     regressions first and fails them here), provider `feature-regressions`, `process_kind` `failure`, and the
     result's exit status.

8. **Mutations, run exactly by the VERIFIER** (each with `PYTHONDONTWRITEBYTECODE=1`; revert after each; each must
   fail its named test and pass when reverted):
   - **M1:** the VERIFIER branch's `if outcome.kind in VERIFIER_INFRASTRUCTURE: return self._retry_verifier(...)`
     restored to `if outcome.kind in {"failure", "timeout"}: return _Advance(current, outcome.kind, {})` ->
     `test_a_verifier_that_ends_without_a_verdict_is_retried_on_the_same_candidate`.
   - **M2:** `if retries > VERIFIER_RETRY_LIMIT:` made `if False:` -> `test_verifier_retries_end_in_a_typed_
     infrastructure_hold`.
   - **M3:** the two `start()` lines `if self._outcome(item.identity) == VERIFIER_RETRY: once.add(item.identity)`
     deleted -> `test_role_orchestration.py::test_producer_success_advances_only_to_verify`.
   - **M4:** in `start` of `real_worker.py`, `"process": process, "cause": cause(outcome.kind, process),` made
     `"process": None, "cause": cause(outcome.kind, None),` -> `test_a_verifier_that_ends_without_a_verdict_is_
     retried_on_the_same_candidate`.
   - **M5:** `"candidate-unavailable"` added to `VERIFIER_INFRASTRUCTURE` -> `tests/composition/test_lifecycle_
     capstone.py::test_an_unpublished_candidate_cannot_be_retrieved_for_verification`.
   - **M6:** the two `malformed-verdict` lines of `cause` deleted -> `test_a_malformed_verdict_is_retried_not_a_
     rejection`.
   - **M7:** `"verifier_retries": 0` removed from the PRODUCER success fields -> `test_a_new_candidate_starts_with_no_
     verifier_retries`.
   - **M8:** in `process_diagnostics`, `redact(stdout)[-TAIL:]` and `redact(stderr)[-TAIL:]` made `stdout[-TAIL:]` and
     `stderr[-TAIL:]` -> `test_worker_diagnostics.py::test_the_kept_text_is_redacted`.

The whole suite at the candidate has no failed or error test case, and
`tools/fitness/check_architecture.py --root src/alienintent --check all` passes.

## 4. Evidence and review record

A prototype of exactly sections 2 and 3, on `bc9a9d8` (not the candidate; for the REVIEWER and PRODUCER only):
`manual/path-to-done/verifier-retry/prototype-on-bc9a9d8.diff`, sha256 `1e710449…012f6`. With it the whole suite gave
2025 passed, 4 skipped, the architecture fitness check passed, and M1-M8 each failed its named test and passed when
reverted (`manual/path-to-done/verifier-retry/prototype-suite-and-mutations.log`). Run against `bc9a9d8`'s own source,
the five new launch tests of checks 1-6 fail and the three changed orchestration tests of 2.7 fail.

**Revision 1 (2026-10-09).** First draft, from the Founder's decision of 2026-10-09 after R2 (`c15a52f6`) and R3
(`fe2db2d3`) of NO-CHANGE were each lost to a VERIFIER process failure with no verdict.
