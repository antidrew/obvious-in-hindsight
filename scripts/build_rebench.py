"""Convert SWE-rebench-leaderboard tasks (CC-BY-4.0, nebius) into the swegemma task format.

    .venv-harness/bin/python -I scripts/build_rebench.py select            # -> data/rebench/selected.json
    .venv-harness/bin/python -I scripts/build_rebench.py build [-j 6]      # snapshots, wheel sets, tasks.jsonl

Why: OOD-45 is near the ceiling for the public single agent (88%) while the hidden set gives it ~17%. SWE-rebench
tasks are recent real issues from many repos with their original statements, closer to how the hidden set was
built ("same sandbox but different wheels", host). Each task becomes:
  data/rebench/snapshots/<id>.tgz    the repo at base_commit as one fresh commit on main (harness format)
  data/rebench/wheelsets/<id>/       wheels resolved inside our own sandbox image (Python 3.13) from the task's
                                     recorded install commands; the repo's own wheel and the image's pre-baked
                                     tools are removed (the harness installs /workspace in editable mode)
  data/rebench/tasks.jsonl           swegemma rows (problem_statement = the original issue text)
Gold / empty validation is separate: DATA=data/rebench scripts/run_ood.sh GOLD|EMPTY ...
Raw parquet files (data/rebench/raw) are downloaded data: read only, never executed.
"""
import argparse, glob, json, os, re, shlex, shutil, subprocess, sys, tarfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
# REBENCH_OUT=data/rebench_full builds the training pool from the full SWE-rebench (raw/*.parquet there),
# excluding every repo of the eval sets (public, OOD-45, RB) and keeping well-specified tasks only.
OUT = ROOT / os.environ.get('REBENCH_OUT', 'data/rebench')
TRAIN_POOL = OUT.name == 'rebench_full'
PUBLIC_REPOS = {'fastapi/fastapi', 'Textualize/rich', 'psf/requests', 'encode/httpx'}
PER_REPO = 8 if TRAIN_POOL else 2
IMAGE = 'swebench-sandbox:latest'
# installed in the sandbox image or by the harness itself; a second copy in site-packages would shadow them
SKIP_WHEELS = {'pytest', 'pluggy', 'pip', 'setuptools', 'wheel', 'iniconfig', 'packaging'}


def sh(cmd, cwd=None, timeout=1800):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        raise RuntimeError(f'{cmd[:4]} failed: {(r.stderr or r.stdout)[-800:]}')
    return r.stdout


def new_id(row):
    owner_repo = row['instance_id'].split('__', 1)[1]
    repo, num = owner_repo.rsplit('-', 1)
    return re.sub(r'[^a-z0-9]+', '_', repo.lower()) + '_' + num


def py_only(patch):
    files = [l.split(' b/', 1)[-1] for l in patch.splitlines() if l.startswith('diff --git')]
    return bool(files) and all(f.endswith('.py') for f in files)


def cmd_select(args):
    df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(OUT / 'raw/*.parquet')))])
    df = df.sort_values('created_at', ascending=False)
    excluded = set(PUBLIC_REPOS)
    if TRAIN_POOL:
        for f in ('data/ood45/tasks.jsonl', 'data/rebench/tasks.jsonl'):
            excluded |= {json.loads(l)['repo'] for l in open(ROOT / f)}
        excluded |= {s['repo'] for s in json.loads((ROOT / 'data/rebench/selected.json').read_text())}
        sc = df['meta'].map(lambda m: m['llm_score'])
        df = df[(df['created_at'] >= '2020-01-01') & sc.map(lambda s: s['issue_text_score'] <= 1 and
                                                             s['test_score'] <= 1 and s['difficulty_score'] <= 2)]
        df = df.drop_duplicates('instance_id')
    picked, per = [], {}
    for _, r in df.iterrows():
        cfg = r['install_config']
        if (r['repo'] in excluded or not py_only(r['patch']) or r['meta']['num_modified_files'] > 3
                or not str(cfg['test_cmd']).startswith('pytest') or cfg['log_parser'] != 'parse_log_pytest'
                or not len(r['FAIL_TO_PASS']) or per.get(r['repo'], 0) >= PER_REPO):
            continue
        per[r['repo']] = per.get(r['repo'], 0) + 1
        picked.append({'instance_id': new_id(r), 'src_id': r['instance_id'], 'repo': r['repo'],
                       'base_commit': r['base_commit'], 'patch': r['patch'], 'test_patch': r['test_patch'],
                       'problem_statement': r['problem_statement'], 'hints_text': '',
                       'created_at': r['created_at'], 'FAIL_TO_PASS': list(r['FAIL_TO_PASS']),
                       'PASS_TO_PASS': list(r['PASS_TO_PASS']),
                       'install': {'install': cfg['install'], 'pre_install': list(cfg['pre_install'] if cfg['pre_install'] is not None else []),
                                   'pip_packages': list(cfg['pip_packages'] if cfg['pip_packages'] is not None else []),
                                   'reqs_path': list(cfg['reqs_path'] if cfg['reqs_path'] is not None else []),
                                   'packages': cfg['packages']}})
    assert len({p['instance_id'] for p in picked}) == len(picked)
    (OUT / 'selected.json').write_text(json.dumps(picked, indent=1))
    print(f'selected {len(picked)} tasks from {len(per)} repos')


def pip_wheel_script(inst, cutoff):
    """Translate the recorded install commands into `pip wheel` calls (no install, no apt, no git)."""
    steps = []
    segs = [s for c in [inst['install'], *inst['pre_install']] for s in re.split(r'&&|;', c or '')]
    for s in segs:
        toks = shlex.split(s.strip()) if s.strip() else []
        if toks[:2] == ['python', '-m'] or toks[:2] == ['python3', '-m']:
            toks = toks[2:]
        if toks[:2] not in (['pip', 'install'], ['pip3', 'install']):
            continue
        keep, skip_next = [], False
        for t in toks[2:]:
            if skip_next:
                skip_next = False; continue
            if t in ('-e', '--editable', '-U', '--upgrade', '--no-deps', '--user', '-q', '--quiet',
                     '--force-reinstall', '--no-build-isolation', '--pre'):
                continue
            if t in ('--index-url', '-i', '--extra-index-url', '-c', '--constraint'):
                skip_next = True; continue
            keep.append(t)
        if keep:
            steps.append(keep)
    if inst['pip_packages']:
        steps.append(list(inst['pip_packages']))
    for r in inst['reqs_path']:
        steps.append(['-r', r])
    if inst['packages'] and inst['packages'] not in ('requirements.txt', 'environment.yml'):
        steps.append(shlex.split(inst['packages']))
    if not any('.' in st[0] and st[0].startswith('.') for st in steps):
        steps.insert(0, ['.'])
    # Resolve as of the task's date (the hidden set ships era wheels; today's releases break old code), and add
    # the build backend: the harness installs /workspace editable offline with --no-build-isolation.
    pw = f'pip wheel -q --uploaded-prior-to {cutoff} -w /out '
    build_reqs = ("python3 -c \"import tomllib;print('\\\\n'.join(tomllib.load(open('pyproject.toml','rb'))"
                  ".get('build-system',{}).get('requires',[])))\" > /tmp/breqs.txt 2>/dev/null || true")
    lines = ['set -u', 'cp -r /repo /tmp/r && cd /tmp/r', 'pip wheel -q --no-deps -w /self . >/dev/null 2>&1 || true',
             build_reqs, f'[ -s /tmp/breqs.txt ] && {{ {pw}-r /tmp/breqs.txt || echo STEP_FAILED; }}']
    for st in steps:
        lines.append(pw + ' '.join(shlex.quote(t) for t in st) + ' || echo STEP_FAILED')
    return '\n'.join(lines)


def norm(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def build_one(inst):
    iid = inst['instance_id']
    work = OUT / 'work' / iid
    snap = OUT / 'snapshots' / f'{iid}.tgz'
    wdir = OUT / 'wheelsets' / iid
    done = OUT / 'work' / f'{iid}.done'
    if done.exists():
        return iid, json.loads(done.read_text())
    shutil.rmtree(work, ignore_errors=True)
    repo = work / 'repo'
    repo.mkdir(parents=True)
    sh(['git', 'init', '-q'], cwd=repo)
    sh(['git', 'fetch', '-q', '--depth', '1', f'https://github.com/{inst["repo"]}.git', inst['base_commit']],
       cwd=repo, timeout=900)
    sh(['git', 'checkout', '-q', 'FETCH_HEAD'], cwd=repo)
    # snapshot: the tree as one commit on main, no history (the harness adds its own baseline commit)
    ws = work / 'ws'
    ws.mkdir()
    sh(['bash', '-c', f'git -C {repo} archive HEAD | tar -x -C {ws}'])
    sh(['git', 'init', '-q', '-b', 'main'], cwd=ws)
    sh(['git', '-c', 'user.name=snapshot', '-c', 'user.email=snapshot@local', 'add', '-A'], cwd=ws)
    sh(['git', '-c', 'user.name=snapshot', '-c', 'user.email=snapshot@local', 'commit', '-q', '-m', 'base'], cwd=ws)
    snap.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(snap.with_suffix('.part'), 'w:gz', compresslevel=6) as tar:
        def f(ti):
            ti.uid = ti.gid = 0; ti.uname = ti.gname = ''; return ti
        for p in sorted(ws.iterdir()):
            tar.add(p, arcname=f'./{p.name}', filter=f)
    snap.with_suffix('.part').replace(snap)
    # wheels, resolved inside the sandbox image with network on
    shutil.rmtree(wdir, ignore_errors=True)
    wdir.mkdir(parents=True)
    selfd = work / 'self'
    selfd.mkdir()
    cutoff = (pd.Timestamp(inst["created_at"]) + pd.Timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    script = pip_wheel_script(inst["install"], cutoff)
    r = subprocess.run(['docker', 'run', '--rm', '-u', f'{_uid()}:{_gid()}', '-e', 'HOME=/tmp',
                        '-v', f'{repo}:/repo:ro', '-v', f'{wdir}:/out', '-v', f'{selfd}:/self',
                        '-v', f'{OUT / "pipcache"}:/tmp/.cache/pip', IMAGE, 'bash', '-c', script],
                       capture_output=True, text=True, timeout=3600)
    failed = r.stdout.count('STEP_FAILED')
    own = {norm(w.name.split('-')[0]) for w in selfd.glob('*.whl')}
    removed = []
    for w in wdir.glob('*'):
        if w.suffix != '.whl' or norm(w.name.split('-')[0]) in own | SKIP_WHEELS:
            removed.append(w.name); w.unlink()
    size = sum(w.stat().st_size for w in wdir.glob('*.whl'))
    meta = {'wheels': len(list(wdir.glob('*.whl'))), 'mb': round(size / 1e6), 'failed_steps': failed,
            'own': sorted(own), 'log': (r.stderr or '')[-600:]}
    shutil.rmtree(work)
    work.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps(meta))
    return iid, meta


FREEZE_SCRIPT = r"""set -u
cp -r /repo /tmp/r && cd /tmp/r
pip wheel -q --no-deps -w /self . >/dev/null 2>&1 || true
python3 -c "import tomllib;print('\\n'.join(tomllib.load(open('pyproject.toml','rb')).get('build-system',{}).get('requires',[])))" > /tmp/breqs.txt 2>/dev/null || true
[ -s /tmp/breqs.txt ] && { pip wheel -q --uploaded-prior-to CUTOFF -w /out -r /tmp/breqs.txt || echo STEP_FAILED; }
while read -r req; do
  [ -z "$req" ] && continue
  name=${req%%[=@ ]*}
  pip wheel -q --no-deps -w /out "$req" >/dev/null 2>&1 || pip wheel -q --no-deps --only-binary :all: --uploaded-prior-to CUTOFF -w /out "$name" >/dev/null 2>&1 || pip wheel -q --no-deps --only-binary :all: -w /out "$name" >/dev/null 2>&1 || echo "STEP_FAILED $req"
done < /freeze.txt
"""


def freeze_reqs(image):
    """Exact pins of the task's own SWE-rebench environment (conda env `testbed`)."""
    subprocess.run(['docker', 'pull', '-q', image], capture_output=True, text=True, timeout=1800, check=True)
    try:
        out = sh(['docker', 'run', '--rm', '--entrypoint', '', image, 'sh', '-c',
                  '/opt/conda/envs/testbed/bin/pip freeze 2>/dev/null || pip freeze'])
    finally:
        subprocess.run(['docker', 'rmi', '-f', image], capture_output=True)
    reqs = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', '-e')):
            continue
        if ' @ file://' in line:  # conda-built local copy: keep the name, resolve by date
            line = line.split(' @ ', 1)[0]
        reqs.append(line)
    return reqs


def freeze_one(inst, image):
    iid = inst['instance_id']
    wdir, work = OUT / 'wheelsets' / iid, OUT / 'work' / f'freeze_{iid}'
    shutil.rmtree(work, ignore_errors=True)
    repo, selfd = work / 'repo', work / 'self'
    repo.mkdir(parents=True); selfd.mkdir()
    sh(['git', 'init', '-q'], cwd=repo)
    sh(['git', 'fetch', '-q', '--depth', '1', f'https://github.com/{inst["repo"]}.git', inst['base_commit']],
       cwd=repo, timeout=900)
    sh(['git', 'checkout', '-q', 'FETCH_HEAD'], cwd=repo)
    reqs = freeze_reqs(image)
    (work / 'freeze.txt').write_text('\n'.join(reqs) + '\n')
    (OUT / 'freeze').mkdir(exist_ok=True)
    (OUT / 'freeze' / f'{iid}.txt').write_text('\n'.join(reqs) + '\n')
    cutoff = (pd.Timestamp(inst['created_at']) + pd.Timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%SZ')
    shutil.rmtree(wdir, ignore_errors=True)
    wdir.mkdir(parents=True)
    r = subprocess.run(['docker', 'run', '--rm', '-u', f'{_uid()}:{_gid()}', '-e', 'HOME=/tmp',
                        '-v', f'{repo}:/repo:ro', '-v', f'{wdir}:/out', '-v', f'{selfd}:/self',
                        '-v', f'{work / "freeze.txt"}:/freeze.txt:ro',
                        '-v', f'{OUT / "pipcache"}:/tmp/.cache/pip', IMAGE, 'bash', '-c',
                        FREEZE_SCRIPT.replace('CUTOFF', cutoff)], capture_output=True, text=True, timeout=5400)
    own = {norm(w.name.split('-')[0]) for w in selfd.glob('*.whl')} | {norm(inst['repo'].split('/')[1])}
    for w in wdir.glob('*'):
        if w.suffix != '.whl' or norm(w.name.split('-')[0]) in own | SKIP_WHEELS:
            w.unlink()
    shutil.rmtree(work)
    fails = [l for l in r.stdout.splitlines() if l.startswith('STEP_FAILED')]
    return iid, {'wheels': len(list(wdir.glob('*.whl'))), 'reqs': len(reqs), 'failed': fails[:8]}


def cmd_freeze(args):
    sel = {s['instance_id']: s for s in json.loads((OUT / 'selected.json').read_text())}
    images = json.loads((OUT / 'images.json').read_text())
    ids = open(args.ids).read().split()

    def safe(iid):
        try:
            return freeze_one(sel[iid], images[iid])
        except Exception as e:  # noqa: BLE001
            return iid, {'error': str(e)[-400:]}

    with ThreadPoolExecutor(args.j) as ex:
        for iid, meta in ex.map(safe, ids):
            print(iid, meta, flush=True)


def _uid():
    import os; return os.getuid()


def _gid():
    import os; return os.getgid()


def cmd_build(args):
    sel = json.loads((OUT / 'selected.json').read_text())
    if args.limit:
        sel = sel[:args.limit]
    (OUT / 'pipcache').mkdir(parents=True, exist_ok=True)
    metas = {}

    def safe(inst):
        try:
            return build_one(inst)
        except Exception as e:  # noqa: BLE001 - record and move on; validation filters later
            return inst['instance_id'], {'error': str(e)[-600:]}

    with ThreadPoolExecutor(args.j) as ex:
        for iid, meta in ex.map(safe, sel):
            metas[iid] = meta
            print(iid, {k: v for k, v in meta.items() if k != 'log'}, flush=True)
    ok = [s for s in sel if 'error' not in metas[s['instance_id']] and metas[s['instance_id']]['wheels']]
    with open(OUT / 'tasks.jsonl', 'w') as fh:
        for s in ok:
            fh.write(json.dumps({k: v for k, v in s.items() if k != 'install'}) + '\n')
    (OUT / 'build_meta.json').write_text(json.dumps(metas, indent=1))
    json.dump({s['instance_id']: s['repo'] for s in ok}, open(OUT / 'repo_of.json', 'w'), indent=1)
    print(f'built {len(ok)} of {len(sel)}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('select')
    b = sub.add_parser('build')
    b.add_argument('-j', type=int, default=6)
    b.add_argument('--limit', type=int, default=0)
    fz = sub.add_parser('freeze', help="rebuild wheel sets from the task's own SWE-rebench image pins")
    fz.add_argument('ids'); fz.add_argument('-j', type=int, default=3)
    a = p.parse_args()
    {'select': cmd_select, 'build': cmd_build, 'freeze': cmd_freeze}[a.cmd](a)
