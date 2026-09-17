#!/usr/bin/env python3
"""Concatenate corpus JSONL files into data/items.jsonl and validate ids."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SOURCES = [
    ROOT / "data" / "timss_complete.jsonl",
    ROOT / "data" / "timss_historical.jsonl",
    ROOT / "data" / "pisa2012.jsonl",
    ROOT / "data" / "pisa.jsonl",
    ROOT / "data" / "staar.jsonl",
    ROOT / "data" / "nysed.jsonl",
    ROOT / "data" / "mcas.jsonl",
    ROOT / "data" / "naplan.jsonl",
    ROOT / "data" / "nyregents.jsonl",
    ROOT / "data" / "eqao.jsonl",
]
OUT = ROOT / "data" / "items.jsonl"


def main() -> None:
    missing = [path for path in REQUIRED_SOURCES if not path.is_file()]
    if missing:
        names = ", ".join(path.relative_to(ROOT).as_posix() for path in missing)
        raise SystemExit(
            "required corpus jsonl missing (run scripts/bootstrap_data.py): " + names
        )
    rows: list[dict] = []
    seen: set[str] = set()
    empty: list[str] = []
    for path in REQUIRED_SOURCES:
        n_before = len(rows)
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            item_id = rec.get("id")
            if item_id in seen:
                continue
            seen.add(item_id)
            rows.append(rec)
        if len(rows) == n_before:
            empty.append(path.relative_to(ROOT).as_posix())
    if empty:
        raise SystemExit("required corpus jsonl is empty: " + ", ".join(empty))
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {len(rows)} items -> {OUT.relative_to(ROOT)}")
    print("by corpus:", dict(Counter(r["corpus"] for r in rows)))
    print("by type:", dict(Counter(r["responseType"] for r in rows)))


if __name__ == "__main__":
    main()
