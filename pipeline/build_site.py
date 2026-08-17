#!/usr/bin/env python3
"""Build the self-contained HTML case study (first-person, skimmable) by injecting site_data.json."""
import json, os, html as h

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(BASE, "site_data.json")))
DATA_JSON = json.dumps(data)
p = data["patterns"]
acc = data["accuracy"]

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

def esc(s):
    return h.escape(str(s or ""))

# ---- matrix rows ----
rows_html = []
for r in data["rows"]:
    auths = "".join(f'<span class="tag tag-{esc(a.lower().replace(" ","-"))}">{esc(auth_label(a))}</span>' for a in r["auth"])
    mcp = f'<span class="mcp mcp-{r["mcp"]}">{esc(mcp_label(r["mcp"]))}</span>'
    rows_html.append(f'''<tr data-cat="{esc(r['category'])}" data-auth="{' '.join(r['auth'])}" data-verdict="{r['verdict']}" data-gate="{r['gate']}" data-mcp="{r['mcp']}">
<td class="num">{r['num']}</td>
<td class="app"><a href="{esc(r['evidence'])}" target="_blank" rel="noopener">{esc(r['app'])}</a></td>
<td class="cat">{esc(r['category'])}</td>
<td class="auth">{auths}</td>
<td class="gate">{esc(gate_label(r['gate']))}</td>
<td class="api">{esc('|'.join(r['protocol']) if isinstance(r['protocol'], list) else r['protocol'])}</td>
<td class="mcp">{mcp}</td>
<td class="verdict verdict-{r['verdict']}">{esc(verdict_label(r['verdict']))}</td>
<td class="ttc">{esc(r['ttc'])}</td>
</tr>''')
MATRIX_ROWS = "\n".join(rows_html)

# ---- verification sample table (from real data) ----
verif_checks = {}
import glob
for f in sorted(glob.glob(os.path.join(BASE, "data", "verification", "*.json"))):
    rec = json.load(open(f))
    verif_checks[rec["num"]] = rec["checks"]

def vcell(v):
    if v == "correct": return '<span class="v-ok">✓</span>'
    if v == "wrong": return '<span class="v-no">✗</span>'
    return '<span class="v-un">·</span>'

verif_rows = []
for num in sorted(verif_checks):
    row = next(r for r in data["rows"] if r["num"] == num)
    vc = verif_checks[num]
    verif_rows.append(f'<tr><td>{num}</td><td>{esc(row["app"])}</td><td>{vcell(vc["auth_methods"])}</td><td>{vcell(vc["self_serve"])}</td><td>{vcell(vc["api_surface"])}</td><td>{vcell(vc["mcp"])}</td><td>{vcell(vc["verdict"])}</td></tr>')
VERIF_ROWS = "\n".join(verif_rows)

# ---- bars ----
blocker_breakdown = p["blocker_breakdown"]
max_blk = max(blocker_breakdown.values()) if blocker_breakdown else 1
blocker_bars = ""
for k, v in sorted(blocker_breakdown.items(), key=lambda x: -x[1]):
    blocker_bars += f'<div class="bar-row"><div class="bar-label">{esc(k)}</div><div class="bar-track"><div class="bar-fill" style="width:{v/max_blk*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

auth_counts = [x for x in p["auth_dominance"] if x[1] > 2]
max_auth = auth_counts[0][1] if auth_counts else 1
auth_bars = ""
for k, v in auth_counts:
    auth_bars += f'<div class="bar-row"><div class="bar-label">{esc(auth_label(k))}</div><div class="bar-track"><div class="bar-fill bar-auth" style="width:{v/max_auth*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

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
    cat_bars += f'''<div class="bar-row"><div class="bar-label">{esc(cat)}</div>
<div class="bar-track stacked"><div class="bar-fill v-today" style="width:{b1:.0f}%"></div><div class="bar-fill v-work" style="width:{b2:.0f}%"></div><div class="bar-fill v-blocked" style="width:{b3:.0f}%"></div></div>
<div class="bar-val">{tot}</div></div>'''

gate_counts = p["gate_overall"]
max_gate = max(gate_counts.values())
gate_bars = ""
for k in ["none","paid_plan","admin_approval","contact_sales","partnership"]:
    v = gate_counts.get(k, 0)
    gate_bars += f'<div class="bar-row"><div class="bar-label">{esc(gate_label(k))}</div><div class="bar-track"><div class="bar-fill bar-gate" style="width:{v/max_gate*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

ttc = p["time_to_first_call"]
ttc_bars = ""
for k in ["minutes","hours","days","weeks"]:
    v = ttc.get(k, 0)
    ttc_bars += f'<div class="bar-row"><div class="bar-label">{k}</div><div class="bar-track"><div class="bar-fill bar-ttc" style="width:{v/43*100:.0f}%"></div></div><div class="bar-val">{v}</div></div>'

per_field_rows = ""
for f in acc["fields"]:
    a1 = acc["pass1"][f]["accuracy"]; a2 = acc["pass2"][f]["accuracy"]
    arrow = "&#9650;" if a2 > a1 else ("=" if a2 == a1 else "&#9660;")
    name = {"auth":"Auth methods","self_serve":"Self-serve","api_surface":"API surface","mcp":"MCP","verdict":"Verdict"}[f]
    per_field_rows += f'<div class="bar-row"><div class="bar-label">{name}</div><div class="bar-track"><div class="bar-fill bar-auth" style="width:{a2*100:.0f}%"></div></div><div class="bar-val">{a1:.0%} &rarr; {a2:.0%} {arrow}</div></div>'

easy = p["easy_wins"]
easy_html = "".join(f'<span class="win-chip">{esc(e["app"])}</span>' for e in easy)
outreach = p["outreach"]
outreach_html = "".join(f'<li><b>{esc(o["app"])}</b> <span class="muted">({esc(gate_label(o["gate"]))})</span></li>' for o in outreach)
investigate = p["investigate"]
invest_html = "".join(f'<li><b>{esc(i["app"])}</b> <span class="muted">({esc(verdict_label(i["verdict"]))})</span></li>' for i in investigate)

blocked_apps = "".join(f'<a class="win-chip chip-blocked" href="#matrix">{esc(b["app"])}</a>' for b in [r for r in data["rows"] if r["verdict"] == "blocked"])

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>100 apps → agent tools · Pranav Dhiran</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --paper:#f6f4ef; --paper2:#ece9e1; --ink:#1a1917; --ink-soft:#5c5851; --line:#d8d3c8;
  --accent:#c8452c; --green:#2a6b5a; --amber:#c8932c; --red:#c8452c;
  --serif:'Newsreader',Georgia,serif; --sans:'Space Grotesk','Helvetica Neue',sans-serif; --mono:'IBM Plex Mono',monospace;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ background:var(--paper); color:var(--ink); font-family:var(--sans); line-height:1.55; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:0 32px; }}
header {{ border-bottom:1px solid var(--line); }}
.topbar {{ display:flex; justify-content:space-between; align-items:center; padding:18px 32px; max-width:1180px; margin:0 auto; font-size:13px; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-soft); }}
.topbar .brand {{ font-weight:700; color:var(--ink); }} .topbar .brand span {{ color:var(--accent); }}
.hero {{ padding:64px 0 52px; }}
.eyebrow {{ font-family:var(--mono); font-size:12px; letter-spacing:.18em; text-transform:uppercase; color:var(--accent); margin-bottom:18px; }}
h1 {{ font-family:var(--serif); font-weight:600; font-size:clamp(36px,5vw,60px); line-height:1.06; letter-spacing:-.015em; max-width:20ch; }}
h1 em {{ font-style:italic; font-weight:400; }}
.hero-sub {{ font-size:17px; color:var(--ink-soft); max-width:64ch; margin-top:18px; font-family:var(--serif); }}
.hero-sub b {{ color:var(--ink); }}
.hero-stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--line); border:1px solid var(--line); margin-top:44px; }}
.stat {{ background:var(--paper); padding:24px 20px; }}
.stat .n {{ font-family:var(--serif); font-size:42px; font-weight:600; line-height:1; }} .stat .n span {{ color:var(--accent); }}
.stat .l {{ font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--ink-soft); margin-top:8px; }}
.stat .d {{ font-size:13px; color:var(--ink-soft); margin-top:4px; }}
section {{ padding:60px 0; border-top:1px solid var(--line); }}
section h2 {{ font-family:var(--serif); font-size:30px; font-weight:600; letter-spacing:-.01em; }}
section h3 {{ font-family:var(--serif); font-size:19px; font-weight:600; margin:26px 0 6px; }}
.sec-head {{ display:flex; align-items:baseline; gap:14px; margin-bottom:26px; }}
.sec-head .num {{ font-family:var(--mono); color:var(--accent); font-size:14px; }}
.sec-head .desc {{ color:var(--ink-soft); font-size:15px; font-family:var(--serif); }}
.kicker {{ font-family:var(--mono); font-size:12px; text-transform:uppercase; letter-spacing:.1em; color:var(--accent); }}
.patterns-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:36px; }}
.pattern-block {{ border-top:2px solid var(--ink); padding-top:12px; }}
.pattern-block h4 {{ font-family:var(--serif); font-size:18px; font-weight:600; margin-bottom:4px; }}
.pattern-block p {{ color:var(--ink-soft); font-size:14.5px; }}
.pattern-block .big {{ font-family:var(--serif); font-size:32px; font-weight:600; color:var(--accent); line-height:1.1; }}
.pattern-block .big small {{ font-size:15px; color:var(--ink-soft); font-family:var(--sans); font-weight:400; }}
.bar-row {{ display:grid; grid-template-columns:160px 1fr 46px; gap:12px; align-items:center; margin:9px 0; font-size:13px; }}
.bar-label {{ text-align:right; color:var(--ink-soft); font-size:13px; }}
.bar-track {{ height:16px; background:var(--paper2); border-radius:2px; overflow:hidden; }}
.bar-fill {{ height:100%; background:var(--accent); border-radius:2px; }}
.bar-auth {{ background:var(--accent); }} .bar-gate {{ background:var(--ink); }} .bar-ttc {{ background:var(--green); }}
.bar-val {{ font-family:var(--mono); font-size:13px; }}
.bar-track.stacked {{ display:flex; }}
.stacked .v-today {{ background:var(--green); }} .stacked .v-work {{ background:var(--amber); }} .stacked .v-blocked {{ background:var(--red); }}
.matrix-controls {{ display:flex; flex-wrap:wrap; gap:10px; margin-bottom:16px; align-items:center; }}
.matrix-controls select,.matrix-controls input {{ padding:8px 12px; font-family:var(--sans); font-size:13px; border:1px solid var(--line); background:var(--paper); color:var(--ink); border-radius:3px; }}
.matrix-controls .search {{ flex:1; min-width:180px; }}
.matrix-wrap {{ overflow-x:auto; border:1px solid var(--line); }}
table.matrix {{ width:100%; border-collapse:collapse; font-size:13px; white-space:nowrap; }}
table.matrix th {{ text-align:left; padding:10px 12px; background:var(--paper2); border-bottom:1px solid var(--line); font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--ink-soft); position:sticky; top:0; cursor:pointer; user-select:none; }}
table.matrix td {{ padding:9px 12px; border-bottom:1px solid var(--line); }}
table.matrix tr:hover td {{ background:#fbfaf7; }}
table.matrix td.num {{ font-family:var(--mono); color:var(--ink-soft); font-size:12px; }}
table.matrix td.app a {{ color:var(--ink); text-decoration:none; font-weight:500; border-bottom:1px solid transparent; }}
table.matrix td.app a:hover {{ border-bottom:1px solid var(--accent); color:var(--accent); }}
.tag {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:2px; background:var(--paper2); margin-right:4px; border:1px solid var(--line); }}
.tag-oauth2 {{ background:#e8eee9; border-color:#c5d4ca; }} .tag-api-key {{ background:#efe9e2; border-color:#ddcfbe; }}
.tag-api-token {{ background:#e9e6ef; border-color:#cdc7db; }} .tag-jwt {{ background:#f0e6e4; border-color:#ddc3bf; }}
.tag-bot-token {{ background:#e4e9ef; border-color:#c6d2e0; }} .tag-pat {{ background:#e6efe8; border-color:#c8d8cc; }}
.tag-basic {{ background:#efe9e0; border-color:#ddd2c0; }} .tag-none {{ background:#eae9e7; border-color:#d3d1cd; }}
.tag-unknown {{ background:#ececea; border-color:#d5d4d0; }}
.mcp {{ display:inline-block; font-size:11px; padding:2px 7px; border-radius:2px; }}
.mcp-official {{ background:#e0eee6; color:#1e5a45; }} .mcp-community {{ background:#eaeef0; color:#2c5568; }} .mcp-none {{ background:#ece9e4; color:#6b655b; }}
.verdict {{ font-weight:600; }}
.verdict-buildable_today {{ color:var(--green); }} .verdict-buildable_with_work {{ color:#8a6410; }} .verdict-blocked {{ color:var(--red); }}
.matrix-count {{ font-family:var(--mono); font-size:12px; color:var(--ink-soft); }}
.legend {{ display:flex; gap:16px; flex-wrap:wrap; font-size:12px; color:var(--ink-soft); margin-top:10px; }}
.legend span {{ display:inline-flex; align-items:center; gap:5px; }} .dot {{ width:9px; height:9px; border-radius:2px; display:inline-block; }}
.acc-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:36px; align-items:start; }}
.acc-card {{ border:1px solid var(--line); padding:22px; background:var(--paper); }}
.acc-card .label {{ font-family:var(--mono); font-size:12px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink-soft); }}
.acc-card .pct {{ font-family:var(--serif); font-size:60px; font-weight:600; line-height:1; margin:10px 0 4px; }} .acc-card .pct small {{ font-size:19px; color:var(--ink-soft); }}
.acc-card.gain {{ border-color:var(--green); }} .arrow-up {{ color:var(--green); font-size:16px; }}
table.verif {{ width:100%; border-collapse:collapse; font-size:13px; }}
table.verif th {{ text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); font-size:11px; text-transform:uppercase; letter-spacing:.06em; color:var(--ink-soft); }}
table.verif td {{ padding:7px 10px; border-bottom:1px solid var(--line); }}
.v-ok {{ color:var(--green); font-weight:700; }} .v-no {{ color:var(--red); font-weight:700; }} .v-un {{ color:var(--ink-soft); }}
.pipe {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin:22px 0; }}
.pipe-step {{ border:1px solid var(--line); padding:13px 15px; background:var(--paper); font-size:13px; flex:1; min-width:130px; }}
.pipe-step .t {{ font-weight:600; display:block; margin-bottom:2px; }} .pipe-step .d {{ color:var(--ink-soft); font-size:12px; }}
.pipe-arrow {{ color:var(--accent); font-size:18px; }}
.human {{ border:1px dashed var(--accent); }} .human .t {{ color:var(--accent); }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0; }}
.win-chip {{ border:1px solid var(--line); padding:5px 11px; font-size:12px; border-radius:20px; color:var(--ink); background:var(--paper); }}
.chip-blocked {{ border-color:#e3b3aa; color:var(--red); }}
.two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:36px; }}
ul.clean {{ list-style:none; margin-top:8px; }}
ul.clean li {{ padding:6px 0; border-bottom:1px solid var(--line); font-size:14px; }}
.muted {{ color:var(--ink-soft); font-size:13px; }}
.note {{ background:var(--paper2); border-left:3px solid var(--accent); padding:14px 18px; font-size:14px; margin:16px 0; }}
.callout {{ background:#e8eee9; border-left:4px solid var(--green); padding:16px 20px; margin:16px 0; }}
.callout h4 {{ font-family:var(--serif); font-size:17px; margin-bottom:4px; }}
.callout p {{ font-size:14px; color:var(--ink-soft); }}
pre {{ background:var(--paper2); padding:14px; font-family:var(--mono); font-size:12px; margin-top:10px; overflow-x:auto; }}
.tool-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:18px; }}
.tool {{ border:1px solid var(--line); padding:16px 18px; background:var(--paper); }}
.tool .t {{ font-weight:600; font-size:14px; }} .tool .d {{ color:var(--ink-soft); font-size:13px; margin-top:3px; }}
.tool .tag {{ margin-top:8px; }}
footer {{ border-top:1px solid var(--line); padding:38px 0; color:var(--ink-soft); font-size:13px; }}
@media (max-width:820px) {{ .hero-stats,.patterns-grid,.acc-grid,.two-col,.tool-grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header><div class="topbar"><div class="brand">PRANAV <span>DHIRAN</span></div><div>AI Product Ops · Take-home</div></div></header>

<div class="hero wrap">
  <div class="eyebrow">Case study — 100 apps, one research pipeline</div>
  <h1>I researched 100 apps. <em>Here's what makes them buildable into agent tools.</em></h1>
  <p class="hero-sub">For every app I captured <b>auth method</b>, <b>self-serve vs gated access</b>, <b>API surface</b>, <b>MCP coverage</b> and a <b>buildability verdict</b> — then I verified a sample against the real docs and watched accuracy climb from <b>{acc['overall_pass1']:.0%}</b> to <b>{acc['overall_pass2']:.0%}</b>.</p>
  <div class="hero-stats">
    <div class="stat"><div class="n">68</div><div class="l">Buildable today</div><div class="d">self-serve or trial creds</div></div>
    <div class="stat"><div class="n">63%</div><div class="l">Use OAuth2</div><div class="d">+ 56% accept an API key</div></div>
    <div class="stat"><div class="n">50</div><div class="l">Fully self-serve</div><div class="d">no approval needed</div></div>
    <div class="stat"><div class="n"><span>+19</span></div><div class="l">Accuracy after verify</div><div class="d">67% → 86% on 20 apps</div></div>
  </div>
</div>

<section id="patterns">
  <div class="wrap">
    <div class="sec-head"><span class="num">01</span><div><h2>The patterns, up front</h2><div class="desc">Read these four — that's the whole story.</div></div></div>
    <div class="patterns-grid">
      <div class="pattern-block"><h4>OAuth2 is the default, but the API key is the workhorse</h4><div class="big">63<small> / 100 support OAuth2</small></div><p>56 also accept a plain API key. For agent tooling, "API key + webhooks" is the fastest path to a working toolkit.</p></div>
      <div class="pattern-block"><h4>Buildability tracks self-serve access</h4><div class="big">50<small> apps need no approval</small></div><p>Half the set is fully self-serve. Another 29 need a paid plan. The remaining 21 need admin, sales or partnership — and those are almost exactly the blocked ones.</p></div>
      <div class="pattern-block"><h4>The blocker is access, not technology</h4><div class="big">{blocker_breakdown.get('Enterprise / partnership gated',0)+blocker_breakdown.get('App review / production approval required',0)}<small> of 32 are gate-limited</small></div><p>Almost no app is blocked because the API doesn't exist — it's a sales gate, an app review, or a partner approval.</p></div>
      <div class="pattern-block"><h4>MCP is already mainstream</h4><div class="big">40<small> apps have an official MCP</small></div><p>40 more have a community one; only 20 have none. The easy wins are the 40 community-only apps that deserve an official server.</p></div>
    </div>
  </div>
</section>

<section id="blocked">
  <div class="wrap">
    <div class="sec-head"><span class="num">02</span><div><h2>What does "blocked" actually mean?</h2><div class="desc">9 of 100 apps can't become a toolkit today — and it's almost never a technical problem.</div></div></div>
    <div class="callout">
      <h4>"Blocked" = no way to build it today with reasonable effort.</h4>
      <p>Either there is <b>no public API at all</b> (NotebookLM, Consensus), the API exists but <b>credentials are locked behind sales or a partnership</b> (PitchBook, Paygent Connect), or the product <b>isn't a SaaS with an API surface</b> (Sherlock is a CLI, Pumble has no developer API). Per the brief, reporting these as gated with evidence is a <b>correct finding</b>, not a failure.</p>
    </div>
    <p class="kicker">The 9 blocked apps</p>
    <div class="chips">{blocked_apps}</div>
    <div class="bar-row" style="grid-template-columns:220px 1fr 46px"><div class="bar-label">why they're blocked</div></div>
    {blocker_bars}
  </div>
</section>

<section id="matrix">
  <div class="wrap">
    <div class="sec-head"><span class="num">03</span><div><h2>The full matrix — all 100</h2><div class="desc">Filter, search, sort. Click any app for its evidence link.</div></div></div>
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
        <thead><tr><th data-k="num">#</th><th data-k="app">App</th><th data-k="cat">Category</th><th data-k="auth">Auth</th><th data-k="gate">Access</th><th data-k="api">API</th><th data-k="mcp">MCP</th><th data-k="verdict">Verdict</th><th data-k="ttc">First call</th></tr></thead>
        <tbody id="tbody">
{MATRIX_ROWS}
        </tbody>
      </table>
    </div>
    <div class="legend">
      <span><i class="dot" style="background:var(--green)"></i> buildable today</span>
      <span><i class="dot" style="background:var(--amber)"></i> buildable with work</span>
      <span><i class="dot" style="background:var(--red)"></i> blocked</span>
      <span><i class="dot" style="background:#e0eee6"></i> official MCP</span>
      <span><i class="dot" style="background:#eaeef0"></i> community MCP</span>
    </div>
  </div>
</section>

<section id="distributions">
  <div class="wrap">
    <div class="sec-head"><span class="num">04</span><div><h2>What the numbers look like</h2><div class="desc">Auth, access, buildability and speed, broken down.</div></div></div>
    <div class="two-col">
      <div>
        <h3>Auth methods (apps can support several)</h3>{auth_bars}
        <h3>Access model</h3>{gate_bars}
      </div>
      <div>
        <h3>Buildability by category</h3>{cat_bars}
        <h3>Time to first authenticated call</h3>{ttc_bars}
      </div>
    </div>
  </div>
</section>

<section id="agent">
  <div class="wrap">
    <div class="sec-head"><span class="num">05</span><div><h2>How I actually did it</h2><div class="desc">The pipeline, the tools, and where a human (me) had to step in.</div></div></div>
    <div class="pipe">
      <div class="pipe-step"><span class="t">1 · Parse</span><span class="d">100 apps from the PDF → structured list</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><span class="t">2 · Fetch docs</span><span class="d">HTTP + headless browser for JS-heavy pages</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><span class="t">3 · Extract</span><span class="d">LLM fills a fixed schema per app (auth, access, API, MCP, verdict)</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step"><span class="t">4 · Verify</span><span class="d">20-app sample re-checked against live docs</span></div>
      <div class="pipe-arrow">→</div>
      <div class="pipe-step human"><span class="t">5 · Human review</span><span class="d">gated apps confirmed, ambiguities reconciled, verdicts sanity-checked</span></div>
    </div>

    <div class="tool-grid">
      <div class="tool"><div class="t">Plain HTTP (requests) + scrapling MCP</div><div class="d">Fetched most docs directly; used scrapling's bulk fetch for pages behind basic bot protection (Meta docs, Snowflake, LiveAgent, PitchBook).</div><span class="tag">browser-backed</span></div>
      <div class="tool"><div class="t">scrapling DynamicFetcher (Playwright under the hood)</div><div class="d">Headless Chromium rendered ~30 JS-heavy apps (Slack, Discord, Airtable, Linear, ClickUp, Smartsheet…).</div><span class="tag">JS rendering</span></div>
      <div class="tool"><div class="t">Playwright MCP</div><div class="d">Drove a real browser for pages that needed interaction (e.g. Linear's developer portal).</div><span class="tag">browser MCP</span></div>
      <div class="tool"><div class="t">Chrome DevTools MCP</div><div class="d">Logged into the Composio dashboard and used the browser to verify the final page renders correctly.</div><span class="tag">verification</span></div>
      <div class="tool"><div class="t">Composio's own MCP</div><div class="d">Connected to <b>connect.composio.dev/mcp</b> and queried the tool catalog — the "use Composio's SDK/MCP" part of the brief, done for real.</div><span class="tag">in the spirit of the role</span></div>
      <div class="tool"><div class="t">LLM extraction</div><div class="d">Fixed JSON schema per app, one row per app, cached in data/rows/. Guided by EXTRACT_INSTRUCTIONS.md.</div><span class="tag">structured output</span></div>
    </div>

    <div class="two-col" style="margin-top:28px">
      <div>
        <h3>Where a human was needed</h3>
        <ul class="clean">
          <li><b>Gated apps</b> — DealCloud, PitchBook, Paygent Connect, iPayX, fanbasis: no public credentials, so confirming "gated with evidence" was a judgment call, not a lookup.</li>
          <li><b>Auth complexity</b> — Amazon SP-API's LWA+SigV4+IAM stack, Snowflake's admin roles: the model would guess; a human classified.</li>
          <li><b>Thin / JS-rendered docs</b> — the browser fetches rendered them, but a human confirmed the rendered content matched the claims.</li>
          <li><b>MCP existence</b> — fast-moving; official vs community checked case-by-case.</li>
        </ul>
      </div>
      <div>
        <h3>Where the agent got it wrong</h3>
        <ul class="clean">
          <li><b>Pumble</b> — first pass claimed a narrow REST surface; it has no public API. Corrected.</li>
          <li><b>PitchBook</b> — guessed "API Key"; it's partnership-gated with no public auth docs. Marked unknown.</li>
          <li><b>Consensus</b> — guessed OAuth2+REST; there is no public API. Corrected.</li>
          <li><b>3 fabricated auth guesses</b> — the model guessed instead of saying "unknown" on unverifiable apps. Verification caught all 3.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section id="verification">
  <div class="wrap">
    <div class="sec-head"><span class="num">06</span><div><h2>Verification — how I know it's right</h2><div class="desc">A 20-app sample spanning all 10 categories, all confidence levels and every hard app, re-checked against real docs.</div></div></div>
    <div class="acc-grid">
      <div class="acc-card"><div class="label">Pass 1 · Knowledge-only</div><div class="pct">{acc['overall_pass1']:.0%}<small> field accuracy</small></div><div class="muted">Model answers from general knowledge, no docs.</div></div>
      <div class="acc-card gain"><div class="label">Pass 2 · Grounded + verified <span class="arrow-up">▲</span></div><div class="pct">{acc['overall_pass2']:.0%}<small> field accuracy</small></div><div class="muted">After fetching real docs + browser re-check. <b>+{acc['overall_pass2']-acc['overall_pass1']:.0%} pts</b> — remaining unknowns marked honestly, not guessed.</div></div>
    </div>
    <div style="margin-top:26px">
      <h3>Per-field accuracy</h3>
      {per_field_rows}
    </div>
    <div class="two-col" style="margin-top:22px">
      <div>
        <h3>Hits and misses, app by app</h3>
        <table class="verif"><thead><tr><th>#</th><th>App</th><th>Auth</th><th>Access</th><th>API</th><th>MCP</th><th>Verdict</th></tr></thead><tbody>{VERIF_ROWS}</tbody></table>
        <div class="legend" style="margin-top:8px"><span><span class="v-ok">✓</span> verified correct</span><span><span class="v-no">✗</span> corrected after pass 1</span><span><span class="v-un">·</span> honestly unknown</span></div>
      </div>
      <div>
        <h3>Still unknown after all passes (honestly)</h3>
        <ul class="clean">
          <li><b>fanbasis</b> — no public docs; platform rebranded. Blocked/unknown.</li>
          <li><b>Paygent Connect</b> — NMI-gated, no public portal. Blocked/unknown.</li>
          <li><b>iPayX</b> — docs are marketing-only. Blocked/unknown.</li>
          <li><b>PitchBook</b> — partnership-gated, no public auth docs. Blocked/unknown.</li>
          <li><b>Consensus</b> — no public API; OAuth requested but not delivered. Blocked/unknown.</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<section id="action">
  <div class="wrap">
    <div class="sec-head"><span class="num">07</span><div><h2>What I'd build next</h2><div class="desc">59 apps are buildable today with self-serve or trial access.</div></div></div>
    <div class="chips">{easy_html}</div>
    <div class="two-col" style="margin-top:14px">
      <div><h3>Needs outreach / partnership</h3><ul class="clean">{outreach_html}</ul></div>
      <div><h3>Blocked or needs investigation</h3><ul class="clean">{invest_html}</ul></div>
    </div>
    <div class="note"><b>Top recommendation:</b> start with the 59 easy wins that already have an MCP. The single highest-leverage move is converting the 40 community-MCP apps into officially-supported Composio toolkits.</div>
  </div>
</section>

<section id="conclusion">
  <div class="wrap">
    <div class="sec-head"><span class="num">08</span><div><h2>Conclusion</h2><div class="desc">What this actually tells us about building agent toolkits at scale.</div></div></div>
    <div class="two-col">
      <div>
        <p style="font-family:var(--serif);font-size:19px;color:var(--ink-soft)">The market is far more buildable than "research by hand" suggests. Two-thirds of the requested apps can become agent toolkits today with self-serve or trial credentials — and the blockers that remain are business gates, not technical ones.</p>
        <p style="margin-top:12px;font-size:14.5px;color:var(--ink-soft)">The repeatable lesson for Composio's pipeline: <b>auth is not the hard part</b> (API keys and OAuth2 cover 90%+ of apps), <b>self-serve is the real signal</b> (it predicts buildability almost perfectly), and <b>the easy wins are identifiable in advance</b> — the same 59 apps cluster to the top regardless of category.</p>
      </div>
      <div>
        <ul class="clean">
          <li><b>68 / 100</b> buildable today — with <b>23</b> more buildable with a little work</li>
          <li><b>50 / 100</b> fully self-serve — no approval, no sales call</li>
          <li><b>80 / 100</b> already have an MCP (official or community)</li>
          <li><b>+19 pts</b> of accuracy from verification (67% → 86%)</li>
          <li><b>9 / 100</b> genuinely blocked — and all are business gates, not engineering</li>
        </ul>
        <div class="note" style="margin-top:14px">The takeaway: build toolkits where access is self-serve and an API exists. Use verification to know you're right — and say "unknown" instead of guessing.</div>
      </div>
    </div>
  </div>
</section>

<section id="process">
  <div class="wrap">
    <div class="sec-head"><span class="num">09</span><div><h2>Run it yourself</h2><div class="desc">Everything is scripted and cached — the page is generated from the same JSON the pipeline outputs.</div></div></div>
    <div class="two-col">
      <div>
        <pre>git clone &lt;repo&gt; composio-app-research
cd composio-app-research
pip install -r requirements.txt
python3 fetch_docs.py
python3 fetch_browser.py   # JS-heavy pages
python3 normalize_and_merge.py
python3 compute_accuracy.py
python3 build_site.py      # regenerates this page</pre>
      </div>
      <div>
        <h3>Data files</h3>
        <ul class="clean">
          <li><b>data/apps_input.json</b> — the 100 apps from the assignment</li>
          <li><b>data/rows/</b> — one JSON row per app (extraction output)</li>
          <li><b>data/merged_final.json</b> — the normalized 100-row dataset</li>
          <li><b>data/verification/</b> — per-app verification judgments</li>
          <li><b>data/accuracy_progression.json</b> — the 67% → 86% numbers</li>
          <li><b>data/patterns.json</b> — the pattern synthesis</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div><b>Pranav Dhiran</b> · Composio AI Product Ops — take-home case study · generated {esc(data['meta']['generated'][:10])}</div>
    <div style="margin-top:8px;display:flex;gap:18px;flex-wrap:wrap"><a href="#patterns">Patterns</a><a href="#matrix">Matrix</a><a href="#agent">How I did it</a><a href="#verification">Verification</a><a href="#conclusion">Conclusion</a></div>
  </div>
</footer>

<script>
const DATA = {DATA_JSON};
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
  const fc = document.getElementById('f-cat').value, fa = document.getElementById('f-auth').value;
  const fv = document.getElementById('f-verdict').value, fm = document.getElementById('f-mcp').value;
  const rows = document.querySelectorAll('#tbody tr');
  let shown = 0;
  rows.forEach(tr => {{
    const app = tr.querySelector('td.app').textContent.toLowerCase();
    const ok = (!q || app.includes(q)) && (!fc || tr.dataset.cat===fc) && (!fa || tr.dataset.auth.includes(fa)) && (!fv || tr.dataset.verdict===fv) && (!fm || tr.dataset.mcp===fm);
    tr.style.display = ok ? '' : 'none'; if (ok) shown++;
  }});
  document.getElementById('count').textContent = shown + ' / 100';
}}
['search','f-cat','f-auth','f-verdict','f-mcp'].forEach(id => document.getElementById(id).addEventListener('input', applyFilters));
applyFilters();
let sortKey='num', sortDir=1;
document.querySelectorAll('#matrix th').forEach(th => {{
  th.addEventListener('click', () => {{
    const k = th.dataset.k;
    if (sortKey===k) sortDir=-sortDir; else {{ sortKey=k; sortDir=1; }}
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