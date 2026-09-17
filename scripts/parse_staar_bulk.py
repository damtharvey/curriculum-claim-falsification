#!/usr/bin/env python3
"""Parse STAAR released math PDFs. Skip items without recoverable stem, choices, and key."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, base_item, clean_ws, dump_jsonl, extract_pdf_text
from parse_helpers import LETTER_MAP, extract_lettered_choices, flatten, looks_like_figure, normalize_letter

LICENSE = (
    "Texas Education Agency STAAR released mathematics test. Public released form. "
    "TEA copyright; research use of released items."
)
KEY_FLAT = re.compile(
    r"(\d{1,2})\s+[1-5]\s+(?:Readiness|Supporting)(?:\s+Standard)?\s+"
    r"((?:A\.\d+|\d{1,2}\.\d+)\s*\([A-Z]\))\s+"
    r"((?:[A-DJFGHJ]|[-–−]?\d+(?:\.\d+)?))"
)
SKIP_NAME = ("spanish", "rationale", "itemanalysis", "item-analysis")


def grade_from_name(name: str) -> str:
    low = name.lower()
    if "algebra" in low or "alg-i" in low or "algi" in low or "alg1" in low or "eoc" in low:
        return "alg1"
    m = re.search(r"(?:gr(?:ade)?|g)[\s_-]*([3-8])", low)
    if m:
        return m.group(1)
    m = re.search(r"-([3-8])-math", low)
    if m:
        return m.group(1)
    m = re.search(r"math-([3-8])", low)
    if m:
        return m.group(1)
    return "unknown"


def year_from_name(name: str) -> str:
    m = re.search(r"(20[1-2][0-9])", name)
    return m.group(1) if m else "unknown"


def is_key_name(name: str) -> bool:
    low = name.lower()
    return any(x in low for x in ("key", "answer")) and "rationale" not in low


def parse_keys(text: str) -> dict[int, tuple[str, str | None]]:
    keys: dict[int, tuple[str, str | None]] = {}
    for m in KEY_FLAT.finditer(flatten(text)):
        q = int(m.group(1))
        teks = clean_ws(m.group(2))
        raw = m.group(3)
        if re.fullmatch(r"\d+(?:\.\d+)?", raw):
            keys[q] = (raw, teks)
        else:
            letter = normalize_letter(raw)
            if letter in "ABCD":
                keys[q] = (letter, teks)
    return keys


KEY_ROW_ITEM = re.compile(r"^\d{1,2}$")
KEY_ROW_TEKS = re.compile(r"^(?:A\.\d+|\d{1,2}\.\d+)\([A-Z]\)$")
KEY_ROW_ANSWER = re.compile(r"^(?:[A-DFGHJ]|[-–−]?\d+(?:\.\d+)?)$")
KEY_ROW_Y_GAP = 4.0


def parse_keys_from_pdf(path: Path) -> dict[int, tuple[str, str | None]]:
    """Read a STAAR answer-key PDF by grouping words into table rows.

    `parse_keys` on concatenated text treats a process-SE code such as 5.15(A)
    as the answer, and `page.get_text("text")` drops some 2016 item numbers.
    Row clustering uses a 4-point y gap. F/G/H/J map to A/B/C/D.
    """
    import fitz

    keys: dict[int, tuple[str, str | None]] = {}
    document = fitz.open(path)
    try:
        for page in document:
            words = sorted(page.get_text("words"), key=lambda row: (row[1], row[0]))
            clusters: list[list] = []
            current: list = []
            last_y: float | None = None
            for word in words:
                y = float(word[1])
                if last_y is None or abs(y - last_y) <= KEY_ROW_Y_GAP:
                    current.append(word)
                else:
                    clusters.append(current)
                    current = [word]
                last_y = y
            if current:
                clusters.append(current)
            for cluster in clusters:
                tokens = [str(word[4]) for word in sorted(cluster, key=lambda row: row[0])]
                if not any(token in {"Readiness", "Supporting"} for token in tokens):
                    continue
                if not tokens or not KEY_ROW_ITEM.match(tokens[0]):
                    continue
                question = int(tokens[0])
                if question < 1 or question > 60:
                    continue
                answer = tokens[-1]
                if not KEY_ROW_ANSWER.match(answer):
                    continue
                teks_token = next((token for token in tokens if KEY_ROW_TEKS.match(token)), None)
                if re.fullmatch(r"[A-DFGHJ]", answer):
                    letter = normalize_letter(answer)
                    if letter in "ABCD":
                        keys[question] = (letter, teks_token)
                else:
                    keys[question] = (answer, teks_token)
    finally:
        document.close()
    return keys


RULER_REST = re.compile(
    r"(?i)^[\d\s.,+\-–−]*(?:inches|centimeters|centimetres)\b"
)
NUMERIC_ONLY_REST = re.compile(r"^[\d\s.,+\-–−]+$")
CHOICE_CUT = re.compile(
    r"(---PAGE\s+\d+---|Mathematics\s+Page\s+\d+|BE SURE YOU HAVE RECORDED)",
    re.I,
)


def looks_like_item_start(rest: str) -> bool:
    if NUMERIC_ONLY_REST.match(rest):
        return False
    if RULER_REST.match(rest):
        return False
    stripped = re.sub(r"(?i)\binches\b|\bcentimeters\b|\bcentimetres\b", " ", rest)
    return bool(re.search(r"[A-Za-z]{4,}", stripped))


def parse_items(text: str, keys: dict[int, tuple[str, str | None]], meta: dict[str, str]) -> list[dict]:
    idx = text.find("DIRECTIONS")
    body = text[idx:] if idx >= 0 else text
    lines = [ln.rstrip() for ln in body.splitlines()]
    item_re = re.compile(r"^(\d{1,2})\s+(\S.*)$")
    blocks: dict[int, list[str]] = {}
    current: int | None = None
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("Mathematics") or s.startswith("Page ") or s.startswith("STAAR"):
            continue
        if s.startswith("---PAGE"):
            continue
        im = item_re.match(s)
        if im and int(im.group(1)) in keys:
            rest = im.group(2).strip()
            if not looks_like_item_start(rest):
                continue
            current = int(im.group(1))
            blocks.setdefault(current, [])
            if rest:
                blocks[current].append(rest)
            continue
        if current is not None:
            blocks[current].append(s)

    rows: list[dict] = []
    for q, (key, teks) in sorted(keys.items()):
        block = blocks.get(q, [])
        letters = "FGHJ" if any(re.match(r"^F\b", ln.strip()) for ln in block) else "ABCD"
        stem_parts, choices = extract_lettered_choices(block, letters)
        stem = clean_ws(" ".join(stem_parts))
        stem = CHOICE_CUT.split(stem)[0].strip()
        choices = {
            letter: clean_ws(CHOICE_CUT.split(text)[0])
            for letter, text in choices.items()
        }
        grade = meta["grade"]
        year = meta["year"]
        claim = f"g{grade}" if grade != "alg1" else "alg1"
        figure_dep = looks_like_figure(stem)
        if re.fullmatch(r"\d+(?:\.\d+)?", key):
            if len(stem) < 12:
                continue
            rec = base_item(
                item_id=f"staar-{year}-{grade}-q{q}",
                corpus="staar",
                authority="teks",
                claim=claim,
                stem=stem,
                key=key,
                response_type="numeric",
                source_url=meta["source"],
                license_note=LICENSE,
                year=year,
                grade=grade if grade != "alg1" else "hs",
                official_tag=teks or claim,
                figure_dependent=figure_dep,
                transcription_method="text-layer",
            )
            rows.append(rec)
            continue
        if figure_dep:
            continue
        if not stem or len(stem) < 12:
            continue
        if len(choices) != 4 or key not in choices:
            continue
        rec = base_item(
            item_id=f"staar-{year}-{grade}-q{q}",
            corpus="staar",
            authority="teks",
            claim=claim,
            stem=stem,
            key=key,
            response_type="selected",
            source_url=meta["source"],
            license_note=LICENSE,
            year=year,
            grade=grade if grade != "alg1" else "hs",
            choices=choices,
            official_tag=teks or claim,
            figure_dependent=False,
            transcription_method="text-layer",
        )
        rows.append(rec)
    return rows


def pair_files(files: list[Path]) -> list[tuple[Path, Path | None]]:
    tests: list[Path] = []
    keys: list[Path] = []
    for p in files:
        name = p.name.lower()
        if p.suffix.lower() != ".pdf":
            continue
        if any(x in name for x in SKIP_NAME):
            continue
        if is_key_name(name):
            keys.append(p)
        else:
            tests.append(p)
    paired: list[tuple[Path, Path | None]] = []
    for test in tests:
        g = grade_from_name(test.name)
        y = year_from_name(test.name)
        candidates = [
            k
            for k in keys
            if grade_from_name(k.name) == g and year_from_name(k.name) == y
        ]

        def key_rank(path: Path) -> int:
            n = path.name.lower()
            score = 0
            if any(x in n for x in ("redesign", "sampler", "practice", "spanish")):
                score -= 20
            if "answerkey" in n or n.endswith("-key.pdf") or "-key-" in n:
                score += 8
            if "may" in n or "released" in n:
                score += 3
            return score

        match = max(candidates, key=key_rank) if candidates else None
        paired.append((test, match))
    return paired


def main() -> None:
    files = list((RAW / "staar").glob("*")) + list(RAW.glob("staar-*.pdf"))
    files = [p for p in files if p.is_file()]
    rows: list[dict] = []
    seen: set[str] = set()
    for test, key_pdf in pair_files(files):
        try:
            text = extract_pdf_text(test)
        except Exception as exc:  # noqa: BLE001
            print("skip", test, exc)
            continue
        keys: dict[int, tuple[str, str | None]] = {}
        if key_pdf is not None:
            try:
                keys = parse_keys(extract_pdf_text(key_pdf))
            except Exception as exc:  # noqa: BLE001
                print("key fail", key_pdf, exc)
        if not keys:
            keys = parse_keys(text)
        if not keys:
            print("no keys", test.name)
            continue
        meta = {
            "grade": grade_from_name(test.name),
            "year": year_from_name(test.name),
            "source": f"https://tea.texas.gov/student-assessment/testing/staar/staar-released-test-questions#{test.name}",
        }
        got = parse_items(text, keys, meta)
        print(f"{test.name}: {len(got)} items from {len(keys)} keys")
        for rec in got:
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            rows.append(rec)
    out = ROOT / "data" / "staar.jsonl"
    dump_jsonl(out, rows)
    print(f"wrote {len(rows)} -> {out}")


if __name__ == "__main__":
    main()
