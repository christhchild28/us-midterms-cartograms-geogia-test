"""Ring helpers shared by the warp pipeline: hexagon outlines, resampling, in-place blobs."""
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

class Rings:
    def __init__(self, s, kmin=180):
        self.s = s; self.side = s / math.sqrt(3); self.kmin = kmin
    def hexagon(self, x, y):
        sd = self.side
        return Polygon([(x + sd * math.cos(math.radians(-90 + 60 * k)), y + sd * math.sin(math.radians(-90 + 60 * k))) for k in range(6)])
    def snap(self, cells):
        s = self.s; out = []
        for x, y in cells:
            r = round(y / (0.8660254 * s)); c = round(x / s - 0.5 * (r & 1)); out.append((s * (c + 0.5 * (r & 1)), s * 0.8660254 * r))
        return out
    def union(self, cells):
        u = unary_union([self.hexagon(x, y).buffer(1e-6, join_style=2) for x, y in cells]).buffer(-1e-6, join_style=2)
        if u.geom_type == 'MultiPolygon': u = max(u.geoms, key=lambda g: g.area)
        return u
    def hex_ring(self, cells):
        """outline of the hexagon union, one point per unit edge (x f), >= kmin points. returns (ring, n_holes)"""
        u = self.union(self.snap(cells)).simplify(1e-5); holes = len(u.interiors)
        u = orient(Polygon(u.exterior.coords), 1.0); v = list(u.exterior.coords)[:-1]
        pieces = []; E = 0
        for a, b in zip(v, v[1:] + v[:1]):
            m = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / self.side)); pieces.append((a, b, m)); E += m
        f = max(1, math.ceil(self.kmin / E)); ring = []
        for a, b, m in pieces:
            n = m * f
            for k in range(n): ring.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
        return np.array(ring), holes
    def ring_K(self, cells, K):
        """same outline resampled to exactly K points, keeping hexagon corners"""
        u = orient(Polygon(self.union(cells).simplify(1e-5).exterior.coords), 1.0); v = list(u.exterior.coords)[:-1]
        segs = []; E = 0
        for a, b in zip(v, v[1:] + v[:1]):
            m = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / self.side)); segs.append((a, b, m)); E += m
        if E > K: return None, E
        pts = []; e = 0
        for a, b, m in segs:
            for uu in range(m):
                cnt = ((e + 1) * K) // E - (e * K) // E; e += 1
                for j in range(cnt):
                    f = (uu + j / cnt) / m; pts.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        return np.array(pts), E
    def blob(self, n, cx, cy):
        """compact n-hexagon blob centred on (cx, cy): the in-place size of a county"""
        s = self.s; best = None
        for pa in range(5):
            for pb in range(5):
                ph = (pa / 5 * s, pb / 5 * s * 0.866)
                pts = np.array([(s * (c + 0.5 * (r & 1)) + ph[0], s * 0.866 * r + ph[1]) for r in range(-14, 15) for c in range(-14, 15)])
                d = (pts ** 2).sum(1) + np.random.default_rng(pa * 5 + pb).uniform(0, 1e-6, len(pts))
                sel = pts[np.argsort(d)[:n]]; sel = sel - sel.mean(0) + np.array([cx, cy])
                u = unary_union([self.hexagon(x, y).buffer(1e-6, join_style=2) for x, y in sel]).buffer(-1e-6, join_style=2)
                if u.geom_type == 'MultiPolygon': continue
                if best is None or u.length < best[0] - 1e-9: best = (u.length, sel)
        return best[1]

def resample(ring, K):
    pts = np.array(ring[:-1] if ring[0] == ring[-1] else ring)
    seg = np.sqrt(((np.roll(pts, -1, 0) - pts) ** 2).sum(1)); cum = np.concatenate([[0], np.cumsum(seg)]); Ltot = cum[-1]
    t = np.linspace(0, Ltot, K, endpoint=False); full = np.vstack([pts, pts[:1]]); out = np.empty((K, 2))
    idx = np.clip(np.searchsorted(cum, t, side='right') - 1, 0, len(pts) - 1); f = (t - cum[idx]) / np.where(seg[idx] > 0, seg[idx], 1)
    out[:, 0] = full[idx, 0] + f * (full[idx + 1, 0] - full[idx, 0]); out[:, 1] = full[idx, 1] + f * (full[idx + 1, 1] - full[idx, 1])
    return out
