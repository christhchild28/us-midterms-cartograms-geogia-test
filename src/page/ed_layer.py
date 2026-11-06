"""Optional fourth view for the warp page: the real shapes of a finer geography (NYC election districts)
shaded by margin, with pan/zoom and a tap card. Driven by the `ed` block of the election config:

  "ed": {"geometry": "election-districts.geojson",      # GeoJSON, feature id = unit id (e.g. 23001 = AD 23, ED 1)
         "results": "ed-results.csv", "id_col": "ed", "a_col": "hochul", "b_col": "blakeman", "pct_col": "pct",
         "parent_div": 1000,                              # parent unit (e.g. Assembly district) = id // parent_div
         "parent_label": "AD", "child_label": "ED", "parent_noun": "Assembly district",
         "noun": "election district", "plural": "election districts", "button": "Precincts",
         "partial_below": 90, "scale": 10000}

build(cfg, counties) returns the template tokens; with no `ed` block every token is empty and the page is unchanged.
Integrity checks (the build stops on failure): every polygon needs a results row, results rows without a polygon
must have zero votes, and the unit totals must equal the parent-unit totals used by the rest of the page."""
import csv, html, json, os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ed')
PARTS = {'ED_CSS': 'ed.css', 'ED_JS': 'ed.js', 'ED_BTN': 'ed.btn.html', 'ED_MAP': 'ed.map.html', 'ED_SIDE': 'ed.side.html'}


def _read(name): return open(os.path.join(HERE, name), encoding='utf-8').read()


def build(cfg, counties):
    e = cfg.c.get('ed')
    if not e: return {k: '' for k in PARTS}
    ES = int(e.get('scale', 10000)); div = int(e.get('parent_div', 1000))
    idc, ac, bc, pc = e.get('id_col', 'ed'), e['a_col'], e['b_col'], e.get('pct_col')
    gj = json.load(open(cfg.inp(e['geometry']), encoding='utf-8'))
    rows = {}
    for r in csv.DictReader(open(cfg.inp(e['results']), encoding='utf-8')): rows[r[idc].strip()] = r
    ids, A, B, P, RINGS, missing, dropped = [], [], [], [], [], [], []
    for f in sorted(gj['features'], key=lambda f: int(f['id'])):
        fid = str(f['id']); r = rows.get(fid)
        if r is None: missing.append(fid); continue
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        unit = []
        for poly in polys:
            for ring in poly:
                pts = []
                for lon, lat in ring:
                    x, y = cfg.proj(lon, lat); q = (int(round(x * ES)), int(round(y * ES)))
                    if not pts or pts[-1] != q: pts.append(q)
                if len(pts) > 1 and pts[0] == pts[-1]: pts.pop()
                if len(pts) < 3: continue
                flat = [pts[0][0], pts[0][1]]
                for k in range(1, len(pts)): flat += [pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]]
                unit.append(flat)
        if not unit:
            if int(float(r[ac])) + int(float(r[bc])): raise SystemExit('ED %s has votes but no usable ring' % fid)
            dropped.append(fid); continue
        ids.append(int(fid)); A.append(int(float(r[ac]))); B.append(int(float(r[bc])))
        P.append(int(round(float(r[pc]) * 10)) if pc and r.get(pc) not in (None, '') else 1000); RINGS.append(unit)
    if missing: raise SystemExit('ED JOIN FAILED: %d polygons have no results row, e.g. %s' % (len(missing), missing[:8]))
    gid = {str(f['id']) for f in gj['features']}
    orphan = [k for k, r in rows.items() if k not in gid and (int(float(r[ac])) + int(float(r[bc])))]
    if orphan: raise SystemExit('ED JOIN FAILED: %d results rows with votes have no polygon, e.g. %s' % (len(orphan), orphan[:8]))
    ta, tb = sum(c['d'] for c in counties), sum(c['r'] for c in counties)
    if not e.get('allow_mismatch') and (sum(A) != ta or sum(B) != tb):
        raise SystemExit('ED TOTALS DO NOT MATCH the parent units: A %d vs %d, B %d vs %d' % (sum(A), ta, sum(B), tb))
    # parent unit of each ED: by default the leading digits of its id (AD*1000+ED); a parent_map csv (ed,parent) overrides it (e.g. EDs grouped into council districts)
    if e.get('parent_map'):
        pm = {r['ed'].strip(): int(r['parent']) for r in csv.DictReader(open(cfg.inp(e['parent_map']), encoding='utf-8'))}
        miss = [i for i in ids if str(i) not in pm]
        if miss: raise SystemExit('ED parent_map is missing %d EDs, e.g. %s' % (len(miss), miss[:8]))
        par = [pm[str(i)] for i in ids]
        lab = ['%d-%d' % (i // div, i % div) for i in ids]
    else:
        par = [i // div for i in ids]; lab = [str(i % div) for i in ids]
    pnames = {c['fips'][-3:]: c['name'] for c in counties}
    for k in par:
        if '%03d' % k not in pnames: raise SystemExit('ED parent %d is not a unit in the page data' % k)
    # parent-unit (e.g. Assembly district) borders, unioned from the finer shapes so they stay aligned when zoomed right in
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    byp = {}
    for f in gj['features']:
        fid = str(f['id'])
        if fid not in rows: continue
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            rr = [[(round(cfg.proj(lo, la)[0] * ES), round(cfg.proj(lo, la)[1] * ES)) for lo, la in ring] for ring in poly]
            pg = Polygon(rr[0], rr[1:]); pg = pg if pg.is_valid else pg.buffer(0)
            byp.setdefault(pm[fid] if e.get('parent_map') else int(fid) // div, []).append(pg)
    eps = float(e.get('border_close', 0.0004)) * ES   # closes the hairline gaps left by simplifying neighbours separately
    pid, prings = [], []
    for k in sorted(byp):
        u = unary_union(byp[k]).buffer(eps).buffer(-eps).simplify(ES * 0.00002)
        gs = list(u.geoms) if u.geom_type == 'MultiPolygon' else [u]
        out = []
        for gg in gs:
            for ring in [gg.exterior] + list(gg.interiors):
                pts = [(int(round(x)), int(round(y))) for x, y in ring.coords][:-1]
                if len(pts) < 3: continue
                flat = [pts[0][0], pts[0][1]]
                for j in range(1, len(pts)): flat += [pts[j][0] - pts[j - 1][0], pts[j][1] - pts[j - 1][1]]
                out.append(flat)
        pid.append(k); prings.append(out)
    data = dict(pid=pid, pr=prings, es=ES, div=div, id=ids, a=A, b=B, p=P, r=RINGS, par=par, lab=lab, partial=float(e.get('partial_below', 90)),
                pl=e.get('parent_label', 'AD'), cl=e.get('child_label', 'ED'), pn=e.get('parent_noun', 'district'),
                noun=e.get('noun', 'precinct'), plural=e.get('plural', 'precincts'), ncount=len(ids),
                nvotes=sum(1 for k in range(len(ids)) if A[k] + B[k] > 0), npartial=sum(1 for k in range(len(ids)) if A[k] + B[k] > 0 and P[k] / 10 < float(e.get('partial_below', 90))))
    dj = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    print('ed layer: %d units, %d with votes, %d below %.0f%% reporting, totals %d/%d reconcile with parent units, %.2f MB of shapes'
          % (len(ids), data['nvotes'], data['npartial'], data['partial'], sum(A), sum(B), len(dj) / 1e6))
    tok = {k: _read(f) for k, f in PARTS.items()}
    tok['ED_JS'] = tok['ED_JS'].replace('/*EDDATA*/null', dj)
    tok['ED_BTN'] = tok['ED_BTN'].replace('{{ED_BUTTON}}', html.escape(e.get('button', 'Precincts'), quote=True))
    return tok
