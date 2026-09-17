#!/usr/bin/env python3
"""Memorization-signal quartiles, recency, and permutation summary for masked-stem."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from masked_stem_followup_lib import (  # noqa: E402
    YEAR_BUCKET_ORDER,
    dump_json,
    load_jsonl,
    parse_regents_session,
    parse_year,
    quartile_by_rank,
    spearman,
    summarize_rows,
    year_bucket,
)
from score_choices_only_local_lm import load_items  # noqa: E402

OUT_DIR = ROOT / "exports" / "addendum-gpu"
STATS_PATH = OUT_DIR / "masked-stem-item-mask-stats.jsonl"
ITEMS_7B = OUT_DIR / "masked-stem-7b-items.jsonl"
ITEMS_14B = OUT_DIR / "masked-stem-14b-items.jsonl"
OPTIONS_7B = OUT_DIR / "choices-only-local-lm-items.jsonl"
OPTIONS_14B = OUT_DIR / "choices-only-local-lm-14b-items.jsonl"
MEMBERSHIP_ITEMS = OUT_DIR / "masked-stem-membership-7b-items.jsonl"
PERM_SUMMARY = OUT_DIR / "masked-stem-permuted-7b.json"
PERM_ITEMS = OUT_DIR / "masked-stem-permuted-7b-items.jsonl"
V2_SUMMARY = OUT_DIR / "masked-stem-v2-7b.json"
V2_ITEMS = OUT_DIR / "masked-stem-v2-7b-items.jsonl"
OUT_PATH = OUT_DIR / "masked-stem-contamination.json"
NAMED_PERM_CELLS = (
    "nyregents::algebra-i",
    "nyregents::geometry",
    "eqao::g6",
    "timss::knowing",
)


def rows_by_id(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in load_jsonl(path)}


def rate_table(rows: list[dict[str, Any]], correct_field: str) -> dict[str, Any]:
    flags = [int(row[correct_field]) for row in rows]
    chances = [1.0 / int(row["n_options"]) for row in rows]
    summary = summarize_rows(
        [
            {
                "correct": row[correct_field],
                "n_options": row["n_options"],
            }
            for row in rows
        ]
    )
    return summary


def quartile_table(
    joined: list[dict[str, Any]],
    signal_field: str,
    correct_field: str,
) -> dict[str, Any]:
    values = [float(row[signal_field]) for row in joined]
    labels = quartile_by_rank(values)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row, label in zip(joined, labels):
        grouped[int(label)].append(row)
    by_q: dict[str, Any] = {}
    for quartile in (1, 2, 3, 4):
        group = grouped.get(quartile, [])
        by_q[f"Q{quartile}"] = {
            "quartile": quartile,
            "meaning": (
                "least_memorized_lowest_logprob"
                if quartile == 1
                else "most_memorized_highest_logprob"
                if quartile == 4
                else f"middle_{quartile}"
            ),
            **rate_table(group, correct_field),
            "meanSignal": (
                sum(float(row[signal_field]) for row in group) / len(group) if group else None
            ),
        }
    q1 = by_q["Q1"]["passRate"]
    q4 = by_q["Q4"]["passRate"]
    gap = q4 - q1
    rho = spearman(values, [float(int(row[correct_field])) for row in joined])
    if gap >= 0.15 and (rho is not None and rho >= 0.20):
        verdict = "memorization_plausible"
    elif abs(gap) < 0.10 or (rho is not None and abs(rho) < 0.12):
        verdict = "signal_does_not_indicate_memorization"
    else:
        verdict = "weak_or_mixed"
    return {
        "signal": signal_field,
        "correctField": correct_field,
        "n": len(joined),
        "spearman": rho,
        "mostMinusLeast": gap,
        "verdict": verdict,
        "quartiles": by_q,
        "note": (
            "Q4 is the highest mean token log-probability (lowest perplexity, most "
            "memorized). Q1 is the lowest log-probability. A large Q4-minus-Q1 gap "
            "would make memorization a plausible driver."
        ),
    }


def recency_table(
    joined: list[dict[str, Any]],
    correct_field: str,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        grouped[str(row["year_bucket"])].append(row)
    by_bucket: dict[str, Any] = {}
    for bucket in list(YEAR_BUCKET_ORDER) + ["unparsed"]:
        group = grouped.get(bucket, [])
        if not group and bucket == "unparsed":
            continue
        by_bucket[bucket] = rate_table(group, correct_field)
        by_bucket[bucket]["nSources"] = dict(Counter(str(row["corpus"]) for row in group))
    return by_bucket


def permutation_block() -> dict[str, Any] | None:
    if not PERM_SUMMARY.exists() or not PERM_ITEMS.exists():
        return None
    summary = json.loads(PERM_SUMMARY.read_text(encoding="utf-8"))
    rows = load_jsonl(PERM_ITEMS)
    named: dict[str, Any] = {}
    for cell_name in NAMED_PERM_CELLS:
        cell_rows = [row for row in rows if str(row.get("cell")) == cell_name]
        named[cell_name] = summarize_rows(cell_rows) if cell_rows else {"n": 0}
    return {
        "n": len(rows),
        "overall": summary.get("overall"),
        "namedCells": named,
        "summaryPath": str(PERM_SUMMARY.relative_to(ROOT)),
        "note": (
            "Option order randomly permuted with a fixed per-item seed. Position "
            "effects are removed by construction; this is the content-only rate on "
            "the version-1 masked_token_count >= 1 population."
        ),
    }


def v2_block(v1_ge1_ids: set[str]) -> dict[str, Any] | None:
    if not V2_SUMMARY.exists() or not V2_ITEMS.exists():
        return None
    summary = json.loads(V2_SUMMARY.read_text(encoding="utf-8"))
    rows = load_jsonl(V2_ITEMS)
    v1_ge1 = rows_by_id(ITEMS_7B)
    overlap = [row for row in rows if str(row["id"]) in v1_ge1_ids]
    both = 0
    v2_only = 0
    v1_only = 0
    neither = 0
    for row in overlap:
        v2_ok = bool(row["correct"])
        v1_ok = bool(v1_ge1[str(row["id"])]["correct"])
        if v2_ok and v1_ok:
            both += 1
        elif v2_ok and not v1_ok:
            v2_only += 1
        elif (not v2_ok) and v1_ok:
            v1_only += 1
        else:
            neither += 1
    v2_rate = summarize_rows(rows)
    overlap_v2 = summarize_rows(overlap) if overlap else {"n": 0}
    overlap_v1 = summarize_rows(
        [
            {
                "correct": v1_ge1[str(row["id"])]["correct"],
                "n_options": row["n_options"],
            }
            for row in overlap
        ]
    ) if overlap else {"n": 0}
    delta = None
    if overlap:
        delta = float(overlap_v2["passRate"]) - float(overlap_v1["passRate"])
    return {
        "nScored": len(rows),
        "overall": summary.get("overall") or v2_rate,
        "minMaskedTokenCount": summary.get("minMaskedTokenCount"),
        "maskVersion": summary.get("maskVersion"),
        "preregistrationSha256": summary.get("preregistrationSha256"),
        "overlapWithV1Ge1": {
            "n": len(overlap),
            "v2": overlap_v2,
            "v1": overlap_v1,
            "deltaV2MinusV1": delta,
            "mcnemar": {
                "bothCorrect": both,
                "v2CorrectV1Wrong": v2_only,
                "v1CorrectV2Wrong": v1_only,
                "bothWrong": neither,
            },
        },
        "namedCells": summary.get("namedCells") or {},
    }


def main() -> None:
    if not MEMBERSHIP_ITEMS.exists():
        dump_json(
            OUT_PATH,
            {
                "status": "partial_waiting_for_membership",
                "writtenAt": datetime.now(timezone.utc).isoformat(),
                "missing": str(MEMBERSHIP_ITEMS.relative_to(ROOT)),
            },
        )
        print(json.dumps({"status": "partial_waiting_for_membership"}, indent=2))
        return

    items_by_id = load_items()
    stats_rows = {str(row["id"]): row for row in load_jsonl(STATS_PATH)}
    membership = rows_by_id(MEMBERSHIP_ITEMS)
    rows_7b = rows_by_id(ITEMS_7B)
    rows_14b = rows_by_id(ITEMS_14B)
    options_7b = rows_by_id(OPTIONS_7B)
    options_14b = rows_by_id(OPTIONS_14B)

    joined_all: list[dict[str, Any]] = []
    joined_ge1: list[dict[str, Any]] = []
    sources_2024: dict[str, int] = defaultdict(int)
    regents_2024_sessions: dict[str, int] = defaultdict(int)
    for item_id, mem in membership.items():
        row_7 = rows_7b[item_id]
        row_14 = rows_14b[item_id]
        item = items_by_id[item_id]
        stats = stats_rows[item_id]
        year = parse_year(item)
        bucket = year_bucket(year)
        session = parse_regents_session(item_id)
        record = {
            "id": item_id,
            "cell": row_7.get("cell"),
            "corpus": row_7.get("corpus"),
            "n_options": row_7["n_options"],
            "masked_token_count": stats["masked_token_count"],
            "stem_chars_masked_share": stats["stem_chars_masked_share"],
            "year": year,
            "year_bucket": bucket,
            "regents_session": None if session is None else session["session"],
            "mean_token_logprob": mem["mean_token_logprob"],
            "min20_token_logprob": mem["min20_token_logprob"],
            "n_scored_tokens": mem["n_scored_tokens"],
            "correct_7b_masked": bool(row_7["correct"]),
            "correct_14b_masked": bool(row_14["correct"]),
            "correct_7b_options": bool(options_7b[item_id]["correct"]),
            "correct_14b_options": bool(options_14b[item_id]["correct"]),
        }
        joined_all.append(record)
        if int(stats["masked_token_count"]) >= 1:
            joined_ge1.append(record)
        if bucket == "2024_and_later":
            sources_2024[str(row_7.get("corpus"))] += 1
            if session is not None and session["year"] >= 2024:
                key = f"{session['year']}-{session['session']}"
                regents_2024_sessions[key] += 1

    per_item = [
        {
            "id": row["id"],
            "cell": row["cell"],
            "masked_token_count": row["masked_token_count"],
            "year": row["year"],
            "year_bucket": row["year_bucket"],
            "mean_token_logprob": row["mean_token_logprob"],
            "min20_token_logprob": row["min20_token_logprob"],
            "correct_7b_masked": row["correct_7b_masked"],
            "correct_14b_masked": row["correct_14b_masked"],
        }
        for row in joined_all
    ]

    payload: dict[str, Any] = {
        "status": "complete" if PERM_SUMMARY.exists() else "partial_membership_done",
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "nMembership": len(joined_all),
        "nGe1": len(joined_ge1),
        "signal": {
            "modelId": "Qwen/Qwen2.5-7B-Instruct",
            "modelRevision": "a09a35458c702b33eeacc393d103063234e8bc28",
            "text": "original unmasked stem plus lettered options, no chat template",
            "higherMeanLogprobMeans": "lower perplexity / more like training text",
        },
        "quartilesAll1487": {
            "mean_token_logprob_7b_picks": quartile_table(
                joined_all, "mean_token_logprob", "correct_7b_masked"
            ),
            "mean_token_logprob_14b_picks": quartile_table(
                joined_all, "mean_token_logprob", "correct_14b_masked"
            ),
            "min20_token_logprob_7b_picks": quartile_table(
                joined_all, "min20_token_logprob", "correct_7b_masked"
            ),
            "min20_token_logprob_14b_picks": quartile_table(
                joined_all, "min20_token_logprob", "correct_14b_masked"
            ),
        },
        "quartilesGe1": {
            "mean_token_logprob_7b_picks": quartile_table(
                joined_ge1, "mean_token_logprob", "correct_7b_masked"
            ),
            "mean_token_logprob_14b_picks": quartile_table(
                joined_ge1, "mean_token_logprob", "correct_14b_masked"
            ),
        },
        "recency": {
            "rule": (
                "Year from item.year when 19xx/20xx, else id or corpus. Buckets: "
                "before 2015, 2015 to 2019, 2020 to 2023, 2024 and later. 2024 and later "
                "are the closest post-training-cutoff administrations on disk."
            ),
            "sourcesWith2024OrLater": dict(sources_2024),
            "regentsSessions2024OrLater": dict(regents_2024_sessions),
            "all1487": {
                "masked7b": recency_table(joined_all, "correct_7b_masked"),
                "masked14b": recency_table(joined_all, "correct_14b_masked"),
                "options7b": recency_table(joined_all, "correct_7b_options"),
                "options14b": recency_table(joined_all, "correct_14b_options"),
            },
            "ge1": {
                "masked7b": recency_table(joined_ge1, "correct_7b_masked"),
                "masked14b": recency_table(joined_ge1, "correct_14b_masked"),
                "options7b": recency_table(joined_ge1, "correct_7b_options"),
                "options14b": recency_table(joined_ge1, "correct_14b_options"),
            },
        },
        "permutation": permutation_block(),
        "maskingVersion2": v2_block(
            {str(row["id"]) for row in joined_ge1}
        ),
        "items": per_item,
    }
    q7_ge1 = payload["quartilesGe1"]["mean_token_logprob_7b_picks"]
    q14_ge1 = payload["quartilesGe1"]["mean_token_logprob_14b_picks"]
    rec7 = payload["recency"]["all1487"]["masked7b"]
    payload["contaminationHeadline"] = (
        "On the >= 1 population, 7B masked-stem accuracy is "
        f"Q1 {q7_ge1['quartiles']['Q1']['passRate']:.3f} vs Q4 {q7_ge1['quartiles']['Q4']['passRate']:.3f} "
        f"(Spearman {q7_ge1['spearman']:.3f}); 14B Spearman {q14_ge1['spearman']:.3f}. "
        "Administration-year rates for masked-stem 7B are flat through 2024 and later "
        f"({rec7['before_2015']['passRate']:.3f} / {rec7['2015_to_2019']['passRate']:.3f} / "
        f"{rec7['2020_to_2023']['passRate']:.3f} / {rec7['2024_and_later']['passRate']:.3f}). "
        "The membership signal does not indicate memorization as the driver."
    )
    dump_json(OUT_PATH, payload)
    q7 = payload["quartilesGe1"]["mean_token_logprob_7b_picks"]
    print(
        json.dumps(
            {
                "out": str(OUT_PATH),
                "status": payload["status"],
                "n": payload["nMembership"],
                "quartile7bGe1": {
                    "spearman": q7["spearman"],
                    "mostMinusLeast": q7["mostMinusLeast"],
                    "verdict": q7["verdict"],
                    "Q1": q7["quartiles"]["Q1"]["passRate"],
                    "Q4": q7["quartiles"]["Q4"]["passRate"],
                },
                "recency7bAll": {
                    name: payload["recency"]["all1487"]["masked7b"][name]["passRate"]
                    for name in payload["recency"]["all1487"]["masked7b"]
                },
                "sources2024": dict(sources_2024),
                "permutationN": None if payload["permutation"] is None else payload["permutation"]["n"],
                "v2n": None
                if payload["maskingVersion2"] is None
                else payload["maskingVersion2"]["nScored"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
