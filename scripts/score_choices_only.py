#!/usr/bin/env python3
"""Score choices-only subagent JSON against shuffled keys. Writes channel-audit.json."""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BATCH_DIR = ROOT / "exports" / "choices-only" / "batches"
AUDIT_PATH = ROOT / "exports" / "channel-audit.json"
PRED_DIR = ROOT / "exports" / "choices-only" / "predictions"


def bootstrap_ci(flags: list[int], n_boot: int = 1000, seed: int = 11) -> tuple[float, float]:
    """Percentile bootstrap. Do not use LCG ``x % n``: that is degenerate when n is a power of two."""
    if not flags:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(flags)
    samples: list[float] = []
    for _ in range(n_boot):
        tot = 0
        for _i in range(n):
            tot += flags[rng.randrange(n)]
        samples.append(tot / n)
    samples.sort()
    lo = samples[int(0.025 * (n_boot - 1))]
    hi = samples[int(0.975 * (n_boot - 1))]
    return (lo, hi)


def extract_json_object(text: str) -> dict[str, str]:
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return {str(k): str(v).strip().upper()[:1] for k, v in obj.items()}
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return {}
    obj = json.loads(m.group(0))
    if not isinstance(obj, dict):
        return {}
    return {str(k): str(v).strip().upper()[:1] for k, v in obj.items()}


def main() -> None:
    audit_path = AUDIT_PATH
    audit: dict[str, Any]
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    else:
        audit = {"batches": [], "discarded": []}

    pred_by_opaque: dict[str, str] = {}
    for pred_file in sorted(PRED_DIR.glob("batch-*.json")):
        blob = json.loads(pred_file.read_text(encoding="utf-8"))
        if isinstance(blob, dict) and "predictions" in blob:
            blob = blob["predictions"]
        if isinstance(blob, dict):
            for k, v in blob.items():
                pred_by_opaque[str(k)] = str(v).strip().upper()[:1]

    maps: list[dict[str, Any]] = []
    for map_file in sorted(BATCH_DIR.glob("batch-*.map.json")):
        maps.extend(json.loads(map_file.read_text(encoding="utf-8")))

    by_corpus: dict[str, list[int]] = defaultdict(list)
    by_claim: dict[str, list[int]] = defaultdict(list)
    scored = 0
    missing = 0
    rows: list[dict[str, Any]] = []
    for rec in maps:
        opaque = rec["opaqueId"]
        pred = pred_by_opaque.get(opaque)
        if not pred:
            missing += 1
            continue
        correct = int(pred == rec["shuffledKey"])
        scored += 1
        by_corpus[rec.get("corpus") or "unknown"].append(correct)
        by_claim[f"{rec.get('authority')}::{rec.get('claim')}"].append(correct)
        rows.append(
            {
                "itemId": rec["itemId"],
                "opaqueId": opaque,
                "predicted": pred,
                "shuffledKey": rec["shuffledKey"],
                "correct": bool(correct),
                "corpus": rec.get("corpus"),
                "claim": rec.get("claim"),
                "nOptions": rec.get("nOptions", 4),
            }
        )

    def summarize(flags: list[int], chance: float) -> dict[str, Any]:
        n = len(flags)
        rate = sum(flags) / n if n else 0.0
        ci = bootstrap_ci(flags, 1000, 21 + n)
        return {
            "n": n,
            "passRate": rate,
            "ci95": [ci[0], ci[1]],
            "chance": chance,
            "ciExcludesChance": n >= 10 and ci[0] > chance,
            "witnessBarEligible": n >= 10 and ci[0] > chance,
        }

    per_corpus = {c: summarize(f, 0.25) for c, f in sorted(by_corpus.items())}
    per_claim = {c: summarize(f, 0.25) for c, f in sorted(by_claim.items())}
    overall_flags = [r["correct"] for r in rows]
    overall = summarize([int(x) for x in overall_flags], 0.25)

    out = {
        "programId": "choices-only-model",
        "channel": "partial-input",
        "model": "composer-2.5-fast",
        "nMapped": len(maps),
        "nScored": scored,
        "nMissing": missing,
        "overall": overall,
        "perCorpus": per_corpus,
        "perClaim": per_claim,
        "audit": audit,
        "anyWitnessClearsBar": any(v["witnessBarEligible"] for v in per_claim.values()),
        "itemRowsPath": "exports/choices-only/scored.jsonl",
    }
    scored_path = ROOT / "exports" / "choices-only" / "scored.jsonl"
    scored_path.parent.mkdir(parents=True, exist_ok=True)
    scored_path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (ROOT / "exports" / "choices-only" / "summary.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("nMapped", "nScored", "nMissing", "overall", "anyWitnessClearsBar")}, indent=2))
    print("perCorpus", json.dumps(per_corpus, indent=2))


if __name__ == "__main__":
    main()
