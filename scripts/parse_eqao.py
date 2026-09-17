#!/usr/bin/env python3
"""Parse EQAO grades 3, 6, 9 released math items that have published keys. Never invent stems, choices, or keys."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import (  # noqa: E402
    DATA,
    RAW,
    append_log,
    archive_url,
    base_item,
    choice_ok,
    clean_ws,
    download_url,
    dump_jsonl,
    extract_pdf_pages,
)

LICENSE = (
    "EQAO released mathematics questions. Public. Ontario curriculum tags, not CCSS. "
    "SOURCE: Education Quality and Accountability Office released-question PDFs."
)
EQAO_DIR = RAW / "eqao"
OUT = DATA / "eqao.jsonl"
QHEAD = re.compile(
    r"\(\s*(\d{1,2})\s*\)\s*(Knowledge and Understanding|Application|Thinking)\s*",
    re.I,
)
SKILL_ABBR = {
    "knowledge and understanding": "KU",
    "application": "AP",
    "thinking": "TH",
}
EXPECT_RE = re.compile(r"^([B-F])(\d)\.\s+(\S.*)$")
KEY_LINE = re.compile(
    r"^\s*(\d{1,2})\s+([A-F]\d)\s+(KU|AP|TH)\s+(\*|([A-F](?:\s*,\s*[A-F])*))\s*$"
)
KEY_BLOCK = re.compile(
    r"(?m)^(\d{1,2})\s*\n([A-F]\d)\s*\n(KU|AP|TH)\s*\n(\*|([A-F](?:\s*,\s*[A-F])*))\s*$"
)
NOISE = re.compile(
    r"(?i)^(EQAO |Education Quality|Information Centre|e-mail|info@|"
    r"©|November 20|January 20|eqao\.com|Resource:|Released Questions|"
    r"These (questions|released)|This resource is provided|"
    r"QUESTIONS WITH ANSWERS|DETAILS OF THE QUESTIONS|Sample Data|"
    r"English-Language Schools|French-Language Schools|"
    r"Currently there are no EQAO)"
)
FIGURE_WORDS = re.compile(
    r"\b(graph|diagram|figure|pictograph|number line|this table|this code|"
    r"coding pieces|shown)\b",
    re.I,
)
KNOWN_PDFS = [
    "https://www.eqao.com/wp-content/uploads/2025/11/math-resource-released-questions-g9-25.pdf",
    "https://www.eqao.com/wp-content/uploads/2025/11/math-resource-released-questions-g6-2025.pdf",
    "https://www.eqao.com/wp-content/uploads/2025/11/math-resource-released-questions-g3-2025.pdf",
    "https://www.eqao.com/wp-content/uploads/2025/01/math-resource-released-questions-g6-2024.pdf",
    "https://www.eqao.com/wp-content/uploads/2025/01/math-resource-released-questions-g3-2024.pdf",
    "https://www.eqao.com/wp-content/uploads/2023/11/math-resource-released-questions-g9-2023.pdf",
    "https://www.eqao.com/wp-content/uploads/2023/11/math-resource-released-questions-g6-2023.pdf",
    "https://www.eqao.com/wp-content/uploads/2023/11/math-resource-released-questions-g3-2023.pdf",
    "https://www.eqao.com/wp-content/uploads/2020/10/math-resource-released-questions-g9-24.pdf",
]


def dest_for(url: str) -> Path:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", url.rstrip("/").split("/")[-1].split("?")[0])
    return EQAO_DIR / name


def fetch_pdfs() -> None:
    EQAO_DIR.mkdir(parents=True, exist_ok=True)
    if not any(EQAO_DIR.glob("*.pdf")):
        append_log("- EQAO raw PDFs empty; running listed fetches")
    for url in KNOWN_PDFS:
        dest = dest_for(url)
        rec = download_url(url, dest)
        if rec["outcome"] == "fail":
            rec = download_url(archive_url(url), dest)
            rec["via"] = "archive-2020"
        if rec["outcome"] == "fail":
            rec = download_url(f"https://web.archive.org/web/{url}", dest)
            rec["via"] = "archive-latest"
        if rec["outcome"] == "fail":
            append_log(f"- FAIL EQAO {url}")


def pages_blob(path: Path) -> str:
    pages = extract_pdf_pages(path)
    parts: list[str] = []
    for i, page in enumerate(pages):
        parts.append(f"\n\n---PAGE {i + 1}---\n")
        parts.append(page)
    return "".join(parts)


def page_at(blob: str, pos: int) -> int:
    marker = blob.rfind("---PAGE ", 0, pos)
    if marker < 0:
        return 1
    m = re.match(r"---PAGE (\d+)---", blob[marker:])
    return int(m.group(1)) if m else 1


def grade_year_from_name(name: str) -> tuple[str, str]:
    low = name.lower()
    gm = re.search(r"g([369])", low)
    grade = gm.group(1) if gm else "unknown"
    if re.search(r"g[369]-25\b", low) or "2025" in low:
        year = "2025"
    elif re.search(r"g[369]-24\b", low) or "2024" in low:
        year = "2024"
    elif "2023" in low:
        year = "2023"
    else:
        ym = re.search(r"(20[12][0-9])", low)
        year = ym.group(1) if ym else "unknown"
    return grade, year


def parse_key_table(text: str) -> dict[int, tuple[str, str, str]]:
    """q -> (key, expectation, skill). Skip star keys."""
    keys: dict[int, tuple[str, str, str]] = {}
    idx = text.find("DETAILS OF THE QUESTIONS")
    if idx < 0:
        return keys
    body = text[idx:]
    cut = body.find("* See next")
    if cut > 0:
        body = body[:cut]
    cut = body.find("* Solution")
    if cut > 0:
        body = body[:cut]
    for m in KEY_BLOCK.finditer(body):
        q = int(m.group(1))
        exp = m.group(2)
        skill = m.group(3)
        key = m.group(4).replace(" ", "")
        if "*" in key:
            continue
        keys[q] = (key.replace(" ", ""), exp, skill)
    for raw in body.splitlines():
        m = KEY_LINE.match(raw.strip())
        if not m:
            continue
        q = int(m.group(1))
        if "*" in m.group(4):
            continue
        keys[q] = (re.sub(r"\s+", "", m.group(4)), m.group(2), m.group(3))
    return keys


def parse_keys_from_answers(text: str) -> dict[int, str]:
    idx = text.find("QUESTIONS WITH ANSWERS")
    if idx < 0:
        return {}
    body = text[idx:]
    keys: dict[int, str] = {}
    matches = list(QHEAD.finditer(body))
    for i, m in enumerate(matches):
        q = int(m.group(1))
        end = matches[i + 1].start() if i + 1 < len(matches) else min(len(body), m.end() + 2000)
        window = body[m.end() : end]
        fc = re.search(r"Fully Correct\s*\(([A-D](?:\s+and\s+[A-D])+)\)", window)
        if fc:
            letters = re.findall(r"[A-D]", fc.group(1))
            if letters:
                keys[q] = ",".join(letters)
                continue
        lead = re.split(
            r"(?i)English-Language|French-Language|No\s+Response|Below\s+Level|Among students",
            window,
            maxsplit=1,
        )[0]
        dotted = re.search(r"(?m)^([A-D])\.\s+\S", lead)
        if dotted:
            keys[q] = dotted.group(1)
            continue
        lead_m = re.match(r"\s*([A-D])(?:\s*\.|\s+)\s*", lead)
        if lead_m:
            keys[q] = lead_m.group(1)
    return keys


def split_questions_region(text: str) -> str:
    start = re.search(r"\nQUESTIONS\b", text)
    if not start:
        return text
    marker = text.rfind("---PAGE ", 0, start.start())
    begin = marker if marker >= 0 else start.start()
    body = text[begin:]
    for stop in ("DETAILS OF THE QUESTIONS", "QUESTIONS WITH ANSWERS"):
        idx = body.find(stop)
        if idx > 200:
            body = body[:idx]
            break
    return body


def parse_question_blocks(region: str) -> tuple[dict[int, dict[str, Any]], dict[int, int]]:
    """q -> {stem, choices, skill, expectation} and q -> page."""
    items: dict[int, dict[str, Any]] = {}
    pages: dict[int, int] = {}
    last_exp = ""
    matches = list(QHEAD.finditer(region))
    for i, m in enumerate(matches):
        q = int(m.group(1))
        skill = SKILL_ABBR[m.group(2).lower()]
        end = matches[i + 1].start() if i + 1 < len(matches) else len(region)
        pre = region[matches[i - 1].end() if i else 0 : m.start()]
        for ln in pre.splitlines():
            em = EXPECT_RE.match(ln.strip())
            if em:
                last_exp = em.group(1) + em.group(2)
        same = region[m.end() : end]
        stem, choices = parse_stem_choices(same)
        items[q] = {
            "stem": stem,
            "choices": choices,
            "skill": skill,
            "expectation": last_exp,
        }
        pages[q] = page_at(region, m.start())
    return items, pages


def parse_stem_choices(block: str) -> tuple[str, dict[str, str]]:
    lines: list[str] = []
    for raw in block.splitlines():
        s = raw.strip()
        if not s or re.fullmatch(r"---PAGE \d+---", s):
            continue
        if NOISE.match(s):
            continue
        if re.fullmatch(r"\d{1,3}", s) and not lines:
            continue
        if EXPECT_RE.match(s) or re.match(r"^[B-F]\.\s+[A-Z]", s):
            break
        if s.endswith("(continued)"):
            break
        if re.match(
            r"(?i)^(use knowledge|demonstrate an|identify, describe|apply an|"
            r"apply coding|represent and compare|manage, analyse|solve problems|"
            r"Currently there)",
            s,
        ):
            break
        if re.fullmatch(r"[0-9−\-–.\sxyXY,]+", s) and sum(ch.isdigit() for ch in s) >= 6:
            break
        lines.append(s)
    start: int | None = None
    for i, s in enumerate(lines):
        if re.match(r"^[A-F][.)]\s+\S", s) or re.fullmatch(r"[A-F]", s):
            start = i
            break
    if start is None:
        return clean_ws(" ".join(lines)), {}
    stem = clean_ws(" ".join(lines[:start]))
    choices: dict[str, str] = {}
    cur: str | None = None
    for s in lines[start:]:
        dotted = re.match(r"^([A-F])[.)]\s+(\S.*)$", s)
        alone = re.fullmatch(r"([A-F])", s)
        if dotted:
            letter = dotted.group(1)
            if letter not in choices:
                choices[letter] = dotted.group(2).strip()
                cur = letter
            continue
        if alone:
            letter = alone.group(1)
            if letter not in choices:
                choices[letter] = ""
                cur = letter
            continue
        if cur is not None:
            choices[cur] = (choices[cur] + " " + s).strip()
    cleaned: dict[str, str] = {}
    for k, v in choices.items():
        text = clean_ws(v)
        text = re.split(
            r"(?i)\b(use knowledge of|demonstrate an understanding|"
            r"identify, describe|for this overall expectation)\b",
            text,
        )[0].strip()
        if choice_ok(text) and 1 <= len(text) <= 280:
            cleaned[k] = text
    return stem, cleaned


def key_letters(key: str) -> list[str]:
    return re.findall(r"[A-F]", key)


def build_item(
    *,
    q: int,
    grade: str,
    year: str,
    stem: str,
    choices: dict[str, str],
    key: str,
    expectation: str,
    skill: str,
    source_url: str,
    page: int,
    fname: str,
    skips: list[str],
) -> dict[str, Any] | None:
    letters = key_letters(key)
    if not letters:
        skips.append(f"{fname} q{q} missing-key")
        return None
    if len(stem) < 18:
        skips.append(f"{fname} q{q} short-stem")
        return None
    if len(choices) < 3:
        skips.append(f"{fname} q{q} figure-only-or-incomplete-choices")
        return None
    if any(let not in choices for let in letters):
        skips.append(f"{fname} q{q} key-letter-not-in-choices {key}")
        return None
    fig = bool(FIGURE_WORDS.search(stem))
    claim = f"g{grade}"
    tag = f"{expectation}-{skill}" if expectation else skill
    rec = base_item(
        item_id=f"eqao-{year}-g{grade}-q{q}",
        corpus="eqao",
        authority="eqao",
        claim=claim,
        stem=stem,
        key=key if "," not in key else key,
        response_type="selected",
        source_url=source_url,
        license_note=LICENSE,
        year=year,
        grade=grade,
        choices=choices,
        official_tag=tag,
        figure_dependent=fig,
        transcription_method="text-layer",
        page_pointer=f"{fname}:p{page}",
    )
    return rec


def source_for(name: str) -> str:
    low = name.lower()
    mapping = {Path(u).name.lower(): u for u in KNOWN_PDFS}
    for fname, url in mapping.items():
        if fname.replace("%20", "_") == low or fname == low:
            return url
    return f"https://www.eqao.com/{name}"


def main() -> None:
    fetch_pdfs()
    pdfs = sorted(p for p in EQAO_DIR.glob("*.pdf") if p.is_file())
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    skips: list[str] = []
    for pdf in pdfs:
        grade, year = grade_year_from_name(pdf.name)
        if grade not in {"3", "6", "9"}:
            append_log(f"- skip EQAO name {pdf.name}")
            continue
        try:
            blob = pages_blob(pdf)
        except Exception as exc:  # noqa: BLE001
            append_log(f"- FAIL EQAO parse {pdf.name}: {exc}")
            continue
        table = parse_key_table(blob)
        answers = parse_keys_from_answers(blob)
        region = split_questions_region(blob)
        blocks, pages = parse_question_blocks(region)
        kept = 0
        for q, block in sorted(blocks.items()):
            key = ""
            exp = block["expectation"]
            skill = block["skill"]
            if q in table:
                key, exp_t, skill_t = table[q]
                exp = exp or exp_t
                skill = skill or skill_t
            elif q in answers:
                key = answers[q]
            else:
                skips.append(f"{pdf.name} q{q} missing-key")
                continue
            rec = build_item(
                q=q,
                grade=grade,
                year=year,
                stem=block["stem"],
                choices=block["choices"],
                key=key,
                expectation=exp,
                skill=skill,
                source_url=source_for(pdf.name),
                page=pages.get(q, 1),
                fname=pdf.name,
                skips=skips,
            )
            if rec is None:
                continue
            if rec["id"] in seen:
                continue
            seen.add(rec["id"])
            rows.append(rec)
            kept += 1
        print(f"{pdf.name} grade={grade} year={year} kept={kept} questions={len(blocks)} table={len(table)} answers={len(answers)}")
        append_log(f"- parse {pdf.name} kept {kept} of {len(blocks)} questions")
    dump_jsonl(OUT, rows)
    miss = [s for s in skips if "missing-key" in s]
    fig = [s for s in skips if "figure-only" in s or "incomplete-choices" in s]
    append_log(
        f"- EQAO wrote {len(rows)} sample={ [r['id'] for r in rows[:8]] } "
        f"missing_keys={len(miss)} figure_or_choices={len(fig)}"
    )
    print(f"wrote {len(rows)} -> {OUT}")
    print("sample ids:", [r["id"] for r in rows[:12]])
    print("blockers missing-key", len(miss), "figure/choices", len(fig), "skips", len(skips))
    for s in skips[:30]:
        print(" skip", s)


if __name__ == "__main__":
    main()
