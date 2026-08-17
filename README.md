# Composio App Research — AI Product Ops Take-Home

Research all 100 apps from the Composio take-home assignment with an agentic
pipeline: fetch each app's real docs, extract structured facts (auth, self-serve
access, API surface, MCP coverage, buildability), cluster the results into
patterns, and verify accuracy on a 20-app sample.

**Live case study:** `site/index.html` (self-contained single page, open in any browser)

## What the pipeline does

```
100 apps (data/apps_input.json)
   │
   ▼
fetch_docs.py ──► data/raw_docs/   (HTTP fetch, then headless browser for JS-heavy pages)
   │
   ▼
html_to_text.py ──► data/text/     (clean text per app)
   │
   ▼
LLM extraction ──► data/rows/      (one JSON row per app, guided by EXTRACT_INSTRUCTIONS.md)
   │
   ▼
normalize_and_merge.py ──► data/merged_final.json   (100-row normalized dataset)
   │
   ▼
synthesize_patterns.py ──► data/patterns.json       (auth, gates, blockers, MCP, easy wins)
   │
   ▼
select_verification_sample.py + compute_accuracy.py ──► data/accuracy_progression.json
   │                                                     (67% → 86% on 20-app sample)
   ▼
build_site.py ──► site/index.html   (the case study page)
```

## Run it

```bash
# 1. Install dependencies (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Fetch docs for all 100 apps (cache in data/raw_docs/)
python3 fetch_docs.py          # simple HTTP; retries skipped cached files
python3 fetch_browser.py       # headless browser for JS-rendered pages (Slack, Discord, etc.)

# 3. Convert to text + merge into one dataset
python3 html_to_text.py
python3 normalize_and_merge.py

# 4. Regenerate the case study page
python3 build_site.py          # writes site/index.html

# 5. Recompute the verification numbers
python3 compute_accuracy.py
```

## Structure

- `data/apps_input.json` — the 100 apps from the assignment (10 categories)
- `data/raw_docs/` — cached HTML per app
- `data/text/` — cleaned text per app
- `data/rows/` — one JSON row per app (extraction output)
- `data/merged_final.json` — the normalized 100-row dataset feeding the page
- `data/verification/` — per-app verification judgments
- `data/accuracy_progression.json` — the 67% → 86% numbers
- `data/patterns.json` — the pattern synthesis
- `site/index.html` — the case study (self-contained)
- `EXTRACT_INSTRUCTIONS.md` — the schema and rules given to the extraction agents

## Honesty notes

- Where an app is gated (DealCloud, PitchBook, Paygent Connect, iPayX, fanbasis,
  Consensus, NotebookLM), "gated / no public API" is reported as the finding —
  per the brief, that is correct, not a failure.
- Verification sample: 20 apps spanning all 10 categories, all confidence levels,
  and every hard/obscure app. Pass 1 (knowledge-only) scored 67%; after fetching
  real docs and browser re-checking, 86%. The remaining unknowns are marked
  honestly rather than guessed.

## Extending

Add a new app by appending to `data/apps_input.json` (num, name, hint), then
re-run the fetch + extract + build pipeline. The page is generated from the same
JSON the pipeline outputs, so the page and the data can never drift.