#!/usr/bin/env python3
"""E1: cluster bootstrap, per-administration breakdown, and rule-definition sensitivity."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from addendum_lib import (
    ADDENDUM_DIR,
    NUMERIC_RULES,
    administration_sort_key,
    binomial_sf,
    dump_json,
    load_items,
    middle_value_option,
    parsed_numeric_options,
    score_program,
    summarize_scored,
)

CELLS = [
    ("nyregents", "geometry", True),
    ("eqao", "g6", True),
    ("nyregents", "algebra-ii", False),
]


def per_administration(scored: list[Any], chance: float) -> dict[str, Any]:
    by_admin: dict[str, list[int]] = defaultdict(list)
    for row in scored:
        by_admin[row.administration].append(1 if row.correct else 0)
    rows: list[dict[str, Any]] = []
    n_exceed = 0
    n_sign_plus = 0
    n_sign_minus = 0
    n_sign_zero = 0
    for admin_id in sorted(by_admin, key=administration_sort_key):
        flags = by_admin[admin_id]
        n = len(flags)
        rate = sum(flags) / n if n else 0.0
        exceeds = rate > chance
        if exceeds:
            n_exceed += 1
            n_sign_plus += 1
        elif rate < chance:
            n_sign_minus += 1
        else:
            n_sign_zero += 1
        rows.append(
            {
                "administration": admin_id,
                "n": n,
                "nCorrect": sum(flags),
                "passRate": rate,
                "exceedsChance": exceeds,
            }
        )
    n_signed = n_sign_plus + n_sign_minus
    sign_p = binomial_sf(n_sign_plus, n_signed, 0.5) if n_signed else 1.0
    return {
        "nAdministrations": len(rows),
        "nAdministrationsExceedingChance": n_exceed,
        "signTest": {
            "nPlus": n_sign_plus,
            "nMinus": n_sign_minus,
            "nZero": n_sign_zero,
            "nSigned": n_signed,
            "null": "P(administration rate > chance) = 0.5, zeros dropped",
            "oneSidedPGreater": sign_p,
        },
        "administrations": rows,
    }


def cell_items(items: list[dict[str, Any]], authority: str, claim: str) -> list[dict[str, Any]]:
    return [item for item in items if item.get("authority") == authority and item.get("claim") == claim]


def main() -> None:
    items = load_items()
    payload: dict[str, Any] = {
        "experiment": "E1",
        "question": (
            "Are the two claimed middle-value witnesses stable under cluster resampling "
            "by exam administration, across administrations, and under alternative "
            "numeric-option central-tendency definitions? Algebra II is reported only."
        ),
        "method": {
            "rule": "lower-central index floor((k-1)/2) on parsed leading numbers, k>=3",
            "itemBootstrap": "mulberry32 seed 11, 1000 replicates, matching runner/src/stats.ts",
            "clusterBootstrap": (
                "resample administrations with replacement, 2000 replicates, mulberry32 "
                "seed 20260916; rate is pooled over items in sampled administrations"
            ),
            "administration": (
                "NY Regents: year-session from item id; EQAO: released-question year"
            ),
            "signTest": "one-sided binomial on administrations with rate != chance",
            "sensitivity": (
                "five definitions on the same k>=3 numeric-option items: lower-central "
                "(pre-registered), upper-central, nearest-to-arithmetic-mean, smallest, largest"
            ),
        },
        "cells": [],
    }
    for authority, claim, claimed in CELLS:
        subset = cell_items(items, authority, claim)
        scored = score_program(subset, middle_value_option)
        summary = summarize_scored(scored)
        chance = summary["chanceRate"]
        admin = per_administration(scored, chance if chance else 0.25)
        variants: dict[str, Any] = {}
        for name, fn in NUMERIC_RULES.items():
            variant_scored = score_program(
                subset,
                lambda item, rule_fn=fn: rule_fn(parsed_numeric_options(item)),
            )
            variants[name] = {
                **summarize_scored(variant_scored),
                "preRegistered": name == "lower-central",
            }
        payload["cells"].append(
            {
                "authority": authority,
                "claim": claim,
                "claimedWitness": claimed,
                "nItemsInCell": len(subset),
                "nSelected": sum(1 for item in subset if item.get("responseType") == "selected"),
                "middleValueLowerCentral": summary,
                "perAdministration": admin,
                "ruleDefinitionSensitivity": variants,
                "cite": (
                    f"exports/addendum/e1-witness-dependence.json cells["
                    f"authority={authority} claim={claim}]"
                ),
            }
        )
    dump_json(ADDENDUM_DIR / "e1-witness-dependence.json", payload)
    print("wrote", ADDENDUM_DIR / "e1-witness-dependence.json")
    for cell in payload["cells"]:
        mid = cell["middleValueLowerCentral"]
        print(
            cell["authority"],
            cell["claim"],
            "n",
            mid["n"],
            "rate",
            round(mid["passRate"], 3),
            "itemCI",
            [round(x, 3) for x in mid["itemBootstrapCi95"]],
            "clusterCI",
            [round(x, 3) for x in mid["clusterBootstrapCi95"]],
            "clusterClears",
            mid["clearsClusterBar"],
            "admins",
            cell["perAdministration"]["nAdministrations"],
            "admins>chance",
            cell["perAdministration"]["nAdministrationsExceedingChance"],
            "signP",
            cell["perAdministration"]["signTest"]["oneSidedPGreater"],
        )


if __name__ == "__main__":
    main()
