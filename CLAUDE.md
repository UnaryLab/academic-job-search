# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A single Claude Code skill (`/academic-job-search`) that finds open faculty positions and renders a dated HTML report. There is no application code beyond `merge.py`; the "program" is the skill workflow in `.claude/skills/academic-job-search/SKILL.md`, which dispatches parallel search agents, merges their JSON, verifies entries, and renders `output/jobs-YYYY-MM-DD.html`. Read SKILL.md first for any change to the search behaviour.

## Commands

All Python runs through the `base` conda env; there is no bare `python` on PATH.

```sh
# self-check of merge.py (no network, no writes); run after any merge.py or template change
cd .claude/skills/academic-job-search && conda run -n base python merge.py --check

# render a report from a directory of agent JSON files (rewrites entries.json and output/)
conda run -n base python merge.py --date 2026-09-12 --in-dir <dir> --gaps <dir>/gaps.json
#   --no-save        keep entries.json untouched (dry run)
#   --out-dir <dir>  render somewhere other than output/
#   --min-rank X     override the Minimum rank row of rank.md

# syntax-check the report's inline script after editing template.html
sed -n '/<script>/,/<\/script>/p' output/jobs-*.html | sed '1d;$d' > /tmp/page.js && node --check /tmp/page.js
```

The full search is run by invoking the skill, not by a command; it needs a fresh session because WebSearch is capped per session (200 calls, shared by every subagent).

## Architecture

**User inputs live at the repo root** and drive everything: `areas.md` (area keys, search terms, adjacent fields, units to check, excluded units), `universities.md` (canonical names, country, region, aliases), `rank.md` (the `Minimum rank` row plus the title-to-rank mapping). `merge.py` reads all three via `ROOT`; SKILL.md tells agents to read them. Do not hardcode areas, regions, departments, or ranks anywhere else.

**Data flow per run** (SKILL.md "Workflow"):
1. The parent copies `entries.json` to `<dir>/00-previous.json` and dispatches board agents (one per job board) plus sweep agents (about 30 universities each). Each writes a JSON array of entries with the 15 fields in `FIELDS`.
2. `merge.py` matches `university` against `universities.md` (normalized exact match on name or alias, never fuzzy), drops branch campuses (`BRANCH_MARKERS`), drops ranks above the minimum, dedupes within a university (`same_posting`: link key or title-token Jaccard), keeps the higher-scoring copy (`score`: university link beats board mirror, dated deadline beats rolling, flag ok beats flagged), and sorts (`sort_key`: dated first, then rolling, then unknown; flagged rows after ok rows).
3. Verify step: the parent selects entries (all previous ones with `verified` below 2 and not checked on the run date; new ones with board links, missing dates, or `unverified`), dispatches verifier agents, applies their `confirmed`/`corrected`/`drop` verdicts to the JSON files, and bumps `verified` on every kept entry whose ad loaded.
4. Render: `render()` fills `template.html` markers (`<!--DATE-->`, `<!--COUNT-->`, `<!--AREAS-->`, `<!--OPTIONS-->`, `<!--ROWS-->`, `<!--GAPS-->`), writes `output/jobs-<date>.html`, deletes every other file in `output/`, and rewrites `entries.json`.

**Template contract** (`render()` and `template.html` must agree): each row is `<tr class="flagged"? data-area="..." data-region="...">` with 15 `<td>` cells in the order listed in SKILL.md's output contract; the page JS styles cells by index (pills, urgency, clamping, compact-mode hidden columns), so reordering `cells` in `render()` means updating every nth-child rule and cell index in the template, and the contract sentence in SKILL.md. The area, region, and university dropdowns are built from the `<!--OPTIONS-->` JSON (`filter_options()`), not from the rows.

**State between runs** is only `entries.json` (with the per-entry `verified` count) and the newest report. Scratch files for a run (agent JSON, gaps, verify outputs) live in the session scratchpad, never in the repo.

## Conventions specific to this repo

- `check()` in merge.py is the only test; extend it when you change matching, dedupe, sorting, rank filtering, or gap rows. It must stay network-free.
- Every change to `merge.py`, `template.html`, or the md inputs is followed by `--check` and a re-render of the current report so `output/` and `entries.json` stay consistent with the code.
- Agent briefs written for a run restate the rules from SKILL.md, `areas.md`, and `rank.md`; when those files change, the brief changes with them.
- No em-dashes in any file, including page text and agent prompts.
