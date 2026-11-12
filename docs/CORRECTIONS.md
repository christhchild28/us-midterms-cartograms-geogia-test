# Corrections policy

We correct our own errors in public. We never change a published page without a note.

## How readers report an error
Every page has a "Report an error" link. It opens a GitHub issue form (`.github/ISSUE_TEMPLATE/correction.yml`).
An email address will be added to `errata/errata.json` (`contact_email`) when the domain exists. Until then the page shows no email.

## Severity
| Level | Meaning | Response target |
|---|---|---|
| S1 | Wrong headline number, wrong winner, or wrong race shown | Page note within 24 hours, fix as soon as possible |
| S2 | A candidate, party or label is missing or wrong; a share means something other than it says | Page note within 2 days |
| S3 | Cosmetic or wording | Fix in the next release; log it |

## Triage
1. A new issue gets the labels `correction` and `triage`.
2. One owner reads it within 2 days, checks it against a primary source, and sets a severity label.
3. If it is real: add an entry to `errata/errata.json`, run `python3 src/corrections.py build`, publish.
4. If it is not real: answer in the issue with the source. Close it.
5. Every entry says what was wrong, what we did, and what check would have caught it.

## Rules
- Entries are never deleted. A fixed entry changes status to `corrected` and keeps its text.
- Page notes carry a date and are never silent edits.
- `python3 src/corrections.py check` fails if a page has a note but no errata entry, or an entry names a page that does not exist.

## What could change (planning)
Each race should list real-world changes that would alter the page: a nominee withdraws, a runoff, a recount, a new party, ranked-choice voting, a county merger. Add them to the race notes. The detection checks for these are tracked in the roadmap.
