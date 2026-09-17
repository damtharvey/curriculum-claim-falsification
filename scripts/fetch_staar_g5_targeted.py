#!/usr/bin/env python3
"""Download known English STAAR grade-5 2015/2017/2018/2020/2023 test+key PDFs.

Logs every URL to exports/replication-staar/fetch-log-g5.md. Does not write ingest-log.md.
Skips scanned PDFs (header present, alnum < 200). No OCR.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
STAAR_DIR = ROOT / "data" / "raw" / "staar"
HTML_DIR = ROOT / "data" / "raw" / "_html"
OUT_DIR = ROOT / "exports" / "replication-staar"
LOG_PATH = OUT_DIR / "fetch-log-g5.md"
USER_AGENT = (
    "Mozilla/5.0 (compatible; CHAT-research/1.0; academic ingest of public released tests)"
)

# Paper English g5 math test+key pairs named on the 2020-12-30 TEA released-test table.
KNOWN_PAIRS: list[tuple[str, str, str]] = [
    (
        "2017-test",
        "STAAR_G5-2017-Test-Math-f.pdf",
        "https://tea.texas.gov/sites/default/files/STAAR_G5-2017-Test-Math-f.pdf",
    ),
    (
        "2017-key",
        "2017_STAAR_Gr5Math_Key_Paper_tagged.pdf",
        "https://tea.texas.gov/sites/default/files/2017_STAAR_Gr5Math_Key_Paper_tagged.pdf",
    ),
    (
        "2018-test",
        "2018_STAAR_Gr5_Math_Test.PDF",
        "https://tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Test.PDF",
    ),
    (
        "2018-key",
        "2018_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
        "https://tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    ),
]

EXTRA_URLS: list[tuple[str, str, str]] = [
    (
        "2015-key-a",
        "STAAR-2015-Key-G5-Math.pdf",
        "https://tea.texas.gov/sites/default/files/STAAR-2015-Key-G5-Math.pdf",
    ),
    (
        "2015-key-b",
        "2015_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
        "https://tea.texas.gov/sites/default/files/2015_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    ),
    (
        "2015-key-c",
        "2015-staar-5-math-key.pdf",
        "https://tea.texas.gov/student-assessment/staar/released-test-questions/2015-staar-5-math-key.pdf",
    ),
    (
        "2020-test-a",
        "2020_STAAR_Gr5_Math_Test.PDF",
        "https://tea.texas.gov/sites/default/files/2020_STAAR_Gr5_Math_Test.PDF",
    ),
    (
        "2020-key-a",
        "2020_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
        "https://tea.texas.gov/sites/default/files/2020_STAAR_Gr5_Math_Key_Paper_tagged.pdf",
    ),
    (
        "2023-test",
        "2023-staar-5-math-test.pdf",
        "https://tea.texas.gov/data-reports/staar/released-test-questions/2023-staar-5-math-test.pdf",
    ),
    (
        "2023-key",
        "2023-staar-math-grade-5-answer-key.pdf",
        "https://tea.texas.gov/data-reports/staar/released-test-questions/2023-staar-math-grade-5-answer-key.pdf",
    ),
]

CDX_QUERIES = [
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/STAAR_G5-2017-Test-Math-f.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Test.PDF&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2017_STAAR_Gr5Math_Key_Paper_tagged.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2018_STAAR_Gr5_Math_Key_Paper_tagged.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/STAAR-2015-Key-G5-Math.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/STAAR_G5-2015-Test-Math-f.pdf&output=json&limit=5",
    "http://web.archive.org/cdx/search/cdx?url=tea.texas.gov/sites/default/files/2020_STAAR_Gr5_Math_Test.PDF&output=json&limit=5",
]

ARCHIVE_STAMPS = ["20201230223459", "20210615000000", "20181215000000"]


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
    print(line, flush=True)


def curl_to(url: str, dest: Path, timeout: int) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "curl",
        "-fsSL",
        "-A",
        USER_AGENT,
        "--retry",
        "1",
        "--max-time",
        str(timeout),
        "-o",
        str(dest),
        url,
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 0 or not dest.exists() or dest.stat().st_size < 200:
        if dest.exists() and dest.stat().st_size < 200:
            dest.unlink(missing_ok=True)
        error = (proc.stderr or proc.stdout or "empty")[:200]
        return {"url": url, "outcome": "fail", "error": error, "dest": str(dest)}
    return {
        "url": url,
        "outcome": "ok",
        "bytes": dest.stat().st_size,
        "dest": str(dest),
    }


def inspect_pdf(path: Path) -> dict[str, Any]:
    import fitz

    header = path.read_bytes()[:8]
    record: dict[str, Any] = {
        "name": path.name,
        "bytes": path.stat().st_size,
        "startsWithPdfHeader": header.startswith(b"%PDF"),
        "pageCount": None,
        "alnumChars": 0,
        "textExtractable": False,
        "scanned": False,
    }
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
    return record


def archive_id_url(url: str, stamp: str) -> str:
    return f"https://web.archive.org/web/{stamp}id_/{url}"


def try_file(label: str, name: str, live_url: str, timeout: int = 60) -> dict[str, Any]:
    dest = STAAR_DIR / name
    if dest.exists() and dest.stat().st_size > 500:
        log(f"- exists {live_url} -> {name} ({dest.stat().st_size} bytes)")
        rec = {"label": label, "url": live_url, "outcome": "exists", "dest": str(dest)}
        rec.update(inspect_pdf(dest))
        return rec
    rec = curl_to(live_url, dest, timeout)
    log(f"- {rec['outcome']} {live_url} :: {rec.get('bytes') or rec.get('error', '')}")
    if rec["outcome"] == "ok":
        rec["label"] = label
        rec.update(inspect_pdf(dest))
        if rec["scanned"]:
            log(f"- skip scanned {name} alnum={rec['alnumChars']}")
        return rec
    for stamp in ARCHIVE_STAMPS:
        archived = archive_id_url(live_url, stamp)
        rec2 = curl_to(archived, dest, timeout=90)
        log(f"- {rec2['outcome']} {archived} :: {rec2.get('bytes') or rec2.get('error', '')}")
        if rec2["outcome"] == "ok":
            rec2["label"] = label
            rec2.update(inspect_pdf(dest))
            if rec2["scanned"]:
                log(f"- skip scanned {name} alnum={rec2['alnumChars']}")
            return rec2
    rec["label"] = label
    return rec


def run_cdx() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    for query in CDX_QUERIES:
        dest = HTML_DIR / ("cdx-" + Path(urlparse(query).path).name + "-" + str(abs(hash(query))) + ".json")
        rec = curl_to(query, dest, timeout=20)
        log(f"- cdx {rec['outcome']} {query[:160]} :: {rec.get('bytes') or rec.get('error', '')}")
        if rec["outcome"] != "ok":
            continue
        try:
            payload = json.loads(dest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            log(f"- cdx parse fail {exc}")
            continue
        log(f"- cdx rows {len(payload)}")
        for row in payload[:8]:
            log(f"  - {row}")


def main() -> None:
    STAAR_DIR.mkdir(parents=True, exist_ok=True)
    log(f"\n## targeted download {utc_now()}")
    log("- TEA live released-test page https://tea.texas.gov/student-assessment/testing/staar/staar-released-test-questions -> 404 (recorded earlier)")
    log("- archive 2020-12-30 table: g5 mathematics paper forms 2019|2018|2017|2016|2014|2013; no 2015 math form; no 2020")
    log("- live data-reports page: 2023 g5 math answer key + rationale + sampler; no operational 2023 test PDF; 2020 is writing samples")
    run_cdx()
    kept: list[dict[str, Any]] = []
    for label, name, url in KNOWN_PAIRS + EXTRA_URLS:
        rec = try_file(label, name, url)
        if rec.get("outcome") in {"ok", "exists"} and rec.get("textExtractable") and not rec.get("scanned"):
            kept.append(rec)
            log(
                f"- keep {name} pages={rec.get('pageCount')} alnum={rec.get('alnumChars')} label={label}"
            )
    dump = {"writtenAt": utc_now(), "kept": kept}
    (OUT_DIR / "fetch-g5-kept.json").write_text(json.dumps(dump, indent=2) + "\n", encoding="utf-8")
    log(f"- wrote fetch-g5-kept.json kept={len(kept)}")


if __name__ == "__main__":
    main()
