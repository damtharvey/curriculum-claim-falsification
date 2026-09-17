#!/usr/bin/env python3
"""A priori rule x cell table, Holm/Bonferroni, and per-cell power from frozen exports."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
ITEMS_PATH = ROOT / "data" / "items.jsonl"

APRIORI_PROGRAMS = (
    "longest-option",
    "stem-option-overlap",
    "option-repeating-stem-numbers",
    "avoid-absolute-terms",
    "middle-value-option",
    "position-c",
    "invert-and-multiply",
    "coefficient-adjacent-to-x",
    "percent-of",
    "percent-change",
    "unit-rate",
    "y-equals-kx",
    "area-lw",
    "volume-lwh",
    "mean-of-listed-numbers",
)

MIN_N = 10
ALPHA = 0.05
CLAIMED = {
    ("middle-value-option", "nyregents", "geometry"),
    ("middle-value-option", "eqao", "g6"),
}


def binomial_sf(k: int, n: int, p: float) -> float:
    """One-sided P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    log_term = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log(1.0 - p)
    )
    term = math.exp(min(log_term, 700.0))
    total = 0.0
    for i in range(k, n + 1):
        total += term
        if total >= 1.0:
            return 1.0
        if i == n:
            break
        term *= (n - i) / (i + 1) * p / (1.0 - p)
    return min(1.0, total)


def holm_reject(p_values: list[float], alpha: float = ALPHA) -> list[bool]:
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    rejected = [False] * m
    for rank, index in enumerate(order):
        threshold = alpha / (m - rank)
        if p_values[index] <= threshold:
            rejected[index] = True
        else:
            break
    return rejected


def round3(value: float) -> float:
    return round(value + 0.0, 3)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def corpus_counts() -> dict[str, Any]:
    n_total = 0
    n_selected = 0
    n_numeric = 0
    by_corpus: Counter[str] = Counter()
    by_cell: Counter[str] = Counter()
    by_response: Counter[str] = Counter()
    for line in ITEMS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        n_total += 1
        corpus = str(item["corpus"])
        by_corpus[corpus] += 1
        by_cell[f"{item['authority']}|{item['claim']}"] += 1
        response = str(item.get("responseType", ""))
        by_response[response] += 1
        if response == "selected":
            n_selected += 1
        elif response == "numeric":
            n_numeric += 1
    return {
        "nItems": n_total,
        "nSelected": n_selected,
        "nNumeric": n_numeric,
        "byCorpus": dict(by_corpus),
        "byCell": dict(by_cell),
        "byResponse": dict(by_response),
    }


def main() -> None:
    rule_rows: list[dict[str, Any]] = load_json(EXPORTS / "rule-chance.json")
    comparisons: dict[str, Any] = load_json(EXPORTS / "comparisons.json")
    method_controls: dict[str, Any] = load_json(EXPORTS / "method-controls.json")
    item_counts = corpus_counts()

    family: list[dict[str, Any]] = []
    for row in rule_rows:
        program_id = str(row["programId"])
        if program_id not in APRIORI_PROGRAMS:
            continue
        n_scored = int(row["nScored"])
        if n_scored < MIN_N:
            continue
        chance = float(row["chanceRate"])
        if chance <= 0.0:
            # Numeric constructed items with undefined format chance. A binomial
            # test against p=0 is degenerate (any hit has p=0) and is not in
            # the family of "rate exceeds chance" tests the witness bar uses.
            continue
        n_correct = int(row["nCorrect"])
        p_value = binomial_sf(n_correct, n_scored, chance)
        ci = row["ci95"]
        family.append(
            {
                "programId": program_id,
                "authority": row["authority"],
                "claim": row["claim"],
                "nScored": n_scored,
                "nCorrect": n_correct,
                "passRate": float(row["passRate"]),
                "passRate3": round3(float(row["passRate"])),
                "chanceRate": chance,
                "chanceRate3": round3(chance),
                "ci95": [float(ci[0]), float(ci[1])],
                "ci95_3": [round3(float(ci[0])), round3(float(ci[1]))],
                "beatsChance": bool(row["beatsChance"]),
                "clearsPerCellBar": bool(row["witnessEligible"]),
                "binomialPGreater": p_value,
                "claimedWitness": (program_id, row["authority"], row["claim"]) in CLAIMED,
                "note": row.get("note", ""),
            }
        )

    family.sort(key=lambda r: (r["authority"], r["claim"], r["programId"]))
    p_values = [r["binomialPGreater"] for r in family]
    holm = holm_reject(p_values)
    m = len(family)
    bonferroni_cut = ALPHA / m if m else ALPHA
    for row, holm_hit in zip(family, holm, strict=True):
        row["holmReject05"] = holm_hit
        row["bonferroniReject05"] = row["binomialPGreater"] <= bonferroni_cut
        row["bonferroniThreshold"] = bonferroni_cut

    eligible = [r for r in family if r["clearsPerCellBar"]]
    holm_hits = [r for r in family if r["holmReject05"]]
    bonf_hits = [r for r in family if r["bonferroniReject05"]]
    claimed_rows = [r for r in family if r["claimedWitness"]]
    middle_value = [r for r in family if r["programId"] == "middle-value-option"]
    mv_p = [r["binomialPGreater"] for r in middle_value]
    mv_holm = holm_reject(mv_p)
    mv_m = len(middle_value)
    mv_bonf = ALPHA / mv_m if mv_m else ALPHA
    for row, holm_hit in zip(middle_value, mv_holm, strict=True):
        row["middleValueFamilyHolmReject05"] = holm_hit
        row["middleValueFamilyBonferroniReject05"] = row["binomialPGreater"] <= mv_bonf

    power_rows: list[dict[str, Any]] = []
    for row in comparisons["rows"]:
        n_items = int(row["nItems"])
        min_rate = row.get("minObservablePassRate")
        power_rows.append(
            {
                "authority": row["authority"],
                "claim": row["claim"],
                "nItems": n_items,
                "nAttempted": row["nAttempted"],
                "chanceRate": row["chanceRate"],
                "minObservablePassRate": min_rate,
                "minObservablePassRate3": None if min_rate is None else round3(float(min_rate)),
                "minDetectableTrueRate80": row.get("minDetectableTrueRate80"),
                "nWitnesses": row.get("nWitnesses"),
                "nullNote": row.get("nullNote"),
                "eligibleForWitness": n_items >= MIN_N,
            }
        )
    power_eligible = [r for r in power_rows if r["eligibleForWitness"] and r["minObservablePassRate"] is not None]
    min_floor = min(float(r["minObservablePassRate"]) for r in power_eligible) if power_eligible else None

    searched_eligible = [
        {
            "programId": r["programId"],
            "authority": r["authority"],
            "claim": r["claim"],
            "nScored": r["nScored"],
            "passRate": r["passRate"],
            "ci95": r["ci95"],
            "chanceRate": r["chanceRate"],
            "note": r.get("note", ""),
        }
        for r in rule_rows
        if r.get("witnessEligible")
        and str(r["programId"]) not in APRIORI_PROGRAMS
    ]

    planted = method_controls["planted"]
    real_sets = {entry["name"]: entry for entry in method_controls["realPublicCueSets"] if "bestHeldOut" in entry}

    artifact = {
        "generatedFrom": {
            "ruleChance": "exports/rule-chance.json",
            "comparisons": "exports/comparisons.json",
            "methodControls": "exports/method-controls.json",
            "items": "data/items.jsonl",
            "comparisonsGeneratedAt": comparisons["generatedAt"],
            "nItemsComparisons": comparisons["nItems"],
            "nTrials": comparisons["nTrials"],
            "nWitnessesClaimedItemLevelDoNotCite": comparisons["nWitnessesClaimed"],
        },
        "familyDefinition": (
            "Every a priori catalog rule on every authority x claim cell with nScored >= 10 "
            "and chanceRate > 0. One PISA unit-rate numeric row with chanceRate 0 was excluded "
            "as a degenerate test. Pre-registered witness bar is lower 95% bootstrap CI above "
            "recorded chanceRate and n >= 10. Family-wise tests are one-sided binomial p-values "
            "H1: rate > chanceRate, Holm and Bonferroni at alpha=0.05."
        ),
        "nFamilyTests": m,
        "alpha": ALPHA,
        "bonferroniThreshold": bonferroni_cut,
        "nClearsPerCellBar": len(eligible),
        "nHolmReject": len(holm_hits),
        "nBonferroniReject": len(bonf_hits),
        "claimedWitnessesSurviveHolm": all(r["holmReject05"] for r in claimed_rows) and len(claimed_rows) == 2,
        "claimedWitnessesSurviveBonferroni": all(r["bonferroniReject05"] for r in claimed_rows) and len(claimed_rows) == 2,
        "claimedWitnesses": claimed_rows,
        "middleValueFamilyN": mv_m,
        "middleValueBonferroniThreshold": mv_bonf,
        "claimedSurviveMiddleValueHolm": all(r.get("middleValueFamilyHolmReject05") for r in claimed_rows),
        "middleValueFamily": middle_value,
        "clearsPerCellBar": eligible,
        "holmRejects": holm_hits,
        "bonferroniRejects": bonf_hits,
        "family": family,
        "searchedEligibleNotClaimed": searched_eligible,
        "itemCounts": item_counts,
        "methodControlsPointers": {
            "nItemsSynthetic": method_controls["nItems"],
            "plantedTypeHits": method_controls["plantedTypeHits"],
            "plantedTypeN": method_controls["plantedTypeN"],
            "falsePositiveOnClean": method_controls["falsePositiveOnClean"],
            "programSpaceSize": method_controls["programSpace"]["programSpaceSize"],
            "openbookqa": real_sets.get("openbookqa", {}).get("bestHeldOut"),
            "swag": real_sets.get("swag", {}).get("bestHeldOut"),
            "race": real_sets.get("race", {}).get("bestHeldOut"),
            "commonsenseqa": real_sets.get("commonsenseqa", {}).get("bestHeldOut"),
            "plantedHoldoutN": planted[0]["nScored"] if planted else None,
        },
    }
    (EXPORTS / "apriori-cell-table.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )

    power_artifact = {
        "source": "exports/comparisons.json rows[].minObservablePassRate",
        "definition": (
            "Minimum detectable bypass rate: smallest observed pass rate whose bootstrap CI "
            "excludes format chance, computed in runner/src/power.ts minObservablePassRate."
        ),
        "nCells": len(power_rows),
        "nCellsNAtLeast10WithRate": len(power_eligible),
        "minFloorAmongEligible": min_floor,
        "minFloor3": None if min_floor is None else round3(min_floor),
        "rows": sorted(power_rows, key=lambda r: (r["authority"], r["claim"])),
        "headline": [
            r
            for r in power_rows
            if (r["authority"], r["claim"])
            in {
                ("timss", "knowing"),
                ("timss", "applying"),
                ("timss", "reasoning"),
                ("nyregents", "algebra-i"),
                ("nyregents", "algebra-ii"),
                ("nyregents", "geometry"),
                ("eqao", "g6"),
                ("teks", "g7"),
                ("acara", "y7-numeracy"),
            }
        ],
    }
    (EXPORTS / "cell-power.json").write_text(json.dumps(power_artifact, indent=2) + "\n", encoding="utf-8")

    print(f"family tests n>={MIN_N}: {m}")
    print(f"clears per-cell bar: {len(eligible)}")
    print(f"Holm rejects: {len(holm_hits)}")
    print(f"Bonferroni rejects (cut={bonferroni_cut:.6g}): {len(bonf_hits)}")
    print("claimed:")
    for row in claimed_rows:
        print(
            f"  {row['authority']} {row['claim']} {row['programId']} "
            f"n={row['nScored']} rate={row['passRate3']} CI={row['ci95_3']} "
            f"p={row['binomialPGreater']:.6g} holm={row['holmReject05']} "
            f"bonf={row['bonferroniReject05']}"
        )
    print("all per-cell bar clears:")
    for row in eligible:
        print(
            f"  {row['authority']} {row['claim']} {row['programId']} "
            f"n={row['nScored']} {row['passRate3']} p={row['binomialPGreater']:.6g} "
            f"holm={row['holmReject05']} bonf={row['bonferroniReject05']}"
        )
    print("holm hits:")
    for row in holm_hits:
        print(f"  {row['authority']} {row['claim']} {row['programId']} p={row['binomialPGreater']:.6g}")
    print("power headline:")
    for row in power_artifact["headline"]:
        print(
            f"  {row['authority']} {row['claim']} n={row['nItems']} "
            f"minDet={row['minObservablePassRate3']}"
        )
    print(f"min floor among n>=10 cells: {power_artifact['minFloor3']}")
    print("item counts", item_counts["nItems"], item_counts["nSelected"], item_counts["nNumeric"])
    print("by corpus", item_counts["byCorpus"])


if __name__ == "__main__":
    main()
