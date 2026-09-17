#!/usr/bin/env python3
"""Extract keyed public items from downloaded NYSED / STAAR / MCAS PDFs.

No invented choices. Empty graphic options stay out of items.jsonl.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def dump(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {len(rows)} -> {path}")


def normalize_ccss(code: str) -> str:
    code = code.replace("CCSS.Math.Content.", "").strip()
    m = re.fullmatch(r"(\d+\.[A-Z]+\.[A-Z]\.\d+)([a-z])", code)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return code


def clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def choice_ok(text: str) -> bool:
    t = clean_ws(text)
    if len(t) < 2:
        return False
    if t in {"A", "B", "C", "D", "F", "G", "H", "J"}:
        return False
    return True


# ---------------------------------------------------------------------------
# NYSED
# ---------------------------------------------------------------------------

MAP_RE = re.compile(
    r"^\s*(\d+)\s+Multiple Choice\s+([A-D])\s+\d+\s+CCSS\.Math\.Content\.(\S+)",
    re.M,
)
QNUM_LINE = re.compile(r"^(?P<pre>.*?)(?P<num>\d{1,2})\s+(?P<rest>\S.*)$")
CHOICE_LINE = re.compile(r"^([A-D])\s*(.*)$")


def parse_nysed(grade: str, txt_path: Path, source_url: str, year: str) -> list[dict]:
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    keys: dict[int, tuple[str, str, float | None]] = {}
    for m in MAP_RE.finditer(text):
        q = int(m.group(1))
        key = m.group(2)
        code = normalize_ccss(m.group(3))
        tail = text[m.end() : m.end() + 80]
        pct = None
        pm = re.search(r"(0\.\d+)", tail)
        if pm:
            pct = round(float(pm.group(1)) * 100, 1)
        keys[q] = (key, code, pct)

    start = -1
    for marker in ("RELEASED QUESTIONS", "Released Questions", "Session 1"):
        start = text.find(marker)
        if start >= 0:
            break
    body = text[start:] if start >= 0 else text
    body = re.split(r"Map to the Standards", body, maxsplit=1)[0]
    lines = [ln.rstrip() for ln in body.splitlines()]

    by_q: dict[int, list[str]] = {}
    current: int | None = None
    for ln in lines:
        stripped = ln.strip()
        if stripped in {"GO ON", "STOP"} or stripped.startswith("Session ") or stripped.startswith("Page "):
            continue
        if stripped.startswith("Grade ") or "Reference Sheet" in stripped:
            continue
        qm = re.match(r"^(\d{1,2})\s+(\S.*)$", stripped)
        if qm and int(qm.group(1)) in keys:
            current = int(qm.group(1))
            by_q.setdefault(current, [])
            rest = qm.group(2).strip()
            if rest:
                by_q[current].append(rest)
            continue
        # number sitting alone at left of a wrapped stem
        qm2 = re.match(r"^(\d{1,2})\s*$", stripped)
        if qm2 and int(qm2.group(1)) in keys:
            current = int(qm2.group(1))
            by_q.setdefault(current, [])
            continue
        if current is not None:
            by_q[current].append(stripped)

    rows: list[dict] = []
    incomplete: list[dict] = []
    for q, (key, code, pct) in sorted(keys.items()):
        block = by_q.get(q, [])
        choices: dict[str, str] = {}
        stem_parts: list[str] = []
        cur_letter: str | None = None
        for ln in block:
            cm = re.match(r"^([A-D])(?:\s+(.*))?$", ln)
            if cm and (cm.group(1) not in choices or cur_letter == cm.group(1)):
                letter = cm.group(1)
                rest = (cm.group(2) or "").strip()
                if letter not in choices:
                    choices[letter] = rest
                    cur_letter = letter
                elif rest:
                    choices[letter] = (choices[letter] + " " + rest).strip()
                continue
            if cur_letter and ln and not re.match(r"^[A-D]\b", ln):
                # continuation of a choice unless it looks like a new stem sentence after all 4
                if len(choices) < 4:
                    choices[cur_letter] = (choices[cur_letter] + " " + ln).strip()
                    continue
            if not cur_letter:
                stem_parts.append(ln)
        stem = clean_ws(" ".join(p for p in stem_parts if p))
        if not stem:
            stem = f"NYSED {year} grade {grade} item {q} (stem graphics in PDF)."
        if len(choices) == 4 and all(choice_ok(v) for v in choices.values()):
            rec = {
                "id": f"nysed-{year}-{grade}-q{q}",
                "corpus": "nysed",
                "authority": "ccss",
                "claim": code,
                "stem": stem,
                "choices": {k: clean_ws(v) for k, v in choices.items()},
                "key": key,
                "responseType": "selected",
                "sourceUrl": source_url,
                "licenseNote": f"NYSED {year} Grades 3-8 Mathematics released questions. Public released-test items; reuse terms follow NYSED.",
                "grade": grade,
                "role": "target",
            }
            if pct is not None:
                rec["percentCorrect"] = pct
            rows.append(rec)
        else:
            incomplete.append(
                {
                    "id": f"nysed-{year}-{grade}-q{q}",
                    "corpus": "nysed",
                    "claim": code,
                    "key": key,
                    "status": "figure-dependent",
                    "note": "choice or stem numbers were graphics; not invented",
                }
            )
    (ROOT / "data" / f"nysed-{year}-g{grade}-incomplete.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in incomplete),
        encoding="utf-8",
    )
    print(f"nysed {year} g{grade}: complete {len(rows)} incomplete {len(incomplete)}")
    return rows


# ---------------------------------------------------------------------------
# STAAR
# ---------------------------------------------------------------------------

IA_LINE = re.compile(
    r"^\s*(\d+)\.†?\s+(\d+)\s+(.+)$",
)


def parse_staar_keys(ia_text: str) -> dict[int, str]:
    """Read the MATHEMATICS half of the two-column item-analysis page."""
    keys: dict[int, str] = {}
    letters = ["A", "B", "C", "D"]
    for raw in ia_text.splitlines():
        marks = list(re.finditer(r"(\d+)\.(†?)", raw))
        if len(marks) < 2:
            continue
        q = int(marks[1].group(1))
        if marks[1].group(2) == "†":
            continue
        rest = raw[marks[1].end() :]
        parts = rest.split()
        starred = None
        # RC then A B C D [**]
        nums = parts[:6]
        choice_parts = nums[1:5] if nums and re.fullmatch(r"\d+", nums[0]) else nums[:4]
        for i, p in enumerate(choice_parts[:4]):
            if "*" in p:
                starred = letters[i]
        if starred:
            keys[q] = starred
    return keys


ITEM_START = re.compile(r"^(\d+)\s+(.+)$")
STAAR_CHOICE = re.compile(r"^([A-D]|[F-J])\s+(.+)$")


def parse_staar_items(test_text: str, keys: dict[int, str], grade: str, source_url: str) -> list[dict]:
    # drop front matter
    idx = test_text.find("DIRECTIONS")
    body = test_text[idx:] if idx >= 0 else test_text
    lines = [ln.rstrip() for ln in body.splitlines()]
    items: dict[int, list[str]] = {}
    current: int | None = None
    for ln in lines:
        s = ln.strip()
        if not s:
            if current is not None:
                items.setdefault(current, []).append("")
            continue
        if s.startswith("Mathematics") or s.startswith("Page ") or s.startswith("STAAR"):
            continue
        if re.fullmatch(r"\d{4,}_\d", s):
            continue
        im = re.match(r"^(\d{1,2})\s+(.+)$", s)
        if im and int(im.group(1)) in keys:
            current = int(im.group(1))
            items.setdefault(current, [])
            items[current].append(im.group(2).strip())
            continue
        if current is not None:
            items[current].append(s)

    letter_sets = (
        ["A", "B", "C", "D"],
        ["F", "G", "H", "J"],
    )
    rows: list[dict] = []
    for q, key in sorted(keys.items()):
        block = items.get(q, [])
        choices: dict[str, str] = {}
        stem_parts: list[str] = []
        cur: str | None = None
        for ln in block:
            cm = re.match(r"^([A-D]|[F-J])\s+(.*)$", ln)
            if cm:
                letter = cm.group(1)
                rest = re.split(r"\s{2,}", cm.group(2).strip())[0].strip()
                mapped = {"F": "A", "G": "B", "H": "C", "J": "D"}.get(letter, letter)
                if mapped not in choices:
                    choices[mapped] = rest
                    cur = mapped
                elif rest and len(choices[mapped]) < 8:
                    choices[mapped] = (choices[mapped] + " " + rest).strip()
                continue
            if cur and ln and len(choices) < 4:
                extra = re.split(r"\s{2,}", ln)[0].strip()
                if extra and not re.match(r"^([A-D]|[F-J])\b", extra):
                    choices[cur] = (choices[cur] + " " + extra).strip()
                continue
            if not cur:
                stem_parts.append(re.split(r"\s{2,}", ln)[0])
        stem = clean_ws(" ".join(p for p in stem_parts if p))
        if "which graph" in stem.lower():
            continue
        if not stem or len(choices) != 4 or not all(choice_ok(v) for v in choices.values()):
            continue
        if any(len(v) > 220 for v in choices.values()):
            continue
        published_key = key
        # if the item used F-J, the IA key is still A-D (A=F, B=G, ...)
        rec = {
            "id": f"staar-2022-{grade}-q{q}",
            "corpus": "staar",
            "authority": "teks",
            "claim": f"g{grade}",
            "stem": stem,
            "choices": {k: clean_ws(v) for k, v in choices.items()},
            "key": published_key,
            "responseType": "selected",
            "sourceUrl": source_url,
            "licenseNote": "Texas Education Agency STAAR May 2022 released mathematics test. Public released form. TEA copyright; research use of released items.",
            "grade": grade,
            "role": "target",
        }
        rows.append(rec)
    print(f"staar g{grade}: {len(rows)} complete MC of {len(keys)} keyed MC")
    return rows


# ---------------------------------------------------------------------------
# MCAS
# ---------------------------------------------------------------------------

MCAS_HEAD = re.compile(r"^MA\S+\s+OP\s+([A-DX]|[A-D],[A-Z]|[A-D];[A-Z])\s*$")


def parse_mcas(txt_path: Path, source_url: str) -> list[dict]:
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    # answer table for short-answer
    table_keys: dict[int, str] = {}
    table_std: dict[int, str] = {}
    table = text.split("Released Operational Items")[-1].split("Unreleased")[0]
    for m in re.finditer(
        r"^\s+(\d+)\s+\d+\s+.*?(\d+\.[A-Z]+\.[A-Z]\.\d+)\s+(SR|SA|CR)\s+([A-D0-9][A-D0-9,;.]*)?",
        table,
        re.M,
    ):
        q = int(m.group(1))
        table_std[q] = m.group(2)
        ans = (m.group(4) or "").strip()
        if ans and m.group(3) in {"SR", "SA"} and "," not in ans and ";" not in ans:
            table_keys[q] = ans

    body = text.split("SESSION 1")[1] if "SESSION 1" in text else text
    body = body.split("Spring 2019 Released Operational Items")[0]
    lines = [ln.rstrip() for ln in body.splitlines()]

    STOP = (
        "enter your answer",
        "this question has",
        "session 2",
        "directions",
        "reference sheet",
        "you may use your",
    )

    chunks: list[tuple[str, list[str]]] = []
    cur_key: str | None = None
    cur_lines: list[str] = []
    for ln in lines:
        hm = re.match(r"^MA\S+\s+OP\s+(\S+)\s*$", ln.strip())
        if hm:
            if cur_key is not None:
                chunks.append((cur_key, cur_lines))
            cur_key = hm.group(1)
            cur_lines = []
            continue
        if cur_key is not None:
            low = ln.strip().lower()
            if any(low.startswith(s) for s in STOP):
                continue
            cur_lines.append(ln)
    if cur_key is not None:
        chunks.append((cur_key, cur_lines))

    rows: list[dict] = []
    n = 0
    for published_key, block in chunks:
        n += 1
        cleaned: list[str] = []
        for ln in block:
            s = re.sub(r"^[a-z]\s+", "", ln.strip())
            if not s:
                continue
            if re.fullmatch(r"[a-z]", s):
                continue
            if s.startswith("Mathematics") or re.fullmatch(r"\d{3}", s):
                continue
            if s.startswith("\\") or re.fullmatch(r"[0-9\\–.•\s-]+", s):
                continue
            cleaned.append(s)
        choices: dict[str, str] = {}
        stem_parts: list[str] = []
        cur: str | None = None
        for ln in cleaned:
            cm = re.match(r"^([A-D])\s+(.*)$", ln)
            if cm:
                letter = cm.group(1)
                rest = cm.group(2).strip()
                choices[letter] = rest
                cur = letter
                continue
            if cur and ln and letter_count(choices) < 4:
                if re.match(r"^[A-D]\b", ln):
                    continue
                choices[cur] = (choices[cur] + " " + ln).strip()
                continue
            if not cur:
                stem_parts.append(ln)
        stem = clean_ws(" ".join(p for p in stem_parts if p))
        stem = re.sub(r"^[qwertyuiopasdfghjklzxcvbnm]\s+", "", stem)
        qid = f"mcas-2019-7-i{n}"
        std = table_std.get(n, "7")
        if (
            published_key in {"A", "B", "C", "D"}
            and len(choices) == 4
            and all(choice_ok(v) and len(v) < 160 for v in choices.values())
            and 20 < len(stem) < 700
        ):
            rows.append(
                {
                    "id": qid,
                    "corpus": "mcas",
                    "authority": "ccss",
                    "claim": std,
                    "stem": stem,
                    "choices": {k: clean_ws(v) for k, v in choices.items()},
                    "key": published_key,
                    "responseType": "selected",
                    "sourceUrl": source_url,
                    "licenseNote": "Massachusetts DESE MCAS Spring 2019 Grade 7 Mathematics released items. Public.",
                    "grade": "7",
                    "role": "target",
                }
            )
        elif published_key == "X":
            ans = table_keys.get(n)
            stem_short = stem.split("completely fill")[0].strip()
            if ans and re.fullmatch(r"-?\d+(?:\.\d+)?", ans) and 15 < len(stem_short) < 240:
                rows.append(
                    {
                        "id": qid,
                        "corpus": "mcas",
                        "authority": "ccss",
                        "claim": std,
                        "stem": stem_short,
                        "key": ans,
                        "responseType": "numeric",
                        "sourceUrl": source_url,
                        "licenseNote": "Massachusetts DESE MCAS Spring 2019 Grade 7 Mathematics released items. Public.",
                        "grade": "7",
                        "role": "target",
                    }
                )
    print(f"mcas: {len(rows)} from {len(chunks)} chunks")
    return rows


def letter_count(choices: dict[str, str]) -> int:
    return len(choices)


def main() -> None:
    nysed = []
    nysed += parse_nysed(
        "6",
        RAW / "nysed-2019-g6.txt",
        "https://www.nysedregents.org/ei/math/2019/english/2019-released-items-math-g6.pdf",
        "2019",
    )
    nysed += parse_nysed(
        "7",
        RAW / "nysed-2019-g7.txt",
        "https://www.nysedregents.org/ei/math/2019/english/2019-released-items-math-g7.pdf",
        "2019",
    )
    nysed += parse_nysed(
        "8",
        RAW / "nysed-2019-g8.txt",
        "https://www.nysedregents.org/ei/math/2019/english/2019-released-items-math-g8.pdf",
        "2019",
    )
    for grade in ("6", "7", "8"):
        txt = RAW / f"nysed-2018-g{grade}.txt"
        if txt.exists():
            nysed += parse_nysed(
                grade,
                txt,
                f"https://www.nysedregents.org/ei/math/2018/english/2018-released-items-math-g{grade}.pdf",
                "2018",
            )
    dump(ROOT / "data" / "nysed.jsonl", nysed)

    # STAAR selected items are transcribed in write_staar_items.py
    # (two-column item-analysis bleed breaks automatic choice recovery).
    # MCAS selected/numeric items are transcribed in write_mcas_items.py
    # (layout glyphs break automatic choice recovery).


if __name__ == "__main__":
    main()
