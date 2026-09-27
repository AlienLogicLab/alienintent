# SWF-29 bootstrap liveness — `scan()`/`gh()` repair

Date: 2026-09-27. Scope: temporary bootstrap liveness service only (SWF-29,
[docs/operations.md § Bootstrap liveness reconciliation](../operations.md)). No Node/B-DISP
product semantics changed, no BIU created. Authorized as bounded non-BIU maintenance by the
Founder-relayed Director inbox handoff `founder-restart-wave2-bindings-liveness-20260927T0047Z`
("The Founder also authorizes bounded repair of the failing temporary SWF-29 bootstrap
liveness service with normal source/custody/verification rules").

## Custody note

`~/.local/share/alienintent-bootstrap/liveness.py` is bootstrap-operator-owned infrastructure,
not a repo artifact (`docs/operations.md` line 215: "Scripts live in
`~/.local/share/alienintent-bootstrap/` and are owned by the bootstrap operator, not by any
session"). That directory is not a git repository. This evidence file is the durable repo-side
record of a fix applied in place at that location; the script itself is not, and should not be,
mirrored into this repository.

## Symptom

`~/.local/state/alienintent/coordinator-liveness.jsonl` recorded an identical
`LIVENESS_CHECK_ERROR` on every 5-minute cycle from at least 2026-09-25T17:15:43Z through
2026-09-26T22:47:37Z (32+ consecutive occurrences, `systemctl --user status
alienintent-liveness` confirmed PID 1182 running continuously since 2026-09-24T06:57:37+07):

```json
{"event": "LIVENESS_CHECK_ERROR", "error": "Expecting value: line 1 column 1 (char 0)", "at": "2026-09-26T22:47:37.266053+00:00"}
```

## Root causes (two independent defects in `liveness.py`)

1. **`gh()` silently swallowed subprocess failures.** It ran `gh` with `capture_output=True`
   and returned `r.stdout` unconditionally, never inspecting `r.returncode` or `r.stderr`. A
   failed `gh` invocation (auth hiccup, transient network error, etc.) returned `""`, and
   `scan()`'s unguarded `json.loads("")` raised exactly the observed `JSONDecodeError`.
2. **`scan()` filtered item titles to a `PY-` prefix left over from Wave 1.** Every current
   Project #1 item is titled `WO-2205xx — ...` (Wave 2 naming); the filter meant that even a
   successful `gh` call would make `scan()` return `[]` unconditionally, silently disabling
   liveness reconciliation rather than crashing — a worse failure mode than the loud one,
   since nothing would ever again distinguish a missing actor from a healthy board.

The `status in EXPECT` clause (limited to `IMPLEMENT`/`VERIFY`/`ACCEPT`) already scopes `scan()`
to nonterminal BIUs that must have an actor; the `PY-` prefix added no correct scoping and
predated the Wave 2 naming convention, so it is removed rather than updated to a new prefix.

## Fix

```diff
 def gh(*a, inp=None):
     r = subprocess.run(["gh", *a], capture_output=True, text=True, input=inp, cwd="/mnt/d/Projects/alienintent")
+    if r.returncode != 0:
+        raise RuntimeError(f"gh {' '.join(a)} failed (exit {r.returncode}): {r.stderr.strip()[:300]}")
     return r.stdout
@@ def scan():
     raw = gh("project", "item-list", "1", "--owner", "AlienLogicLab", "--format", "json", "-L", "500")
     items = json.loads(raw).get("items", [])
-    return [i for i in items if i["title"].startswith("PY-") and i.get("status") in EXPECT
-            and i.get("content", {}).get("number")]
+    return [i for i in items if i.get("status") in EXPECT and i.get("content", {}).get("number")]
```

A nonzero-exit `gh` call now raises a diagnostic `RuntimeError` (command, exit code, first 300
chars of stderr) instead of surfacing as an opaque `JSONDecodeError` two calls later. The
existing `except Exception as e: record({"event": "LIVENESS_CHECK_ERROR", "error": str(e)[:200]})`
catch-all in `main()` (unchanged) now logs that diagnostic message on the next transient
failure, fail-closed with a useful diagnostic per the inbox authorization, and the watch
continues rather than re-emitting anything.

No other function, and no recovery/duplicate-prevention logic (`recover()`, `lane_claims()`,
`wait_for_claim()`, `judgment_suppression()`), was touched.

## Test evidence (TDD: failing test written first, then the fix)

New regression test file: `~/.local/share/alienintent-bootstrap/test_liveness_scan.py` (4
tests), co-located with the existing `test_liveness_suppression.py`. Before the fix, 3 of 4
failed, reproducing the exact recorded error:

```
FAILED test_liveness_scan.py::test_scan_finds_a_current_wo_titled_item_in_an_expected_state
FAILED test_liveness_scan.py::test_gh_raises_a_clear_diagnostic_on_nonzero_exit
FAILED test_liveness_scan.py::test_scan_propagates_the_gh_failure_instead_of_a_bare_json_error
...
E           json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

After the fix, the same 4 tests pass, and the full pre-existing bootstrap suite is unaffected:

```
test_liveness_scan.py::test_scan_finds_a_current_wo_titled_item_in_an_expected_state PASSED
test_liveness_scan.py::test_scan_ignores_items_outside_the_expected_lifecycle_states PASSED
test_liveness_scan.py::test_gh_raises_a_clear_diagnostic_on_nonzero_exit PASSED
test_liveness_scan.py::test_scan_propagates_the_gh_failure_instead_of_a_bare_json_error PASSED
4 passed in 0.04s

142 passed in 5.62s   # full ~/.local/share/alienintent-bootstrap suite, no regressions
```

## Live verification (read-only, no side effects)

- `python3 -c "import liveness; print(liveness.scan())"` against the real Project #1 board
  returned `[]` cleanly (no exception) — consistent with `state.json` showing `active: {}`
  (no in-flight invocations) and no board item currently in `IMPLEMENT`/`VERIFY`/`ACCEPT`
  (#127 and #130 are `TASKS`; the rest are `READY`/`DONE`). `scan()` was called directly and
  read-only; `recover()` (which posts issue comments and toggles the Status field) was never
  invoked, so this check carried no duplicate-recovery risk.
- `systemctl --user restart alienintent-liveness` (safe: `state.json` `active` was empty, so
  no in-flight invocation was disturbed). New PID 2453523 started 2026-09-27T00:54:20Z,
  logged `LIVENESS_WATCH_STARTED`, and completed its first `check_once()` cycle with **no**
  `LIVENESS_CHECK_ERROR` — the first clean cycle since at least 2026-09-25T17:15:43Z.

## Disposition

Fix applied in place at `~/.local/share/alienintent-bootstrap/liveness.py` (operator custody,
not repo-tracked) and `~/.local/share/alienintent-bootstrap/test_liveness_scan.py` (new). This
file is the durable repo-side evidence record; no other repository state changed. This remains
temporary bootstrap infrastructure and still expires when the canonical Python liveness
capability (SF-REQ-056) replaces it — this repair does not extend or re-authorize its
lifetime.
