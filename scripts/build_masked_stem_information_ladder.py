#!/usr/bin/env python3
"""Information ladder: chance, modal letter, options-only, masked-stem, with-stem."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from masked_stem_followup_lib import (  # noqa: E402
    dump_json,
    load_jsonl,
    modal_letter,
    summarize_rows,
)

OUT_DIR = ROOT / "exports" / "addendum-gpu"
STATS_PATH = OUT_DIR / "masked-stem-item-mask-stats.jsonl"
LADDER_PATH = OUT_DIR / "information-ladder.json"
CELLS = ("nyregents::algebra-i", "nyregents::algebra-ii")
MODEL_FILES = {
    "qwen2.5-7b-instruct": {
        "modelId": "Qwen/Qwen2.5-7B-Instruct",
        "modelRevision": "a09a35458c702b33eeacc393d103063234e8bc28",
        "optionsOnly": OUT_DIR / "choices-only-local-lm-items.jsonl",
        "maskedStem": OUT_DIR / "masked-stem-7b-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-7b-items.jsonl",
        "withStemSummary": OUT_DIR / "with-stem-algebra-7b.json",
    },
    "qwen2.5-14b-instruct": {
        "modelId": "Qwen/Qwen2.5-14B-Instruct",
        "modelRevision": "cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8",
        "optionsOnly": OUT_DIR / "choices-only-local-lm-14b-items.jsonl",
        "maskedStem": OUT_DIR / "masked-stem-14b-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-14b-items.jsonl",
        "withStemSummary": OUT_DIR / "with-stem-algebra-14b.json",
    },
}


def load_primary_by_cell() -> dict[str, list[str]]:
    by_cell: dict[str, list[str]] = {cell: [] for cell in CELLS}
    with STATS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if int(row["masked_token_count"]) < 1:
                continue
            cell = str(row.get("cell"))
            if cell in by_cell:
                by_cell[cell].append(str(row["id"]))
    return by_cell


def rows_for_ids(path: Path, allowed: set[str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [row for row in load_jsonl(path) if str(row["id"]) in allowed]


def constant_letter_rows(rows: list[dict[str, Any]], letter: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        copied = dict(row)
        copied["correct"] = str(row["key"]).strip().upper() == letter
        out.append(copied)
    return out


def rung(name: str, rows: list[dict[str, Any]], *, available: bool, note: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "available": available,
        "n": len(rows) if available else 0,
        "note": note,
    }
    if not available or not rows:
        payload["passRate"] = None
        payload["ci95"] = None
        payload["chance"] = None
        return payload
    stats = summarize_rows(rows)
    payload.update(stats)
    return payload


def cell_ladder(
    cell: str,
    item_ids: list[str],
    model_key: str,
    files: dict[str, Any],
) -> dict[str, Any]:
    allowed = set(item_ids)
    options_rows = rows_for_ids(files["optionsOnly"], allowed)
    masked_rows = rows_for_ids(files["maskedStem"], allowed)
    with_stem_rows = rows_for_ids(files["withStem"], allowed)
    if not masked_rows:
        raise RuntimeError(f"missing masked-stem rows for {model_key} {cell}")
    if len(masked_rows) != len(item_ids):
        raise RuntimeError(
            f"{model_key} {cell} masked-stem n={len(masked_rows)} expected {len(item_ids)}"
        )
    keys = [str(row["key"]) for row in masked_rows]
    letter, count, frequency = modal_letter(keys)
    chance = sum(1.0 / int(row["n_options"]) for row in masked_rows) / len(masked_rows)
    with_stem_available = len(with_stem_rows) == len(item_ids)
    rungs = [
        {
            "name": "chance",
            "available": True,
            "n": len(masked_rows),
            "passRate": chance,
            "ci95": None,
            "chance": chance,
            "meanOneOverK": chance,
            "note": "Mean of 1/k on these items. Not a sample proportion; no bootstrap CI.",
        },
        rung(
            "modal_letter",
            constant_letter_rows(masked_rows, letter),
            available=True,
            note=f"Always pick population modal key letter {letter} ({count}/{len(keys)}).",
        ),
        rung(
            "options_only",
            options_rows,
            available=len(options_rows) == len(item_ids),
            note="Option list only; letter log-probability argmax.",
        ),
        rung(
            "masked_stem_plus_options",
            masked_rows,
            available=True,
            note="Quantities in the stem replaced by [N]; options shown; letter argmax.",
        ),
        rung(
            "with_stem",
            with_stem_rows,
            available=with_stem_available,
            note="Full original stem plus options; letter argmax; no chain of thought.",
        ),
    ]
    return {
        "cell": cell,
        "n": len(item_ids),
        "modalLetter": letter,
        "modalCount": count,
        "modalFrequency": frequency,
        "rungs": rungs,
        "withStemComplete": with_stem_available,
        "optionsOnlyComplete": len(options_rows) == len(item_ids),
    }


def main() -> None:
    by_cell = load_primary_by_cell()
    expected = {"nyregents::algebra-i": 358, "nyregents::algebra-ii": 248}
    for cell, n_expected in expected.items():
        n_got = len(by_cell[cell])
        if n_got != n_expected:
            raise RuntimeError(f"{cell} primary n={n_got} expected {n_expected}")
    models: dict[str, Any] = {}
    any_missing_with_stem = False
    for model_key, files in MODEL_FILES.items():
        cells: dict[str, Any] = {}
        for cell in CELLS:
            block = cell_ladder(cell, by_cell[cell], model_key, files)
            cells[cell] = block
            if not block["withStemComplete"]:
                any_missing_with_stem = True
        models[model_key] = {
            "modelId": files["modelId"],
            "modelRevision": files["modelRevision"],
            "cells": cells,
        }
    payload = {
        "status": "partial" if any_missing_with_stem else "complete",
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "population": "masked_token_count_ge_1",
        "promptModes": {
            "chance": "mean 1/k",
            "modal_letter": "constant letter = cell modal key on this population",
            "options_only": "choices-only",
            "masked_stem_plus_options": "masked-stem",
            "with_stem": "full stem, letter argmax, no chain of thought",
        },
        "scoring": (
            "Next-token log-softmax over option letters after the chat template; "
            "greedy argmax of bare letter vs space-prefixed letter."
        ),
        "models": models,
        "missing": (
            "with-stem rows still scoring"
            if any_missing_with_stem
            else None
        ),
    }
    dump_json(LADDER_PATH, payload)
    print(json.dumps({"status": payload["status"], "path": str(LADDER_PATH)}, indent=2))


if __name__ == "__main__":
    main()
