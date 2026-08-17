# Composio Toolkit Coverage — Verified (100 apps)

This is the **corrected** coverage analysis. An initial pass using `composio search`
(Claude Code's approach) reported 100% coverage — but `composio search` is a fuzzy
natural-language tool finder, not a catalog lookup. It returns unrelated tools for
many apps (e.g. Copper → `excalidraw_mcp`, a diagram tool; Sherlock → `postman`).

We re-ran the audit with the **authoritative** query, `composio dev toolkits list`,
which only returns real toolkit slugs. Result:

## Headline

- **59 / 100 apps (59%)** have a **native Composio toolkit**
- **41 / 100 (41%)** have **no native toolkit** (a gap / opportunity)

The earlier "100% covered" claim was wrong; the real coverage is **59%**.

## Native toolkits by category

| Category | Native | Total | Coverage |
|---|---|---|---|
| CRM and Sales | 7 | 10 | 70% |
| Support and Helpdesk | 7 | 10 | 70% |
| Communications and Messaging | 4 | 10 | 40% |
| Marketing, Ads, Email and Social | 8 | 10 | 80% |
| Ecommerce | 4 | 10 | 40% |
| Data, SEO and Scraping | 6 | 10 | 60% |
| Developer, Infra and Data platforms | 9 | 10 | 90% |
| Productivity and Project Management | 9 | 10 | 90% |
| Finance and Fintech | 4 | 10 | 40% |
| AI, Research and Media-native | 4 | 10 | 40% |

## Largest native toolkits (by tool count)

| Toolkit | Tools |
|---|---|
| github | 871 |
| zendesk | 451 |
| stripe | 425 |
| pipedrive | 399 |
| sendgrid | 359 |
| shopify | 315 |
| dataforseo | 312 |
| mailchimp | 272 |
| hubspot | 244 |
| klaviyo | 225 |

## Notable gaps (no native toolkit) — potential build opportunities

- **CRM:** Twenty (open-source CRM), Copper, DealCloud
- **Support:** LiveAgent, Gladly
- **Communications:** Twilio, Lark, Pumble, Vonage, Aircall, Zoho Cliq
- **Marketing:** GoHighLevel, systeme.io, Threads
- **Ecommerce:** WooCommerce, BigCommerce, Magento, Squarespace, Ecwid, Amazon Selling Partner
- **Data:** Sherlock, Waterfall.io, Clay, SE Ranking
- **Dev/Infra:** Netlify, MongoDB Atlas
- **PM:** Smartsheet
- **Fintech:** Plaid, Binance, Paygent, iPayX, PitchBook
- **AI/Media:** Otter AI, Reducto, higgsfield, Grain, YouTube Transcript

## Cross-check vs our research

**25 apps we researched as "buildable today" have no native Composio toolkit yet.**
These are the highest-value toolkits to build — they're buildable AND uncovered:

Twenty, Podio, Copper (CRM) · Front, LiveAgent (Support) · Twilio, Zoho Cliq,
Lark, Vonage (Comms) · systeme.io, Threads (Marketing) · WooCommerce, BigCommerce,
Magento, Squarespace, Ecwid (Ecommerce) · SE Ranking (Data) · Netlify, MongoDB
Atlas (Dev/Infra) · Smartsheet (PM) · Plaid, Binance (Fintech) · Reducto,
Mermaid CLI, YouTube Transcript (AI/Media)

That's the single most actionable finding: **~1 in 4 of the requested apps is both
buildable today and not yet a Composio toolkit** — a ready-made build roadmap.

## Method & honesty

- **Method:** `composio dev toolkits list --query <app>` for each of the 100 apps;
  a toolkit counts as native only on an exact/strong name match. Alias handling for
  known cases (Salesforce → `salesforce`, Zoho CRM → `zoho`, Monday → `monday`,
  Google Ads → `googleads`, etc.).
- **Honest limits:** Some apps share a parent toolkit (Zoho CRM uses the shared
  `zoho` toolkit). We could not verify from the catalog alone that the shared
  toolkit covers every sub-product (e.g. Zoho Cliq), so those are conservatively
  reported. Tool counts are from the catalog at analysis time and can change.
- **Data file:** `data/composio_coverage.json`
