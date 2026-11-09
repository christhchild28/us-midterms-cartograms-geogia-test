"""Regenerate the root index.html: a plain gallery of every elections/<id>/ that has a built page."""
import html, json, os, re, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = []; built = []
for d in sorted(os.listdir(os.path.join(ROOT, 'elections'))):
    cp = os.path.join(ROOT, 'elections', d, 'config.json')
    if not (os.path.exists(cp) and os.path.exists(os.path.join(ROOT, 'elections', d, 'index.html'))): continue
    c = json.load(open(cp)); r = c['race']; built.append((d, c['state']['name'])); yr = (re.findall(r'\d{4}', r.get('date', '')) or [''])[-1]
    gif = 'elections/%s/media/%s.gif' % (d, c['id'])
    png = gif[:-4] + '.png'
    if not os.path.exists(os.path.join(ROOT, gif)) and os.path.exists(os.path.join(ROOT, png)): gif = png
    has = os.path.exists(os.path.join(ROOT, gif))
    off = r['office']; office = 'Senate' if 'Senate' in off else 'Governor' if 'Governor' in off else 'House' if 'House' in off else off
    items.append(dict(id=d, state=c['state']['name'], office=office, gif=gif if has else '', unc=bool(r.get('uncalled')),
                      a=c['candidates']['a']['name'], b=c['candidates']['b']['name']))


# ---- gallery theme: decorative background layer, swappable (see src/gallery_themes/README.md) ----
def load_theme():
    name = None
    if '--theme' in sys.argv: name = sys.argv[sys.argv.index('--theme') + 1]
    else:
        cp_ = os.path.join(ROOT, 'gallery.config.json')
        if os.path.exists(cp_): name = json.load(open(cp_)).get('theme')
    name = name or 'plain'
    try:
        path = os.path.join(ROOT, 'src', 'gallery_themes', name.replace('-', '_') + '.py')
        spec = importlib.util.spec_from_file_location('gallery_theme', path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        out = mod.build(ROOT); out = {k: out.get(k, '') for k in ('css', 'top', 'bottom', 'band')}
    except Exception as e:
        print('theme %r failed (%s); using plain' % (name, e)); name, out = 'plain', {'css': '', 'top': '', 'bottom': '', 'band': ''}
    print('gallery theme:', name); return out
THEME = load_theme()

# ---- typography: Source Serif 4 headlines, Archivo body, IBM Plex Mono for labels only; metric-matched fallbacks limit layout shift ----
TYPE_HEAD = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400..800&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400..700&display=swap" rel="stylesheet">')
TYPE_CSS = """
@font-face{font-family:"Archivo Fallback";src:local("Arial"),local("Helvetica Neue");size-adjust:103.5%;ascent-override:84.8%;descent-override:20.3%;line-gap-override:0%}
@font-face{font-family:"Source Serif 4 Fallback";src:local("Times New Roman"),local("Times");size-adjust:109.2%;ascent-override:94.8%;descent-override:30.7%;line-gap-override:0%}
html{--f-body:"Archivo","Archivo Fallback","Helvetica Neue",Arial,sans-serif;--f-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,monospace;--f-head:"Source Serif 4","Source Serif 4 Fallback",Georgia,"Times New Roman",serif}
html body{font-family:var(--f-body);font-size:16px;line-height:1.55}
html :is(h1,h2,.bh,.gh,.card b,.lede){font-family:var(--f-head);font-optical-sizing:auto;font-weight:600;letter-spacing:-.015em}
html p.lede{font-weight:400;letter-spacing:-.005em}
html :is(h3:not(.gh),.steps h3,.row3 h3){font-family:var(--f-body);font-weight:700;font-size:18px;line-height:1.25}
html :is(.kick,.pill,.gh small,.ticks,.sw div,.phl){font-family:var(--f-mono);font-size:12px;letter-spacing:.08em}
html .pill{font-size:11px}
html :is(button,.chip,.skip,.seg span){font-family:var(--f-body)}
html :is(.by,footer,.chipm span,.mini,.brow b,.sum u){font-family:var(--f-body)}
html .by{font-size:14px;letter-spacing:0}html footer{font-size:13px;line-height:1.55}
html :is(.brow b,.mini b,.sum b,.bh,.gh small){font-variant-numeric:tabular-nums lining-nums}
html h1{font-size:clamp(42px,11vw,72px);line-height:1;letter-spacing:-.025em;font-weight:650}
html .lede{font-size:clamp(20px,5vw,26px);line-height:1.3;max-width:34ch}
html h2{font-size:clamp(26px,6.4vw,36px);line-height:1.1}
html .bh{font-size:clamp(36px,9.5vw,60px);line-height:1;letter-spacing:-.025em}
html .gh{font-size:26px;line-height:1.1}
html :is(.steps p,.fine p,.cap,.row3 p,.bsub,.keys,.brow,.hatchkey p,.sum){font-size:15px}
html .card b{font-size:21px;line-height:1.1}
html .card em{font-size:14px}
html :is(h2,.lede,.bh,.gh){text-wrap:balance}
html p{text-wrap:pretty}
"""
RAMPS = json.load(open(os.path.join(ROOT, 'src', 'common', 'ramps.json')))
BL, RD = RAMPS['blue'], RAMPS['red']

# ---- toy "Examplia": 5 counties, drawn three ways (land, lens, people) for the intro ----
def poly(pts, cls, style=''):
    return '<path class="%s"%s d="M%s Z"/>' % (cls, (' style="%s"' % style) if style else '', ' L'.join('%g %g' % p for p in pts))
def rect(x, y, w, h): return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
LAND = [  # (shape, cls)
    (rect(0, 0, 220, 55), 'r2'), (rect(0, 55, 80, 95), 'r1'), (rect(80, 55, 70, 95), 'r2'),
    ([(150, 55), (220, 55), (220, 95), (170, 95), (170, 150), (150, 150)], 'r1'), (rect(170, 95, 50, 55), 'b2')]
LENS = [
    (rect(0, 0, 220, 22), 'r2'), (rect(0, 22, 38, 128), 'r1'), (rect(38, 22, 34, 128), 'r2'),
    (rect(72, 22, 30, 128), 'r1'), (rect(102, 22, 118, 128), 'b2')]
def hexpath(cx, cy, r):
    import math
    return 'M' + ' L'.join('%.1f %.1f' % (cx + r * math.cos(math.radians(60 * k - 30)), cy + r * math.sin(math.radians(60 * k - 30))) for k in range(6)) + ' Z'
def hexes(cells, r, ox, oy, cls):
    import math
    w = math.sqrt(3) * r; out = []
    for (q, rw) in cells:
        out.append('<path class="%s" d="%s"/>' % (cls, hexpath(ox + w * (q + (0.5 if rw % 2 else 0)), oy + 1.5 * r * rw, r)))
    return ''.join(out)
R_ = 9.2
metro = [(q, rw) for rw in range(5) for q in range(6)]                                     # 30 hexes
reds = [(q, rw) for rw in range(2) for q in range(5)]                                      # 10 hexes: 2 + 3 + 3 + 2 residents-units
def svg(inner, label, vb='0 0 220 150'):
    return '<svg class="toy" viewBox="%s" role="img" aria-label="%s">%s</svg>' % (vb, html.escape(label), inner)
TOY_LAND = svg(''.join(poly(p, c) for p, c in LAND), 'A made-up state drawn by land: four red counties cover about nine tenths of the area and one small blue county in the corner covers the rest.')
TOY_LENS = svg(''.join(poly(p, c) for p, c in LENS), 'The same state with counties resized by population: the small blue county swells to nearly half the map and the red counties are squeezed.')
TOY_PEOPLE = svg(hexes(reds, R_, 16, 40, 'r1') + hexes(metro, R_, 96, 22, 'b2'), 'The same state with one hexagon per group of residents: ten red hexagons on the left and thirty blue hexagons on the right.')
# ---- real-map versions of the three intro figures (Nevada Governor 2026); falls back to the toy above if data is missing ----
def real_toys(src='nv-2026-governor'):
    import math
    d = json.load(open(os.path.join(ROOT, 'elections', src, 'warp-rings.json')))
    cs = d['counties']
    def cls(c):
        # same ramp as the map pages: neutral -> mid at 30pt margin -> deep at 60pt (t = margin/.6)
        t = max(-1., min(1., ((c['d'] - c['r']) / ((c['d'] + c['r']) or 1)) / .6)); a = abs(t); P = 'b' if t >= 0 else 'r'
        if a < .5: return 'fill:color-mix(in srgb,var(--%sm) %.1f%%,var(--n))' % (P, a / .5 * 100)
        return 'fill:color-mix(in srgb,var(--%sd) %.1f%%,var(--%sm))' % (P, (a - .5) / .5 * 100, P)
    def ring(c, k): v = c[k]; return [(v[i] / 1000., v[i + 1] / 1000.) for i in range(0, len(v) - 1, 2)]
    def fit(shapes, W=220, H=150, pad=6):
        xs = [x for sh in shapes for x, y in sh[0]]; ys = [y for sh in shapes for x, y in sh[0]]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); k = min((W - 2 * pad) / (x1 - x0), (H - 2 * pad) / (y1 - y0))
        ox = (W - k * (x1 - x0)) / 2 - k * x0; oy = (H - k * (y1 - y0)) / 2 - k * y0
        return k, ox, oy
    def shapes(key): return [(ring(c, key), cls(c)) for c in cs]
    def draw(sh, k, ox, oy): return ''.join(poly([(x * k + ox, y * k + oy) for x, y in pts], '', cl) for pts, cl in sh)
    def mix(c, t=.5):
        a, b = ring(c, 'real'), ring(c, 'warp'); return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for (x0, y0), (x1, y1) in zip(a, b)]
    land, lens = shapes('real'), [(mix(c), cls(c)) for c in cs]   # lens figure: halfway between real and population-warped, readable at small size
    cells = [((x, y), cls(c)) for c in cs for x, y in c['cells']]
    k1 = fit(land); k2 = fit(lens); k3 = fit([([p], c) for p, c in cells])
    r = d['s'] / math.sqrt(3) * k3[0] * .94
    hx = ''.join('<path style="%s" d="%s"/>' % (c, hexpath(x * k3[0] + k3[1], y * k3[0] + k3[2], r)) for (x, y), c in cells)
    lab = lambda t: 'Nevada drawn %s: ' % t
    return (svg(draw(land, *k1), lab('by land') + 'Clark County (Las Vegas) is a blue sliver in the south; the huge rural counties are mostly red.').replace('class="toy"', 'class="toy map"'),
            svg(draw(lens, *k2), lab('with counties resized by population') + 'Clark and Washoe swell and the rural counties shrink.').replace('class="toy"', 'class="toy map"'),
            svg(hx, lab('with one hexagon per block of residents') + 'most hexagons sit in blue Clark County in the south.').replace('class="toy"', 'class="toy map hexmap"'))
try: TOY_LAND, TOY_LENS, TOY_PEOPLE = real_toys()
except Exception as e: print('real-map intro figures unavailable (%s); using toy' % e)
HEX1 = svg(hexes([(0, 0)], 20, 24, 24, 'b1'), 'One hexagon', '0 0 48 48')
HEX3 = svg(hexes([(0, 0), (1, 0), (0.5, 1)] and [(0, 0), (1, 0)], 20, 24, 24, 'r1') + hexes([(0, 1)], 20, 24, 24, 'r1'), 'Three hexagons', '0 0 80 72')

OFFICES = ['Senate', 'Governor', 'House']
def card(it):
    thumb = ('<img src="%s" alt="" loading="lazy">' % it['gif']) if it['gif'] else PH
    return ('<a class="card" href="elections/%s/">%s<span class="meta"><span class="pill">%s</span>%s</span><b>%s</b>'
            '<em><span><i class="d"></i>%s</span><span><i class="r"></i>%s</span></em></a>') % (
        it['id'], thumb, it['office'], '<span class="pill unc">Uncalled</span>' if it['unc'] else '', html.escape(it['state']), html.escape(it['a']), html.escape(it['b']))
PH = svg(hexes([(q, rw) for rw in range(6) for q in range(4)], 14, 22, 26, 'ph'), 'Preview coming', '0 0 120 150').replace('class="toy"', 'class="toy phs"') + '<span class="phl">Preview coming</span>'
PH = '<div class="phbox">' + PH + '</div>'
groups = []
for o in OFFICES:
    its = sorted([i for i in items if i['office'] == o], key=lambda i: (i['state'], i['id']))
    if its: groups.append((o, its))
nstates = len(set(i['state'] for i in items if not i['state'].endswith(' City')))
chips = '<button type="button" class="chip" data-f="all" aria-pressed="true">All</button>' + ''.join('<button type="button" class="chip" data-f="%s" aria-pressed="false">%s</button>' % (o, o) for o, _ in groups)
gh = ''.join('<div class="grp" data-g="%s"><h3 class="gh">%s<small>%d race%s</small></h3><div class="grid">%s</div></div>' % (o, o, len(its), '' if len(its) == 1 else 's', ''.join(card(i) for i in its)) for o, its in groups)
BAND = ('<section class="band" id="elections">@@THEME_BAND@@<div class="wrap"><p class="kick">Now pick one</p><h2 class="bh">%d races, %d states</h2>'
        '<p class="bsub">Each card opens one race, drawn by land and by people. Everything in the guide above works the same way on all of them.</p></div>'
        '<div class="bar"><div class="wrap barin"><div class="chips" role="group" aria-label="Filter by office">%s</div><a class="up" href="#top" aria-label="Back to the guide">&uarr;</a></div></div>'
        '<div class="wrap" id="picks">%s</div></section>') % (len(items), nstates, chips, gh)
BAND = BAND.replace('@@THEME_BAND@@', THEME['band'])
BAND_JS = """<script>(function(){var cs=document.querySelectorAll('.chip'),gs=document.querySelectorAll('.grp'),pk=document.getElementById('picks');
cs.forEach(function(c){c.addEventListener('click',function(){var f=c.getAttribute('data-f');cs.forEach(function(x){x.setAttribute('aria-pressed',x===c?'true':'false')});
gs.forEach(function(g){g.hidden=!(f==='all'||g.getAttribute('data-g')===f)});pk.scrollIntoView({behavior:'smooth',block:'start'})})})})();</script>"""

page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Land vs people: how to read an election map</title>
<meta name="description" content="County election maps drawn two ways, by land and by people, and a short guide to reading them.">
<style>
:root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--ink3:#75746f;--hair:#e3e2de;--raised:#fff;--n:#e5e3dd;--bm:@BML@;--bd:@BDL@;--rm:@RML@;--rd:@RDL@;--soft:rgba(11,11,11,.05)}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--ink3:#a09f96;--hair:#343432;--raised:#262625;--n:#4a4a46;--bm:@BMD@;--bd:@BDD@;--rm:@RMD@;--rd:@RDD@;--soft:rgba(240,239,236,.07)}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-text-size-adjust:100%}
main{max-width:960px;margin:0 auto;padding:28px 16px 64px}
h1{font-size:clamp(32px,8vw,56px);line-height:1;letter-spacing:-.03em;margin:0 0 10px;font-weight:800;text-wrap:balance}
h2{font-size:clamp(21px,4.6vw,28px);line-height:1.15;letter-spacing:-.015em;margin:0 0 8px;font-weight:800}
p{margin:0 0 14px;color:var(--ink2);max-width:62ch}
.lede{font-size:clamp(17px,3.9vw,21px);color:var(--ink);max-width:48ch;margin-bottom:14px}
.by{font:500 13px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink3);letter-spacing:.02em;margin:0 0 18px}
.skip{display:inline-block;font-weight:700;color:var(--ink);border:1px solid var(--ink);border-radius:99px;padding:10px 16px;text-decoration:none;min-height:44px}
section.i{margin-top:44px;padding-top:28px;border-top:1px solid var(--hair)}
.kick{font:500 12px/1 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin:0 0 10px}
.b1{fill:var(--bm)}.b2{fill:var(--bd)}.r1{fill:var(--rm)}.r2{fill:var(--rd)}
svg.toy{display:block;width:100%;height:auto}
svg.toy path{stroke:var(--bg);stroke-width:2;stroke-linejoin:round}
svg.toy.map path{stroke-width:.7}svg.toy.hexmap path{stroke-width:.4}
.fig{background:var(--raised);border:1px solid var(--hair);border-radius:12px;padding:12px}
.row3{display:grid;gap:12px;margin:16px 0 8px}
@media(min-width:620px){.row3{grid-template-columns:repeat(3,1fr)}}
.row3 .fig{display:grid;grid-template-columns:42% 1fr;gap:12px;align-items:center}
@media(min-width:620px){.row3 .fig{grid-template-columns:1fr;gap:8px}}
.row3 h3{font-size:17px;margin:0 0 2px}.row3 p{font-size:14px;margin:0}
.cap{font-size:14px;color:var(--ink2)}
.bars{display:grid;gap:10px;margin:14px 0 6px}
.brow{display:grid;grid-template-columns:96px 1fr 48px;gap:8px;align-items:center;font-size:13px}
.brow span:first-child{color:var(--ink2)}.brow b{text-align:right;font:600 13px ui-monospace,monospace}
.trk{display:flex;height:11px;border-radius:6px;overflow:hidden;background:var(--rd)}.trk i{display:block;background:var(--bd)}
.keys{display:flex;gap:16px;font-size:13px;color:var(--ink2);margin:0 0 4px}.keys i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.ramp{height:14px;border-radius:7px;border:1px solid var(--hair);background:linear-gradient(90deg,var(--rd),var(--rm),var(--n),var(--bm),var(--bd))}
.ticks{display:flex;justify-content:space-between;font:500 12px ui-monospace,monospace;color:var(--ink3);margin-top:6px}
.sw{display:flex;gap:6px;margin:12px 0 4px}.sw div{flex:1;text-align:center;font:500 11px/1.3 ui-monospace,monospace;color:var(--ink3)}.sw i{display:block;height:28px;border-radius:6px;margin-bottom:5px;border:1px solid var(--hair)}
.hatchkey{display:flex;gap:14px;align-items:center;margin-top:12px;padding-top:12px;border-top:1px solid var(--hair)}.hatchkey svg{width:64px;flex:none}.hatchkey p{margin:0;font-size:14px}
.two{display:grid;gap:12px}@media(min-width:620px){.two{grid-template-columns:1fr 1fr}}
.hexrow{display:flex;gap:16px;align-items:center}.hexrow svg{width:72px;flex:none;box-sizing:border-box;padding:8px;background:#f1f0ec;border-radius:10px}
.hexrow svg path{stroke:#fff;stroke-width:1.6;stroke-linejoin:round}
.steps{list-style:none;margin:16px 0 0;padding:0;display:grid;gap:12px;counter-reset:s}
.steps li{counter-increment:s;display:grid;grid-template-columns:30px 1fr;gap:4px 12px;align-items:start}
.steps li::before{content:counter(s);width:30px;height:30px;border-radius:50%;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:700;font-size:14px}
.steps h3{font-size:17px;margin:3px 0 4px}.steps p{font-size:15px;margin:0 0 10px}
.mock{grid-column:2;background:var(--raised);border:1px solid var(--hair);border-radius:12px;padding:12px;pointer-events:none;user-select:none;max-width:420px}
.seg{display:inline-flex;border:1px solid var(--hair);border-radius:10px;padding:3px;gap:2px;background:var(--soft)}.seg span{padding:7px 14px;border-radius:7px;font-size:14px;color:var(--ink2)}.seg .on{background:var(--ink);color:var(--bg);font-weight:600}
.chipm{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}.chipm span{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--hair);border-radius:99px;padding:5px 11px;font:600 11.5px ui-monospace,monospace;color:var(--ink2)}.chipm .on{background:var(--ink);color:var(--bg);border-color:var(--ink)}.chipm i{width:9px;height:9px;border-radius:50%;display:inline-block}
.sum{display:flex;justify-content:space-between;gap:10px;align-items:center;font-size:12.5px;color:var(--ink3);margin-bottom:10px}.sum b{color:var(--ink)}.sum u{text-decoration:none;border:1px solid var(--hair);border-radius:99px;padding:5px 10px;font:600 10.5px ui-monospace,monospace;letter-spacing:.05em;text-transform:uppercase;color:var(--ink);flex:none}
.cardm h4{margin:0 0 2px;font-size:18px}.cardm small{color:var(--ink3);font-size:12.5px}
.mini{display:grid;grid-template-columns:78px 1fr 40px;gap:8px;align-items:center;font:500 12px ui-monospace,monospace;color:var(--ink3);margin-top:7px}.mini .t{height:8px;border-radius:4px;background:var(--soft);overflow:hidden}.mini .t i{display:block;height:100%}.mini b{color:var(--ink);text-align:right}
.fine{display:grid;gap:10px;margin-top:12px}.fine p{margin:0;font-size:14.5px}.fine b{color:var(--ink)}
.band{--band:#f6f6f3;background:var(--band);border-top:4px solid var(--ink);margin-top:48px;padding:28px 0 40px}
@media (prefers-color-scheme:dark){.band{--band:#121211}}
.wrap{max-width:960px;margin:0 auto;padding:0 16px}
.band>.wrap:first-child{padding-top:28px}
.bh{font-size:clamp(30px,8vw,48px);line-height:1.02;letter-spacing:-.03em;margin:0 0 8px}
.bsub{margin:0 0 18px;max-width:52ch}
.bar{position:sticky;top:0;z-index:20;background:var(--band);border-bottom:1px solid var(--hair);padding:8px 0}
.barin{display:flex;gap:8px;align-items:center}
.chips{flex:1;display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch}.chips::-webkit-scrollbar{display:none}
.chip{flex:none;min-height:40px;padding:0 12px;border-radius:99px;border:1px solid var(--hair);background:var(--raised);color:var(--ink2);font:600 14px system-ui,sans-serif;cursor:pointer}
.chip[aria-pressed=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.up{flex:none;width:40px;height:40px;border-radius:50%;border:1px solid var(--hair);background:var(--raised);color:var(--ink);display:grid;place-items:center;text-decoration:none;font-size:18px}
#picks{scroll-margin-top:64px;padding-top:6px}
.grp[hidden]{display:none}
.gh{display:flex;align-items:baseline;gap:10px;font-size:22px;letter-spacing:-.01em;margin:26px 0 0;padding-top:14px;border-top:1px solid var(--hair)}
.grp:first-child .gh{border-top:0;margin-top:14px;padding-top:0}
.gh small{font:500 12px ui-monospace,monospace;color:var(--ink3);letter-spacing:.04em;text-transform:uppercase}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}
@media(min-width:620px){.grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}
@media(min-width:900px){.grid{grid-template-columns:repeat(4,minmax(0,1fr))}}
.card{display:flex;flex-direction:column;gap:5px;background:var(--raised);border:1px solid var(--hair);border-radius:12px;padding:8px 8px 11px;color:inherit;text-decoration:none;min-width:0}
.card:hover,.card:focus-visible{border-color:var(--ink2)}
.card img,.phbox{width:100%;border-radius:8px;aspect-ratio:4/5;object-fit:cover;object-position:top;display:block}
.phbox{background:var(--soft);display:grid;place-items:center;position:relative;overflow:hidden}.phbox svg{width:70%;height:auto}.phbox path{fill:var(--n);stroke:var(--bg);stroke-width:2}
.phl{position:absolute;bottom:8px;left:0;right:0;text-align:center;font:500 11px ui-monospace,monospace;color:var(--ink3);letter-spacing:.04em;text-transform:uppercase}
.meta{display:flex;gap:5px;flex-wrap:wrap;margin-top:3px}
.pill{font:600 10.5px/1 ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);border:1px solid var(--hair);border-radius:99px;padding:4px 7px}
.pill.unc{color:var(--bg);background:var(--ink2);border-color:var(--ink2)}
.card b{font-size:17px;line-height:1.15;overflow-wrap:anywhere}
.card em{display:grid;gap:1px;font-style:normal;font-size:13px;color:var(--ink2)}.card em span{display:flex;align-items:center;gap:6px;min-width:0}
.card em i{width:8px;height:8px;border-radius:50%;flex:none}.card em .d{background:var(--bd)}.card em .r{background:var(--rd)}
main.after{padding-top:0;padding-bottom:40px}footer{margin-top:28px;padding-top:18px;border-top:1px solid var(--hair);font:500 13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink3)}
footer b{color:var(--ink)}
@@THEME_CSS@@
</style></head><body>@@THEME_TOP@@<main id="top">
<p class="kick">Election maps, explained</p>
<h1>Land vs people</h1>
<p class="lede">A county map shows where the acres are, not where the voters are. Here every race is drawn both ways, so you can see who really won.</p>
<p class="by">By Christian Theodore &middot; Media Intelligence Architect, Fovea</p>
<a class="skip" href="#elections">Jump to the elections &darr;</a>

<section class="i">
<p class="kick">The problem</p>
<h2>A mostly red map can still elect a blue winner</h2>
<p>Nevada's 2026 governor's race, counted four ways. The Democrat carried only two counties and 13% of the land, yet won the state, because almost nine in ten Nevadans live in those two counties.</p>
<div class="fig">
<div class="keys"><span><i style="background:var(--bd)"></i>Aaron Ford, Democrat</span><span><i style="background:var(--rd)"></i>Joe Lombardo, Republican</span></div>
<div class="bars">
<div class="brow"><span>Land area</span><span class="trk"><i style="width:13%"></i></span><b>13%</b></div>
<div class="brow"><span>Counties</span><span class="trk"><i style="width:12%"></i></span><b>12%</b></div>
<div class="brow"><span>Residents</span><span class="trk"><i style="width:89%"></i></span><b>89%</b></div>
<div class="brow"><span>Votes</span><span class="trk"><i style="width:54%"></i></span><b>54%</b></div>
</div>
<p class="cap" style="margin:6px 0 0">Share of Nevada that the winner's side held. Each page has this chart for its own race.</p>
</div>
</section>

<section class="i">
<p class="kick">Three ways to look</p>
<h2>One state, three maps</h2>
<p>Every page has a Land / Lens / People switch. Here is a made-up state with five counties, drawn all three ways.</p>
<div class="row3">
<div class="fig">@TOYLAND@<div><h3>Land</h3><p>The real county shapes. Big counties look important whether or not many people live there.</p></div></div>
<div class="fig">@TOYLENS@<div><h3>Lens</h3><p>Counties swell or shrink with population. Drag across the map to magnify the area you touch.</p></div></div>
<div class="fig">@TOYPEOPLE@<div><h3>People</h3><p>One hexagon for each block of residents, so every hexagon counts the same.</p></div></div>
</div>
<div class="keys" style="margin-top:4px"><span><i style="background:var(--bd)"></i>Democrat</span><span><i style="background:var(--rd)"></i>Republican</span></div>
<p class="cap">In the made-up state, Republicans win about 90% of the land but hold a quarter of the people. Democrats are one small corner on the land map and three quarters of the state on the people map.</p>
</section>

<section class="i">
<p class="kick">Reading the hexagons</p>
<h2>Count the hexagons, not the acres</h2>
<div class="two">
<div class="fig hexrow">@HEX1@<p style="margin:0"><b style="color:var(--ink)">One hexagon is a fixed number of residents</b>, often 10,000. Small states use fewer, big states more, so each page states its own size.</p></div>
<div class="fig hexrow">@HEX3@<p style="margin:0"><b style="color:var(--ink)">More residents, more hexagons.</b> A county of 30,000 people gets three. A county of 3 million gets 300 and becomes a big block of its winner\'s color.</p></div>
</div>
<p class="cap" style="margin-top:12px">Hexagons follow the stretched county shapes from the Lens view, so the People map still looks like its state.</p>
</section>

<section class="i">
<p class="kick">Reading the colors</p>
<h2>Color shows who won, and by how much</h2>
<div class="fig">
<h3 style="margin:0 0 8px;font-size:16px">Winner: county margin</h3>
<div class="ramp"></div>
<div class="ticks"><span>Republican +60</span><span>Even</span><span>Democrat +60</span></div>
<div class="sw"><div><i style="background:var(--rd)"></i>Rep.<br>+60</div><div><i style="background:var(--rm)"></i>Rep.<br>+30</div><div><i style="background:var(--n)"></i>Even</div><div><i style="background:var(--bm)"></i>Dem.<br>+30</div><div><i style="background:var(--bd)"></i>Dem.<br>+60</div></div>
<p class="cap" style="margin:10px 0 0">Blue is the Democratic candidate and red is the Republican. Gray is a toss-up. The stronger the color, the bigger the winner's lead in that county. Each page's legend names the two candidates.</p>
</div>
<div class="fig" style="margin-top:12px">
<h3 style="margin:0 0 8px;font-size:16px">Swing: change since the last comparable race</h3>
<div class="ramp"></div>
<div class="ticks"><span>Toward Republican</span><span>No change</span><span>Toward Democrat</span></div>
<p class="cap" style="margin:10px 0 0">Switch "Color by" from Winner to Swing to see where each side gained or lost ground compared with the earlier race named on the page. A county can lean Republican and still swing toward the Democrat.</p>
<div class="hatchkey"><svg viewBox="0 0 56 40" aria-hidden="true"><defs><pattern id="ih" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)"><rect width="7" height="7" fill="none"/><rect width="3" height="7" fill="rgba(255,255,255,.95)"/></pattern></defs><rect x="2" y="2" width="52" height="36" rx="6" class="b2"/><rect x="2" y="2" width="52" height="36" rx="6" fill="url(#ih)" stroke="var(--ink3)" stroke-width="1"/></svg><p><b style="color:var(--ink)">Diagonal hatching means the county flipped.</b> A different party won it than in the earlier race. The fill color is still this race's winner, and the card names the party that held it before.</p></div>
</div>
</section>

<section class="i">
<p class="kick">Using the maps</p>
<h2>Four things to try</h2>
<ol class="steps">
<li><div><h3>Switch the view</h3><p>Start in Land, then flip to People and watch the shapes morph.</p></div><div class="mock"><span class="seg"><span>Land</span><span>Lens</span><span class="on">People</span></span></div></li>
<li><div><h3>Tap a county</h3><p>A card shows the winner, the margin, its share of the state's land and of its people. On phones it slides up from the bottom.</p></div><div class="mock cardm"><h4>Essex</h4><small>Booker +64</small><div class="mini"><span>Land area</span><span class="t"><i style="width:2%;background:var(--bd)"></i></span><b>1.7%</b></div><div class="mini"><span>People</span><span class="t"><i style="width:9.4%;background:var(--bd)"></i></span><b>9.4%</b></div></div></li>
<li><div><h3>Tap several counties to compare</h3><p>In Land view, each county you tap opens up and gets a chip. Tap a chip to jump between them. The line under the chips adds them up. <b style="color:var(--ink)">Revert all</b> puts everything back.</p></div><div class="mock"><div class="chipm"><span><i style="background:var(--bm)"></i>Bergen</span><span class="on"><i style="background:var(--bm)"></i>Middlesex</span><span><i style="background:var(--rm)"></i>Ocean</span></div><div class="sum" style="margin:0"><span>3 counties hold <b>16.9%</b> of the land and <b>26.5%</b> of the people</span><u>Revert all</u></div></div></li>
<li><div><h3>Change what the colors mean</h3><p>Winner shows who won. Swing shows who gained ground.</p></div><div class="mock"><span class="seg"><span class="on">Winner</span><span>Swing vs 2020 Senate</span></span></div></li>
</ol>
</section>

<section class="i">
<p class="kick">Good to know</p>
<h2>Fine print</h2>
<div class="fine">
<p><b>Counts are unofficial.</b> Results come from the Associated Press via NBC News, and can change until counties certify them.</p>
<p><b>Shares are two-party.</b> Each map compares the top two candidates. Independents and write-ins are left out.</p>
<p><b>The People map bends the borders.</b> Each page reports how many real county borders survive. States with one giant city lose more, and evenly spread states like New Jersey keep almost all.</p>
<p><b>Residents are Census estimates</b> for July 1, 2025, not voter counts.</p>
</div>
</section>

</main>
@@BAND@@
<main class="after"><footer><b>Christian Theodore</b> &middot; Media Intelligence Architect, Fovea<br>County results: AP via NBC News. Population: U.S. Census Bureau. Earlier-race comparisons: official county returns.</footer></main>
@@JS@@
@@THEME_BOTTOM@@
</body></html>"""
for k, v in (('@BML@', BL['mid_l']), ('@BDL@', BL['deep_l']), ('@RML@', RD['mid_l']), ('@RDL@', RD['deep_l']), ('@BMD@', BL['mid_d']), ('@BDD@', BL['deep_d']), ('@RMD@', RD['mid_d']), ('@RDD@', RD['deep_d']),
             ('@TOYLAND@', TOY_LAND), ('@TOYLENS@', TOY_LENS), ('@TOYPEOPLE@', TOY_PEOPLE), ('@HEX1@', HEX1), ('@HEX3@', HEX3)):
    page = page.replace(k, v)
page = page.replace("@@BAND@@", BAND).replace("@@JS@@", BAND_JS).replace("@@THEME_CSS@@", THEME["css"]).replace("@@THEME_TOP@@", THEME["top"]).replace("@@THEME_BOTTOM@@", THEME["bottom"])
page = page.replace('</head>', TYPE_HEAD + '<style>' + TYPE_CSS + '</style></head>', 1)
open(os.path.join(ROOT, 'index.html'), 'w').write(page)
print('wrote root index.html with', len(items), 'election(s)')

OLD_NAV = '<nav class="pgnav" aria-label="Elections"><a class="back" href="../../">&larr; All elections</a><!--next--><!--/next--></nav>'
NEW_NAV = '<nav class="pgnav" aria-label="Elections"><span class="pgl"><button type="button" class="back pgb" hidden>&larr; Back</button><a class="back" href="../../">All elections</a></span><!--next--><!--/next--></nav><script>(function(){try{var b=document.querySelector(".pgb"),r=document.referrer;if(b&&history.length>1&&r&&new URL(r).origin===location.origin){b.hidden=false;b.addEventListener("click",function(){history.back()})}}catch(e){}})()</script>'
NAV_CSS = '.pgl { display: flex; flex-wrap: wrap; align-items: center; column-gap: 8px; }\n.pgnav .pgl + .back { margin-left: auto; text-align: right; }\nbutton.back { background: none; border: 0; cursor: pointer; -webkit-appearance: none; appearance: none; }\n.pgb[hidden] { display: none; }\n.pgb[hidden] + a::before { content: "\\2190\\00a0"; }\n'
# Next-election link on each page (wraps from last to first, same order as the gallery).
for i, (d, _) in enumerate(built):
    nd, nname = built[(i + 1) % len(built)]
    if nd == d: link = ''
    else: link = '<a class="back" href="../%s/" aria-label="Next election: %s">Next: %s &rarr;</a>' % (nd, html.escape(nname), html.escape(nname))
    p = os.path.join(ROOT, 'elections', d, 'index.html'); t = t0 = open(p).read()
    if 'class="pgl"' not in t:   # upgrade older pages: add the history Back button next to "All elections"
        t = re.sub(r'<nav class="pgnav" aria-label="Elections"><a class="back" href="\.\./\.\./">&larr; All elections</a>(<!--next-->.*?<!--/next-->)</nav>', lambda m: NEW_NAV.replace('<!--next--><!--/next-->', m.group(1)), t, count=1, flags=re.S).replace('.back:hover { color: var(--ink); }', NAV_CSS + '.back:hover { color: var(--ink); }', 1)
    t2 = re.sub(r'<!--next-->.*?<!--/next-->', lambda m: '<!--next-->' + link + '<!--/next-->', t, count=1, flags=re.S)
    if t2 != t0: open(p, 'w').write(t2)
print('linked next-election on', len(built), 'page(s)')
