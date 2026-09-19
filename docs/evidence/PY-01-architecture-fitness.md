# PY-01 architecture-fitness evidence

Executed from the repository root on the PY-01 candidate. The checks below
exercise the checker against actual files; they are not mocked or source-text
assertions.

## Deliberately violating fixtures

Command pattern:

```text
python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/<check> --check <check>
```

```text
## layering fixture
domain/boundary.py:1: domain imports adapters
EXIT=1

## vendor-signature fixture
domain/vendor_type.py:7: third-party type in domain signature
domain/vendor_type.py:7: third-party type in domain signature
EXIT=1

## port-contract fixture
adapters/uncontracted.py:1: adapter class has no declared port contract
EXIT=1

## configuration fixture
application/settings.py:5: configuration read outside composition
EXIT=1
```

## Rejection-regression fixtures

The independent verifier found ordinary syntax forms that the first candidate
did not reject. Each command below returned the shown nonzero exit status.

```text
## relative adapter import
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/layering/relative-import --check layering
domain/boundary.py:1: domain imports adapters
EXIT=1

## absolute adapter import
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/layering/absolute-import --check layering
application/boundary.py:1: application imports adapters
EXIT=1

## quoted vendor annotation
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/vendor-signature/quoted-annotation --check vendor-signature
domain/value.py:7: third-party type in domain signature
domain/value.py:7: third-party type in domain signature
EXIT=1

## vendor base in domain
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/vendor-signature/vendor-base-domain --check vendor-signature
domain/value.py:4: third-party type in domain signature
EXIT=1

## vendor base in port
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/vendor-signature/vendor-base-port --check vendor-signature
ports/command.py:4: third-party type in ports signature
EXIT=1

## root beneath an ancestor named domain
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/path-classification/domain/alienintent --check port-contract
adapters/uncontracted.py:1: adapter class has no declared port contract
EXIT=1
```

## Nested quoted vendor annotation

The second independent verifier found that a quoted reference nested in a
subscript annotation was not inspected. The checker now parses every quoted
fragment while walking an annotation.

```text
$ python3 tools/fitness/check_architecture.py --root tests/fixtures/fitness/vendor-signature/nested-quoted-annotation --check vendor-signature
domain/value.py:7: third-party type in domain signature
EXIT=1
```

## Skeleton

```text
$ python3 tools/fitness/check_architecture.py --root src/alienintent --check all
PASS: all architecture fitness checks
EXIT=0
```

## Regression and coexistence checks

```text
$ python3 -m pytest tests/test_architecture_fitness.py -q
6 passed
EXIT=0

$ node scripts/check.mjs all
runtime: 309 passed, 0 failed
preflight: PASS
rai: 18 passed, 0 failed
policy: 2 passed, 0 failed
NODE_SUITE_EXIT=0
```

The regression fixtures cover relative and absolute adapter imports, quoted
vendor annotations, vendor base classes in domain and ports, and a checked root
whose ancestor is named after an architecture layer. A `uuid.UUID` domain
signature continues to pass, preventing a false positive on a standard-library
value type.

## CI enforcement

`.github/workflows/python-architecture-fitness.yml` runs on every push and
pull request in a separate Python-specific job. It invokes the checker against
the skeleton and runs the regression suite; each command retains its native
nonzero failure status, so an architecture violation fails CI. The existing
Node workflow remains unchanged.

`git diff --name-only 2288cef..HEAD -- src/config src/domain src/github
src/providers src/runtime test scripts package.json` produced no paths before
the PY-01 commit. Node source, tests, configuration, runtime and package metadata
therefore remain unchanged from its behavioral baseline.
