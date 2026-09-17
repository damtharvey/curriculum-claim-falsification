#!/usr/bin/env python3
"""Build blinded choices-only batches. Prompt has opaque ids and shuffled options only."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "data" / "items.jsonl"
OUT_DIR = ROOT / "exports" / "choices-only" / "batches"
BATCH_SIZE = 50


def opaque_id(item_id: str) -> str:
    return hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:12]


def shuffle_choices(item_id: str, choices: dict[str, str], key: str) -> tuple[dict[str, str], str, dict[str, str]]:
    rng = random.Random(hashlib.sha256(f"shuffle:{item_id}".encode()).hexdigest())
    pairs = list(choices.items())
    rng.shuffle(pairs)
    letters = [chr(ord("A") + i) for i in range(len(pairs))]
    shuffled: dict[str, str] = {}
    new_from_old: dict[str, str] = {}
    for new_letter, (old_letter, text) in zip(letters, pairs):
        shuffled[new_letter] = text
        new_from_old[old_letter] = new_letter
    new_key = new_from_old.get(key.upper(), "")
    return shuffled, new_key, new_from_old


def load_selected(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("responseType") != "selected":
            continue
        choices = rec.get("choices") or {}
        if len(choices) < 2:
            continue
        rows.append(rec)
    return rows


def prompt_for(batch: list[dict]) -> str:
    lines = [
        "Answer from this text only. Do not use any tool. Return JSON {id: letter}.",
        "Each id is opaque. You see only the answer options, in shuffled order with relabeled letters.",
        "There is no question stem and no source. Pick the letter that looks most likely to be correct from the option text alone.",
        "Return a single JSON object mapping each id to one letter (A, B, C, D, or E).",
        "",
        "Items:",
    ]
    for rec in batch:
        opts = " | ".join(f"{k}) {v}" for k, v in rec["options"].items())
        lines.append(f"{rec['opaqueId']}: {opts}")
    return "\n".join(lines) + "\n"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ITEMS
    items = load_selected(src)
    already: set[str] = set()
    if OUT_DIR.exists():
        for map_file in OUT_DIR.glob("batch-*.map.json"):
            for rec in json.loads(map_file.read_text(encoding="utf-8")):
                already.add(rec["itemId"])
    new_items = [rec for rec in items if rec["id"] not in already]
    print(f"selected {len(items)} already-batched {len(already)} new {len(new_items)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing_nums = [
        int(p.stem.split("-")[1])
        for p in OUT_DIR.glob("batch-*.prompt.txt")
        if p.stem.split("-")[1].isdigit()
    ]
    n_batches = max(existing_nums) if existing_nums else 0
    maps: list[dict] = []
    prompt_items: list[dict] = []
    for rec in new_items:
        opaque = opaque_id(rec["id"])
        shuffled, new_key, mapping = shuffle_choices(rec["id"], rec["choices"], rec["key"])
        maps.append(
            {
                "itemId": rec["id"],
                "opaqueId": opaque,
                "corpus": rec.get("corpus"),
                "authority": rec.get("authority"),
                "claim": rec.get("claim"),
                "originalKey": rec["key"],
                "shuffledKey": new_key,
                "letterMapOldToNew": mapping,
                "nOptions": len(shuffled),
            }
        )
        prompt_items.append({"opaqueId": opaque, "options": shuffled, "map": maps[-1]})

    wrote = 0
    for start in range(0, len(prompt_items), BATCH_SIZE):
        chunk = prompt_items[start : start + BATCH_SIZE]
        n_batches += 1
        wrote += 1
        bid = f"{n_batches:03d}"
        prompt_rows = [{"opaqueId": r["opaqueId"], "options": r["options"]} for r in chunk]
        map_rows = [r["map"] for r in chunk]
        (OUT_DIR / f"batch-{bid}.prompt.txt").write_text(prompt_for(prompt_rows), encoding="utf-8")
        (OUT_DIR / f"batch-{bid}.map.json").write_text(json.dumps(map_rows, indent=2), encoding="utf-8")
        (OUT_DIR / f"batch-{bid}.ids.txt").write_text(
            "\n".join(r["itemId"] for r in map_rows) + "\n", encoding="utf-8"
        )
        print(f"batch-{bid} n={len(chunk)}")
    print(f"wrote {wrote} new batches covering {len(new_items)} selected items")


if __name__ == "__main__":
    main()
