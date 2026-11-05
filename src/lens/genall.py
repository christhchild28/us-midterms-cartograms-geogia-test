"""Local lens fields: one displacement field per lens centre on a coarse grid, plus one global field
(the 'Whole map' view), packed (int16, delta-coded along x, gzip, base64) into lens-fields.json."""
import numpy as np, json, gzip, base64, math, time, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lensfield as L
from shapely.geometry import Point
from scipy.ndimage import map_coordinates
from shapely.ops import unary_union
from shapely.geometry import Polygon
cfg = L.cfg; F = L.F
SP = cfg.lens['spacing'] * F; R = cfg.lens['radius'] * F
x0, y0, x1, y1 = L.state.bounds
xs = np.arange(x0 - 0.1 * F, x1 + 0.1 * F + 1e-9, SP); ys = np.arange(y0 - 0.1 * F, y1 + 0.1 * F + 1e-9, SP)
centers = [(i, j) for j in range(len(ys)) for i in range(len(xs)) if L.state.distance(Point(xs[i], ys[j])) < 0.28 * F]
print('lens scale', round(F, 3), 'grid', len(xs), len(ys), 'centers', len(centers), 'radius', round(R, 3))
t = time.time()
arr = np.zeros((len(centers), L.ony, L.onx, 2), np.int16); dmin = 9
for n, (i, j) in enumerate(centers):
    U, det = L.field(xs[i], ys[j], R); dmin = min(dmin, det.min())
    assert np.abs(U).max() * 2000 < 32000, 'displacement exceeds int16 range'
    arr[n] = np.round(U * 2000).astype(np.int16)
    if n % 20 == 0: print(' centre', n, '/', len(centers), round(time.time() - t), 's', flush=True)
print('local fields done', round(time.time() - t), 's; min det', round(dmin, 3))
def enc(a):
    d = a.astype(np.int32).copy(); d[:, 1:, :] = a[:, 1:, :].astype(np.int32) - a[:, :-1, :].astype(np.int32)
    return d.astype(np.int16).tobytes()
blob = b''.join(enc(arr[n]) for n in range(len(centers)))

# ---- global field (Whole map of the outline-mode page; the warp page uses exact warp rings instead) ----
HAVE_RINGS = os.path.exists(cfg.out('rings.json'))
U, det = L.field(0, 0, 1, glob=True) if HAVE_RINGS else (np.zeros((L.ony, L.onx, 2)), np.ones((L.ony, L.onx)))
print('global det min/max', round(det.min(), 3), round(det.max(), 3), 'max|U|', round(np.abs(U).max(), 3))
assert det.min() > 0, 'global warp folds'
assert dmin > 0, 'a local warp folds'
a = np.round(U * 2000).astype(np.int16); assert np.abs(U).max() * 2000 < 32000
blob += enc(a)
def warp(pts):
    ix = (pts[:, 0] - L.ox0) / L.HO; iy = (pts[:, 1] - L.oy0) / L.HO
    return pts + np.stack([map_coordinates(U[:, :, 0], [iy, ix], order=1, mode='nearest'), map_coordinates(U[:, :, 1], [iy, ix], order=1, mode='nearest')], 1)
wl = [warp(np.array(p.exterior.coords)) for ps in L.polys for p in ps]
allw = np.vstack(wl); bx0, by0 = allw.min(0); bx1, by1 = allw.max(0)
D = json.load(open(cfg.out('rings.json') if HAVE_RINGS else cfg.out('warp-rings.json'))) if (HAVE_RINGS or os.path.exists(cfg.out('warp-rings.json'))) else dict(bounds=[x0, y0, x1, y1]); B = D['bounds']; vw = B[2] - B[0]; vh = B[3] - B[1]
w = (bx1 - bx0) * 1.06; h = (by1 - by0) * 1.06; cx = (bx0 + bx1) / 2; cy = (by0 + by1) / 2
if w / h < vw / vh: w = h * vw / vh
else: h = w * vh / vw
w = max(w, vw); h = max(h, vh)
gvb = [cx - w / 2, cy - h / 2, w, h]
ws = unary_union([Polygon(w_).buffer(0.002 * F) for w_ in wl]).buffer(-0.002 * F)
print('IoU warped state vs original (Whole map)', round(L.state.intersection(ws).area / L.state.union(ws).area, 3))
gz = gzip.compress(blob, 9)
st = L.state.simplify(0.004 * F); xy = np.array(st.exterior.coords)[:-1]
meta = dict(h=L.HO, ox=L.ox0, oy=L.oy0, nx=L.onx, ny=L.ony, scale=2000, sx=float(xs[0]), sy=float(ys[0]), sp=SP, gx=len(xs), gy=len(ys),
            centers=[[int(i), int(j)] for (i, j) in centers], radii=[R], data=base64.b64encode(gz).decode(),
            gvb=[round(v, 4) for v in gvb], outline=[int(round(v * 1000)) for v in xy.reshape(-1)], minDet=round(float(min(dmin, det.min())), 4))
json.dump(meta, open(cfg.out('lens-fields.json'), 'w'), separators=(',', ':'))
print('wrote lens-fields.json', round(os.path.getsize(cfg.out('lens-fields.json')) / 1e6, 2), 'MB')
