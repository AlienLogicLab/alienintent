# PY-04 execution trajectory

PY-04 ran from release at 06:27:42Z to DONE at 12:31:12Z. It retained an initial unpublished safety-reviewed candidate, then accumulated nine Issue-recorded verifier rejections before `03896f62` was accepted. The one measured genuine Founder wait was the SWF-22 custody decision: 7,074 seconds. The initial exception was later classified by the coordinator as unfinished contracted work, not missing authority.

The accepted candidate `03896f62` is the second parent of normal merge `0170af0`; Git confirms ancestry and a scoped accepted-parent-to-merge diff is empty. Closure cited SWF-19 and reported post-merge 65 Python tests, architecture fitness, Node suite, and required Actions. Those local test claims are worker/coordinator observations; the cited Actions records are the independently retrievable CI evidence.

## Rejection taxonomy

The JSONL preserves ten rejection-class events: an initial behavioral safety finding; behavioral rejections on `10fb82ef` and `c14beb6e`; custody identity work on `a73baf72`; evidence/proof rejections on `847c90c8`, `5cb53b27`, `468cb562`, and `1b372c2a`; process-instruction adherence on `064432a7`; and candidate-identity/publication failure where no reviewable candidate was recorded. These labels are evidence-local classifications, not v1 schema authority.

## Mutation and monotonic repair evidence

SWF-26 records a verifier-defined battery with five survivors M4/M10/M14/M20/M22, coordinator reproduction, and an additional M1 survivor caused by semantically different implementations. The accepted candidate added M1 proof and the final verifier reported red-green confirmation. No durable source inspected here supports claiming a final full-battery 23/23 or 24/24 total; it remains UNKNOWN. Coordinator comments requiring additive repairs and the sequence of retained candidates are observed monotonic-repair evidence, not a trend claim.
