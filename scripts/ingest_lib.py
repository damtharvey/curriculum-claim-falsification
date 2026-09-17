#!/usr/bin/env python3
"""Shared helpers for CHAT public-item ingest. Never invent stems, choices, or keys."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"
LOG = ROOT / "ingest-log.md"


def clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def choice_ok(text: str) -> bool:
    t = clean_ws(text)
    if len(t) < 1:
        return False
    if t in {"A", "B", "C", "D", "E", "F", "G", "H", "J", "1", "2", "3", "4"}:
        return False
    return True


def append_log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if not LOG.exists():
        LOG.write_text(
            "# Ingest log\n\nEvery attempted URL and outcome. No deposits. Items not invented.\n\n",
            encoding="utf-8",
        )
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")


def download_url(url: str, dest: Path, timeout: int = 90) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 500:
        rec = {"url": url, "dest": str(dest.relative_to(ROOT)), "outcome": "exists", "bytes": dest.stat().st_size}
        append_log(f"- exists {url} -> {dest.name} ({dest.stat().st_size} bytes)")
        return rec
    cmd = [
        "curl",
        "-fsSL",
        "-A",
        "Mozilla/5.0 (compatible; CHAT-research/1.0; academic ingest of public released tests)",
        "--retry",
        "2",
        "--max-time",
        str(timeout),
        "-o",
        str(dest),
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
        if dest.exists() and dest.stat().st_size < 200:
            dest.unlink(missing_ok=True)
        rec = {
            "url": url,
            "dest": str(dest.relative_to(ROOT)),
            "outcome": "fail",
            "error": (proc.stderr or proc.stdout or "empty")[:300],
        }
        append_log(f"- FAIL {url} :: {rec['error'][:120]}")
        return rec
    rec = {"url": url, "dest": str(dest.relative_to(ROOT)), "outcome": "ok", "bytes": dest.stat().st_size}
    append_log(f"- ok {url} -> {dest.name} ({dest.stat().st_size} bytes)")
    return rec


def archive_url(url: str) -> str:
    return f"https://web.archive.org/web/2020/{url}"


def extract_pdf_text(path: Path) -> str:
    import fitz  # pymupdf

    doc = fitz.open(path)
    parts: list[str] = []
    for i, page in enumerate(doc):
        parts.append(f"\n\n---PAGE {i + 1}---\n")
        parts.append(page.get_text("text"))
    doc.close()
    return "".join(parts)


def extract_pdf_pages(path: Path) -> list[str]:
    import fitz

    doc = fitz.open(path)
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return pages


def render_page_png(pdf_path: Path, page_index: int, out_path: Path, dpi: int = 150) -> Path:
    import fitz

    doc = fitz.open(pdf_path)
    page = doc[page_index]
    pix = page.get_pixmap(dpi=dpi)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(out_path))
    doc.close()
    return out_path


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def base_item(
    *,
    item_id: str,
    corpus: str,
    authority: str,
    claim: str,
    stem: str,
    key: str,
    response_type: str,
    source_url: str,
    license_note: str,
    year: str,
    grade: str,
    choices: dict[str, str] | None = None,
    official_tag: str | None = None,
    figure_dependent: bool = False,
    transcription_method: str = "text-layer",
    page_pointer: str | None = None,
    figure: dict[str, Any] | None = None,
    percent_correct: float | None = None,
    content_domain: str | None = None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "id": item_id,
        "corpus": corpus,
        "authority": authority,
        "claim": claim,
        "stem": stem,
        "key": key,
        "responseType": response_type,
        "sourceUrl": source_url,
        "licenseNote": license_note,
        "role": "target",
        "year": year,
        "grade": grade,
        "figureDependent": figure_dependent,
        "transcriptionMethod": transcription_method,
    }
    if choices is not None:
        rec["choices"] = choices
    if official_tag:
        rec["officialTag"] = official_tag
    if page_pointer:
        rec["pagePointer"] = page_pointer
    if figure:
        rec["figure"] = figure
    if percent_correct is not None:
        rec["percentCorrect"] = percent_correct
    if content_domain:
        rec["contentDomain"] = content_domain
    return rec
