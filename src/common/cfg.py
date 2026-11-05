"""Shared config loader. Every pipeline script calls cfg.load() and gets paths, projection and options
from one election config (elections/<id>/config.json). Path comes from argv-less env var CARTOGRAM_CONFIG."""
import json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULTS = {
    "hex": {"unit": 10000, "seed": 1, "relax": 0.93},
    "lens": {"start_county": None, "radius": 0.8, "spacing": 0.4, "grid": 0.03, "node": 0.09, "scale": "auto"},
    "population": {"format": "jhu-uid", "file": "data/raw/uid-lookup.csv"},
    "results": {"county_col": "county", "fips_col": None, "a_col": "a", "b_col": "b"},
    "geometry": {"file": "data/raw/us-counties.geojson"},
}
# reference extent (projected degrees) the Georgia-tuned lens constants were designed for
REF_EXTENT = 4.6


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


class Cfg:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        raw = json.load(open(self.path))
        self.raw = raw
        c = _merge(DEFAULTS, raw)
        self.c = c
        self.id = c["id"]
        self.dir = os.path.dirname(self.path)
        self.cache = os.path.join(self.dir, ".cache")
        os.makedirs(self.cache, exist_ok=True)
        self.state = c["state"]
        self.fips = self.state["fips"]
        self.hex = c["hex"]
        self.unit = int(self.hex["unit"])
        self.seed = int(self.hex["seed"])
        self.lens = c["lens"]
        self.a = c["candidates"]["a"]
        self.b = c["candidates"]["b"]
        self._feat = None
        self._proj = None

    # ---- paths ----
    def inp(self, rel):  # input file: relative to the election folder first, then repo root
        p = os.path.join(self.dir, rel)
        return p if os.path.exists(p) else os.path.join(ROOT, rel)
    def out(self, name): return os.path.join(self.dir, name)
    def tmp(self, name): return os.path.join(self.cache, name)

    # ---- geometry ----
    def features(self):
        if self._feat is None:
            gj = json.load(open(self.inp(self.c["geometry"]["file"])))
            self._feat = {f["id"]: f for f in gj["features"] if str(f["id"]).startswith(self.fips)}
            if not self._feat: raise SystemExit("no counties with FIPS prefix %s in geometry" % self.fips)
        return self._feat

    def _projection(self):
        if self._proj is None:
            p = self.c.get("projection") or {}
            if "lon0" in p and "lat0" in p:
                lon0, lat0 = p["lon0"], p["lat0"]
            else:  # centre of the state's bounding box
                xs, ys = [], []
                for f in self.features().values():
                    g = f["geometry"]; ps = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
                    for poly in ps:
                        for x, y in poly[0]: xs.append(x); ys.append(y)
                lon0, lat0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            self._proj = (lon0, lat0, math.cos(math.radians(lat0)))
        return self._proj

    @property
    def lon0(self): return self._projection()[0]
    @property
    def lat0(self): return self._projection()[1]
    @property
    def kk(self): return self._projection()[2]
    def proj(self, lon, lat): return ((lon - self.lon0) * self.kk, -lat)

    def lens_scale(self, extent):
        s = self.lens["scale"]
        return float(s) if s != "auto" else max(0.25, extent / REF_EXTENT)


def load(path=None):
    path = path or os.environ.get("CARTOGRAM_CONFIG")
    if not path: raise SystemExit("set CARTOGRAM_CONFIG or pass a config path")
    return Cfg(path)
