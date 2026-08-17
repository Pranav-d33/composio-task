#!/usr/bin/env python3
"""Refine blocker taxonomy from agent_notes + blocker text into 6 clean classes.
Updates data/patterns.json with blocker_breakdown."""
import json, os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(BASE, "data", "merged_final.json")))["rows"]

def classify(r):
    blk = (r.get("blocker") or "") + " " + (r.get("agent_notes") or "")
    low = blk.lower()
    if r["buildability_verdict"] == "buildable_today":
        return None
    # order matters: most specific first
    if "no public api" in low or "no api" in low or "no developer portal" in low \
       or "no public documentation" in low or "marketing content only" in low \
       or "undocumented" in low or "no api surface" in low:
        return "No public API / undocumented"
    if "not a saas" in low or ("self-host" in low and "cli" in low):
        return "Not a SaaS (CLI / self-hosted)"
    if "partnership" in low or "contact sales" in low or "sales contact" in low \
       or "enterprise" in low or "client credentials" in low or "sales-gated" in low \
       or "gated" in low:
        return "Enterprise / partnership gated"
    if "app review" in low or "advanced access" in low or "marketing api approval" in low \
       or "token approval" in low or "production approval" in low or "verification" in low:
        return "App review / production approval required"
    if "lwa" in low or "sigv4" in low or "per-role registration" in low or "registration flow" in low \
       or "registration" in low or "auth" in low and "complex" in low:
        return "Complex auth / registration flow"
    if "thin" in low or "not confirmed" in low or "not documented" in low or "limited" in low \
       or "marketing/learning material" in low or "partial" in low:
        return "Thin / unverified docs"
    if "paid" in low or "subscription" in low or "account required" in low or "admin" in low \
       or "account" in low and "approval" in low:
        return "Paid plan / account required"
    return "Other"

counts = Counter()
examples = {}
for r in rows:
    c = classify(r)
    if c:
        counts[c] += 1
        examples.setdefault(c, []).append(r["app"])

print("BLOCKER TAXONOMY (32 non-buildable apps):")
for c, n in counts.most_common():
    print(f"  {n:2d}  {c}")
    print(f"        e.g. {', '.join(examples[c][:4])}")

# attach to each row
for r in rows:
    r["blocker_class"] = classify(r)

json.dump(json.load(open(os.path.join(BASE, "data", "merged_final.json"))), open(os.path.join(BASE, "data", "merged_final.json"), "w"), indent=1)

# update patterns.json
patterns = json.load(open(os.path.join(BASE, "data", "patterns.json")))
patterns["blocker_breakdown"] = dict(counts)
patterns["blocker_examples"] = examples
json.dump(patterns, open(os.path.join(BASE, "data", "patterns.json"), "w"), indent=1)
print("\nUpdated data/patterns.json")