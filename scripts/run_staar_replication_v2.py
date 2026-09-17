#!/usr/bin/env python3
"""Score STAAR replication version-2 repaired items. Does not overwrite version-1 files."""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import dump_json  # noqa: E402
from ingest_lib import dump_jsonl, extract_pdf_text  # noqa: E402
from repair_staar_options import repair_items  # noqa: E402
from run_staar_replication import (  # noqa: E402
    BOOT_SEED,
    HAND_CHECK_N,
    MIN_N_WITNESS,
    N_BOOT,
    POWER_MIN_N,
    PRIORITY_GRADES,
    ROOT,
    apply_lower_central,
    apply_stem_repeat,
    apply_unit_rate,
    chance_of,
    discovery_g5_selected,
    n_parseable_numeric_options,
    pdf_window,
    question_from_id,
    score_s3_cell,
    score_simple,
    summarize_rule,
)

OUT_DIR = ROOT / "exports" / "replication-staar"
HAND_CHECK_SEED_V2 = 202609162
V1_HAND_CHECK_SEED = 20260916


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(item: dict[str, Any]) -> str:
    return str(item.get("sourceUrl") or "").removeprefix("file:")


def hand_check_v2(
    items: list[dict[str, Any]],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    selected = [item for item in items if item.get("responseType") == "selected"]
    rng = random.Random(HAND_CHECK_SEED_V2)
    sample = selected[:]
    rng.shuffle(sample)
    sample = sample[:HAND_CHECK_N]
    form_by_id = {form["formId"]: form for form in inventory["replicationCandidates"]}
    rows: list[dict[str, Any]] = []
    for item in sample:
        form_id = str(item.get("replicationFormId"))
        form = form_by_id[form_id]
        question = question_from_id(str(item["id"]))
        window = pdf_window(ROOT / form["testPdf"], question or 0)
        stem = str(item.get("stem") or "")
        stem_tokens = [tok for tok in re.findall(r"[A-Za-z]{4,}", stem)[:8]]
        stem_hits = sum(1 for tok in stem_tokens if tok.lower() in window.lower())
        choices = item.get("choices") or {}
        key = str(item.get("key"))
        key_text = str(choices.get(key, ""))
        key_in_window = bool(key_text) and (key_text[:12].strip() in window or key in window)
        option_letters_present = all(
            re.search(rf"\b{letter}\b", window) or letter.lower() in window.lower()
            for letter in choices
        )
        if stem_hits >= max(2, len(stem_tokens) // 2) and key_in_window:
            auto_judgment = "agree"
        elif stem_hits == 0 and not key_in_window:
            auto_judgment = "disagree"
        else:
            auto_judgment = "uncertain"
        rows.append(
            {
                "id": item["id"],
                "formId": form_id,
                "question": question,
                "stemPreview": stem[:180],
                "choices": choices,
                "key": key,
                "stemTokenHits": stem_hits,
                "nStemTokensChecked": len(stem_tokens),
                "keyTextInWindow": key_in_window,
                "optionLettersPresent": option_letters_present,
                "autoJudgment": auto_judgment,
                "judgment": auto_judgment,
                "windowPreview": re.sub(r"\s+", " ", window)[:280],
                "repair": item.get("repair"),
            }
        )
    existing_path = OUT_DIR / "parse-hand-check-v2.json"
    if existing_path.is_file():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        prior_by_id = {str(row["id"]): row for row in existing.get("items") or []}
        for row in rows:
            prior = prior_by_id.get(str(row["id"]))
            if not prior:
                continue
            for field in ("judgment", "stemJudgment", "optionsJudgment", "keyJudgment", "notes"):
                if field in prior:
                    row[field] = prior[field]
        human_review = existing.get("humanReview")
    else:
        human_review = None
    counts = {
        "nSampled": len(rows),
        "nAgree": sum(1 for row in rows if row["judgment"] == "agree"),
        "nDisagree": sum(1 for row in rows if row["judgment"] == "disagree"),
        "nUncertain": sum(1 for row in rows if row["judgment"] == "uncertain"),
        "nDisagreeStem": sum(1 for row in rows if row.get("stemJudgment") == "disagree"),
        "nDisagreeOptions": sum(1 for row in rows if row.get("optionsJudgment") == "disagree"),
        "nDisagreeKey": sum(1 for row in rows if row.get("keyJudgment") == "disagree"),
    }
    payload = {
        "seed": HAND_CHECK_SEED_V2,
        "version1Seed": V1_HAND_CHECK_SEED,
        "nRequested": HAND_CHECK_N,
        "counts": counts,
        "stopScoring": int(counts["nDisagreeKey"]) >= 3,
        "stopRule": (
            "Stop scoring only if 3 or more items disagree on the key / item-number "
            "alignment. Option leakage is recorded, not a stop."
        ),
        "items": rows,
    }
    if human_review:
        payload["humanReview"] = human_review
    return payload


def prediction_met(summary: dict[str, Any]) -> bool:
    return float(summary["ci95"][0]) > 0.250


def score_repaired(items: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [item for item in items if item.get("responseType") == "selected"]
    grade5 = [item for item in selected if item.get("claim") == "g5"]
    s3_filtered = score_s3_cell(grade5, filtered=True, cell="teks/g5")
    s3_unfiltered = score_s3_cell(grade5, filtered=False, cell="teks/g5")
    secondary: list[dict[str, Any]] = []
    secondary.append(score_simple("unit-rate", "teks/g5", grade5, apply_unit_rate))
    algebra1 = [item for item in selected if item.get("claim") == "alg1"]
    secondary.append(
        score_simple("option-repeating-stem-numbers", "teks/alg1", algebra1, apply_stem_repeat)
    )
    for grade in PRIORITY_GRADES:
        claim = f"g{grade}" if grade != "alg1" else "alg1"
        cell_items = [item for item in selected if item.get("claim") == claim]
        secondary.append(
            score_simple(
                "lower-central-negative-control",
                f"teks/{claim}",
                cell_items,
                apply_lower_central,
            )
        )
    discovery_items = discovery_g5_selected()
    discovery_unfiltered = score_s3_cell(
        discovery_items, filtered=False, cell="teks/g5-discovery"
    )
    pooled_flags = [1 if row["correct"] else 0 for row in discovery_unfiltered["items"]] + [
        1 if row["correct"] else 0 for row in s3_unfiltered["items"]
    ]
    from run_staar_replication import bootstrap_ci

    pooled_ci = bootstrap_ci(pooled_flags) if pooled_flags else (0.0, 0.0)
    pooled = {
        "label": "pooledDiscoveryAndReplication",
        "filter": "unfiltered",
        "nDiscoveryFired": discovery_unfiltered["nFired"],
        "nDiscoveryHits": discovery_unfiltered["nHits"],
        "nReplicationFired": s3_unfiltered["nFired"],
        "nReplicationHits": s3_unfiltered["nHits"],
        "nFired": len(pooled_flags),
        "nHits": sum(pooled_flags),
        "rate": (sum(pooled_flags) / len(pooled_flags)) if pooled_flags else 0.0,
        "chance": 0.25,
        "ci95": [pooled_ci[0], pooled_ci[1]],
        "clearsBar": len(pooled_flags) >= MIN_N_WITNESS and pooled_ci[0] > 0.25,
        "note": "Descriptive. Not the replication verdict.",
    }
    primary = {key: value for key, value in s3_filtered.items() if key != "items"}
    primary["predictionMetLowerCiAbove025"] = prediction_met(s3_filtered)
    primary["powerFloorReached"] = s3_filtered["nFired"] >= POWER_MIN_N
    primary["powerMinimumN"] = POWER_MIN_N
    unfiltered = {key: value for key, value in s3_unfiltered.items() if key != "items"}
    unfiltered["predictionMetLowerCiAbove025"] = prediction_met(s3_unfiltered)
    unfiltered["powerFloorReached"] = s3_unfiltered["nFired"] >= POWER_MIN_N
    unfiltered["powerMinimumN"] = POWER_MIN_N
    return {
        "nSelected": len(selected),
        "nGrade5Selected": len(grade5),
        "nFourNumeric": sum(1 for item in selected if n_parseable_numeric_options(item) == 4),
        "primary": primary,
        "s3UnfilteredGrade5": unfiltered,
        "secondary": secondary,
        "pooledDiscoveryAndReplication": pooled,
        "primaryItemIds": [row["id"] for row in s3_filtered["items"]],
        "s3FilteredItems": s3_filtered["items"],
    }


def main() -> None:
    prereg_path = OUT_DIR / "preregistration.md"
    sha_path = OUT_DIR / "preregistration-v2.sha256"
    sha_text = sha_path.read_text(encoding="utf-8")
    sha_fields = {}
    for line in sha_text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            sha_fields[key] = value
    live_sha = sha256_file(prereg_path)
    if sha_fields.get("sha256") != live_sha:
        raise SystemExit(
            f"preregistration.md sha256 {live_sha} does not match {sha_path}"
        )

    inventory = json.loads((OUT_DIR / "inventory.json").read_text(encoding="utf-8"))
    items_v1 = load_jsonl(OUT_DIR / "items.jsonl")
    sources = sorted({source_path(item) for item in items_v1})
    pdf_text_by_source: dict[str, str] = {}
    for source in sources:
        pdf_text_by_source[source] = extract_pdf_text(ROOT / source)
    repaired = repair_items(items_v1, pdf_text_by_source)
    dump_jsonl(OUT_DIR / "items-repaired.jsonl", repaired)

    hand = hand_check_v2(repaired, inventory)
    dump_json(OUT_DIR / "parse-hand-check-v2.json", hand)

    scored = score_repaired(repaired)
    n_last = sum(1 for item in repaired if (item.get("repair") or {}).get("lastOptionRepaired"))
    n_stacked = sum(
        1 for item in repaired if (item.get("repair") or {}).get("stackedFractionRejoined")
    )
    payload = {
        "writtenAt": utc_now(),
        "version": 2,
        "preregistration": {
            "path": "exports/replication-staar/preregistration.md",
            "sha256File": "exports/replication-staar/preregistration-v2.sha256",
            "sha256": sha_fields.get("sha256"),
            "utc": sha_fields.get("utc"),
            "powerMinimumN": POWER_MIN_N,
            "bootstrap": {
                "method": "random.Random.randrange",
                "nBoot": N_BOOT,
                "seed": BOOT_SEED,
            },
            "handCheckSeed": HAND_CHECK_SEED_V2,
        },
        "repair": {
            "nItems": len(repaired),
            "nLastOptionRepaired": n_last,
            "nStackedFractionRejoined": n_stacked,
            "rule": (
                "Last option reconstructed from the PDF text layer, stopping at the first "
                "footer line or next item; trailing token equal to the item PDF page number "
                "stripped when it is not the sole token. Stacked fractions rejoined to num/den."
            ),
        },
        "parse": {
            "nItems": len(repaired),
            "nSelected": scored["nSelected"],
            "nFourNumeric": scored["nFourNumeric"],
            "handCheck": {
                "seed": hand["seed"],
                "counts": hand["counts"],
                "stopScoring": hand["stopScoring"],
                "stopRule": hand.get("stopRule"),
                "humanReview": hand.get("humanReview"),
            },
        },
        "nGrade5Selected": scored["nGrade5Selected"],
        "primary": scored["primary"],
        "s3UnfilteredGrade5": scored["s3UnfilteredGrade5"],
        "secondary": scored["secondary"],
        "pooledDiscoveryAndReplication": scored["pooledDiscoveryAndReplication"],
        "primaryItemIds": scored["primaryItemIds"],
        "version1PredictionMetLowerCiAbove025": True,
        "version1PowerFloorReached": False,
        "repairedPredictionMetLowerCiAbove025": scored["primary"][
            "predictionMetLowerCiAbove025"
        ],
        "repairedPowerFloorReached": scored["primary"]["powerFloorReached"],
    }
    dump_json(OUT_DIR / "results-v2.json", payload)
    print(
        "v2 filtered",
        scored["primary"]["nHits"],
        "/",
        scored["primary"]["nFired"],
        "ci",
        scored["primary"]["ci95"],
        "predictionMet",
        scored["primary"]["predictionMetLowerCiAbove025"],
        "powerFloor",
        scored["primary"]["powerFloorReached"],
    )


if __name__ == "__main__":
    main()
