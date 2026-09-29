# Candidate work sequence — Python factory builds AlienIntent

**Status:** Draft decomposition. The first item received a native Agent Ready READY assessment on 2026-09-29, bound to its exact text; it has not been released to Claude. The remaining items require their own assessments. Use the current Python code where it already works; the PY-10 sandbox proved prepared-work execution, automatic refill and restart with six seeded tasks.

Issue 125 completes under the Node factory first. After its custody and completed state are read back, a separate owner shuts down Node and its managed services. During the [hand-fed build period](../../operations/manual-python-build-handoff.md), Claude and Codex use separate temporary working directories and an independent closure process lands verified work and moves it to completed. No Python or Node writer shares the same live profile.

| Order | Small work unit | Independent result |
|---|---|---|
| 1 | [Hand assessed work to the live queue](PY-SELF-01.md) | An exact, approved Python-prepared work contract appears once in the runner's real work queue, with safe refusal on stale assessment or uncertain write. |
| 2 | Admit real AlienIntent requirements through the existing preparation path | One authorized AlienIntent requirement, its resolved questions, approved design, proof obligations and bounded work contract reach the assessment service without hand-maintained intermediate files. Separate this further if assessment finds independent decisions. |
| 3 | Gate acceptance on product and code quality | A fresh Codex review of Claude's exact candidate checks source intent, design, domain boundaries, Python quality, duplicated behavior, anti-patterns, regression and actual outcome. Wrong but plausible code and unsupported proof cannot reach acceptance. |
| 4 | Controlled self-building run | Claude builds a small AlienIntent change under Python control; Codex independently checks it; an independent closure step lands and proves the result; Python restarts and takes the next eligible work unit without manual lane movement. |
| 5 | Prevent new leftovers | Every new working directory, branch, process and evidence object has a named owner, size/time bound and removal rule, including crash and rejected-work paths. |
| 6 | Inventory old leftovers | After issue 125 and Node shutdown, join each old directory and branch to its claim, work item, evidence, pending effect and retention rule; record unknown ownership without deleting it. |
| 7 | Remove proved leftovers | Review the inventory, preserve recovery references, remove only entries with no active owner or needed evidence, and verify the resulting repository state. |

**Order of work:** assess each packet independently, revise or split when Agent Ready says so, then release one at a time. Before a release, the exact prior work and writer shutdown must be read back. A separate closure owner and the cleanup rules in the hand-fed build plan apply to every packet. The preparation path and live runner already exist as separate Python compositions; the first packet joins them. The second gives the joined path a genuine AlienIntent requirement. The third enforces product quality before acceptance. The fourth is a proof packet. The final three units separate prevention, inventory and deletion so cleanup cannot silently discard active work.

**Review standard for every change:** Claude supplies a published exact candidate and concrete checks; Codex reviews it independently for architecture, clean Python, resource lifetime, maintainability, anti-patterns and agent slop, as well as correct behavior. Preserve proof when repairing a finding. A reviewer who cannot retrieve the candidate or reproduce a required check must hold it.

**First factory flywheel claim:** the factory starts from an authorized requirement, prepares its own assessed work, performs a real code change, independently reviews and closes that work, cleans up its temporary resources, recovers from restart and selects the next eligible item. A second pre-seeded task alone does not prove preparation.
