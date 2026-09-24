# FDH-91 — Issue #91: the host env file must set a PATH that resolves the host's tools

This is the bounded work of existing Issue **#91**, "FDH-01 follow-up P1: live-proof host env must set PATH
so the adapter can run gh", run through #91's own lifecycle. It is a follow-up to FDH-01 (#89). It is not a
Wave 2 DAG node and adds no new Issue.

Baseline: `origin/main` @ `0eda915`.

## Intent

An operator who follows the repository's host procedure and installer must end up with a host that can run
its tools. A missing tool must fail closed with a diagnostic that names it. Today the working
configuration exists only as an operator edit to the live env file. This is one of the two remaining
conditions on the Factory Director Host retirement threshold (Founder direction, 2026-09-24).

## Authority

- Issue #91: its defect statement and bounded scope.
- Founder direction 2026-09-24, relayed through Director inbox entries `founder-operating-mode-20260924T091522Z`
  (P1) and `founder-priority-91-92-20260924T104141Z`: make #91 and #92 the next priority, and prove each fix
  with a discriminating test.

## Current state (evidence)

- `docs/operations/factory-director-host-live-proof.md` step 0a tells the operator to put only
  `FACTORY_DIRECTOR_WORKTREE` and `GH_CONFIG_DIR` in `~/.config/alienintent/factory-director-host.env`.
- `tools/orchestration/install_factory_director_host.sh` seeds a new env file with comments for those two
  variables only.
- The systemd user unit's `PATH` does not include `~/.local/bin`, where `gh` (and the provider CLI) are
  installed. During the FDH-01 live proof the adapter could not run `gh`, and the host stayed at
  `AUTHORITATIVE_STATE_UNAVAILABLE` until an operator added
  `PATH=/home/netmarine/.local/bin:/usr/local/bin:/usr/bin:/bin` to the live env file. Evidence:
  `docs/evidence/fdh-01-live-proof/20260924T080401Z/FINDINGS.txt` (P1) and `README.md` (commit `59db3c5`).
- The host fails closed in this case, so behaviour is safe. The defect is that the procedure and installer do
  not carry the working configuration, and that the resulting diagnostic does not name the missing tool.

## Scope (bounded extent)

1. **Procedure.** In `docs/operations/factory-director-host-live-proof.md` step 0a, and in
   `docs/operations/factory-director-host.md` wherever it describes the env file, require a `PATH` line in
   the host env file. Say why: the systemd user unit does not inherit the login shell's `PATH`. The `PATH`
   must resolve every executable the host runs: `gh` and `python3` (adapter), `git`, and the configured
   provider CLI (`claude` or `codex`).
2. **Installer.** When `install_factory_director_host.sh` seeds a new env file, it also seeds a commented
   `PATH` guidance line. It still never overwrites an existing env file, and never enables or starts the
   unit.
3. **Deterministic preflight** (`DETERMINISTIC_PREFLIGHT`). When the adapter
   (`tools/orchestration/factory_director_inputs.py`) cannot resolve `gh`, it fails closed with a diagnostic
   that names `gh` and the `PATH` it searched. It must not rely on a raw `FileNotFoundError` traceback.
   Keep this within the adapter's existing failure path (`SourceUnavailable`, recorded as the host's
   `failure`), so that `authoritative_state` stays false exactly as today.

## Non-goals

- Changing host behaviour other than the diagnostic text on that failure path, or any predicate or idle
  reason. The predicate change is #92.
- Editing the live `~/.config/alienintent/factory-director-host.env`, installing, or restarting the live
  host. Deployment is a separate, recorded Factory Director action after landing.
- Hard-coding a user-specific path in code. Documentation may show the live installation's value as an
  example.
- Retiring, disabling or removing any continuity mechanism, unit or service.

## Acceptance criteria

1. The live-proof procedure step 0a and the host operations document require a `PATH` in the env file, say
   why, and list the tools it must resolve.
2. Run with `HOME` pointed at a temporary directory, with `systemctl` stubbed, the installer seeds a new env
   file that contains the `PATH` guidance. An existing env file is left byte-identical.
3. When the adapter runs with a `PATH` that cannot resolve `gh`, it exits non-zero with
   `authoritative_state` false in its output, and its recorded failure names `gh` and the searched `PATH`.
   No traceback is printed.
4. With `gh` resolvable (a fake `gh` on `PATH` in tests), adapter behaviour is unchanged. All existing
   adapter, host and docs tests pass.
5. Discriminating proof: the new tests for criteria 2 and 3 (and any docs test for criterion 1) are shown
   **failing** on the baseline `0eda915` code and **passing** on the candidate. Record commands, exit
   statuses and counts.
6. `node scripts/check.mjs all` exits 0. `python3 -m pytest -q tools` shows no new failure. The known baseline
   failure `tools/orchestration/test_director.py::test_substantial_technical_analysis_routes_to_codex_primary`
   is non-hermetic: it reads the live `~/.codex/config.toml`. It is dispositioned as in ARP-01 and must not be
   modified here.

## Verification obligations

An independent VERIFIER retrieves the exact candidate SHA in its own worktree and re-runs criteria 1–6. It
records commands, exit statuses and counts.

## Evidence obligations

Retain the candidate branch and full SHA, the commands, exit codes, test counts and the discrimination
results under `docs/evidence/fdh-91/`.

## Deployment (Factory Director, after landing)

After DONE, the Factory Director refreshes the installed copy under
`~/.local/share/alienintent-bootstrap/factory-director-host/` through the installer from the landed commit,
and restarts the host service between episodes while no Director episode is live. That is a deliberate,
recorded step. It is not a retirement. Workers do not perform this step.

## Execution packet and allocation

- PRODUCER Morty on Claude; independent VERIFIER JC on Codex (Founder routing policy, 2026-09-24).
- Concurrency 1.
- 3 execution cycles and 1 replacement per phase, bound in `execution.biuLimits` for #91 before release.
- Wall-clock bounded by systemd supervision.

Landing: SWF-19. Merge the accepted candidate branch directly into `main`, preserving the accepted SHA.
**Do not open a pull request.** AlienIntent does not use pull requests.

Release authority is not granted by this document.

## Stop and escalation

Stop on:

- a source revision mismatch;
- any need to change a predicate, an idle reason or the host's launch behaviour;
- any need to edit live operator configuration;
- a discriminating test that does not fail on the baseline.

Scope questions go to the Factory Director.
