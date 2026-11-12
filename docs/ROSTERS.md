# Ballot rosters: how we record and resolve them

Evidence goes in `errata/evidence/<race>.json`. `errata/rosters.json` is derived from it. Do not edit `rosters.json` by hand.

## Add or update a race
1. Open or create `errata/evidence/<race>.json`.
2. Add one observation per source:
   `{"tier": 1, "publisher": "Kansas Secretary of State", "url": "https://...", "as_of": "2026-11-12", "retrieved": "2026-11-12", "names": ["A (D)", "B (R)"], "exhaustive": true}`
   Use `total` when the source gives a count but no names. Use `"exhaustive": false` when the source only names some candidates.
3. Run `python3 src/roster_resolve.py resolve`, then `python3 src/corrections.py build` and `check`.
4. If no source gives a roster, write `{"race": "<race>", "unresolved": "what we know", "observations": []}`.

## Source tiers
1 state election office list. 2 AP or Green Papers. 3 Ballotpedia. 4 news or other.
The lower tier number wins. With equal tiers the newer `as_of` wins. Equal tier and date with different counts leaves the race unresolved. Lower-ranked disagreements are kept in `conflicts`.

## What readers see
Tier 1 shows "Confirmed against the state election office list". Tiers 2 to 4 show "Reported by <publisher>". A race with no usable evidence shows "Ballot roster not yet verified".

## Fault rules
- A bad observation is skipped with a warning. A bad file leaves only that race unverified.
- `resolve` writes atomically and copies the old file to `rosters.last-good.json`. It refuses to overwrite with an empty result.
- The page build falls back to the last-good copy if `rosters.json` is unreadable. A failure on one page's card shows the "not yet verified" card and the build goes on.
- Evidence older than 14 days produces a warning.

Tests: `python3 -m unittest tests.test_roster_resolve`
