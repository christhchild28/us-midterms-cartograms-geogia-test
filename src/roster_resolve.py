"""Ballot roster resolver.

Evidence in, one derived file out:
  errata/evidence/<race>.json   what each source said, with tier, URL and dates (edited by people or fetchers)
  errata/rosters.json           derived. Do not edit by hand. The page build reads only this file.

  python3 src/roster_resolve.py resolve   rebuild rosters.json from evidence (atomic, keeps a last-good copy)
  python3 src/roster_resolve.py status    one line per race: confidence, conflicts, stale evidence
  python3 src/roster_resolve.py migrate   one-time: write evidence files from the current rosters.json

Source tiers (lower number wins a conflict):
  1 state election office list   2 AP or Green Papers (built from state filings)   3 Ballotpedia   4 news or other
Confidence shown to readers: tier 1 = confirmed, tiers 2 to 4 = reported.

Fault rules: one bad evidence file or observation never stops the others. A race with no valid
observation becomes "unverified". A failed run leaves the last good rosters.json in place.
"""
import json, os, re, sys, datetime, shutil

TIERS = {1: 'State election office', 2: 'AP or Green Papers', 3: 'Ballotpedia', 4: 'News or other'}
STALE_DAYS = 14
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(path):
    """Return (data, error). Never raises."""
    try:
        with open(path) as f: return json.load(f), None
    except FileNotFoundError: return None, 'missing'
    except (ValueError, OSError) as e: return None, str(e)


def atomic_write(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f: json.dump(data, f, indent=1, ensure_ascii=False); f.write('\n')
    os.replace(tmp, path)


def _date(s):
    try: return datetime.date.fromisoformat(s)
    except (TypeError, ValueError): return None


def validate(o):
    """Problems with one observation. Empty list means usable."""
    p = []
    if not isinstance(o, dict): return ['not an object']
    if o.get('tier') not in TIERS: p.append('tier must be 1 to 4')
    if not str(o.get('url', '')).startswith('http'): p.append('url missing')
    if not o.get('publisher'): p.append('publisher missing')
    if not _date(o.get('as_of')): p.append('as_of must be YYYY-MM-DD')
    if not _date(o.get('retrieved')): p.append('retrieved must be YYYY-MM-DD')
    names, total = o.get('names'), o.get('total')
    if names is not None and not (isinstance(names, list) and all(isinstance(n, str) and n for n in names)): p.append('names must be a list of strings')
    if total is not None and not (isinstance(total, int) and total >= 2): p.append('total must be an integer of 2 or more')
    if not names and total is None: p.append('needs names or total')
    if names and total is not None and total < len(names): p.append('total is smaller than the number of names')
    return p


def count(o):
    """(count, exact). Exact only when the source says its list is the whole ballot."""
    n = o['total'] if o.get('total') is not None else len(o.get('names') or [])
    return n, bool(o.get('exhaustive', True)) or o.get('total') is not None


def _tok(n): return [re.sub(r'[^a-z]', '', t.lower()) for t in n.split('(')[0].split() if re.sub(r'[^a-z]', '', t.lower())]


def same(a, b):
    """Same person: equal last name and equal first initial. Ford, Aaron and Ford, Danielle differ."""
    x, y = _tok(a), _tok(b)
    return bool(x and y) and x[-1] == y[-1] and x[0][0] == y[0][0]


def resolve_race(race, ev, mapped, today):
    """Return (roster_or_None, unresolved_note_or_None, warnings)."""
    warn = []; good = []
    for i, o in enumerate(ev.get('observations') or []):
        bad = validate(o)
        if bad: warn.append('%s observation %d skipped: %s' % (race, i, '; '.join(bad)))
        else: good.append(o)
    if not good: return None, ev.get('unresolved'), warn
    good.sort(key=lambda o: (o['tier'], [-int(c) for c in o['as_of'].replace('-', '')]))
    top = good[0]
    ties = [o for o in good if o['tier'] == top['tier'] and o['as_of'] == top['as_of'] and count(o)[0] != count(top)[0]]
    if ties:
        return None, 'Sources of the same rank disagree: %s says %d, %s says %d.' % (top['publisher'], count(top)[0], ties[0]['publisher'], count(ties[0])[0]), warn
    n, exact = count(top)
    names = top.get('names') or []
    if names:
        for m in mapped:
            if not any(same(m, x) for x in names): warn.append('%s: mapped candidate %s is not in the source list' % (race, m))
        omitted = [x for x in names if not any(same(m, x) for m in mapped)]
    else: omitted = None
    n_om = max(n - 2, 0)
    r = {'total': n, 'omitted': omitted if (omitted and len(omitted) == n_om) else None, 'src': top['url'], 'publisher': top['publisher'], 'tier': top['tier'],
         'confidence': 'confirmed' if top['tier'] == 1 else 'reported', 'as_of': top['as_of'], 'retrieved': top['retrieved']}
    if r['omitted'] is None and n_om: r['n_omitted'] = n_om
    if not exact: r['at_least'] = True
    for k in ('caveat', 'extra'):
        if top.get(k): r[k] = top[k]
    r['conflicts'] = [{'publisher': o['publisher'], 'tier': o['tier'], 'url': o['url'], 'count': count(o)[0]} for o in good[1:] if count(o)[0] != n]
    age = (today - _date(top['retrieved'])).days
    if age > STALE_DAYS: warn.append('%s: evidence is %d days old' % (race, age))
    return r, None, warn


def mapped_names(root, race):
    d, err = load_json(os.path.join(root, 'elections', race, 'config.json'))
    if err or not d: return []
    c = d.get('candidates', {}); return [c.get('a', {}).get('full', ''), c.get('b', {}).get('full', '')]


def resolve_all(root=ROOT, today=None):
    today = today or datetime.date.today(); races = {}; unresolved = {}; warns = []; newest = ''
    evd = os.path.join(root, 'errata', 'evidence')
    for fn in sorted(os.listdir(evd)) if os.path.isdir(evd) else []:
        if not fn.endswith('.json'): continue
        race = fn[:-5]; ev, err = load_json(os.path.join(evd, fn))
        if err or not isinstance(ev, dict): warns.append('%s evidence unreadable (%s); race left unverified' % (race, err)); continue
        try: r, u, w = resolve_race(race, ev, mapped_names(root, race), today)
        except Exception as e: warns.append('%s resolver error (%s); race left unverified' % (race, e)); continue
        warns += w
        if r: races[race] = r; newest = max(newest, r['retrieved'])
        elif u: unresolved[race] = u
    return {'checked': newest, 'note': 'Derived from errata/evidence by src/roster_resolve.py. Do not edit by hand.', 'races': races, 'unresolved': unresolved}, warns


def resolve(root=ROOT):
    out, warns = resolve_all(root)
    for w in warns: print('WARN', w)
    path = os.path.join(root, 'errata', 'rosters.json')
    if not out['races']: print('FAIL no valid evidence; leaving rosters.json untouched'); return 1
    if os.path.exists(path): shutil.copyfile(path, path.replace('.json', '.last-good.json'))
    atomic_write(path, out); print('resolved %d races, %d unresolved, %d warnings' % (len(out['races']), len(out['unresolved']), len(warns))); return 0


def status(root=ROOT):
    out, warns = resolve_all(root)
    for k, r in sorted(out['races'].items()):
        print('%-22s %-9s tier %d  %s%d  %s%s' % (k, r['confidence'], r['tier'], 'at least ' if r.get('at_least') else '', r['total'], r['publisher'], '  CONFLICT' if r['conflicts'] else ''))
    for k, u in sorted(out['unresolved'].items()): print('%-22s unresolved  %s' % (k, u))
    for w in warns: print('WARN', w)


def migrate(root=ROOT):
    old, err = load_json(os.path.join(root, 'errata', 'rosters.json'))
    if err: print('FAIL', err); return 1
    evd = os.path.join(root, 'errata', 'evidence'); os.makedirs(evd, exist_ok=True)
    pub = {'news.ballotpedia.org': ('Ballotpedia', 3), 'kaxe.org': ('KAXE', 4), 'newsfromthestates.com': ('South Dakota Searchlight', 4)}
    for race, q in old['races'].items():
        host = re.sub(r'^https?://(www\.)?', '', q['src']).split('/')[0]; name, tier = pub.get(host, (host, 4))
        o = {'tier': tier, 'publisher': name, 'url': q['src'], 'as_of': old['checked'], 'retrieved': old['checked'], 'total': q['total'], 'exhaustive': True}
        if q.get('omitted') and len(q['omitted']) == q['total'] - 2: o['names'] = [x for x in mapped_names(root, race) if x] + q['omitted']
        for k in ('caveat', 'extra'):
            if q.get(k): o[k] = q[k]
        atomic_write(os.path.join(evd, race + '.json'), {'race': race, 'observations': [o]})
    for race, note in old.get('unresolved', {}).items():
        atomic_write(os.path.join(evd, race + '.json'), {'race': race, 'unresolved': note, 'observations': []})
    print('wrote evidence for', len(old['races']), 'races and', len(old.get('unresolved', {})), 'unresolved'); return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    sys.exit({'resolve': resolve, 'status': lambda: status() or 0, 'migrate': migrate}.get(cmd, lambda: print(__doc__) or 2)())
