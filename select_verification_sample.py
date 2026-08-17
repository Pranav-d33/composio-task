#!/usr/bin/env python3
"""Stratified sample: max 2 per category, mix of confidence + verdicts, include hard ones."""
import json, random, os

BASE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(BASE, "data", "merged_final.json")))["rows"]
by_num = {r["num"]: r for r in rows}

random.seed(7)
SAMPLE_SIZE = 20

# hard/obscure apps that MUST be verified honestly (spread across categories)
force = [10, 25, 44, 50, 58, 84, 85, 90, 91, 94]  # DealCloud, Pumble, SFCC, fanbasis, Sherlock, Paygent, iPayX, PitchBook, NotebookLM, Consensus

selected = [n for n in force if n in by_num]
selected_by_cat = {}
for n in selected:
    c = by_num[n]["category"]
    selected_by_cat.setdefault(c, []).append(n)

# fill up: 2 per category, prefer lower-confidence (harder) rows first
candidates = [r for r in rows if r["num"] not in selected]
by_cat = {}
for r in candidates:
    by_cat.setdefault(r["category"], []).append(r)

# shuffle each category's pool, then sort by confidence (low->high) so we bias toward verifying the uncertain ones
for c in by_cat:
    random.shuffle(by_cat[c])
    by_cat[c].sort(key=lambda r: {"low": 0, "medium": 1, "high": 2}.get(r["confidence"], 3))

for cat in by_cat:
    if len(selected) >= SAMPLE_SIZE:
        break
    cur = len(selected_by_cat.get(cat, []))
    need = 2 - cur
    for r in by_cat[cat]:
        if need <= 0 or len(selected) >= SAMPLE_SIZE:
            break
        selected.append(r["num"])
        selected_by_cat.setdefault(cat, []).append(r["num"])
        need -= 1

selected.sort()
sample = [by_num[n] for n in selected]

# category coverage report
print(f"Sample of {len(sample)}:")
cats = {}
for s in sample:
    cats.setdefault(s["category"], []).append(s["app"])
    print(f"  {s['num']:3d} {s['app']:28s} {s['category']:32s} conf={s['confidence']:6s} verdict={s['buildability_verdict']}")
print(f"\nCategories covered: {len(cats)}/10")
conf_counts = {}
for s in sample:
    conf_counts[s["confidence"]] = conf_counts.get(s["confidence"], 0) + 1
print("Confidence mix:", conf_counts)

out = os.path.join(BASE, "data", "verification_sample.json")
json.dump({
    "seed": 7,
    "count": len(sample),
    "sample": [{"num": r["num"], "app": r["app"], "category": r["category"],
                "confidence": r["confidence"], "verdict": r["buildability_verdict"],
                "docs_url": r.get("evidence", {}).get("docs", "")} for r in sample]
}, open(out, "w"), indent=1)
print(f"\nWrote {out}")