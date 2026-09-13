# Academic Job Search

A Claude Code skill that finds currently open faculty positions (tenure-track/tenured, plus permanent teaching-stream posts) in the research areas listed in `areas.md` at the universities listed in `universities.md`, and writes a dated, self-contained HTML report. The default configuration targets computer architecture, AI/ML hardware and systems, quantum error correction, computer systems, and teaching-stream posts at North American, European, and Asian top-150 universities.

## Usage

Open this folder in Claude Code and run:

```
/academic-job-search
```

Optional scope in the arguments, e.g. `/academic-job-search US and UK only`.

Each run carries over the previous report's entries, verifies those not yet confirmed twice (and not already checked on the run date), and adds new postings from the parallel board agents and department sweeps over every listed university, dropping an entry only when verification rejects it or its deadline has passed. The result is merged, deduped, filtered by minimum rank, and rendered to `output/jobs-YYYY-MM-DD.html`; only the newest report is kept.

Web search is capped per session (200 calls by default, shared by all agents), so run the search in a fresh session, or raise `CLAUDE_CODE_MAX_WEB_SEARCHES_PER_SESSION`.

## Layout

| Path | Purpose |
|---|---|
| `areas.md` | User input: research areas, search terms, adjacent fields, and the university units whose hiring pages to check |
| `universities.md` | User input: North America/EU/Asia top-150 university list (rebuilt only on request) |
| `rank.md` | User input: minimum rank applied at (default assistant) and title-to-rank mapping |
| `.claude/skills/academic-job-search/SKILL.md` | Skill definition: workflow, output contract, rules, failure modes |
| `.claude/skills/academic-job-search/merge.py` | Matches, dedupes, rank-filters, and renders the agent output; `--check` runs its self-check |
| `.claude/skills/academic-job-search/template.html` | Report template (sortable table, area/region/university filters, dark mode) |
| `.claude/skills/academic-job-search/entries.json` | Entries of the last report, the baseline for the next run, with a per-entry `verified` count |
| `output/` | The newest dated report |

## Report

One row per posting: university, deadline, title, area, rank, apply link, flag, stated priority, notes, department, country, materials, references, contact, date checked. Rows are sorted by deadline, with the urgency of the next 14 and 30 days marked; rows flagged `unverified` or `deadline-unclear` need a manual look. The page has a text search, tick-dropdown filters for area, region, and university (options come from `areas.md` and `universities.md`), a compact toggle that hides the three low-value columns, click-to-expand long cells, and light and dark themes. A second table lists the universities whose department pages blocked or failed to load during the run, with what blocked and where to look by hand.

## Rules the search follows

- Faculty only: tenure-track/tenured research posts, plus permanent or continuing teaching-stream posts in the units `areas.md` names (area `teaching`). No postdoc, sessional, staff, or industry posts. Ads must accept applicants at the minimum rank in `rank.md`.
- Open now: deadline on or after the run date, or rolling with evidence the ad is from the current cycle. Ads whose start date has passed or that name a past cycle are dropped.
- Every entry links to a page an agent actually loaded; nothing is fabricated. Unverifiable entries are kept and flagged.
- Late-August to early-fall runs return few results; most faculty ads appear September to December.
