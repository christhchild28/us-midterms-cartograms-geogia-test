"""Certified-list recheck.

Re-reads each race's tier 1 source and reports. It never edits evidence, rosters or pages.

  python3 src/recheck.py run [--force] [--out report.md]

What it can tell:
  ok           every recorded candidate name is still on the source
  review       some recorded names are missing from the source (a person must look)
  manual       the source cannot be read by machine (script-driven page, scan, error, moved)
What it cannot tell: a candidate ADDED to a source. Only a person or a per-state parser can see that,
so a clean report is not proof. The report says so.

Runs only inside WINDOW unless --force. The weekly workflow is in .github/workflows/recheck.yml.
"""
import json, os, re, subprocess, sys, tempfile, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVID = os.path.join(ROOT, 'errata', 'evidence')
WINDOW = (datetime.date(2026, 12, 7), datetime.date(2027, 1, 31))
MIN_TEXT = 300
UA = 'Mozilla/5.0 (compatible; roster-recheck; +https://github.com/christhchild28/us-midterms-cartograms-geogia-test)'
SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv'}


def fetch(url, timeout=40):
    """Return (bytes, content_type) or raise."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(25_000_000), (r.headers.get('Content-Type') or '')


def to_text(body, ctype):
    if body[:5] == b'%PDF-' or 'pdf' in ctype.lower():
        with tempfile.NamedTemporaryFile(suffix='.pdf') as f:
            f.write(body); f.flush()
            out = subprocess.run(['pdftotext', '-layout', f.name, '-'], capture_output=True, timeout=120)
            return out.stdout.decode('utf-8', 'replace')
    t = body.decode('utf-8', 'replace')
    t = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', t)
    t = re.sub(r'(?s)<[^>]+>', ' ', t)
    return re.sub(r'&[a-z#0-9]+;', ' ', t)


def last_name(name):
    n = re.sub(r'\s*\([^)]*\)', '', name).strip()
    parts = [p.strip('.,') for p in n.split() if p.strip('.,').lower() not in SUFFIX]
    return parts[-1] if parts else ''


def has_name(text, name):
    ln = last_name(name)
    return bool(ln) and re.search(r'(?i)(?<![A-Za-z])' + re.escape(ln) + r'(?![A-Za-z])', text) is not None


def check_race(race, obs, fetcher=fetch):
    url = obs.get('url', '')
    names = obs.get('names') or []
    base = {'race': race, 'publisher': obs.get('publisher', ''), 'url': url, 'as_of': obs.get('as_of', '')}
    try:
        body, ctype = fetcher(url)
        text = to_text(body, ctype)
    except Exception as e:
        return dict(base, status='manual', why='could not fetch: %s' % str(e)[:80])
    if len(text.strip()) < MIN_TEXT:
        return dict(base, status='manual', why='page has no readable text (script-driven or scanned)')
    missing = [n for n in names if not has_name(text, n)]
    if len(missing) == len(names) and names:
        return dict(base, status='manual', why='no recorded name found (script-driven page, or the source moved)')
    if missing:
        return dict(base, status='review', why='missing from source: ' + ', '.join(missing))
    return dict(base, status='ok', why='')


def collect():
    out = []
    for fn in sorted(os.listdir(EVID)):
        if not fn.endswith('.json'):
            continue
        d = json.load(open(os.path.join(EVID, fn)))
        if d.get('same_race_as'):
            continue
        t1 = [o for o in d.get('observations', []) if o.get('tier') == 1]
        if t1:
            out.append((d.get('race', fn[:-5]), t1[-1]))
    return out


def render(results, today):
    by = {k: [r for r in results if r['status'] == k] for k in ('review', 'manual', 'ok')}
    L = ['# Certified-list recheck, %s' % today, '',
         '%d races read: %d ok, %d need review, %d need a manual look.' % (
             len(results), len(by['ok']), len(by['review']), len(by['manual'])), '',
         'Limit: this check sees recorded names that disappeared. It cannot see a candidate added to a source. '
         'A clean result is not proof of a certified list.', '']
    if by['review']:
        L += ['## Needs review (names missing from the source)', '']
        L += ['- [ ] `%s` %s: %s <%s>' % (r['race'], r['publisher'], r['why'], r['url']) for r in by['review']] + ['']
    if by['manual']:
        L += ['## Manual checklist (not machine-readable)', '']
        L += ['- [ ] `%s` %s: %s <%s>' % (r['race'], r['publisher'], r['why'], r['url']) for r in by['manual']] + ['']
    L += ['## Next step', '',
          'Ask Claude to clear the checklist in one Chrome session. Any real difference becomes a draft entry in errata/errata.json for approval. Nothing here edits a page.', '']
    return '\n'.join(L)


def main(argv, fetcher=fetch, today=None):
    today = today or datetime.date.today()
    force = '--force' in argv
    out = argv[argv.index('--out') + 1] if '--out' in argv else 'recheck-report.md'
    if not force and not (WINDOW[0] <= today <= WINDOW[1]):
        print('outside window %s to %s; nothing to do' % WINDOW)
        return 0
    results = [check_race(r, o, fetcher) for r, o in collect()]
    open(out, 'w').write(render(results, today))
    print(open(out).read().split('\n## ')[0])
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'run':
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[2:]))
