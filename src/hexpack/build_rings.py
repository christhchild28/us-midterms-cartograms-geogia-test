import json, math, sys
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import cfg as cfg_
cfg = cfg_.load()
proj = cfg.proj
PACK = cfg.out('layout.json')
OUT = cfg.tmp('rings1.json')
KMIN = 180

P = json.load(open(PACK))
s = P['s']; side = s / math.sqrt(3)
feat = cfg.features()

def hexagon(x, y):
    return Polygon([(x + side * math.cos(math.radians(-90 + 60 * k)), y + side * math.sin(math.radians(-90 + 60 * k))) for k in range(6)])

def resample(ring, K):
    pts = np.array(ring[:-1] if ring[0] == ring[-1] else ring)
    seg = np.sqrt(((np.roll(pts, -1, 0) - pts) ** 2).sum(1))
    cum = np.concatenate([[0], np.cumsum(seg)])
    L = cum[-1]
    t = np.linspace(0, L, K, endpoint=False)
    full = np.vstack([pts, pts[:1]])
    out = np.empty((K, 2))
    idx = np.searchsorted(cum, t, side='right') - 1
    idx = np.clip(idx, 0, len(pts) - 1)
    f = (t - cum[idx]) / np.where(seg[idx] > 0, seg[idx], 1)
    out[:, 0] = full[idx, 0] + f * (full[idx + 1, 0] - full[idx, 0])
    out[:, 1] = full[idx, 1] + f * (full[idx + 1, 1] - full[idx, 1])
    return out

def snap(cells):
    out=[]
    for x,y in cells:
        r=round(y/(0.8660254*P['s'])); c=round(x/P['s']-0.5*(r&1)); out.append((P['s']*(c+0.5*(r&1)), P['s']*0.8660254*r))
    return out
def hex_ring(cells):
    cells=snap(cells)
    u = unary_union([hexagon(x, y).buffer(1e-6, join_style=2) for x, y in cells]).buffer(-1e-6, join_style=2)
    if u.geom_type == 'MultiPolygon': u = max(u.geoms, key=lambda g: g.area)
    u = u.simplify(1e-5)
    holes = len(u.interiors)
    u = orient(Polygon(u.exterior.coords), 1.0)
    v = list(u.exterior.coords)[:-1]
    # unit edges along the ring
    pieces = []
    E = 0
    for a, b in zip(v, v[1:] + v[:1]):
        m = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / side)); pieces.append((a, b, m)); E += m
    f = max(1, math.ceil(KMIN / E))
    ring = []
    for a, b, m in pieces:
        n = m * f
        for k in range(n):
            ring.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return np.array(ring), holes

out = []; bad = []
allx = []; ally = []
for c in P['counties']:
    g = feat[c['fips']]['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    best = max(polys, key=lambda p: Polygon([proj(x, y) for x, y in p[0]]).area)
    real = Polygon([proj(x, y) for x, y in best[0]])
    if not real.is_valid: real = real.buffer(0)
    if real.geom_type == 'MultiPolygon': real = max(real.geoms, key=lambda q: q.area)
    real = orient(real, 1.0)
    H, holes = hex_ring(c['cells'])
    if holes: bad.append((c['name'], 'holes', holes))
    K = len(H)
    Rr = resample(list(real.exterior.coords), K)
    # best cyclic shift
    costs = [((np.roll(Rr, -sh, 0) - H) ** 2).sum() for sh in range(K)]
    sh = int(np.argmin(costs))
    Rr = np.roll(Rr, -sh, 0)
    allx += list(Rr[:, 0]) + list(H[:, 0]); ally += list(Rr[:, 1]) + list(H[:, 1])
    out.append(dict(name=c['name'], fips=c['fips'], pop=c['pop'], d=c['d'], r=c['r'], n=c['n'],
                    cells=[[round(x,5),round(y,5)] for x,y in snap(c['cells'])], landArea=c['landArea'],
                    real=[int(round(v * 1000)) for v in Rr.reshape(-1)],
                    hex=[int(round(v * 1000)) for v in H.reshape(-1)],
                    K=K))
print('rings built', len(out), 'holes/bad', bad)
print('K range', min(o['K'] for o in out), max(o['K'] for o in out), 'total points', sum(o['K'] for o in out))
bounds = [min(allx) - 0.06, min(ally) - 0.06, max(allx) + 0.06, max(ally) + 0.06]
json.dump(dict(s=s, unit=P['unit'], N=P['N'], stats=P['stats'], bounds=bounds, counties=out), open(OUT, 'w'), separators=(',', ':'))
import os; print('bytes', os.path.getsize(OUT), 'bounds', [round(b, 3) for b in bounds])
