# PY-01 architecture-fitness evidence

Executed from the repository root at baseline `8bb35ed` before the PY-01
commit. The checks below exercise the checker against actual files; they are not
mocked or source-text assertions.

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

## Skeleton

```text
$ python3 tools/fitness/check_architecture.py --root src/alienintent --check all
PASS: all architecture fitness checks
EXIT=0
```

## Regression and coexistence checks

```text
$ python3 -m pytest tests/test_architecture_fitness.py -q
3 passed in 0.44s
EXIT=0

$ node scripts/check.mjs all
runtime: 309 passed, 0 failed
preflight: PASS
rai: 18 passed, 0 failed
policy: 2 passed, 0 failed
NODE_SUITE_EXIT=0
```

The independent review also added two boundary cases: a vendor type imported
under `TYPE_CHECKING` fails, while a `uuid.UUID` domain signature passes. This
prevents both an evasion of the vendor-type check and a false positive on a
standard-library value type.

`git diff --name-only 2288cef..HEAD -- src/config src/domain src/github
src/providers src/runtime test scripts package.json` produced no paths before
the PY-01 commit. Node source, tests, configuration, runtime and package metadata
therefore remain unchanged from its behavioral baseline.
