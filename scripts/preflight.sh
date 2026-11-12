#!/bin/bash
# Preflight for a new agent before it enters the GPU queue or the Kaggle queue (added 2026-10-30 after the E15 smoke
# died on an ADK template error and 009c/009d ran past Kaggle's 12 h limit).
#   scripts/preflight.sh [--static-only] <agent dir> [submission.zip]
#   scripts/preflight.sh --check-stamp <submission.zip>     exit 0 only if this exact zip has a passing stamp
# 1. static: agent.yaml + sub_agents parse; every {identifier} in every prompt is a known state key or optional;
#    every prompts/ file referenced exists.   2. live: one easy OOD task (apprise_1747) end to end; fails on any
#    Traceback, on zero tool calls, or on a crash before the first model call.   3. zip (if given): contains exactly
#    the agent dir's files, byte-identical.
# Oracle firewall (added 2026-11-03, reports/rethink-2026-11-02/ceilings.md section 4), run first, stops before any live call:
# A1. no oracle|research/ in the agent path or zip name, no file referring to them or to oracle_arm, no symlink leaving
#     the agent dir, no symlink in the zip.   A2. no gold added line (>= 40 non-space chars, patch or test_patch of every
#     data task set) in any text file of the agent or zip, except hashes listed in scripts/preflight_gold_allowlist.txt.
#     Verbatim leaks only; adapters are binary and cannot be scanned (train/oracle_guard.py covers what they train on).
# A4. a full pass with a zip writes results/preflight-stamps/<zip sha256>.json. --static-only never stamps: no live check.
set -u
STATIC=0
cd "$(dirname "$0")/.."   # paths are repo-relative or absolute, as before
case "${1:-}" in
  --static-only) STATIC=1; shift ;;
  --check-stamp)
    S=$(sha256sum "$2" | cut -d' ' -f1)
    [ -f "results/preflight-stamps/$S.json" ] && { echo "stamp OK $S"; exit 0; }
    echo "NO PREFLIGHT STAMP for $2 ($S)"; exit 1 ;;
esac
A=$1; Z=${2:-}; PY=.venv-harness/bin/python; FAIL=0
[ -n "$Z" ] && ZS=$(sha256sum "$Z" | cut -d' ' -f1)
$PY - "$A" "$Z" <<'PYEOF' || { echo "PREFLIGHT FAIL (oracle firewall; nothing else was run)"; exit 1; }
import glob, json, os, re, stat, sys, zipfile, hashlib
a, z = sys.argv[1:]; bad = []
NAME = re.compile(r'oracle|research/', re.I)      # paths and names
BODY = re.compile(r'oracle|research/|oracle_arm', re.I)  # file contents
files = []  # (label, bytes)
root = os.path.realpath(a)
if NAME.search(a) or NAME.search(os.path.relpath(root)): bad.append(f'agent path matches oracle|research/: {a}')
for d, subs, fs in os.walk(a):
    for n in subs + fs:
        p = os.path.join(d, n)
        if NAME.search(os.path.relpath(p, a)): bad.append(f'{p}: name matches oracle|research/')
        if os.path.islink(p):
            t = os.path.realpath(p)
            if t != root and not t.startswith(root + os.sep): bad.append(f'{p}: symlink leaves the agent dir ({t})')
    for n in fs:
        p = os.path.join(d, n)
        if os.path.isfile(p): files.append((p, open(p, 'rb').read()))
if z:
    if NAME.search(z): bad.append(f'zip path matches oracle|research/: {z}')
    zf = zipfile.ZipFile(z)
    for i in zf.infolist():
        if i.is_dir(): continue
        if NAME.search(i.filename): bad.append(f'{z}:{i.filename}: name matches oracle|research/')
        if stat.S_ISLNK(i.external_attr >> 16): bad.append(f'{z}:{i.filename}: symlink in zip')
        files.append((f'{z}:{i.filename}', zf.read(i)))
texts, skipped = [], []
for label, b in files:
    if b'\0' in b[:8192] or len(b) > 20_000_000:
        skipped.append(label); continue
    texts.append((label, b.decode('utf-8', 'replace')))
for label, t in texts:
    m = BODY.search(t)
    if m: bad.append(f'{label}: refers to {m.group()!r}: ...{t[max(0, m.start() - 40):m.end() + 40]!r}...')
# A2: gold fingerprint. Whitespace-free substring match, so an escaped or re-indented line still counts.
sq = lambda s: re.sub(r'\s+', '', s)
gold = {}
sets = ['data/tasks.jsonl'] + sorted(glob.glob('data/*/tasks.jsonl'))
for s in sets:
    for l in open(s):
        r = json.loads(l)
        for field in ('patch', 'test_patch'):
            for g in (r.get(field) or '').splitlines():
                if g.startswith('+') and not g.startswith('+++'):
                    k = sq(g[1:])
                    if len(k) >= 40: gold.setdefault(k, r.get('instance_id'))
allow = set()
if os.path.exists('scripts/preflight_gold_allowlist.txt'):
    for l in open('scripts/preflight_gold_allowlist.txt'):
        if l.split('#')[0].strip(): allow.add(l.split()[0])
hits = 0
for label, t in texts:
    q = sq(t)
    for k, iid in gold.items():
        if k in q:
            h = hashlib.sha256(k.encode()).hexdigest()[:16]
            if h in allow: continue
            hits += 1
            if hits <= 10: bad.append(f'{label}: gold line of {iid} (allowlist key {h}): {k[:70]}')
if hits > 10: bad.append(f'... {hits} gold-line matches in all')
print(f'firewall:', 'OK' if not bad else 'FAIL', f'{len(texts)} text files against {len(gold)} gold lines from {len(sets)} task sets;',
      f'{len(skipped)} binary or huge files not scanned', skipped[:3] if skipped else '')
[print('  ', b) for b in bad]
sys.exit(1 if bad else 0)
PYEOF
$PY - "$A" <<'PYEOF' || FAIL=1
import glob, os, re, sys, yaml
from google.adk.utils.instructions_utils import _is_valid_state_name
a = sys.argv[1]; bad = []
outs = {'problem_description', 'hints'}
ymls = [f'{a}/agent.yaml'] + glob.glob(f'{a}/sub_agents/*.yaml')
class L(yaml.SafeLoader):
    pass
L.add_constructor('!include', lambda l, n: l.construct_scalar(n))
for y in ymls:
    d = yaml.load(open(y), Loader=L)  # syntax check; !include is the harness's file include
    for k in re.findall(r"output_key:\s*(\w+)", open(y).read()):
        outs.add(k)
    for ref in re.findall(r"!include\s+([\w./-]+)", open(y).read()):
        if not os.path.exists(os.path.join(os.path.dirname(y), ref)):
            bad.append(f'{y}: missing {ref}')
for f in glob.glob(f'{a}/prompts/*') + ymls:
    for m in re.finditer(r'{+[^{}]*}+', open(f).read()):
        v = m.group().lstrip('{').rstrip('}').strip()
        if v.endswith('?'):
            continue
        if _is_valid_state_name(v) and v not in outs:
            bad.append(f'{f}: {m.group()} is not a session state key (ADK will raise KeyError)')
print('static:', 'OK' if not bad else 'FAIL'); [print('  ', b) for b in bad]
sys.exit(1 if bad else 0)
PYEOF
if [ "$STATIC" = 0 ]; then
OUT=results/preflight-$(basename $A)-$(date +%s)
echo apprise_1747 > $OUT.tasks
scripts/run_ood.sh "$A" "$OUT" $OUT.tasks >/dev/null 2>&1
LOG=$OUT/apprise_1747.log
if grep -q Traceback $LOG 2>/dev/null || ! ls $OUT/apprise_1747/traces/*.json >/dev/null 2>&1; then
  echo "live: FAIL ($LOG)"; grep -m3 -E "Error|Traceback" $LOG; FAIL=1
else
  N=$($PY -c "import json,glob;t=json.load(open(glob.glob('$OUT/apprise_1747/traces/*.json')[0]));print(sum(len(s.get('tool_calls') or []) for s in t['steps']))")
  R=$(grep -o '"resolved": [0-9]*' $OUT/apprise_1747/summary.json | head -1)
  [ "$N" -gt 0 ] && echo "live: OK ($N tool calls, $R)" || { echo "live: FAIL (0 tool calls)"; FAIL=1; }
fi
else
echo "live: skipped (--static-only)"
fi
if [ -n "$Z" ]; then
  $PY - "$A" "$Z" <<'PYEOF' || FAIL=1
import hashlib, os, sys, zipfile
a, z = sys.argv[1:]; zf = zipfile.ZipFile(z); bad = []
names = {n for n in zf.namelist() if not n.endswith('/')}
for n in names:
    p = os.path.join(a, n)
    if not os.path.exists(p) or open(p, 'rb').read() != zf.read(n):
        bad.append(f'{n} differs from {p}')
if 'agent.yaml' not in names:
    bad.append('agent.yaml not at zip root')
print('zip:', 'OK' if not bad else 'FAIL', len(names), 'files'); [print('  ', b) for b in bad]
sys.exit(1 if bad else 0)
PYEOF
fi
# A4: only a full pass (live included) with a zip earns a stamp. Keyed by the zip's sha256; the queue side reads it via --check-stamp.
if [ $FAIL = 0 ] && [ -n "$Z" ] && [ "$STATIC" = 0 ]; then
  mkdir -p results/preflight-stamps
  printf '{"zip": "%s", "sha256": "%s", "agent": "%s", "commit": "%s", "at": "%s"}\n' "$Z" "$ZS" "$A" "$(git rev-parse --short HEAD)" "$(date -u +%FT%TZ)" > "results/preflight-stamps/$ZS.json"
  echo "stamp: results/preflight-stamps/$ZS.json"
fi
[ $FAIL = 0 ] && echo PREFLIGHT PASS || echo PREFLIGHT FAIL
exit $FAIL
