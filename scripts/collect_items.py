#!/usr/bin/env python3
"""Concatenate corpus JSONL files into data/items.jsonl and validate ids."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "data" / "timss_complete.jsonl",
    ROOT / "data" / "timss_historical.jsonl",
    ROOT / "data" / "pisa2012.jsonl",
    ROOT / "data" / "pisa.jsonl",
    ROOT / "data" / "eureka.jsonl",
    ROOT / "data" / "staar.jsonl",
    ROOT / "data" / "nysed.jsonl",
    ROOT / "data" / "mcas.jsonl",
    ROOT / "data" / "naplan.jsonl",
    ROOT / "data" / "nyregents.jsonl",
    ROOT / "data" / "eqao.jsonl",
]
OUT = ROOT / "data" / "items.jsonl"


def main() -> None:
    rows: list[dict] = []
    seen: set[str] = set()
    for path in SOURCES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("id") in seen:
                continue
            seen.add(rec["id"])
            rows.append(rec)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    from collections import Counter

    print(f"wrote {len(rows)} items -> {OUT}")
    print("by corpus:", dict(Counter(r["corpus"] for r in rows)))
    print("by type:", dict(Counter(r["responseType"] for r in rows)))


if __name__ == "__main__":
    main()
