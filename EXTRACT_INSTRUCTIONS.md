# Extraction Instructions for Research Subagent

You are a research extraction agent working on the Composio take-home assignment.
For each app assigned to you, produce a JSON row using the schema below.

## Your tools
- Read the app's fetched text: `data/text/NN_name.txt` (NN = app number).
  If the text is thin (<1200 chars), it's a JS-rendered shell — use your own
  knowledge of the app PLUS the evidence URL, and set `confidence` to "medium".
- If needed you may run `curl -s -L <url>` for a specific docs page to confirm a
  fact (auth method, self-serve status, MCP existence). Prefer confirming from
  the fetched text first.

## The schema (exact fields)

Write ONE JSON object per app to `data/rows/NN_name.json`:

```json
{
  "num": 1,
  "app": "App Name",
  "category": "Category Name",
  "one_line": "What it does in one sentence.",
  "auth_methods": ["OAuth2"],
  "auth_notes": "Details: OAuth2, API key, scopes, app registration needed, etc.",
  "self_serve": "yes|no|trial|paid|admin|partnership",
  "self_serve_notes": "Can a dev get credentials free/solo? What's required?",
  "gate_type": "none|paid_plan|admin_approval|contact_sales|partnership",
  "api_surface": {
    "protocol": ["REST", "GraphQL"],
    "breadth": "narrow|moderate|broad|very_broad",
    "breadth_estimate": "rough endpoint count or scope description",
    "webhooks": true,
    "webhook_note": "webhook support details if known"
  },
  "existing_mcp": {
    "official": true,
    "community": true,
    "note": "evidence of MCP server existence if found"
  },
  "buildability_verdict": "buildable_today|buildable_with_work|blocked",
  "blocker": null,
  "time_to_first_call": "minutes|hours|days|weeks",
  "evidence": {
    "docs": "the docs URL you consulted",
    "note": "how you found this (fetched text, browser, knowledge)"
  },
  "confidence": "high|medium|low",
  "tier": "B",
  "verification_status": "pass1",
  "agent_notes": "short note on any uncertainty"
}
```

## Rules
- BE HONEST. If you cannot determine a field from evidence, use your best
  knowledge and mark confidence low/medium. Never fabricate evidence URLs —
  only use URLs you actually consulted or that are the app's official docs.
- `self_serve`: "yes" = free self-serve, "trial" = free trial then paid,
  "paid" = requires paid plan, "admin" = needs org admin, "partnership" = needs
  partnership/sales.
- `buildability_verdict`: buildable_today (auth solvable + docs exist),
  buildable_with_work (some friction), blocked (no public API / totally gated).
- Write exactly one file per app to data/rows/. Report back the list of files
  you wrote and any apps you could not confidently extract.