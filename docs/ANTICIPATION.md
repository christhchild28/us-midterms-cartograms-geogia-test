# Planning for what we can know in advance

Rule: a fact that is public before election day must be a required input, not something we find out afterwards.
Each item has: what to capture, when it is knowable, and the check that blocks a release if it is missing.

| # | Fact | Knowable by | Capture as | Check |
|---|---|---|---|---|
| 1 | Full ballot roster: every candidate, party, status (on ballot / withdrawn but on ballot / write-in) | State certification, before ballots go out (45 days before the election for overseas and military voters) | `errata/rosters.json` today; a roster table in the data model next | Page build fails without a roster; the page card shows count and shown vs not shown |
| 2 | Contest rules: plurality, majority with runoff, top-two, ranked-choice, closed or open primary | Statute, months before | `race.rules` field | Headline wording must match the rule (for example "leads with" until a majority is confirmed) |
| 3 | Special vs regular election | Calendar | `race.kind` | Page title says "special" |
| 4 | Candidate changes: withdrawals, replacements, court orders, deadlines | Withdrawal deadlines (Aug to Sept) | `what_could_change` per race, with the date it closes | Re-check roster on the freeze date and on election day |
| 5 | Party-backed independents and nonpartisan labels | Endorsements, filings | `alignment` per race with sources | Colour and swing wording follow the declared alignment |
| 6 | Comparison race validity: same geography, same kind of race | Known when the page is designed | `prior` block with reason | Swing shows "not comparable" when the prior race lacks the family |
| 7 | Geography quirks: independent cities, boroughs, planning regions, town-level reporting, merged counties | Census and state files | unit registry notes | Geometry gates G1 to G8 |
| 8 | Count and certification rules: mail-ballot receipt deadlines, canvass dates, automatic recount margins | Statute | `what_could_change` | Page states "unofficial" until certification; recount watch flag |
| 9 | Denominator of every percentage and label | Design time | metric registry | Wording check: "vote", "votes cast" and "of the vote" need an all-candidates denominator |
| 10 | Source terms and data vintage (population estimates, results provider) | Contract and file headers | `data/SOURCES` | Manifest gates D1 to D12 |
| 11 | Official vote total and call status per race: certified, counting, recount, uncalled | State results page (tier 1), updated until certification | `errata/results.json` per race: official total, status, as_of, source | `drafts` flags a page total that differs from the official total beyond a set tolerance, and a "won" headline on a race that is uncalled, counting or in recount. A person reviews every draft; nothing publishes itself |

## Planning field: what could change
Every race page carries a short list: the real-world change, the date it closes, and the check that would catch it.
Examples: a nominee withdraws after ballots print; a majority is needed and a runoff follows; a recount threshold is met; a county merges.
