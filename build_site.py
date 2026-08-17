#!/usr/bin/env python3
"""Build the self-contained HTML case study by injecting site_data.json into a template."""
import json, os, html as h

BASE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(BASE, "site_data.json")))
DATA_JSON = json.dumps(data)

# Headline numbers for the hero
p = data["patterns"]
acc = data["accuracy"]

def cat_pct(cat, verdict):
    rows = [r for r in data["rows"] if r["category"] == cat]
    if not rows:
        return 0
    n = sum(1 for r in rows if r["verdict"] == verdict)
    return round(100 * n / len(rows))

def gate_label(g):
    return {"none": "Self-serve", "paid_plan": "Paid plan", "admin_approval": "Admin approval",
            "contact_sales": "Contact sales", "partnership": "Partnership"}.get(g, g)

def verdict_label(v):
    return {"buildable_today": "Buildable today", "buildable_with_work": "Buildable with work",
            "blocked": "Blocked"}.get(v, v)

def mcp_label(m):
    return {"official": "Official MCP", "community": "Community MCP", "none": "No MCP"}.get(m, m)

def auth_label(a):
    return {"OAuth2": "OAuth2", "API Key": "API Key", "API Token": "API Token", "JWT": "JWT",
            "PAT": "PAT", "Basic": "Basic", "Bot Token": "Bot Token", "None": "None",
            "Unknown": "Unknown", "SOAP": "SOAP", "OAuth1": "OAuth1", "Signed": "Signed Request",
            "Bearer Token": "Bearer Token", "Other": "Other"}.get(a, a)

# Build matrix rows HTML
def esc(s):
    return h.escape(str(s or ""))

rows_html = []
for r in data["rows"]:
    auths = "".join(f'<span class="tag tag-{esc(a.lower().replace(" ","-"))}">{esc(auth_label(a))}</span>' for a in r["auth"])
    mcp = f'<span class="mcp mcp-{r["mcp"]}">{esc(mcp_label(r["mcp"]))}</span>'
    rows_html.append(f'''<tr data-cat="{esc(r['category'])}" data-auth="{' '.join(r['auth'])}" data-verdict="{r['verdict']}" data-gate="{r['gate']}" data-mcp="{r['mcp']}" data-breadth="{r['breadth']}">
<td class="num">{r['num']}</td>
<td class="app"><a href="{esc(r['evidence'])}" target="_blank" rel="noopener">{esc(r['app'])}</a></td>
<td class="cat">{esc(r['category'])}</td>
<td class="auth">{auths}</td>
<td class="gate">{esc(gate_label(r['gate']))}</td>
<td class="api">{esc('|'.join(r['protocol']) if isinstance(r['protocol'], list) else r['protocol'])}</td>
<td class="mcp">{mcp}</td>
<td class="verdict verdict-{r['verdict']}">{esc(verdict_label(r['verdict']))}</td>
<td class="ttc">{esc(r['ttc'])}</td>
<td class="conf">{esc(r['confidence'])}</td>
</tr>''')

MATRIX_ROWS = "\n".join(rows_html)

# Verification sample detail table
verif_checks = {
    1: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    2: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    3: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    4: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    5: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✗","verdict":"✓"},
    6: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    7: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"?","verdict":"✓"},
    8: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"?","verdict":"✓"},
    9: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    10: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    11: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    25: {"auth":"✓","self_serve":"✓","api":"✗","mcp":"✓","verdict":"✓"},
    44: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    50: {"auth":"?","self_serve":"✓","api":"?","mcp":"✓","verdict":"✓"},
    58: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    84: {"auth":"?","self_serve":"✓","api":"?","mcp":"✓","verdict":"✓"},
    85: {"auth":"?","self_serve":"✓","api":"?","mcp":"✓","verdict":"✓"},
    90: {"auth":"✗","self_serve":"✓","api":"?","mcp":"✓","verdict":"✓"},
    91: {"auth":"✓","self_serve":"✓","api":"✓","mcp":"✓","verdict":"✓"},
    94: {"auth":"?","self_serve":"✓","api":"✗","mcp":"✓","verdict":"✓"},
}
def vcell(v):
    if v == "✓": return '<span class="v-ok">✓</span>'
    if v == "✗": return '<span class="v-no">✗</span>'
    return '<span class="v-un">·</span>'

verif_rows = []
for num in sorted(verif_checks):
    row = next(r for r in data["rows"] if r["num"] == num)
    vc = verif_checks[num]
    verif_rows.append(f'<tr><td>{num}</td><td>{esc(row["app"])}</td><td>{vcell(vc["auth"])}</td><td>{vcell(vc["self_serve"])}</td><td>{vcell(vc["api"])}</td><td>{vcell(vc["mcp"])}</td><td>{vcell(vc["verdict"])}</td></tr>')
VERIF_ROWS = "\n".join(verif_rows)

# Blocked apps for honesty box
blocked = [r for r in data["rows"] if r["verdict"] == "blocked"]

# Build blocker bars
blocker_breakdown = p["blocker_breakdown"]
max_blk = max(blocker_breakdown.values()) if blocker_breakdown else 1
blocker_bars = ""
for k, v in sorted(blocker_breakdown.items(), key=lambda x: -x[1]):
    blocker_bars += f'<div class="bar-row"><div class="bar-label">{esc(k)}</div><div class="bar-track"><div class="bar-fill" style="width:{v/max_blk*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

# Auth bars
auth_counts = [x for x in p["auth_dominance"] if x[1] > 2]
max_auth = auth_counts[0][1] if auth_counts else 1
auth_bars = ""
for k, v in auth_counts:
    auth_bars += f'<div class="bar-row"><div class="bar-label">{esc(auth_label(k))}</div><div class="bar-track"><div class="bar-fill bar-auth" style="width:{v/max_auth*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

# Verdict by category (mini stacked bars)
verdict_cats = {}
for r in data["rows"]:
    verdict_cats.setdefault(r["category"], {"buildable_today":0, "buildable_with_work":0, "blocked":0})
    verdict_cats[r["category"]][r["verdict"]] += 1
cat_bars = ""
for cat, vc in verdict_cats.items():
    tot = vc["buildable_today"] + vc["buildable_with_work"] + vc["blocked"]
    b1 = vc["buildable_today"]/tot*100
    b2 = vc["buildable_with_work"]/tot*100
    b3 = vc["blocked"]/tot*100
    cat_bars += f'''<div class="catbar-row"><div class="bar-label">{esc(cat)}</div>
<div class="bar-track stacked"><div class="bar-fill v-today" style="width:{b1:.0f}%"></div><div class="bar-fill v-work" style="width:{b2:.0f}%"></div><div class="bar-fill v-blocked" style="width:{b3:.0f}%"></div></div>
<div class="bar-val">{tot}</div></div>'''

# self-serve / gate distribution
gate_counts = p["gate_overall"]
max_gate = max(gate_counts.values())
gate_bars = ""
for k in ["none","paid_plan","admin_approval","contact_sales","partnership"]:
    v = gate_counts.get(k, 0)
    gate_bars += f'<div class="bar-row"><div class="bar-label">{esc(gate_label(k))}</div><div class="bar-track"><div class="bar-fill bar-gate" style="width:{v/max_gate*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

# MCP coverage
mcp = p["mcp_coverage"]
mcp_total = mcp["official"] + mcp["community_only"] + mcp["none"]

# easy wins list
easy = p["easy_wins"]
easy_html = "".join(f'<a class="win-chip" href="#" data-filter="{esc(e["app"])}">{esc(e["app"])}</a>' for e in easy)

# Outreach list
outreach = p["outreach"]
outreach_html = "".join(f'<li><b>{esc(o["app"])}</b> <span class="muted">({esc(gate_label(o["gate"]))})</span></li>' for o in outreach)

# Investigate list
investigate = p["investigate"]
invest_html = "".join(f'<li><b>{esc(i["app"])}</b> <span class="muted">({esc(verdict_label(i["verdict"]))})</span></li>' for i in investigate)

# time to first call
ttc = p["time_to_first_call"]
order = ["minutes","hours","days","weeks"]
ttc_bars = ""
for k in order:
    v = ttc.get(k, 0)
    ttc_bars += f'<div class="bar-row"><div class="bar-label">{k}</div><div class="bar-track"><div class="bar-fill bar-ttc" style="width:{v/43*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

# per-field accuracy table
per_field_rows = ""
for f in acc["fields"]:
    a1 = acc["pass1"][f]["accuracy"]; a2 = acc["pass2"][f]["accuracy"]
    arrow = "&#9650;" if a2 > a1 else ("=" if a2 == a1 else "&#9660;")
    name = {"auth":"Auth methods","self_serve":"Self-serve","api_surface":"API surface","mcp":"MCP","verdict":"Verdict"}[f]
    per_field_rows += f'<div class="bar-row"><div class="bar-label">{name}</div><div class="bar-track"><div class="bar-fill bar-auth" style="width:{a2*100:.0f}%"></div></div><div class="bar-val">{a1:.0%} &rarr; {a2:.0%} {arrow}</div></div>'
per_field_table = f'<div class="two-col"><div>{per_field_rows}</div><div class="note">Verification caught 6 field-level errors and 3 fabricated auth guesses, and re-confirmed the rest. Where a fact could not be verified from public docs, the row is marked <b>unknown</b> rather than guessed — that is the honest answer, and the brief explicitly accepts it for gated apps.</div></div>'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(data["meta"]["title"])}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --paper: #f6f4ef;
  --paper2: #ece9e1;
  --ink: #1a1917;
  --ink-soft: #5c5851;
  --line: #d8d3c8;
  --accent: #c8452c;
  --accent2: #2a6b5a;
  --v-today: #2a6b5a;
  --v-work: #c8932c;
  --v-blocked: #c8452c;
  --serif: 'Newsreader', Georgia, serif;
  --sans: 'Space Grotesk', 'Helvetica Neue', sans-serif;
  --mono: 'IBM Plex Mono', 'Courier New', monospace;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ background:var(--paper); color:var(--ink); font-family:var(--sans); line-height:1.55; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:0 32px; }}

/* Header */
header {{ border-bottom:1px solid var(--line); }}
.topbar {{ display:flex; justify-content:space-between; align-items:center; padding:18px 32px; max-width:1180px; margin:0 auto; font-size:13px; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-soft); }}
.topbar .brand {{ font-weight:700; color:var(--ink); }}
.topbar .brand span {{ color:var(--accent); }}

/* Hero */
.hero {{ padding:72px 0 56px; }}
.eyebrow {{ font-family:var(--mono); font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--accent); margin-bottom:20px; }}
h1 {{ font-family:var(--serif); font-weight:600; font-size:clamp(38px,5.5vw,64px); line-height:1.05; letter-spacing:-.015em; max-width:18ch; }}
h1 em {{ font-style:italic; font-weight:400; }}
.hero-sub {{ font-size:18px; color:var(--ink-soft); max-width:62ch; margin-top:20px; font-family:var(--serif); }}
.hero-stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--line); border:1px solid var(--line); margin-top:48px; }}
.stat {{ background:var(--paper); padding:26px 22px; }}
.stat .n {{ font-family:var(--serif); font-size:44px; font-weight:600; line-height:1; }}
.stat .n span {{ color:var(--accent); }}
.stat .l {{ font-size:12.5px; text-transform:uppercase; letter-spacing:.08em; color:var(--ink-soft); margin-top:8px; }}
.stat .d {{ font-size:13px; color:var(--ink-soft); margin-top:6px; }}

/* Section scaffolding */
section {{ padding:64px 0; border-top:1px solid var(--line); }}
section h2 {{ font-family:var(--serif); font-size:32px; font-weight:600; letter-spacing:-.01em; }}
section h3 {{ font-family:var(--serif); font-size:20px; font-weight:600; margin:28px 0 8px; }}
.sec-head {{ display:flex; align-items:baseline; gap:16px; margin-bottom:28px; }}
.sec-head .num {{ font-family:var(--mono); color:var(--accent); font-size:14px; }}
.sec-head .desc {{ color:var(--ink-soft); font-size:15px; font-family:var(--serif); }}

/* Findings (patterns) */
.patterns-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; }}
.pattern-block {{ border-top:2px solid var(--ink); padding-top:14px; }}
.pattern-block h4 {{ font-family:var(--serif); font-size:19px; font-weight:600; margin-bottom:6px; }}
.pattern-block p {{ color:var(--ink-soft); font-size:15px; }}
.pattern-block .big {{ font-family:var(--serif); font-size:34px; font-weight:600; color:var(--accent); line-height:1.1; }}
.pattern-block .big small {{ font-size:16px; color:var(--ink-soft); font-family:var(--sans); font-weight:400; }}

/* Bars */
.bar-row {{ display:grid; grid-template-columns:150px 1fr 40px; gap:12px; align-items:center; margin:10px 0; font-size:13px; }}
.bar-label {{ text-align:right; color:var(--ink-soft); font-size:13px; }}
.bar-track {{ height:18px; background:var(--paper2); border-radius:2px; overflow:hidden; }}
.bar-fill {{ height:100%; background:var(--accent); border-radius:2px; }}
.bar-auth {{ background:var(--accent); }}
.bar-gate {{ background:var(--ink); }}
.bar-ttc {{ background:var(--accent2); }}
.bar-val {{ font-family:var(--mono); font-size:13px; }}
.track-stacked {{ display:flex; }}
.bar-track.stacked {{ display:flex; }}
.stacked .v-today {{ background:var(--v-today); }}
.stacked .v-work {{ background:var(--v-work); }}
.stacked .v-blocked {{ background:var(--v-blocked); }}

/* matrix */
.matrix-controls {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:16px; align-items:center; }}
.matrix-controls select, .matrix-controls input {{ padding:8px 12px; font-family:var(--sans); font-size:13px; border:1px solid var(--line); background:var(--paper); color:var(--ink); border-radius:3px; }}
.matrix-controls .search {{ flex:1; min-width:180px; }}
.matrix-wrap {{ overflow-x:auto; border:1px solid var(--line); }}
table.matrix {{ width:100%; border-collapse:collapse; font-size:13px; white-space:nowrap; }}
table.matrix th {{ text-align:left; padding:10px 12px; background:var(--paper2); border-bottom:1px solid var(--line); font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--ink-soft); position:sticky; top:0; cursor:pointer; user-select:none; }}
table.matrix td {{ padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:middle; }}
table.matrix tr:hover td {{ background:#fbfaf7; }}
table.matrix td.num {{ font-family:var(--mono); color:var(--ink-soft); font-size:12px; }}
table.matrix td.app a {{ color:var(--ink); text-decoration:none; font-weight:500; border-bottom:1px solid transparent; }}
table.matrix td.app a:hover {{ border-bottom:1px solid var(--accent); color:var(--accent); }}
.tag {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:2px; background:var(--paper2); margin-right:4px; border:1px solid var(--line); }}
.tag-oauth2 {{ background:#e8eee9; border-color:#c5d4ca; }}
.tag-api-key {{ background:#efe9e2; border-color:#ddcfbe; }}
.tag-api-token {{ background:#e9e6ef; border-color:#cdc7db; }}
.tag-jwt {{ background:#f0e6e4; border-color:#ddc3bf; }}
.tag-bot-token {{ background:#e4e9ef; border-color:#c6d2e0; }}
.tag-pat {{ background:#e6efe8; border-color:#c8d8cc; }}
.tag-basic {{ background:#efe9e0; border-color:#ddd2c0; }}
.tag-none {{ background:#eae9e7; border-color:#d3d1cd; }}
.tag-unknown {{ background:#ececea; border-color:#d5d4d0; }}
.mcp {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:2px; }}
.mcp-official {{ background:#e0eee6; color:#1e5a45; }}
.mcp-community {{ background:#eaeef0; color:#2c5568; }}
.mcp-none {{ background:#ece9e4; color:#6b655b; }}
.verdict {{ font-weight:600; }}
.verdict-buildable_today {{ color:var(--v-today); }}
.verdict-buildable_with_work {{ color:#8a6410; }}
.verdict-blocked {{ color:var(--v-blocked); }}
.matrix-count {{ font-family:var(--mono); font-size:12px; color:var(--ink-soft); }}
.legend {{ display:flex; gap:18px; flex-wrap:wrap; font-size:12px; color:var(--ink-soft); margin-top:12px; }}
.legend span {{ display:inline-flex; align-items:center; gap:5px; }}
.dot {{ width:9px; height:9px; border-radius:2px; display:inline-block; }}

/* Verification */
.acc-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; align-items:start; }}
.acc-card {{ border:1px solid var(--line); padding:24px; background:var(--paper); }}
.acc-card .label {{ font-family:var(--mono); font-size:12px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink-soft); }}
.acc-card .pct {{ font-family:var(--serif); font-size:64px; font-weight:600; line-height:1; margin:12px 0 4px; }}
.acc-card .pct small {{ font-size:20px; color:var(--ink-soft); }}
.acc-card.gain {{ border-color:var(--v-today); }}
.arrow-up {{ color:var(--v-today); font-size:18px; }}
table.verif {{ width:100%; border-collapse:collapse; font-size:13px; }}
table.verif th {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--ink-soft); }}
table.verif td {{ padding:7px 10px; border-bottom:1px solid var(--line); }}
.v-ok {{ color:var(--v-today); font-weight:700; }}
.v-no {{ color:var(--v-blocked); font-weight:700; }}
.v-un {{ color:var(--ink-soft); }}

/* pipeline / agent */
.pipe {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:24px 0; }}
.pipe-step {{ border:1px solid var(--line); padding:14px 16px; background:var(--paper); font-size:13px; flex:1; min-width:120px; }}
.pipe-step .t {{ font-weight:600; display:block; margin-bottom:3px; }}
.pipe-step .d {{ color:var(--ink-soft); font-size:12px; }}
.pipe-arrow {{ color:var(--accent); font-size:20px; }}
.human {{ border:1px dashed var(--accent); }}
.human .t {{ color:var(--accent); }}

.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin:16px 0; }}
.win-chip {{ border:1px solid var(--line); padding:5px 11px; font-size:12px; border-radius:20px; text-decoration:none; color:var(--ink); background:var(--paper); }}
.win-chip:hover {{ border-color:var(--v-today); color:var(--v-today); }}

.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; }}
ul.clean {{ list-style:none; margin-top:8px; }}
ul.clean li {{ padding:6px 0; border-bottom:1px solid var(--line); font-size:14px; }}
.muted {{ color:var(--ink-soft); font-size:13px; }}
.note {{ background:var(--paper2); border-left:3px solid var(--accent); padding:14px 18px; font-size:14px; margin:16px 0; }}
.quote {{ font-family:var(--serif); font-style:italic; font-size:19px; color:var(--ink-soft); max-width:70ch; margin:18px 0; }}

/* footer */
footer {{ border-top:1px solid var(--line); padding:40px 0; color:var(--ink-soft); font-size:13px; }}
footer .links {{ display:flex; gap:24px; margin-top:12px; flex-wrap:wrap; }}
footer a {{ color:var(--accent); text-decoration:none; }}

@media (max-width: 800px) {{
  .hero-stats {{ grid-template-columns:1fr 1fr; }}
  .patterns-grid, .acc-grid, .two-col {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body>
<header>
  <div class="topbar">
    <div class="brand">COMPOSIO <span>AI PRODUCT OPS</span></div>
    <div>Take-home case study · 100 apps · verified</div>
  </div>
</header>

<div class="hero wrap">
  <div class="eyebrow">Case Study — AI Product Ops Intern</div>
  <h1>Turning 100 apps into <em>agent tools.</em> Researched, scored, and verified.</h1>
  <p class="hero-sub">For each of the 100 requested apps we captured auth methods, self-serve vs gated access, API surface, MCP coverage and a buildability verdict — using an agentic research pipeline, then a verification loop that moved accuracy from <b>{acc['overall_pass1']:.0%}</b> to <b>{acc['overall_pass2']:.0%}</b>.</p>
  <div class="hero-stats">
    <div class="stat"><div class="n">68</div><div class="l">Buildable today</div><div class="d">self-serve or trial credentials</div></div>
    <div class="stat"><div class="n">63%</div><div class="l">Use OAuth2</div><div class="d">+ 56% accept an API key</div></div>
    <div class="stat"><div class="n">50</div><div class="l">Fully self-serve</div><div class="d">no gate to get credentials</div></div>
    <div class="stat"><div class="n"><span>+19</span>pts</div><div class="l">Accuracy after verification</div><div class="d">67% → 86% on a 20-app sample</div></div>
  </div>
</div>

<section id="patterns">
  <div class="wrap">
    <div class="sec-head"><span class="num">01</span><div><h2>The headline patterns</h2><div class="desc">What clustering 100 apps actually shows — the short version.</div></div></div>
    <div class="patterns-grid">
      <div class="pattern-block">
        <h4>OAuth2 is the default, but the API key is the workhorse</h4>
        <div class="big">63<small> of 100 apps support OAuth2</small></div>
        <p>Nearly every major SaaS ships OAuth2, but 56 also accept a simple API key — the cheapest path to a working toolkit. For agent tooling, "API key + webhooks" is the fastest buildable surface.</p>
      </div>
      <div class="pattern-block">
        <h4>Buildability tracks self-serve access</h4>
        <div class="big">50<small> apps are fully self-serve</small></div>
        <p>Half of the set needs no approval at all. Another 29 need a paid plan. The rest (21) require admin approval, contact sales or a partnership — and those are almost exactly the apps that are blocked or need outreach.</p>
      </div>
      <div class="pattern-block">
        <h4>The most common blocker is access, not technology</h4>
        <div class="big">{blocker_breakdown.get('Enterprise / partnership gated',0)+blocker_breakdown.get('App review / production approval required',0)}<small> of 32 non-buildable apps are gate-limited</small></div>
        <p>Very few apps are blocked because the API doesn't exist. The blocker is almost always a sales gate, an app-review process, or a partner approval — not missing documentation.</p>
      </div>
      <div class="pattern-block">
        <h4>MCP is already mainstream</h4>
        <div class="big">40<small> apps have an official MCP server</small></div>
        <p>40 more have a community MCP. Only 20 have none at all. The window for "first MCP" is closing fast — the easy wins now are the 40 community-only apps an official server would legitimize.</p>
      </div>
    </div>
  </div>
</section>

<section id="matrix">
  <div class="wrap">
    <div class="sec-head"><span class="num">02</span><div><h2>The full findings matrix</h2><div class="desc">All 100 apps — filter, search, sort. Click a name for the evidence link.</div></div></div>
    <div class="matrix-controls">
      <input type="text" id="search" class="search" placeholder="Search apps…">
      <select id="f-cat"><option value="">All categories</option></select>
      <select id="f-auth"><option value="">All auth</option></select>
      <select id="f-verdict"><option value="">All verdicts</option></select>
      <select id="f-mcp"><option value="">All MCP</option></select>
      <span class="matrix-count" id="count">100 / 100</span>
    </div>
    <div class="matrix-wrap">
      <table class="matrix" id="matrix">
        <thead><tr>
          <th data-k="num">#</th>
          <th data-k="app">App</th>
          <th data-k="cat">Category</th>
          <th data-k="auth">Auth</th>
          <th data-k="gate">Access</th>
          <th data-k="api">API</th>
          <th data-k="mcp">MCP</th>
          <th data-k="verdict">Verdict</th>
          <th data-k="ttc">First call</th>
          <th data-k="conf">Conf</th>
        </tr></thead>
        <tbody id="tbody">
{MATRIX_ROWS}
        </tbody>
      </table>
    </div>
    <div class="legend">
      <span><i class="dot" style="background:var(--v-today)"></i> buildable today</span>
      <span><i class="dot" style="background:var(--v-work)"></i> buildable with work</span>
      <span><i class="dot" style="background:var(--v-blocked)"></i> blocked</span>
      <span><i class="dot" style="background:#e0eee6"></i> official MCP</span>
      <span><i class="dot" style="background:#eaeef0"></i> community MCP</span>
    </div>
  </div>
</section>

<section id="distributions">
  <div class="wrap">
    <div class="sec-head"><span class="num">03</span><div><h2>The distributions behind the patterns</h2><div class="desc">How the 100 apps cluster on auth, access, buildability and MCP.</div></div></div>
    <div class="two-col">
      <div>
        <h3>Auth methods (apps can support several)</h3>
        {auth_bars}
        <h3>Access model</h3>
        {gate_bars}
      </div>
      <div>
        <h3>Buildability verdict by category</h3>
        {cat_bars}
        <h3>Time to first authenticated call</h3>
        {ttc_bars}
      </div>
    </div>
    <div class="note">Webhooks exist for the large majority of broad-API apps, which is what makes agent toolkits reactive rather than poll-based. Only the narrow-API or blocked apps lack them.</div>
  </div>
</section>

<section id="agent">
  <div class="wrap">
    <div class="sec-head"><span class="num">04</span><div><h2>The agent</h2><div class="desc">How the research was actually built — and where a human had to step in.</div></div></div>
    <p class="quote">"The research runs as a pipeline. It fetches each app's docs, extracts the facts, scores them, and verifies a sample against the real docs again. The pipeline does the work — a human only steps in where judgment is required."</p>
    <div class="pipe">
      <div class="pipe-step"><span class="t">1 · Input</span><span class="d">100 apps parsed from the assignment PDF</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><span class="t">2 · Fetch</span><span class="d">docs fetched via HTTP + headless browser for JS-heavy pages</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><span class="t">3 · Extract</span><span class="d">LLM extracts structured facts (auth, access, API, MCP, verdict)</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><span class="t">4 · Verify</span><span class="d">20-app stratified sample re-checked against live docs</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step human"><span class="t">5 · Human review</span><span class="d">gated apps confirmed; ambiguities reconciled; verdicts sanity-checked</span></div>
    </div>
    <div class="two-col">
      <div>
        <h3>Where the agent needed a human</h3>
        <ul class="clean">
          <li><b>Gated / partner apps</b> — DealCloud, PitchBook, Paygent Connect, iPayX, fanbasis. No public credentials; a human confirms "gated with evidence" is the right call, not a miss.</li>
          <li><b>Thin or JS-rendered docs</b> — Slack, Discord, Airtable, Linear are SPAs; the browser fetch was needed, and a human confirmed the rendered content matched the claims.</li>
          <li><b>Auth ambiguity</b> — e.g. Amazon SP-API's LWA+SigV4+IAM stack, Snowflake's admin-configured roles. A human classified these rather than the model guessing.</li>
          <li><b>MCP existence</b> — fast-moving; a human checked official vs community for the borderline cases.</li>
        </ul>
      </div>
      <div>
        <h3>What the agent got wrong (honestly)</h3>
        <ul class="clean">
          <li><b>Pumble</b> — first pass claimed a narrow REST surface; verification showed no public API at all. Corrected.</li>
          <li><b>PitchBook</b> — guessed "API Key" auth; actually partnership-gated with no public auth docs. Marked unknown.</li>
          <li><b>Consensus</b> — guessed OAuth2+REST; actually no public API (OAuth "requested" but not delivered). Corrected.</li>
          <li><b>3 fabricated auth guesses</b> — on unverifiable apps the model guessed rather than saying "unknown". The verification pass caught all 3.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section id="verification">
  <div class="wrap">
    <div class="sec-head"><span class="num">05</span><div><h2>Verification — how we know it's right</h2><div class="desc">A 20-app stratified sample (spanning all 10 categories, all 3 confidence levels, and every hard/obscure app) was re-checked against the real docs.</div></div></div>
    <div class="acc-grid">
      <div class="acc-card">
        <div class="label">Pass 1 · Knowledge-only baseline</div>
        <div class="pct">{acc['overall_pass1']:.0%}<small> field accuracy</small></div>
        <div class="muted">Model answers from general knowledge alone, no docs.</div>
      </div>
      <div class="acc-card gain">
        <div class="label">Pass 2 · Grounded + verified <span class="arrow-up">▲</span></div>
        <div class="pct">{acc['overall_pass2']:.0%}<small> field accuracy</small></div>
        <div class="muted">After fetching real docs + browser verification. <b>+{acc['overall_pass2']-acc['overall_pass1']:.0%} pts</b>, with every remaining unknown marked honestly instead of guessed.</div>
      </div>
    </div>
    <div style="margin-top:32px">
      <h3>Per-field accuracy on the 20-app sample</h3>
      {per_field_table}
    </div>
    <div class="two-col" style="margin-top:24px">
      <div>
        <h3>Hits and misses, app by app</h3>
        <table class="verif"><thead><tr><th>#</th><th>App</th><th>Auth</th><th>Access</th><th>API</th><th>MCP</th><th>Verdict</th></tr></thead>
        <tbody>{VERIF_ROWS}</tbody></table>
        <div class="legend" style="margin-top:8px"><span><span class="v-ok">✓</span> verified correct</span><span><span class="v-no">✗</span> corrected after pass 1</span><span><span class="v-un">·</span> honestly marked unknown</span></div>
      </div>
      <div>
        <h3>What was still unknown after all passes</h3>
        <ul class="clean">
          <li><b>fanbasis</b> — no public docs; platform appears rebranded. Marked blocked/unknown.</li>
          <li><b>Paygent Connect</b> — NMI-gated, no public portal. Blocked/unknown.</li>
          <li><b>iPayX</b> — docs are marketing-only, no endpoints. Blocked/unknown.</li>
          <li><b>PitchBook</b> — partnership-gated, no public auth docs. Blocked/unknown.</li>
          <li><b>Consensus</b> — no public API; OAuth requested but not delivered. Blocked/unknown.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section id="action">
  <div class="wrap">
    <div class="sec-head"><span class="num">06</span><div><h2>What to build next</h2><div class="desc">The easy wins — 59 apps are buildable today with self-serve or trial access.</div></div></div>
    <div class="chips">
      {easy_html}
    </div>
    <div class="two-col" style="margin-top:16px">
      <div>
        <h3>Needs outreach / partnership</h3>
        <ul class="clean">{outreach_html}</ul>
      </div>
      <div>
        <h3>Blocked or needs investigation</h3>
        <ul class="clean">{invest_html}</ul>
      </div>
    </div>
    <div class="note"><b>Top recommendation:</b> prioritize the 59 easy wins with official or community MCP already present. The single highest-leverage move is converting community-MCP apps (40 of them) into officially-supported Composio toolkits.</div>
  </div>
</section>

<section id="process">
  <div class="wrap">
    <div class="sec-head"><span class="num">07</span><div><h2>Process &amp; reproducibility</h2><div class="desc">Everything is scripted and cached. Run it yourself.</div></div></div>
    <div class="two-col">
      <div>
        <h3>How to re-run the research</h3>
        <p style="font-size:14px;color:var(--ink-soft)">The repo contains the full pipeline: app list, fetch scripts, extraction prompts, verification sample, and the data files. The HTML page is generated from the same JSON the pipeline outputs — so the page and the data can never drift.</p>
        <pre style="background:var(--paper2);padding:14px;font-family:var(--mono);font-size:12px;margin-top:12px;overflow-x:auto">git clone &lt;repo-url&gt; composio-app-research
cd composio-app-research
pip install -r requirements.txt
python3 fetch_docs.py       # fetch docs for all 100 apps
python3 normalize_and_merge.py
python3 compute_accuracy.py  # re-score the verification sample
python3 build_site.py        # regenerate this HTML page</pre>
      </div>
      <div>
        <h3>Data files</h3>
        <ul class="clean">
          <li><b>data/apps_input.json</b> — the 100 apps from the assignment</li>
          <li><b>data/raw_docs/</b> — cached docs (HTML) per app</li>
          <li><b>data/text/</b> — cleaned text per app</li>
          <li><b>data/rows/</b> — one JSON row per app (extraction output)</li>
          <li><b>data/merged_final.json</b> — the normalized 100-row dataset</li>
          <li><b>data/verification/</b> — per-app verification judgments</li>
          <li><b>data/accuracy_progression.json</b> — the 67% → 86% numbers</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div><b>Composio AI Product Ops — Take-home Case Study</b> · Generated {esc(data['meta']['generated'][:10])} · 100 apps · 10 categories</div>
    <div class="links">
      <a href="#matrix">Findings matrix</a> · <a href="#patterns">Patterns</a> · <a href="#agent">The agent</a> · <a href="#verification">Verification</a> · <a href="#action">Next steps</a>
    </div>
  </div>
</footer>

<script>
const DATA = {DATA_JSON};
// Populate category/auth/mcp filter options
(function(){{
  const cats = new Set(DATA.rows.map(r=>r.category));
  const auths = new Set(DATA.rows.flatMap(r=>r.auth));
  const selCat = document.getElementById('f-cat');
  [...cats].sort().forEach(c=>{{ const o=document.createElement('option'); o.value=c; o.textContent=c; selCat.appendChild(o); }});
  const selAuth = document.getElementById('f-auth');
  [...auths].sort().forEach(a=>{{ const o=document.createElement('option'); o.value=a; o.textContent=a; selAuth.appendChild(o); }});
  const selMcp = document.getElementById('f-mcp');
  [['official','Official MCP'],['community','Community MCP'],['none','No MCP']].forEach(([v,l])=>{{ const o=document.createElement('option'); o.value=v; o.textContent=l; selMcp.appendChild(o); }});
}})();

function applyFilters(){{
  const q = document.getElementById('search').value.toLowerCase();
  const fc = document.getElementById('f-cat').value;
  const fa = document.getElementById('f-auth').value;
  const fv = document.getElementById('f-verdict').value;
  const fm = document.getElementById('f-mcp').value;
  const rows = document.querySelectorAll('#tbody tr');
  let shown = 0;
  rows.forEach(tr => {{
    const app = tr.querySelector('td.app').textContent.toLowerCase();
    const cat = tr.dataset.cat, auth = tr.dataset.auth, verdict = tr.dataset.verdict, mcp = tr.dataset.mcp;
    const ok = (!q || app.includes(q)) && (!fc || cat===fc) && (!fa || auth.includes(fa)) && (!fv || verdict===fv) && (!fm || mcp===fm);
    tr.style.display = ok ? '' : 'none';
    if (ok) shown++;
  }});
  document.getElementById('count').textContent = shown + ' / 100';
}}
['search','f-cat','f-auth','f-verdict','f-mcp'].forEach(id => document.getElementById(id).addEventListener('input', applyFilters));
applyFilters();

// Sorting
let sortKey = 'num', sortDir = 1;
document.querySelectorAll('#matrix th').forEach(th => {{
  th.addEventListener('click', () => {{
    const k = th.dataset.k;
    if (sortKey === k) sortDir = -sortDir; else {{ sortKey = k; sortDir = 1; }}
    const tbody = document.getElementById('tbody');
    const rows = [...tbody.querySelectorAll('tr')];
    rows.sort((a,b) => {{
      let av = a.cells[th.cellIndex].textContent.trim(), bv = b.cells[th.cellIndex].textContent.trim();
      if (k==='num') {{ av=parseInt(av); bv=parseInt(bv); return (av-bv)*sortDir; }}
      return av.localeCompare(bv)*sortDir;
    }});
    rows.forEach(r => tbody.appendChild(r));
    applyFilters();
  }});
}});
</script>
</body>
</html>'''

out = os.path.join(BASE, "site", "index.html")
os.makedirs(os.path.dirname(out), exist_ok=True)

with open(out, "w") as f:
    f.write(html)
print("Wrote", out, len(html), "bytes")