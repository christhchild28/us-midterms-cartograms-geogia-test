"""Nevada's county outlines morph from land shapes to population shapes as the intro scrolls.
Source geometry: elections/<SOURCE>/warp-rings.json ('real' = land outline, 'warp' = population-warped outline, 200 points each).
Also adds a red/blue glow behind the headline and a dense hexagon-mosaic texture (very light grout, faint tile tones) behind the Elections band."""
import json, math, os, random

SOURCE = 'nv-2026-governor'
SHAPE_OPACITY = .6        # strength of the hero shape (before it fades after the headline)
HEX_R, HEX_COLS, HEX_ROWS, HEX_SEED = 9, 20, 24, 9   # band mosaic: hex radius and repeating tile size (cols x even rows)
GROUT_OPACITY, GROUT_WIDTH = .022, .7                  # grout lines between tiles
BAND_LIGHT = '#f6f6f3'                                 # light-mode band background (was #ecebe4, then #f1f0eb)
TONES = True                                           # faint per-tile tone shifts (+ a few blue/red tiles)

def _hexpath(cx, cy, r):
    return 'M' + ' L'.join('%.1f %.1f' % (cx + r * math.cos(math.radians(60 * k - 30)), cy + r * math.sin(math.radians(60 * k - 30))) for k in range(6)) + ' Z'

def _band_svg():
    r = HEX_R; w = math.sqrt(3) * r; W, H = w * HEX_COLS, 1.5 * r * HEX_ROWS; rnd = random.Random(HEX_SEED); body = ''
    for rw in range(HEX_ROWS):
        for q in range(HEX_COLS):
            t = rnd.random(); cls = 't3' if t < .06 else 't2' if t < .21 else 't1' if t < .41 else 'tb' if t < .435 else 'tr' if t < .46 else ''
            cx = q * w + (w / 2 if rw % 2 else 0); cy = 1.5 * r * rw
            for dx in (-W, 0, W):
                for dy in (-H, 0, H):
                    x, y = cx + dx, cy + dy
                    if x + w / 2 < 0 or x - w / 2 > W or y + r < 0 or y - r > H: continue      # only copies that touch the tile (seamless wrap)
                    body += '<use href="#hxm" x="%.1f" y="%.1f"%s/>' % (x, y, (' class="%s"' % cls) if cls else '')
    hexd = 'M' + ' L'.join('%.2f %.2f' % ((r - .3) * math.cos(math.radians(60 * k - 30)), (r - .3) * math.sin(math.radians(60 * k - 30))) for k in range(6)) + ' Z'
    return ('<svg class="hexbg" aria-hidden="true" focusable="false"><defs><path id="hxm" d="%s"/><pattern id="hxp" patternUnits="userSpaceOnUse" width="%.2f" height="%.2f">%s</pattern></defs>'
            '<rect width="100%%" height="100%%" fill="url(#hxp)"/></svg>') % (hexd, W, H, body)

def build(root):
    rings = json.load(open(os.path.join(root, 'elections', SOURCE, 'warp-rings.json')))['counties']
    xs, ys = [], []
    for c in rings:
        for k in ('real', 'warp'):
            xs += c[k][0::2]; ys += c[k][1::2]
    x0, x1, y0, y1 = min(xs) / 1000, max(xs) / 1000, min(ys) / 1000, max(ys) / 1000
    pad = .08 * max(x1 - x0, y1 - y0)
    vb = '%.3f %.3f %.3f %.3f' % (x0 - pad, y0 - pad, x1 - x0 + 2 * pad, y1 - y0 + 2 * pad)
    paths = ''; pairs = []
    for c in rings:
        m = (c['d'] - c['r']) / max(1, c['d'] + c['r'])
        paths += '<path class="%s" style="fill-opacity:%.2f"/>' % ('tb' if m > 0 else 'tr', .10 + .36 * min(abs(m), .6) / .6)
        pairs.append([c['real'], c['warp']])
    svg = '<svg viewBox="%s" preserveAspectRatio="xMaxYMid meet" aria-hidden="true" focusable="false">%s</svg>' % (vb, paths)
    css = """
:root{--gb:rgba(40,100,200,.15);--gr:rgba(190,50,50,.12)}
@media (prefers-color-scheme:dark){:root{--gb:rgba(90,150,240,.17);--gr:rgba(240,100,100,.12)}}
body{position:relative}
.bg{position:fixed;top:0;left:0;right:0;height:100vh;height:100lvh;overflow:hidden;pointer-events:none;z-index:0;-webkit-mask-image:linear-gradient(#000 62%,transparent);mask-image:linear-gradient(#000 62%,transparent)}
.bg::before{content:"";position:absolute;inset:0;background:radial-gradient(62% 72% at 3% 4%,var(--gr),transparent 72%),radial-gradient(62% 72% at 97% 9%,var(--gb),transparent 72%)}
.bg svg{position:absolute;top:5vh;right:-12%;height:74vh;width:auto;max-width:none;opacity:calc(@SO@*var(--fade,1))}
.bg path{stroke:var(--ink);stroke-opacity:.3;stroke-width:1;vector-effect:non-scaling-stroke;stroke-linejoin:round}
.bg path.tb{fill:var(--bd)}.bg path.tr{fill:var(--rd)}
main{position:relative;z-index:1}
.band{position:relative;isolation:isolate}
.hexbg{position:absolute;inset:0;width:100%;height:100%;z-index:-1;pointer-events:none}
.hexbg use{fill:none;stroke:var(--ink);stroke-opacity:@GO@;stroke-width:@GW@}
.hexbg use.t1,.hexbg use.t2,.hexbg use.t3{fill:var(--tile)}
.hexbg use.t1{fill-opacity:@L1@}.hexbg use.t2{fill-opacity:@L2@}.hexbg use.t3{fill-opacity:@L3@}
.band{--tile:#fff}
@media (prefers-color-scheme:light){.band{--band:@BANDL@}}
@media (prefers-color-scheme:dark){.band{--tile:var(--ink)}.hexbg use.t1{fill-opacity:@D1@}.hexbg use.t2{fill-opacity:@D2@}.hexbg use.t3{fill-opacity:@D3@}}
.hexbg use.tb{fill:var(--bd);fill-opacity:@TB@}.hexbg use.tr{fill:var(--rd);fill-opacity:@TR@}
.bar{background:color-mix(in srgb,var(--band) 84%,transparent)!important;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px)}
.band>.wrap{position:relative}
"""
    tn = 1 if TONES else 0
    for k, v in (("@SO@", str(SHAPE_OPACITY)), ("@GO@", str(GROUT_OPACITY)), ("@GW@", str(GROUT_WIDTH)), ("@BANDL@", BAND_LIGHT), ("@L1@", str(.35 * tn)), ("@L2@", str(.6 * tn)), ("@L3@", str(.9 * tn)), ("@D1@", str(.02 * tn)), ("@D2@", str(.04 * tn)), ("@D3@", str(.065 * tn)), ("@TB@", str(.09 * tn)), ("@TR@", str(.08 * tn))): css = css.replace(k, v)
    top = '<div class="bg" aria-hidden="true">%s</div>' % svg
    js = """<script>/* gallery theme: nevada-morph. Land outlines -> population-warped outlines as the intro scrolls; still half-way pose for reduced motion. */
(function(){var D=@DATA@,bg=document.querySelector('.bg'),ps=bg&&bg.querySelectorAll('path'),cur=-1,tk=false;if(!ps||!ps.length)return;
function draw(t){t=Math.max(0,Math.min(1,t));if(Math.abs(t-cur)<.002)return;cur=t;var e=t*t*(3-2*t);
for(var i=0;i<D.length;i++){var a=D[i][0],b=D[i][1],d='M';for(var k=0;k<a.length;k+=2){d+=(k?'L':'')+((a[k]+(b[k]-a[k])*e)/1000).toFixed(3)+','+((a[k+1]+(b[k+1]-a[k+1])*e)/1000).toFixed(3)}ps[i].setAttribute('d',d+'Z')}}
function upd(){tk=false;var s=document.querySelectorAll('section.i')[1],end=s?(s.offsetTop+s.offsetHeight*.6-innerHeight*.5):1400,y=window.pageYOffset||0;
bg.style.setProperty('--fade',(1-.72*Math.min(1,y/420)).toFixed(3));draw(y/Math.max(600,end))}
var rm=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
if(rm){bg.style.setProperty('--fade','.45');draw(.55)}else{upd();addEventListener('scroll',function(){if(!tk){tk=true;requestAnimationFrame(upd)}},{passive:true});addEventListener('resize',function(){cur=-1;upd()})}})();
</script>""".replace("@DATA@", json.dumps(pairs, separators=(',', ':')))
    return {'css': css, 'top': top, 'bottom': js, 'band': _band_svg()}
