"""Corrections pipeline. Source of truth: errata/errata.json.
  python3 src/corrections.py build   writes errata/index.html, errata/feed.xml, ERRATA.md and the footer link on every page
  python3 src/corrections.py check   fails on a page note with no entry, or an entry naming a missing page
"""
import json, os, re, sys, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = json.load(open(os.path.join(ROOT, 'errata', 'errata.json')))
ENT = E['entries']; SITE = E['site']; REPO = E['repo']
SEV = {'S1': 'Wrong headline or winner', 'S2': 'Missing or misleading', 'S3': 'Cosmetic'}
ST = {'open': 'Open', 'disclosed': 'Disclosed on page', 'corrected': 'Corrected'}
esc = html.escape
ROS = json.load(open(os.path.join(ROOT, 'errata', 'rosters.json')))
FACTS = json.load(open(os.path.join(ROOT, 'errata', 'facts.json')))['races']
races = sorted(d for d in os.listdir(os.path.join(ROOT, 'elections')) if os.path.exists(os.path.join(ROOT, 'elections', d, 'index.html')))

def check():
    bad = []
    for e in ENT:
        for r in e['races']:
            if r not in races: bad.append('%s names missing page %s' % (e['id'], r))
    for r in races:
        cp = os.path.join(ROOT, 'elections', r, 'config.json')
        if os.path.exists(cp) and json.load(open(cp)).get('text', {}).get('notice') and not any(r in e['races'] for e in ENT):
            bad.append('%s has a page note but no errata entry' % r)
    for r, q in ROS['races'].items():
        if r not in races: bad.append('rosters.json names missing page ' + r)
        elif (q.get('n_omitted', len(q.get('omitted') or [])) > 0) and not any(r in e['races'] for e in ENT): bad.append(r + ' omits candidates but has no errata entry')
    ids = [e['id'] for e in ENT]
    if len(ids) != len(set(ids)): bad.append('duplicate entry id')
    return bad

def contact():
    return E['contact_email'] if E.get('email_live') and E.get('contact_email') else None

def report_url(r=''):
    return REPO + '/issues/new?template=correction.yml' + ('&race=' + r if r else '')

CSS = ':root{color-scheme:light dark;--bg:#fff;--ink:#16181d;--ink2:#555b66;--line:#d9dce2}@media(prefers-color-scheme:dark){:root{--bg:#111318;--ink:#eceef2;--ink2:#a3a9b5;--line:#2c313a}}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}main{max-width:68ch;margin:0 auto;padding:20px 16px 48px}h1{font-size:26px;line-height:1.2;margin:8px 0 4px}h2{font-size:18px;margin:0 0 6px}a{color:inherit}.sub{color:var(--ink2);margin:0 0 20px}.e{border:1px solid var(--line);border-left:4px solid var(--ink2);border-radius:8px;padding:12px 14px;margin:0 0 14px}.m{font-size:13px;color:var(--ink2);margin:0 0 8px}.e p{margin:0 0 8px}.btn{display:inline-block;padding:11px 14px;border:1px solid var(--ink);border-radius:8px;text-decoration:none;font-weight:600;min-height:44px}'

def page():
    out = []
    for e in sorted(ENT, key=lambda x: x['id'], reverse=True):
        links = ' · '.join('<a href="../elections/%s/">%s</a>' % (r, esc(r)) for r in e['races'])
        out.append('<article class="e" id="%s"><p class="m">%s · %s · %s (%s)</p><h2>%s</h2><p><b>What was wrong.</b> %s</p><p><b>What we did.</b> %s</p><p><b>How we will catch it.</b> %s</p><p class="m">Pages: %s · Found by: %s</p></article>' % (
            e['id'], esc(e['id']), esc(e['date']), esc(ST[e['status']]), esc(e['severity']), esc(e['title']), esc(e['wrong']), esc(e['done']), esc(e['prevent']), links, esc(e['found_by'])))
    c = contact()
    where = '<a class="btn" href="%s">Report an error</a>' % esc(report_url()) + ('<p class="m">Or write to <a href="mailto:%s">%s</a>.</p>' % (c, c) if c else '')
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Corrections</title><link rel="alternate" type="application/atom+xml" title="Corrections" href="feed.xml"><style>%s</style></head><body><main><p><a href="../">&larr; All elections</a></p><h1>Corrections</h1><p class="sub">We list every error we find in our own pages, what we did, and how we will catch the next one. Entries are never deleted. <a href="feed.xml">Feed</a></p>%s%s<p class="m">Policy: severity levels and response times are in docs/CORRECTIONS.md in the repository.</p></main></body></html>' % (CSS, where, ''.join(out))

def feed():
    ent = ''.join('<entry><id>tag:fovea,2026:errata:%s</id><title>%s</title><updated>%sT12:00:00Z</updated><link href="%serrata/#%s"/><summary>%s</summary></entry>' % (
        e['id'], esc(e['id'] + ' ' + e['title']), e['date'], SITE, e['id'], esc('%s. %s' % (ST[e['status']], e['wrong']))) for e in sorted(ENT, key=lambda x: x['id'], reverse=True))
    upd = max(e['date'] for e in ENT)
    return '<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom"><id>tag:fovea,2026:errata</id><title>Corrections</title><updated>%sT12:00:00Z</updated><link rel="self" href="%serrata/feed.xml"/><link href="%serrata/"/>%s</feed>\n' % (upd, SITE, SITE, ent)

def md():
    s = '# Corrections\n\nGenerated from `errata/errata.json`. Do not edit by hand.\n\n'
    for e in sorted(ENT, key=lambda x: x['id'], reverse=True):
        s += '## %s %s\n\n%s · %s (%s) · pages: %s\n\n**Wrong.** %s\n\n**Done.** %s\n\n**Catch.** %s\n\n' % (e['id'], e['title'], e['date'], ST[e['status']], e['severity'], ', '.join(e['races']), e['wrong'], e['done'], e['prevent'])
    return s

def inject():
    n = 0
    for r in races:
        p = os.path.join(ROOT, 'elections', r, 'index.html'); t = t0 = open(p).read()
        cnt = sum(r in e['races'] for e in ENT)
        c = contact()
        blk = '<!--corr--><p class="corr"><a style="display:inline-block;padding:10px 0;color:inherit" href="%s">Report an error</a> · <a style="display:inline-block;padding:10px 0;color:inherit" href="../../errata/">Corrections%s</a>%s</p><!--/corr-->' % (
            esc(report_url(r)), (' (%d for this page)' % cnt) if cnt else '', (' · <a style="display:inline-block;padding:10px 0;color:inherit" href="mailto:%s">%s</a>' % (c, c)) if c else '')
        if '<!--corr-->' in t: t = re.sub(r'<!--corr-->.*?<!--/corr-->', lambda m: blk, t, count=1, flags=re.S)
        else: t = t.replace('<p>', '<p>', 0); t = re.sub(r'(<div class="foot">.*?)(</div>)', lambda m: m.group(1) + blk + m.group(2), t, count=1, flags=re.S)
        if t != t0: open(p, 'w').write(t); n += 1
    return n



FN_CSS = ('<style id="fn-css">.fnote{border:1px solid;border-left-width:4px;border-color:color-mix(in srgb,currentColor 35%,transparent);border-radius:8px;margin:12px 0 0;max-width:62ch;font-size:14px;line-height:1.5}'
  '.fnote>summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:44px;padding:0 12px;cursor:pointer;-webkit-tap-highlight-color:transparent}'
  '.fnote>summary::-webkit-details-marker{display:none}.fnote>summary:focus-visible{outline:2px solid currentColor;outline-offset:2px;border-radius:6px}'
  '.fnote .fn-b{padding:0 12px 12px}.fnote .fn-t{font-weight:600}.fnote .fn-c{opacity:.6;font-size:20px;line-height:1}'
  '.fnote[open] .fn-s,.fnote:not([open]) .fn-o{display:none}.fnote:not([open]){border:0;display:block;margin-top:4px}'
  '.fnote:not([open])>summary{padding:0;justify-content:flex-start}.fnote .fn-s{display:inline-flex;align-items:center;gap:6px;opacity:.75}.fnote .fn-i{display:inline-block;width:16px;height:16px;border:1.5px solid;border-radius:50%;text-align:center;font:600 11px/13px system-ui,sans-serif}'
  '.fnote[open]>summary:hover .fn-c{opacity:1}.ballot{margin:14px 0;padding:12px 0;border-top:1px solid color-mix(in srgb,currentColor 25%,transparent);border-bottom:1px solid color-mix(in srgb,currentColor 25%,transparent);font-size:14px;line-height:1.5}.ballot b{font-weight:600}.ballot .bn{font-size:20px;font-weight:700;line-height:1.2;display:block}.ballot .bs{opacity:.8;font-size:12.5px;margin-top:6px;display:block}.ballot a{color:inherit}</style>')

def fnote(label, body):
    return ('<details class="fnote" open><summary aria-label="Show or hide this note"><span class="fn-o fn-t">%s</span>'
            '<span class="fn-s fn-t"><span class="fn-i" aria-hidden="true">i</span> Note</span><span class="fn-o fn-c" aria-hidden="true">&times;</span></summary>'
            '<div class="fn-b">%s</div></details>') % (label, body)

def roster_note(r):
    q = ROS['races'].get(r)
    if not q or r == 'mt-2026-senate': return ''
    om = q.get('omitted'); n = q.get('n_omitted', len(om or []))
    if n == 0: return ''
    who = (' It leaves out ' + '; '.join(esc(x) for x in om) + '.') if om else (' It leaves out %d other candidate%s.' % (n, '' if n == 1 else 's'))
    body = ('This map shows two of the %d candidates on the ballot, according to Ballotpedia.%s Shares and colours are each county\'s share of the two shown candidates\' votes, not of all votes. '
            '<a style="color:inherit" href="%s">Source</a> &middot; <a style="color:inherit" href="../../errata/#E-2026-002">Corrections</a>') % (q['total'], who, esc(q['src']))
    if q.get('caveat'): body = esc(q['caveat']) + ' ' + body
    return '<!--roster-->' + fnote('Note, added ' + esc(ROS['checked']), body) + '<!--/roster-->'


def wrap_notice(t):
    """Turn the builder's plain note (aside.notice) into the same collapsible component."""
    return re.sub(r'<aside class="notice" role="note"><b>Note, added (.*?)\.</b> (.*?)</aside>', lambda m: fnote('Note, added ' + m.group(1), m.group(2)), t, count=1, flags=re.S)


def _extras(r, q=None):
    out = ''
    if q and q.get('caveat'): out += '<span class="bs">%s</span>' % esc(q['caveat'])
    f = FACTS.get(r)
    if f:
        for k, lab in (('kind', ''), ('rules', 'Rules: '), ('changes', 'Change: ')):
            if f.get(k): out += '<span class="bs">%s%s <a href="%s">Source</a></span>' % (lab, esc(f[k]), esc(f['src']))
    return out

def ballot_card(r):
    cp = os.path.join(ROOT, 'elections', r, 'config.json')
    c = json.load(open(cp))['candidates']; shown = [c['a']['full'], c['b']['full']]
    q = ROS['races'].get(r)
    if q:
        n = q.get('n_omitted', len(q.get('omitted') or [])); extra = q.get('extra')
        tot = ('%d candidates' % q['total']) + (' and %s' % extra if extra else '')
        if n == 0: line = 'The map shows both: %s and %s.' % tuple(esc(x) for x in shown)
        else:
            line = 'The map shows 2: %s and %s.' % tuple(esc(x) for x in shown)
            line += (' Not shown: ' + '; '.join(esc(x) for x in q['omitted']) + '.') if q.get('omitted') else ' Not shown: %d others (names not yet recorded).' % n
        src = _extras(r, q) + '<span class="bs">Checked %s against Ballotpedia. <a href="%s">Source</a></span>' % (esc(ROS['checked']), esc(q['src']))
        return '<!--ballot--><div class="ballot"><b class="bn">%s on the ballot</b>%s%s</div><!--/ballot-->' % (esc(tot), line, src)
    if r in ROS.get('unresolved', {}):
        return '<!--ballot--><div class="ballot"><b class="bn">Ballot roster being checked</b>The map shows 2: %s and %s. Sources disagree on whether others are on the ballot.</div><!--/ballot-->' % tuple(esc(x) for x in shown)
    return '<!--ballot--><div class="ballot"><b class="bn">Ballot roster not yet verified</b>The map shows 2: %s and %s. Other candidates may be on the ballot.</div><!--/ballot-->' % tuple(esc(x) for x in shown)

def inject_roster():
    n = 0
    for r in races:
        p = os.path.join(ROOT, 'elections', r, 'index.html'); t = t0 = open(p).read()
        blk = roster_note(r)
        t = re.sub(r'<!--roster-->.*?<!--/roster-->', '', t, flags=re.S)
        t = wrap_notice(t)
        q = ROS['races'].get(r); complete = bool(q) and q.get('n_omitted', len(q.get('omitted') or [])) == 0
        want = 'Votes cast' if complete else 'Votes for the two shown'
        t = t.replace("votes: 'Votes cast'", "votes: '" + want + "'").replace("votes: 'Votes for the two shown'", "votes: '" + want + "'")
        t = re.sub(r'<!--cmp-->.*?<!--/cmp-->', '', t, flags=re.S)
        VW = 'the vote' if complete else 'the two shown candidates\u2019 votes'
        t = re.sub(r"\['t', ' of (?:the vote|the two shown candidates\u2019 votes|the two-candidate vote)", "['t', ' of " + VW, t)
        t = t.replace('"voteWord": "the two-candidate vote"', '"voteWord": "the two shown candidates\u2019 votes"')
        t = re.sub(r'<!--ballot-->.*?<!--/ballot-->', '', t, flags=re.S)
        t = t.replace('<div class="bars" id="bars"></div>', '<div class="bars" id="bars"></div>' + ballot_card(r), 1)
        if blk and 'class="notice"' not in t and 'class="fnote"' not in t: t = t.replace('<p class="dek" id="dek"></p>', '<p class="dek" id="dek"></p>' + blk, 1)
        t = re.sub(r'<style id="fn-css">.*?</style>', '', t, flags=re.S)
        if 'class="fnote"' in t or 'class="ballot"' in t: t = t.replace('</style>', '</style>' + FN_CSS, 1)
        if t != t0: open(p, 'w').write(t); n += 1
    return n

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    bad = check()
    if bad: print('\n'.join('FAIL ' + b for b in bad)); sys.exit(1)
    if cmd == 'build':
        open(os.path.join(ROOT, 'errata', 'index.html'), 'w').write(page())
        open(os.path.join(ROOT, 'errata', 'feed.xml'), 'w').write(feed())
        open(os.path.join(ROOT, 'ERRATA.md'), 'w').write(md())
        print('wrote errata page, feed, ERRATA.md; footer link on', inject(), 'page(s); roster note on', inject_roster(), 'page(s)')
    else: print('check ok:', len(ENT), 'entries,', len(races), 'pages;', len(ROS['races']), 'rosters checked,', len(races) - len(ROS['races']), 'pages NOT yet checked')
