# Academic Job Search

A Claude Code skill that finds currently open tenure-track/tenured faculty positions in computer architecture, AI/ML hardware, and quantum error correction at North American, European, and Asian top-150 universities, and writes a dated, self-contained HTML report.

## Usage

Open this folder in Claude Code and run:

```
/academic-job-search
```

Optional scope in the arguments, e.g. `/academic-job-search US and UK only`.

Each run carries over the previous report's entries, verifies them, and adds new postings from the parallel board agents and department sweeps over every listed university, dropping an entry only when verification rejects it or its deadline has passed; the result is merged, deduped, and rendered to `output/jobs-YYYY-MM-DD.html`.

## Layout

| Path | Purpose |
|---|---|
| `.claude/skills/academic-job-search/SKILL.md` | Skill definition: workflow, output contract, rules, failure modes |
| `.claude/skills/academic-job-search/areas.md` | Research areas, search terms, and adjacent fields that count |
| `.claude/skills/academic-job-search/universities.md` | North America/EU/Asia top-150 university list (rebuilt only on request) |
| `.claude/skills/academic-job-search/template.html` | Report template (sortable table, filter box, dark mode) |
| `.claude/skills/academic-job-search/entries.json` | Entries of the last report, the baseline for the next run |
| `output/` | Dated reports, one per run |

## Report

One row per posting: university, country, deadline, apply link, department, title, rank, area, stated priority, materials, contact, notes, flag, date checked. Rows are sorted by deadline; yellow rows are flagged `unverified` or `deadline-unclear` and need a manual look. A second table lists the universities whose department pages blocked or failed to load during the run, with what blocked and where to look by hand.

## Rules the search follows

- Faculty only: tenure-track/tenured (UK: Lecturer through Professor). No postdoc, teaching-only, staff, or industry posts.
- Open now: deadline on or after the run date, or rolling with evidence the ad is from the current cycle. Ads whose start date has passed or that name a past cycle are dropped.
- Every entry links to a page an agent actually loaded; nothing is fabricated. Unverifiable entries are kept and flagged.
- Late-August to early-fall runs return few results; most faculty ads appear September to December.
