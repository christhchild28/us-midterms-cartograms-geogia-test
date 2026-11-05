"""Sanity checks on a finished build. Exits non-zero if anything is structurally wrong."""
import json, math, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg as cfg_
cfg = cfg_.load()
bad = []
def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok: bad.append(msg)

lay = json.load(open(cfg.out('layout.json'))); rings = json.load(open(cfg.out('rings.json')))
lens = json.load(open(cfg.out('lens-fields.json')))
cs = rings['counties']; s = rings['s']
check(len(cs) == len(lay['counties']), '%d counties in layout and rings' % len(cs))
check(all(c['n'] == max(1, round(c['pop'] / cfg.unit)) for c in cs), 'hexagon count per county = pop / %d (min 1)' % cfg.unit)
check(rings['N'] == sum(c['n'] for c in cs), 'total hexagons N = %d' % rings['N'])

def nbrs(c, r):
    d = [(1,0),(-1,0),(-1,-1),(0,-1),(-1,1),(0,1)] if r % 2 == 0 else [(1,0),(-1,0),(0,-1),(1,-1),(0,1),(1,1)]
    return [(c+a, r+b) for a, b in d]
def rc(x, y):
    r = round(y / (0.8660254 * s)); return (round(x / s - 0.5 * (r & 1)), r)
disc, seen_cells, dup = [], set(), 0
for c in cs:
    cells = {rc(x, y) for x, y in c['cells']}
    if len(cells) != c['n']: check(False, '%s has %d distinct cells, expected %d' % (c['name'], len(cells), c['n']))
    dup += len(cells & seen_cells); seen_cells |= cells
    k0 = next(iter(cells)); st = [k0]; seen = {k0}
    while st:
        q = st.pop()
        for nb in nbrs(*q):
            if nb in cells and nb not in seen: seen.add(nb); st.append(nb)
    if len(seen) != len(cells): disc.append(c['name'])
check(not disc, 'every county is one connected piece' + (' (broken: %s)' % disc if disc else ''))
check(dup == 0, 'no hexagon shared by two counties')

def area(flat):
    p = [(flat[i] / 1000, flat[i + 1] / 1000) for i in range(0, len(flat), 2)]
    return abs(sum(p[i][0] * p[(i+1) % len(p)][1] - p[(i+1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2
cell = 0.8660254 * s * s
worst1 = max(abs(area(c['hex']) / (c['n'] * cell) - 1) for c in cs)
worst2 = max(abs(area(c['hex2']) / (c['n'] * cell) - 1) for c in cs if 'hex2' in c)
check(worst1 < 0.02, 'layout outline areas within %.2f%% of n x hexagon (limit 2%%)' % (100 * worst1))
check(worst2 < 0.05, 'in-place outline areas within %.2f%% of n x hexagon (limit 5%%)' % (100 * worst2))
check(all(len(c['hex']) == len(c['real']) == len(c['hex2']) for c in cs), 'real / hex / in-place rings have equal point counts')
check(lens['minDet'] > 0, 'lens warps never fold (min Jacobian %.3f > 0)' % lens['minDet'])
st = lay['stats']; print('  info  border pairs kept: %d of %d (%.1f%%), %d spurious touches' % (st['kept'], st['real'], 100 * st['kept'] / st['real'], st['spurious']))

pg = open(cfg.out('outline.html')).read()
check(not re.findall(r'\{\{[A-Z_]+\}\}|/\*(DATA|LENS|META)\*/', pg), 'page has no unfilled placeholders')
check(len(pg) < 16e6, 'page size %.2f MB (limit 16 MB)' % (len(pg) / 1e6))
js = re.search(r'<script>([\s\S]*)</script>', pg).group(1)
open(cfg.tmp('page.js'), 'w').write(js)
r = subprocess.run(['node', '-e', "new Function(require('fs').readFileSync(process.argv[1],'utf8'))", cfg.tmp('page.js')], capture_output=True, text=True)
check(r.returncode == 0, 'page script parses' + (': ' + r.stderr.strip()[:200] if r.returncode else ''))
sys.exit(1 if bad else 0)
