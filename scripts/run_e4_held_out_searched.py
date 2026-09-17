#!/usr/bin/env python3
"""E4: temporal held-out of searched cue programs and fitted n-grams."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any

from addendum_lib import (
    ADDENDUM_DIR,
    FEATURE_NAMES,
    MIN_N_WITNESS,
    administration_id,
    administration_sort_key,
    apply_cue_program,
    bootstrap_ci_mulberry,
    chance_rate,
    dump_json,
    load_items,
    option_features,
    parse_weighted_program,
)

SEARCHED_ROWS = [
    {
        "programId": "search/w:positionC-1,numericMed+1,distinctive-1/timss-to-state",
        "authority": "teks",
        "claim": "g6",
        "frozenN": 11,
        "frozenRate": 0.6363636363636364,
        "frozenRandomP95": 0.369,
    },
    {
        "programId": "search/w:overlap+1,numericMin-1,specificity-1/timss-to-state",
        "authority": "nyregents",
        "claim": "algebra-i",
        "frozenN": 13,
        "frozenRate": 0.5384615384615384,
        "frozenRandomP95": 0.268,
    },
    {
        "programId": "search/w:longest-1,overlap+1,numericMax-1/timss-to-state",
        "authority": "nyregents",
        "claim": "algebra-i",
        "frozenN": 19,
        "frozenRate": 0.47368421052631576,
        "frozenRandomP95": 0.268,
    },
    {
        "programId": "search/w:overlap+1,numericMin-1,distinctive-1/timss-to-state",
        "authority": "nyregents",
        "claim": "geometry",
        "frozenN": 20,
        "frozenRate": 0.5,
        "frozenRandomP95": 0.292,
    },
]


def selected_cell(items: list[dict[str, Any]], authority: str, claim: str) -> list[dict[str, Any]]:
    return [
        item
        for item in items
        if item.get("authority") == authority
        and item.get("claim") == claim
        and item.get("responseType") == "selected"
        and item.get("choices")
    ]


def split_by_administration(
    items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    by_admin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_admin[administration_id(item)].append(item)
    admins = sorted(by_admin, key=administration_sort_key)
    if len(admins) < 2:
        return [], items, [], admins
    cut = max(1, len(admins) // 2)
    early_ids = admins[:cut]
    late_ids = admins[cut:]
    early = [item for admin in early_ids for item in by_admin[admin]]
    late = [item for admin in late_ids for item in by_admin[admin]]
    return early, late, early_ids, late_ids


def score_items(program: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    flags: list[int] = []
    chances: list[float] = []
    for item in items:
        answer = apply_cue_program(program, item)
        if answer is None:
            continue
        chance = chance_rate(item)
        if chance is None:
            continue
        flags.append(1 if answer.upper() == str(item["key"]).upper() else 0)
        chances.append(chance)
    n = len(flags)
    rate = sum(flags) / n if n else 0.0
    chance = sum(chances) / n if n else 0.0
    ci = bootstrap_ci_mulberry(flags, 1000, 11) if n else (0.0, 0.0)
    return {
        "nScored": n,
        "nCorrect": sum(flags),
        "passRate": rate,
        "chanceRate": chance,
        "ci95": [ci[0], ci[1]],
        "beatsChance": n >= MIN_N_WITNESS and ci[0] > chance,
    }


def random_program(rng: random.Random, complexity: int, index: int) -> dict[str, Any]:
    pool = list(FEATURE_NAMES)
    features: list[str] = []
    while len(features) < complexity and pool:
        features.append(pool.pop(rng.randrange(len(pool))))
    weights = {feat: (-1.0 if rng.random() < 0.5 else 1.0) for feat in features}
    return {
        "id": f"search/random:k{complexity}:{index}",
        "kind": "random",
        "features": features,
        "weights": weights,
        "complexity": complexity,
    }


def random_p95(eval_items: list[dict[str, Any]], seed: int = 20260916) -> dict[str, Any]:
    rng = random.Random(seed)
    rates: list[float] = []
    details: list[dict[str, Any]] = []
    for complexity in (1, 2, 3):
        for index in range(40):
            program = random_program(rng, complexity, 1000 * complexity + index)
            scored = score_items(program, eval_items)
            if scored["nScored"] >= 8:
                rates.append(scored["passRate"])
                details.append({"programId": program["id"], "n": scored["nScored"], "passRate": scored["passRate"]})
    if not rates:
        return {"p95": 1.0, "nRandomWithNAtLeast8": 0, "rates": []}
    ordered = sorted(rates)
    index = min(len(ordered) - 1, max(0, math.ceil(0.95 * len(ordered)) - 1))
    return {
        "p95": ordered[index],
        "nRandomWithNAtLeast8": len(ordered),
        "percentileMethod": "ceil(0.95 * n) - 1, matching runner/src/programs/search.ts percentile",
    }


def pass_rate_only(program: dict[str, Any], items: list[dict[str, Any]]) -> tuple[int, float]:
    n = 0
    hit = 0
    for item in items:
        answer = apply_cue_program(program, item)
        if answer is None:
            continue
        n += 1
        if answer.upper() == str(item["key"]).upper():
            hit += 1
    return n, (hit / n if n else 0.0)


def enumerate_weighted() -> list[dict[str, Any]]:
    programs: list[dict[str, Any]] = []
    names = list(FEATURE_NAMES)
    for feat in names:
        programs.append(
            {
                "id": f"search/atom:{feat}",
                "kind": "atomic",
                "features": [feat],
                "weights": {feat: 1.0},
                "complexity": 1,
            }
        )
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            programs.append(
                {
                    "id": f"search/and:{left}+{right}",
                    "kind": "conjunction",
                    "features": [left, right],
                    "weights": {left: 1.0, right: 1.0},
                    "complexity": 2,
                }
            )
    signs = (-1.0, 1.0)

    def combos(values: list[str], k: int) -> list[list[str]]:
        if k == 0:
            return [[]]
        if k > len(values):
            return []
        out: list[list[str]] = []
        for index, head in enumerate(values):
            for tail in combos(values[index + 1 :], k - 1):
                out.append([head, *tail])
        return out

    for k in (1, 2, 3):
        for feats in combos(names, k):
            sign_rows: list[list[float]] = [[]]
            for _ in feats:
                sign_rows = [row + [sign] for row in sign_rows for sign in signs]
            for row in sign_rows:
                if k == 1 and row[0] == 1.0:
                    continue
                if k == 2 and all(sign == 1.0 for sign in row):
                    continue
                weights = {feat: sign for feat, sign in zip(feats, row)}
                ident = "search/w:" + ",".join(
                    f"{feat}{'+' if sign >= 0 else '-'}{int(abs(sign))}" for feat, sign in zip(feats, row)
                )
                programs.append(
                    {
                        "id": ident,
                        "kind": "weighted",
                        "features": feats,
                        "weights": weights,
                        "complexity": k,
                    }
                )
    return programs


def train_ngram(train: list[dict[str, Any]]) -> dict[str, Any]:
    key_count: dict[str, int] = defaultdict(int)
    dist_count: dict[str, int] = defaultdict(int)
    key_total = 0
    dist_total = 0
    selected = [item for item in train if item.get("responseType") == "selected" and item.get("choices")]
    for item in selected:
        for letter in sorted((item.get("choices") or {}).keys()):
            feats = option_features(item, letter)
            is_key = letter.upper() == str(item["key"]).upper()
            bag = key_count if is_key else dist_count
            if is_key:
                key_total += len(feats)
            else:
                dist_total += len(feats)
            for feat in feats:
                bag[feat] += 1
    return {
        "keyCount": dict(key_count),
        "distCount": dict(dist_count),
        "keyTotal": key_total or 1,
        "distTotal": dist_total or 1,
        "trainN": len(selected),
    }


def apply_ngram(model: dict[str, Any], item: dict[str, Any]) -> str | None:
    letters = sorted((item.get("choices") or {}).keys())
    if not letters:
        return None
    vocab = len(set(model["keyCount"]) | set(model["distCount"])) + 1

    def log_prob(count: int, total: int) -> float:
        return math.log((count + 1) / (total + vocab))

    scores: dict[str, float] = {}
    best = -math.inf
    winners: list[str] = []
    for letter in letters:
        score = 0.0
        for feat in option_features(item, letter):
            score += log_prob(model["keyCount"].get(feat, 0), model["keyTotal"]) - log_prob(
                model["distCount"].get(feat, 0), model["distTotal"]
            )
        scores[letter] = score
        if score > best:
            best = score
            winners = [letter]
        elif score == best:
            winners.append(letter)
    return winners[0] if winners else None


def score_callable(fn, items: list[dict[str, Any]]) -> dict[str, Any]:
    flags: list[int] = []
    chances: list[float] = []
    for item in items:
        answer = fn(item)
        if answer is None:
            continue
        chance = chance_rate(item)
        if chance is None:
            continue
        flags.append(1 if str(answer).upper() == str(item["key"]).upper() else 0)
        chances.append(chance)
    n = len(flags)
    rate = sum(flags) / n if n else 0.0
    chance = sum(chances) / n if n else 0.0
    ci = bootstrap_ci_mulberry(flags, 1000, 13) if n else (0.0, 0.0)
    return {
        "nScored": n,
        "nCorrect": sum(flags),
        "passRate": rate,
        "chanceRate": chance,
        "ci95": [ci[0], ci[1]],
        "beatsChance": n >= MIN_N_WITNESS and ci[0] > chance,
    }


def main() -> None:
    items = load_items()
    enumerated = enumerate_weighted()
    searched_results: list[dict[str, Any]] = []
    any_clears = False

    for spec in SEARCHED_ROWS:
        program = parse_weighted_program(spec["programId"])
        subset = selected_cell(items, spec["authority"], spec["claim"])
        early, late, early_ids, late_ids = split_by_administration(subset)
        late_score = score_items(program, late)
        late_random = random_p95(late)
        late_clears = (
            late_score["beatsChance"]
            and late_score["nScored"] >= MIN_N_WITNESS
            and late_score["passRate"] >= late_random["p95"]
        )
        # Re-search on early administrations; evaluate the train-best program on late.
        ranked: list[tuple[float, int, dict[str, Any]]] = []
        for cand in enumerated:
            n_train, rate_train = pass_rate_only(cand, early)
            if n_train >= 8:
                ranked.append((rate_train, n_train, cand))
        ranked.sort(key=lambda row: row[0], reverse=True)
        best = ranked[0][2] if ranked else None
        refit_late = score_items(best, late) if best else None
        refit_clears = False
        if refit_late is not None:
            refit_clears = (
                refit_late["beatsChance"]
                and refit_late["nScored"] >= MIN_N_WITNESS
                and refit_late["passRate"] >= late_random["p95"]
            )
        any_clears = any_clears or late_clears or refit_clears
        searched_results.append(
            {
                "frozenProgramId": spec["programId"],
                "authority": spec["authority"],
                "claim": spec["claim"],
                "frozenN": spec["frozenN"],
                "frozenRate": spec["frozenRate"],
                "frozenRandomP95": spec["frozenRandomP95"],
                "nItemsCellSelected": len(subset),
                "earlyAdministrations": early_ids,
                "lateAdministrations": late_ids,
                "nEarlyItems": len(early),
                "nLateItems": len(late),
                "frozenProgramOnLate": late_score,
                "randomP95OnLate": late_random["p95"],
                "randomP95Meta": {k: late_random[k] for k in ("nRandomWithNAtLeast8", "percentileMethod")},
                "frozenProgramClearsHeldOutBar": late_clears,
                "refitBestOnEarly": None
                if best is None
                else {
                    "programId": best["id"],
                    "trainRate": ranked[0][0],
                    "trainN": ranked[0][1],
                    "late": refit_late,
                    "clearsHeldOutBar": refit_clears,
                },
            }
        )

    # Fitted n-grams: earlier vs later administrations of NY Regents + STAAR pooled,
    # and within geometry / algebra-ii / algebra-i.
    ngram_rows: list[dict[str, Any]] = []
    state_items = [
        item
        for item in items
        if item.get("corpus") in {"nyregents", "staar", "nysed", "mcas", "eqao"}
        and item.get("responseType") == "selected"
    ]
    for label, pool in [
        ("state-pooled", state_items),
        ("nyregents-geometry", selected_cell(items, "nyregents", "geometry")),
        ("nyregents-algebra-i", selected_cell(items, "nyregents", "algebra-i")),
        ("nyregents-algebra-ii", selected_cell(items, "nyregents", "algebra-ii")),
        ("teks-g6", selected_cell(items, "teks", "g6")),
    ]:
        early, late, early_ids, late_ids = split_by_administration(pool)
        if not early or not late:
            ngram_rows.append({"slice": label, "note": "need at least two administrations", "clearsHeldOutBar": False})
            continue
        model = train_ngram(early)
        scored = score_callable(lambda item, trained=model: apply_ngram(trained, item), late)
        ngram_rows.append(
            {
                "slice": label,
                "earlyAdministrations": early_ids,
                "lateAdministrations": late_ids,
                "nTrain": model["trainN"],
                "late": scored,
                "clearsHeldOutBar": scored["beatsChance"],
            }
        )
        any_clears = any_clears or scored["beatsChance"]

    payload = {
        "experiment": "E4",
        "question": (
            "Do the thin searched programs (n=11 to 20) or fitted n-grams survive a "
            "temporal administration split?"
        ),
        "split": "sort administrations by year then session; first half train, second half test",
        "bar": "n>=10, lower 95% CI > chance, and for searched rules also passRate >= random-program p95 on the same late set",
        "anyClearsHeldOutBar": any_clears,
        "searched": searched_results,
        "fittedNgrams": ngram_rows,
        "cite": "exports/addendum/held-out-searched.json",
    }
    dump_json(ADDENDUM_DIR / "held-out-searched.json", payload)
    print("wrote", ADDENDUM_DIR / "held-out-searched.json")
    print("any clears", any_clears)
    for row in searched_results:
        late = row["frozenProgramOnLate"]
        print(
            row["claim"],
            "late n",
            late["nScored"],
            "rate",
            round(late["passRate"], 3) if late["nScored"] else None,
            "ci",
            [round(x, 3) for x in late["ci95"]] if late["nScored"] else None,
            "p95",
            round(row["randomP95OnLate"], 3),
            "clears",
            row["frozenProgramClearsHeldOutBar"],
            "refit",
            row["refitBestOnEarly"]["programId"] if row["refitBestOnEarly"] else None,
            "refitClears",
            row["refitBestOnEarly"]["clearsHeldOutBar"] if row["refitBestOnEarly"] else None,
        )


if __name__ == "__main__":
    main()
