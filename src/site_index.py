"""Regenerate the root index.html: a plain gallery of every elections/<id>/ that has a built page."""
import html, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cards = []; built = []
for d in sorted(os.listdir(os.path.join(ROOT, 'elections'))):
    cp = os.path.join(ROOT, 'elections', d, 'config.json')
    if not (os.path.exists(cp) and os.path.exists(os.path.join(ROOT, 'elections', d, 'index.html'))): continue
    c = json.load(open(cp)); r = c['race']; built.append((d, c['state']['name'])); yr = (re.findall(r'\d{4}', r.get('date', '')) or [''])[-1]
    gif = 'elections/%s/media/%s.gif' % (d, c['id'])
    png = gif[:-4] + '.png'
    if not os.path.exists(os.path.join(ROOT, gif)) and os.path.exists(os.path.join(ROOT, png)): gif = png
    img = '<img src="%s" alt="" loading="lazy">' % gif if os.path.exists(os.path.join(ROOT, gif)) else ''
    cards.append('<a class="card" href="elections/%s/%s">%s<b>%s</b><span>%s</span><em>%s vs %s</em></a>' % (
        d, '', img, html.escape(c['state']['name']), html.escape((yr + ' ' + r['office']).strip()),
        html.escape(c['candidates']['a']['name']), html.escape(c['candidates']['b']['name'])))

RAMPS = json.load(open(os.path.join(ROOT, 'src', 'common', 'ramps.json')))
BL, RD = RAMPS['blue'], RAMPS['red']

# ---- toy "Examplia": 5 counties, drawn three ways (land, lens, people) for the intro ----
def poly(pts, cls, label=''):
    return '<path class="%s" d="M%s Z"/>' % (cls, ' L'.join('%g %g' % p for p in pts))
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
HEX1 = svg(hexes([(0, 0)], 20, 24, 24, 'b1'), 'One hexagon', '0 0 48 48')
HEX3 = svg(hexes([(0, 0), (1, 0), (0.5, 1)] and [(0, 0), (1, 0)], 20, 24, 24, 'r1') + hexes([(0, 1)], 20, 24, 24, 'r1'), 'Three hexagons', '0 0 80 72')

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
.hexrow{display:flex;gap:16px;align-items:center}.hexrow svg{width:64px;flex:none}
.hexrow svg path{stroke:var(--bg);stroke-width:2}
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
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;margin-top:16px}
.card{display:flex;flex-direction:column;gap:4px;background:var(--raised);border:1px solid var(--hair);border-radius:12px;padding:12px;color:inherit;text-decoration:none}
.card:hover{border-color:var(--ink2)}.card img{width:100%;border-radius:8px;aspect-ratio:4/5;object-fit:cover;object-position:top}
.card b{font-size:20px}.card span,.card em{color:var(--ink2);font-style:normal;font-size:14px}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--hair);font:500 13px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--ink3)}
footer b{color:var(--ink)}
</style></head><body><main>
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

<section class="i" id="elections">
<p class="kick">Now pick one</p>
<h2>The elections</h2>
<p>Each card opens one race. Everything above works the same way on all of them.</p>
<div class="grid">@@CARDS@@</div>
</section>
<footer><b>Christian Theodore</b> &middot; Media Intelligence Architect, Fovea<br>County results: AP via NBC News. Population: U.S. Census Bureau. Earlier-race comparisons: official county returns.</footer>
</main></body></html>"""
for k, v in (('@BML@', BL['mid_l']), ('@BDL@', BL['deep_l']), ('@RML@', RD['mid_l']), ('@RDL@', RD['deep_l']), ('@BMD@', BL['mid_d']), ('@BDD@', BL['deep_d']), ('@RMD@', RD['mid_d']), ('@RDD@', RD['deep_d']),
             ('@TOYLAND@', TOY_LAND), ('@TOYLENS@', TOY_LENS), ('@TOYPEOPLE@', TOY_PEOPLE), ('@HEX1@', HEX1), ('@HEX3@', HEX3)):
    page = page.replace(k, v)
page = page.replace("@@CARDS@@", ''.join(cards))
open(os.path.join(ROOT, 'index.html'), 'w').write(page)
print('wrote root index.html with', len(cards), 'election(s)')

# Next-election link on each page (wraps from last to first, same order as the gallery).
for i, (d, _) in enumerate(built):
    nd, nname = built[(i + 1) % len(built)]
    if nd == d: link = ''
    else: link = '<a class="back" href="../%s/" aria-label="Next election: %s">Next: %s &rarr;</a>' % (nd, html.escape(nname), html.escape(nname))
    p = os.path.join(ROOT, 'elections', d, 'index.html'); t = open(p).read()
    t2 = re.sub(r'<!--next-->.*?<!--/next-->', lambda m: '<!--next-->' + link + '<!--/next-->', t, count=1, flags=re.S)
    if t2 != t: open(p, 'w').write(t2)
print('linked next-election on', len(built), 'page(s)')
