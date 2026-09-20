# PY-02 quality evidence

This document renders derived measures from [PY-02-quality-evidence.json](PY-02-quality-evidence.json). It does not replace the trajectory or its raw sources.

## Verdict

PY-02 was not accepted on its first candidate. After one independent rejection and one repair cycle, the second candidate was independently accepted, landed by normal merge `ab4efe5`, and recorded DONE. Both required merge-result Actions runs succeeded.

## Derived measurements

| Measure | Value | Interpretation |
|---|---:|---|
| First-pass accepted | false | Candidate `a82ca4e6` was rejected. |
| Producer implementation attempts | 2 | Candidate 1 plus repair candidate. |
| Verifier cycles | 2 | One REJECT, then one ACCEPT. |
| Repair cycles | 1 | One return to IMPLEMENT and repair candidate. |
| Blocking findings | 3 | B1 lifecycle contract, B2 reproducibility/CI, B3 test effectiveness. |
| Human decisions required | 1 | Landing authority, SWF-16. |
| Human attention blocked | 1,832 s | Authority-exception to authority-decision timestamps. |
| Total elapsed | 3,788 s | Release to DONE comment timestamps. |
| Candidate custody failures | 0 | For the two reviewed PY-02 candidates; both were reported identifiable and retrievable. |
| Reproducibility failures | 1 | B2. |
| Ineffective-test detections | 2 | WIP mutation remained green; equal-priority FIFO was unobserved. |
| `RETURN_TO_IMPLEMENT` controls | 1 | The first verifier rejection returned the BIU to IMPLEMENT. Closure-specific count was 0. |
| Closure command count | 46 | Reported by final closure worker. |

Implementation active time (978 seconds), repair interval (212 seconds), and closure interval (2,206 seconds) are defined precisely in the JSON evidence. Closure includes the 1,832-second human authority wait.

## Unknown metrics

Both verifier logs identify `firstParty` / `claude-opus-5` and report $3.999279 of combined list-basis cost. All four producer logs report token fields, but not provider-model identity or cost. End-to-end cost, producer cost, a comparable summed token total, per-command duration, and qualitative human-attention effort are **UNKNOWN**. Unknown is not zero.

## Lessons eligible for future promotion

- **CANDIDATE LEARNING — NOT PROMOTED:** Require clean-environment reproduction for claimed verification commands.
- **CANDIDATE LEARNING — NOT PROMOTED:** Use mutation or proven-red checks to show policy tests can detect removal of the policy.
- **CANDIDATE LEARNING — NOT PROMOTED:** Rework transitions must retain immutable bound contracts while clearing only execution progress.
- **CANDIDATE LEARNING — NOT PROMOTED:** Make closure landing authority explicit in BIU contracts or standing closure policy.

These are retrospective candidates only. This task does not change architecture, policy, skills, contracts, or runtime behavior.
