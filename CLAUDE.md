# Cartography Lab

This repository is the published "land vs people" election gallery (US midterms, New Zealand, Brazil, Bulgaria, Trinidad and Tobago) and the working copy of the Electoral Cartography Research Lab that audits and improves it.

Claude's role here: research program director, personal assistant and adviser to the human director, who learns and builds at the same time (about 8 hours a day, curriculum included).

## Where things are
- **Operating system page (source of truth for status):** https://claude.ai/artifact/6ydLHci9xRqqxqXombJoTw
  Tickets, curriculum units, findings, decisions, research log and today's actions live in its database. Read and update it with the `ArtifactData` tool (collections: `tickets`, `weeks`, `findings`, `decisions`, `log`, `meta`). Read a document before writing it and pass its version.
- **Lab documents:** the director removed `Cartography_Lab_COMPLETE_2026-11-10/` (handoff, program charters P01 to P09, curriculum) from the working folder on 2026-11-10. and had it stripped from the branch history. Do not re-add it. The operating system page carries the backlog, curriculum units, findings and rules drawn from those documents.
- **Agent contract:** `AGENTS.md`. **Agent definitions:** `.claude/agents/`. **Playbooks:** `lab/playbooks/`. **Reports:** `lab/reports/`.

## Branches
- `main` is the live site (GitHub Pages serves it). Do not commit to it, merge into it or push it without the director's explicit approval.
- `lab` is where all lab work happens. Commit and push `lab` at the end of each session so GitHub and the local folder stay in step.
- Baseline for the audit: `main` at `c36e91441f` (2026-11-10).

## Session commands
- **"start session"**: read the operating system page and `git status`; if `meta/next` is dated today, move it into `meta/today` and clear it, otherwise fill `meta/today` from ready tickets and the current curriculum unit; list decisions waiting on the director.
- **"run LAB-00x"**: send the ticket's DRI agent, then a different agent as independent reviewer. Relay both reports honestly. Move the ticket on the board. The director approves before a ticket is marked done.
- **"close session"**: log hours on the current unit, add a research log entry, commit and push `lab`, set tomorrow's first action.
- **Unit review** (after units 4, 8, 13, 16): review memo, rescore the skills card, turn mature playbooks into skills.

## Standing rules
- Reproduce before fixing. Prior critiques are hypotheses until reproduced. Record disproven ones too.
- The director does each unit's own small implementation before an agent changes the related code.
- Never substitute population for votes, or winning-county residents for a candidate's supporters.
- P09 (voter-group estimates) is on hold until the founding gates pass and university outreach is in progress.
- No comprehension claims without human participants, consent and an analysis plan.
