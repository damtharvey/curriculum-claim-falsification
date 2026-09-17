#!/usr/bin/env python3
"""Summarize scorer-capability runs; safe to call on partial artifacts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
OUT_DIR = ROOT / "exports" / "addendum-gpu"
README_PATH = OUT_DIR / "README.md"
TABLE_PATH = OUT_DIR / "scorer-capability-table.json"
STATUS_PATH = OUT_DIR / "scorer-capability-status.json"
STATS_PATH = OUT_DIR / "masked-stem-item-mask-stats.jsonl"
POSITION_PATH = OUT_DIR / "position-and-memorization.json"
SECTION_MARKER = "## Scorer capability (masked-stem vs family, 2026-09-16)"

sys.path.insert(0, str(SCRIPTS))

from analyze_masked_stem_cue_attribution import (  # noqa: E402
    ALGEBRA_I_CELL,
    classify_item_option_type,
    unique_longest_letter,
    numeric_pairs,
)
from masked_stem_followup_lib import (  # noqa: E402
    dump_json,
    enrich_cells,
    load_jsonl,
    paired_increment,
    summarize_rows,
    vs_always_b,
)
from score_choices_only_local_lm import load_items, load_modal_by_cell  # noqa: E402
from strategy_channels import apply_s1, lower_central_key  # noqa: E402

ALGEBRA_II_CELL = "nyregents::algebra-ii"
CHANCE_BAR = 0.250
ALGEBRA_I_MODAL = 0.271
ALGEBRA_II_MODAL = 0.278

SCORERS: dict[str, dict[str, Any]] = {
    "mistral-7b-instruct-v0.3": {
        "modelId": "mistralai/Mistral-7B-Instruct-v0.3",
        "display": "Mistral 7B",
        "maskedStem": OUT_DIR / "masked-stem-mistral-7b-items.jsonl",
        "optionsOnly": OUT_DIR / "options-only-mistral-7b-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-mistral-items.jsonl",
        "maskedSummary": OUT_DIR / "masked-stem-mistral-7b.json",
        "optionsSummary": OUT_DIR / "options-only-mistral-7b.json",
        "withStemSummary": OUT_DIR / "with-stem-algebra-mistral.json",
        "family": "mistral",
    },
    "qwen2.5-7b-instruct": {
        "modelId": "Qwen/Qwen2.5-7B-Instruct",
        "display": "Qwen 7B",
        "maskedStem": OUT_DIR / "masked-stem-7b-items.jsonl",
        "optionsOnly": OUT_DIR / "choices-only-local-lm-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-7b-items.jsonl",
        "maskedSummary": OUT_DIR / "masked-stem-7b.json",
        "optionsSummary": OUT_DIR / "choices-only-local-lm.json",
        "withStemSummary": OUT_DIR / "with-stem-algebra-7b.json",
        "family": "qwen",
    },
    "qwen2.5-14b-instruct": {
        "modelId": "Qwen/Qwen2.5-14B-Instruct",
        "display": "Qwen 14B",
        "maskedStem": OUT_DIR / "masked-stem-14b-items.jsonl",
        "optionsOnly": OUT_DIR / "choices-only-local-lm-14b-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-14b-items.jsonl",
        "maskedSummary": OUT_DIR / "masked-stem-14b.json",
        "optionsSummary": OUT_DIR / "choices-only-local-lm-14b.json",
        "withStemSummary": OUT_DIR / "with-stem-algebra-14b.json",
        "family": "qwen",
    },
    "phi-4": {
        "modelId": "microsoft/phi-4",
        "display": "Phi-4",
        "maskedStem": OUT_DIR / "masked-stem-phi4-items.jsonl",
        "optionsOnly": OUT_DIR / "options-only-phi4-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-phi4-items.jsonl",
        "maskedSummary": OUT_DIR / "masked-stem-phi4.json",
        "optionsSummary": OUT_DIR / "options-only-phi4.json",
        "withStemSummary": OUT_DIR / "with-stem-algebra-phi4.json",
        "family": "phi",
    },
    "gemma-2-9b-it": {
        "modelId": "google/gemma-2-9b-it",
        "display": "Gemma 2 9B",
        "maskedStem": OUT_DIR / "masked-stem-gemma-2-9b-items.jsonl",
        "optionsOnly": OUT_DIR / "options-only-gemma-2-9b-items.jsonl",
        "withStem": OUT_DIR / "with-stem-algebra-gemma-2-9b-items.jsonl",
        "maskedSummary": OUT_DIR / "masked-stem-gemma-2-9b.json",
        "optionsSummary": OUT_DIR / "options-only-gemma-2-9b.json",
        "withStemSummary": OUT_DIR / "with-stem-algebra-gemma-2-9b.json",
        "family": "gemma",
    },
}

OPTION_TYPE_ORDER = (
    "algebraic_expression",
    "text",
    "numeric",
    "mixed",
    "ordered_pair",
)


def load_primary_ids() -> list[str]:
    stats_ids: list[str] = []
    with STATS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if int(row["masked_token_count"]) >= 1:
                stats_ids.append(str(row["id"]))
    if len(stats_ids) != 1215:
        raise RuntimeError(f"expected 1215 primary ids, got {len(stats_ids)}")
    return stats_ids


def filter_primary(rows: list[dict[str, Any]], allowed: set[str]) -> list[dict[str, Any]]:
    return [row for row in rows if str(row["id"]) in allowed]


def revision_from_summary(path: Path) -> str | None:
    if not path.exists():
        return None
    blob = json.loads(path.read_text(encoding="utf-8"))
    revision = blob.get("modelRevision")
    return str(revision) if revision else None


def cell_verdict(stats: dict[str, Any] | None) -> str:
    if not stats:
        return "missing"
    if stats.get("clearsWitnessBarOnPopulation"):
        return "clears both"
    if stats.get("lowerCiAboveChance"):
        return "chance only"
    return "neither"


def rate_block(rows: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not rows:
        return None
    return summarize_rows(rows)


def residual_ids(items_by_id: dict[str, dict[str, Any]], primary_ids: set[str]) -> list[str]:
    algebra_rows: list[dict[str, Any]] = []
    for item_id in sorted(primary_ids):
        item = items_by_id.get(item_id)
        if item is None:
            continue
        cell = f"{item.get('authority')}::{item.get('claim')}"
        if cell != ALGEBRA_I_CELL:
            continue
        choices = item.get("choices") or {}
        key = str(item.get("key", "")).strip().upper()
        pairs = numeric_pairs(item)
        lower_central = lower_central_key(pairs) if pairs else None
        hub = apply_s1(item)
        hub_letter = str(hub.answer).strip().upper() if hub.fired and hub.answer else None
        longest = unique_longest_letter(choices)
        algebra_rows.append(
            {
                "id": item_id,
                "key": key,
                "key_is_lower_central": bool(lower_central and key == lower_central),
                "key_is_hub": bool(hub_letter and key == hub_letter),
                "key_is_longest": bool(longest and key == longest),
            }
        )
    keys = [str(row["key"]) for row in algebra_rows]
    from collections import Counter

    counts = Counter(keys)
    max_count = max(counts.values()) if counts else 0
    modal = min((letter for letter, count in counts.items() if count == max_count), default="")
    residual = [
        row
        for row in algebra_rows
        if (not row["key_is_lower_central"])
        and str(row["key"]) != modal
        and (not row["key_is_hub"])
        and (not row["key_is_longest"])
    ]
    if len(algebra_rows) != 358:
        raise RuntimeError(f"expected 358 Algebra I primary items, got {len(algebra_rows)}")
    if len(residual) != 163:
        raise RuntimeError(f"expected 163 residual Algebra I items, got {len(residual)}")
    return [str(row["id"]) for row in residual]


def option_type_by_id(
    items_by_id: dict[str, dict[str, Any]],
    item_ids: list[str],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item_id in item_ids:
        item = items_by_id[item_id]
        mapping[item_id] = classify_item_option_type(item)
    return mapping


def rows_by_cell(rows: list[dict[str, Any]], cell: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("cell")) == cell]


def summarize_scorer(
    key: str,
    spec: dict[str, Any],
    primary_ids: set[str],
    residual: set[str],
    type_by_id: dict[str, str],
    modal_by_cell: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    masked_path: Path = spec["maskedStem"]
    options_path: Path = spec["optionsOnly"]
    with_stem_path: Path = spec["withStem"]
    masked_rows = (
        filter_primary(load_jsonl(masked_path), primary_ids) if masked_path.exists() else []
    )
    options_rows = (
        filter_primary(load_jsonl(options_path), primary_ids) if options_path.exists() else []
    )
    with_stem_rows = (
        filter_primary(load_jsonl(with_stem_path), primary_ids) if with_stem_path.exists() else []
    )
    revision = revision_from_summary(spec["maskedSummary"]) or revision_from_summary(
        spec["withStemSummary"]
    ) or revision_from_summary(spec["optionsSummary"])
    payload: dict[str, Any] = {
        "scorerKey": key,
        "display": spec["display"],
        "modelId": spec["modelId"],
        "modelRevision": revision,
        "family": spec["family"],
        "complete": {
            "maskedStem": len(masked_rows) == 1215,
            "optionsOnly": len(options_rows) == 1215,
            "withStemAlgebra": len(with_stem_rows) == 606,
        },
        "nMaskedStem": len(masked_rows),
        "nOptionsOnly": len(options_rows),
        "nWithStem": len(with_stem_rows),
    }
    if masked_rows:
        payload["pooledMaskedStem"] = summarize_rows(masked_rows)
        payload["vsAlwaysB"] = vs_always_b(masked_rows)
        enriched = enrich_cells(masked_rows, modal_by_cell)
        algebra_i = enriched["namedCells"].get(ALGEBRA_I_CELL)
        algebra_ii = enriched["namedCells"].get(ALGEBRA_II_CELL)
        payload["algebraI"] = {
            **(algebra_i or {}),
            "verdict": cell_verdict(algebra_i),
            "statedChance": CHANCE_BAR,
            "statedModalLetterBar": ALGEBRA_I_MODAL,
        }
        payload["algebraII"] = {
            **(algebra_ii or {}),
            "verdict": cell_verdict(algebra_ii),
            "statedChance": CHANCE_BAR,
            "statedModalLetterBar": ALGEBRA_II_MODAL,
        }
        if options_rows:
            options_by_id = {str(row["id"]): row for row in options_rows}
            payload["vsOptionsOnly"] = paired_increment(masked_rows, options_by_id)
            payload["algebraI"]["vsOptionsOnly"] = paired_increment(
                rows_by_cell(masked_rows, ALGEBRA_I_CELL),
                options_by_id,
            )
            payload["algebraII"]["vsOptionsOnly"] = paired_increment(
                rows_by_cell(masked_rows, ALGEBRA_II_CELL),
                options_by_id,
            )
        algebra_i_rows = rows_by_cell(masked_rows, ALGEBRA_I_CELL)
        type_groups: dict[str, list[dict[str, Any]]] = {name: [] for name in OPTION_TYPE_ORDER}
        for row in algebra_i_rows:
            option_type = type_by_id.get(str(row["id"]), "text")
            type_groups.setdefault(option_type, []).append(row)
        payload["algebraIOptionTypes"] = {
            name: summarize_rows(group) if group else {"n": 0}
            for name, group in type_groups.items()
        }
        residual_rows = [row for row in algebra_i_rows if str(row["id"]) in residual]
        payload["algebraIResidualNoCatalogCue"] = {
            "nExpected": 163,
            "n": len(residual_rows),
            "stats": summarize_rows(residual_rows) if residual_rows else {"n": 0},
        }
    if options_rows:
        payload["pooledOptionsOnly"] = summarize_rows(options_rows)
        options_enriched = enrich_cells(options_rows, modal_by_cell)
        payload["optionsOnlyAlgebraI"] = options_enriched["namedCells"].get(ALGEBRA_I_CELL)
        payload["optionsOnlyAlgebraII"] = options_enriched["namedCells"].get(ALGEBRA_II_CELL)
    if with_stem_rows:
        with_enriched = enrich_cells(with_stem_rows, modal_by_cell)
        payload["withStemAlgebraI"] = with_enriched["namedCells"].get(ALGEBRA_I_CELL)
        payload["withStemAlgebraII"] = with_enriched["namedCells"].get(ALGEBRA_II_CELL)
        payload["withStemCeiling"] = {
            "algebraI": rate_block(rows_by_cell(with_stem_rows, ALGEBRA_I_CELL)),
            "algebraII": rate_block(rows_by_cell(with_stem_rows, ALGEBRA_II_CELL)),
        }
    return payload


def table_row(block: dict[str, Any]) -> dict[str, Any]:
    algebra_i = block.get("algebraI") or {}
    algebra_ii = block.get("algebraII") or {}
    ceiling = block.get("withStemCeiling") or {}
    ceiling_i = ceiling.get("algebraI") or {}
    ceiling_ii = ceiling.get("algebraII") or {}
    with_stem_i = block.get("withStemAlgebraI")
    with_stem_ii = block.get("withStemAlgebraII")
    return {
        "display": block.get("display"),
        "modelId": block.get("modelId"),
        "modelRevision": block.get("modelRevision"),
        "family": block.get("family"),
        "complete": block.get("complete"),
        "algebraI": {
            "withStemCeiling": ceiling_i.get("passRate"),
            "withStemCi95": ceiling_i.get("ci95"),
            "withStemVerdict": cell_verdict(with_stem_i),
            "maskedStem": algebra_i.get("passRate"),
            "maskedStemCi95": algebra_i.get("ci95"),
            "maskedStemVerdict": algebra_i.get("verdict"),
            "n": algebra_i.get("n"),
        },
        "algebraII": {
            "withStemCeiling": ceiling_ii.get("passRate"),
            "withStemCi95": ceiling_ii.get("ci95"),
            "withStemVerdict": cell_verdict(with_stem_ii),
            "maskedStem": algebra_ii.get("passRate"),
            "maskedStemCi95": algebra_ii.get("ci95"),
            "maskedStemVerdict": algebra_ii.get("verdict"),
            "n": algebra_ii.get("n"),
        },
        "pooledMaskedStem": (block.get("pooledMaskedStem") or {}).get("passRate"),
        "pooledMaskedStemCi95": (block.get("pooledMaskedStem") or {}).get("ci95"),
    }


def reading_sentence(rows: list[dict[str, Any]]) -> str:
    usable = [
        row
        for row in rows
        if row["algebraI"].get("withStemCeiling") is not None
        and row["algebraI"].get("maskedStem") is not None
        and row["algebraI"].get("maskedStemVerdict") not in (None, "n/a", "missing")
    ]
    if not usable:
        return (
            "Need a non-Qwen scorer with both a with-stem ceiling and a masked-stem "
            "rate before saying whether the channel tracks capability."
        )
    weak = [
        row
        for row in usable
        if row["algebraI"].get("withStemVerdict") != "clears both"
    ]
    capable = [
        row
        for row in usable
        if row["algebraI"].get("withStemVerdict") == "clears both"
        and row["algebraI"].get("maskedStemVerdict") == "clears both"
    ]
    capable_non_qwen = [row for row in capable if row.get("family") != "qwen"]
    def brief(row: dict[str, Any]) -> str:
        algebra_i = row["algebraI"]
        return (
            f"{row['display']} ceiling {float(algebra_i['withStemCeiling']):.3f} "
            f"({algebra_i.get('withStemVerdict')}) "
            f"masked-stem {float(algebra_i['maskedStem']):.3f} "
            f"({algebra_i.get('maskedStemVerdict')})"
        )
    if weak and capable_non_qwen:
        return (
            "Masked-stem tracks capability rather than Qwen: "
            + "; ".join(brief(row) for row in weak)
            + "; capable non-Qwen and Qwen scorers clear both ("
            + "; ".join(brief(row) for row in capable)
            + ")."
        )
    if capable_non_qwen and not weak:
        return (
            "A capable non-Qwen scorer clears both on Algebra I, so the channel is "
            "not Qwen-family-specific: "
            + "; ".join(brief(row) for row in usable)
            + "."
        )
    return (
        "Scorer table is incomplete for the capability reading: "
        + "; ".join(brief(row) for row in usable)
        + "."
    )


def fmt_ci(ci: list[float] | None) -> str:
    if not ci:
        return "n/a"
    return f"[{ci[0]:.3f}, {ci[1]:.3f}]"


def fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def write_readme_section(payload: dict[str, Any]) -> None:
    existing = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""
    if SECTION_MARKER in existing:
        existing = existing[: existing.index(SECTION_MARKER)].rstrip() + "\n\n"
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8")) if STATUS_PATH.exists() else {}
    table_rows = payload.get("scorerTable") or []
    table_lines = [
        "| scorer | family | Algebra I with-stem | Algebra I masked-stem | Algebra I verdict | Algebra II with-stem | Algebra II masked-stem | Algebra II verdict |",
        "|---|---|---:|---:|---|---:|---:|---|",
    ]
    for row in table_rows:
        algebra_i = row["algebraI"]
        algebra_ii = row["algebraII"]
        table_lines.append(
            f"| {row['display']} | {row['family']} | "
            f"{fmt_rate(algebra_i.get('withStemCeiling'))} {fmt_ci(algebra_i.get('withStemCi95'))} | "
            f"{fmt_rate(algebra_i.get('maskedStem'))} {fmt_ci(algebra_i.get('maskedStemCi95'))} | "
            f"{algebra_i.get('maskedStemVerdict') or 'n/a'} | "
            f"{fmt_rate(algebra_ii.get('withStemCeiling'))} {fmt_ci(algebra_ii.get('withStemCi95'))} | "
            f"{fmt_rate(algebra_ii.get('maskedStem'))} {fmt_ci(algebra_ii.get('maskedStemCi95'))} | "
            f"{algebra_ii.get('maskedStemVerdict') or 'n/a'} |"
        )
    phi = payload["scorers"].get("phi-4") or {}
    option_types = phi.get("algebraIOptionTypes") or {}
    type_bits = []
    for type_name in (
        "algebraic_expression",
        "text",
        "numeric",
        "mixed",
        "ordered_pair",
    ):
        stats = option_types.get(type_name) or {}
        type_bits.append(
            f"{type_name} {fmt_rate(stats.get('passRate'))} {fmt_ci(stats.get('ci95'))} n={stats.get('n')}"
        )
    residual = (phi.get("algebraIResidualNoCatalogCue") or {}).get("stats") or {}
    mistral = payload["scorers"].get("mistral-7b-instruct-v0.3") or {}
    gemma = payload["scorers"].get("gemma-2-9b-it") or {}
    gemma_skip = payload.get("gemmaSkip") or {}
    cut = status.get("cut") or []
    cut_text = (
        "; ".join(f"{row.get('job')}: {row.get('reason')}" for row in cut)
        if cut
        else "nothing cut"
    )
    jobs = status.get("jobs") or {}
    wall = status.get("wallTimeSeconds")
    text = f"""{SECTION_MARKER}

Primary population `masked_token_count >= 1` (n=1215; Algebra I 358; Algebra II 248). Same letter-logprob argmax as the Qwen and Mistral runs. Exploratory. Do not deposit.

Hypothesis: the masked-stem plus options channel needs a capable scorer, not a Qwen scorer.

### Phi-4 (`microsoft/phi-4`)

- revision: `{phi.get('modelRevision')}`
- pooled masked-stem: {fmt_rate((phi.get('pooledMaskedStem') or {}).get('passRate'))} {fmt_ci((phi.get('pooledMaskedStem') or {}).get('ci95'))} n={(phi.get('pooledMaskedStem') or {}).get('n')}
- pooled options-only: {fmt_rate((phi.get('pooledOptionsOnly') or {}).get('passRate'))} {fmt_ci((phi.get('pooledOptionsOnly') or {}).get('ci95'))}
- Algebra I masked-stem: {fmt_rate((phi.get('algebraI') or {}).get('passRate'))} {fmt_ci((phi.get('algebraI') or {}).get('ci95'))} vs chance 0.250 and modal B 0.271; verdict **{(phi.get('algebraI') or {}).get('verdict')}**
- Algebra II masked-stem: {fmt_rate((phi.get('algebraII') or {}).get('passRate'))} {fmt_ci((phi.get('algebraII') or {}).get('ci95'))} vs chance 0.250 and modal C 0.278; verdict **{(phi.get('algebraII') or {}).get('verdict')}**
- Algebra I residual (163 items where no catalog cue points at the key): {fmt_rate(residual.get('passRate'))} {fmt_ci(residual.get('ci95'))}
- Algebra I option types: {'; '.join(type_bits)}
- with-stem ceiling: Algebra I {fmt_rate(((phi.get('withStemCeiling') or {}).get('algebraI') or {}).get('passRate'))}; Algebra II {fmt_rate(((phi.get('withStemCeiling') or {}).get('algebraII') or {}).get('passRate'))}

### Mistral-7B-Instruct-v0.3 with-stem ceiling

- Algebra I: {fmt_rate(((mistral.get('withStemCeiling') or {}).get('algebraI') or {}).get('passRate'))} {fmt_ci(((mistral.get('withStemCeiling') or {}).get('algebraI') or {}).get('ci95'))}
- Algebra II: {fmt_rate(((mistral.get('withStemCeiling') or {}).get('algebraII') or {}).get('passRate'))} {fmt_ci(((mistral.get('withStemCeiling') or {}).get('algebraII') or {}).get('ci95'))}
- Masked-stem (already on disk): Algebra I {fmt_rate((mistral.get('algebraI') or {}).get('passRate'))} verdict {(mistral.get('algebraI') or {}).get('verdict')}; Algebra II {fmt_rate((mistral.get('algebraII') or {}).get('passRate'))} verdict {(mistral.get('algebraII') or {}).get('verdict')}

### Gemma-2-9B-it

- cached: {gemma_skip.get('cached')}
- scored: {bool((gemma.get('complete') or {}).get('maskedStem'))}
- revision: `{gemma.get('modelRevision')}`
- skip: {gemma_skip.get('reason') or 'not applicable'}

### Scorer table (with-stem ceiling vs masked-stem)

{chr(10).join(table_lines)}

Reading: {payload.get('reading')}

GPU runner wall: {wall}; cut: {cut_text}. Jobs: {', '.join(f"{name}={blob.get('status')}" for name, blob in jobs.items()) or 'none yet'}.

Cite `exports/addendum-gpu/scorer-capability-table.json`:

- `hypothesis`
- `residualItemIds` (the 163 Algebra I items)
- `scorers.phi-4.modelRevision`
- `scorers.phi-4.pooledMaskedStem`, `pooledOptionsOnly`, `vsOptionsOnly`
- `scorers.phi-4.algebraI` / `algebraII` (`passRate`, `ci95`, `verdict`, `vsOptionsOnly`)
- `scorers.phi-4.algebraIOptionTypes`
- `scorers.phi-4.algebraIResidualNoCatalogCue`
- `scorers.phi-4.withStemCeiling`
- `scorers.mistral-7b-instruct-v0.3.withStemCeiling`
- `gemmaSkip`
- `scorerTable`
- `reading`
- `runnerStatusPath`

Phi-4 item rows: `masked-stem-phi4-items.jsonl`, `options-only-phi4-items.jsonl`. With-stem summaries: `with-stem-algebra-phi4.json`, `with-stem-algebra-mistral.json`.
"""
    README_PATH.write_text(existing + text, encoding="utf-8")


def main() -> None:
    primary_list = load_primary_ids()
    primary_ids = set(primary_list)
    items_by_id = load_items()
    residual = residual_ids(items_by_id, primary_ids)
    algebra_i_ids = [
        item_id
        for item_id in primary_list
        if f"{items_by_id[item_id].get('authority')}::{items_by_id[item_id].get('claim')}"
        == ALGEBRA_I_CELL
    ]
    type_by_id = option_type_by_id(items_by_id, algebra_i_ids)
    modal_by_cell = load_modal_by_cell(POSITION_PATH)
    scorers: dict[str, Any] = {}
    for key, spec in SCORERS.items():
        scorers[key] = summarize_scorer(
            key,
            spec,
            primary_ids,
            set(residual),
            type_by_id,
            modal_by_cell,
        )
    table = [table_row(scorers[key]) for key in SCORERS]
    status = json.loads(STATUS_PATH.read_text(encoding="utf-8")) if STATUS_PATH.exists() else {}
    phi_complete = bool(
        scorers["phi-4"]["complete"]["maskedStem"]
        and scorers["phi-4"]["complete"]["optionsOnly"]
        and scorers["phi-4"]["complete"]["withStemAlgebra"]
    )
    mistral_ceiling_complete = bool(
        scorers["mistral-7b-instruct-v0.3"]["complete"]["withStemAlgebra"]
    )
    gemma_skip = {
        "cached": True,
        "scored": False,
        "revision": "11c9b309abf73637e4b6f9a3fa1e92e615547819",
        "reason": (
            "Weights were already cached, but google/gemma-2-9b-it "
            "apply_chat_template raises TemplateError: System role not supported. "
            "The shared scorer always sends a system message, so this family was not scored."
        ),
    }
    required_complete = phi_complete and mistral_ceiling_complete
    payload = {
        "status": "complete" if required_complete else (status.get("status") or "partial"),
        "label": "exploratory",
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "population": "masked_token_count_ge_1",
        "nPrimary": 1215,
        "nAlgebraI": 358,
        "nAlgebraII": 248,
        "chance": CHANCE_BAR,
        "algebraIModalLetterBar": ALGEBRA_I_MODAL,
        "algebraIIModalLetterBar": ALGEBRA_II_MODAL,
        "hypothesis": (
            "The masked-stem plus options Algebra I / II effect needs a capable "
            "scorer, not a Qwen scorer."
        ),
        "residualDefinition": (
            "Algebra I primary items where none of lower-central numeric, population "
            "modal letter, S1 hub, or unique-longest option points at the key."
        ),
        "residualItemIds": residual,
        "optionTypeRule": (
            "Item-level: all options share a type, else majority if it is at least half, "
            "else mixed. Types: numeric, algebraic_expression, ordered_pair, text."
        ),
        "scorers": scorers,
        "scorerTable": table,
        "reading": reading_sentence(table),
        "gemmaSkip": gemma_skip,
        "requiredJobsComplete": required_complete,
        "runnerStatusPath": "exports/addendum-gpu/scorer-capability-status.json",
        "doNotDeposit": True,
    }
    if required_complete and STATUS_PATH.exists():
        status["status"] = "complete"
        status["requiredJobsComplete"] = True
        status["gemmaSkip"] = gemma_skip
        existing_cut = status.get("cut") or []
        if not any(str(row.get("job", "")).startswith("gemma") for row in existing_cut):
            existing_cut.append(
                {
                    "job": "gemma-2-9b-it",
                    "reason": gemma_skip["reason"],
                }
            )
        else:
            for row in existing_cut:
                if str(row.get("job", "")).startswith("gemma"):
                    row["reason"] = gemma_skip["reason"]
        status["cut"] = existing_cut
        dump_json(STATUS_PATH, status)
    dump_json(TABLE_PATH, payload)
    write_readme_section(payload)
    print(
        json.dumps(
            {
                "out": str(TABLE_PATH),
                "status": payload["status"],
                "reading": payload["reading"],
                "phi4": {
                    "revision": scorers["phi-4"].get("modelRevision"),
                    "complete": scorers["phi-4"].get("complete"),
                    "algebraI": (scorers["phi-4"].get("algebraI") or {}).get("verdict"),
                    "algebraII": (scorers["phi-4"].get("algebraII") or {}).get("verdict"),
                },
                "mistralWithStem": scorers["mistral-7b-instruct-v0.3"].get("withStemCeiling"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
