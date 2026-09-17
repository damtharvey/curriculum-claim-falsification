"""Emit items-to-code.jsonl for the 358 NY Regents Algebra I masked-stem items.

Outputs only {id, stem, options, source} per line, sorted by id, with all
key/prediction/score fields stripped so the coder is blind to the answer key
and to any model prediction.

Source priority for stem + options:
  1. exports/repaired-layer/repaired-items.jsonl  (if it exists) -- repaired VLM
  2. exports/print-faithful/fidelity-items.jsonl   -- VLM transcription
     (vlmStem + vlmOptions), preferred over the text layer when present.
  3. data/items.jsonl                              -- text layer fallback
     (stem + choices), used when no VLM transcription is available.

The 358-item population is the masked-stem primary population for Algebra I:
corpus == "nyregents", id matches ^nyregents-algebra-i-, and
masked_token_count >= 1 (from masked-stem-item-mask-stats.jsonl).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MASK_STATS = REPO / "exports/addendum-gpu/masked-stem-item-mask-stats.jsonl"
FIDELITY = REPO / "exports/print-faithful/fidelity-items.jsonl"
REPAIRED = REPO / "exports/repaired-layer/repaired-items.jsonl"
ITEMS = REPO / "data/items.jsonl"
OUT = REPO / "exports/item-demand-coding/coder-glm/items-to-code.jsonl"

ALG_I_PREFIX = re.compile(r"^nyregents-algebra-i-")


def load_target_ids() -> set[str]:
    """Algebra I items with at least one masked token (primary population)."""
    ids: set[str] = set()
    with MASK_STATS.open() as f:
        for line in f:
            d = json.loads(line)
            if (
                d.get("corpus") == "nyregents"
                and ALG_I_PREFIX.match(d["id"])
                and d.get("masked_token_count", 0) >= 1
            ):
                ids.add(d["id"])
    return ids


def load_repaired() -> dict[str, dict]:
    if not REPAIRED.exists():
        return {}
    out: dict[str, dict] = {}
    with REPAIRED.open() as f:
        for line in f:
            d = json.loads(line)
            stem = d.get("stem") or d.get("vlmStem")
            opts = d.get("options") or d.get("vlmOptions")
            if stem and opts:
                out[d["id"]] = {"stem": stem, "options": opts, "source": "repaired-vlm"}
    return out


def load_fidelity_vlm() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with FIDELITY.open() as f:
        for line in f:
            d = json.loads(line)
            stem = d.get("vlmStem")
            opts = d.get("vlmOptions")
            if stem and opts:
                out[d["id"]] = {"stem": stem, "options": opts, "source": "vlm"}
    return out


def load_text_layer() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with ITEMS.open() as f:
        for line in f:
            d = json.loads(line)
            stem = d.get("stem")
            opts = d.get("choices")
            if stem and opts:
                out[d["id"]] = {"stem": stem, "options": opts, "source": "text-layer"}
    return out


def normalize_options(opts: dict) -> dict[str, str]:
    """Return options keyed by letter with string values, sorted A,B,C,D,..."""
    norm: dict[str, str] = {}
    for k, v in opts.items():
        norm[str(k)] = str(v)
    return dict(sorted(norm.items()))


def main() -> None:
    target_ids = load_target_ids()
    repaired = load_repaired()
    vlm = load_fidelity_vlm()
    text = load_text_layer()

    rows: list[dict] = []
    for item_id in sorted(target_ids):
        rec = repaired.get(item_id) or vlm.get(item_id) or text.get(item_id)
        if rec is None:
            # Last resort: text-layer fields from fidelity if present.
            rows.append(
                {
                    "id": item_id,
                    "stem": "",
                    "options": {},
                    "source": "missing",
                }
            )
            continue
        rows.append(
            {
                "id": item_id,
                "stem": rec["stem"],
                "options": normalize_options(rec["options"]),
                "source": rec["source"],
            }
        )

    with OUT.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    from collections import Counter

    src_counts = Counter(r["source"] for r in rows)
    missing = [r["id"] for r in rows if r["source"] == "missing" or not r["stem"]]
    print(f"wrote {len(rows)} items to {OUT}")
    print("by source:", dict(src_counts))
    print("missing/empty:", len(missing), missing[:10])


if __name__ == "__main__":
    main()
