"""Regenerate the root index.html: a plain gallery of every elections/<id>/ that has a built page."""
import html, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cards = []; built = []
for d in sorted(os.listdir(os.path.join(ROOT, 'elections'))):
    cp = os.path.join(ROOT, 'elections', d, 'config.json')
    if not (os.path.exists(cp) and os.path.exists(os.path.join(ROOT, 'elections', d, 'index.html'))): continue
    c = json.load(open(cp)); r = c['race']; built.append((d, c['state']['name'])); yr = (re.findall(r'\d{4}', r.get('date', '')) or [''])[-1]
    gif = 'elections/%s/media/%s.gif' % (d, c['id'])
    img = '<img src="%s" alt="" loading="lazy">' % gif if os.path.exists(os.path.join(ROOT, gif)) else ''
    cards.append('<a class="card" href="elections/%s/%s">%s<b>%s</b><span>%s</span><em>%s vs %s</em></a>' % (
        d, '', img, html.escape(c['state']['name']), html.escape((yr + ' ' + r['office']).strip()),
        html.escape(c['candidates']['a']['name']), html.escape(c['candidates']['b']['name'])))
page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>County cartograms: land vs people</title>
<style>
:root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--hair:#e3e2de;--raised:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--hair:#343432;--raised:#262625}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:960px;margin:0 auto;padding:32px 16px 56px}
h1{font-size:clamp(28px,6vw,44px);line-height:1.05;letter-spacing:-.02em;margin:0 0 8px}
p{color:var(--ink2);margin:0 0 24px;max-width:60ch}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.card{display:flex;flex-direction:column;gap:4px;background:var(--raised);border:1px solid var(--hair);border-radius:12px;padding:12px;color:inherit;text-decoration:none}
.card:hover{border-color:var(--ink2)}.card img{width:100%;border-radius:8px;aspect-ratio:4/5;object-fit:cover;object-position:top}
.card b{font-size:20px}.card span,.card em{color:var(--ink2);font-style:normal;font-size:14px}
</style></head><body><main><h1>Land vs people</h1>
<p>County results drawn two ways: by land area, and by the number of people who live there. Pick an election.</p>
<div class="grid">@@CARDS@@</div></main></body></html>""".replace("@@CARDS@@", ''.join(cards))
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
