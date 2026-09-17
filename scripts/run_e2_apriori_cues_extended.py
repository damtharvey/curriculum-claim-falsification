#!/usr/bin/env python3
"""E2: literature-derived a priori cues not in programs/apriori.ts."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from addendum_lib import (
    ADDENDUM_DIR,
    EXTENDED_CITATIONS,
    EXTENDED_PROGRAMS,
    MIN_N_WITNESS,
    binomial_sf,
    chance_rate,
    dump_json,
    holm_reject,
    load_items,
    score_program,
    summarize_scored,
)

EXISTING_FAMILY_TESTS = 105


def main() -> None:
    items = load_items()
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if item.get("responseType") != "selected":
            continue
        by_cell[(str(item["authority"]), str(item["claim"]))].append(item)

    rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    for program_id, program in EXTENDED_PROGRAMS.items():
        for (authority, claim), subset in sorted(by_cell.items()):
            scored = score_program(subset, program)
            summary = summarize_scored(scored)
            n = summary["n"]
            chance = summary["chanceRate"]
            n_correct = summary["nCorrect"]
            p_value = binomial_sf(n_correct, n, chance) if n and chance > 0 else 1.0
            clears = n >= MIN_N_WITNESS and chance > 0 and summary["itemBootstrapCi95"][0] > chance
            row = {
                "programId": program_id,
                "authority": authority,
                "claim": claim,
                "nScored": n,
                "nCorrect": n_correct,
                "passRate": summary["passRate"],
                "chanceRate": chance,
                "ci95": summary["itemBootstrapCi95"],
                "clusterBootstrapCi95": summary["clusterBootstrapCi95"],
                "nAdministrations": summary["nAdministrations"],
                "binomialPGreater": p_value,
                "clearsBar": clears,
                "inFamily": n >= MIN_N_WITNESS and chance > 0,
                "citation": EXTENDED_CITATIONS[program_id],
            }
            rows.append(row)
            if row["inFamily"]:
                family_rows.append(row)

    p_values = [row["binomialPGreater"] for row in family_rows]
    holm = holm_reject(p_values) if p_values else []
    alpha = 0.05
    n_family_new = len(family_rows)
    n_family_total = EXISTING_FAMILY_TESTS + n_family_new
    bonferroni_new = alpha / n_family_new if n_family_new else None
    bonferroni_total = alpha / n_family_total if n_family_total else None
    n_holm = 0
    n_bonf = 0
    for row, rejected in zip(family_rows, holm):
        row["holmReject05NewFamily"] = rejected
        row["bonferroniReject05NewFamily"] = (
            bonferroni_new is not None and row["binomialPGreater"] <= bonferroni_new
        )
        row["bonferroniReject05CombinedFamily"] = (
            bonferroni_total is not None and row["binomialPGreater"] <= bonferroni_total
        )
        if rejected:
            n_holm += 1
        if row["bonferroniReject05NewFamily"]:
            n_bonf += 1

    clears = [row for row in family_rows if row["clearsBar"]]
    payload = {
        "experiment": "E2",
        "question": (
            "Do classic mechanical test-wiseness cues that were missing from the "
            "a priori catalog clear the witness bar on frozen items?"
        ),
        "existingCatalogAlreadyPresent": [
            "longest-option",
            "stem-option-overlap",
            "avoid-absolute-terms",
            "middle-value-option",
            "position-c",
        ],
        "newPrograms": list(EXTENDED_PROGRAMS.keys()),
        "citations": EXTENDED_CITATIONS,
        "existingFamilyTests": EXISTING_FAMILY_TESTS,
        "nNewFamilyTests": n_family_new,
        "nFamilyTestsCombined": n_family_total,
        "nClearsPerCellBar": len(clears),
        "nHolmRejectNewFamily": n_holm,
        "nBonferroniRejectNewFamily": n_bonf,
        "bonferroniThresholdNewFamily": bonferroni_new,
        "bonferroniThresholdCombinedFamily": bonferroni_total,
        "clears": clears,
        "familyRows": family_rows,
        "allRows": rows,
        "cite": "exports/addendum/apriori-cues-extended.json",
        "holmNote": (
            "Paper Holm/Bonferroni should be recomputed on nFamilyTestsCombined, "
            "not on the new-family-only counts."
        ),
    }
    dump_json(ADDENDUM_DIR / "apriori-cues-extended.json", payload)
    print("wrote", ADDENDUM_DIR / "apriori-cues-extended.json")
    print("new family tests", n_family_new, "combined", n_family_total)
    print("clears", len(clears))
    for row in clears:
        print(
            row["programId"],
            row["authority"],
            row["claim"],
            "n",
            row["nScored"],
            "rate",
            round(row["passRate"], 3),
            "ci",
            [round(x, 3) for x in row["ci95"]],
            "p",
            row["binomialPGreater"],
        )


if __name__ == "__main__":
    main()
