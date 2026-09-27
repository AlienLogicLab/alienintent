# Python-only AlienIntent factory: complete-cutover acceptance contract

Date: 2026-09-27. Status: **Founder decision — binding, recorded for a future cutover; does not
itself retire anything.**

Recorded via Director inbox handoff `founder-full-python-only-factory-20260927T0306Z`
(2026-09-27T03:04:09Z, relayed by a Founder-authorized observing session (ChatGPT), not acting
as Factory Director). Founder statement, verbatim: "Yes I mean completely turn off node.js and
only use Python AlienIntent for everything."

## Decision

The finish line is stricter than R7 (`WO-220607`, Node/bootstrap execution authority) alone: all
AlienIntent factory runtime, supervision, dispatch, project/issue interaction, admission,
observation, liveness, attention, checkpoint, mailbox and normal launch-command paths must
operate through Python AlienIntent with no Node.js process or Node-backed factory role required.
R7 remains required. R8 (`WO-220608`, b-disp command compatibility alias) and R9 (`WO-220609`,
local Program Director bootstrap orchestration role), including B9 (`WO-220512`, programme
completion or bounded successor custody), must be explicitly reconciled as part of the finish
line, not silently excluded.

All four DAG nodes already exist (`docs/evidence/wave2-dependency-dag.json`: R7, R8, R9, B9) and
already have assigned candidate work-unit identifiers in
`docs/evidence/wave2-candidate-bius.md`: `WO-220607` (R7, `GAP_BLOCKED`), `WO-220608` (R8,
`SEPARATE_AUTHORITY_REQUIRED`), `WO-220512` (B9, `GAP_BLOCKED`), `WO-220609` (R9,
`GAP_BLOCKED`). No new DAG node or candidate identifier is needed to record this decision. This
decision does not itself materialize any of them as GitHub Issues, does not run a fresh Agent
Ready assessment, and does not release anything.

Per the Founder's own direction: the temporary external Python bootstrap modules also require
per-component custody/replacement/consumer disposition — "Python language alone is not enough if
normal operation still depends on ungoverned bootstrap scripts outside canonical AlienIntent."
Existing module/history evidence must be retained; no bulk deletion.

## Boundaries

Do not stop unrelated non-AlienIntent Node tools merely because they use Node.js. Do not stop any
AlienIntent Node service before verified replacement and approved one-writer cutover. Preserve
protocol markers/persisted resource identities, history, security and no-duplicate-effect
protections. No material new external spend. At final cutover: verified single writer, real
workload evidence, no residual AlienIntent Node service/required alias or scheduled Node
launcher, Python self-hosting and rollback/readback — do not stop the current Node service early.

## What this episode did and did not do

This episode recorded this decision durably (this document) and confirmed R7/R8/R9/B9 already
exist as DAG nodes and candidate BIUs, so the requested "add/materialize... if not yet issues"
step reduces to a materialization/audit task, not a design task.

This episode did **not** perform the requested live audit ("audit all installed AlienIntent unit
files, ExecStart commands, launch scripts, aliases and currently running Node processes for
factory ownership; distinguish unrelated developer tools... from factory dependencies") or the
gap-exhaustion audit ("audit whether WO-220607/R7 plus WO-220608/R8 and WO-220512/B9 plus
WO-220609/R9 exhaust factory Node and bootstrap retirement"). Both are substantial, live-system
work distinct from Wave 2 BIU paperwork, and this episode discovered and was actively handling a
real WIP=1 overlap incident (`docs/evidence/wave2-wip-overlap-incident-20260927.md`) at the time
this handoff arrived; per that incident's own disposition, no further release work is authorized
until a tested guard exists, and this cutover's own eventual BIU releases are equally subject to
that constraint. The audit and any resulting BIU progression are deferred to a successor episode
(see the Director inbox handoff carrying this forward).
