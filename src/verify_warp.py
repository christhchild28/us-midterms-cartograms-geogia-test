"""Checks for the warp-following hexmap: hex counts, uniqueness, connectivity, page presence."""
import json, math, os, sys
from common import cfg as cfg_
cfg = cfg_.load()
L = json.load(open(cfg.out('warp-layout.json'))); R = json.load(open(cfg.out('warp-rings.json')))
s = L['s']; bad = []
tot = 0; seen = set()
for c in L['counties']:
    n = round(c['pop'] / L['unit']) if False else c['n']
    if len(c['cells']) != n: bad.append((c['name'], 'cell count', len(c['cells']), n))
    for x, y in c['cells']:
        k = (round(x, 3), round(y, 3))
        if k in seen: bad.append((c['name'], 'duplicate hex', k))
        seen.add(k)
    tot += len(c['cells'])
    # connectivity: hex centres within 1.05*s apart
    pts = c['cells']; comp = {0}; st = [0]
    while st:
        i = st.pop()
        for j, q in enumerate(pts):
            if j not in comp and math.hypot(pts[i][0] - q[0], pts[i][1] - q[1]) < 1.05 * s: comp.add(j); st.append(j)
    if pts and len(comp) != len(pts): bad.append((c['name'], 'disconnected', len(comp), len(pts)))
if tot != L['N']: bad.append(('total', tot, L['N']))
if len(R['counties']) != len(L['counties']): bad.append(('rings', len(R['counties']), len(L['counties'])))
page = cfg.out('warp.html')
if not os.path.exists(page): bad.append(('missing', 'warp.html'))
print('hexes %d, counties %d, border retention %d/%d (%.1f%%)' % (tot, len(L['counties']), L['stats']['kept'], L['stats']['real'], 100 * L['stats']['kept'] / L['stats']['real']))
print('PASS' if not bad else 'FAIL %s' % bad[:10]); sys.exit(1 if bad else 0)
