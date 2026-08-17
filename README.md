# Composio App Research — AI Product Ops Take-Home

Research all 100 apps from the Composio take-home assignment with an agentic
pipeline: fetch each app's real docs, extract structured facts (auth, self-serve
access, API surface, MCP coverage, buildability), cluster the results into
patterns, verify accuracy on a 20-app sample, and cross-check coverage against
Composio's own catalog.

**Live case study:** `site/index.html` (self-contained single page, open in any browser)

## Repo layout

```
├── pipeline/            # the research pipeline
│   ├── fetch_docs.py        # HTTP fetch of docs for all 100 apps
│   ├── fetch_browser.py     # headless-browser fetch for JS-heavy pages
│   ├── html_to_text.py      # HTML → clean text
│   ├── normalize_and_merge.py  # → data/merged_final.json
│   ├── refine_blockers.py   # classify blockers into a taxonomy
│   ├── synthesize_patterns.py  # → data/patterns.json
│   ├── fix_categories.py    # normalize to canonical 10 categories + site_data.json
│   ├── build_site.py        # → site/index.html (the case study)
│   └── EXTRACT_INSTRUCTIONS.md  # schema/rules given to the extraction LLMs
├── verification/        # accuracy + Composio coverage
│   ├── select_verification_sample.py  # stratified 20-app sample
│   ├── write_verification.py          # per-app verification judgments
│   ├── compute_accuracy.py            # 67% → 86% numbers
│   ├── run_verification.py
│   └── analyze_coverage.py            # Composio catalog coverage audit (uses Composio SDK/MCP)
├── data/                # research output
│   ├── apps_input.json          # the 100 apps from the assignment
│   ├── rows/                    # one JSON row per app (extraction output)
│   ├── verification/            # per-app verification judgments
│   ├── merged_final.json        # the normalized 100-row dataset
│   ├── patterns.json            # pattern synthesis
│   ├── accuracy_progression.json# the 67% → 86% numbers
│   └── (raw_docs/, text/ — large caches, gitignored)
├── site/                # the deliverable (index.html)
├── docs/                # assignment PDF + internal PRD
└── requirements.txt
```

## Tooling used

- **Plain HTTP (`requests`)** — most docs pages
- **scrapling MCP + scrapling's DynamicFetcher (Playwright-backed)** — JS-heavy and
  lightly protected pages (Slack, Discord, Airtable, Linear, Meta docs, Snowflake, LiveAgent, PitchBook)
- **Playwright MCP** — interactive docs (Linear developer portal)
- **Chrome DevTools MCP** — Composio dashboard + final-page verification
- **Composio's own SDK / MCP** — `verification/analyze_coverage.py` queries the
  Composio catalog (via `composio search` / `connect.composio.dev/mcp`) to check
  which of the 100 apps Composio already ships toolkits for — a second,
  independent ground-truth source, and the brief's "use Composio's SDK/MCP" done
  for real.

## Run it

```bash
# 1. Install dependencies (Python 3.10+)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Fetch docs for all 100 apps (cached in data/raw_docs/)
python3 pipeline/fetch_docs.py          # simple HTTP
python3 pipeline/fetch_browser.py       # headless browser for JS-rendered pages

# 3. Convert + merge into one dataset
python3 pipeline/html_to_text.py
python3 pipeline/normalize_and_merge.py

# 4. Patterns + accuracy + site
python3 pipeline/synthesize_patterns.py
python3 pipeline/refine_blockers.py   # adds the blocker taxonomy to patterns.json
python3 verification/compute_accuracy.py
python3 pipeline/build_site.py          # writes site/index.html

# 5. (Optional) Composio catalog coverage audit
python3 verification/analyze_coverage.py  # needs Composio API key / CLI auth
```

The page is generated from the same JSON the pipeline outputs, so the page and
the data can never drift.

## Honesty notes

- Where an app is gated (DealCloud, PitchBook, Paygent Connect, iPayX, fanbasis,
  Consensus, NotebookLM), "gated / no public API" is reported as the finding —
  per the brief, that is correct, not a failure.
- Verification sample: 20 apps spanning all 10 categories, all confidence levels,
  and every hard/obscure app. Pass 1 (knowledge-only) scored 67%; after fetching
  real docs and browser re-checking, 86%. Remaining unknowns are marked honestly
  rather than guessed.

## Extending

Add a new app by appending to `data/apps_input.json` (num, name, hint), then
re-run the fetch + extract + build pipeline.
