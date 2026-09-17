#!/usr/bin/env python3
"""Targeted fetch of missing English STAAR grade-5 test+key pairs. Logs every URL."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT
from parse_staar_bulk import grade_from_name, is_key_name, year_from_name

OUT_DIR = ROOT / "exports" / "replication-staar"
LOG_PATH = OUT_DIR / "fetch-log-g5.md"
HTML_DIR = RAW / "_html"
STAAR_DIR = RAW / "staar"
TEA_PAGES = [
    "https://tea.texas.gov/student-assessment/testing/staar/staar-released-test-questions",
    "https://tea.texas.gov/data-reports/staar/staar-released-test-questions",
]
TARGET_YEARS = ("2015", "2017", "2018", "2020", "2023")
CDX_QUERIES = [
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/STAAR_G5-2017-Test-Math-f.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Test.PDF&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2017_STAAR_Gr5Math_Key_Paper_tagged.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Key_Paper_tagged.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/STAAR-2015-Key-G5-Math.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2015_STAAR_Gr5_Math_Key_Paper_tagged.pdf&output=json&limit=5",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(line: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text(
            "# STAAR grade-5 missing-administration fetch log\n\n", encoding="utf-8"
        )
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")
    print(line)


def curl_body(url: str, dest: Path, timeout: int = 90) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = [
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
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size < 50:
        if dest.exists() and dest.stat().st_size < 50:
            dest.unlink(missing_ok=True)
        error = (proc.stderr or proc.stdout or "empty")[:300]
        return {"url": url, "outcome": "fail", "error": error, "dest": str(dest)}
    return {
        "url": url,
        "outcome": "ok",
        "bytes": dest.stat().st_size,
        "dest": str(dest),
    }


def archive_url(url: str, timestamp: str = "20201230223459") -> str:
    return f"https://web.archive.org/web/{timestamp}id_/{url}"


TARGET_URLS = [
    # 2017 English g5 math (TEA released-test page, archive 2020-12-30)
    "https://tea.texas.gov/sites/default/files/STAAR_G5-2017-Test-Math-f.pdf",
    "https://tea.texas.gov/sites/default/files/2017_STAAR_Gr5Math_Key_Paper_tagged.pdf",
    # 2018 English g5 math
    "https://tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Test.PDF",
    "https://tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    # 2015 English g5 math: test already on disk; key was missing from the 2020 table
    "https://tea.texas.gov/student-assessment/staar/released-test-questions/2015-staar-5-math-key.pdf",
    "https://tea.texas.gov/sites/default/files/2015-staar-5-math-key.pdf",
    "https://tea.texas.gov/sites/default/files/STAAR-2015-Key-G5-Math.pdf",
    "https://tea.texas.gov/sites/default/files/staar-2015-key-g5-math.pdf",
    "https://tea.texas.gov/sites/default/files/2015_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    "https://tea.texas.gov/sites/default/files/STAAR_G5-2015-Test-Math-f.pdf",
    "https://tea.texas.gov/sites/default/files/STAAR-G5-2015Test-Math.pdf",
    # 2020: COVID year; try the same filename family anyway
    "https://tea.texas.gov/sites/default/files/2020_STAAR_Gr5_Math_Test.PDF",
    "https://tea.texas.gov/sites/default/files/STAAR_G5-2020-Test-Math-f.pdf",
    "https://tea.texas.gov/sites/default/files/2020_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    "https://tea.texas.gov/student-assessment/staar/released-test-questions/2020-staar-5-math-test.pdf",
    "https://tea.texas.gov/student-assessment/staar/released-test-questions/2020-staar-5-math-key.pdf",
    # 2023: live TEA page has the key, not a PDF test form
    "https://tea.texas.gov/data-reports/staar/released-test-questions/2023-staar-math-grade-5-answer-key.pdf",
    "https://tea.texas.gov/data-reports/staar/released-test-questions/2023-staar-5-math-test.pdf",
    "https://tea.texas.gov/sites/default/files/2023-staar-5-math-test.pdf",
]


def rewrite_href(href: str, page_url: str) -> str:
    joined = urljoin(page_url, href).split("#")[0]
    archive_match = re.search(
        r"(?:https?://web\.archive\.org)?/web/\d+/https?://(.+)$", joined
    )
    if archive_match:
        return "https://" + archive_match.group(1)
    broken = re.search(r"https?://tea\.texas\.gov/web/\d+/https?://(.+)$", joined)
    if broken:
        return "https://" + broken.group(1)
    return joined


def is_english_grade5_math(url: str) -> bool:
    low = url.lower()
    if "spanish" in low or "rationale" in low or "sampler" in low:
        return False
    if "practice" in low or "redesign" in low or "item-analysis" in low:
        return False
    if "expectation" in low or "_online" in low:
        return False
    if "math" not in low and "mathematics" not in low:
        return False
    year = year_from_name(low)
    grade = grade_from_name(low)
    return year in TARGET_YEARS and grade == "5"


def dest_for(url: str) -> Path:
    name = Path(urlparse(url).path).name or "index.pdf"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return STAAR_DIR / name


def inspect_pdf(path: Path) -> dict[str, Any]:
    import fitz

    size = path.stat().st_size
    header = path.read_bytes()[:8]
    record: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "bytes": size,
        "startsWithPdfHeader": header.startswith(b"%PDF"),
        "pageCount": None,
        "alnumChars": 0,
        "textExtractable": False,
        "scanned": False,
        "openError": None,
    }
    if size == 1_048_576:
        record["likelyTruncated"] = True
    try:
        document = fitz.open(path)
        try:
            record["pageCount"] = document.page_count
            alnum = 0
            for page in document:
                alnum += sum(1 for char in page.get_text("text") if char.isalnum())
            record["alnumChars"] = alnum
            record["textExtractable"] = alnum >= 200
            record["scanned"] = header.startswith(b"%PDF") and alnum < 200
        finally:
            document.close()
    except Exception as exc:  # noqa: BLE001
        record["openError"] = str(exc)[:200]
    return record


def file_exists_ok(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 500


def try_download(url: str) -> dict[str, Any]:
    dest = dest_for(url)
    if file_exists_ok(dest):
        rec = {
            "url": url,
            "triedUrl": url,
            "dest": str(dest),
            "outcome": "exists",
            "bytes": dest.stat().st_size,
        }
        log(f"- exists {url} -> {dest.name} ({rec['bytes']} bytes)")
        return rec
    rec = curl_body(url, dest, timeout=60)
    rec["triedUrl"] = url
    rec["dest"] = str(dest)
    if rec["outcome"] == "fail":
        for stamp in ("20201230223459", "2020", "2018", "2019"):
            archived = archive_url(url, stamp)
            rec2 = curl_body(archived, dest, timeout=90)
            rec2["triedUrl"] = archived
            rec2["via"] = "archive.org"
            rec2["dest"] = str(dest)
            if rec2["outcome"] == "ok":
                log(f"- ok {archived} -> {dest.name} ({rec2.get('bytes')} bytes)")
                return rec2
            log(f"- FAIL {archived} :: {(rec2.get('error') or '')[:120]}")
        log(f"- FAIL {url} :: {(rec.get('error') or '')[:120]}")
        return rec2
    log(f"- ok {url} -> {dest.name} ({rec.get('bytes')} bytes)")
    return rec


def scrape_page(page_url: str, dest_name: str) -> list[str]:
    html_path = HTML_DIR / dest_name
    if file_exists_ok(html_path):
        log(f"- page exists {page_url}")
    else:
        rec = curl_body(page_url, html_path, timeout=60)
        log(f"- page {rec['outcome']} {page_url}")
        if rec["outcome"] not in {"ok", "exists"}:
            archived = archive_url(page_url)
            archive_path = HTML_DIR / f"aw_{dest_name}"
            rec2 = curl_body(archived, archive_path, timeout=90)
            log(f"- page {rec2['outcome']} {archived}")
            if rec2["outcome"] not in {"ok", "exists"}:
                return []
            html_path = archive_path
    html = html_path.read_text(encoding="utf-8", errors="replace")
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
    out: list[str] = []
    for href in hrefs:
        if href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        out.append(rewrite_href(href, page_url))
    return out


def cdx_search(query: str) -> list[str]:
    dest = HTML_DIR / ("cdx-" + hashlib_name(query) + ".json")
    rec = curl_body(query, dest, timeout=20)
    log(f"- cdx {rec['outcome']} {query[:180]}")
    if rec["outcome"] != "ok":
        return []
    try:
        payload = json.loads(dest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log(f"- cdx parse fail {exc}")
        return []
    urls: list[str] = []
    for row in payload[1:] if payload and isinstance(payload[0], list) else payload:
        if not row:
            continue
        original = row[0] if isinstance(row, list) else str(row)
        urls.append(original)
    log(f"- cdx rows {len(urls)}")
    return urls


def hashlib_name(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def main() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    STAAR_DIR.mkdir(parents=True, exist_ok=True)
    log(f"\n## fetch {utc_now()}")
    discovered: list[str] = []
    for index, page in enumerate(TEA_PAGES):
        discovered.extend(scrape_page(page, f"tea-staar-g5-{index}.html"))
    for query in CDX_QUERIES:
        discovered.extend(cdx_search(query))
    discovered.extend(TARGET_URLS)

    wanted = []
    seen: set[str] = set()
    for url in discovered:
        clean = url.split("?")[0]
        if clean in seen:
            continue
        if not is_english_grade5_math(clean):
            continue
        if not clean.lower().endswith(".pdf"):
            continue
        seen.add(clean)
        wanted.append(clean)
    log(f"- candidate english g5 math pdf urls {len(wanted)}")
    for url in wanted:
        log(f"- candidate {url}")

    downloads: list[dict[str, Any]] = []
    for url in wanted:
        rec = try_download(url)
        downloads.append(rec)

    kept: list[dict[str, Any]] = []
    for rec in downloads:
        dest = Path(rec.get("dest") or "")
        if rec.get("outcome") not in {"ok", "exists"}:
            continue
        path = dest if dest.is_absolute() else ROOT / dest
        if not path.exists():
            path = dest_for(rec.get("triedUrl") or "")
        if not path.exists():
            continue
        info = inspect_pdf(path)
        info["url"] = rec.get("triedUrl")
        info["outcome"] = rec.get("outcome")
        if info.get("scanned"):
            log(f"- skip scanned {path.name} alnum={info['alnumChars']}")
            continue
        if not info.get("textExtractable"):
            log(f"- skip not-extractable {path.name} alnum={info['alnumChars']}")
            continue
        kept.append(info)
        log(
            f"- keep {path.name} pages={info['pageCount']} alnum={info['alnumChars']} "
            f"role={'key' if is_key_name(path.name) else 'test'} year={year_from_name(path.name)}"
        )

    dump = {
        "writtenAt": utc_now(),
        "nDiscovered": len(discovered),
        "nWanted": len(wanted),
        "nDownloadedOk": sum(1 for rec in downloads if rec.get("outcome") in {"ok", "exists"}),
        "kept": kept,
    }
    (OUT_DIR / "fetch-g5-kept.json").write_text(json.dumps(dump, indent=2) + "\n", encoding="utf-8")
    log(f"- wrote fetch-g5-kept.json kept={len(kept)}")


if __name__ == "__main__":
    main()
