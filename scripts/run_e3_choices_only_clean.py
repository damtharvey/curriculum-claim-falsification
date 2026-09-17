#!/usr/bin/env python3
"""E3: mechanical clean-option filter and rescore of existing choices-only predictions."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from addendum_lib import (
    ADDENDUM_DIR,
    COUNTRY_FRAGMENT_RE,
    PAGE_FOOTER_RE,
    STAAR_FOOTER_RE,
    dump_json,
    load_items,
)
from score_choices_only import bootstrap_ci

ROOT = Path(__file__).resolve().parents[1]
SCORED_PATH = ROOT / "exports" / "choices-only" / "scored.jsonl"
ITEMS_BY_ID: dict[str, dict[str, Any]] = {}

LENGTH_THRESHOLD = 120
ITEM_CODE_RE = re.compile(r"\b\d{5}_\d\b")
NEXT_ITEM_RE = re.compile(r"(?i)\b(which (ordered pair|statement|number)|there are a total of)\b")
REGENTS_COURSE_FOOTER_RE = re.compile(
    r"(?i)(geometry|algebra i{0,2}|algebra 2)\s+[–—'′-]\s+(jan|june|aug)"
)


def option_contamination(text: str) -> list[str]:
    reasons: list[str] = []
    if len(text) > LENGTH_THRESHOLD:
        reasons.append(f"length>{LENGTH_THRESHOLD}")
    if COUNTRY_FRAGMENT_RE.search(text):
        reasons.append("country-or-jurisdiction-fragment")
    if PAGE_FOOTER_RE.search(text) or REGENTS_COURSE_FOOTER_RE.search(text):
        reasons.append("exam-footer")
    if STAAR_FOOTER_RE.search(text) or ITEM_CODE_RE.search(text):
        reasons.append("item-code-or-staar-id")
    if NEXT_ITEM_RE.search(text) and len(text) > 80:
        reasons.append("next-item-bleed")
    if re.search(r"\b\d{2,3}\s*$", text) and re.search(r"(?i)(cm|m|°)", text) and COUNTRY_FRAGMENT_RE.search(text):
        reasons.append("timss-percent-correct-suffix")
    return reasons


def item_is_clean(item: dict[str, Any]) -> tuple[bool, dict[str, list[str]]]:
    choices = item.get("choices") or {}
    per_option: dict[str, list[str]] = {}
    dirty = False
    for key, text in choices.items():
        reasons = option_contamination(str(text))
        if reasons:
            dirty = True
            per_option[str(key)] = reasons
    return (not dirty, per_option)


def summarize(flags: list[int], chance: float) -> dict[str, Any]:
    n = len(flags)
    rate = sum(flags) / n if n else 0.0
    ci = bootstrap_ci(flags, 1000, 21 + n) if n else (0.0, 0.0)
    return {
        "n": n,
        "passRate": rate,
        "ci95": [ci[0], ci[1]],
        "chance": chance,
        "ciExcludesChance": n >= 10 and ci[0] > chance,
        "witnessBarEligible": n >= 10 and ci[0] > chance,
        "exploratory": True,
    }


def main() -> None:
    items = load_items()
    global ITEMS_BY_ID
    ITEMS_BY_ID = {str(item["id"]): item for item in items}
    selected = [item for item in items if item.get("responseType") == "selected"]
    keep_ids: list[str] = []
    drop_ids: list[str] = []
    drop_examples: list[dict[str, Any]] = []
    reason_counts: dict[str, int] = defaultdict(int)
    by_corpus_counts = defaultdict(lambda: {"n": 0, "kept": 0})
    for item in selected:
        corpus = str(item.get("corpus", "unknown"))
        by_corpus_counts[corpus]["n"] += 1
        clean, per_option = item_is_clean(item)
        if clean:
            keep_ids.append(str(item["id"]))
            by_corpus_counts[corpus]["kept"] += 1
        else:
            drop_ids.append(str(item["id"]))
            for reasons in per_option.values():
                for reason in reasons:
                    reason_counts[reason] += 1
            if len(drop_examples) < 12:
                drop_examples.append(
                    {
                        "itemId": item["id"],
                        "corpus": corpus,
                        "perOptionReasons": per_option,
                    }
                )

    scored_rows: list[dict[str, Any]] = []
    if SCORED_PATH.exists():
        for line in SCORED_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                scored_rows.append(json.loads(line))
    keep_set = set(keep_ids)
    clean_scored = [row for row in scored_rows if row.get("itemId") in keep_set]
    by_corpus: dict[str, list[int]] = defaultdict(list)
    by_claim: dict[str, list[int]] = defaultdict(list)
    flags: list[int] = []
    for row in clean_scored:
        flag = int(bool(row.get("correct")))
        flags.append(flag)
        by_corpus[str(row.get("corpus") or "unknown")].append(flag)
        item = ITEMS_BY_ID.get(str(row["itemId"]))
        if item:
            by_claim[f"{item['authority']}::{item['claim']}"].append(flag)

    filter_payload = {
        "experiment": "E3-filter",
        "question": "Which selected-response items have option strings free of known transcription bleed?",
        "rules": {
            "lengthGreaterThan": LENGTH_THRESHOLD,
            "countryOrJurisdictionFragment": COUNTRY_FRAGMENT_RE.pattern,
            "examFooter": PAGE_FOOTER_RE.pattern,
            "staarItemCode": STAAR_FOOTER_RE.pattern,
            "nextItemBleed": NEXT_ITEM_RE.pattern,
            "regentsCourseFooter": REGENTS_COURSE_FOOTER_RE.pattern,
        },
        "nSelected": len(selected),
        "nKept": len(keep_ids),
        "nDropped": len(drop_ids),
        "keepRate": len(keep_ids) / len(selected) if selected else 0.0,
        "reasonCounts": dict(reason_counts),
        "byCorpus": {k: dict(v) for k, v in sorted(by_corpus_counts.items())},
        "dropExamples": drop_examples,
        "keptItemIdsPath": "exports/addendum/choices-only-clean-item-ids.json",
        "cite": "exports/addendum/choices-only-clean-filter.json",
    }
    dump_json(ADDENDUM_DIR / "choices-only-clean-filter.json", filter_payload)
    dump_json(ADDENDUM_DIR / "choices-only-clean-item-ids.json", keep_ids)

    score_payload = {
        "experiment": "E3-score",
        "label": "exploratory",
        "protocol": (
            "Reuse existing composer-2.5-fast choices-only predictions from "
            "exports/choices-only/scored.jsonl on items that pass the mechanical "
            "clean-option filter. No new LM calls. Predictions were collected with "
            "opaque ids, shuffled options, and a transcript tool_use audit."
        ),
        "nCleanSelected": len(keep_ids),
        "nCleanAlreadyScored": len(clean_scored),
        "nExistingScored": len(scored_rows),
        "overall": summarize(flags, 0.25),
        "perCorpus": {corpus: summarize(vals, 0.25) for corpus, vals in sorted(by_corpus.items())},
        "perClaim": {claim: summarize(vals, 0.25) for claim, vals in sorted(by_claim.items())},
        "cite": "exports/addendum/choices-only-clean-score.json",
        "claimStatus": "not claimed; option-clean subset of a contaminated-channel run",
    }
    dump_json(ADDENDUM_DIR / "choices-only-clean-score.json", score_payload)
    print("filter kept", len(keep_ids), "/", len(selected))
    print("scored clean", len(clean_scored), "rate", score_payload["overall"])


if __name__ == "__main__":
    main()
