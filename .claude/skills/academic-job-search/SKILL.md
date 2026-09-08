---
name: academic-job-search
description: Search open faculty positions in computer architecture, AI/ML hardware, and quantum error correction (areas configurable in areas.md) at US/EU/Asia top-150 universities; write a dated self-contained HTML report to output/. Use when the user asks to run the faculty job search, refresh job listings, or find new faculty openings.
---

# Faculty Job Search

## Scope

Finds currently open tenure-track/tenured faculty positions at US, European, and Asian top-150 universities in the areas listed in `areas.md`. Each run starts from the entries in the last report (`entries.json`), verifies them, adds newly found postings, and drops an entry only when a verifier rejects it or its deadline has passed. One run = one dated HTML file. Not for postdoc, lecturer, staff, or industry positions.

## Handoffs

None. Self-contained; dispatches its own general-purpose search agents.

## Persona

A methodical research assistant compiling a faculty application target list: thorough on coverage, honest about unverified entries, never inventing postings.

## Inputs

- `universities.md` (this skill directory): the static US/EU/Asia top-150 union list with an `Aliases` column (short forms separated by `;`). Rebuild only when the user asks; add an alias when a real posting names a listed university by a form not yet in the table.
- `merge.py` (this skill directory): matches, dedupes, sorts, and renders the agent JSON files.
- `entries.json` (this skill directory): the full entry list of the last rendered report; `merge.py` rewrites it after each render (`--no-save` skips).
- `areas.md` (this skill directory): the research areas, with area key, name, search terms, and adjacent fields that count.
- `template.html` (this skill directory): self-contained report template with `<!--DATE-->`, `<!--COUNT-->`, `<!--ROWS-->`, `<!--GAPS-->` markers.
- Run date (today).

## Output contract

- `output/jobs-YYYY-MM-DD.html` under the project root, named with the run date; overwrite on same-day rerun. Self-contained, no external assets. `output/` holds only files of this name form; no variant names (no `jobs-<region>-...html`, a scoped run still writes `jobs-YYYY-MM-DD.html`). Only the newest report is kept: once today's file is written, delete every other file in `output/`.
- One table row per posting with 15 cells in header order: university, country, deadline (`YYYY-MM-DD`, `rolling`, or `unknown`), references (count of letters or referee contacts the ad asks for: `3`, `3+`, `4`, or `unknown`; note "letters" vs "contacts" in materials), application link (`<a href>Apply</a>`), department, title, rank (`assistant|associate|full|open`), area (a key from `areas.md`, comma-joined if several), stated priority (the hiring areas the ad itself names, `none stated (all-areas)` otherwise), required materials, contact, fit notes, flag (`ok|unverified|deadline-unclear`), date checked. `class="flagged"` on the `<tr>` when flag != ok; `class="wide"` on materials and notes cells. Rows sorted by deadline ascending, `rolling`/`unknown` last; flagged rows after all `ok` rows in the same order, with `unverified` rows last.
- A second table, "Not checked this run", with one row per university the sweep could not check: university, country, what blocked, where to look (one link per URL). Rendered from `--gaps`; empty when the flag is absent.
- Final report to the user: file path, entry count, count per area, flagged count, gap count.

## Workflow

1. Dispatch parallel search agents (general-purpose, one message, concurrent), each returning a JSON array of entries with the fields in the output contract:
   - One agent per board: **AcademicJobsOnline** (also carries Asian postings), **CRA job board** (careercenter.cra.org; cra.org/ads redirects there), **HigherEdJobs**, **jobs.ac.uk**, **academicpositions.com**, **Nature Careers** (jobs.nature.com / nature.com/naturecareers).
   - Department-sweep agents covering every university in `universities.md`: split the table in order into lists of about 30 (one agent per list; US rows first, then EU, then Asia; a scoped run splits only the rows in scope). Each agent works its list sequentially and searches `<university> faculty opening <search terms from areas.md, slash-joined>` plus the university's ECE/CS hiring pages, and returns in its final message its gaps: each university it could not check, with what blocked and the URL to check.
2. Merge: copy `entries.json` to `<dir>/00-previous.json` so the previous report's entries are merged as a source. Write the agent JSON files to the same directory and run `conda run -n base python merge.py --date <date> --in-dir <dir>`. It keeps an entry only when its `university` field, normalized (lowercase, punctuation stripped, spaces collapsed), exactly equals a canonical name or alias in `universities.md`; nothing fuzzy. Entries whose title or link names a branch campus (`hkust-gz`, `hkust(gz)`, `cuhk-shenzhen`, `cuhk shenzhen`, `nyu abu dhabi`, `nyu shanghai`, `duke kunshan`) are dropped. Every drop is printed with its reason. Within a university, two entries are the same posting when their link keys match (Interfolio id, or same host and same 5+ digit id) or their title token-set Jaccard is at least 0.5; same host with different numeric ids means distinct postings. The kept entry is the higher-scoring one (+3 university-domain or Interfolio link, -2 board mirror, +2 dated deadline, +1 rolling, +2 flag `ok`, +1 `deadline-unclear`); it takes the firmest deadline of the pair and notes the other link as `[also listed: url]`.
3. Verify the merged list before rendering. Every entry from `00-previous.json` is verified each run. Also select every new entry that meets any of these: flag is `unverified`; deadline is rolling or unknown and no posted date is recorded; the link is a search, category, listing, or board-mirror page rather than the ad itself; the deadline or title came from a search snippet the agent did not open; the notes say the areas were copied from a previous round. Dispatch at most 6 general-purpose verifiers, grouping the selected entries evenly (parallel, one message). Each verifier loads the ad itself (or the university's portal), then returns for each entry one of: `confirmed` with corrected fields and the direct ad URL; `corrected` with what changed; `drop` with the reason (past cycle, not faculty, conflated with a postdoc or news item, does not exist). Apply the results to the files in `<dir>` (including `00-previous.json`): update fields, keep `unverified` only where the verifier could not load anything, and remove entries the verifier rejected; an existing entry is removed only on a `drop` verdict. Write the outcome to `verify.json` in the scratchpad, one record per entry: link key, action (`confirmed`, `corrected`, `drop`), what changed. The drops go in the user report with reasons.
4. Collect the sweep agents' gaps into `gaps.json` in the scratchpad (`university`, `blocked`, `check`), one record per university the sweep could not check; universities that were checked and had nothing open are not gaps.
5. Render: run `merge.py --date <date> --in-dir <dir> --gaps <scratchpad>/gaps.json` again (`conda run -n base python merge.py ...`). It fills `template.html`, writes `output/jobs-YYYY-MM-DD.html`, deletes every other file in `output/`, rewrites `entries.json`, fills the gap table, and prints the new-since-last-report and gone-since-last-report lists plus any gap university not in `universities.md`.
6. Report to the user per the output contract, plus the new entries, the gone entries (each with its drop reason), and the gap count.

## Rules

- Tenure-track/tenured faculty only; ads in the adjacent fields listed in `areas.md` count when they plausibly cover one of the areas. Physics-department or quantum-information-theory hires do not count for `qec`.
- Open now: deadline on/after run date, or rolling/until-filled with evidence the ad is from the current cycle.
- Deadline inference (a missing deadline does not mean open). An ad is for the cycle it was posted in, so infer expiry from the ad's other dates and drop the ad when any of these hold:
  - Stated start date is on or before the run date, or in a semester that has already begun (e.g. "start Fall 2026" seen after August 2026).
  - Ad names a past cycle ("2025-2026 positions") or its posted/updated date is more than 9 months before the run date and it carries no deadline.
  - "Until filled" with a posted date more than 9 months old and no sign of renewal (no updated date, still lists last year's review date).
  - An ad posted before March of the run year, with a deadline in the run year, is prior-cycle unless the ad itself says it is for the next academic year.
  A job board's listing expiry (Nature Careers, jobRxiv, and the like) is not a deadline; use `unknown` unless the ad itself states a date.
  Ads that survive with no stated deadline keep `deadline=unknown` and flag `deadline-unclear`; record posted date and start date in the notes so the reader can judge.
- Region: US, Europe (incl. UK, Switzerland, Nordics), and Asia (China, Hong Kong, Macau, Singapore).
- Agents verify each application URL loads (WebFetch); unverifiable or ambiguous entries are kept and flagged until the verify step, which may drop them.
- Time cap per agent: 30 minutes and at most 3 fetch attempts per site. A site that still does not respond is skipped, listed as a gap in the agent's summary, and never retried in that run. Sweep agents do not spawn sub-agents; they work their list sequentially so the parent can always return partial results.
- A branch campus or joint institute (HKUST(GZ), CUHK-Shenzhen, Tsinghua SIGS, ZJU-UIUC, NYU Abu Dhabi, and the like) counts only when `universities.md` lists it by name.
- No fabricated postings: every entry needs a real URL an agent actually visited.
- The application link points at the ad itself (or the university's application record), never at a search, category, or listing page. Dates and area lists come from the ad that is open now, not from a previous round or a news item about it.

## Self-check

`conda run -n base python merge.py --check` (no network, no file writes).

## References

- `universities.md`, `areas.md`, `template.html`, `merge.py`, `entries.json` in this skill directory.
- Boards: academicjobsonline.org, cra.org/ads, higheredjobs.com, jobs.ac.uk, academicpositions.com, jobs.nature.com.

## Failure modes

- **Board unreachable or blocks fetches**: note the gap in the user report; don't silently return fewer results.
- **Search agents return nothing**: the previous entries still carry over; the report is then the verified previous list, say so.
- **Snippet conflation**: a search snippet can splice dates from a postdoc ad onto last year's faculty round (seen with Imperial Computing, Sept 2026). The verify step catches this; a sweep agent that cannot open the ad must say so in the notes instead of filling fields from the snippet.
- **JS-only application pages**: Interfolio ads (`apply.interfolio.com/<id>`) render nothing in WebFetch; read the public JSON at `https://logic.interfolio.com/dossier-api/positions/<id>` (fields `start_date`, `end_date`, description). For bot-walled boards (HigherEdJobs, CRA) prefix the URL with `https://r.jina.ai/`.
- **Paginated boards**: CRA and jobs.ac.uk paginate with JavaScript; only the first page of a listing is readable, so lean on keyword searches.
- **August to early-fall runs**: faculty ads mostly appear Sept-Dec; a thin result set is expected, say so rather than padding with stale postings.
- **Same-day rerun**: overwrites today's file by design; warn only if the user expected an append.
- **Render fails**: keep the previous report; older files are deleted only after the new one is written.
- **University name mismatches** (e.g. "U. Michigan" vs "University of Michigan"): `merge.py` drops the entry and lists it; add the form to the `Aliases` column in `universities.md` when it names a listed university.
