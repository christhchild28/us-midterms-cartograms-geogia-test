"""Join county geometry + population + two-candidate results into <cache>/counties.json.
Internal field names keep the original d / r = candidate A / candidate B."""
import csv, json, re, sys
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__file__), '..'))
from common import cfg as C_

cfg = C_.load()
feat = cfg.features()

def norm(s):
    s = s.lower().replace('&', 'and').replace('.', '').replace("'", '').replace('’', '')
    s = re.sub(r'\b(county|parish|borough|census area|municipality|city and borough)\b', '', s)
    s = re.sub(r'\bsaint\b', 'st', s)
    return re.sub(r'[^a-z0-9]+', '', s)

# ---- population ----
pc = cfg.c['population']; popfile = cfg.inp(pc['file'])
pop, pname = {}, {}
if pc['format'] == 'jhu-uid':        # JHU CSSE UID_ISO_FIPS_LookUp_Table.csv
    for r in csv.DictReader(open(popfile, encoding='utf-8')):
        if r['Province_State'] == cfg.state['name'] and r['FIPS'] and r['Admin2']:
            f = r['FIPS'].split('.')[0].zfill(5)
            pop[f] = int(float(r['Population'] or 0)); pname[f] = r['Admin2']
elif pc['format'] == 'csv':          # any CSV: fips_col, pop_col, name_col
    for r in csv.DictReader(open(popfile, encoding='utf-8')):
        f = r[pc['fips_col']].split('.')[0].zfill(5)
        if f.startswith(cfg.fips): pop[f] = int(float(r[pc['pop_col']])); pname[f] = r.get(pc.get('name_col', ''), f)
else:
    raise SystemExit('unknown population format ' + pc['format'])

# ---- results ----
rc = cfg.c['results']; rows = list(csv.DictReader(open(cfg.inp(rc['file']), encoding='utf-8')))
byname = {norm(pname[f]): f for f in pop}
res, unmatched = {}, []
for r in rows:
    if rc.get('fips_col'):
        f = r[rc['fips_col']].split('.')[0].zfill(5)
    else:
        f = byname.get(norm(r[rc['county_col']]))
    if f is None or f not in feat or f not in pop: unmatched.append(r.get(rc['county_col']) or r.get(rc.get('fips_col'))); continue
    res[f] = (int(float(r[rc['a_col']])), int(float(r[rc['b_col']])))
nores = sorted(pname.get(f, f) for f in feat if f not in res)

def centroid(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    A = cx = cy = 0
    for p in polys:
        ring = p[0]
        for i in range(len(ring) - 1):
            x0, y0 = ring[i]; x1, y1 = ring[i + 1]
            c = x0 * y1 - x1 * y0; A += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    A /= 2; return cx / (6 * A), cy / (6 * A)

out = []
for f in sorted(feat):
    if f not in res or f not in pop: continue
    lon, lat = centroid(feat[f]['geometry'])
    out.append(dict(name=pname[f], fips=f, pop=pop[f], lon=round(lon, 4), lat=round(lat, 4), d=res[f][0], r=res[f][1]))
# keep results-file order (Georgia's alphabetical order == FIPS order, but stay faithful to the file)
order = {}
for i, r in enumerate(rows):
    f = r[rc['fips_col']].split('.')[0].zfill(5) if rc.get('fips_col') else byname.get(norm(r[rc['county_col']]))
    order[f] = i
out.sort(key=lambda o: order.get(o['fips'], 1e9))
print(len(out), 'counties joined; results rows unmatched:', unmatched, '; geometry counties without results:', nores)
print('pop total', sum(o['pop'] for o in out), '| votes A/B', sum(o['d'] for o in out), sum(o['r'] for o in out))
print('largest', [(o['name'], o['pop']) for o in sorted(out, key=lambda o: -o['pop'])[:5]], '| zero-pop', [o['name'] for o in out if o['pop'] <= 0])
if unmatched or nores or any(o['pop'] <= 0 for o in out):
    raise SystemExit('JOIN FAILED: every county in the geometry needs a population and a results row (see lists above)')
json.dump(out, open(cfg.tmp('counties.json'), 'w'))
