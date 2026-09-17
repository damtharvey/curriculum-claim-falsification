#!/usr/bin/env python3
"""Parse PISA 2003/2006/2012 released mathematics PDFs. Never invent stems, choices, or keys."""

from __future__ import annotations

import json
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
    "OECD PISA released mathematics items. Public with acknowledgement. "
    "SOURCE: OECD/NCES/ACER public-release PDFs."
)
PISA_DIR = RAW / "pisa"
OUT = DATA / "pisa.jsonl"
EXISTING = DATA / "pisa2012.jsonl"

ID_RE = re.compile(r"\b(P?M\d{2,4}[A-Z]?Q\d{2})\b")
QUESTION_HEAD = re.compile(
    r"Question\s+(\d+)\s*:\s*([A-Z][A-Z0-9 ,\-'/]+?)\s*\n\s*(P?M\d{2,4}[A-Z]?Q\d{2})\b",
)
PROCESS_RE = re.compile(r"Process:\s*(Formulate|Employ|Interpret)\b", re.I)
CONTENT_RE = re.compile(r"Mathematical content area:\s*([A-Za-z][A-Za-z /&-]+)", re.I)
CLUSTER_RE = re.compile(
    r"(reproduction|connections|reflection)\s+competency\s+cluster",
    re.I,
)
OECD_PCT = re.compile(r"OECD average:\s*(\d+)\s*%", re.I)
FULL_CREDIT = re.compile(
    r"Full\s+Credit\s+Code\s+\d+\s*:\s*(.{0,160})|"
    r"Full\s+credit(?:\s+Code\s+\d+\s*:)?\s*(.{0,160})|"
    r"Correct\s*(?:Answer\s*)?(?:[:\n]\s*)(.{0,160})",
    re.I,
)
NOISE_LINE = re.compile(
    r"(?i)^(PISA 2012 Released Items|ReleasedPISAItems|Mathematics Literacy|"
    r"Page \d+|Translation Note:|UNIT NAME|TABLE OF CONTENTS|"
    r"TAKE THE TEST:|ISBN |© OECD)"
)
FIGURE_WORDS = re.compile(
    r"\b(graph|diagram|chart|figure|pictograph|map|plan of the)\b",
    re.I,
)

EXTRA_URLS = [
    "https://www.acer.org/files/pisa_relitems_maths_2.pdf",
    "https://nces.ed.gov/surveys/pisa/pdf/items_math.pdf",
]


def dest_for(url: str) -> Path:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", url.rstrip("/").split("/")[-1].split("?")[0])
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return PISA_DIR / name


def fetch_missing() -> None:
    PISA_DIR.mkdir(parents=True, exist_ok=True)
    for url in EXTRA_URLS:
        dest = dest_for(url)
        rec = download_url(url, dest)
        if rec["outcome"] == "fail":
            rec = download_url(archive_url(url), dest)
            rec["via"] = "archive.org"
            append_log(f"- archive retry {url} -> {rec['outcome']}")


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


def strip_noise(text: str) -> str:
    keep: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            keep.append("")
            continue
        if NOISE_LINE.match(s):
            continue
        if re.fullmatch(r"---PAGE \d+---", s):
            keep.append(s)
            continue
        keep.append(raw.rstrip())
    return "\n".join(keep)


def letter_key(credit: str) -> str | None:
    head = credit.strip()
    if re.match(r"(?i)(correct substitution|partial|other responses|missing)", head):
        return None
    m = re.match(r"(?i)(?:answer\s+)?([A-E])\b", head)
    if m:
        return m.group(1).upper()
    return None


def numeric_key(credit: str) -> str | None:
    head = credit.strip()
    if re.search(
        r"(?i)(correct substitution|correct method|correct drawing|correct rule|"
        r"correct response|valid argument|adequate explanation|all \d|"
        r"exactly \d|both |table|graph shows|indicated|interval|identify|"
        r"explain|newspaper|any time|from \d|fill in)",
        head[:90],
    ):
        return None
    if letter_key(head):
        return None
    m = re.match(r"(?i)(?:yes|no)\b", head)
    if m:
        if re.search(r"(?i)(explain|argument|because|with |and give|example)", head[:100]):
            return None
        return m.group(0).capitalize()
    m = re.match(
        r"^(?:about\s+|approximately\s+|accept\s+)?([0-9]+(?:\s[0-9]{3})*(?:\.[0-9]+)?)",
        head,
        re.I,
    )
    if not m:
        return None
    val = m.group(1).replace(" ", "")
    if val in {"9", "99", "0"}:
        return None
    return val


def parse_credit(scoring: str) -> tuple[str | None, str]:
    """Return (key, response_type_guess) from a scoring block."""
    chunk = scoring
    m = re.search(
        r"Full\s+[Cc]redit\s*(?:Code\s+\d+\s*:)?\s*(.{0,200})",
        chunk,
        re.I | re.S,
    )
    if not m:
        m = re.search(r"(?i)Correct\s*(?:\n|\s{1,3})(?:Answer\s*)?(.{0,180})", chunk)
    if not m:
        return None, "constructed"
    credit = clean_ws(m.group(1))
    credit = re.sub(r"(?i)^Code\s+\d+\s*:\s*", "", credit)
    credit = re.split(r"(?i)\b(No Credit|Partial credit|Incorrect|Percentage of students)\b", credit)[0]
    lk = letter_key(credit)
    if lk:
        return lk, "selected"
    nk = numeric_key(credit)
    if nk:
        return nk, "numeric"
    return None, "constructed"


def clean_stem(stem: str) -> str:
    stem = clean_ws(stem)
    stem = re.sub(r"^[-–—−]\s*(?:\d+\s+)+", "", stem)
    stem = re.sub(r"(?i)^Question intent:\s*[A-Za-z /&-]+\s+", "", stem)
    return clean_ws(stem)


def extract_choices(block: str) -> tuple[str, dict[str, str]]:
    lines = [ln.rstrip() for ln in block.splitlines()]
    start: int | None = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if re.match(r"^[A-E][.)]\s+\S", s):
            start = i
            break
        if re.fullmatch(r"[A-E]", s):
            start = i
            break
    if start is None:
        stem = clean_ws(" ".join(ln.strip() for ln in lines if ln.strip() and not re.fullmatch(r"---PAGE \d+---", ln.strip())))
        return clean_stem(stem), {}
    stem = clean_ws(
        " ".join(
            ln.strip()
            for ln in lines[:start]
            if ln.strip() and not re.fullmatch(r"---PAGE \d+---", ln.strip())
        )
    )
    choices: dict[str, str] = {}
    cur: str | None = None
    for ln in lines[start:]:
        s = ln.strip()
        if not s or re.fullmatch(r"---PAGE \d+---", s):
            continue
        dotted = re.match(r"^([A-E])[.)]\s+(\S.*)$", s)
        alone = re.fullmatch(r"([A-E])", s)
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
            if choices[cur] and re.fullmatch(r"[0-9][0-9,.\s%]*", choices[cur]) and not re.match(r"^[0-9]", s):
                cur = None
                continue
            choices[cur] = (choices[cur] + " " + s).strip()
    cleaned = {k: clean_ws(v) for k, v in choices.items() if choice_ok(v) and len(clean_ws(v)) <= 280}
    return clean_stem(stem), cleaned


def unit_from_header(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().upper()


def build_cluster_map(take_text: str) -> dict[tuple[str, int], str]:
    """Map (unit name, question index) to reproduction|connections|reflection."""
    out: dict[tuple[str, int], str] = {}
    starts = list(re.finditer(r"([A-Z][A-Z0-9 /'\-]{2,48}?)\s+SCORING\s+(\d+)\.(\d+)", take_text))
    for i, m in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else min(len(take_text), m.end() + 2500)
        window = take_text[m.end() : end]
        unit = unit_from_header(m.group(1))
        tokens = [t for t in unit.split() if re.fullmatch(r"[A-Z']+", t)]
        if not tokens:
            continue
        unit_key = " ".join(tokens[-5:])
        qn = int(m.group(3))
        cl = CLUSTER_RE.search(window)
        if not cl:
            continue
        val = cl.group(1).lower()
        out[(unit_key, qn)] = val
        out[(tokens[-1], qn)] = val
        if len(tokens) >= 2:
            out[(" ".join(tokens[-2:]), qn)] = val
    return out


def recover_process(scoring: str, unit: str, qn: int, clusters: dict[tuple[str, int], str]) -> str | None:
    pm = PROCESS_RE.search(scoring)
    if pm:
        return pm.group(1).lower()
    cm = CLUSTER_RE.search(scoring)
    if cm:
        return cm.group(1).lower()
    u = unit_from_header(unit)
    tokens = [t for t in u.split() if t]
    candidates = [u]
    if tokens:
        candidates.append(tokens[-1])
        if len(tokens) >= 2:
            candidates.append(" ".join(tokens[-2:]))
    for key in candidates:
        if (key, qn) in clusters:
            return clusters[(key, qn)]
    last = tokens[-1] if tokens else ""
    for (uname, uq), val in clusters.items():
        if uq != qn:
            continue
        if last and (uname == last or uname.endswith(" " + last) or last.endswith(uname.split()[-1])):
            return val
    return None


def year_for(code: str, default: str, in_2012: set[str], in_2003: set[str]) -> str:
    if code.startswith("PM") or code in in_2012:
        return "2012"
    if code in in_2003:
        return "2003"
    return default


def parse_question_pdf(
    path: Path,
    source_url: str,
    default_year: str,
    clusters: dict[tuple[str, int], str],
    in_2012: set[str],
    in_2003: set[str],
    skips: list[str],
) -> list[dict[str, Any]]:
    try:
        blob = strip_noise(pages_blob(path))
    except Exception as exc:  # noqa: BLE001
        append_log(f"- FAIL parse {path.name}: {exc}")
        return []
    rows: list[dict[str, Any]] = []
    matches = list(QUESTION_HEAD.finditer(blob))
    for i, m in enumerate(matches):
        qn = int(m.group(1))
        unit = clean_ws(m.group(2))
        code = m.group(3)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
        chunk = blob[start:end]
        score_m = re.search(
            rf"(?:UNIT\s+)?{re.escape(unit)}\s+SCORING\s+{qn}\b|"
            rf"{re.escape(unit.split()[0])}\s+SCORING\s+{qn}\b|"
            r"\bSCORING:\s",
            chunk,
            re.I,
        )
        if score_m:
            body = chunk[: score_m.start()]
            scoring = chunk[score_m.start() :]
        else:
            body, scoring = chunk, chunk
        key, guessed_type = parse_credit(scoring)
        if not key:
            skips.append(f"missing-key {code} {path.name}")
            continue
        stem, choices = extract_choices(body)
        stem = re.sub(r"\s*Show your (work|calculation).*$", "", stem, flags=re.I)
        if len(stem) < 20:
            skips.append(f"short-stem {code} {path.name}")
            continue
        figure_dep = bool(FIGURE_WORDS.search(stem + " " + unit))
        if guessed_type == "selected" or (len(choices) >= 3 and key in choices):
            if key not in "ABCDE":
                # numeric credit on an MC layout; keep numeric if no usable choices
                if len(choices) >= 3:
                    skips.append(f"key-not-letter {code} {path.name} key={key}")
                    continue
                response_type = "numeric"
                choices_out = None
            else:
                if len(choices) < 3 or key not in choices:
                    skips.append(f"choices-incomplete {code} {path.name}")
                    continue
                if not all(choice_ok(v) for v in choices.values()):
                    skips.append(f"figure-only-choices {code} {path.name}")
                    continue
                response_type = "selected"
                choices_out = choices
        else:
            if key in "ABCDE" and len(choices) >= 3 and key in choices:
                response_type = "selected"
                choices_out = choices
            elif re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", key) or key in {"Yes", "No"}:
                if key in {"Yes", "No"}:
                    skips.append(f"constructed-yesno {code} {path.name}")
                    continue
                if re.match(r"(?i)(explain |identify |fill in|complete the table)", stem):
                    skips.append(f"constructed-numeric {code} {path.name}")
                    continue
                response_type = "numeric"
                choices_out = None
            else:
                skips.append(f"constructed-no-simple-key {code} {path.name}")
                continue
        process = recover_process(scoring, unit, qn, clusters)
        content_m = CONTENT_RE.search(scoring)
        content = clean_ws(content_m.group(1)) if content_m else None
        if process is None and content:
            process = re.sub(r"[^a-z]+", "-", content.lower()).strip("-")
        if process is None:
            intent = re.search(r"QUESTION INTENT:\s*(.{0,80})", scoring, re.I)
            if intent and PROCESS_RE.search(intent.group(1)):
                process = PROCESS_RE.search(intent.group(1)).group(1).lower()  # type: ignore[union-attr]
        if process is None:
            skips.append(f"no-process {code} {path.name}")
            continue
        year = year_for(code, default_year, in_2012, in_2003)
        pct = None
        pm = OECD_PCT.search(scoring)
        if pm:
            pct = float(pm.group(1)) / 100.0
        page = page_at(blob, m.start())
        rec = base_item(
            item_id=f"pisa{year}-{code}",
            corpus="pisa",
            authority="pisa",
            claim=process,
            stem=stem,
            key=key,
            response_type=response_type,
            source_url=source_url,
            license_note=LICENSE,
            year=year,
            grade="15",
            choices=choices_out,
            official_tag=process if not content else f"{process}|{content}",
            figure_dependent=figure_dep,
            transcription_method="text-layer",
            page_pointer=f"{path.name}:p{page}",
            percent_correct=pct,
            content_domain=content,
        )
        rec["clusterId"] = f"pisa{year}-{code.split('Q', 1)[0]}"
        rows.append(rec)
    return rows


def nces_ids(text: str) -> set[str]:
    return set(ID_RE.findall(text))


def main() -> None:
    fetch_missing()
    skips: list[str] = []
    files = {
        "2012_oecd": PISA_DIR / "PISA_202012_20items_20for_20release_ENGLISH.pdf",
        "2012_nces": PISA_DIR / "items_math2012.pdf",
        "2006_oecd": PISA_DIR / "38709418.pdf",
        "2006_acer": PISA_DIR / "pisa_relitems_maths_2.pdf",
        "2003_nces": PISA_DIR / "items2_math.pdf",
        "2003_nces2": PISA_DIR / "items_math.pdf",
        "take_test": PISA_DIR / "Take_20the_20test_20e_20book.pdf",
    }
    clusters: dict[tuple[str, int], str] = {}
    if files["take_test"].exists():
        clusters = build_cluster_map(pages_blob(files["take_test"]))
        append_log(f"- PISA Take-the-Test competency map size {len(clusters)}")

    in_2012: set[str] = set()
    in_2003: set[str] = set()
    for key in ("2012_oecd", "2012_nces"):
        if files[key].exists():
            in_2012 |= nces_ids(pages_blob(files[key]))
    for key in ("2003_nces", "2003_nces2"):
        if files[key].exists():
            in_2003 |= nces_ids(pages_blob(files[key]))

    jobs: list[tuple[Path, str, str]] = []
    if files["2012_oecd"].exists():
        jobs.append(
            (
                files["2012_oecd"],
                "https://www.oecd.org/content/dam/oecd/en/about/programmes/edu/pisa/pisa-test/PISA%202012%20items%20for%20release_ENGLISH.pdf",
                "2012",
            )
        )
    if files["2006_oecd"].exists():
        jobs.append((files["2006_oecd"], "https://www.oecd.org/pisa/38709418.pdf", "2006"))
    if files["2006_acer"].exists():
        jobs.append((files["2006_acer"], "https://www.acer.org/files/pisa_relitems_maths_2.pdf", "2006"))
    if files["2003_nces"].exists():
        jobs.append((files["2003_nces"], "https://nces.ed.gov/surveys/pisa/pdf/items2_math.pdf", "2003"))
    if files["2003_nces2"].exists():
        jobs.append((files["2003_nces2"], "https://nces.ed.gov/surveys/pisa/pdf/items_math.pdf", "2003"))
    if files["2012_nces"].exists():
        jobs.append((files["2012_nces"], "https://nces.ed.gov/surveys/pisa/pdf/items_math2012.pdf", "2012"))

    rows: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    seen_ids: set[str] = set()
    for path, url, year in jobs:
        got = parse_question_pdf(path, url, year, clusters, in_2012, in_2003, skips)
        print(f"{path.name}: parsed {len(got)}")
        append_log(f"- parse {path.name} kept {len(got)}")
        for rec in got:
            code = rec["id"].split("-", 1)[-1]
            if code in seen_codes or rec["id"] in seen_ids:
                continue
            seen_codes.add(code)
            seen_ids.add(rec["id"])
            rows.append(rec)

    if EXISTING.exists():
        for line in EXISTING.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            code = rec["id"].split("-", 1)[-1]
            if rec["id"] in seen_ids or code in seen_codes:
                continue
            rec.setdefault("year", "2012")
            rec.setdefault("grade", "15")
            rec.setdefault("transcriptionMethod", "text-layer")
            rec.setdefault("figureDependent", bool(rec.get("figure")))
            rec.setdefault("officialTag", rec.get("claim"))
            rec.setdefault("pagePointer", "pisa2012.jsonl")
            seen_ids.add(rec["id"])
            seen_codes.add(code)
            rows.append(rec)

    dump_jsonl(OUT, rows)
    miss = [s for s in skips if s.startswith("missing-key")]
    fig = [s for s in skips if "figure-only" in s or "choices-incomplete" in s]
    nproc = [s for s in skips if s.startswith("no-process")]
    append_log(
        f"- PISA wrote {len(rows)} ids sample={ [r['id'] for r in rows[:8]] } "
        f"missing_keys={len(miss)} figure_or_choices={len(fig)} no_process={len(nproc)}"
    )
    print(f"wrote {len(rows)} -> {OUT}")
    print("sample ids:", [r["id"] for r in rows[:12]])
    print("blockers missing-key", len(miss), "figure/choices", len(fig), "no-process", len(nproc), "skips", len(skips))
    for s in skips[:25]:
        print(" skip", s)


if __name__ == "__main__":
    main()
