# academic-job-search

A Claude Code skill that finds currently open tenure-track/tenured faculty positions in computer architecture, AI/ML hardware, and quantum error correction at US, European, and Asian top-100 universities, and writes a dated, self-contained HTML report.

## Usage

Open this folder in Claude Code and run:

```
/academic-job-search
```

Optional scope in the arguments, e.g. `/academic-job-search US and UK only`.

Each run is a fresh full search: it dispatches parallel agents over AcademicJobsOnline, the CRA job board, HigherEdJobs, jobs.ac.uk, and EURAXESS, plus per-region department sweeps, then merges, dedupes, and renders `output/jobs-YYYY-MM-DD.html`.

## Layout

| Path | Purpose |
|---|---|
| `.claude/skills/academic-job-search/SKILL.md` | Skill definition: workflow, output contract, rules, failure modes |
| `.claude/skills/academic-job-search/areas.md` | Research areas, search terms, and adjacent fields that count |
| `.claude/skills/academic-job-search/universities.md` | US/EU/Asia top-100 university list (rebuilt only on request) |
| `.claude/skills/academic-job-search/template.html` | Report template (sortable table, filter box, dark mode) |
| `output/` | Dated reports, one per run |

## Report

One row per posting: university, country, deadline, apply link, department, title, rank, area, stated priority, materials, contact, notes, flag, date checked. Rows are sorted by deadline; yellow rows are flagged `unverified` or `deadline-unclear` and need a manual look.

## Rules the search follows

- Faculty only: tenure-track/tenured (UK: Lecturer through Professor). No postdoc, teaching-only, staff, or industry posts.
- Open now: deadline on or after the run date, or rolling with evidence the ad is from the current cycle. Ads whose start date has passed or that name a past cycle are dropped.
- Every entry links to a page an agent actually loaded; nothing is fabricated. Unverifiable entries are kept and flagged.
- Late-August to early-fall runs return few results; most faculty ads appear September to December.
