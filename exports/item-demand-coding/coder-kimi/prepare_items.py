"""Emit items-to-code.jsonl for the independent item-demand coding pass.

Universe: the 358 NY Regents Algebra I items present in both
exports/addendum-gpu/masked-stem-7b-items.jsonl and
exports/print-faithful/fidelity-items.jsonl (the fidelity file is an exact
subset of the masked-stem file for algebra-i).

Output record: {id, stem, options, source} sorted by id. All key / prediction
/ score fields are stripped by construction (they are never copied).

Source preference:
  1. relocated VLM transcription (exports/print-faithful/relocated-items.jsonl)
     when present with a non-empty stem and four non-empty options;
  2. VLM transcription (vlmStem / vlmOptions in fidelity-items.jsonl) when
     non-empty stem and four non-empty options;
  3. text layer (textLayerStem / textLayerOptions in fidelity-items.jsonl,
     falling back to data/items.jsonl stem / choices).
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MASKED = REPO / "exports/addendum-gpu/masked-stem-7b-items.jsonl"
FIDELITY = REPO / "exports/print-faithful/fidelity-items.jsonl"
RELOCATED = REPO / "exports/print-faithful/relocated-items.jsonl"
ITEMS = REPO / "data/items.jsonl"
OUT = Path(__file__).resolve().parent / "items-to-code.jsonl"

LETTERS = ("A", "B", "C", "D")


def complete(stem: object, options: object) -> bool:
    if not isinstance(stem, str) or not stem.strip():
        return False
    if not isinstance(options, dict):
        return False
    return all(str(options.get(letter, "")).strip() for letter in LETTERS)


def main() -> None:
    masked_ids: set[str] = set()
    with MASKED.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record["id"].startswith("nyregents-algebra-i-"):
                masked_ids.add(record["id"])

    fidelity: dict[str, dict] = {}
    with FIDELITY.open() as handle:
        for line in handle:
            record = json.loads(line)
            if record["id"].startswith("nyregents-algebra-i-"):
                fidelity[record["id"]] = record

    relocated: dict[str, dict] = {}
    if RELOCATED.exists():
        with RELOCATED.open() as handle:
            for line in handle:
                record = json.loads(line)
                if record["id"].startswith("nyregents-algebra-i-"):
                    relocated[record["id"]] = record

    items: dict[str, dict] = {}
    with ITEMS.open() as handle:
        for line in handle:
            record = json.loads(line)
            items[record["id"]] = record

    universe = sorted(masked_ids & set(fidelity))
    assert len(universe) == 358, f"expected 358 items, got {len(universe)}"

    rows = []
    for item_id in universe:
        fid = fidelity[item_id]
        stem = options = None
        source = None

        rel = relocated.get(item_id)
        if rel and complete(rel.get("vlmStem"), rel.get("vlmOptions")):
            stem = rel["vlmStem"].strip()
            options = rel["vlmOptions"]
            source = "vlm-relocated"
        elif complete(fid.get("vlmStem"), fid.get("vlmOptions")):
            stem = fid["vlmStem"].strip()
            options = fid["vlmOptions"]
            source = "vlm"
        else:
            stem = (fid.get("textLayerStem") or "").strip()
            options = fid.get("textLayerOptions") or {}
            source = "text"
            if not complete(stem, options):
                fallback = items.get(item_id, {})
                stem = (fallback.get("stem") or stem).strip()
                options = fallback.get("choices") or options
                source = "text-items-jsonl"

        ordered_options = {letter: str(options.get(letter, "")).strip() for letter in LETTERS}
        rows.append({"id": item_id, "stem": stem, "options": ordered_options, "source": source})

    with OUT.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    from collections import Counter

    counts = Counter(row["source"] for row in rows)
    print(f"wrote {len(rows)} rows to {OUT}")
    print("sources:", dict(counts))
    incomplete = [row["id"] for row in rows if not complete(row["stem"], row["options"])]
    print("rows with missing stem/options:", incomplete)


if __name__ == "__main__":
    main()
