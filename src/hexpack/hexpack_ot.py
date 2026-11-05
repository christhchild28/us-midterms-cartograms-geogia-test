import json, math, random, sys, time, os
import numpy as np, shapely
from shapely.geometry import shape, Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from scipy.optimize import linear_sum_assignment

UNIT = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 1
random.seed(SEED); np.random.seed(SEED)
LON0 = -83.4; K = math.cos(math.radians(32.7))
def proj(lon, lat): return ((lon - LON0) * K, -lat)

C = json.load(open('/tmp/ga/build/counties.json'))
gj = json.load(open('/tmp/ga/raw/counties.json'))
feat = {f['id']: f for f in gj['features'] if f['id'].startswith('13')}
def poly_of(c):
    g = feat[c['fips']]['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    ps = []
    for p in polys:
        ring = [proj(x, y) for x, y in p[0]]
        pg = Polygon(ring)
        if not pg.is_valid: pg = pg.buffer(0)
        ps.append(pg)
    ps.sort(key=lambda q: -q.area)
    return ps
for c in C:
    ps = poly_of(c); c['main'] = ps[0]; c['allarea'] = sum(p.area for p in ps)
    c['anchor'] = np.array([c['main'].centroid.x, c['main'].centroid.y])
    c['n'] = max(1, round(c['pop'] / UNIT))
NC = len(C); N = sum(c['n'] for c in C)
state = unary_union([c['main'].buffer(0.002) for c in C]).buffer(-0.002)
if state.geom_type == 'MultiPolygon': state = max(state.geoms, key=lambda g: g.area)
A = state.area
BAL = float(os.environ.get('BAL', '0'))
if BAL > 0:
    fx = [c for c in C if c['name'] == 'Fulton'][0]['anchor']
    RAD = float(os.environ.get('BALR', '0.9'))
    # grow a disc around Atlanta until the union adds BAL fraction of state area
    lo, hi = 0.05, 3.0
    for _ in range(40):
        mid = (lo + hi) / 2; u = state.union(Point(fx[0], fx[1]).buffer(mid))
        if u.area - A < BAL * A: lo = mid
        else: hi = mid
    reg_shape = state.union(Point(fx[0], fx[1]).buffer(hi))
else: reg_shape = state
A2 = reg_shape.area
s = math.sqrt(A2 / (0.8660254 * N))
print('N', N, 'state area', round(A, 3), 's', round(s, 4))

# ---------- hex grid helpers ----------
def center(c, r): return (s * (c + 0.5 * (r & 1)), s * 0.8660254 * r)
def nbrs(c, r):
    if r % 2 == 0: d = [(1,0),(-1,0),(-1,-1),(0,-1),(-1,1),(0,1)]
    else: d = [(1,0),(-1,0),(0,-1),(1,-1),(0,1),(1,1)]
    return [(c+a, r+b) for a, b in d]
minx, miny, maxx, maxy = reg_shape.bounds
cols = range(int(minx / s) - 3, int(maxx / s) + 4); rows = range(int(miny / (s*0.866)) - 3, int(maxy / (s*0.866)) + 4)
allc = [(c, r) for c in cols for r in rows]
xy = np.array([center(c, r) for c, r in allc])
pts = shapely.points(xy[:, 0], xy[:, 1])
inside = shapely.contains_xy(reg_shape, xy[:, 0], xy[:, 1])
dist = shapely.distance(pts, reg_shape.boundary)
sd = np.where(inside, dist, -dist)
order = np.argsort(-sd)[:N]
region = [allc[i] for i in order]
rset = set(region)
# fill holes: cells not in region whose neighbours are all in region -> swap with weakest boundary cell
def comps(cells):
    cs = set(cells); seen = set(); out = []
    for k in cs:
        if k in seen: continue
        st = [k]; seen.add(k); comp = [k]
        while st:
            q = st.pop()
            for n in nbrs(*q):
                if n in cs and n not in seen: seen.add(n); st.append(n); comp.append(n)
        out.append(comp)
    return out
cc = comps(region)
print('region components', [len(x) for x in cc])
cpos = {k: np.array(center(*k)) for k in allc}
poly_region_iou = None

# ---------- real adjacency ----------
R = set()
bufs = [c['main'].buffer(3e-4) for c in C]
for i in range(NC):
    for j in range(i+1, NC):
        if bufs[i].intersects(C[j]['main']):
            if bufs[i].intersection(C[j]['main'].boundary).length > 0.012: R.add((i, j))
print('real border pairs', len(R))

# ---------- disc relaxation: touching discs sized by population, inside the state ----------
real_anchors = np.array([c['anchor'] for c in C])
cellarea = 0.8660254 * s * s
nvec = np.array([c['n'] for c in C], float)
rad = np.sqrt(nvec * cellarea / math.pi)
Ri = np.array([i for i, j in sorted(R)]); Rj = np.array([j for i, j in sorted(R)])
eroded = [state.buffer(-0.55 * rad[i]) if state.buffer(-0.55 * rad[i]).area > 0 else state for i in range(NC)]
def relax_discs(P0, alpha, iters=5000, k_adj=0.35, k_anchor=0.012, seed=0):
    r = rad * alpha
    P = P0.copy()
    for it in range(iters):
        cool = 1.0 if it < iters * 0.6 else 0.5
        D = P[:, None, :] - P[None, :, :]
        dist = np.sqrt((D ** 2).sum(-1)) + 1e-9
        np.fill_diagonal(dist, 1e9)
        ov = np.clip((r[:, None] + r[None, :]) - dist, 0, None)
        F = ((ov[:, :, None] * D / dist[:, :, None]).sum(1)) * 0.5
        d = P[Ri] - P[Rj]; dd = np.sqrt((d ** 2).sum(1)) + 1e-9
        gap = np.clip(dd - (r[Ri] + r[Rj]) * 1.02, 0, None)
        pull = (k_adj * gap / dd)[:, None] * d
        np.add.at(F, Ri, -pull); np.add.at(F, Rj, pull)
        F += k_anchor * (P0 - P)
        P = P + 0.6 * cool * F
        if it % 5 == 0:
            xs = shapely.points(P[:, 0], P[:, 1])
            for i in range(NC):
                if not eroded[i].contains(xs[i]):
                    q = shapely.ops.nearest_points(eroded[i], xs[i])[0]
                    P[i] = [q.x, q.y]
    return P
import shapely.ops
import shapely.ops
K_PER = int(os.environ.get('KPER', '5'))
rng = np.random.default_rng(SEED)
samp_xy = []; samp_c = []
for i in range(NC):
    ps = poly_of(C[i]); tot_a = sum(p.area for p in ps)
    need = C[i]['n'] * K_PER
    for p in ps:
        m = max(1, round(need * p.area / tot_a)) if p is not ps[0] else None
        if p is ps[0]: m = need - sum(max(1, round(need * q.area / tot_a)) for q in ps[1:]); m = max(1, m)
        bx0, by0, bx1, by1 = p.bounds; got = []
        while len(got) < m:
            q = rng.uniform([bx0, by0], [bx1, by1], size=(m * 3, 2))
            ok = shapely.contains_xy(p, q[:, 0], q[:, 1]); got += list(q[ok])
        for g in got[:m]: samp_xy.append(g); samp_c.append(i)
samp_xy = np.array(samp_xy); samp_c = np.array(samp_c)
NS = N * K_PER
# trim/pad to exactly NS
if len(samp_xy) > NS: samp_xy = samp_xy[:NS]; samp_c = samp_c[:NS]
cellxy = np.array([cpos[k] for k in region])
slots_cell = np.repeat(np.arange(N), K_PER)
print('OT samples', len(samp_xy), 'slots', len(slots_cell))
cost = ((samp_xy[:, None, :] - cellxy[slots_cell][None, :, :]) ** 2).sum(-1)
ri, ci = linear_sum_assignment(cost); del cost
cell_of_sample = np.empty(len(samp_xy), int); cell_of_sample[ri] = slots_cell[ci]
V = np.zeros((N, NC))
for sidx in range(len(samp_xy)): V[cell_of_sample[sidx], samp_c[sidx]] += 1
slots = np.concatenate([[i] * C[i]['n'] for i in range(NC)]).astype(int)
ri, ci = linear_sum_assignment(-V[:, slots])
own = np.empty(N, int); own[ri] = slots[ci]
owner = {region[k]: int(own[k]) for k in range(N)}
anchors = np.zeros((NC, 2))
for i in range(NC):
    ks = [k for k in range(N) if own[k] == i]; anchors[i] = cellxy[ks].mean(0)
print('OT done; mean shift from real centroid (deg)', round(float(np.sqrt(((anchors - real_anchors) ** 2).sum(1)).mean()), 3))


# ---------- contiguity repair + annealing ----------
WM, WS, WD, WC, WCC = float(os.environ.get('WM','2.0')), 0.8, float(os.environ.get('WD','1.5')), 0.3, 6.0
cellsof = [set() for _ in range(NC)]
for k, o in owner.items(): cellsof[o].add(k)
def ncomp(cells):
    if not cells: return 0
    cs = cells; seen = set(); n = 0
    for k0 in cs:
        if k0 in seen: continue
        n += 1; st = [k0]; seen.add(k0)
        while st:
            q = st.pop()
            for nb in nbrs(*q):
                if nb in cs and nb not in seen: seen.add(nb); st.append(nb)
    return n
def perim(cells):
    return sum(1 for k in cells for n in nbrs(*k) if n not in cells)
def pmin(n): return 2 * math.ceil(math.sqrt(12 * n - 3))
# weighted real borders
Rw = {}
for (i, j) in R:
    L = bufs[i].intersection(C[j]['main'].boundary).length
    Rw[(i, j)] = max(0.4, min(1.6, L / 0.12))
def edges_E():
    E = {}
    for k, o in owner.items():
        for n in nbrs(*k):
            o2 = owner.get(n)
            if o2 is not None and o2 != o and k < n:
                key = (min(o, o2), max(o, o2)); E[key] = E.get(key, 0) + 1
    return E
E = edges_E()
def pair_cost(key, e):
    if e > 0: return 0.0 if key in R else WS
    return WM * Rw[key] if key in R else 0.0
S = np.zeros((NC, 2)); nn = np.array([len(cellsof[i]) for i in range(NC)])
for k, o in owner.items(): S[o] += cpos[k]
def disp(i, Si=None):
    Si = S[i] if Si is None else Si
    return nn[i] * float(((Si / nn[i] - anchors[i]) ** 2).sum()) / (s * s)
cc = [ncomp(cellsof[i]) for i in range(NC)]
P = [perim(cellsof[i]) for i in range(NC)]
def stats():
    ok = sum(1 for key in R if E.get(key, 0) > 0)
    sp = sum(1 for key in E if key not in R)
    return ok, len(R), sp
print('before SA: kept %d of %d real borders, %d spurious; disconnected %d' % (*stats(), sum(1 for c_ in cc if c_ > 1)))
def touched_edges(cells_):
    es = set()
    for k in cells_:
        for n in nbrs(*k):
            if n in owner: es.add((k, n) if k < n else (n, k))
    return es
def apply_edges(es, sign):
    changed = {}
    for a, b in es:
        o1, o2 = owner[a], owner[b]
        if o1 == o2: continue
        key = (min(o1, o2), max(o1, o2)); changed[key] = changed.get(key, 0) + sign
    return changed
def swap(x, y):
    A_, B_ = owner[x], owner[y]
    es = touched_edges([x, y])
    before = apply_edges(es, -1)
    cellsof[A_].remove(x); cellsof[B_].remove(y); cellsof[A_].add(y); cellsof[B_].add(x)
    ca, cb = ncomp(cellsof[A_]), ncomp(cellsof[B_])
    if ca > cc[A_] or cb > cc[B_]:
        cellsof[A_].remove(y); cellsof[B_].remove(x); cellsof[A_].add(x); cellsof[B_].add(y)
        return None
    owner[x], owner[y] = B_, A_
    after = apply_edges(es, +1)
    keys = set(before) | set(after)
    dc = 0.0
    for key in keys:
        e0 = E.get(key, 0); e1 = e0 + before.get(key, 0) + after.get(key, 0)
        dc += pair_cost(key, e1) - pair_cost(key, e0)
    SA_ = S[A_] + cpos[y] - cpos[x]; SB_ = S[B_] + cpos[x] - cpos[y]
    dd = disp(A_, SA_) + disp(B_, SB_) - disp(A_) - disp(B_)
    pa, pb = perim(cellsof[A_]), perim(cellsof[B_])
    dp = (max(0, pa - pmin(nn[A_])) - max(0, P[A_] - pmin(nn[A_]))) + (max(0, pb - pmin(nn[B_])) - max(0, P[B_] - pmin(nn[B_])))
    dcc = (ca - cc[A_]) + (cb - cc[B_])
    return dc + WD * dd + WC * dp + WCC * dcc, (keys, before, after, SA_, SB_, A_, B_, x, y, ca, cb, pa, pb)
def commit(info):
    keys, before, after, SA_, SB_, A_, B_, x, y, ca, cb, pa, pb = info
    for key in keys:
        e1 = E.get(key, 0) + before.get(key, 0) + after.get(key, 0)
        if e1 <= 0: E.pop(key, None)
        else: E[key] = e1
    S[A_] = SA_; S[B_] = SB_; cc[A_] = ca; cc[B_] = cb; P[A_] = pa; P[B_] = pb
def revert(info):
    keys, before, after, SA_, SB_, A_, B_, x, y, ca, cb, pa, pb = info
    owner[x], owner[y] = A_, B_
    cellsof[A_].remove(y); cellsof[B_].remove(x); cellsof[A_].add(x); cellsof[B_].add(y)
def run_sa(ITER, T0, p=1.5, ptarget=0.45):
    bnd = []; miss_ = []
    for it in range(ITER):
        T = T0 * (1 - it / ITER) ** p + 0.02
        if it % 3000 == 0:
            bnd = [k for k in owner if any(owner.get(n, owner[k]) != owner[k] for n in nbrs(*k))]
            miss_ = [(i, j) for (i, j) in R if E.get((i, j), 0) == 0]
        if miss_ and random.random() < ptarget:
            i, j = random.choice(miss_)
            if random.random() < 0.5: i, j = j, i
            cj = S[j] / nn[j]
            cl = list(cellsof[i]); samp = random.sample(cl, min(len(cl), 6))
            x = min(samp, key=lambda k: float(((cpos[k] - cj) ** 2).sum()))
            dx = float(((cpos[x] - cj) ** 2).sum())
            ys = [n for n in nbrs(*x) if n in owner and owner[n] != i and float(((cpos[n] - cj) ** 2).sum()) < dx]
            if not ys: continue
            y = random.choice(ys)
        else:
            x = random.choice(bnd)
            ys = [n for n in nbrs(*x) if n in owner and owner[n] != owner[x]]
            if not ys: continue
            y = random.choice(ys)
        res = swap(x, y)
        if res is None: continue
        dcost, info = res
        if dcost <= 0 or random.random() < math.exp(-dcost / T): commit(info)
        else: revert(info)
def components(cells):
    seen = set(); out = []
    for k0 in cells:
        if k0 in seen: continue
        st = [k0]; seen.add(k0); comp = [k0]
        while st:
            q = st.pop()
            for nb in nbrs(*q):
                if nb in cells and nb not in seen: seen.add(nb); st.append(nb); comp.append(nb)
        out.append(comp)
    return out
def repair2():
    for i in range(NC):
        for step in range(600):
            if cc[i] <= 1: break
            comps_ = sorted(components(cellsof[i]), key=len); stray = comps_[0]; main = comps_[-1]
            mxy = np.array([cpos[k] for k in main])
            best = None
            for x in stray:
                dx = np.sqrt(((mxy - cpos[x]) ** 2).sum(1)).min()
                for y in nbrs(*x):
                    B_ = owner.get(y)
                    if B_ is None or B_ == i: continue
                    dy = np.sqrt(((mxy - cpos[y]) ** 2).sum(1)).min()
                    if dy < dx - 1e-9 and (best is None or dy < best[0]): best = (dy, x, y)
            if best is None:
                print('repair2 stuck', C[i]['name'], [len(c_) for c_ in comps_], 'stray', stray[:3]); break
            _, x, y = best
            B_ = owner[y]
            # perform swap if neither county gets worse connectivity (A's stray moves closer)
            cellsof[i].remove(x); cellsof[B_].remove(y); cellsof[i].add(y); cellsof[B_].add(x)
            ca, cb = ncomp(cellsof[i]), ncomp(cellsof[B_])
            if cb > cc[B_] or ca > cc[i] + 0:
                # try alternatives: revert and stop trying this pair
                cellsof[i].remove(y); cellsof[B_].remove(x); cellsof[i].add(x); cellsof[B_].add(y)
                # block by marking: shuffle by moving on (try random other stray cell)
                alt = [(xx, yy) for xx in stray for yy in nbrs(*xx) if owner.get(yy) not in (None, i)]
                random.shuffle(alt); done = False
                for xx, yy in alt[:20]:
                    BB = owner[yy]
                    cellsof[i].remove(xx); cellsof[BB].remove(yy); cellsof[i].add(yy); cellsof[BB].add(xx)
                    ca2, cb2 = ncomp(cellsof[i]), ncomp(cellsof[BB])
                    if cb2 <= cc[BB] and ca2 <= cc[i]:
                        owner[xx], owner[yy] = BB, i; S[i] += cpos[yy] - cpos[xx]; S[BB] += cpos[xx] - cpos[yy]; cc[i], cc[BB] = ca2, cb2; done = True; break
                    cellsof[i].remove(yy); cellsof[BB].remove(xx); cellsof[i].add(xx); cellsof[BB].add(yy)
                if not done: break
                continue
            owner[x], owner[y] = B_, i; S[i] += cpos[y] - cpos[x]; S[B_] += cpos[x] - cpos[y]; cc[i], cc[B_] = ca, cb
    for i in range(NC): P[i] = perim(cellsof[i])
    E.clear(); E.update(edges_E())

def release_options(Xa, Xb):
    opts = []
    for v in cellsof[Xa]:
        if any(owner.get(n) == Xb for n in nbrs(*v)):
            if ncomp(cellsof[Xa] - {v}) <= 1: opts.append(v)
    return opts
def adj_counties(X):
    return {owner[n] for k in cellsof[X] for n in nbrs(*k) if n in owner and owner[n] != X}
def bfs_path(starts, target):
    from collections import deque
    if target in starts: return [target]
    prev = {}; dq = deque()
    for a in starts: prev[a] = None; dq.append(a)
    while dq:
        a = dq.popleft()
        for b in adj_counties(a):
            if b in prev: continue
            if not release_options(a, b): continue
            prev[b] = a
            if b == target:
                path = [b]
                while prev[path[-1]] is not None: path.append(prev[path[-1]])
                return path[::-1]
            dq.append(b)
    return None
def fix_county(i):
    comps_ = sorted(components(cellsof[i]), key=len)
    strays = [k for c_ in comps_[:-1] for k in c_]
    for k in strays: cellsof[i].remove(k); del owner[k]
    for u in strays:
        cands = {owner[n] for n in nbrs(*u) if n in owner}
        path = bfs_path(cands, i)
        if path is None:
            print('  fix failed for', C[i]['name']); 
            X0 = next(iter(cands)); owner[u] = X0; cellsof[X0].add(u); continue
        owner[u] = path[0]; cellsof[path[0]].add(u)
        ex = path[0]
        guard = 0
        while ex != i and guard < 60:
            guard += 1
            p2 = bfs_path({ex}, i)
            if p2 is None or len(p2) < 2:
                print('  chain broke for', C[i]['name'], 'at', C[ex]['name']); break
            a_, b_ = p2[0], p2[1]
            opts = release_options(a_, b_)
            v = min(opts, key=lambda q: float(((cpos[q] - anchors[b_]) ** 2).sum()))
            cellsof[a_].remove(v); cellsof[b_].add(v); owner[v] = b_
            ex = b_
def rebuild_state():
    S[:] = 0
    for k, o in owner.items(): S[o] += cpos[k]
    for i in range(NC): nn[i] = len(cellsof[i]); cc[i] = ncomp(cellsof[i]); P[i] = perim(cellsof[i])
    E.clear(); E.update(edges_E())
t0 = time.time()
ITER = int(sys.argv[3]) if len(sys.argv) > 3 else 120000
repair2()
for i in range(NC):
    if cc[i] > 1: fix_county(i)
rebuild_state()
print('disconnected before SA:', [C[i]['name'] for i in range(NC) if cc[i] > 1], 'sizes ok', all(nn[i]==C[i]['n'] for i in range(NC)))
print('start: kept %d of %d, %d spurious' % stats())
run_sa(ITER, 1.0)
WCC = 40.0
run_sa(ITER // 3, 0.3)
print('SA done in %.1fs' % (time.time() - t0))
E.clear(); E.update(edges_E())
ok, tot, sp = stats()
disc = [C[i]['name'] for i in range(NC) if ncomp(cellsof[i]) > 1]
print('after SA: kept %d of %d real borders (%.1f%%), %d spurious touches; disconnected %s' % (ok, tot, 100*ok/tot, sp, disc))
miss = [(C[i]['name'], C[j]['name']) for (i, j) in R if E.get((i, j), 0) == 0]
print('missing', len(miss), miss[:10])
print('mean centroid displacement (deg)', round(sum(math.sqrt(((S[i]/nn[i]-anchors[i])**2).sum()) for i in range(NC))/NC, 3), 'cell', round(s, 3))
excess = sum(max(0, P[i]-pmin(nn[i])) for i in range(NC)); print('perimeter excess total', excess, 'of', sum(P))
# region iou
cellpoly = [Polygon([(cpos[k][0] + (s/math.sqrt(3))*math.cos(math.radians(-90+60*t)), cpos[k][1] + (s/math.sqrt(3))*math.sin(math.radians(-90+60*t))) for t in range(6)]) for k in owner]
ru = unary_union(cellpoly)
print('IoU region vs state', round(ru.intersection(state).area / ru.union(state).area, 3))

out = dict(unit=UNIT, s=s, N=N, stats=dict(kept=ok, real=tot, spurious=sp, miss=len(miss)),
           counties=[dict(name=C[i]['name'], fips=C[i]['fips'], pop=C[i]['pop'], d=C[i]['d'], r=C[i]['r'], n=int(nn[i]),
                          cells=[[round(cpos[k][0], 4), round(cpos[k][1], 4)] for k in sorted(cellsof[i])],
                          anchor=[round(float(real_anchors[i][0]), 4), round(float(real_anchors[i][1]), 4)],
                          landArea=C[i]['allarea']) for i in range(NC)],
           stateArea=A)
json.dump(out, open('/tmp/ga/hp/packot_%s_%d_%d.json' % (os.environ.get('TAG','x'), UNIT, SEED), 'w'))

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
fig, ax = plt.subplots(figsize=(7, 8))
cm = plt.cm.RdBu
for i, c in enumerate(C):
    m = (c['d'] - c['r']) / (c['d'] + c['r']); col = cm(0.5 + max(-1, min(1, m / 0.6)) * 0.5)
    for k in cellsof[i]:
        x, y = cpos[k]; r_ = s / math.sqrt(3)
        ax.add_patch(MP([(x + r_*math.cos(math.radians(-90+60*t)), y + r_*math.sin(math.radians(-90+60*t))) for t in range(6)], facecolor=col, edgecolor='white', lw=0.3))
    uu = unary_union([Polygon([(cpos[k][0] + (s/math.sqrt(3))*math.cos(math.radians(-90+60*t)), cpos[k][1] + (s/math.sqrt(3))*math.sin(math.radians(-90+60*t))) for t in range(6)]) for k in cellsof[i]])
    geoms = [uu] if uu.geom_type == 'Polygon' else list(uu.geoms)
    for g in geoms:
        xs, ys = g.exterior.xy; ax.plot(xs, ys, color='#222', lw=0.6)
for g in ([state] if state.geom_type == 'Polygon' else state.geoms):
    xs, ys = g.exterior.xy; ax.plot(xs, ys, color='#e6a800', lw=1.2, ls='--')
ax.set_aspect('equal'); ax.invert_yaxis(); ax.axis('off')
plt.savefig('/tmp/ga/hp/packot_%s_%d_%d.png' % (os.environ.get('TAG','x'), UNIT, SEED), dpi=90, bbox_inches='tight')
