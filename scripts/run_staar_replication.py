#!/usr/bin/env python3
"""Parse registered STAAR replication forms and score pre-registered rules."""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from addendum_lib import (  # noqa: E402
    ROOT,
    answers_match,
    dump_json,
    lower_central_key as catalog_lower_central,
    parsed_numeric_options as catalog_parsed_numeric,
)
from ingest_lib import dump_jsonl, extract_pdf_text  # noqa: E402
from parse_staar_bulk import (  # noqa: E402
    grade_from_name,
    parse_items,
    parse_keys_from_pdf,
    year_from_name,
)
from strategy_channels import (  # noqa: E402
    apply_s3,
    parse_option_number,
    parsed_numeric_options,
)

OUT_DIR = ROOT / "exports" / "replication-staar"
INVENTORY_PATH = OUT_DIR / "inventory.json"
ITEMS_PATH = ROOT / "data" / "items.jsonl"
N_BOOT = 1000
BOOT_SEED = 11
HAND_CHECK_SEED = 20260916
HAND_CHECK_N = 20
MIN_N_WITNESS = 10
POWER_MIN_N = 46
PRIORITY_GRADES = ["5", "3", "4", "6", "7", "8", "alg1"]

THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{3}(?:\D|$))")
PAGE_RE = re.compile(r"(?i)\bpage\s+\d+\b")
GRADE_FOOTER_RE = re.compile(r"(?i)\bgrade\s+[3-8]\b")
STAAR_WORD_RE = re.compile(r"(?i)\bstaar\b")
ITEM_CODE_RE = re.compile(r"\b\d{5}_\d\b")
CHROME_LINE_RE = re.compile(r"(?i)^(mathematics|go on|stop|texas education agency)\s*$")
CHOICE_LABEL_RE = re.compile(r"\(([A-DJFGHJ])\)|(?<![A-Za-z])[A-DJFGHJ][.\)]")
AXIS_CUE_RE = re.compile(
    r"(?i)coordinate|grid|axis|scatter|bar chart|bar graph|stem-and-leaf|dot plot|\bplot\b|\bgraph\b"
)
AGE_BIN_RE = re.compile(r"\b\d{1,2}\s*[-–]\s*\d{1,2}\b")
ISOLATED_DIGIT_RE = re.compile(r"(?<![\d.])(\d)(?![\d.])")
INTEGER_TOKEN_RE = re.compile(r"(?<![\d.])(\d+)(?![\d.])")
CATALOG_NUMBER_TOKEN_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
ITEM_ID_QUESTION_RE = re.compile(r"-q(\d+)$")
ARITH_DIFFS = {1, 2, 5, 10, 15}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def bootstrap_ci(flags: list[int], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> tuple[float, float]:
    if not flags:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(flags)
    samples: list[float] = []
    for _ in range(n_boot):
        total = 0
        for _i in range(n):
            total += flags[rng.randrange(n)]
        samples.append(total / n)
    samples.sort()
    low = samples[int(0.025 * (n_boot - 1))]
    high = samples[int(0.975 * (n_boot - 1))]
    return (low, high)


def question_from_id(item_id: str) -> int | None:
    match = ITEM_ID_QUESTION_RE.search(item_id)
    return int(match.group(1)) if match else None


def drop_arithmetic_runs(text: str) -> str:
    tokens = list(INTEGER_TOKEN_RE.finditer(text))
    if len(tokens) < 4:
        return text
    drop_spans: list[tuple[int, int]] = []
    index = 0
    values = [int(match.group(1)) for match in tokens]
    while index < len(values):
        best_end = index
        for diff in ARITH_DIFFS:
            end = index
            while end + 1 < len(values) and values[end + 1] - values[end] == diff:
                end += 1
            if end - index + 1 >= 4:
                best_end = max(best_end, end)
        if best_end - index + 1 >= 4:
            drop_spans.append((tokens[index].start(), tokens[best_end].end()))
            index = best_end + 1
        else:
            index += 1
    if not drop_spans:
        return text
    out: list[str] = []
    cursor = 0
    for start, end in drop_spans:
        out.append(text[cursor:start])
        out.append(" ")
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


def filter_stem_text(text: str, item_number: int | None) -> str:
    filtered = THOUSANDS_RE.sub("", text)
    filtered = PAGE_RE.sub(" ", filtered)
    filtered = GRADE_FOOTER_RE.sub(" ", filtered)
    filtered = STAAR_WORD_RE.sub(" ", filtered)
    filtered = ITEM_CODE_RE.sub(" ", filtered)
    kept_lines = [line for line in filtered.splitlines() if not CHROME_LINE_RE.match(line.strip())]
    filtered = "\n".join(kept_lines)
    filtered = CHOICE_LABEL_RE.sub(" ", filtered)
    if item_number is not None:
        filtered = re.sub(rf"^{item_number}\b\s*", " ", filtered)
        filtered = re.sub(r"(?i)\bitem\s+\d+\b", " ", filtered)
    if "?" in filtered:
        filtered = filtered[: filtered.rfind("?") + 1]
    if AXIS_CUE_RE.search(filtered):
        isolated = {int(match.group(1)) for match in ISOLATED_DIGIT_RE.finditer(filtered)}
        if len(isolated & set(range(10))) >= 8:
            filtered = ISOLATED_DIGIT_RE.sub(" ", filtered)
        filtered = drop_arithmetic_runs(filtered)
        if re.search(r"(?i)stem-and-leaf", filtered):
            filtered = ISOLATED_DIGIT_RE.sub(" ", filtered)
        if re.search(r"(?i)\b(age|year|visitor)", filtered):
            filtered = AGE_BIN_RE.sub(" ", filtered)
    return filtered


def filtered_item(item: dict[str, Any]) -> dict[str, Any]:
    copy = dict(item)
    number = question_from_id(str(item.get("id") or ""))
    copy["stem"] = filter_stem_text(str(item.get("stem") or ""), number)
    figure = item.get("figure")
    if isinstance(figure, dict) and figure.get("transcription"):
        figure_copy = dict(figure)
        figure_copy["transcription"] = filter_stem_text(str(figure["transcription"]), number)
        copy["figure"] = figure_copy
    return copy


def catalog_number_tokens(text: str) -> list[str]:
    return CATALOG_NUMBER_TOKEN_RE.findall(text)


def catalog_numbers(text: str) -> list[float]:
    values: list[float] = []
    for token in catalog_number_tokens(text):
        number = float(token.replace(",", ""))
        if math.isfinite(number):
            values.append(number)
    return values


def apply_unit_rate(item: dict[str, Any]) -> tuple[str | None, bool]:
    numbers = [value for value in catalog_numbers(str(item.get("stem") or "")) if value != 0]
    if len(numbers) < 2:
        return None, False
    left, right = numbers[0], numbers[1]
    candidates = [left / right, right / left]
    choices = item.get("choices") or {}
    for value in candidates:
        for key in sorted(choices):
            option_value = parse_option_number(str(choices[key]))
            if option_value is None:
                continue
            scale = max(1.0, abs(option_value), abs(value))
            if abs(option_value - value) <= 1e-4 * scale or abs(option_value - value) < 0.01:
                return key, True
    return None, False


def apply_stem_repeat(item: dict[str, Any]) -> tuple[str | None, bool]:
    tokens = catalog_number_tokens(str(item.get("stem") or ""))
    if not tokens:
        return None, False
    choices = item.get("choices") or {}
    hits = [
        key
        for key in sorted(choices)
        if any(token in str(choices[key]) for token in tokens)
    ]
    if not hits:
        return None, False
    return hits[0], True


def apply_lower_central(item: dict[str, Any]) -> tuple[str | None, bool]:
    parsed = catalog_parsed_numeric(item)
    pick = catalog_lower_central(parsed)
    return pick, pick is not None


def n_parseable_numeric_options(item: dict[str, Any]) -> int:
    choices = item.get("choices") or {}
    return sum(1 for text in choices.values() if parse_option_number(str(text)) is not None)


def chance_of(item: dict[str, Any]) -> float | None:
    n_choices = len(item.get("choices") or {})
    return 1.0 / n_choices if n_choices else None


def summarize_rule(
    name: str,
    cell: str,
    rows: list[dict[str, Any]],
    *,
    chance_values: list[float] | None = None,
) -> dict[str, Any]:
    n = len(rows)
    hits = sum(1 for row in rows if row["correct"])
    rate = hits / n if n else 0.0
    flags = [1 if row["correct"] else 0 for row in rows]
    ci = bootstrap_ci(flags) if n else (0.0, 0.0)
    if chance_values:
        chance = sum(chance_values) / len(chance_values)
    else:
        chance = 0.25 if n else 0.0
    clears = n >= MIN_N_WITNESS and chance > 0 and ci[0] > chance
    return {
        "rule": name,
        "cell": cell,
        "nFired": n,
        "nHits": hits,
        "rate": rate,
        "chance": chance,
        "ci95": [ci[0], ci[1]],
        "clearsBar": clears,
        "underpowered": n < MIN_N_WITNESS,
    }


def load_inventory() -> dict[str, Any]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def parse_forms(inventory: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    form_reports: list[dict[str, Any]] = []
    for form in inventory["replicationCandidates"]:
        test_path = ROOT / form["testPdf"]
        key_path = ROOT / form["keyPdf"]
        keys = parse_keys_from_pdf(key_path)
        test_text = extract_pdf_text(test_path)
        meta = {
            "grade": form["grade"] if form["grade"] != "alg1" else "alg1",
            "year": form["year"],
            "source": f"file:{form['testPdf']}",
        }
        parsed = parse_items(test_text, keys, meta)
        selected = [row for row in parsed if row.get("responseType") == "selected"]
        four_numeric = [row for row in selected if n_parseable_numeric_options(row) == 4]
        key_in_choices = [
            row
            for row in selected
            if str(row.get("key")) in (row.get("choices") or {})
        ]
        stopped = False
        stop_reason = None
        if not keys:
            stopped = True
            stop_reason = "zero_keys_recovered"
        elif keys and not key_in_choices:
            stopped = True
            stop_reason = "keys_not_in_parsed_choices"
        report = {
            "formId": form["formId"],
            "year": form["year"],
            "grade": form["grade"],
            "testPdf": form["testPdf"],
            "keyPdf": form["keyPdf"],
            "nKeysRecovered": len(keys),
            "nItemsParsed": len(parsed),
            "nWithKey": len(parsed),
            "nSelected": len(selected),
            "nSelectedKeyInChoices": len(key_in_choices),
            "nFourParseableNumericOptions": len(four_numeric),
            "nParseFailures": len(keys) - len(parsed),
            "stopped": stopped,
            "stopReason": stop_reason,
        }
        form_reports.append(report)
        if stopped:
            continue
        for row in parsed:
            row["replicationFormId"] = form["formId"]
            items.append(row)
    return items, form_reports


def pdf_window(path: Path, question: int) -> str:
    text = extract_pdf_text(path)
    pattern = re.compile(rf"(?:^|\n)\s*{question}\s+(\S.*)")
    for match in pattern.finditer(text):
        rest = match.group(1).strip()
        if not re.search(r"[A-Za-z]{4,}", rest):
            continue
        if re.match(r"(?i)^[\d\s.,+-]*(?:inches|centimeters)", rest):
            continue
        start = match.start()
        return text[start : start + 1600]
    return text[:800]


def hand_check(
    items: list[dict[str, Any]],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    selected = [item for item in items if item.get("responseType") == "selected"]
    rng = random.Random(HAND_CHECK_SEED)
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
            judgment = "agree"
        elif stem_hits == 0 and not key_in_window:
            judgment = "disagree"
        else:
            judgment = "uncertain"
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
                "judgment": judgment,
                "windowPreview": re.sub(r"\s+", " ", window)[:280],
            }
        )
    existing_path = OUT_DIR / "parse-hand-check.json"
    human_by_id: dict[str, dict[str, Any]] = {}
    existing_meta: dict[str, Any] = {}
    if existing_path.is_file():
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
        existing_meta = {key: existing[key] for key in ("humanReview", "stopRule") if key in existing}
        for prior in existing.get("items") or []:
            if prior.get("stemJudgment"):
                human_by_id[str(prior["id"])] = prior
    for row in rows:
        prior = human_by_id.get(str(row["id"]))
        if not prior:
            continue
        row["autoJudgment"] = row["judgment"]
        for field in ("judgment", "stemJudgment", "optionsJudgment", "keyJudgment", "notes"):
            if field in prior:
                row[field] = prior[field]
    counts = {
        "nSampled": len(rows),
        "nAgree": sum(1 for row in rows if row["judgment"] == "agree"),
        "nDisagree": sum(1 for row in rows if row["judgment"] == "disagree"),
        "nUncertain": sum(1 for row in rows if row["judgment"] == "uncertain"),
        "nDisagreeStem": sum(1 for row in rows if row.get("stemJudgment") == "disagree"),
        "nDisagreeOptions": sum(1 for row in rows if row.get("optionsJudgment") == "disagree"),
        "nDisagreeKey": sum(1 for row in rows if row.get("keyJudgment") == "disagree"),
    }
    n_key_disagree = int(counts["nDisagreeKey"])
    payload = {
        "seed": HAND_CHECK_SEED,
        "nRequested": HAND_CHECK_N,
        "counts": counts,
        "stopScoring": n_key_disagree >= 3,
        "stopRule": existing_meta.get(
            "stopRule",
            "Stop scoring only if 3 or more items disagree on the key / item-number alignment.",
        ),
        "items": rows,
    }
    if existing_meta.get("humanReview"):
        payload["humanReview"] = existing_meta["humanReview"]
    return payload


def s3_row(item: dict[str, Any], *, filtered: bool) -> dict[str, Any] | None:
    target = filtered_item(item) if filtered else item
    result = apply_s3(target, max_depth=2, include_geometry_extras=True, tie="lower-central")
    if not result.fired or result.answer is None:
        return None
    depths = result.extra.get("depths") or {}
    min_depth = result.extra.get("minDepth")
    n_at_min = sum(1 for depth in depths.values() if depth == min_depth)
    decided = "depth" if n_at_min == 1 else "tie-break"
    parsed = parsed_numeric_options(target)
    all_pairs = [(key, value) for key, value, _text in parsed]
    lower_all = None
    if len(all_pairs) >= 1:
        from strategy_channels import lower_central_key

        lower_all = lower_central_key(all_pairs)
    return {
        "id": item["id"],
        "formId": item.get("replicationFormId"),
        "year": item.get("year"),
        "grade": item.get("claim"),
        "key": item.get("key"),
        "pick": result.answer,
        "correct": answers_match(str(item.get("key")), str(result.answer)),
        "chance": result.chance if result.chance is not None else chance_of(item),
        "nInClosure": result.extra.get("nHit"),
        "minDepth": min_depth,
        "nAtMinDepth": n_at_min,
        "decidedBy": decided,
        "uniqueDepth1": bool(result.extra.get("uniqueDepth1")),
        "lowerCentralAllOptions": lower_all,
        "filtered": filtered,
    }


def score_s3_cell(items: list[dict[str, Any]], *, filtered: bool, cell: str) -> dict[str, Any]:
    fired = []
    for item in items:
        row = s3_row(item, filtered=filtered)
        if row is not None:
            fired.append(row)
    chance_values = [float(row["chance"]) for row in fired if row["chance"]]
    summary = summarize_rule("s3-closure" + ("-filtered" if filtered else "-unfiltered"), cell, fired, chance_values=chance_values)
    n_depth = [row for row in fired if row["decidedBy"] == "depth"]
    n_tie = [row for row in fired if row["decidedBy"] == "tie-break"]
    unique_depth1 = [row for row in fired if row["uniqueDepth1"]]
    by_year: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in fired:
        by_year[str(row.get("year"))].append(row)
    administrations = []
    for year, rows in sorted(by_year.items()):
        hits = sum(1 for row in rows if row["correct"])
        administrations.append(
            {
                "administration": f"staar:{year}",
                "n": len(rows),
                "nCorrect": hits,
                "rate": hits / len(rows) if rows else 0.0,
            }
        )
    mean_closure = (
        sum(int(row["nInClosure"] or 0) for row in fired) / len(fired) if fired else 0.0
    )
    summary["tieBreakDecomposition"] = {
        "nDecidedByDepth": len(n_depth),
        "nHitsDecidedByDepth": sum(1 for row in n_depth if row["correct"]),
        "rateAmongDepthDecided": (
            sum(1 for row in n_depth if row["correct"]) / len(n_depth) if n_depth else None
        ),
        "nDecidedByTieBreak": len(n_tie),
        "nHitsDecidedByTieBreak": sum(1 for row in n_tie if row["correct"]),
        "rateAmongTieBreakDecided": (
            sum(1 for row in n_tie if row["correct"]) / len(n_tie) if n_tie else None
        ),
    }
    summary["closureDensity"] = {
        "meanOptionsInClosurePerFiredItem": mean_closure,
        "nFiredUniqueDepth1": len(unique_depth1),
        "nFiredUniqueDepth1IsKey": sum(1 for row in unique_depth1 if row["correct"]),
        "uniqueDepth1IsKeyRateAmongThoseItems": (
            sum(1 for row in unique_depth1 if row["correct"]) / len(unique_depth1)
            if unique_depth1
            else None
        ),
    }
    summary["perAdministration"] = administrations
    summary["items"] = fired
    return summary


def score_simple(
    name: str,
    cell: str,
    items: list[dict[str, Any]],
    apply_fn,
) -> dict[str, Any]:
    fired: list[dict[str, Any]] = []
    chance_values: list[float] = []
    for item in items:
        if item.get("responseType") != "selected":
            continue
        pick, did_fire = apply_fn(item)
        if not did_fire or pick is None:
            continue
        chance = chance_of(item)
        if chance is None:
            continue
        fired.append(
            {
                "id": item["id"],
                "pick": pick,
                "key": item.get("key"),
                "correct": answers_match(str(item.get("key")), str(pick)),
            }
        )
        chance_values.append(chance)
    summary = summarize_rule(name, cell, fired, chance_values=chance_values)
    return summary


def discovery_g5_selected() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with ITEMS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            if (
                item.get("corpus") == "staar"
                and item.get("authority") == "teks"
                and item.get("claim") == "g5"
                and item.get("responseType") == "selected"
            ):
                rows.append(item)
    return rows


def s3_verdict(summary: dict[str, Any]) -> str:
    n = int(summary["nFired"])
    clears = bool(summary["clearsBar"])
    if n < POWER_MIN_N:
        return "underpowered"
    if clears:
        return "replicated"
    return "did_not_replicate"


def write_readme(payload: dict[str, Any]) -> None:
    """Version-1 README writer. Not used by version-2 scoring."""
    return


def main() -> None:
    inventory = load_inventory()
    sha_text = (OUT_DIR / "preregistration.md.sha256").read_text(encoding="utf-8")
    sha_fields = {}
    for line in sha_text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            sha_fields[key] = value

    items, form_reports = parse_forms(inventory)
    dump_jsonl(OUT_DIR / "items.jsonl", items)
    selected = [item for item in items if item.get("responseType") == "selected"]
    g5 = [item for item in selected if item.get("claim") == "g5"]
    hand = hand_check(items, inventory)
    dump_json(OUT_DIR / "parse-hand-check.json", hand)

    parser_changes = {
        "summary": (
            "Added parse_keys_from_pdf (word-row clustering, y-gap 4) in parse_staar_bulk.py. "
            "Unchanged KEY_FLAT concatenates process TEKS into the answer on 2013-2016 keys, "
            "and get_text drops some 2016 item numbers. parse_items skips ruler/numeric-only "
            "item starts, drops ---PAGE lines, and cuts stem/choice text at page markers. "
            "Last-choice leakage remains when extract_lettered_choices continues after a skipped "
            "Mathematics/Page footer; not retuned after seeing rates."
        ),
        "functionsAdded": ["parse_keys_from_pdf"],
        "functionsUnchanged": ["parse_keys", "KEY_FLAT"],
        "parseItemsChanges": (
            "looks_like_item_start rejects ruler/numeric-only lines; ---PAGE lines are not "
            "appended; choice/stem text is cut at page markers. extract_lettered_choices still "
            "appends post-footer lines to the last option."
        ),
    }

    if hand["stopScoring"]:
        payload = {
            "writtenAt": utc_now(),
            "status": "stopped_hand_check",
            "parserChanges": parser_changes,
            "formReports": form_reports,
            "handCheck": hand,
        }
        dump_json(OUT_DIR / "results.json", payload)
        print("stopped after hand-check disagreements")
        return

    s3_filtered = score_s3_cell(g5, filtered=True, cell="teks/g5")
    s3_unfiltered = score_s3_cell(g5, filtered=False, cell="teks/g5")
    verdict = s3_verdict(s3_filtered)

    discovery_items = discovery_g5_selected()
    discovery_unfiltered = score_s3_cell(discovery_items, filtered=False, cell="teks/g5-discovery")
    pooled_flags = [
        1 if row["correct"] else 0 for row in discovery_unfiltered["items"]
    ] + [1 if row["correct"] else 0 for row in s3_unfiltered["items"]]
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
        "note": "Descriptive. Not the replication verdict. Discovery side is recomputed unfiltered S3 on frozen census g5.",
    }

    secondary: list[dict[str, Any]] = []
    secondary.append(score_simple("unit-rate", "teks/g5", g5, apply_unit_rate))
    alg1 = [item for item in selected if item.get("claim") == "alg1"]
    secondary.append(score_simple("option-repeating-stem-numbers", "teks/alg1", alg1, apply_stem_repeat))
    for grade in PRIORITY_GRADES:
        claim = f"g{grade}" if grade != "alg1" else "alg1"
        cell_items = [item for item in selected if item.get("claim") == claim]
        secondary.append(
            score_simple("lower-central-negative-control", f"teks/{claim}", cell_items, apply_lower_central)
        )

    cut = [
        "Census English 2019/2021/2022 not re-parsed.",
        "Spanish forms excluded.",
        "2015 tests have no key PDF.",
        "2023-2026 keys have no matching test PDF.",
        "2017/2018/2020 missing on disk.",
        "2014-6 and 2013-8 tests are mostly image items; text-layer parse yield is near zero and is not OCR'd.",
        "No CPU OCR. No neural model this run.",
    ]

    payload = {
        "writtenAt": utc_now(),
        "preregistration": {
            "path": "exports/replication-staar/preregistration.md",
            "sha256": sha_fields.get("sha256"),
            "utc": sha_fields.get("utc"),
            "powerMinimumN": POWER_MIN_N,
            "bootstrap": {
                "method": "random.Random.randrange",
                "nBoot": N_BOOT,
                "seed": BOOT_SEED,
            },
        },
        "parserChanges": parser_changes,
        "inventoryCounts": inventory["counts"],
        "parse": {
            "nItems": len(items),
            "nSelected": len(selected),
            "nFourNumeric": sum(1 for item in selected if n_parseable_numeric_options(item) == 4),
            "formReports": form_reports,
            "handCheck": {
                "seed": hand["seed"],
                "counts": hand["counts"],
                "stopScoring": hand["stopScoring"],
                "stopRule": hand.get("stopRule"),
                "humanReview": hand.get("humanReview"),
            },
        },
        "nGrade5Selected": len(g5),
        "primary": {k: v for k, v in s3_filtered.items() if k != "items"},
        "s3UnfilteredGrade5": {k: v for k, v in s3_unfiltered.items() if k != "items"},
        "verdict": verdict,
        "paperMaySay": {
            "replicated": "Filtered S3 grade 5 n>=46 and lower CI > 0.25; one-sided wording only.",
            "did_not_replicate": "n>=46 and lower CI not above 0.25; do not claim replication of g5 closure.",
            "underpowered": "n_fired below 46; do not treat this run as a replication of g5 closure.",
            "applied": verdict,
            "appliedText": (
                f"Underpowered: filtered S3 grade 5 fired n={s3_filtered['nFired']}, "
                f"below the registered minimum of {POWER_MIN_N}. The paper may not treat "
                "this run as a replication of the g5 closure result. Pooled "
                "discovery+replication is descriptive only. unit-rate and stem-repeat "
                "did not clear. Do not advertise g4 lower-central as a new witness."
            ),
        },
        "pooledDiscoveryAndReplication": pooled,
        "discoveryRecomputedUnfiltered": {
            "nFired": discovery_unfiltered["nFired"],
            "nHits": discovery_unfiltered["nHits"],
            "rate": discovery_unfiltered["rate"],
            "ci95": discovery_unfiltered["ci95"],
            "frozenRegistered": {"nFired": 40, "nHits": 21, "rate": 0.525},
        },
        "secondary": secondary,
        "cut": cut,
        "primaryItemIds": [row["id"] for row in s3_filtered["items"]],
        "negativeControlNote": (
            "lower-central on teks/g4 clearing the witness bar is a negative-control "
            "failure on that cell. Other STAAR grades stayed at chance."
        ),
    }
    payload["primary"]["underpoweredVsPowerMinimumN"] = s3_filtered["nFired"] < POWER_MIN_N
    payload["primary"]["powerMinimumN"] = POWER_MIN_N
    payload["s3UnfilteredGrade5"]["underpoweredVsPowerMinimumN"] = (
        s3_unfiltered["nFired"] < POWER_MIN_N
    )
    payload["s3UnfilteredGrade5"]["powerMinimumN"] = POWER_MIN_N
    dump_json(OUT_DIR / "results.json", payload)
    write_readme(payload)
    print("verdict", verdict, "n", s3_filtered["nFired"], "hits", s3_filtered["nHits"], "rate", s3_filtered["rate"])
    print("wrote", OUT_DIR / "results.json")


if __name__ == "__main__":
    main()
