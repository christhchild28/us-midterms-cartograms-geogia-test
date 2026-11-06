"""Assemble elections/<id>/index.html (hexes follow the lens warp) from warp.template.html + warp-rings.json + lens-fields.json."""
import html, json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import cfg as cfg_
cfg = cfg_.load()

# Two-way colour ramps (light-mode mid/deep, dark-mode mid/deep). Georgia's blue/red are the validated pair.
RAMPS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'common', 'ramps.json')))
def ramp(cand):
    r = cand.get('ramp', 'blue')
    if isinstance(r, dict): return r
    if r not in RAMPS: raise SystemExit('unknown ramp %r (use %s or give {mid_l,deep_l,mid_d,deep_d})' % (r, '/'.join(RAMPS)))
    return RAMPS[r]

_raw = json.load(open(cfg.out('warp-rings.json')))
def _delta(a):                                   # first point absolute, then per-vertex differences (decoded in the page)
    assert all(isinstance(v, int) for v in a)
    return a[:2] + [a[i] - a[i - 2] for i in range(2, len(a))]
for _c in _raw['counties']:
    for _k in ('real', 'warp', 'hex', 'hex2'): _c[_k] = _delta(_c[_k])
_prior = cfg.c.get('prior')                      # optional comparison race: {"file","fips_col","a_col","b_col","label","short","a","b"}
if _prior:
    import csv
    _pm = {r[_prior.get('fips_col', 'fips')].split('.')[0].zfill(5): (int(float(r[_prior['a_col']])), int(float(r[_prior['b_col']]))) for r in csv.DictReader(open(cfg.inp(_prior['file']), encoding='utf-8'))}
    _miss = [c['name'] for c in _raw['counties'] if c['fips'] not in _pm]
    if _miss: raise SystemExit('prior file has no row for: %s' % _miss)
    for _c in _raw['counties']: _c['pd'], _c['pr'] = _pm[_c['fips']]
D = json.dumps(_raw, separators=(',', ':'))
_l = json.load(open(cfg.out('lens-fields.json')))
_sh = json.load(open(cfg.out('warp-rings.json')))['shift']          # the warp frame is the real frame shifted onto the hex lattice
_l['outline'] = [int(round(v - 1000 * _sh[i % 2])) for i, v in enumerate(_l['outline'])]
L = json.dumps(_l, separators=(',', ':'))
names = [c['name'] for c in json.loads(D)['counties']]
pops = {c['name']: c['pop'] for c in json.loads(D)['counties']}
start = cfg.lens.get('start_county')
if start not in names: start = max(pops, key=pops.get)
a, b = cfg.a, cfg.b
meta = dict(state=cfg.state['name'], people=cfg.state.get('people'), a=a['name'], b=b['name'], af=a.get('full', a['name']), bf=b.get('full', b['name']), start=start)
race = cfg.c['race']; year = (re.findall(r'\d{4}', race.get('date', '')) or [''])[-1]
if _prior: meta['prior'] = dict(label=_prior['label'], short=_prior['short'], a=_prior['a'], b=_prior['b'], now=year or 'Now')
src = cfg.c.get('text', {}).get('source') or ('Results: county returns as supplied for this build. Residents: Census Bureau county estimates.')
ra, rb = ramp(a), ramp(b)
tok = {
    'STATE': cfg.state['name'], 'OFFICE': race['office'], 'DATE': race.get('date', ''), 'RACE': (year + ' ' + race['office']).strip(),
    'UNIT': format(cfg.unit, ','), 'A': a['name'], 'B': b['name'], 'NCOUNTIES': str(len(names)), 'SOURCE': src,
    'A_MID_L': ra['mid_l'], 'A_DEEP_L': ra['deep_l'], 'A_MID_D': ra['mid_d'], 'A_DEEP_D': ra['deep_d'],
    'B_MID_L': rb['mid_l'], 'B_DEEP_L': rb['deep_l'], 'B_MID_D': rb['mid_d'], 'B_DEEP_D': rb['deep_d'],
}
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'warp.template.html')).read()
for k, v in tok.items(): t = t.replace('{{%s}}' % k, html.escape(v, quote=True))
# Optional vocabulary override for non-county units (districts, wards...) and non-resident weights (votes cast...).
# text.vocab = {"unit": "district", "units": "districts", "measure": "votes cast", "fix": [[old, new], ...]}
# "fix" pairs are exact replacements applied first and must each match; then the guarded word swap runs.
# Identifiers are left alone: anything preceded by '.', '-', '_' or a word character, and whole quoted tokens like 'county'.
vocab = cfg.c.get('text', {}).get('vocab')
if vocab:
    for old, new in vocab.get('fix', []):
        if old not in t: raise SystemExit('vocab fix not found in template: %r' % old)
        t = t.replace(old, new)
    cap = lambda s: s[:1].upper() + s[1:]
    forms = {'counties': vocab['units'], 'Counties': cap(vocab['units']), 'county': vocab['unit'], 'County': cap(vocab['unit'])}
    def _swap(m):
        s, e = m.start(), m.end()
        if s > 0 and e < len(t) and t[s - 1] in '\'"' and t[e] == t[s - 1]: return m.group(0)   # whole quoted token: an identifier
        return forms[m.group(1)]
    t = re.sub(r'(?<![.\w-])(counties|Counties|county|County)(?![\w-])', _swap, t)
    t = re.sub(r'\bresidents\b', vocab['measure'], t); t = re.sub(r'\bResidents\b', cap(vocab['measure']), t)
import ed_layer
_ed = ed_layer.build(cfg, json.loads(D)['counties']) if cfg.c.get('ed') else {}
for _k in ('ED_CSS', 'ED_BTN', 'ED_MAP', 'ED_SIDE', 'ED_JS'):
    t = t.replace({'ED_CSS': '/*ED_CSS*/', 'ED_JS': '/*ED_JS*/'}.get(_k, '<!--%s-->' % _k), _ed.get(_k, ''))
if _prior:
    _e = lambda s: html.escape(s, quote=True)
    _ctl = '<div class="swctl"><span class="lbl">Color by</span><div class="seg sm" role="group" aria-label="Map color"><button type="button" id="mWin" aria-pressed="true">Winner</button><button type="button" id="mSw" aria-pressed="false">Swing vs %s</button></div></div>' % _e(_prior['label'])
    _leg = ('<div class="swleg" id="swleg" hidden><h2>Swing vs %s</h2><div class="ramp" id="swramp"></div><div class="ticks"><span>Better for %s</span><span>No change</span><span>Better for %s</span></div>'
            '<p class="sw-note">Shading compares %s and %s with %s and %s in the %s race: the change in two-party share, in full color at <span id="swcap">5</span> points or more. Different candidates ran in each race, so this shows how much each party moved, not voters switching candidates. A dark outline marks a county that a different party won in %s.</p></div>') % (
        _e(_prior['label']), _e(b['name']), _e(a['name']), _e(a['name']), _e(b['name']), _e(_prior['a']), _e(_prior['b']), _e(_prior['label']), _e(_prior['short']))
else: _ctl = _leg = ''
t = t.replace('<!--SWING_CTL-->', _ctl).replace('<!--SWING_LEG-->', _leg)
left = re.findall(r'\{\{[A-Z_]+\}\}', t)
if left: raise SystemExit('unfilled template tokens: %s' % sorted(set(left)))
# </ inside a JSON string would end the script block
meta_js = json.dumps(meta).replace('</', '<\\/')
assert '/*DATA*/' in t and '/*LENS*/' in t and '/*META*/' in t
t = t.replace('/*DATA*/', D).replace('/*LENS*/', L).replace('/*META*/', meta_js)
pre = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
live = str(cfg.lens.get('card', 'tap')).lower() == 'live'   # tap: card changes on tap (desktop: hover previews); live: card follows the lens as you drag
open(cfg.out('index.html'), 'w').write(pre + t.replace('/*LIVE*/true', 'true' if live else 'false') + '</html>')
print('wrote index.html', round(os.path.getsize(cfg.out('index.html')) / 1e6, 2), 'MB; card:', 'live' if live else 'tap', '; lens starts at', start)
