---
name: academic-job-search
description: Search open faculty positions in computer architecture, AI/ML hardware, and quantum error correction (areas configurable in areas.md) at US/EU/Asia top-100 universities; write a dated self-contained HTML report to output/. Use when the user asks to run the faculty job search, refresh job listings, or find new faculty openings.
---

# Faculty Job Search

## Scope

Finds currently open tenure-track/tenured faculty positions at US, European, and Asian top-100 universities in the areas listed in `areas.md`. One run = one fresh full search = one dated HTML file. No state carried between runs. Not for postdoc, lecturer, staff, or industry positions.

## Handoffs

None. Self-contained; dispatches its own general-purpose search agents.

## Persona

A methodical research assistant compiling a faculty application target list: thorough on coverage, honest about unverified entries, never inventing postings.

## Inputs

- `universities.md` (this skill directory): the static US/EU/Asia top-100 union list. Rebuild only when the user asks.
- `areas.md` (this skill directory): the research areas, with area key, name, search terms, and adjacent fields that count.
- `template.html` (this skill directory): self-contained report template with `<!--DATE-->`, `<!--COUNT-->`, `<!--ROWS-->` markers.
- Run date (today).

## Output contract

- `output/jobs-YYYY-MM-DD.html` under the project root, named with the run date; overwrite on same-day rerun. Self-contained, no external assets. `output/` holds only files of this name form; no variant names (no `jobs-<region>-...html`, a scoped run still writes `jobs-YYYY-MM-DD.html`). Only the newest report is kept: once today's file is written, delete every other file in `output/`.
- One table row per posting with 15 cells in header order: university, country, deadline (`YYYY-MM-DD`, `rolling`, or `unknown`), references (count of letters or referee contacts the ad asks for: `3`, `3+`, `4`, or `unknown`; note "letters" vs "contacts" in materials), application link (`<a href>Apply</a>`), department, title, rank (`assistant|associate|full|open`), area (a key from `areas.md`, comma-joined if several), stated priority (the hiring areas the ad itself names, `none stated (all-areas)` otherwise), required materials, contact, fit notes, flag (`ok|unverified|deadline-unclear`), date checked. `class="flagged"` on the `<tr>` when flag != ok; `class="wide"` on materials and notes cells. Rows sorted by deadline ascending, `rolling`/`unknown` last.
- Final report to the user: file path, entry count, count per area, flagged count.

## Workflow

1. Dispatch parallel search agents (general-purpose, one message, concurrent), each returning a JSON array of entries with the fields in the output contract:
   - One agent per board: **AcademicJobsOnline** (also carries Asian postings), **CRA job board** (cra.org/ads), **HigherEdJobs**, **jobs.ac.uk**, **EURAXESS**.
   - Three department-sweep agents (one US, one EU, one Asia): from `universities.md`, pick the ~25 universities per region strongest in the areas and search `<university> faculty opening <search terms from areas.md, slash-joined>` plus their ECE/CS hiring pages.
2. Merge all results. Keep only universities in `universities.md` (match loosely on name). Dedupe by (university, title), preferring the entry with a verified link and firmer deadline.
3. Verify the merged list before rendering. Select every entry that meets any of these: flag is `unverified`; the link is a search, category, listing, or board-mirror page rather than the ad itself; the deadline or title came from a search snippet the agent did not open; the notes say the areas were copied from a previous round. Dispatch one general-purpose verifier per 5-8 such entries (parallel, one message). Each verifier loads the ad itself (or the university's portal), then returns for each entry one of: `confirmed` with corrected fields and the direct ad URL; `corrected` with what changed; `drop` with the reason (past cycle, not faculty, conflated with a postdoc or news item, does not exist). Apply the results: update fields, keep `unverified` only where the verifier could not load anything, and drop entries the verifier rejected, listing them with reasons in the user report.
4. Render: fill `template.html` markers, write `output/jobs-YYYY-MM-DD.html`, then delete every other file in `output/`.
5. Report to the user per the output contract, plus the verify step's drops.

## Rules

- Tenure-track/tenured faculty only; ads in the adjacent fields listed in `areas.md` count when they plausibly cover one of the areas.
- Open now: deadline on/after run date, or rolling/until-filled with evidence the ad is from the current cycle.
- Deadline inference (a missing deadline does not mean open). An ad is for the cycle it was posted in, so infer expiry from the ad's other dates and drop the ad when any of these hold:
  - Stated start date is on or before the run date, or in a semester that has already begun (e.g. "start Fall 2026" seen after August 2026).
  - Ad names a past cycle ("2025-2026 positions") or its posted/updated date is more than 9 months before the run date and it carries no deadline.
  - "Until filled" with a posted date more than 9 months old and no sign of renewal (no updated date, still lists last year's review date).
  Ads that survive with no stated deadline keep `deadline=unknown` and flag `deadline-unclear`; record posted date and start date in the notes so the reader can judge.
- Region: US, Europe (incl. UK, Switzerland, Nordics), and Asia (China, Hong Kong, Singapore, South Korea, Japan, Taiwan).
- Agents verify each application URL loads (WebFetch); unverifiable or ambiguous entries are kept and flagged, never dropped.
- Time cap per agent: 15 minutes and at most 3 fetch attempts per site. A site that still does not respond is skipped, listed as a gap in the agent's summary, and never retried in that run. Sweep agents do not spawn sub-agents; they work their list sequentially so the parent can always return partial results.
- No fabricated postings: every entry needs a real URL an agent actually visited.
- The application link points at the ad itself (or the university's application record), never at a search, category, or listing page. Dates and area lists come from the ad that is open now, not from a previous round or a news item about it.

## References

- `universities.md`, `areas.md`, `template.html` in this skill directory.
- Boards: academicjobsonline.org, cra.org/ads, higheredjobs.com, jobs.ac.uk, euraxess.ec.europa.eu.

## Failure modes

- **Board unreachable or blocks fetches**: note the gap in the user report; don't silently return fewer results.
- **Snippet conflation**: a search snippet can splice dates from a postdoc ad onto last year's faculty round (seen with Imperial Computing, Sept 2026). The verify step catches this; a sweep agent that cannot open the ad must say so in the notes instead of filling fields from the snippet.
- **JS-only application pages**: Interfolio ads (`apply.interfolio.com/<id>`) render nothing in WebFetch; read the public JSON at `https://logic.interfolio.com/dossier-api/positions/<id>` (fields `start_date`, `end_date`, description). For bot-walled boards (HigherEdJobs, CRA) prefix the URL with `https://r.jina.ai/`.
- **August to early-fall runs**: faculty ads mostly appear Sept-Dec; a thin result set is expected, say so rather than padding with stale postings.
- **Same-day rerun**: overwrites today's file by design; warn only if the user expected an append.
- **Render fails**: keep the previous report; older files are deleted only after the new one is written.
- **University name mismatches** (e.g. "U. Michigan" vs "University of Michigan"): match loosely before discarding an entry as out-of-list.
