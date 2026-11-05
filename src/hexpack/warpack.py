"""Hexagon layout that follows the lens warp: flow every county to its population-proportional shape,
then fill each warped shape with exactly n hexagons (one exact assignment, no annealing)."""
import json, math, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lens'))
import numpy as np, shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.ndimage import distance_transform_edt, binary_closing
from scipy.optimize import linear_sum_assignment
from PIL import Image, ImageDraw
import warpflow as W
L = W.L; cfg = L.cfg; NC = W.NC; n = L.nhex.astype(int); N = int(n.sum())
T0 = time.time()
rings = W.dense_rings()
print('dense vertices', sum(len(r) for r in rings))
f, parts, abar = W.fit_areas(rings)
print('flow done %.0fs' % (time.time() - T0))
polys = []
for p in parts:
    g = Polygon(p)
    if not g.is_valid: g = g.buffer(0)
    polys.append(g)
s = math.sqrt(abar / 0.8660254); SQ3 = math.sqrt(3)
allx = np.concatenate([p[:, 0] for p in parts]); ally = np.concatenate([p[:, 1] for p in parts])
bx0, by0, bx1, by1 = allx.min() - 3 * s, ally.min() - 3 * s, allx.max() + 3 * s, ally.max() + 3 * s
res = s / 10; WID = int((bx1 - bx0) / res) + 1; HEI = int((by1 - by0) / res) + 1
img = Image.new('I', (WID, HEI), 0); dr = ImageDraw.Draw(img)
for k, p in enumerate(parts):
    dr.polygon([((x - bx0) / res, (y - by0) / res) for x, y in p], fill=k + 1)
LAB = np.array(img)
inside = binary_closing(LAB > 0, iterations=2)
depth = distance_transform_edt(inside) * res / s            # hex units, 0 outside
outd = distance_transform_edt(~inside) * res / s

def lattice(a, b):
    """hex centres (world coords) for lattice offset (a, b); returns ints c, r and x, y."""
    r0 = int((by0 - b) / (0.8660254 * s)) - 1; r1 = int((by1 - b) / (0.8660254 * s)) + 2
    c0 = int((bx0 - a) / s) - 2; c1 = int((bx1 - a) / s) + 2
    R, Cc = np.meshgrid(np.arange(r0, r1 + 1), np.arange(c0, c1 + 1), indexing='ij'); R = R.ravel(); Cc = Cc.ravel()
    X = a + s * (Cc + 0.5 * (R & 1)); Y = b + 0.8660254 * s * R
    ok = (X > bx0) & (X < bx1) & (Y > by0) & (Y < by1)
    return Cc[ok], R[ok], X[ok], Y[ok]
def px(X, Y): return np.clip(((Y - by0) / res).astype(int), 0, HEI - 1), np.clip(((X - bx0) / res).astype(int), 0, WID - 1)

best = None
for a in np.linspace(0, s, 6, endpoint=False):
    for b in np.linspace(0, 1.7320508 * s, 6, endpoint=False):
        Cc, R, X, Y = lattice(a, b); iy, ix = px(X, Y); lab = LAB[iy, ix]
        cnt = np.bincount(lab[lab > 0] - 1, minlength=NC); sc = np.abs(cnt - n).sum() + abs((lab > 0).sum() - N)
        if best is None or sc < best[0]: best = (sc, a, b)
print('lattice offset score (hexes in wrong county) %d' % best[0])
_, oa, ob = best
Cc, R, X, Y = lattice(oa, ob); iy, ix = px(X, Y)
keep = (outd[iy, ix] <= 1.5); Cc, R, X, Y, iy, ix = Cc[keep], R[keep], X[keep], Y[keep], iy[keep], ix[keep]
M = len(Cc); print('candidate hexes', M, 'needed', N)
# squared distance (hex units) to each warped county, plus a tiny pull towards its centre for compact shapes
D = np.empty((M, NC), np.float32)
cent = np.array([p.centroid.coords[0] for p in polys])
for k in range(NC):
    d = distance_transform_edt(LAB != k + 1) * res / s
    D[:, k] = d[iy, ix] ** 2 + 0.01 * (((X - cent[k, 0]) ** 2 + (Y - cent[k, 1]) ** 2) / s ** 2)
sea = (depth[iy, ix] ** 2).astype(np.float32)
cols = np.concatenate([np.repeat(np.arange(NC), n), -np.ones(M - N, int)])
cost = np.where(cols[None, :] >= 0, D[:, np.maximum(cols, 0)], sea[:, None])
ri, ci = linear_sum_assignment(cost)
own = np.empty(M, int); own[ri] = cols[ci]
print('assignment done %.0fs, total cost %.1f' % (time.time() - T0, cost[ri, ci].sum()))

# ---------- neighbours, contiguity repair ----------
idx = {(int(c), int(r)): i for i, (c, r) in enumerate(zip(Cc, R))}
def nb(c, r):
    d = [(1, 0), (-1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)] if r % 2 == 0 else [(1, 0), (-1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
    return [idx[(c + a, r + b)] for a, b in d if (c + a, r + b) in idx]
NB = [nb(int(c), int(r)) for c, r in zip(Cc, R)]
def comps(cells):
    cells = set(cells); out = []
    while cells:
        s0 = cells.pop(); comp = {s0}; st = [s0]
        while st:
            q = st.pop()
            for w in NB[q]:
                if w in cells: cells.remove(w); comp.add(w); st.append(w)
        out.append(comp)
    return sorted(out, key=len, reverse=True)
def cells_of(k): return [i for i in range(M) if own[i] == k]
def conn_set(cs_):
    return len(cs_) <= 1 or len(comps(cs_)) == 1
def connected_without(k, g):
    c = [i for i in cells_of(k) if i != g]
    return len(c) == 0 or len(comps(c)) == 1
def repair(maxit=200):
    for it in range(maxit):
        fixed = False
        for k in range(NC):
            cc = comps(cells_of(k))
            if len(cc) == 1: continue
            main = cc[0]
            for orphan in cc[1:]:
                done = False
                for h in orphan:
                    for g in NB[h]:
                        m = own[g]
                        if m == k: continue
                        # swap: h joins m, one of m's hexes next to k's main body joins k
                        for g2 in ([i for i in range(M) if own[i] == m and any(w in main for w in NB[i])] if m >= 0 else [i for i in set(w for q in main for w in NB[q]) if own[i] == -1]):
                            if m >= 0 and not conn_set((set(cells_of(m)) - {g2}) | {h}): continue
                            own[h] = m; own[g2] = k; done = True; break
                        if done: break
                    if done: break
                if done: fixed = True; main = comps(cells_of(k))[0]
        if not fixed: break
repair()
disc = [C['name'] for C, k in zip(L.C, range(NC)) if len(comps(cells_of(k))) > 1]
print('disconnected counties after repair:', disc)

# ---------- stats against real borders ----------
mains = [W.main_part(i) for i in range(NC)]; bufs = [m.buffer(3e-4) for m in mains]
Rr = set()
for i in range(NC):
    for j in range(i + 1, NC):
        if bufs[i].intersects(mains[j]) and bufs[i].intersection(mains[j].boundary).length > 0.012: Rr.add((i, j))

# ---------- local polish: swap neighbouring hexagons between counties to keep more real borders ----------
# Counts never change (a swap trades one hexagon each way). Each swap must keep both counties in one piece and not
# push a hexagon far from its warped position. Greedy, deterministic, a few passes.
RA = np.zeros((NC, NC), bool)
for i, j in Rr: RA[i, j] = RA[j, i] = True
WD = float(cfg.hex.get('polish_pull', 0.25))
def e(p, q):
    if p < 0 or q < 0: return 0.0
    return 0.3 if p == q else (1.0 if RA[p, q] else -0.7)
def disp(i, k): return float(sea[i] if k < 0 else D[i, k])
members = {k: set(cells_of(k)) for k in range(NC)}
def conn(cells):
    if len(cells) <= 1: return True
    s0 = next(iter(cells)); seen = {s0}; st = [s0]
    while st:
        q = st.pop()
        for w in NB[q]:
            if w in cells and w not in seen: seen.add(w); st.append(w)
    return len(seen) == len(cells)
swaps = 0
for it in range(30):
    moved = 0
    for a_ in range(M):
        ka = own[a_]
        for b_ in NB[a_]:
            kb = own[b_]
            if kb == ka: continue
            before = sum(e(ka, own[w]) for w in NB[a_] if w != b_) + sum(e(kb, own[w]) for w in NB[b_] if w != a_)
            after = sum(e(kb, own[w]) for w in NB[a_] if w != b_) + sum(e(ka, own[w]) for w in NB[b_] if w != a_)
            dd = disp(a_, kb) + disp(b_, ka) - disp(a_, ka) - disp(b_, kb)
            if after - before - WD * dd <= 0.05: continue
            if ka >= 0 and not conn((members[ka] - {a_}) | {b_}): continue
            if kb >= 0 and not conn((members[kb] - {b_}) | {a_}): continue
            own[a_], own[b_] = kb, ka
            if ka >= 0: members[ka] = (members[ka] - {a_}) | {b_}
            if kb >= 0: members[kb] = (members[kb] - {b_}) | {a_}
            moved += 1; break
    swaps += moved
    if not moved: break
print('polish: %d swaps in %d passes' % (swaps, it + 1))
Hh = set()
for i in range(M):
    if own[i] < 0: continue
    for w in NB[i]:
        if own[w] >= 0 and own[w] != own[i]: Hh.add((min(own[i], own[w]), max(own[i], own[w])))
kept = len(Rr & Hh); sp = len(Hh - Rr)
print('border pairs kept: %d of %d (%.1f%%), %d spurious' % (kept, len(Rr), 100 * kept / len(Rr), sp))
sel = [i for i in range(M) if own[i] >= 0]
st_poly = unary_union([Polygon(p) .buffer(0) for p in parts]).buffer(0.002).buffer(-0.002)
hexU = unary_union([Polygon([(X[i] + s / SQ3 * math.cos(math.radians(-90 + 60 * t)), Y[i] + s / SQ3 * math.sin(math.radians(-90 + 60 * t))) for t in range(6)]) for i in sel])
print('outline IoU hexes vs warped state: %.3f; runtime %.0fs' % (hexU.intersection(st_poly).area / hexU.union(st_poly).area, time.time() - T0))

# lattice frame: subtract (oa, ob) so cells sit on the canonical lattice the rest of the pipeline uses
out = dict(unit=cfg.unit, s=s, N=N, shift=[oa, ob], f=[float(v) for v in f],
           stats=dict(kept=kept, real=len(Rr), spurious=sp, miss=len(Rr - Hh)),
           counties=[dict(name=L.C[k]['name'], fips=L.C[k]['fips'], pop=L.C[k]['pop'], d=L.C[k]['d'], r=L.C[k]['r'], n=int(n[k]),
                          cells=[[round(float(s * (Cc[i] + 0.5 * (R[i] & 1))), 5), round(float(0.8660254 * s * R[i]), 5)] for i in cells_of(k)],
                          anchor=[round(float(cent[k, 0] - oa), 4), round(float(cent[k, 1] - ob), 4)],
                          landArea=float(L.allarea[k])) for k in range(NC)],
           stateArea=float(st_poly.area))
json.dump(out, open(cfg.out('warp-layout.json'), 'w'))
print('wrote warp-layout.json')
