# Academic Job Search

A Claude Code skill that finds open faculty positions in chosen research areas and publishes a dated HTML report.

Latest report: https://www.unarylab.com/academic-job-search/

## Overview

The skill searches for tenure-track/tenured and permanent teaching-stream posts in the research areas listed in `areas.md` at the universities listed in `universities.md`. The default configuration targets computer architecture, AI/ML hardware and systems, quantum error correction, computer systems, and teaching-stream posts at North American, European, and Asian top-150 universities.

### Report

One row per posting: university, deadline, title, area, rank, apply link, flag, stated priority, notes, department, country, materials, references, contact, date checked. Rows are sorted by deadline (click a column header to re-sort), with the urgency of the next 14 and 30 days marked; rows flagged `unverified` or `deadline-unclear` need a manual look. The page has a text search, tick-dropdown filters for area, region, and university (options come from `areas.md` and `universities.md`), a compact toggle that hides the three low-value columns, click-to-expand long cells, and light and dark themes. A second table lists the universities whose department pages blocked or failed to load during the run, with what blocked and where to look by hand.

### Rules the search follows

- Faculty only: tenure-track/tenured research posts, plus permanent or continuing teaching-stream posts in the units `areas.md` names (area `teaching`). No postdoc, sessional, staff, or industry posts. Ads must accept applicants at the minimum rank in `rank.md`.
- Open now: deadline on or after the run date, or rolling with evidence the ad is from the current cycle. Ads whose start date has passed or that name a past cycle are dropped.
- Every entry links to a page an agent actually loaded; nothing is fabricated. Unverifiable entries are kept and flagged.

### Files

| Path | Purpose |
|---|---|
| `areas.md`, `universities.md`, `rank.md` | User inputs (see Configuration) |
| `.claude/skills/academic-job-search/SKILL.md` | Skill definition: workflow, output contract, rules, failure modes |
| `.claude/skills/academic-job-search/merge.py` | Matches, dedupes, rank-filters, and renders the agent output; `--check` runs its self-check |
| `.claude/skills/academic-job-search/template.html` | Report template |
| `.claude/skills/academic-job-search/entries.json` | Entries of the last report, the baseline for the next run, with a per-entry `verified` count |
| `output/` | The newest dated report |
| `.github/workflows/pages.yml` | Deploys the newest report to GitHub Pages |
| `tools/weekly_run.sh` | Weekly unattended run: search, commit, push, email the site link |

## Requirements

- Claude Code with web search enabled.
- The conda `base` env with Python 3; `merge.py` uses only the standard library.
- For the weekly run: macOS (launchd), push access to this repo, and an SMTP account.

## Installation

Clone the repo and open it in Claude Code; the skill is project-local under `.claude/skills/`, so nothing else is installed.

For the weekly run, create `tools/mail.json` (gitignored) with the keys listed at the top of `tools/weekly_run.sh`, and load a launchd agent labelled `com.unarylab.academic-job-search` that calls `tools/weekly_run.sh` on Wednesdays at 23:59. The plist lives in `~/Library/LaunchAgents/`, not in the repo.

To uninstall, run `launchctl bootout gui/$(id -u)/com.unarylab.academic-job-search` and delete `~/Library/LaunchAgents/com.unarylab.academic-job-search.plist`. The script does this itself after 2027-01-31.

## Quick start

In Claude Code, from this folder:

```
/academic-job-search
```

To narrow the scope, add it as an argument, e.g. `/academic-job-search US and UK only`. Web search is capped per session (200 calls by default, shared by all agents), so run the search in a fresh session, or raise `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`. Late-August to early-fall runs return few results, because most faculty ads appear September to December.

## Reproducing results

Each run carries over the previous report's entries, verifies those not yet confirmed twice (and not already checked on the run date), and adds new postings from the parallel board agents and department sweeps over every listed university, dropping an entry only when verification rejects it or its deadline has passed. The result is merged, deduped, filtered by minimum rank, and rendered to `output/jobs-YYYY-MM-DD.html`; only the newest report is kept.

Every push to `main` that changes `output/` triggers the GitHub Pages workflow, which deploys the newest `output/jobs-*.html` as the site's `index.html`. No built copy of the site is kept in the repo.

`tools/weekly_run.sh` runs the search unattended: Claude runs the skill headless, then the script commits `entries.json` and `output/`, pushes to `main`, and emails the site link. Logs go to `~/Library/Logs/academic-job-search/`. Run it by hand with `tools/weekly_run.sh`.

## Configuration

| File | Sets |
|---|---|
| `areas.md` | Research areas, search terms, adjacent fields, and the university units whose hiring pages to check |
| `universities.md` | North America/EU/Asia top-150 university list with country, region, and aliases (rebuilt only on request) |
| `rank.md` | Minimum rank applied at (default assistant) and the title-to-rank mapping |
| `tools/mail.json` | SMTP credentials and recipient lists for the weekly email (gitignored) |

## Citation

Not applicable; this is a tool, not a publication.

## License

MIT; see [`LICENSE`](LICENSE).
