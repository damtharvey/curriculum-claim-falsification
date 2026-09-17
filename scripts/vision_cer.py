#!/usr/bin/env python3
"""Character error rate of a vision transcript vs PDF text layer. Validation only."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def cer(ref: str, hyp: str) -> float:
    r = list(normalize(ref))
    h = list(normalize(hyp))
    if not r:
        return 0.0 if not h else 1.0
    # Levenshtein
    prev = list(range(len(h) + 1))
    for i, rc in enumerate(r, start=1):
        cur = [i]
        for j, hc in enumerate(h, start=1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if rc == hc else 1)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1] / len(r)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", required=True, help="JSON list of {reference, hypothesis, page}")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    pairs = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
    rows = []
    for p in pairs:
        rate = cer(p["reference"], p["hypothesis"])
        rows.append({"page": p.get("page"), "cer": rate, "refChars": len(normalize(p["reference"]))})
    mean = sum(r["cer"] for r in rows) / len(rows) if rows else None
    out = {"n": len(rows), "meanCer": mean, "pages": rows}
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"n": len(rows), "meanCer": mean}))


if __name__ == "__main__":
    main()
