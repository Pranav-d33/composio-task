# PRD — Composio AI Product Ops Intern Take-Home
### Agentic research pipeline across 100 apps + verified case study page

**Owner:** Pranav Dhiran
**Budget:** 6–8 hours, submit early
**Status:** Planning → build

---

## 1. What's actually being evaluated

The brief reads like a data task. It isn't. Composio's own copy tells you what they're filtering for:

- "Doing it by hand does not scale" → **can you build the thing, not just use the thing.**
- "Using Composio's own SDK and MCP to build it is in the spirit of the role" → **do you reach for their product as a builder would, not just as a user.**
- "Accuracy is what matters most" + a whole paragraph on verification loops → **do you know your agent is wrong before a human tells you, and can you show the delta.**
- "If the agent got things wrong or an app defeated you, say so" → **honesty under a false-confidence trap.** Most candidates will submit 100 clean rows. A pipeline that admits failure on 6–10 apps is more credible, not less.
- "A reviewer understands it in about two minutes with no narration" → **this is a comms/clarity test as much as a technical one**, which is the actual job (AI *Product Ops*, not AI research).

The scoring is probably weighted: verification rigor > pattern insight > pipeline design > raw row accuracy > polish.

---

## 2. The core insight the pipeline is built around

Composio already has a **live catalog of 1000+ toolkits**, queryable via their own API:

- `GET /api/v3/toolkits` / `composio.toolkits.get()` — list + filter by category
- `GET /api/v3.1/toolkits/{slug}` / `composio.toolkits.get(slug)` — per-toolkit detail: `authConfigDetails[]` (OAUTH2 / API_KEY / BEARER_TOKEN / BASIC), whether it ships **managed auth** (Composio hosts the OAuth app → zero-setup self-serve signal), `categories[]`, description
- `composio.toolkits.listCategories()` — canonical category taxonomy
- `GET /api/v3/tools?toolkit_slug=X` — tool count per toolkit → direct proxy for API-surface breadth
- `composio.mcp.list(toolkits=...)` — whether an MCP server config already exists

**Implication:** for every app in the 100 that already has a Composio toolkit, we don't need an LLM to *guess* auth method or self-serve status — we can pull it straight from Composio's production API. That's ground truth, not inference. This becomes the spine of the whole design: split the 100 into two tiers with two different pipelines and two different trust levels, and make that split the headline finding.

---

## 3. Data schema (per app row)

| Field | Source | Notes |
|---|---|---|
| `app_name`, `category` | input list | as given in the assignment |
| `one_line_description` | Tier A: Composio `description` / Tier B: agent | |
| `auth_methods[]` | Tier A: `authConfigDetails` / Tier B: agent + docs | OAuth2, API key, Basic, token, other |
| `self_serve` | Tier A: managed-auth flag / Tier B: agent judgment | free/trial vs paid-plan vs admin-approval vs partner/sales-gate |
| `gate_type` | derived | none / paid-plan / approval / contact-sales |
| `api_surface` | Tier A: tool count from `/tools` / Tier B: docs review | REST/GraphQL, rough breadth (narrow/moderate/broad) |
| `existing_mcp` | Tier A: `mcp.list()` / Tier B: docs search | yes/no/unknown |
| `buildability_verdict` | derived | buildable today / buildable with auth workaround / blocked |
| `blocker` | derived | only if not cleanly buildable |
| `evidence_url` | both | docs page actually consulted |
| `tier` | pipeline | A (Composio-verified) / B (agent-researched) |
| `confidence` | pipeline | high/med/low — low triggers Pass 3 |
| `verification_status` | pipeline | pass1-only / pass2-corrected / human-checked / insufficient-info |

`insufficient-info` is a legitimate value, not a failure state — the brief says so explicitly for gated/thin-docs apps.

---

## 4. System architecture

```
100 apps (parsed from PDF)
        │
        ▼
 Tier classifier ── query Composio catalog by name + known aliases
        │
   ┌────┴────┐
   ▼         ▼
 Tier A    Tier B
(match)   (no match)
   │         │
   │         ▼
   │    Pass 1: naive LLM + single web search → draft row
   │         │
   │         ▼
   │    Pass 2: agent fetches the actual docs URL (web_fetch/browse),
   │            extracts auth/pricing/API claims, diffs vs Pass 1,
   │            corrects with citation
   │         │
   │         ▼
   │    Pass 3: only for low-confidence / Pass1↔Pass2 disagreement —
   │            second independent source, or explicit
   │            "insufficient public info" marking
   │         │
   ▼         ▼
 composio.toolkits.get(slug)   merged, tiered dataset (JSON)
 → auth, managed-auth flag,          │
   category, tool count, MCP         ▼
        │                    Human sample audit (~15–20 apps,
        └───────► merge ◄────  stratified across tier + category)
                     │         → per-field agreement logged at
                     ▼           Pass 1 vs Pass 2/3 vs human
             Pattern synthesis
             (auth mix, self-serve/gated by category,
              common blockers, easy-wins vs outreach-needed)
                     │
                     ▼
             Single HTML case study page
```

### 4.1 Tier A — Composio-native pipeline
For each app, resolve to a Composio toolkit slug (exact name match first, then fuzzy/alias match — e.g. "Zoho CRM" → `zoho_crm` or similar). On match: pull `authConfigDetails`, managed-auth flag, `categories`, tool count, MCP presence directly. No LLM inference on these fields — the row is stamped `tier: A`, `verification_status: composio-verified`. This is the fastest, most trustworthy chunk of the dataset and should be visually distinguished on the final page (e.g., a badge), because it's the strongest, most defensible claim in the whole submission.

### 4.2 Tier B — agentic research pipeline
Apps with no Composio toolkit (expect this to include the thin/obscure ones by design — Paygent Connect, iPayX, fanbasis, Waterfall.io, DealCloud, higgsfield, Sherlock, etc.). Three-pass loop:

- **Pass 1 (fast, cheap):** LLM answers from general knowledge + a single web search per app. This is the intentionally weak baseline — its accuracy number is the "before."
- **Pass 2 (grounded correction):** agent fetches the actual docs URL given in the assignment table (plus 1–2 more if the given URL is thin), extracts the specific claims (auth type, pricing/access tier, API format), and corrects Pass 1 field-by-field with a citation. This is where most of the accuracy gain should come from.
- **Pass 3 (targeted re-verification):** only runs where Pass 1 and Pass 2 disagreed, or confidence is low. Either a second independent source is fetched, or the row is explicitly marked `insufficient-info` — never silently guessed.

### 4.3 Human verification layer
Stratified random sample of ~15–20 apps (mix of Tier A/B, mix of categories, deliberately including a few of the hard/obscure ones). Hand-check each field against the real docs. Log agreement at each stage:

`Pass 1 raw accuracy` → `Pass 2 corrected accuracy` → `Final (Pass 3 + human-reconciled) accuracy`

This three-number progression is the single most important artifact in the whole submission — it's the direct, literal answer to "show how accuracy moved from a lower first pass to a higher one."

---

## 5. Tech stack

- **Composio Python SDK** (`composio`) — Tier A ground truth, and as the tool layer for Tier B's agent (rather than raw `requests` calls, to actually be "in the spirit of the role")
- **Web search/fetch tools** for Tier B research — Composio-connected search/scrape toolkit (e.g. Firecrawl, DataForSEO — both are in the assignment's own app list, nice self-referential touch) or Claude's native web tools if simpler to wire up in the time budget
- **JSON** as the single intermediate data store (one row per app, matches the schema above) — this is what both the human-audit script and the HTML renderer read from
- **Static HTML/CSS/vanilla JS** for the deliverable — a filterable/sortable table, not a framework build, to keep it a single self-contained file
- **Deploy:** Vercel or GitHub Pages for the live link (fast, free, no backend needed since the page just renders a static JSON snapshot)

---

## 6. Repo structure

```
composio-app-research/
├── README.md                 ← how to run it, API keys needed, runtime
├── data/
│   ├── apps_input.json       ← the 100 apps, parsed from the PDF
│   ├── tier_a_output.json    ← Composio-verified rows
│   ├── tier_b_pass1.json     ← naive baseline (kept, for the accuracy story)
│   ├── tier_b_pass2.json     ← corrected rows
│   ├── tier_b_pass3.json     ← re-verified / insufficient-info rows
│   ├── merged_final.json     ← full 100-row dataset feeding the page
│   └── human_audit.json      ← sample checks + per-field agreement log
├── pipeline/
│   ├── classify_tier.py
│   ├── tier_a_composio.py
│   ├── tier_b_agent.py       ← pass 1 + pass 2 + pass 3 logic
│   └── synthesize_patterns.py
├── audit/
│   └── human_audit.py        ← script that logs hand-checks + computes agreement %
└── site/
    └── index.html            ← the single-page deliverable
```

README covers: API keys needed (Composio, LLM provider, search tool), one command to run the full pipeline end-to-end, one command to regenerate the HTML from `merged_final.json`, and where the human-audit numbers come from.

---

## 7. The HTML deliverable — section order (two-minute skim test)

1. **Headline** (top, 2–3 sentences, no scrolling): the split (e.g. "X/100 apps already exist as Composio toolkits — for those we queried, not guessed"), auth method that dominates, self-serve vs gated split, most common blocker.
2. **Findings matrix**: clean, filterable/sortable table — filter by category, tier, buildability verdict.
3. **Patterns**: 4–6 concrete clustered insights (not adjectives) — auth distribution, self-serve/gated by category, easy-wins list vs needs-outreach list.
4. **The agent**: what it does, the 2-tier/3-pass architecture in one diagram, where a human was needed and why (name the specific apps).
5. **Verification**: the 3-number accuracy progression, a visible hits/misses table for the sampled apps, honest about what was still wrong after all passes.
6. **Proof**: link to the repo, and either a live runnable trigger or an embedded run log.

---

## 8. Timeline (8-hour budget, with buffer)

| Time | Task |
|---|---|
| 0:00–0:30 | Parse 100 apps from PDF into structured JSON with categories; repo scaffold; Composio API key set up |
| 0:30–1:30 | Tier classifier: match all 100 against Composio catalog by name/alias; hand-review ambiguous matches |
| 1:30–2:30 | Tier A extraction: pull full toolkit detail for every matched app |
| 2:30–4:30 | Tier B pipeline: Pass 1 + Pass 2 across unmatched apps |
| 4:30–5:30 | Tier B Pass 3: targeted re-verification on flagged/low-confidence rows |
| 5:30–6:30 | Human sample audit (~15–20 apps) + compute accuracy at each pass |
| 6:30–7:30 | Pattern synthesis + build the HTML page |
| 7:30–8:00 | Deploy, write README, final QA pass, submit |

---

## 9. Risk register

| Risk | Mitigation |
|---|---|
| Composio catalog match is wrong (slug mismatch, e.g. "Zoho CRM" vs "Zoho") | Fuzzy match + manual review pass on all Tier A matches before trusting them |
| Composio's own category taxonomy doesn't map 1:1 to the assignment's 10 categories | Keep the assignment's categories as the primary axis; treat Composio categories as a secondary tag, note the mismatch openly if it's a real pattern |
| Some apps genuinely have near-zero public docs (Paygent Connect, iPayX, fanbasis, Waterfall.io) | Expected — mark `insufficient-info` with evidence of the search attempt, report as a finding, not hidden |
| Rate limits / API quota during Tier B fetch passes | Batch requests, cache fetched pages, budget time accordingly in hours 2:30–5:30 |
| Running out of time before human audit | Human audit is non-negotiable per the brief ("accuracy is what matters most") — protect this time block even if Tier B Pass 3 gets cut short |

---

## 10. Why this stands out (explicit differentiation)

- **Ground-truth tier, not guesswork everywhere.** Most submissions will run one LLM pass over all 100 apps uniformly. Splitting into Composio-verified vs agent-researched is a structurally different (and more honest) approach, and it's the one thing genuinely unique to being evaluated *by Composio*.
- **A real, numeric accuracy story**, not a claim of accuracy. Three concrete numbers (Pass 1 → Pass 2 → final), computed against a real hand-checked sample.
- **Failures shown, not smoothed over.** A visible "here's where the agent got it wrong / where an app defeated it" section is a stronger trust signal than a spotless 100-row table.
- **Built with their own SDK as a tool layer**, not just cited as a nice-to-have.
- **Two-minute-skim page.** Headline pattern first, no narration needed — matches their own instruction to the letter.

---

## 11. Assumptions / open questions

- Assuming a Composio API key is available (free tier should cover read-only catalog queries + a small number of Tier A calls).
- No paid accounts for any of the 100 apps — gated apps are reported as gated with evidence, per the brief.
- Assuming Tier A/B split will land roughly 30–50% Tier A given the app list mixes major SaaS (likely covered) with niche/new tools (likely not covered) — this ratio itself is a finding worth reporting, not just a pipeline detail.
