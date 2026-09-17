#!/usr/bin/env python3
"""Score a human masked-stem plus options response file against sheet-key.json."""

from __future__ import annotations

import argparse
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "exports" / "human-masked-stem"
KEY_PATH = OUT_DIR / "sheet-key.json"
N_BOOTSTRAP = 1000
CHANCE = 0.25
MODAL_FREQUENCY = 97 / 358
ALLOWED_LETTERS = {"A", "B", "C", "D"}
ALLOWED_TOKENS = ALLOWED_LETTERS | {"R"}
START_RE = re.compile(r"^#\s*start:\s*(.+)\s*$", re.I)
END_RE = re.compile(r"^#\s*end:\s*(.+)\s*$", re.I)
COMMENT_RE = re.compile(r"^#")
N_SAMPLE = 40
MIN_N_WITNESS = 10


def bootstrap_ci(flags: list[int], n_bootstrap: int = N_BOOTSTRAP, seed: int = 11) -> tuple[float, float]:
    """Percentile bootstrap matching scripts/score_choices_only.py (Random.randrange)."""
    if not flags:
        raise RuntimeError("bootstrap CI is undefined for an empty flag list")
    rng = random.Random(seed)
    sample_size = len(flags)
    samples: list[float] = []
    for _replicate in range(n_bootstrap):
        total = 0
        for _index in range(sample_size):
            total += flags[rng.randrange(sample_size)]
        samples.append(total / sample_size)
    samples.sort()
    lower = samples[int(0.025 * (n_bootstrap - 1))]
    upper = samples[int(0.975 * (n_bootstrap - 1))]
    return (lower, upper)


def cohens_kappa(human_letters: list[str], model_letters: list[str]) -> dict[str, Any]:
    if len(human_letters) != len(model_letters):
        raise RuntimeError("kappa requires paired letter lists of equal length")
    pair_count = len(human_letters)
    if pair_count == 0:
        raise RuntimeError("kappa is undefined for zero included items")
    observed_agreement = sum(
        int(human == model) for human, model in zip(human_letters, model_letters)
    ) / pair_count
    expected_agreement = 0.0
    categories = sorted(ALLOWED_LETTERS)
    for letter in categories:
        human_share = sum(int(letter == token) for token in human_letters) / pair_count
        model_share = sum(int(letter == token) for token in model_letters) / pair_count
        expected_agreement += human_share * model_share
    if expected_agreement == 1.0:
        if observed_agreement != 1.0:
            raise RuntimeError("kappa undefined: expected agreement is 1 and observed agreement is not 1")
        kappa = 1.0
    else:
        kappa = (observed_agreement - expected_agreement) / (1.0 - expected_agreement)
    return {
        "n": pair_count,
        "observedAgreement": observed_agreement,
        "expectedAgreement": expected_agreement,
        "kappa": kappa,
    }


def load_key(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, dict):
        raise RuntimeError(f"key file missing items object: {path}")
    if len(items) != N_SAMPLE:
        raise RuntimeError(f"key file has {len(items)} items, expected {N_SAMPLE}")
    ordered: list[dict[str, Any]] = []
    for number in range(1, N_SAMPLE + 1):
        record = items.get(str(number))
        if not isinstance(record, dict):
            raise RuntimeError(f"key file missing item {number}")
        key_letter = str(record["key"]).strip().upper()
        pick = str(record["pick14b"]).strip().upper()
        if key_letter not in ALLOWED_LETTERS:
            raise RuntimeError(f"item {number} has non-letter key {key_letter}")
        if pick not in ALLOWED_LETTERS:
            raise RuntimeError(f"item {number} has non-letter 14B pick {pick}")
        ordered.append(
            {
                "number": number,
                "id": str(record["id"]),
                "key": key_letter,
                "modalLetter": bool(record["modalLetter"]),
                "lowerCentral": bool(record["lowerCentral"]),
                "pick14b": pick,
            }
        )
    return {"meta": payload, "ordered": ordered}


def parse_response_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"response file not found: {path}")
    start_time: str | None = None
    end_time: str | None = None
    letters: list[str] = []
    cue_notes: list[str | None] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        start_match = START_RE.match(line)
        if start_match:
            if start_time is not None:
                raise RuntimeError(f"duplicate start time at line {line_number}")
            start_time = start_match.group(1).strip()
            if not start_time:
                raise RuntimeError(f"empty start time at line {line_number}")
            continue
        end_match = END_RE.match(line)
        if end_match:
            if end_time is not None:
                raise RuntimeError(f"duplicate end time at line {line_number}")
            end_time = end_match.group(1).strip()
            if not end_time:
                raise RuntimeError(f"empty end time at line {line_number}")
            continue
        if COMMENT_RE.match(line):
            continue
        parts = line.split()
        token = parts[0].upper()
        if token not in ALLOWED_TOKENS:
            raise RuntimeError(f"invalid token {parts[0]!r} at line {line_number}")
        if len(parts) > 2:
            raise RuntimeError(f"cue note must be one word at line {line_number}")
        cue_note = parts[1] if len(parts) == 2 else None
        letters.append(token)
        cue_notes.append(cue_note)
    if len(letters) != N_SAMPLE:
        raise RuntimeError(f"{path} has {len(letters)} letters, expected {N_SAMPLE}")
    return {
        "start": start_time,
        "end": end_time,
        "letters": letters,
        "cueNotes": cue_notes,
    }


def score_rater(
    rater: str,
    response_path: Path,
    key_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    key_bundle = load_key(key_path)
    responses = parse_response_file(response_path)
    ordered = key_bundle["ordered"]
    meta = key_bundle["meta"]
    per_item: list[dict[str, Any]] = []
    included_correct: list[int] = []
    included_human: list[str] = []
    included_model: list[str] = []
    recognized_numbers: list[int] = []
    recognized_ids: list[str] = []
    for record, human_letter, cue_note in zip(
        ordered, responses["letters"], responses["cueNotes"], strict=True
    ):
        excluded = human_letter == "R"
        correct: bool | None
        if excluded:
            correct = None
            recognized_numbers.append(record["number"])
            recognized_ids.append(record["id"])
        else:
            correct = human_letter == record["key"]
            included_correct.append(int(correct))
            included_human.append(human_letter)
            included_model.append(record["pick14b"])
        per_item.append(
            {
                "number": record["number"],
                "id": record["id"],
                "key": record["key"],
                "human": human_letter,
                "pick14b": record["pick14b"],
                "correct": correct,
                "excluded": excluded,
                "modalLetter": record["modalLetter"],
                "lowerCentral": record["lowerCentral"],
                "cueNote": cue_note,
            }
        )
    included_n = len(included_correct)
    if included_n == 0:
        raise RuntimeError("primary n is 0 after R exclusions")
    pass_rate = sum(included_correct) / included_n
    interval = bootstrap_ci(included_correct, N_BOOTSTRAP, 21 + included_n)
    model_included_rate = sum(
        int(record["pick14b"] == record["key"])
        for record in ordered
        if record["number"] not in recognized_numbers
    ) / included_n
    model_all_rate = sum(int(record["pick14b"] == record["key"]) for record in ordered) / N_SAMPLE
    kappa = cohens_kappa(included_human, included_model)
    lower = interval[0]
    clears_chance = included_n >= MIN_N_WITNESS and lower > CHANCE
    clears_modal = included_n >= MIN_N_WITNESS and lower > MODAL_FREQUENCY
    payload: dict[str, Any] = {
        "status": "complete",
        "rater": rater,
        "responsePath": str(response_path),
        "keyPath": str(key_path),
        "scoredAt": datetime.now(timezone.utc).isoformat(),
        "preregistrationSha256": meta.get("preregistrationSha256"),
        "seed": meta.get("seed"),
        "start": responses["start"],
        "end": responses["end"],
        "nItems": N_SAMPLE,
        "nIncluded": included_n,
        "nRecognized": len(recognized_numbers),
        "recognizedItemNumbers": recognized_numbers,
        "recognizedIds": recognized_ids,
        "passRate": pass_rate,
        "ci95": [interval[0], interval[1]],
        "chance": CHANCE,
        "modalFrequency": MODAL_FREQUENCY,
        "vsChance": {
            "chance": CHANCE,
            "lowerCiAboveChance": clears_chance,
        },
        "vsModal": {
            "modalFrequency": MODAL_FREQUENCY,
            "lowerCiAboveModal": clears_modal,
        },
        "clearsChannelBar": bool(clears_chance and clears_modal),
        "pick14bRateIncluded": model_included_rate,
        "pick14bRateAll40": model_all_rate,
        "kappa14b": kappa,
        "bootstrap": {
            "method": "random.Random.randrange",
            "nBoot": N_BOOTSTRAP,
            "seed": 21 + included_n,
        },
        "perItem": per_item,
    }
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rater", required=True, help="rater slug, used in default paths")
    parser.add_argument("--responses", type=Path, default=None)
    parser.add_argument("--key", type=Path, default=KEY_PATH)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    rater = str(args.rater).strip()
    if not rater:
        raise RuntimeError("rater slug is empty")
    response_path = args.responses if args.responses is not None else OUT_DIR / f"responses-{rater}.txt"
    output_path = args.output if args.output is not None else OUT_DIR / f"results-{rater}.json"
    payload = score_rater(rater, response_path, args.key, output_path)
    print(
        f"rater={payload['rater']} n={payload['nIncluded']} "
        f"rate={payload['passRate']:.3f} CI [{payload['ci95'][0]:.3f}, {payload['ci95'][1]:.3f}] "
        f"kappa={payload['kappa14b']['kappa']:.3f} recognized={payload['nRecognized']} "
        f"clears={payload['clearsChannelBar']} -> {output_path}"
    )


if __name__ == "__main__":
    main()
