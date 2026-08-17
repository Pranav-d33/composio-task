#!/usr/bin/env python3
"""Fix categories to canonical 10 from apps_input.json, then rebuild site_data.json."""
import json, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

input_data = json.load(open(os.path.join(BASE, "data", "apps_input.json")))
cat_map = {}
for c in input_data["categories"]:
    for a in c["apps"]:
        cat_map[a["num"]] = c["name"]

merged = json.load(open(os.path.join(BASE, "data", "merged_final.json")))
for r in merged["rows"]:
    r["category"] = cat_map.get(r["num"], r["category"])
json.dump(merged, open(os.path.join(BASE, "data", "merged_final.json"), "w"), indent=1)
print("Fixed categories:", dict(Counter(r["category"] for r in merged["rows"])))

# Rebuild site_data.json with canonical categories
rows = merged["rows"]
patterns = json.load(open(os.path.join(BASE, "data", "patterns.json")))
acc = json.load(open(os.path.join(BASE, "data", "accuracy_progression.json")))

compact = []
for r in rows:
    compact.append({
        'num': r['num'], 'app': r['app'], 'category': r['category'],
        'one_line': r.get('one_line',''),
        'auth': r.get('auth_methods_normalized', []),
        'self_serve': r.get('self_serve',''),
        'gate': r.get('gate_type','none'),
        'protocol': r.get('api_surface',{}).get('protocol',[]),
        'breadth': r.get('api_surface',{}).get('breadth',''),
        'webhooks': r.get('api_surface',{}).get('webhooks',False),
        'mcp': 'official' if r.get('existing_mcp',{}).get('official') else ('community' if r.get('existing_mcp',{}).get('community') else 'none'),
        'verdict': r.get('buildability_verdict',''),
        'blocker_class': r.get('blocker_class'),
        'ttc': r.get('time_to_first_call',''),
        'confidence': r.get('confidence',''),
        'evidence': r.get('evidence',{}).get('docs',''),
        'agent_notes': r.get('agent_notes','')[:200],
    })

bundle = {
    'meta': {
        'title': 'Composio AI Product Ops — Take-home Case Study',
        'author': 'Pranav Dhiran',
        'generated': merged['generated'],
        'total': len(compact),
    },
    'rows': compact,
    'patterns': patterns,
    'accuracy': acc,
}
json.dump(bundle, open(os.path.join(BASE, "site_data.json"), "w"), indent=1)
print(f"Rebuilt site_data.json with {len(compact)} rows, categories = 10 canonical")
print("Category set:", sorted(set(r['category'] for r in compact)))