#!/usr/bin/env python3
"""Write primary-population item-id lists for the masked-stem follow-up."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "exports" / "addendum-gpu"
STATS_PATH = OUT_DIR / "masked-stem-item-mask-stats.jsonl"
PRIMARY_IDS_PATH = OUT_DIR / "masked-stem-primary-item-ids.json"
ALGEBRA_IDS_PATH = OUT_DIR / "masked-stem-algebra-primary-item-ids.json"
ALGEBRA_CELLS = ("nyregents::algebra-i", "nyregents::algebra-ii")


def load_stats(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    stats = load_stats(STATS_PATH)
    primary = [
        str(row["id"])
        for row in stats
        if int(row["masked_token_count"]) >= 1
    ]
    algebra = [
        str(row["id"])
        for row in stats
        if int(row["masked_token_count"]) >= 1
        and str(row.get("cell")) in ALGEBRA_CELLS
    ]
    n_algebra_i = sum(
        1
        for row in stats
        if int(row["masked_token_count"]) >= 1
        and str(row.get("cell")) == "nyregents::algebra-i"
    )
    n_algebra_ii = sum(
        1
        for row in stats
        if int(row["masked_token_count"]) >= 1
        and str(row.get("cell")) == "nyregents::algebra-ii"
    )
    if len(primary) != 1215:
        raise RuntimeError(f"expected 1215 primary ids, got {len(primary)}")
    if n_algebra_i != 358 or n_algebra_ii != 248:
        raise RuntimeError(
            f"expected Algebra I 358 and Algebra II 248, got {n_algebra_i} and {n_algebra_ii}"
        )
    if len(algebra) != n_algebra_i + n_algebra_ii:
        raise RuntimeError(f"algebra id count mismatch: {len(algebra)}")
    PRIMARY_IDS_PATH.write_text(json.dumps(primary, indent=2) + "\n", encoding="utf-8")
    ALGEBRA_IDS_PATH.write_text(json.dumps(algebra, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "primaryN": len(primary),
                "algebraN": len(algebra),
                "algebraI": n_algebra_i,
                "algebraII": n_algebra_ii,
                "primaryPath": str(PRIMARY_IDS_PATH.relative_to(ROOT)),
                "algebraPath": str(ALGEBRA_IDS_PATH.relative_to(ROOT)),
            }
        )
    )


if __name__ == "__main__":
    main()
