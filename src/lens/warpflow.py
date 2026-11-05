"""Density-equalizing flow applied to arbitrary points, with per-county area correction.
The same flow that draws the lens 'Whole map' is used to place the hexagons, so the hexmap follows the warp."""
import math, sys, os
os.environ.setdefault('LENS_GRID', str(__import__('json').load(open(os.environ['CARTOGRAM_CONFIG'])).get('hex', {}).get('warp_grid', 0.015)))   # finer than the lens grid: thin counties need it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely
from scipy.fft import dctn, idctn
from scipy.ndimage import map_coordinates, gaussian_filter
import lensfield as L
cfg = L.cfg; NC = len(L.C)
SEA = float(cfg.hex.get('warp_sea', 1.0))

def density(f):
    fg = np.where(L.LAB >= 0, f[np.maximum(L.LAB, 0)], 1.0)
    return np.where(L.INS, L.G0 * fg, SEA)

def advect(rho0, P0, TF=2.2, sig=0.3):
    rho = gaussian_filter(rho0, sig, mode='nearest'); rh = dctn(rho, type=2, norm='ortho')
    def rho_t(t): return idctn(rh * np.exp(-L.lam * t), type=2, norm='ortho')
    def vel(r, P):
        gyy, gxx = np.gradient(r, L.hy, L.hx)
        ix = (P[:, 0] - L.X0) / L.hx - .5; iy = (P[:, 1] - L.Y0) / L.hy - .5
        g = lambda a: map_coordinates(a, [iy, ix], order=1, mode='nearest')
        rp = g(r); return np.stack([-g(gxx) / rp, -g(gyy) / rp], 1)
    P = P0.copy(); T = TF * max(L.Lx, L.Ly) ** 2 / math.pi ** 2; t = 0.0
    while t < T:
        r1 = rho_t(t); v1 = vel(r1, P); vm = np.abs(v1).max()
        dt = min(0.3 * min(L.hx, L.hy) / max(vm, 1e-9), T - t, 0.02 * T)
        r2 = rho_t(t + dt / 2); v2 = vel(r2, P + 0.5 * dt * v1); P = P + dt * v2; t += dt
    return P

def main_part(i):
    return max(L.polys[i], key=lambda p: p.area)

def dense_rings(seg=0.02, tol=0.0015):
    """Exterior ring of each county's main part, simplified then densified so the warp bends it smoothly."""
    out = []
    for i in range(NC):
        g = shapely.segmentize(main_part(i).simplify(tol), seg)
        out.append(np.array(g.exterior.coords)[:-1])
    return out

def shoelace(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * (np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y))

def fit_areas(rings, passes=10, tol=0.02, log=print):
    """Scale each county's target mass until its warped area is proportional to its hexagon count."""
    n = L.nhex; f = np.ones(NC); allp = np.vstack(rings); cuts = np.cumsum([len(r) for r in rings])[:-1]
    for it in range(passes):
        Pw = advect(density(f), allp); parts = np.split(Pw, cuts)
        a = np.abs(np.array([shoelace(p) for p in parts])); abar = a.sum() / n.sum(); err = a / (n * abar) - 1
        log('  area pass %d: max error %.1f%%, mean %.1f%%, hex area %.5f' % (it, 100 * np.abs(err).max(), 100 * np.abs(err).mean(), abar))
        if np.abs(err).max() < tol: break
        f = f * (n * abar / a) ** 0.9
    return f, parts, abar
