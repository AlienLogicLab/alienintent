# Work unit: a VERIFIER that ends without a verdict is retried, and every worker process leaves durable diagnostics

**Label:** `VERIFIER-INFRASTRUCTURE-RETRY-AND-DIAGNOSTICS` (a document label; permanent id `8bbe866f-0c73-4189-82a5-d2029ea86042`).
**Status:** Revision 3 (work item `8bbe866f-0c73-4189-82a5-d2029ea86042`, at CAPTURE), 2026-10-09. Reviewed (follow-up check PASS). Not approved, not assessed, not released.
**Position on the path:** first on the autonomy critical path (Founder 2026-10-09): VERIFIER-INFRASTRUCTURE-RETRY-AND-
DIAGNOSTICS -> NO-CHANGE re-issue -> PLAN-AUTHORITY-INHERITANCE -> remaining autonomy blockers -> three-item proof.
**Starting revision:** main `bc9a9d8`. Every line number below is at `bc9a9d8`.
**Roles:** launched by the factory: PRODUCER, a fresh VERIFIER on the exact candidate, CLOSURE through the Landing Authority.

## Contract

```json alienintent-contract
{
 "identity": "8bbe866f-0c73-4189-82a5-d2029ea86042",
 "version": "revision-3",
 "intent": "A VERIFIER whose session ends without a valid verdict (its process fails or times out, or it leaves no verdict, a malformed one or one for another revision) made no engineering judgment: the work item stays at VERIFY on the same custodied candidate and the next launch runs a fresh VERIFIER, at most twice in a row, then a typed infrastructure hold. No rejection is counted and no PRODUCER cycle is used; only a valid REJECT is a rejection. Every worker process's exit status, bounded and redacted output tails (also of a timed-out process), provider, executable, provider session id and command are kept with its outcome in the invocation journal, with the cause they show.",
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
  "the VERIFIER runs mutations M1-M10 of check 8 exactly and records that each makes its named test fail and that reverting makes it pass"
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

   The hold is resumable through the existing `work decide` path: `record_decision` (line 941) re-admits on any
   non-cancel choice, and the carried count then allows exactly one more VERIFIER session before the next hold.

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
CAUSES = ("success", "closed", "accept", "reject", "timeout", "network-or-provider", "authentication",
          "launcher-or-runtime", "malformed-verdict", "cancellation", "unknown")
_RESULTS = frozenset({"success", "closed", "accept", "reject"})
_AUTHENTICATION = re.compile(r"unauthori[sz]ed|forbidden|not logged in|log ?in required|authentication failed|"
                             r"invalid api key|token (?:has )?expired", re.I)
_SESSION = re.compile(r"session[ _]id\"?\s*[:=]\s*\"?([0-9A-Za-z]{8}(?:-[0-9A-Za-z]{4,12}){1,4})", re.I)
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


def process_diagnostics(provider: str, command: Sequence[str], kind: str, exit_status: int | None, stdout: str,
                        stderr: str) -> dict[str, object]:
    """The bounded, redacted record of one process: its provider and executable, the provider's session id when its
    output names one, its command, its result kind and exit status, and the last TAIL characters of each stream."""
    session = _SESSION.search(f"{stderr}\n{stdout}")
    return {"provider": provider, "executable": Path(command[0]).name if command else None,
            "session_id": None if session is None else redact(session.group(1)),
            "command": [redact(argument)[:ARGUMENT] for argument in command],
            "process_kind": kind, "exit_status": exit_status,
            "stdout_tail": redact(stdout)[-TAIL:], "stderr_tail": redact(stderr)[-TAIL:]}


def cause(outcome_kind: str, diagnostics: dict[str, object] | None) -> str:
    """The cause of an invocation's outcome, from its kind and its last process's diagnostics. A process ended by a
    signal (a negative exit status: an operator kill, a shutdown) is a cancellation."""
    if outcome_kind in _RESULTS:
        return outcome_kind
    if outcome_kind in {"cancelled", "cancellation"}:
        return "cancellation"
    if outcome_kind == "timeout":
        return "timeout"
    exit_status = None if diagnostics is None else diagnostics.get("exit_status")
    if isinstance(exit_status, int) and exit_status < 0:
        return "cancellation"
    if outcome_kind in _VERDICT and exit_status == 0:
        return "malformed-verdict"
    if exit_status == 0:
        return "unknown"  # the process succeeded: its text says nothing about why the outcome failed
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
beside it, and `unknown` is the default; a process that exited 0 has no cause read from its text (`unknown`). A
negative exit status (the process ended by a signal: an operator kill, a
shutdown) is `cancellation`; a live process never returns the `cancelled` kind through `run`. `provider` is the
process adapter's configured provider (`capabilities.provider`; `routed` in the registry), `executable` the
command's file name (`codex`, `claude`) and `session_id` the id a provider prints as `session id: ...` or
`"session_id": "..."`, searched in the whole streams before they are cut.

### 2.4 The CLI worker records each process (`invocation_runtime/adapters/cli_worker.py`)

1. After the `process_ownership` import (line 15) add
   `from alienintent.invocation_runtime.domain.diagnostics import process_diagnostics`.
2. After `_VARIABLE = re.compile(...)` (line 29) add, after two blank lines:

```python
def _decoded(data: bytes | str | None) -> str:
    """A partial stream as text: `TimeoutExpired` carries it as bytes, or None when nothing was read."""
    return data.decode(errors="replace") if isinstance(data, bytes) else data or ""
```

3. After `self.outputs: dict[str, tuple[str, str]] = {}` (line 86) add:

```python
        # Per invocation, the bounded diagnostics of its last process (the worker journals them with its outcome).
        self.diagnostics: dict[str, dict[str, object]] = {}
```

4. In `run`, the feature-regression early return (lines 207-209) becomes:

```python
            if regression.kind != "success":
                self._completed.add(invocation_id)
                self.diagnostics[invocation_id] = process_diagnostics(self.capabilities.provider, ["feature-regressions"],
                                                                      regression.kind, regression.exit_status, "", "")
                return regression
```

5. From `argv, text = self._command(invocation_id, role, workspace)` (line 210) to the end of `run` (line 239), the
   method reads exactly:

```python
        argv, text = self._command(invocation_id, role, workspace)
        command = list(argv)  # the provider command alone, before any worker-user prefix and its environment
        environment = self._child_environment(invocation_id, role)
        if self._worker_user is not None:
            # The sudo rule replaces the environment: `env -i` and the allowlisted variables only.
            argv, environment = [*worker_prefix(self._worker_user, environment), *argv], None
        deadline = time.monotonic() + wall_clock_seconds
        stdin = None if text is None else subprocess.PIPE
        process = subprocess.Popen(argv, cwd=workspace, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment, start_new_session=True)
        self._active[invocation_id] = process
        stdout = stderr = ""
        result: ProcessResult | None = None
        try:
            try:
                stdout, stderr = process.communicate(input=text, timeout=wall_clock_seconds)
                # Diagnostics only (the end of each stream), for a person reading why a worker failed.
                self.outputs[invocation_id] = (stdout[-OUTPUT_TAIL:], stderr[-OUTPUT_TAIL:])
            except subprocess.TimeoutExpired as expired:
                stdout, stderr = _decoded(expired.stdout), _decoded(expired.stderr)  # what it wrote before the deadline
                result = ProcessResult("timeout", self._stop(invocation_id, process), not self._owned(invocation_id, process), BudgetRecord.unknown())
                return result
            if not self._await_owned(invocation_id, process, deadline):
                self._stop(invocation_id, process)
                result = ProcessResult("timeout", process.returncode, not self._owned(invocation_id, process), BudgetRecord.unknown())
                return result
            result = ProcessResult("success" if process.returncode == 0 else "failure", process.returncode, True, BudgetRecord.unknown())
            return result
        except BaseException:
            # An unexpected failure must not leave owned work running unobserved.
            self._stop(invocation_id, process)
            raise
        finally:
            self._active.pop(invocation_id, None)
            if result is not None:
                self.diagnostics[invocation_id] = process_diagnostics(self.capabilities.provider, command, result.kind,
                                                                      result.exit_status, stdout, stderr)
            # Finished only when nothing it owns is still observed; otherwise
            # a later cancel answers unresolved rather than already-finished.
            if not self._owned(invocation_id, process):
                self._completed.add(invocation_id)
```

### 2.5 The worker journals them (`invocation_runtime/application/real_worker.py`)

1. Before the `runtime` import (line 17) add `from alienintent.invocation_runtime.domain.diagnostics import cause`.
2. `start` (lines 266-288) is replaced by exactly these three methods (the old body moves into `_journaled`
   unchanged except for the diagnostics lines; diagnostics are always taken, so none is left behind without a journal
   or when `_start` raises):

```python
    def start(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str], budget: BudgetPolicy) -> WorkerOutcome:
        """Run one role invocation; with a journal, retain its attributable outcome durably first."""
        try:
            return self._journaled(invocation, context, grants, budget)
        finally:
            self._diagnostics(invocation.correlation_id)  # never left behind, whatever happened

    def _diagnostics(self, correlation: str) -> dict[str, object] | None:
        """The bounded diagnostics of the invocation's last process, taken from the process adapter (None without)."""
        kept = getattr(self._process, "diagnostics", None)
        return kept.pop(correlation, None) if isinstance(kept, dict) else None

    def _journaled(self, invocation: WorkerInvocation, context: BiuContract | None, grants: frozenset[str],
                   budget: BudgetPolicy) -> WorkerOutcome:
        if self._journal is None:
            outcome = self._start(invocation, context, grants, budget)
            # Every returned outcome, including an early refusal, must read back.
            self._outcomes[invocation.correlation_id] = outcome
            return outcome
        attribution = {
            "correlation_id": invocation.correlation_id, "work_identity": invocation.work_identity, "role": invocation.role,
            "contract_digest": None if context is None else context.content_digest,
        }
        # The owner is attestable later only if every process the invocation
        # starts carries its markers; otherwise surviving work is unobservable.
        marked = getattr(self._process, "marks_owned_work", False) is True
        owner = None if self._ownership is None or not marked else self._ownership.current()
        self._journal.append({"event": "invocation-started"} | attribution | ({} if owner is None else {"owner": dict(owner)}))
        outcome = self._start(invocation, context, grants, budget)
        retry = self.retry_evidence.get(invocation.correlation_id)
        # The last process's bounded diagnostics and the cause they show, kept with the outcome so they outlive the
        # launcher (a process adapter without diagnostics records none; of several attempts, the last).
        process = self._diagnostics(invocation.correlation_id)
        self._journal.append({"event": "invocation-outcome"} | attribution | {
            "attempt": None if retry is None else retry.attempts, "kind": outcome.kind, "candidate": encode_candidate(outcome.candidate),
            "findings": list(outcome.findings), "receipts": list(outcome.receipts),
            "process": process, "cause": cause(outcome.kind, process),
        })
        return outcome
```

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

- `tests/composition/test_worker_launch.py`, the fake provider `FAKE_PROVIDER` (a format string: braces doubled): after
  `role = os.environ.get("ALIENINTENT_ROLE")` (line 70) add two blank lines and exactly:

```python
def verifier_document():
    """The next step of `verifier-plan.json` (accept when none): exit (no verdict), malformed, reject or accept."""
    steps_path = Path({plan!r}).with_name("verifier-plan.json")
    steps = json.loads(steps_path.read_text()) if steps_path.exists() else []
    step = steps.pop(0) if steps else "accept"
    steps_path.write_text(json.dumps(steps))
    if step == "exit":
        sys.stderr.write("progress line\n" * 500 + "error sending request for url (https://provider.invalid/)\n")
        sys.exit(1)
    if step == "malformed":
        return {{"revision": head, "verdict": "maybe", "findings": []}}
    if step == "reject":
        return {{"revision": head, "verdict": "reject", "findings": ["VERIFIER-REJECT-FINDING"]}}
    return {{"revision": head, "verdict": "accept", "findings": []}}

```

  then two blank lines before `record = {{...`. The two verdict writes become `Path(verdict).write_text(json.dumps(
  verifier_document()))` (line 101) and, in the `else:` branch, `document = verifier_document()` as its first line and
  `Path(".alienintent/verdict.json").write_text(json.dumps(document))` (line 104). With no plan file every VERIFIER
  accepts, as today.

No other existing test changes.

## 3. Acceptance checks

The test code is given exactly at the end of this section; the list states what each test proves.

New tests in `tests/composition/test_worker_launch.py` (helpers `_verifier_plan(fx, *steps)` writing
`fx.root / "verifier-plan.json"`, `_outcomes(fx, identity, role)` reading the `invocation-outcome` records of
`launch_root(fx.loaded().configuration) / "invocation-journal.jsonl"`, and `_verified(fx, *steps)`: an authorized item
launched through its PRODUCER to VERIFY, then the plan written):

1. **No verdict is retried on the same candidate; diagnostics survive** (`test_a_verifier_that_ends_without_a_verdict_
   is_retried_on_the_same_candidate`, plan `["exit"]`). After one VERIFIER launch: stage VERIFY, outcome
   `verifier-retry`, the same `candidate`, `verifier_retries` 1, `verifier_failure` `failure`, no `rejections`. Its
   journal record has kind `failure`, cause `network-or-provider`, `process.exit_status` 1, `process.stderr_tail` of
   length exactly 4000 ending with `(https://provider.invalid/)\n`, and `process.executable` the fake codex's file name;
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
   - `test_the_cause_is_read_from_the_outcome_and_its_process`, parametrized over cases including: accept, reject, timeout,
     cancelled -> cancellation; failure with "error sending request for url ...", with
     `{"type":"error","message":"workspace routing discovery failed"}` on stdout, and with "getaddrinfo EAI_AGAIN" ->
     network-or-provider; "HTTP 401 Unauthorized: not logged in" -> authentication; exit 127 "codex: not found" ->
     launcher-or-runtime; `verdict-malformed` and `verdict-missing` with exit 0 -> malformed-verdict;
     "500 passed in 12.0s" -> unknown; no diagnostics -> unknown.
   - `test_the_diagnostics_are_bounded`: command `["/opt/bin/codex", "y " * 500]` keeps 200 characters of the
     second argument; streams of `"out line\n" * 1200 + "END-OUT"` and the same for err keep exactly 4000 characters,
     ending with `END-OUT` / `END-ERR`.
   - `test_the_session_id_is_an_id_and_redacted`: a bare word after `session id =` is not an id; a token-like value
     is never kept as the session id; a provider's UUID `session_id` is.
   - `test_the_kept_text_is_redacted`: the secrets of the existing proof test (Bearer, `token=`, `sk-proj-...`,
     `ghs_...`, a JWT) are absent from both tails and the command, `[REDACTED]` present, and a 40-hex SHA kept.
   - `test_the_cli_worker_records_each_process`: a real `CliWorkerProvider` running `python -c` (print `out`, write
     `"err line\n" * 600 + "LAST"` to standard error, exit 3) as PRODUCER records exit status 3, `process_kind`
     `failure`, stdout `out`, a 4000-character stderr tail ending `LAST`, provider `python` and the interpreter's
     file name as executable.
   - `test_the_cli_worker_keeps_what_a_timed_out_process_wrote`: a process that prints `partial` and a `session id:`
     line, then sleeps past a 2-second wall clock, records kind `timeout`, stdout `partial` and that session id.
   - `test_the_cli_worker_records_a_verifier_stopped_by_its_feature_regressions`: as VERIFIER, the adapter runs the
     feature regressions first; in a bare temporary folder they fail, and executable `feature-regressions`,
     `process_kind` `failure` and the result's exit status are recorded.

8. **Mutations, run exactly by the VERIFIER** (each with `PYTHONDONTWRITEBYTECODE=1`; revert after each; each must
   fail its named test and pass when reverted):
   - **M1:** the VERIFIER branch's `if outcome.kind in VERIFIER_INFRASTRUCTURE: return self._retry_verifier(...)`
     restored to `if outcome.kind in {"failure", "timeout"}: return _Advance(current, outcome.kind, {})` ->
     `test_a_verifier_that_ends_without_a_verdict_is_retried_on_the_same_candidate`.
   - **M2:** `if retries > VERIFIER_RETRY_LIMIT:` made `if False:` -> `test_verifier_retries_end_in_a_typed_
     infrastructure_hold`.
   - **M3:** the two `start()` lines `if self._outcome(item.identity) == VERIFIER_RETRY: once.add(item.identity)`
     deleted -> `test_role_orchestration.py::test_producer_success_advances_only_to_verify`.
   - **M4:** in `_journaled` of `real_worker.py`, `"process": process, "cause": cause(outcome.kind, process),` made
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
   - **M9:** the two lines of `cause` that make a negative exit status `cancellation` deleted ->
     `test_worker_diagnostics.py::test_the_cause_is_read_from_the_outcome_and_its_process`.
   - **M10:** in `run`, the line `stdout, stderr = _decoded(expired.stdout), _decoded(expired.stderr)` deleted ->
     `test_worker_diagnostics.py::test_the_cli_worker_keeps_what_a_timed_out_process_wrote`.

The whole suite at the candidate (`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` at the
repository root) has no failed or error test case, and `python3 tools/fitness/check_architecture.py --root
src/alienintent --check all` passes.

The new tests, exactly. At the end of `tests/composition/test_worker_launch.py`, after two blank lines:

```python
# --- VERIFIER-INFRASTRUCTURE-RETRY-AND-DIAGNOSTICS ------------------------------------------------------------------

def _verifier_plan(fx: Launch, *steps: str) -> None:
    (fx.root / "verifier-plan.json").write_text(json.dumps(list(steps)))


def _outcomes(fx: Launch, identity: str, role: str) -> list[dict]:
    path = launch_root(fx.loaded().configuration) / "invocation-journal.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    return [r for r in records if r.get("event") == "invocation-outcome" and r.get("work_identity") == identity
            and r.get("role") == role]


def _verified(fx: Launch, *steps: str):
    """An authorized item launched through its PRODUCER to VERIFY, with the VERIFIER's next steps planned."""
    item = fx.authorized("UNIT")
    fx.launch(item.id)
    _verifier_plan(fx, *steps)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.VERIFY
    return item, state


def test_a_verifier_that_ends_without_a_verdict_is_retried_on_the_same_candidate(fx):
    """Checks 1 and 2: a VERIFIER process that exits non-zero with no verdict (here after a network-style error)
    leaves the item at VERIFY on the same candidate; the next launch runs a fresh VERIFIER that accepts, without a
    second PRODUCER. The process's bounded diagnostics are in the invocation journal after the launcher exited."""
    item, before = _verified(fx, "exit")
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert (state.stage, state.outcome) == (LifecycleStage.VERIFY, "verifier-retry")
    assert state.candidate == before.candidate and state.record["verifier_retries"] == 1
    assert state.record["verifier_failure"] == "failure" and not state.record.get("rejections")
    [failed] = _outcomes(fx, item.id, "VERIFIER")
    process = failed["process"]
    assert (failed["kind"], failed["cause"], process["exit_status"]) == ("failure", "network-or-provider", 1)
    assert len(process["stderr_tail"]) == 4000 and process["stderr_tail"].endswith("(https://provider.invalid/)\n")
    assert process["executable"] == Path(str(fx.codex)).name
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.ACCEPT and state.candidate == before.candidate
    assert (len(fx.runs("PRODUCER")), len(fx.runs("VERIFIER"))) == (1, 2)
    assert [r["cause"] for r in _outcomes(fx, item.id, "VERIFIER")] == ["network-or-provider", "accept"]


def test_a_malformed_verdict_is_retried_not_a_rejection(fx):
    """Check 4."""
    item, before = _verified(fx, "malformed")
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert (state.stage, state.outcome, state.record["verifier_failure"]) == (
        LifecycleStage.VERIFY, "verifier-retry", "verdict-malformed")
    assert state.candidate == before.candidate and not state.record.get("rejections")
    assert _outcomes(fx, item.id, "VERIFIER")[-1]["cause"] == "malformed-verdict"


def test_a_valid_reject_is_still_a_rejection(fx):
    """Check 3: a valid REJECT takes the normal rework path."""
    item, _ = _verified(fx, "reject")
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.IMPLEMENT and state.record["rejections"] == 1
    assert state.record["findings"][-1]["source"] == "verifier"
    assert _outcomes(fx, item.id, "VERIFIER")[-1]["cause"] == "reject"


def test_verifier_retries_end_in_a_typed_infrastructure_hold(fx):
    """Check 5: after VERIFIER_RETRY_LIMIT retries in a row, a typed hold naming the infrastructure, never a verdict,
    a rejection or a PRODUCER cycle."""
    item, before = _verified(fx, "exit", "exit", "exit")
    for retries in (1, 2):
        fx.launch(item.id)
        assert fx.loaded().coordinator(None, None).state(item.id).outcome == "verifier-retry"
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert (state.stage, state.outcome, state.record["hold_reason"]) == (
        LifecycleStage.VERIFY, "authority-block", "verifier-infrastructure-exhausted:failure")
    assert state.candidate == before.candidate and not state.record.get("rejections")
    assert (len(fx.runs("PRODUCER")), len(fx.runs("VERIFIER"))) == (1, 3)
    [request] = [r for r in fx.store.read_state("registry", "decision-inbox")[1]["open"].values()
                 if r["work_item"] == item.id]
    assert "no engineering judgment" in request["reason"]


def test_a_new_candidate_starts_with_no_verifier_retries(fx):
    """Check 6. The retry count belongs to one candidate: after a rejection and a new PRODUCER candidate it starts
    again."""
    item = fx.authorized("UNIT", budget_policy={"maximum_attempts": 3, "hard_wall_clock_seconds": 120, "cancellation_limit": 1})
    fx.launch(item.id)
    _verifier_plan(fx, "exit", "reject", "exit", "exit")
    for _ in range(2):
        fx.launch(item.id)
    assert fx.loaded().coordinator(None, None).state(item.id).stage is LifecycleStage.IMPLEMENT
    fx.launch(item.id)
    state = fx.loaded().coordinator(None, None).state(item.id)
    assert state.stage is LifecycleStage.VERIFY and state.record["verifier_retries"] == 0
    for retries in (1, 2):
        fx.launch(item.id)
        state = fx.loaded().coordinator(None, None).state(item.id)
        assert (state.outcome, state.record["verifier_retries"]) == ("verifier-retry", retries)
```

The new file `tests/invocation_runtime/test_worker_diagnostics.py`:

```python
"""Bounded worker-process diagnostics and the cause they show (VERIFIER-INFRASTRUCTURE-RETRY-AND-DIAGNOSTICS)."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

from alienintent.invocation_runtime.adapters.cli_worker import CliWorkerProvider
from alienintent.invocation_runtime.domain.diagnostics import ARGUMENT, TAIL, cause, process_diagnostics
from alienintent.invocation_runtime.domain.runtime import InvocationRole

DIMENSIONS = frozenset({"wall-clock", "cancellation"})


def failed(stdout: str = "", stderr: str = "", exit_status: int | None = 1) -> dict[str, object]:
    return process_diagnostics("codex", ["/opt/bin/codex", "exec"], "failure", exit_status, stdout, stderr)


@pytest.mark.parametrize(("kind", "diagnostics", "expected"), [
    ("success", failed(stdout="tests for 401 Unauthorized handling passed", exit_status=0), "success"),
    ("closed", None, "closed"),
    ("accept", None, "accept"),
    ("reject", None, "reject"),
    ("timeout", None, "timeout"),
    ("cancelled", None, "cancellation"),
    ("failure", failed(exit_status=-15), "cancellation"),
    ("failure", failed(stderr="error sending request for url (https://chatgpt.com/x)"), "network-or-provider"),
    ("failure", failed(stdout='{"type":"error","message":"workspace routing discovery failed"}'), "network-or-provider"),
    ("failure", failed(stderr="getaddrinfo EAI_AGAIN api.example"), "network-or-provider"),
    ("failure", failed(stderr="error sending request (status 401), will retry"), "network-or-provider"),
    ("failure", failed(stderr="HTTP 401 Unauthorized: not logged in"), "authentication"),
    ("failure", failed(exit_status=127, stderr="codex: not found"), "launcher-or-runtime"),
    ("verdict-malformed", process_diagnostics("codex", ["codex"], "success", 0, "", ""), "malformed-verdict"),
    ("verdict-missing", process_diagnostics("codex", ["codex"], "success", 0, "", ""), "malformed-verdict"),
    ("failure", failed(stderr="500 passed in 12.0s"), "unknown"),
    ("candidate-unavailable", failed(stdout="test_x timed out", exit_status=0), "unknown"),
    ("failure", None, "unknown"),
])
def test_the_cause_is_read_from_the_outcome_and_its_process(kind, diagnostics, expected):
    assert cause(kind, diagnostics) == expected


def test_the_diagnostics_are_bounded():
    record = process_diagnostics("routed", ["/opt/bin/codex", "y " * 500], "failure", 1, "out line\n" * 1200 + "END-OUT",
                                 "session id: 01a11efe-394f-7961\n" + "err line\n" * 1200 + "END-ERR")
    assert (record["provider"], record["executable"], record["session_id"]) == ("routed", "codex", "01a11efe-394f-7961")
    assert [len(argument) for argument in record["command"]] == [len("/opt/bin/codex"), ARGUMENT]
    assert len(record["stdout_tail"]) == TAIL and record["stdout_tail"].endswith("END-OUT")
    assert len(record["stderr_tail"]) == TAIL and record["stderr_tail"].endswith("END-ERR")
    assert (record["process_kind"], record["exit_status"]) == ("failure", 1)


def test_the_session_id_is_an_id_and_redacted():
    assert failed(stderr="the session id = ABCDEFGHIJ")["session_id"] is None
    assert failed(stdout="curl -d session_id=sk-proj-ABCDEFGH-IJKLMNOPQRSTUV")["session_id"] != "sk-proj-ABCDEFGH-IJKLMNOPQRSTUV"
    assert failed(stdout='{"session_id":"01a11efe-394f-7961-afd7-0a801bb17e76"}')["session_id"] == \
        "01a11efe-394f-7961-afd7-0a801bb17e76"


def test_the_kept_text_is_redacted():
    sha = "a" * 40
    secret_text = (f"commit {sha} Authorization: Bearer abc.def token=s3cr3t sk-proj-ABCDEFGHIJKLMNOP "
                   "ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345 eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl")
    record = process_diagnostics("codex", ["codex", "--api-key=sk-proj-ABCDEFGHIJKLMNOP"], "failure", 1, secret_text,
                                 secret_text)
    for kept in (record["stdout_tail"], record["stderr_tail"], " ".join(record["command"])):
        assert "[REDACTED]" in kept
        for secret in ("abc.def", "s3cr3t", "sk-proj-ABCDEFGHIJKLMNOP", "ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345",
                       "eyJhbGciOiJIUzI1NiJ9"):
            assert secret not in kept
    assert sha in record["stdout_tail"]


def test_the_cli_worker_records_each_process(tmp_path: Path):
    script = "import sys; print('out'); sys.stderr.write('err line\\n' * 600 + 'LAST'); sys.exit(3)"
    cli = CliWorkerProvider("python", sys.executable, ("-c", script), "explicit", DIMENSIONS)
    result = cli.run("invocation-1", InvocationRole.PRODUCER, tmp_path, 10)
    record = cli.diagnostics["invocation-1"]
    assert (result.kind, record["process_kind"], record["exit_status"]) == ("failure", "failure", 3)
    assert record["stdout_tail"].strip() == "out" and len(record["stderr_tail"]) == TAIL
    assert record["stderr_tail"].endswith("LAST")
    assert (record["provider"], record["executable"]) == ("python", Path(sys.executable).name)


def test_the_cli_worker_keeps_what_a_timed_out_process_wrote(tmp_path: Path):
    script = ("import sys, time; print('partial', flush=True); sys.stderr.write('session id: 0a1b2c3d-4e5f\\n');"
              " sys.stderr.flush(); time.sleep(30)")
    cli = CliWorkerProvider("python", sys.executable, ("-c", script), "explicit", DIMENSIONS)
    result = cli.run("invocation-3", InvocationRole.PRODUCER, tmp_path, 2)
    record = cli.diagnostics["invocation-3"]
    assert (result.kind, record["process_kind"]) == ("timeout", "timeout")
    assert record["stdout_tail"].strip() == "partial" and record["session_id"] == "0a1b2c3d-4e5f"


def test_the_cli_worker_records_a_verifier_stopped_by_its_feature_regressions(tmp_path: Path):
    cli = CliWorkerProvider("python", sys.executable, ("-c", "pass"), "explicit", DIMENSIONS)
    result = cli.run("invocation-2", InvocationRole.VERIFIER, tmp_path, 10)
    record = cli.diagnostics["invocation-2"]
    assert result.kind == "failure" and (record["executable"], record["process_kind"]) == ("feature-regressions", "failure")
    assert record["exit_status"] == result.exit_status
```

### Stated limits (not in this item)

- No spacing between VERIFIER retries beyond one per launch or `start()` call (and the REGRESSION-GATE suite run before
  each session); a director launching back to back can spend the three sessions inside one outage, ending in the
  typed hold.
- A VERIFIER that wrote a valid verdict and then exited non-zero is retried, not trusted: `_evaluate` returns the
  process kind before `read_verdict` (`real_worker.py` lines 352-354), unchanged here.
- A coordinator `cancel` during a running VERIFIER is not signalled to that process (it is keyed by correlation, the
  cancel names the work item); its later result can overwrite `cancelled-by-operator`, as an accept or success already
  can today.
- A VERIFIER retry recorded by `_recover` at the start of a `start()` call may run again in that same call.
- `feature-regressions-missing` (REGRESSION-GATE could not run) still holds: the candidate itself may be what cannot
  run.
- Outside the registry, a VERIFIER stopped by the CLI adapter's own feature regressions (`cli_worker.py` lines 204-209;
  the registry passes `feature_regressions=False`, `work_registry.py` line 721, and uses REGRESSION-GATE, whose
  findings are a `reject`) returns `failure` and is retried, then held, although the candidate failed its tests.


## 4. Evidence and review record

A prototype of exactly sections 2 and 3, on `bc9a9d8` (not the candidate; for the REVIEWER and PRODUCER only):
`manual/path-to-done/verifier-retry/prototype-on-bc9a9d8.diff`, sha256 `d70b0310…f2aaa`. With it the whole suite
(the command above) gave 2032 passed, 4 skipped, the architecture fitness check passed, and M1-M10 each failed its named test and
passed when reverted (`manual/path-to-done/verifier-retry/prototype-suite-and-mutations.log`). Run against `bc9a9d8`'s
own source, the new launch tests of checks 1-6 fail and the three changed orchestration tests of 2.7 fail. (The
REGRESSION-GATE counts its own runs differently: 2913 test cases for the NO-CHANGE candidates.)

**Revision 3 (2026-10-09).** Follow-up REVIEWER of `a5a5783` (FAIL; 6 findings). Fixed: the contract binds M1-M10 and
its version is `revision-3` (2); the session id is UUID-like only and redacted (3); a successful process's text is
never read as a cause (`unknown`) (4); the prose of checks 1 and 7 and M4 matches the exact code, the test docstrings
name their checks, and `_decoded` sits after the constants with two blank lines on each side (5). Stated limit: the
CLI adapter's own feature regressions outside the registry (1). Finding 6 is stated in 2.3 (`provider` is `routed` in
the registry).

**Revision 2 (2026-10-09).** REVIEWER of `6cf3db4` (FAIL; 11 findings). Fixed: a negative exit status is
`cancellation` (1); `success` and `closed` keep their kind as cause (2); a timed-out process keeps what it wrote (3);
`provider` is the configured provider, with `executable` and `session_id` added (4); authentication matches words, not
bare 401/403, so network text with a status code stays network (8); diagnostics are always taken, also without a
journal or when `_start` raises (10); the hold sentence names `record_decision` (6); the test code is given exactly and
the suite command is named (Q2). Stated limits: findings 5, 6 (spacing), 7, 9 and 11 (the tool's lazy import, like its
other `alienintent` imports). New mutations M9, M10.

**Revision 1 (2026-10-09).** First draft, from the Founder's decision of 2026-10-09 after R2 (`c15a52f6`) and R3
(`fe2db2d3`) of NO-CHANGE were each lost to a VERIFIER process failure with no verdict.
