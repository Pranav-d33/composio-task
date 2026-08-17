#!/usr/bin/env python3
"""Correct Composio toolkit coverage audit.

Uses `composio dev toolkits list --query <app>` — the authoritative catalog
query — to determine whether Composio has a native toolkit for each app.
Unlike `composio search` (a fuzzy tool finder that returns unrelated tools),
this only matches real toolkit slugs by name.

Output: data/composio_coverage.json with a per-app record:
  found (bool), toolkit (slug), tools_count (int), description
A record is also written to data/composio_coverage.json.
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE, "data", "apps_input.json")) as f:
    data = json.load(f)

all_apps = []
for category in data["categories"]:
    for app in category["apps"]:
        all_apps.append(app)

print(f"Analyzing {len(all_apps)} apps via 'composio dev toolkits list'...\n", file=sys.stderr)

coverage = []

for i, app in enumerate(all_apps, 1):
    app_name = app["name"]
    num = app["num"]
    query = app_name.split(" (")[0].split(" (")[0]  # strip parenthetical hints

    print(f"[{i:3d}/100] {app_name} ... ", file=sys.stderr, end="", flush=True)

    # Use the full app name as the query (multi-word matches better).
    # Strip parenthetical hints, TLDs, and normalize known aliases.
    q = app_name
    if " (" in q:
        q = q.split(" (")[0]
    q = q.replace(".com", "").replace(".io", "").replace(".ai", "")
    # known slug aliases where the name doesn't map to the slug
    alias = {
        "Salesforce Commerce Cloud": "salesforce",
        "Salesforce": "salesforce",
        "Magento": "magento",
        "Monday.com": "monday",
        "WhatsApp Business": "whatsapp",
        "Google Ads": "google ads",
        "Meta Ads": "meta ads",
        "LinkedIn Ads": "linkedin",
        "NotebookLM": "notebook lm",
        "Zoho CRM": "zoho",          # Composio ships a shared 'zoho' toolkit
        "YouTube Transcript": "youtube transcript",
        "Salesforce": "salesforce",
    }
    q = alias.get(app_name.split(" (")[0], q)

    try:
        result = subprocess.run(
            ["composio", "dev", "toolkits", "list", "--query", q, "--limit", "20"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"ERROR (code {result.returncode})", file=sys.stderr)
            coverage.append({
                "num": num, "app": app_name, "found": False, "toolkit": None,
                "tools_count": 0, "description": "",
                "notes": f"command failed: {result.stderr[:80]}",
            })
            continue

        results = json.loads(result.stdout)
        if not results:
            print("NOT FOUND", file=sys.stderr)
            coverage.append({
                "num": num, "app": app_name, "found": False, "toolkit": None,
                "tools_count": 0, "description": "", "notes": "no native toolkit",
            })
            continue

        # Score: prefer an exact slug or name match on the cleaned app name.
        # Strong match = the toolkit slug/name equals the app name or contains
        # the app name as a whole token. Weak/partial matches are rejected.
        app_l = q.lower().replace(".", "").replace("/", " ")
        app_keywords = [w for w in app_l.replace("_", " ").split() if len(w) > 2]

        def score(t):
            s = (t.get("slug", "") + " " + t.get("name", "")).lower()
            # exact slug equality is the strongest signal
            if t.get("slug", "").lower() in (app_l, app_l.replace(" ", "_")):
                return 3
            # full name appears in the toolkit name/slug
            if app_l in s:
                return 2
            # all distinctive keywords present
            if app_keywords and all(k in s for k in app_keywords):
                return 2
            # half the keywords present (partial, treated as weak)
            hits = sum(1 for k in app_keywords if k in s)
            if app_keywords and hits >= max(1, len(app_keywords) - 1):
                return 1
            return 0

        scored = [(score(t), t) for t in results]
        best = max(scored, key=lambda x: x[0]) if scored else (0, None)
        s, best_toolkit = best
        if s < 2 or best_toolkit is None:
            # only exact/strong matches count as "found"
            print(f"NO STRONG MATCH (closest={best_toolkit.get('slug') if best_toolkit else None})", file=sys.stderr)
            coverage.append({
                "num": num, "app": app_name, "found": False, "toolkit": None,
                "tools_count": 0, "description": "",
                "notes": f"closest was {best_toolkit.get('slug') if best_toolkit else None} but no strong match",
            })
            continue

        print(f"FOUND {best_toolkit.get('slug')} ({best_toolkit.get('tools_count')} tools)", file=sys.stderr)
        coverage.append({
            "num": num, "app": app_name, "found": True,
            "toolkit": best_toolkit.get("slug"),
            "tools_count": best_toolkit.get("tools_count", 0),
            "description": best_toolkit.get("description", ""),
            "notes": "",
        })
    except subprocess.TimeoutExpired:
        print("TIMEOUT", file=sys.stderr)
        coverage.append({
            "num": num, "app": app_name, "found": False, "toolkit": None,
            "tools_count": 0, "description": "", "notes": "timeout",
        })
    except Exception as e:
        print(f"ERROR {e}", file=sys.stderr)
        coverage.append({
            "num": num, "app": app_name, "found": False, "toolkit": None,
            "tools_count": 0, "description": "", "notes": f"error: {str(e)[:60]}",
        })

out_path = os.path.join(BASE, "data", "composio_coverage.json")
with open(out_path, "w") as f:
    json.dump(coverage, f, indent=2)

print(f"\nCoverage analysis complete. Results saved to {out_path}", file=sys.stderr)

found = sum(1 for c in coverage if c["found"])
print(f"\n=== SUMMARY ===", file=sys.stderr)
print(f"Total apps: {len(coverage)}", file=sys.stderr)
print(f"Native toolkit found: {found} ({100*found/len(coverage):.1f}%)", file=sys.stderr)
print(f"No native toolkit: {len(coverage)-found} ({100*(len(coverage)-found)/len(coverage):.1f}%)", file=sys.stderr)
