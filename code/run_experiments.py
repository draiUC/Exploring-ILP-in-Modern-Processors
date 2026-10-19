"""Run from this directory inside Ubuntu WSL; only Python stdlib required."""
from pathlib import Path
import subprocess
import json
import hashlib
import sys

base = Path(__file__).resolve().parent
results = base.parent / 'results'
results.mkdir(exist_ok=True)
gem5 = Path.home() / 'src/gem5/build/ARM/gem5.opt'
for src in base.glob('*.S'):
    binary = src.with_suffix('')
    subprocess.run(['gcc-13', '-nostdlib', '-static', '-Wl,--build-id=none', str(src), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

cases = []
def case(name, binary, width=1, model='o3', predictor='tournament', second=None, policy='Partitioned'):
    cases.append((name, binary, width, model, predictor, second, policy))
if '--pilot' in sys.argv:
    case('pilot', 'integer')
    case('pilot_smt', 'integer', 4, second='floating')
else:
    for binary in ['integer', 'dependent', 'floating', 'memory', 'branch', 'pointer']:
        for width in [1, 2, 4]:
            case(f'{binary}_w{width}', binary, width)
    case('branch_local', 'branch', 1, predictor='local')
    case('branch_timing_no_prediction', 'branch', model='timing')
    case('integer_minor', 'integer', model='minor')
    for pair in [('integer','floating'), ('memory','integer'), ('integer','integer'), ('pointer','integer')]:
        for policy in ['Partitioned', 'Dynamic']:
            case(f'smt_{pair[0]}_{pair[1]}_{policy.lower()}', pair[0], 4, second=pair[1], policy=policy)

for name, binary, width, model, predictor, second, policy in cases:
    dest = results / name
    if '--resume' in sys.argv and (dest / 'exit.json').exists() and not name.endswith('_dynamic'):
        print('EXISTS', name, flush=True)
        continue
    args = [str(gem5), f'--outdir={dest}', '--debug-flags=O3PipeView', '--debug-file=trace.out',
            str(base / 'ilp_config.py'), '--binary', str(base / binary),
            '--width', str(width), '--model', model, '--predictor', predictor, '--smt-policy', policy]
    if second:
        args += ['--second', str(base / second)]
    print('RUN', name, flush=True)
    with (results / (name + '.log')).open('w') as log:
        completed = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=240)
    if completed.returncode:
        print((results / (name + '.log')).read_text()[-6000:])
        raise SystemExit(completed.returncode)
    print('PASS', name, flush=True)

manifest = {'revision': subprocess.check_output(['git','-C',str(Path.home()/'src/gem5'),'rev-parse','HEAD'],text=True).strip(),
            'source_sha256': {x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in base.glob('*') if x.suffix in ['.py','.S']},
            'cases': [x[0] for x in cases]}
(results / 'manifest.json').write_text(json.dumps(manifest,indent=2))
