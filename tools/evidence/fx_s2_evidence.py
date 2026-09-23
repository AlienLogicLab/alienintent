"""FX-S2 local proof with immutable observations and fault/restored controls.

Run against a committed source. Supply the actual caller invocation explicitly;
producer fixture metadata is never misrepresented as verifier provenance.
"""
from dataclasses import asdict, replace
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PLAN = Path('docs/evidence/wave2-proof-fixtures/FX-S2/fixture-plan.json')
STORE = Path('src/alienintent/execution_coordination/adapters/sqlite_store.py')
TESTS = ['tests/execution_coordination/test_fenced_store.py', 'tests/execution_coordination/test_operational_store.py', 'tests/composition/test_fenced_profile.py']
CONTROLS = (
    ('fence', 'if not row or row["owner"] != reservation.owner or row["fence"] != reservation.fence:', 'if False:', 'test_stale_fence_rejected[intent]'),
    ('vector', 'if actual != expected:', 'if False:', 'test_stale_vector_rejected[intent]'),
    ('expiry', 'if now >= expiry:', 'if False:', 'test_expired_authority_cannot_claim_or_deliver'),
    ('receipt', 'receipt != self._consumer_receipt(record)', 'False', 'test_forged_receipt_cannot_confirm'),
)


def digest(body):
    return 'sha256:' + sha256(body).hexdigest()


def retain(output, record):
    body = json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    name = sha256(body).hexdigest()
    target = output / 'observations' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(body)
    return {'revision_digest': 'sha256:' + name, 'locator': 'observations/' + name}


def execute(cwd, args):
    env = {**os.environ, 'PYTHONPATH': str(cwd / 'src') + os.pathsep + str(cwd), 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, timeout=180)
    return {'argv': args, 'cwd': str(cwd), 'exit_status': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}


def run(output, invocation):
    output.mkdir(parents=True, exist_ok=False)
    plan = json.loads((ROOT / PLAN).read_text())
    report = {'record_kind': 'ProofFixtureExecution', 'schema_version': 1, 'fixture_id': 'FX-S2',
              'invocation': invocation, 'producer_invocation': plan['invocation'],
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_status': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
              'fixture_plan_sha256': digest((ROOT / PLAN).read_bytes()), 'independent_verdict': 'PENDING',
              'live_proof': 'NOT_ESTABLISHED', 'measurements': {'tokens': None, 'cost': None, 'provider_calls': None,
              'uncertainty': 'not instrumented by this local fixture; no inference from absent telemetry'},
              'commands': [], 'mutations': [], 'holds': []}
    if report['source_status']:
        report['holds'].append('source is not a clean committed candidate')
    paths = [STORE, PLAN, Path(__file__).relative_to(ROOT),
             Path('src/alienintent/execution_coordination/ports/fenced_store.py'),
             Path('src/alienintent/execution_coordination/application/guarded_effect_execution.py'),
             Path('src/alienintent/composition/fenced_profile.py'), *(Path(p) for p in TESTS)]
    report['input_digests'] = {str(p): digest((ROOT / p).read_bytes()) for p in paths}
    intact = execute(ROOT, [sys.executable, '-B', '-m', 'pytest', '-q', *TESTS])
    report['commands'].append({'id': 'intact', 'expected_exit': 0, 'observed_exit': intact['exit_status'], 'observation_ref': retain(output, intact)})
    if intact['exit_status'] != 0:
        report['holds'].append('intact tests failed')
    with tempfile.TemporaryDirectory(prefix='fx-s2-controls-') as temp:
        copy = Path(temp)
        for name in ('src', 'tests'):
            shutil.copytree(ROOT / name, copy / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(ROOT / 'pyproject.toml', copy / 'pyproject.toml')
        path = copy / STORE
        original = path.read_text()
        for name, needle, replacement, test in CONTROLS:
            count = original.count(needle)
            if count != 1:
                raise RuntimeError(f'{name}: expected one mutation, found {count}')
            command = [sys.executable, '-B', '-m', 'pytest', '-q', 'tests/execution_coordination/test_fenced_store.py::' + test]
            path.write_text(original.replace(needle, replacement, 1))
            fault = execute(copy, command)
            path.write_text(original)
            restored = execute(copy, command)
            discriminates = fault['exit_status'] == 1 and 'DID NOT RAISE' in fault['stdout'] and restored['exit_status'] == 0
            report['mutations'].append({'control': name, 'application_count': count,
                'source_sha256': digest(original.encode()), 'mutation': {'remove': needle, 'replace_with': replacement},
                'expected_fault_exit': 1, 'observed_fault_exit': fault['exit_status'],
                'expected_restored_exit': 0, 'observed_restored_exit': restored['exit_status'],
                'fault_ref': retain(output, fault), 'restored_ref': retain(output, restored), 'discriminates': discriminates})
            if not discriminates:
                report['holds'].append(name + ' did not discriminate')
    # Inspect actual same-database durable state after the composed local effect.
    sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
    from alienintent.composition.fenced_profile import FencedProfile
    from tests.execution_coordination.test_fenced_store import setup_store, intent, PROFILE, AUTHORITY
    with tempfile.TemporaryDirectory(prefix='fx-s2-journal-') as temp:
        path = Path(temp) / 'store.sqlite'
        store, locks, vector = setup_store(path)
        intent(store, locks, vector)
        post = replace(vector, versions=(('job', 1), ('authority', 1), ('premise', 1)))
        profile = FencedProfile(path, name=PROFILE, clock=lambda: 100)
        confirmation = profile.executor.execute(PROFILE, 'effect-1', locks, post)
        receipt = profile.store.readback_guarded(PROFILE, 'effect-1')
        assert receipt == confirmation.receipt
        with sqlite3.connect(path) as connection:
            snapshot = {table: connection.execute('SELECT * FROM ' + table + ' ORDER BY 1, 2').fetchall()
                        for table in ('aggregates', 'effects', 'reservations', 'fences')}
        report['readback_ref'] = retain(output, {'confirmation': asdict(confirmation), 'receipt': asdict(receipt), 'database_rows': snapshot})
        profile_record = {'name': PROFILE, 'clock': 100, 'authority': AUTHORITY, 'initial_vector': asdict(vector),
                          'reservations': [asdict(r) for r in locks], 'consumer': 'same-database local durable delivery journal'}
        report['profile_ref'] = retain(output, profile_record)
        report['profile_digest'] = report['profile_ref']['revision_digest']
    report['exit_status'] = 1 if report['holds'] else 0
    (output / 'execution-record.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'fixture_id': 'FX-S2', 'exit_status': report['exit_status'], 'holds': report['holds'], 'report': str(output / 'execution-record.json')}))
    return report['exit_status']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--invocation', required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.output, args.invocation))
