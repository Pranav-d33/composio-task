#!/usr/bin/env python3
"""Convert cached HTML docs to clean text for extraction. Output: data/text/NN_name.txt"""
import os, re, json
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw_docs")
OUT = os.path.join(BASE, "data", "text")
os.makedirs(OUT, exist_ok=True)

def html_to_text(html):
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        t.decompose()
    text = soup.get_text(separator="\n")
    lines = [re.sub(r"\s+", " ", l).strip() for l in text.splitlines()]
    lines = [l for l in lines if l and len(l) > 2]
    return "\n".join(lines)

total = 0
for fn in sorted(os.listdir(RAW)):
    if not fn.endswith(".html"):
        continue
    path = os.path.join(RAW, fn)
    outfn = fn.replace(".html", ".txt")
    outpath = os.path.join(OUT, outfn)
    if os.path.exists(outpath):
        continue
    try:
        html = open(path, errors="ignore").read()
        text = html_to_text(html)
        with open(outpath, "w") as f:
            f.write(text)
        print(f"{fn}: {len(text)} chars")
        total += 1
    except Exception as e:
        print(f"{fn}: ERR {e}")

print(f"\nConverted {total} files. Total files now: {len(os.listdir(OUT))}")