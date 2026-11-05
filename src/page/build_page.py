"""Assemble elections/<id>/index.html from lens.template.html + rings.json + lens-fields.json + config text."""
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

D = open(cfg.out('rings.json')).read().strip()
L = open(cfg.out('lens-fields.json')).read().strip()
names = [c['name'] for c in json.loads(D)['counties']]
pops = {c['name']: c['pop'] for c in json.loads(D)['counties']}
start = cfg.lens.get('start_county')
if start not in names: start = max(pops, key=pops.get)
a, b = cfg.a, cfg.b
meta = dict(state=cfg.state['name'], people=cfg.state.get('people'), a=a['name'], b=b['name'], af=a.get('full', a['name']), bf=b.get('full', b['name']), start=start)
race = cfg.c['race']; year = (re.findall(r'\d{4}', race.get('date', '')) or [''])[-1]
src = cfg.c.get('text', {}).get('source') or ('Results: county returns as supplied for this build. Residents: Census Bureau 2019 county estimates.')
ra, rb = ramp(a), ramp(b)
tok = {
    'STATE': cfg.state['name'], 'OFFICE': race['office'], 'DATE': race.get('date', ''), 'RACE': (year + ' ' + race['office']).strip(),
    'UNIT': format(cfg.unit, ','), 'A': a['name'], 'B': b['name'], 'NCOUNTIES': str(len(names)), 'SOURCE': src,
    'A_MID_L': ra['mid_l'], 'A_DEEP_L': ra['deep_l'], 'A_MID_D': ra['mid_d'], 'A_DEEP_D': ra['deep_d'],
    'B_MID_L': rb['mid_l'], 'B_DEEP_L': rb['deep_l'], 'B_MID_D': rb['mid_d'], 'B_DEEP_D': rb['deep_d'],
}
t = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lens.template.html')).read()
for k, v in tok.items(): t = t.replace('{{%s}}' % k, html.escape(v, quote=True))
left = re.findall(r'\{\{[A-Z_]+\}\}', t)
if left: raise SystemExit('unfilled template tokens: %s' % sorted(set(left)))
# </ inside a JSON string would end the script block
meta_js = json.dumps(meta).replace('</', '<\\/')
assert '/*DATA*/' in t and '/*LENS*/' in t and '/*META*/' in t
t = t.replace('/*DATA*/', D).replace('/*LENS*/', L).replace('/*META*/', meta_js)
pre = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
open(cfg.out('index.html'), 'w').write(pre + t + '</html>')
print('wrote index.html', round(os.path.getsize(cfg.out('index.html')) / 1e6, 2), 'MB; lens starts at', start)
