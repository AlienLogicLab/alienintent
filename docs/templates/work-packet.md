# Bounded AlienIntent work packet

Governing authority: [agent directive](../migration/agent-packages/GOVERNING_AGENT_DIRECTIVE.md).

## Intent and authority

State the required outcome, task authorization, source baseline, permitted paths,
excluded actions and existing implementation to reuse.

## Repository-state classification

Record current changes and their ownership, content and authority. Known authorized
uncommitted work is admissible. Investigate unexplained changes; resolve conflicting
work. Preserve exact baseline evidence where required.

## Acceptance and execution

Specify observable acceptance criteria, checks, independent review, finding repair,
evidence and meaningful commit requirements. Execute established steps without
routine confirmation. Distinguish local evidence from verified external state.

## Boundaries and continuation

Identify concrete authority gaps, conflicts, destructive operations and unavailable
external prerequisites. State the next authorized step and continue when its actual
prerequisites are satisfied. Keep private history, installation credentials and
operational state out of public artifacts.

## Repair cycles

Repairs must converge monotonically unless authority explicitly changes the target ([SWF-23](../decisions/2026-09-20-convergent-repair-monotonic-progress.md)). A repair records the findings it fixes, the previously satisfied acceptance criteria, the evidence that must be preserved, any evidence explicitly superseded with its authorizing decision, and the replacement proof obligations. Previously verified behavior stays correct; previously valid evidence stays valid or is explicitly superseded. Evidence disappearance without supersession is a regression.
