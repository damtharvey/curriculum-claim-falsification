#!/usr/bin/env python3
"""Score pre-registered strategy channels S1–S5. Writes each channel JSON as it finishes."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from addendum_lib import (  # noqa: E402
    MIN_N_WITNESS,
    ROOT,
    answers_match,
    binomial_sf,
    bootstrap_ci_mulberry,
    dump_json,
    holm_reject,
    load_items,
)
from addendum_lib import Mulberry32  # noqa: E402
from strategy_channels import (  # noqa: E402
    S5_BRANCHES,
    SOLVING_CELLS,
    TEKS_SOLVE_TAGS,
    TRANSFORM_NAMES,
    apply_s1,
    apply_s2,
    apply_s3,
    apply_s4,
    apply_s4_v2,
    apply_s5,
    choice_keys,
    constraint_keyword_matched,
    extract_equations,
    extract_equations_v2,
    format_chance_k,
    is_solving_item,
    letter_b,
    lower_central_key,
    option_candidate_value,
    parsed_numeric_options,
    s1_edges_by_transform,
    s2_survivors,
    s5_from_precomputed,
)

OUT_DIR = ROOT / "exports" / "addendum-strategies"
EXISTING_FAMILY_TESTS = 105
N_RANDOM = 200
RANDOM_SEED = 20260916
ALPHA = 0.05
UNBOUND_CATALOG = (
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
HEADLINE_CELLS = (
    ("nyregents", "geometry"),
    ("eqao", "g6"),
    ("timss", "knowing"),
    ("timss", "applying"),
    ("timss", "reasoning"),
)


def percentile_p95(rates: list[float]) -> float:
    if not rates:
        return 1.0
    ordered = sorted(rates)
    index = min(len(ordered) - 1, int(math.floor(0.95 * len(ordered))))
    return ordered[index]


def cell_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item["authority"]), str(item["claim"]))


def selected_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in items if item.get("responseType") == "selected"]


def eligible_cells(selected: list[dict[str, Any]]) -> list[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter(cell_key(item) for item in selected)
    return sorted(cell for cell, count in counts.items() if count >= MIN_N_WITNESS)


def summarize(
    flags: list[int],
    chances: list[float],
) -> dict[str, Any]:
    n = len(flags)
    n_correct = int(sum(flags))
    rate = n_correct / n if n else 0.0
    chance = sum(chances) / n if n else 0.0
    ci = bootstrap_ci_mulberry(flags, 1000, 11) if n else (0.0, 0.0)
    p_value = binomial_sf(n_correct, n, chance) if n and 0.0 < chance < 1.0 else (0.0 if n and chance <= 0.0 and n_correct else 1.0)
    clears = n >= MIN_N_WITNESS and chance > 0 and ci[0] > chance
    return {
        "nScored": n,
        "nCorrect": n_correct,
        "passRate": rate,
        "chanceRate": chance,
        "ci95": [ci[0], ci[1]],
        "binomialPGreater": p_value,
        "clearsBar": clears,
        "inFamily": n >= MIN_N_WITNESS and chance > 0,
    }


def load_split_capped(path: Path, train_cap: int = 1500, eval_cap: int = 400) -> dict[str, list[dict[str, Any]]]:
    train: list[dict[str, Any]] = []
    hold: list[dict[str, Any]] = []
    raw = path.read_text(encoding="utf-8").splitlines()

    def split_of(item: dict[str, Any]) -> str:
        if item.get("split"):
            return str(item["split"])
        item_id = str(item.get("id") or "")
        if "-train-" in item_id:
            return "train"
        if "-validation-" in item_id or "-dev-" in item_id:
            return "dev"
        if "-test-" in item_id:
            return "test"
        return "all"

    for line in raw:
        if not line.strip():
            continue
        item = json.loads(line)
        split = split_of(item)
        if split == "train":
            if len(train) < train_cap:
                train.append(item)
        elif split in {"test", "validation", "dev"}:
            if len(hold) < eval_cap:
                hold.append(item)
        if len(train) >= train_cap and len(hold) >= eval_cap:
            break
    if len(hold) < 32:
        for line in raw:
            if not line.strip():
                continue
            item = json.loads(line)
            if split_of(item) != "train" and len(hold) < eval_cap:
                hold.append(item)
            if len(hold) >= eval_cap:
                break
    return {"train": train, "hold": hold}


def existing_unbound_rows() -> list[dict[str, Any]]:
    path = ROOT / "exports" / "rule-chance.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    kept = [
        {
            "programId": row["programId"],
            "authority": row["authority"],
            "claim": row["claim"],
            "nScored": row["nScored"],
            "nCorrect": row["nCorrect"],
            "passRate": row["passRate"],
            "chanceRate": row["chanceRate"],
            "ci95": row["ci95"],
            "beatsChance": row["beatsChance"],
            "witnessEligible": row["witnessEligible"],
            "note": row.get("note", ""),
        }
        for row in rows
        if row["programId"] in UNBOUND_CATALOG and int(row["nScored"]) >= MIN_N_WITNESS
    ]
    return kept


def score_channel(
    selected: list[dict[str, Any]],
    cells: list[tuple[str, str]],
    apply: Callable[[dict[str, Any]], Any],
    *,
    chance_field: str | None = None,
    include: Callable[[dict[str, Any], Any], bool] | None = None,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in selected:
        result = apply(item)
        if include is not None and not include(item, result):
            continue
        if not result.fired or result.answer is None or result.chance is None:
            continue
        correct = answers_match(str(item["key"]), result.answer)
        chance = result.chance if chance_field is None else float(result.extra.get(chance_field, result.chance))
        by_cell[cell_key(item)].append(
            {
                "item": item,
                "result": result,
                "correct": correct,
                "chance": chance,
            }
        )
    rows: list[dict[str, Any]] = []
    for authority, claim in cells:
        scored = by_cell[(authority, claim)]
        flags = [1 if row["correct"] else 0 for row in scored]
        chances = [float(row["chance"]) for row in scored]
        summary = summarize(flags, chances)
        rows.append({"authority": authority, "claim": claim, **summary})
    return rows, by_cell


def attach_family(rows: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    family = [row for row in rows if row.get("inFamily")]
    p_values = [float(row["binomialPGreater"]) for row in family]
    holm = holm_reject(p_values) if p_values else []
    bonf = ALPHA / len(family) if family else None
    for row, rejected in zip(family, holm):
        row["holmReject05Family"] = rejected
        row["bonferroniReject05Family"] = bonf is not None and row["binomialPGreater"] <= bonf
        if extra:
            row.update(extra)
    for row in rows:
        row.setdefault("holmReject05Family", False)
        row.setdefault("bonferroniReject05Family", False)
    return family


def write_channel(name: str, payload: dict[str, Any]) -> None:
    path = OUT_DIR / name
    dump_json(path, payload)
    print("wrote", path, "family", payload.get("nFamilyTests"), "clears", payload.get("nClearsPerCellBar"))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prereg_hash = (OUT_DIR / "preregistration.sha256").read_text(encoding="utf-8")
    print("preregistration.sha256 present:\n", prereg_hash)
    items = load_items()
    selected = selected_items(items)
    cells = eligible_cells(selected)
    n_selected_by_cell = Counter(cell_key(item) for item in selected)
    print("items", len(items), "selected", len(selected), "eligible cells", len(cells))

    print("precomputing S1 edges")
    s1_edges = {item["id"]: s1_edges_by_transform(item) for item in selected}

    def s1_apply(item: dict[str, Any]) -> Any:
        return apply_s1(item, edges_by_transform=s1_edges[item["id"]])

    s1_rows, s1_scored = score_channel(selected, cells, s1_apply)
    s1_family = attach_family(s1_rows)
    unique_hub_share = {}
    for authority, claim in cells:
        scored = s1_scored[(authority, claim)]
        if scored:
            unique_hub_share[(authority, claim)] = sum(
                1 for row in scored if row["result"].extra.get("uniqueHub")
            ) / len(scored)
        else:
            unique_hub_share[(authority, claim)] = None
    for row in s1_rows:
        key = (row["authority"], row["claim"])
        row["uniqueHubShare"] = unique_hub_share[key]
        row["nSelected"] = n_selected_by_cell[key]
        row["coverage"] = row["nScored"] / row["nSelected"] if row["nSelected"] else 0.0
        row["programId"] = "s1-hub"
        row["channel"] = "s1-hub"

    print("S1 random p95")
    rng = Mulberry32(RANDOM_SEED)
    s1_p95: dict[tuple[str, str], float] = {}
    s1_variant_rates: dict[tuple[str, str], list[float]] = {cell: [] for cell in cells}
    for _variant in range(N_RANDOM):
        names = list(TRANSFORM_NAMES)
        for index in range(len(names) - 1, 0, -1):
            swap_at = int(math.floor(rng.random() * (index + 1)))
            names[index], names[swap_at] = names[swap_at], names[index]
        subset = names[:10]
        variant_rng = Mulberry32(int(math.floor(rng.random() * 2**32)))
        cell_flags: dict[tuple[str, str], list[int]] = defaultdict(list)
        for item in selected:
            result = apply_s1(
                item,
                transform_names=subset,
                tie="random",
                rng=variant_rng,
                edges_by_transform=s1_edges[item["id"]],
            )
            if not result.fired or result.answer is None:
                continue
            cell_flags[cell_key(item)].append(1 if answers_match(str(item["key"]), result.answer) else 0)
        for cell in cells:
            flags = cell_flags[cell]
            s1_variant_rates[cell].append(sum(flags) / len(flags) if flags else 0.0)
    for cell in cells:
        s1_p95[cell] = percentile_p95(s1_variant_rates[cell])
    for row in s1_rows:
        cell = (row["authority"], row["claim"])
        row["randomP95"] = s1_p95[cell]
        row["clearsBar"] = bool(row["clearsBar"] and row["passRate"] > s1_p95[cell])
        row["clearsChanceOnly"] = row["nScored"] >= MIN_N_WITNESS and row["chanceRate"] > 0 and row["ci95"][0] > row["chanceRate"]
    s1_clears = [row for row in s1_family if row["clearsBar"]]
    write_channel(
        "s1-hub.json",
        {
            "channel": "s1-hub",
            "version": 1,
            "question": "Does a distractor-derivation hub (common student-error transforms among numeric options) clear the witness bar?",
            "citation": "Haladyna and Downing 1989; Haladyna, Downing, Rodriguez 2002; Rodriguez 2005.",
            "nFamilyTests": len(s1_family),
            "nClearsPerCellBar": len(s1_clears),
            "nHolmRejectFamily": sum(1 for row in s1_family if row["holmReject05Family"]),
            "randomProgram": {"nVariants": N_RANDOM, "subsetSize": 10, "seed": RANDOM_SEED},
            "clears": s1_clears,
            "familyRows": s1_family,
            "allRows": s1_rows,
        },
    )

    print("S2")
    s2_rows, s2_scored = score_channel(selected, cells, apply_s2)
    for row in s2_rows:
        key = (row["authority"], row["claim"])
        cell_items = [item for item in selected if cell_key(item) == key]
        scored = s2_scored[key]
        n_selected = len(cell_items)
        n_one = 0
        n_key = 0
        n_keyword = 0
        n_elim = 0
        remainders: list[int] = []
        for item in cell_items:
            survivors, predicates = s2_survivors(item)
            remainders.append(len(survivors))
            if len(survivors) == 1:
                n_one += 1
            if str(item["key"]) in survivors:
                n_key += 1
            if predicates:
                n_keyword += 1
            if 0 < len(survivors) < len(choice_keys(item)):
                n_elim += 1
        keyword_flags = [
            1 if row_s["correct"] else 0
            for row_s in scored
            if row_s["result"].extra.get("keywordMatched")
        ]
        keyword_chances = [
            float(row_s["chance"])
            for row_s in scored
            if row_s["result"].extra.get("keywordMatched")
        ]
        keyword_summary = summarize(keyword_flags, keyword_chances) if keyword_flags else None
        row.update(
            {
                "programId": "s2-elimination",
                "channel": "s2-elimination",
                "nSelected": n_selected,
                "coverage": row["nScored"] / n_selected if n_selected else 0.0,
                "meanRemainingOptions": sum(remainders) / n_selected if n_selected else 0.0,
                "shareExactlyOneSurvivor": n_one / n_selected if n_selected else 0.0,
                "keySurvivalRate": n_key / n_selected if n_selected else 0.0,
                "shareKeywordMatched": n_keyword / n_selected if n_selected else 0.0,
                "shareEliminated": n_elim / n_selected if n_selected else 0.0,
                "keywordMatchedSubset": keyword_summary,
            }
        )
    s2_family = attach_family(s2_rows)
    s2_clears = [row for row in s2_family if row["clearsBar"]]
    write_channel(
        "s2-elimination.json",
        {
            "channel": "s2-elimination",
            "version": 1,
            "question": "Do shallow stem-keyword constraints eliminate options so that lower-central among survivors beats effective chance?",
            "citation": "Millman, Bishop, and Ebel 1965 elimination strategies.",
            "nFamilyTests": len(s2_family),
            "nClearsPerCellBar": len(s2_clears),
            "nHolmRejectFamily": sum(1 for row in s2_family if row["holmReject05Family"]),
            "clears": s2_clears,
            "familyRows": s2_family,
            "allRows": s2_rows,
        },
    )

    print("S3")
    s3_results = {item["id"]: apply_s3(item) for item in selected}

    def s3_apply(item: dict[str, Any]) -> Any:
        return s3_results[item["id"]]

    s3_rows, s3_scored = score_channel(selected, cells, s3_apply)
    for row in s3_rows:
        key = (row["authority"], row["claim"])
        cell_items = [item for item in selected if cell_key(item) == key]
        n_selected = len(cell_items)
        n_unique_d1 = 0
        n_fired = 0
        imputed_correct = 0.0
        for item in cell_items:
            result = s3_results[item["id"]]
            chance_k = format_chance_k(item) or 0.25
            if result.extra.get("uniqueDepth1"):
                n_unique_d1 += 1
            if result.fired and result.answer is not None:
                n_fired += 1
                imputed_correct += 1.0 if answers_match(str(item["key"]), result.answer) else 0.0
            else:
                imputed_correct += chance_k
        row.update(
            {
                "programId": "s3-closure",
                "channel": "s3-closure",
                "nSelected": n_selected,
                "coverage": n_fired / n_selected if n_selected else 0.0,
                "shareUniqueDepth1": n_unique_d1 / n_selected if n_selected else 0.0,
                "rateWithAbstentionAsChance": imputed_correct / n_selected if n_selected else 0.0,
            }
        )
    s3_family = attach_family(s3_rows)
    s3_clears = [row for row in s3_family if row["clearsBar"]]
    unbound_existing = existing_unbound_rows()
    write_channel(
        "s3-closure.json",
        {
            "channel": "s3-closure",
            "version": 1,
            "question": "Does depth-2 arithmetic closure of stem numbers (unbound execution) clear the witness bar?",
            "citation": "Paper unbound-execution channel; Millman, Bishop, and Ebel 1965 use-the-numbers-given.",
            "reusedCatalogUnbound": {
                "source": "exports/rule-chance.json",
                "note": (
                    "The nine catalog unbound formulas in runner/src/programs/apriori.ts are implemented "
                    "and already scored. Reused here as comparison only. S3 is a different program "
                    "(full depth-2 closure). Catalog n>=10 rows that beat chance: unit-rate on TEKS g5 only."
                ),
                "nRowsNge10": len(unbound_existing),
                "beatsChance": [row for row in unbound_existing if row["beatsChance"]],
                "rows": unbound_existing,
            },
            "nFamilyTests": len(s3_family),
            "nClearsPerCellBar": len(s3_clears),
            "nHolmRejectFamily": sum(1 for row in s3_family if row["holmReject05Family"]),
            "clears": s3_clears,
            "familyRows": s3_family,
            "allRows": s3_rows,
        },
    )

    print("S4")
    s4_results = {item["id"]: apply_s4(item) for item in selected}

    def s4_apply(item: dict[str, Any]) -> Any:
        return s4_results[item["id"]]

    s4_rows, s4_scored = score_channel(selected, cells, s4_apply)
    for row in s4_rows:
        key = (row["authority"], row["claim"])
        cell_items = [item for item in selected if cell_key(item) == key]
        n_selected = len(cell_items)
        n_parse = sum(1 for item in cell_items if extract_equations(str(item.get("stem") or "")))
        n_fired = sum(1 for item in cell_items if s4_results[item["id"]].fired)
        imputed = 0.0
        for item in cell_items:
            result = s4_results[item["id"]]
            chance_k = format_chance_k(item) or 0.25
            if result.fired and result.answer is not None:
                imputed += 1.0 if answers_match(str(item["key"]), result.answer) else 0.0
            else:
                imputed += chance_k
        row.update(
            {
                "programId": "s4-backsolve",
                "channel": "s4-backsolve",
                "nSelected": n_selected,
                "nParseableEquation": n_parse,
                "coverage": n_fired / n_selected if n_selected else 0.0,
                "rateWithAbstentionAsChance": imputed / n_selected if n_selected else 0.0,
                "solvingTaggedCell": key in SOLVING_CELLS,
            }
        )
    s4_family = attach_family(s4_rows)

    def pooled_s4(predicate: Callable[[dict[str, Any]], bool], label: str) -> dict[str, Any]:
        flags: list[int] = []
        chances: list[float] = []
        n_sel = 0
        for item in selected:
            if not predicate(item):
                continue
            n_sel += 1
            result = s4_results[item["id"]]
            if result.fired and result.answer is not None and result.chance is not None:
                flags.append(1 if answers_match(str(item["key"]), result.answer) else 0)
                chances.append(result.chance)
        summary = summarize(flags, chances)
        summary.update({"label": label, "nSelected": n_sel, "coverage": summary["nScored"] / n_sel if n_sel else 0.0})
        return summary

    teks_solve = pooled_s4(
        lambda item: str(item.get("authority")) == "teks" and str(item.get("officialTag") or "") in TEKS_SOLVE_TAGS,
        "teks/solve-se",
    )
    timss_alg = pooled_s4(
        lambda item: str(item.get("authority")) == "timss"
        and bool(__import__("re").search(r"algebra", str(item.get("contentDomain") or ""), __import__("re").I)),
        "timss/algebra",
    )
    solving_pool = pooled_s4(is_solving_item, "solving-tagged-pooled")
    rest_pool = pooled_s4(lambda item: not is_solving_item(item), "rest-pooled")
    s4_clears = [row for row in s4_family if row["clearsBar"]]
    write_channel(
        "s4-backsolve.json",
        {
            "channel": "s4-backsolve",
            "version": 1,
            "question": "Does substituting options into a parseable single-variable stem equation uniquely recover the key?",
            "citation": "Millman, Bishop, and Ebel 1965 substitution; verify-versus-solve.",
            "nFamilyTests": len(s4_family),
            "nClearsPerCellBar": len(s4_clears),
            "nHolmRejectFamily": sum(1 for row in s4_family if row["holmReject05Family"]),
            "breakoutsNotInFamily": {
                "teksSolveStudentExpectations": teks_solve,
                "timssAlgebraContentDomain": timss_alg,
                "solvingTaggedPooled": solving_pool,
                "restPooled": rest_pool,
            },
            "clears": s4_clears,
            "familyRows": s4_family,
            "allRows": s4_rows,
        },
    )

    print("S5 precompute parts")
    s5_parts: dict[str, dict[str, Any]] = {}
    for item in selected:
        s4 = s4_results[item["id"]]
        s3 = s3_results[item["id"]]
        survivors, _predicates = s2_survivors(item)
        if not survivors:
            survivors = choice_keys(item)
        unique_depth1 = None
        if s3.extra.get("uniqueDepth1"):
            unique_depth1 = next(
                (key for key, depth in (s3.extra.get("depths") or {}).items() if depth <= 1),
                None,
            )
        survivor_item = {
            **item,
            "choices": {key: (item.get("choices") or {}).get(key) for key in survivors},
        }
        hub = apply_s1(survivor_item, edges_by_transform=s1_edges[item["id"]])
        unique_hub = hub.answer if hub.extra.get("uniqueHub") else None
        numeric_pairs = [
            (key, value)
            for key, value, _text in parsed_numeric_options(survivor_item)
        ]
        lower = lower_central_key(numeric_pairs) if numeric_pairs else (survivors[0] if survivors else letter_b(item))
        s5_parts[item["id"]] = {
            "s4_unique": s4.answer if s4.fired else None,
            "s3_depth1_unique": unique_depth1,
            "survivors": survivors,
            "unique_hub": unique_hub,
            "lower_central": lower,
            "numeric_pairs": numeric_pairs,
        }

    def s5_apply(item: dict[str, Any]) -> Any:
        parts = s5_parts[item["id"]]
        return s5_from_precomputed(item, **parts)

    s5_rows, s5_scored = score_channel(selected, cells, s5_apply)
    print("S5 random p95")
    rng5 = Mulberry32(RANDOM_SEED + 1)
    s5_p95: dict[tuple[str, str], float] = {}
    s5_variant_rates: dict[tuple[str, str], list[float]] = {cell: [] for cell in cells}
    for _variant in range(N_RANDOM):
        order = list(S5_BRANCHES)
        for index in range(len(order) - 1, 0, -1):
            swap_at = int(math.floor(rng5.random() * (index + 1)))
            order[index], order[swap_at] = order[swap_at], order[index]
        variant_rng = Mulberry32(int(math.floor(rng5.random() * 2**32)))
        cell_flags: dict[tuple[str, str], list[int]] = defaultdict(list)
        for item in selected:
            parts = s5_parts[item["id"]]
            result = s5_from_precomputed(
                item,
                branch_order=order,
                rng=variant_rng,
                **parts,
            )
            if not result.fired or result.answer is None:
                continue
            cell_flags[cell_key(item)].append(1 if answers_match(str(item["key"]), result.answer) else 0)
        for cell in cells:
            flags = cell_flags[cell]
            s5_variant_rates[cell].append(sum(flags) / len(flags) if flags else 0.0)
    for cell in cells:
        s5_p95[cell] = percentile_p95(s5_variant_rates[cell])

    for row in s5_rows:
        key = (row["authority"], row["claim"])
        scored = s5_scored[key]
        cell_items = [item for item in selected if cell_key(item) == key]
        n_selected = len(cell_items)
        branches = Counter(str(row_s["result"].extra.get("usedBranch")) for row_s in scored)
        flags_k = [1 if row_s["correct"] else 0 for row_s in scored]
        chances_k = [float(row_s["result"].extra.get("chanceK") or format_chance_k(row_s["item"]) or 0.25) for row_s in scored]
        vs_k = summarize(flags_k, chances_k)
        row.update(
            {
                "programId": "s5-portfolio",
                "channel": "s5-portfolio",
                "nSelected": n_selected,
                "coverage": 1.0,
                "branchCounts": dict(branches),
                "againstOneOverK": vs_k,
                "randomP95": s5_p95[key],
            }
        )
        row["clearsChanceOnly"] = row["clearsBar"]
        row["clearsBar"] = bool(row["clearsBar"] and row["passRate"] > s5_p95[key])
        row["headlineCell"] = key in HEADLINE_CELLS
    s5_family = attach_family(s5_rows)
    s5_clears = [row for row in s5_family if row["clearsBar"]]
    headlines = [row for row in s5_rows if (row["authority"], row["claim"]) in HEADLINE_CELLS]
    write_channel(
        "s5-portfolio.json",
        {
            "channel": "s5-portfolio",
            "version": 1,
            "question": "Does a fixed-order test-wise taker (S4 then S3 depth-1 then S2+S1 then lower-central then B) clear the witness bar?",
            "citation": "Millman et al. 1965 test-wiseness as a sequence of strategies; this paper's channel stack.",
            "branchOrder": list(S5_BRANCHES),
            "letterPrior": "B",
            "nFamilyTests": len(s5_family),
            "nClearsPerCellBar": len(s5_clears),
            "nHolmRejectFamily": sum(1 for row in s5_family if row["holmReject05Family"]),
            "headlineCells": headlines,
            "clears": s5_clears,
            "familyRows": s5_family,
            "allRows": s5_rows,
        },
    )

    dump_json(
        OUT_DIR / "random-program-p95.json",
        {
            "nVariants": N_RANDOM,
            "seed": RANDOM_SEED,
            "s1": {
                "rule": "uniform subset of 10 of 15 transforms; random tie-break among max out-degree",
                "p95ByCell": [
                    {"authority": a, "claim": c, "randomP95": s1_p95[(a, c)], "variantRates": s1_variant_rates[(a, c)]}
                    for a, c in cells
                ],
            },
            "s5": {
                "rule": "shuffled branch order; random lower-central / hub ties; letter B fixed",
                "p95ByCell": [
                    {"authority": a, "claim": c, "randomP95": s5_p95[(a, c)], "variantRates": s5_variant_rates[(a, c)]}
                    for a, c in cells
                ],
            },
        },
    )
    print("wrote", OUT_DIR / "random-program-p95.json")

    print("controls")
    control_payload: dict[str, Any] = {
        "evalRule": "runner/src/run_real_controls.ts loadSplitCapped train 1500 / eval 400",
        "datasets": [],
    }
    for name in ("openbookqa", "swag"):
        path = ROOT / "data" / f"real-controls-{name}.jsonl"
        split = load_split_capped(path)
        hold = split["hold"]
        print(name, "hold", len(hold))
        dataset: dict[str, Any] = {"name": name, "nHold": len(hold), "path": str(path), "channels": {}}
        for channel_id, apply in (
            ("s1-hub", apply_s1),
            ("s2-elimination", apply_s2),
            ("s3-closure", apply_s3),
            ("s4-backsolve", apply_s4),
            ("s5-portfolio", apply_s5),
        ):
            flags: list[int] = []
            chances: list[float] = []
            n_sel = len(hold)
            for item in hold:
                result = apply(item)
                if result.fired and result.answer is not None and result.chance is not None:
                    flags.append(1 if answers_match(str(item["key"]), result.answer) else 0)
                    chances.append(result.chance)
            summary = summarize(flags, chances)
            summary["nSelected"] = n_sel
            summary["coverage"] = summary["nScored"] / n_sel if n_sel else 0.0
            dataset["channels"][channel_id] = summary
        control_payload["datasets"].append(dataset)
    dump_json(OUT_DIR / "controls.json", control_payload)
    print("wrote", OUT_DIR / "controls.json")

    print("hand-check ids")
    ordered = sorted(selected, key=lambda item: str(item["id"]))
    s2_sample: list[dict[str, Any]] = []
    for item in ordered:
        if constraint_keyword_matched(item):
            s2_sample.append(item)
        if len(s2_sample) >= 15:
            break
    s2_ids = {item["id"] for item in s2_sample}
    s4_sample: list[dict[str, Any]] = []
    for item in ordered:
        if item["id"] in s2_ids:
            continue
        if extract_equations(str(item.get("stem") or "")):
            s4_sample.append(item)
        if len(s4_sample) >= 15:
            break

    def s2_trace(item: dict[str, Any]) -> dict[str, Any]:
        result = apply_s2(item)
        survivors, predicates = s2_survivors(item)
        return {
            "id": item["id"],
            "authority": item["authority"],
            "claim": item["claim"],
            "stem": item["stem"],
            "choices": item.get("choices"),
            "key": item["key"],
            "nConstraints": len(predicates),
            "survivors": survivors,
            "keySurvives": item["key"] in survivors,
            "answer": result.answer,
            "correct": bool(result.answer and answers_match(str(item["key"]), result.answer)),
            "judgment": None,
            "notes": None,
        }

    def s4_trace(item: dict[str, Any]) -> dict[str, Any]:
        result = s4_results.get(item["id"]) or apply_s4(item)
        equations = extract_equations(str(item.get("stem") or ""))
        return {
            "id": item["id"],
            "authority": item["authority"],
            "claim": item["claim"],
            "stem": item["stem"],
            "choices": item.get("choices"),
            "key": item["key"],
            "equations": [
                {"left": eq.left, "rel": eq.rel, "right": eq.right, "variable": eq.variable}
                for eq in equations
            ],
            "fired": result.fired,
            "answer": result.answer,
            "hits": result.extra.get("hits"),
            "keyNumeric": option_candidate_value(str((item.get("choices") or {}).get(item["key"], item["key"]))),
            "judgment": None,
            "notes": None,
        }

    dump_json(
        OUT_DIR / "hand-check.json",
        {
            "selectionRule": (
                "selected-response sorted by id; first 15 constraint-keyword stems for S2; "
                "first 15 remaining with extract_equations non-empty for S4"
            ),
            "s2": [s2_trace(item) for item in s2_sample],
            "s4": [s4_trace(item) for item in s4_sample],
        },
    )
    print("wrote", OUT_DIR / "hand-check.json")

    print("combined family table")
    table_rows: list[dict[str, Any]] = []
    for channel_id, rows in (
        ("s1-hub", s1_rows),
        ("s2-elimination", s2_rows),
        ("s3-closure", s3_rows),
        ("s4-backsolve", s4_rows),
        ("s5-portfolio", s5_rows),
    ):
        for row in rows:
            if not row.get("inFamily"):
                continue
            table_rows.append(
                {
                    "channel": channel_id,
                    "authority": row["authority"],
                    "claim": row["claim"],
                    "n": row["nScored"],
                    "nCorrect": row["nCorrect"],
                    "rate": row["passRate"],
                    "chance": row["chanceRate"],
                    "ci95": row["ci95"],
                    "binomialPGreater": row["binomialPGreater"],
                    "clearsBar": row["clearsBar"],
                    "randomP95": row.get("randomP95"),
                    "coverage": row.get("coverage"),
                }
            )
    table_rows.sort(key=lambda row: (row["channel"], row["authority"], row["claim"]))
    p_values = [float(row["binomialPGreater"]) for row in table_rows]
    holm = holm_reject(p_values) if p_values else []
    bonf = ALPHA / len(table_rows) if table_rows else None
    for index, (row, rejected) in enumerate(zip(table_rows, holm)):
        row["familyIndex"] = index
        row["holmReject05Family"] = rejected
        row["bonferroniReject05Family"] = bonf is not None and row["binomialPGreater"] <= bonf

    prior_family = json.loads((ROOT / "exports" / "apriori-cell-table.json").read_text(encoding="utf-8"))["family"]
    pooled_p = [float(row["binomialPGreater"]) for row in prior_family] + p_values
    pooled_holm = holm_reject(pooled_p)
    new_holm_pooled = pooled_holm[len(prior_family) :]
    pooled_bonf = ALPHA / len(pooled_p) if pooled_p else None
    for row, rejected in zip(table_rows, new_holm_pooled):
        row["holmReject05PooledWith105"] = rejected
        row["bonferroniReject05PooledWith105"] = (
            pooled_bonf is not None and row["binomialPGreater"] <= pooled_bonf
        )

    n_family = len(table_rows)
    dump_json(
        OUT_DIR / "strategy-cell-table.json",
        {
            "existingAprioriFamilyTests": EXISTING_FAMILY_TESTS,
            "nFamilyTestsThisAddendum": n_family,
            "nFamilyTestsPooledWith105": EXISTING_FAMILY_TESTS + n_family,
            "bonferroniThresholdThisFamily": bonf,
            "bonferroniThresholdPooled": pooled_bonf,
            "nClearsPerCellBar": sum(1 for row in table_rows if row["clearsBar"]),
            "nHolmRejectThisFamily": sum(1 for row in table_rows if row["holmReject05Family"]),
            "nHolmRejectPooledWith105": sum(1 for row in table_rows if row["holmReject05PooledWith105"]),
            "nHolmRejectAmong105InPooled": sum(1 for flag in pooled_holm[: len(prior_family)] if flag),
            "rows": table_rows,
        },
    )
    print("wrote", OUT_DIR / "strategy-cell-table.json", "m", n_family)


def key_satisfies_used(item: dict[str, Any], result: Any) -> bool | None:
    used = result.extra.get("used") or {}
    key_letter = str(item.get("key"))
    hits = result.extra.get("hits") or []
    if not used:
        return None
    return key_letter in hits


def run_s4_version_2() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prereg_v2 = OUT_DIR / "preregistration-v2.sha256"
    if not prereg_v2.exists():
        raise SystemExit("preregistration-v2.sha256 is required before scoring S4 version 2")
    print("preregistration-v2.sha256 present:\n", prereg_v2.read_text(encoding="utf-8"))
    items = load_items()
    selected = selected_items(items)
    cells = eligible_cells(selected)
    print("S4 v2 items", len(items), "selected", len(selected), "eligible cells", len(cells))
    s4_results = {item["id"]: apply_s4_v2(item) for item in selected}

    def s4_apply(item: dict[str, Any]) -> Any:
        return s4_results[item["id"]]

    s4_rows, s4_scored = score_channel(selected, cells, s4_apply)
    key_misses: list[dict[str, Any]] = []
    for row in s4_rows:
        key = (row["authority"], row["claim"])
        cell_items = [item for item in selected if cell_key(item) == key]
        n_selected = len(cell_items)
        n_parse = sum(1 for item in cell_items if extract_equations_v2(str(item.get("stem") or "")))
        n_fired = sum(1 for item in cell_items if s4_results[item["id"]].fired)
        imputed = 0.0
        for item in cell_items:
            result = s4_results[item["id"]]
            chance_k = format_chance_k(item) or 0.25
            if result.fired and result.answer is not None:
                imputed += 1.0 if answers_match(str(item["key"]), result.answer) else 0.0
                satisfies = key_satisfies_used(item, result)
                if satisfies is False:
                    key_misses.append(
                        {
                            "id": item["id"],
                            "authority": item["authority"],
                            "claim": item["claim"],
                            "key": item["key"],
                            "pick": result.answer,
                            "hits": result.extra.get("hits"),
                            "used": result.extra.get("used"),
                        }
                    )
            else:
                imputed += chance_k
        row.update(
            {
                "programId": "s4-backsolve-v2",
                "channel": "s4-backsolve-v2",
                "nSelected": n_selected,
                "nParseableEquation": n_parse,
                "coverage": n_fired / n_selected if n_selected else 0.0,
                "uniqueSatisfierShare": n_fired / n_parse if n_parse else 0.0,
                "rateWithAbstentionAsChance": imputed / n_selected if n_selected else 0.0,
                "solvingTaggedCell": key in SOLVING_CELLS or (
                    key[0] == "teks" and any(
                        str(item.get("officialTag") or "") in TEKS_SOLVE_TAGS
                        for item in cell_items
                    )
                    and key == ("teks", "solve-se")
                ),
            }
        )
        row["solvingTaggedCell"] = key in SOLVING_CELLS
    s4_family = attach_family(s4_rows)

    def pooled_s4(predicate: Any, label: str) -> dict[str, Any]:
        flags: list[int] = []
        chances: list[float] = []
        n_sel = 0
        n_parse = 0
        n_fired = 0
        imputed = 0.0
        for item in selected:
            if not predicate(item):
                continue
            n_sel += 1
            result = s4_results[item["id"]]
            chance_k = format_chance_k(item) or 0.25
            if extract_equations_v2(str(item.get("stem") or "")):
                n_parse += 1
            if result.fired and result.answer is not None and result.chance is not None:
                n_fired += 1
                flags.append(1 if answers_match(str(item["key"]), result.answer) else 0)
                chances.append(result.chance)
                imputed += 1.0 if answers_match(str(item["key"]), result.answer) else 0.0
            else:
                imputed += chance_k
        summary = summarize(flags, chances)
        summary.update(
            {
                "label": label,
                "nSelected": n_sel,
                "nParseableEquation": n_parse,
                "coverage": n_fired / n_sel if n_sel else 0.0,
                "uniqueSatisfierShare": n_fired / n_parse if n_parse else 0.0,
                "rateWithAbstentionAsChance": imputed / n_sel if n_sel else 0.0,
            }
        )
        return summary

    teks_solve = pooled_s4(
        lambda item: str(item.get("authority")) == "teks" and str(item.get("officialTag") or "") in TEKS_SOLVE_TAGS,
        "teks/solve-se",
    )
    timss_alg = pooled_s4(
        lambda item: str(item.get("authority")) == "timss"
        and bool(__import__("re").search(r"algebra", str(item.get("contentDomain") or ""), __import__("re").I)),
        "timss/algebra",
    )
    solving_pool = pooled_s4(is_solving_item, "solving-tagged-pooled")
    rest_pool = pooled_s4(lambda item: not is_solving_item(item), "rest-pooled")
    s4_clears = [row for row in s4_family if row["clearsBar"]]
    solving_cell_rows = [
        row
        for row in s4_rows
        if (row["authority"], row["claim"]) in SOLVING_CELLS
        or (row["authority"] == "eqao" and row["claim"] == "g9")
    ]
    write_channel(
        "s4-backsolve-v2.json",
        {
            "channel": "s4-backsolve-v2",
            "version": 2,
            "question": "Does substituting options into a version-2 parseable stem equation uniquely recover the key?",
            "citation": "Millman, Bishop, and Ebel 1965 substitution; verify-versus-solve.",
            "preregistration": "exports/addendum-strategies/preregistration.md S4 version 2 section; preregistration-v2.sha256",
            "nFamilyTests": len(s4_family),
            "nClearsPerCellBar": len(s4_clears),
            "nHolmRejectFamily": sum(1 for row in s4_family if row["holmReject05Family"]),
            "coverageBeforeVersion1": {
                "solvingTaggedFiredOverEligible": 1 / 1186,
                "nFamilyTests": 0,
            },
            "breakoutsNotInFamily": {
                "teksSolveStudentExpectations": teks_solve,
                "timssAlgebraContentDomain": timss_alg,
                "solvingTaggedPooled": solving_pool,
                "restPooled": rest_pool,
            },
            "solvingTaggedCells": solving_cell_rows,
            "keyDoesNotSatisfy": {
                "n": len(key_misses),
                "items": key_misses,
            },
            "clears": s4_clears,
            "familyRows": s4_family,
            "allRows": s4_rows,
        },
    )
    ordered_fired = sorted(
        (item for item in selected if s4_results[item["id"]].fired),
        key=lambda item: str(item["id"]),
    )
    sample = ordered_fired[:30]
    traces = []
    for item in sample:
        result = s4_results[item["id"]]
        used = result.extra.get("used") or {}
        traces.append(
            {
                "id": item["id"],
                "authority": item["authority"],
                "claim": item["claim"],
                "stem": item["stem"],
                "extractedEquation": used,
                "allExtracted": result.extra.get("equations"),
                "choices": item.get("choices"),
                "satisfier": result.answer,
                "hits": result.extra.get("hits"),
                "key": item["key"],
                "keyNumeric": option_candidate_value(str((item.get("choices") or {}).get(item["key"], item["key"]))),
                "correct": answers_match(str(item["key"]), result.answer or ""),
                "keySatisfies": key_satisfies_used(item, result),
                "judgment": None,
                "notes": None,
            }
        )
    dump_json(
        OUT_DIR / "s4-v2-hand-check.json",
        {
            "selectionRule": "selected-response items on which S4 v2 fired, sorted by id; first 30",
            "nFiredCensus": len(ordered_fired),
            "nSample": len(sample),
            "items": traces,
        },
    )
    print("wrote", OUT_DIR / "s4-v2-hand-check.json", "sample", len(sample), "fired", len(ordered_fired))
    print("family", len(s4_family), "clears", len(s4_clears), "key-miss", len(key_misses))
    print("solving coverage", solving_pool.get("coverage"), "fired", solving_pool.get("nScored"), "of", solving_pool.get("nSelected"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s4-version", type=int, default=1, choices=[1, 2])
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    if args.s4_version == 2:
        run_s4_version_2()
    else:
        main()
