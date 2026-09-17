#!/usr/bin/env python3
"""Download public MCQ cue-control datasets and convert to Contract A items. No invented labels."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import DATA, ROOT, append_log, base_item, dump_jsonl

OUT = DATA / "real-controls.jsonl"
RAW = ROOT / "data" / "raw" / "controls"


def letters_for(n: int) -> list[str]:
    return [chr(ord("A") + i) for i in range(n)]


def write_split(rows: list[dict[str, Any]], name: str) -> None:
    path = DATA / f"real-controls-{name}.jsonl"
    dump_jsonl(path, rows)
    print(name, len(rows), "->", path)


def load_openbookqa() -> list[dict[str, Any]]:
    from datasets import load_dataset

    ds = load_dataset("allenai/openbookqa", "main")
    rows: list[dict[str, Any]] = []
    for split, table in ds.items():
        for i, rec in enumerate(table):
            choices = rec["choices"]
            labels = list(choices["label"])
            texts = list(choices["text"])
            cmap = {str(lab): str(txt) for lab, txt in zip(labels, texts)}
            key = str(rec["answerKey"]).upper()
            if key not in cmap or len(cmap) < 2:
                continue
            rows.append(
                base_item(
                    item_id=f"openbookqa-{split}-{rec.get('id', i)}",
                    corpus="openbookqa",
                    authority="openbookqa",
                    claim="choices-only",
                    stem=str(rec["question_stem"]),
                    key=key,
                    response_type="selected",
                    source_url="https://huggingface.co/datasets/allenai/openbookqa",
                    license_note="OpenBookQA (Allen AI). Public research dataset. Mihaylov et al. 2018.",
                    year="2018",
                    grade="na",
                    choices=cmap,
                    official_tag=f"openbookqa-{split}",
                    transcription_method="dataset",
                )
            )
            rows[-1]["split"] = split
    return rows


def load_commonsenseqa() -> list[dict[str, Any]]:
    from datasets import load_dataset

    ds = load_dataset("tau/commonsense_qa")
    rows: list[dict[str, Any]] = []
    for split, table in ds.items():
        for i, rec in enumerate(table):
            labels = list(rec["choices"]["label"])
            texts = list(rec["choices"]["text"])
            cmap = {str(lab): str(txt) for lab, txt in zip(labels, texts)}
            key = str(rec.get("answerKey") or "").upper()
            if not key or key not in cmap:
                continue
            rows.append(
                base_item(
                    item_id=f"commonsenseqa-{split}-{rec.get('id', i)}",
                    corpus="commonsenseqa",
                    authority="commonsenseqa",
                    claim="choices-only",
                    stem=str(rec["question"]),
                    key=key,
                    response_type="selected",
                    source_url="https://huggingface.co/datasets/tau/commonsense_qa",
                    license_note="CommonsenseQA (Talmor et al. 2019). Public research dataset.",
                    year="2019",
                    grade="na",
                    choices=cmap,
                    official_tag=f"commonsenseqa-{split}",
                    transcription_method="dataset",
                )
            )
            rows[-1]["split"] = split
    return rows


def load_swag() -> list[dict[str, Any]]:
    import csv
    import io
    import urllib.request

    RAW.mkdir(parents=True, exist_ok=True)
    urls = {
        "train": "https://raw.githubusercontent.com/rowanz/swagaf/master/data/train.csv",
        "val": "https://raw.githubusercontent.com/rowanz/swagaf/master/data/val.csv",
    }
    rows: list[dict[str, Any]] = []
    for split, url in urls.items():
        dest = RAW / f"swag-{split}.csv"
        if not dest.exists():
            urllib.request.urlretrieve(url, dest)
            append_log(f"- ok {url} -> {dest.name}")
        text = dest.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for i, rec in enumerate(reader):
            opts = [str(rec.get(f"ending{k}") or rec.get(f"end{k}") or "") for k in range(4)]
            if any(not o for o in opts):
                continue
            try:
                label = int(rec.get("label", 0))
            except ValueError:
                continue
            cmap = {letters_for(4)[k]: opts[k] for k in range(4)}
            rows.append(
                base_item(
                    item_id=f"swag-{split}-{rec.get('id', i)}",
                    corpus="swag",
                    authority="swag",
                    claim="endings-only",
                    stem=str(rec.get("startphrase") or rec.get("sent1") or ""),
                    key=letters_for(4)[label],
                    response_type="selected",
                    source_url=url,
                    license_note="SWAG (Zellers et al. 2018). Public GitHub release.",
                    year="2018",
                    grade="na",
                    choices=cmap,
                    official_tag=f"swag-{split}",
                    transcription_method="dataset",
                )
            )
            rows[-1]["split"] = "train" if split == "train" else "dev"
    return rows


def load_race() -> list[dict[str, Any]]:
    from datasets import load_dataset

    ds = load_dataset("ehovy/race", "all")
    rows: list[dict[str, Any]] = []
    for split, table in ds.items():
        for i, rec in enumerate(table):
            options = list(rec["options"])
            key = str(rec["answer"]).upper()
            cmap = {letters_for(len(options))[k]: str(options[k]) for k in range(len(options))}
            if key not in cmap:
                continue
            rows.append(
                base_item(
                    item_id=f"race-{split}-{rec.get('example_id', i)}",
                    corpus="race",
                    authority="race",
                    claim="options-only",
                    stem=str(rec.get("question") or ""),
                    key=key,
                    response_type="selected",
                    source_url="https://huggingface.co/datasets/ehovy/race",
                    license_note="RACE (Lai et al. 2017). Public research dataset. Passage withheld from this channel.",
                    year="2017",
                    grade="na",
                    choices=cmap,
                    official_tag=f"race-{split}",
                    transcription_method="dataset",
                )
            )
            rows[-1]["split"] = split
    return rows


def load_arct() -> list[dict[str, Any]]:
    """ARCT from the IBM/UKP public release if datasets hub has it; else GitHub raw."""
    import urllib.request

    RAW.mkdir(parents=True, exist_ok=True)
    urls = {
        "train": "https://raw.githubusercontent.com/UKPLab/acl2018-argument-reasoning-comprehension-task/master/data/train-w-swap.csv",
        "dev": "https://raw.githubusercontent.com/UKPLab/acl2018-argument-reasoning-comprehension-task/master/data/dev-w-swap.csv",
        "test": "https://raw.githubusercontent.com/UKPLab/acl2018-argument-reasoning-comprehension-task/master/data/test-w-swap.csv",
    }
    mirrors = {
        "train": "https://raw.githubusercontent.com/IBM/neuro-symbolic-ai/master/neuro-symbolic-pretrained-concept-tagger/data/arct/train.csv",
        "dev": "https://raw.githubusercontent.com/timniven/arct/master/data/train.csv",
        "test": "https://raw.githubusercontent.com/timniven/arct/master/data/test.csv",
    }
    extra = {
        "train": "https://raw.githubusercontent.com/habernal/acl2018-argument-reasoning-comprehension-task/master/data/train.csv",
        "dev": "https://github.com/UKPLab/acl2018-argument-reasoning-comprehension-task/raw/master/mturk/train-full.csv",
        "test": "https://raw.githubusercontent.com/pepa/argument-reasoning-comprehension/master/data/test.csv",
    }
    rows: list[dict[str, Any]] = []
    import csv
    import io

    for split, url in list(urls.items()) + list(mirrors.items()) + list(extra.items()):
        dest = RAW / f"arct-{split}-{url.split('/')[-1]}"
        try:
            if not dest.exists():
                urllib.request.urlretrieve(url, dest)
                append_log(f"- ok {url} -> {dest.name}")
        except Exception as exc:  # noqa: BLE001
            append_log(f"- FAIL {url} :: {exc}")
            continue
        text = dest.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for i, rec in enumerate(reader):
            # try common schemas
            w0 = rec.get("warrant0") or rec.get("warrant_0") or rec.get("#1 Warrant") or rec.get("warrant")
            w1 = rec.get("warrant1") or rec.get("warrant_1") or rec.get("#2 Warrant") or rec.get("alternative")
            label = rec.get("correctLabelW0orW1") or rec.get("label") or rec.get("correctLabel")
            if w0 is None or w1 is None or label is None or str(label).strip() == "":
                continue
            try:
                lab = int(float(str(label).strip()))
            except ValueError:
                continue
            if lab not in (0, 1):
                continue
            cmap = {"A": str(w0), "B": str(w1)}
            rows.append(
                base_item(
                    item_id=f"arct-{split}-{rec.get('#id', rec.get('id', i))}",
                    corpus="arct",
                    authority="arct",
                    claim="not-cue",
                    stem=str(rec.get("claim") or rec.get("#1 Claim") or ""),
                    key="A" if lab == 0 else "B",
                    response_type="selected",
                    source_url=url,
                    license_note="ARCT (Habernal et al. 2018; Niven and Kao 2019 cue analysis). Public research dataset.",
                    year="2018",
                    grade="na",
                    choices=cmap,
                    official_tag=f"arct-{split}",
                    transcription_method="dataset",
                )
            )
            rows[-1]["split"] = split
            rows[-1]["reason"] = rec.get("reason") or rec.get("#1 Reason") or ""
        if rows:
            break
    return rows


def main() -> None:
    all_rows: list[dict[str, Any]] = []
    loaders = {
        "openbookqa": load_openbookqa,
        "commonsenseqa": load_commonsenseqa,
        "swag": load_swag,
        "race": load_race,
        "arct": load_arct,
    }
    for name, fn in loaders.items():
        try:
            rows = fn()
            write_split(rows, name)
            all_rows.extend(rows)
            append_log(f"- controls {name} n={len(rows)}")
        except Exception as exc:  # noqa: BLE001
            append_log(f"- FAIL controls {name} :: {exc}")
            print("FAIL", name, exc)
    dump_jsonl(OUT, all_rows)
    print("total", len(all_rows), "->", OUT)


if __name__ == "__main__":
    main()
