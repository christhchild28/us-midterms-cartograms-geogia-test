"""Rings for the warp page: per county a real ring R, the same points flowed into the lens warp W, the hexagon ring H
(all with K points, aligned), plus the in-place blob ring H2 for tap-to-grow."""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lens'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
import warpflow as WF
from ringlib import Rings, resample
L = WF.L; cfg = L.cfg
P = json.load(open(cfg.out('warp-layout.json'))); s = P['s']; shift = np.array(P['shift']); RG = Rings(s)
f = np.array(P['f']); rho = WF.density(f)
cs = P['counties']; out = []; bad = []
reals = []; Hs = []
for i, c in enumerate(cs):
    H, holes = RG.hex_ring(c['cells'])
    if holes: bad.append((c['name'], 'holes', holes))
    real = orient(WF.main_part(i).buffer(0) if not WF.main_part(i).is_valid else WF.main_part(i), 1.0)
    R = resample(list(real.exterior.coords), len(H)); reals.append(R); Hs.append(H)
Wp = WF.advect(rho, np.vstack(reals), sig=0.3); cuts = np.cumsum([len(r) for r in reals])[:-1]
Ws = [w - shift for w in np.split(Wp, cuts)]
allx = {'R': [], 'W': [], 'H': []}; ally = {'R': [], 'W': [], 'H': []}
for i, c in enumerate(cs):
    R, Wr, H = reals[i], Ws[i], Hs[i]; K = len(H)
    sh = int(np.argmin([((np.roll(Wr, -k, 0) - H) ** 2).sum() for k in range(K)]))
    R, Wr = np.roll(R, -sh, 0), np.roll(Wr, -sh, 0)
    cx, cy = (float(v) for v in Polygon(R).centroid.coords[0])
    cells2 = RG.blob(c['n'], cx, cy); H2, E2 = RG.ring_K([tuple(p) for p in cells2], K)
    if H2 is None: bad.append((c['name'], E2, K)); continue
    H2 = np.roll(H2, -int(np.argmin([((np.roll(H2, -k, 0) - R) ** 2).sum() for k in range(K)])), 0)
    for key, A in (('R', R), ('W', Wr), ('H', H)): allx[key] += list(A[:, 0]); ally[key] += list(A[:, 1])
    iv = lambda A: [int(round(v * 1000)) for v in A.reshape(-1)]
    out.append(dict(name=c['name'], fips=c['fips'], pop=c['pop'], d=c['d'], r=c['r'], n=c['n'], K=K, landArea=c['landArea'],
                    cells=[[round(x, 5), round(y, 5)] for x, y in RG.snap(c['cells'])], cells2=[[round(float(x), 4), round(float(y), 4)] for x, y in cells2],
                    real=iv(R), warp=iv(Wr), hex=iv(H), hex2=iv(H2), cx=round(cx, 4), cy=round(cy, 4)))
print('rings', len(out), 'bad', bad)
pad = 0.06
def bnd(k): return [min(allx[k]) - pad, min(ally[k]) - pad, max(allx[k]) + pad, max(ally[k]) + pad]
bR = bnd('R'); asp = (bR[2] - bR[0]) / (bR[3] - bR[1])
def fit(b):   # same aspect as the real view so the map box never changes height
    w, h = b[2] - b[0], b[3] - b[1]; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    if w / h < asp: w = h * asp
    else: h = w / asp
    return [cx - w / 2, cy - h / 2, w, h]
# warped-view box must also hold the dashed real outline (shifted into the warp frame)
vbR = [bR[0], bR[1], bR[2] - bR[0], bR[3] - bR[1]]; vbW = fit(bnd('W')); vbH = fit(bnd('H'))
json.dump(dict(s=s, unit=P['unit'], N=P['N'], stats=P['stats'], shift=P['shift'], bounds=bR, vbW=vbW, vbH=vbH, counties=out), open(cfg.out('warp-rings.json'), 'w'), separators=(',', ':'))
print('wrote warp-rings.json', os.path.getsize(cfg.out('warp-rings.json')))
