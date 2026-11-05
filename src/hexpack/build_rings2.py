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
D = json.load(open(cfg.tmp('rings1.json'))); s = D['s']; side = s / math.sqrt(3)
feat = cfg.features()
def hexagon(x, y):
    return Polygon([(x + side * math.cos(math.radians(-90 + 60 * k)), y + side * math.sin(math.radians(-90 + 60 * k))) for k in range(6)])
def ring_K(cells, K):
    u = unary_union([hexagon(x, y).buffer(1e-6, join_style=2) for x, y in cells]).buffer(-1e-6, join_style=2)
    if u.geom_type == 'MultiPolygon': u = max(u.geoms, key=lambda g: g.area)
    u = orient(Polygon(u.simplify(1e-5).exterior.coords), 1.0)
    v = list(u.exterior.coords)[:-1]
    segs = []; E = 0
    for a, b in zip(v, v[1:] + v[:1]):
        m = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / side)); segs.append((a, b, m)); E += m
    if E > K: return None, E
    pts = []; e = 0
    for a, b, m in segs:
        for uu in range(m):
            cnt = ((e + 1) * K) // E - (e * K) // E; e += 1
            for j in range(cnt):
                f = (uu + j / cnt) / m
                pts.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return np.array(pts), E
def blob(n, cx, cy):
    best = None
    for pa in range(5):
        for pb in range(5):
            ph = (pa / 5 * s, pb / 5 * s * 0.866)
            pts = []
            for r in range(-14, 15):
                for c in range(-14, 15):
                    pts.append((s * (c + 0.5 * (r & 1)) + ph[0], s * 0.866 * r + ph[1]))
            pts = np.array(pts); d = (pts ** 2).sum(1) + np.random.default_rng(pa * 5 + pb).uniform(0, 1e-6, len(pts))
            sel = pts[np.argsort(d)[:n]]
            sel = sel - sel.mean(0) + np.array([cx, cy])
            u = unary_union([hexagon(x, y).buffer(1e-6, join_style=2) for x, y in sel]).buffer(-1e-6, join_style=2)
            if u.geom_type == 'MultiPolygon': continue
            per = u.length
            if best is None or per < best[0] - 1e-9: best = (per, sel)
    return best[1]
bad = []
for c in D['counties']:
    g = feat[c['fips']]['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    best_p = max(polys, key=lambda p: Polygon([proj(x, y) for x, y in p[0]]).area)
    real = Polygon([proj(x, y) for x, y in best_p[0]])
    if not real.is_valid: real = real.buffer(0)
    if real.geom_type == 'MultiPolygon': real = max(real.geoms, key=lambda q: q.area)
    cx, cy = real.centroid.x, real.centroid.y
    cells2 = blob(c['n'], cx, cy)
    K = c['K']
    H2, E2 = ring_K([tuple(p) for p in cells2], K)
    if H2 is None: bad.append((c['name'], E2, K)); K = E2; continue
    R = np.array(c['real']).reshape(-1, 2) / 1000.0
    costs = [((np.roll(H2, -sh, 0) - R) ** 2).sum() for sh in range(K)]
    H2 = np.roll(H2, -int(np.argmin(costs)), 0)
    c['hex2'] = [int(round(v * 1000)) for v in H2.reshape(-1)]
    c['cells2'] = [[round(float(x), 4), round(float(y), 4)] for x, y in cells2]
    c['cx'] = round(cx, 4); c['cy'] = round(cy, 4)
print('bad', bad)
json.dump(D, open(cfg.out('rings.json'), 'w'), separators=(',', ':'))
print(os.path.getsize(cfg.out('rings.json')))
