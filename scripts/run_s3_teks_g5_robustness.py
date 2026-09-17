#!/usr/bin/env python3
"""S3 arithmetic-closure robustness on TEKS grade 5. Does not overwrite version-1 numbers."""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from addendum_lib import (  # noqa: E402
    ROOT,
    administration_id,
    answers_match,
    binomial_sf,
    bootstrap_ci_mulberry,
    cluster_bootstrap_ci,
    dump_json,
    holm_reject,
    load_items,
)
from addendum_lib import Mulberry32  # noqa: E402
from strategy_channels import (  # noqa: E402
    apply_s3,
    format_chance_k,
    lower_central_key,
    parsed_numeric_options,
)

OUT_DIR = ROOT / "exports" / "addendum-strategies"
ALPHA = 0.05
CHANCE = 0.25
N_RANDOM_TIES = 1000
RANDOM_TIE_SEED = 11
CLUSTER_BOOT_N = 2000
CLUSTER_BOOT_SEED = 20260916

STEM_JUDGMENTS: dict[str, dict[str, str]] = {
    "staar-2019-5-q2": {
        "kind": "coincidence",
        "line": "Multi-step (8*16.95-7.50); all four dollar amounts sit at depth 2.",
    },
    "staar-2019-5-q3": {
        "kind": "parse_artifact",
        "line": "Axis ticks 0-9 swept into the stem; every option coordinate is already a seed.",
    },
    "staar-2019-5-q7": {
        "kind": "one_operation",
        "line": "428.5/5 = 85.7, unique at depth 1.",
    },
    "staar-2019-5-q10": {
        "kind": "coincidence",
        "line": "PEMDAS wording; leading numbers in the options repeat the expression numerals.",
    },
    "staar-2019-5-q11": {
        "kind": "coincidence",
        "line": "Equation-identification; all four choices lead with the seed 27.",
    },
    "staar-2019-5-q13": {
        "kind": "one_operation",
        "line": "3.75*28 = 105, unique at depth 1.",
    },
    "staar-2019-5-q19": {
        "kind": "coincidence",
        "line": "Remainder 2-0.475-0.35 is two operations; unique depth-1 hit is the sum, not the key.",
    },
    "staar-2019-5-q20": {
        "kind": "coincidence",
        "line": "Plot thresholds 36 and 25; key 6 is not 36-25.",
    },
    "staar-2019-5-q21": {
        "kind": "coincidence",
        "line": "Two-product shopping total 2*36.95+5*23.95 at depth 2.",
    },
    "staar-2019-5-q29": {
        "kind": "coincidence",
        "line": "Given multi-op grocery expression; all four prices at depth 2.",
    },
    "staar-2019-5-q32": {
        "kind": "one_operation",
        "line": "151.2/24 = 6.3, unique at depth 1.",
    },
    "staar-2019-5-q35": {
        "kind": "parse_artifact",
        "line": "Bar-chart axis labels 45,55,65,75,85; bar counts are not in the stem.",
    },
    "staar-2019-5-q36": {
        "kind": "parse_artifact",
        "line": "Previous-item options and layout 1 2 leaked; 1+2 puts key 3 at depth 1.",
    },
    "staar-2021-5-q1": {
        "kind": "one_operation",
        "line": "6.75*14 = 94.50, tied at depth 1 with 6.75+14.",
    },
    "staar-2021-5-q3": {
        "kind": "coincidence",
        "line": "Equation-identification; A and B both lead with the seed 90.",
    },
    "staar-2021-5-q5": {
        "kind": "parse_artifact",
        "line": "1,012 split by a thousands comma into seeds 1 and 12.",
    },
    "staar-2021-5-q9": {
        "kind": "coincidence",
        "line": "Comparison options contain the table times, all at depth 0.",
    },
    "staar-2021-5-q10": {
        "kind": "parse_artifact",
        "line": "Broken fraction OCR dumps 1,2,3 into the stem; option D is empty.",
    },
    "staar-2021-5-q16": {
        "kind": "one_operation",
        "line": "8.05/35 = 0.23, unique at depth 1.",
    },
    "staar-2021-5-q18": {
        "kind": "one_operation",
        "line": "48*144 = 6912, unique at depth 1.",
    },
    "staar-2021-5-q21": {
        "kind": "coincidence",
        "line": "(625-7*55)/8 is two operations; key 30 at depth 2.",
    },
    "staar-2021-5-q23": {
        "kind": "coincidence",
        "line": "Prime-list item; 43 is not a one-op of the listed primes.",
    },
    "staar-2021-5-q24": {
        "kind": "one_operation",
        "line": "6.48/9 = 0.72, unique at depth 1.",
    },
    "staar-2021-5-q25": {
        "kind": "parse_artifact",
        "line": "Coordinate-grid axis 0-9 swept into seeds; options are grid points.",
    },
    "staar-2021-5-q31": {
        "kind": "parse_artifact",
        "line": "$2,135 split by a thousands comma into 2 and 135.",
    },
    "staar-2021-5-q33": {
        "kind": "coincidence",
        "line": "Target value 25 in the stem; unique depth-1 option C leads with 50=2*25.",
    },
    "staar-2021-5-q34": {
        "kind": "parse_artifact",
        "line": "Missing fraction; D=3 is the only remaining stem number.",
    },
    "staar-2021-5-q35": {
        "kind": "parse_artifact",
        "line": "Scatterplot axis ticks 0-90 become seeds; C=90 and D=80 are labels.",
    },
    "staar-2021-5-q36": {
        "kind": "one_operation",
        "line": "10-6.275 = 3.725 from the story numbers.",
    },
    "staar-2022-5-q1": {
        "kind": "parse_artifact",
        "line": "Stem-and-leaf digits 6 0 3 2 and 30 dumped as seeds; options are fractions.",
    },
    "staar-2022-5-q3": {
        "kind": "parse_artifact",
        "line": "OCR 3 5 plus footer GRADE 5; every option leads with 5.",
    },
    "staar-2022-5-q10": {
        "kind": "one_operation",
        "line": "6*0.93 = 5.58 at depth 1.",
    },
    "staar-2022-5-q15": {
        "kind": "parse_artifact",
        "line": "Age-bin labels 10-14,... as seeds; visitor counts are missing from the stem.",
    },
    "staar-2022-5-q16": {
        "kind": "coincidence",
        "line": "6*3+21*2+16 is three operations; unique depth-1 hit is the partial 48.",
    },
    "staar-2022-5-q17": {
        "kind": "coincidence",
        "line": "Option text contains the table +5; A and D parse as 5 at depth 0.",
    },
    "staar-2022-5-q18": {
        "kind": "coincidence",
        "line": "Figure not OCR'd; 10 and 1 do not one-op to the key 300.",
    },
    "staar-2022-5-q21": {
        "kind": "parse_artifact",
        "line": "$4,554 split by a thousands comma into 4 and 554.",
    },
    "staar-2022-5-q23": {
        "kind": "coincidence",
        "line": "3(25+19)+4*3 is a multi-op expression value at depth 2.",
    },
    "staar-2022-5-q26": {
        "kind": "coincidence",
        "line": "Budget options parse as $10/$20 from the wording, not a one-op of the story.",
    },
    "staar-2022-5-q35": {
        "kind": "coincidence",
        "line": "PEMDAS options contain the expression numbers 40,5,3,8,1.",
    },
}


def summarize_flags(flags: list[int], chance: float = CHANCE) -> dict[str, Any]:
    n = len(flags)
    n_correct = int(sum(flags))
    rate = n_correct / n if n else 0.0
    ci = bootstrap_ci_mulberry(flags, 1000, 11) if n else (0.0, 0.0)
    p_value = binomial_sf(n_correct, n, chance) if n and 0.0 < chance < 1.0 else 1.0
    return {
        "nFired": n,
        "nCorrect": n_correct,
        "rate": rate,
        "chance": chance,
        "ci95": [ci[0], ci[1]],
        "binomialPGreater": p_value,
        "clearsBar": n >= 10 and chance > 0 and ci[0] > chance,
    }


def holm_step_for(
    p_values: list[float],
    target_p: float,
) -> dict[str, Any]:
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    rejected = holm_reject(p_values, ALPHA)
    target_indices = [i for i, value in enumerate(p_values) if abs(value - target_p) < 1e-18 or value == target_p]
    if not target_indices:
        closest = min(range(len(p_values)), key=lambda i: abs(p_values[i] - target_p))
        target_indices = [closest]
    index = target_indices[0]
    rank = order.index(index)
    threshold = ALPHA / (len(p_values) - rank)
    return {
        "familySize": len(p_values),
        "targetP": p_values[index],
        "holmRank0": rank,
        "holmThreshold": threshold,
        "holmReject": rejected[index],
        "bonferroniThreshold": ALPHA / len(p_values) if p_values else None,
        "bonferroniReject": bool(p_values) and p_values[index] <= ALPHA / len(p_values),
        "nReject": sum(1 for flag in rejected if flag),
    }


def score_variant(
    items: list[dict[str, Any]],
    *,
    max_depth: int,
    include_geometry_extras: bool,
) -> dict[str, Any]:
    flags: list[int] = []
    for item in items:
        result = apply_s3(
            item,
            max_depth=max_depth,
            include_geometry_extras=include_geometry_extras,
        )
        if not result.fired or result.answer is None:
            continue
        flags.append(1 if answers_match(str(item["key"]), result.answer) else 0)
    summary = summarize_flags(flags)
    summary["maxDepth"] = max_depth
    summary["includeGeometryExtras"] = include_geometry_extras
    return summary


def main() -> None:
    items = load_items()
    selected = [
        item
        for item in items
        if item.get("responseType") == "selected"
        and str(item.get("authority")) == "teks"
        and str(item.get("claim")) == "g5"
    ]
    fired_rows: list[dict[str, Any]] = []
    unique_depth1_selected = 0
    unique_depth1_is_key = 0
    n_in_closure: list[int] = []
    for item in selected:
        result = apply_s3(item)
        if result.extra.get("uniqueDepth1"):
            unique_depth1_selected += 1
            unique_key = next(
                (key for key, depth in (result.extra.get("depths") or {}).items() if depth <= 1),
                None,
            )
            if unique_key and answers_match(str(item["key"]), unique_key):
                unique_depth1_is_key += 1
        if not result.fired or result.answer is None:
            continue
        parsed = parsed_numeric_options(item)
        pairs = [(key, value) for key, value, _text in parsed]
        lower = lower_central_key(pairs)
        depths = result.extra.get("depths") or {}
        min_depth = int(result.extra.get("minDepth"))
        at_min = [key for key, depth in depths.items() if depth == min_depth]
        decided = "depth" if len(at_min) == 1 else "tie-break"
        correct = answers_match(str(item["key"]), result.answer)
        n_in_closure.append(len(depths))
        judgment = STEM_JUDGMENTS.get(str(item["id"]))
        if judgment is None:
            raise SystemExit(f"missing stem judgment for {item['id']}")
        fired_rows.append(
            {
                "id": item["id"],
                "administration": administration_id(item),
                "stem": item["stem"],
                "choices": item.get("choices"),
                "key": item["key"],
                "pick": result.answer,
                "correct": correct,
                "nInClosure": len(depths),
                "minDepthByOption": depths,
                "minDepth": min_depth,
                "nAtMinDepth": len(at_min),
                "decidedBy": decided,
                "lowerCentralAllOptions": lower,
                "lowerCentralCorrect": bool(lower and answers_match(str(item["key"]), lower)),
                "uniqueDepth1": bool(result.extra.get("uniqueDepth1")),
                "keyInClosure": str(item["key"]) in depths,
                "judgmentKind": judgment["kind"],
                "judgment": judgment["line"],
            }
        )

    if len(fired_rows) != 40:
        raise SystemExit(f"expected 40 fired TEKS g5 items, got {len(fired_rows)}")
    if len(STEM_JUDGMENTS) != 40:
        raise SystemExit(f"expected 40 stem judgments, got {len(STEM_JUDGMENTS)}")

    depth_decided = [row for row in fired_rows if row["decidedBy"] == "depth"]
    tie_decided = [row for row in fired_rows if row["decidedBy"] == "tie-break"]
    depth_hits = sum(1 for row in depth_decided if row["correct"])
    tie_hits = sum(1 for row in tie_decided if row["correct"])

    expected_random = 0.0
    for row in fired_rows:
        if row["decidedBy"] == "depth":
            expected_random += 1.0 if row["correct"] else 0.0
            continue
        key = str(row["key"])
        at_min = [option for option, depth in row["minDepthByOption"].items() if depth == row["minDepth"]]
        if key in at_min:
            expected_random += 1.0 / len(at_min)
    expected_random_rate = expected_random / len(fired_rows)

    rng = Mulberry32(RANDOM_TIE_SEED)
    random_rates: list[float] = []
    for _draw in range(N_RANDOM_TIES):
        n_correct = 0
        for row in fired_rows:
            if row["decidedBy"] == "depth":
                n_correct += 1 if row["correct"] else 0
                continue
            at_min = sorted(
                option for option, depth in row["minDepthByOption"].items() if depth == row["minDepth"]
            )
            index = int(math.floor(rng.random() * len(at_min)))
            pick = at_min[index]
            n_correct += 1 if answers_match(str(row["key"]), pick) else 0
        random_rates.append(n_correct / len(fired_rows))
    random_rates.sort()
    random_ci = (
        random_rates[int(math.floor(0.025 * N_RANDOM_TIES))],
        random_rates[min(N_RANDOM_TIES - 1, int(math.floor(0.975 * N_RANDOM_TIES)))],
    )

    lower_flags = [1 if row["lowerCentralCorrect"] else 0 for row in fired_rows]
    lower_summary = summarize_flags(lower_flags)
    n_same_pick = sum(1 for row in fired_rows if row["pick"] == row["lowerCentralAllOptions"])
    closure_adds = n_same_pick != len(fired_rows) or abs(lower_summary["rate"] - 0.525) > 1e-12
    if closure_adds:
        closure_sentence = (
            "Closure is not redundant with lower-central on these 40 items: "
            f"{len(fired_rows) - n_same_pick} picks differ, and the unique depth-1 one-op items "
            "are exactly where S3 parts from lower-central."
        )
    else:
        closure_sentence = (
            "The closure adds nothing over lower-central on these 40 items: every pick matches."
        )

    depth_sensitivity = {
        "depth1Only": score_variant(selected, max_depth=1, include_geometry_extras=True),
        "depth2Registered": score_variant(selected, max_depth=2, include_geometry_extras=True),
        "depth2WithoutGeometryExtras": score_variant(
            selected,
            max_depth=2,
            include_geometry_extras=False,
        ),
    }

    by_admin: dict[str, list[int]] = defaultdict(list)
    for row in fired_rows:
        by_admin[str(row["administration"])].append(1 if row["correct"] else 0)
    admin_rows = []
    n_above = 0
    n_below = 0
    n_equal = 0
    clusters: list[list[int]] = []
    for admin in sorted(by_admin):
        flags = by_admin[admin]
        rate = sum(flags) / len(flags)
        admin_rows.append(
            {
                "administration": admin,
                "n": len(flags),
                "nCorrect": int(sum(flags)),
                "rate": rate,
            }
        )
        clusters.append(flags)
        if rate > CHANCE:
            n_above += 1
        elif rate < CHANCE:
            n_below += 1
        else:
            n_equal += 1
    clustered_ci = cluster_bootstrap_ci(clusters, CLUSTER_BOOT_N, CLUSTER_BOOT_SEED)
    n_unequal = n_above + n_below
    sign_p = binomial_sf(n_above, n_unequal, 0.5) if n_unequal else 1.0

    n_unique_d1_fired = sum(1 for row in fired_rows if row["uniqueDepth1"])
    n_unique_d1_fired_is_key = sum(
        1
        for row in fired_rows
        if row["uniqueDepth1"]
        and row["key"]
        in [option for option, depth in row["minDepthByOption"].items() if depth <= 1]
        and answers_match(
            str(row["key"]),
            next(option for option, depth in row["minDepthByOption"].items() if depth <= 1),
        )
    )

    kind_counts = {
        "one_operation": sum(1 for row in fired_rows if row["judgmentKind"] == "one_operation"),
        "coincidence": sum(1 for row in fired_rows if row["judgmentKind"] == "coincidence"),
        "parse_artifact": sum(1 for row in fired_rows if row["judgmentKind"] == "parse_artifact"),
    }
    artifact_rows = [row for row in fired_rows if row["judgmentKind"] == "parse_artifact"]
    clean_rows = [row for row in fired_rows if row["judgmentKind"] != "parse_artifact"]
    artifact_free = summarize_flags([1 if row["correct"] else 0 for row in clean_rows])
    artifact_free["nRemoved"] = len(artifact_rows)
    artifact_free["artifactHits"] = sum(1 for row in artifact_rows if row["correct"])

    version1_p = binomial_sf(21, 40, CHANCE)
    cell_table = json.loads((OUT_DIR / "strategy-cell-table.json").read_text(encoding="utf-8"))
    family_p = [float(row["binomialPGreater"]) for row in cell_table["rows"]]
    holm_67 = holm_step_for(family_p, version1_p)
    prior_family = json.loads((ROOT / "exports" / "apriori-cell-table.json").read_text(encoding="utf-8"))["family"]
    pooled_p = [float(row["binomialPGreater"]) for row in prior_family] + family_p
    holm_172 = holm_step_for(pooled_p, version1_p)

    s3_table = [
        row
        for row in cell_table["rows"]
        if row["channel"] == "s3-closure"
        and (
            (row["authority"] == "teks")
            or (row["authority"] == "nyregents" and row["claim"] in {"algebra-i", "geometry"})
        )
    ]
    clearing = [row for row in s3_table if row["clearsBar"]]
    grade5_only = (
        len(clearing) == 1
        and clearing[0]["authority"] == "teks"
        and clearing[0]["claim"] == "g5"
    )

    flags_40 = [1 if row["correct"] else 0 for row in fired_rows]
    registered = summarize_flags(flags_40)
    if registered["nCorrect"] != 21 or abs(registered["rate"] - 0.525) > 1e-12:
        raise SystemExit(f"version-1 21/40 drifted: {registered}")

    payload = {
        "channel": "s3-closure",
        "cell": {"authority": "teks", "claim": "g5"},
        "version1Unchanged": {
            "nFired": 40,
            "nCorrect": 21,
            "rate": 0.525,
            "ci95": [0.375, 0.675],
            "binomialPGreater": version1_p,
            "nSelected": len(selected),
        },
        "tieBreakDecomposition": {
            "nFired": 40,
            "nDecidedByDepth": len(depth_decided),
            "nHitsDecidedByDepth": depth_hits,
            "rateAmongDepthDecided": depth_hits / len(depth_decided) if depth_decided else 0.0,
            "nDecidedByTieBreak": len(tie_decided),
            "nHitsDecidedByTieBreak": tie_hits,
            "rateAmongTieBreakDecided": tie_hits / len(tie_decided) if tie_decided else 0.0,
            "randomTieBreaks": {
                "nDraws": N_RANDOM_TIES,
                "seed": RANDOM_TIE_SEED,
                "expectedRate": expected_random_rate,
                "drawMean": sum(random_rates) / len(random_rates),
                "drawCi95": [random_ci[0], random_ci[1]],
                "drawMin": random_rates[0],
                "drawMax": random_rates[-1],
            },
            "lowerCentralAloneOnSame40": lower_summary,
            "nPicksIdenticalToLowerCentral": n_same_pick,
            "closureAddsOverLowerCentral": closure_adds,
            "sentence": closure_sentence,
        },
        "depthSensitivity": depth_sensitivity,
        "clusteredByAdministration": {
            "clusterBootstrap": {
                "nBoot": CLUSTER_BOOT_N,
                "seed": CLUSTER_BOOT_SEED,
                "ci95": [clustered_ci[0], clustered_ci[1]],
                "clearsBar": clustered_ci[0] > CHANCE,
            },
            "administrations": admin_rows,
            "signTest": {
                "nAdministrations": len(admin_rows),
                "nRateAboveChance": n_above,
                "nRateBelowChance": n_below,
                "nEqualChance": n_equal,
                "nUnequal": n_unequal,
                "oneSidedPGreater": sign_p,
                "null": "P(administration rate > 0.25) = 0.5, equals dropped",
            },
        },
        "closureDensity": {
            "meanOptionsInClosurePerFiredItem": sum(n_in_closure) / len(n_in_closure),
            "shareSelectedUniqueDepth1": unique_depth1_selected / len(selected),
            "nSelectedUniqueDepth1": unique_depth1_selected,
            "nSelectedUniqueDepth1IsKey": unique_depth1_is_key,
            "shareFiredUniqueDepth1": n_unique_d1_fired / len(fired_rows),
            "nFiredUniqueDepth1": n_unique_d1_fired,
            "nFiredUniqueDepth1IsKey": n_unique_d1_fired_is_key,
            "uniqueDepth1IsKeyRateAmongThoseItems": (
                unique_depth1_is_key / unique_depth1_selected if unique_depth1_selected else 0.0
            ),
            "note": (
                "The cleanest version of the claim is unique depth-1: exactly one option "
                "in the depth-1 closure, and that option is the key."
            ),
        },
        "otherCellsSameRule": {
            "source": "exports/addendum-strategies/strategy-cell-table.json",
            "grade5IsOnlyClearingCell": grade5_only,
            "clears": clearing,
            "rows": s3_table,
        },
        "stemRead": {
            "nRead": 40,
            "counts": kind_counts,
            "parseArtifactIsConstructProblem": True,
            "artifactFree": artifact_free,
            "items": [
                {
                    "id": row["id"],
                    "key": row["key"],
                    "pick": row["pick"],
                    "correct": row["correct"],
                    "kind": row["judgmentKind"],
                    "judgment": row["judgment"],
                    "nInClosure": row["nInClosure"],
                    "decidedBy": row["decidedBy"],
                }
                for row in fired_rows
            ],
        },
        "holmVerification": {
            "oneSidedBinomialP_21_of_40_vs_0.25": version1_p,
            "family67": holm_67,
            "family172": holm_172,
            "matchesPublished": {
                "family67Reject": holm_67["holmReject"] is True,
                "family172Reject": holm_172["holmReject"] is True,
                "publishedFamily67Rejects": 1,
                "publishedFamily172Rejects": 1,
            },
        },
        "firedItems": [
            {key: value for key, value in row.items() if key not in {"stem", "choices"}}
            | {"stem": row["stem"], "choices": row["choices"]}
            for row in fired_rows
        ],
    }
    dump_json(OUT_DIR / "s3-teks-g5-robustness.json", payload)
    print("wrote", OUT_DIR / "s3-teks-g5-robustness.json")
    print("depth hits", depth_hits, "/", len(depth_decided), "tie hits", tie_hits, "/", len(tie_decided))
    print("random expected", expected_random_rate, "lc", lower_summary["rate"])
    print("depth1", depth_sensitivity["depth1Only"])
    print("clustered", clustered_ci, "sign", n_above, n_below, sign_p)
    print("kinds", kind_counts, "artifact-free", artifact_free["rate"], artifact_free["nFired"])
    print("g5 only clear", grade5_only)
    print("p", version1_p, "holm67", holm_67["holmReject"], "holm172", holm_172["holmReject"])


if __name__ == "__main__":
    main()
