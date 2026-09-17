#!/usr/bin/env python3
"""Download public-release PDFs and rebuild data/items.jsonl when it is missing.

Required system tools (see also scripts/bootstrap_data.sh):
- curl, used by ingest_lib.download_url
- uv, to create .venv
- node and npm, for the TypeScript runner (not this script)
- PDF text is extracted with pymupdf. poppler pdftotext is not used.
  There is no OCR path.

Relative paths only. STAAR URL guessing is the existing
scripts/download_public_pdfs.py templates; this file does not rewrite them.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, append_log, archive_url, download_url, extract_pdf_text

DATA = ROOT / "data"
ITEMS_PATH = DATA / "items.jsonl"
PYTHON = ROOT / ".venv" / "bin" / "python"
FROZEN_N = 2405

REQUIRED_CORPUS_JSONL = (
    "timss_complete.jsonl",
    "timss_historical.jsonl",
    "pisa2012.jsonl",
    "pisa.jsonl",
    "staar.jsonl",
    "nysed.jsonl",
    "mcas.jsonl",
    "naplan.jsonl",
    "nyregents.jsonl",
    "eqao.jsonl",
)

MCAS_DEST = RAW / "mcas-2019-g7.pdf"
MCAS_URLS = (
    "https://www.doe.mass.edu/mcas/2019/release/gr7-math.pdf",
    "https://web.archive.org/web/2020/https://www.doe.mass.edu/mcas/2019/release/gr7-math.pdf",
)

TIMSS_2011 = (
    (
        (RAW / "TIMSS2011_G4_Math.pdf", RAW / "timss" / "TIMSS2011_G4_Math.pdf"),
        RAW / "TIMSS2011_G4_Math.txt",
        "timss2011-g4",
    ),
    (
        (RAW / "TIMSS2011_G8_Math.pdf", RAW / "timss" / "TIMSS2011_G8_Math.pdf"),
        RAW / "TIMSS2011_G8_Math.txt",
        "timss2011-g8",
    ),
)

REQUIRED_PDF_GLOBS = (
    ("staar", ("data/raw/staar/*.pdf", "data/raw/staar/*.PDF", "data/raw/staar-*.pdf")),
    ("nyregents-alg1", ("data/raw/regents-alg1/*.pdf",)),
    ("nyregents-geo", ("data/raw/regents-geo/*.pdf",)),
    ("nyregents-alg2", ("data/raw/regents-alg2/*.pdf",)),
    ("nysed", ("data/raw/nysed/*.pdf", "data/raw/nysed-*.pdf")),
    ("naplan", ("data/raw/naplan/*.pdf", "data/raw/naplan-*.pdf")),
    ("pisa", ("data/raw/pisa/*.pdf",)),
    ("eqao", ("data/raw/eqao/*.pdf",)),
    ("timss-historical", ("data/raw/timss/*.pdf",)),
)

PARSE_SCRIPTS = (
    "write_mcas_items.py",
    "write_pisa_items.py",
    "write_naplan_items.py",
    "parse_timss.py",
    "parse_timss_cycles.py",
    "parse_pisa_bulk.py",
    "parse_staar_bulk.py",
    "parse_nysed_expand.py",
    "parse_naplan_bulk.py",
    "parse_regents.py",
    "parse_eqao.py",
    "collect_items.py",
)


def count_jsonl_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    n = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                n += 1
    return n


def first_existing(paths: tuple[Path, ...]) -> Path | None:
    for path in paths:
        if path.is_file() and path.stat().st_size > 500:
            return path
    return None


def glob_has_file(patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file() and path.stat().st_size > 500:
                return True
    return False


def require_curl() -> None:
    if shutil.which("curl") is None:
        raise SystemExit("curl is required to download public PDFs")


def require_venv_python() -> Path:
    if not PYTHON.is_file():
        raise SystemExit(
            "missing .venv/bin/python at the repository root. "
            "Create it with uv as documented in README.md."
        )
    return PYTHON


def require_pymupdf() -> None:
    try:
        import fitz  # noqa: F401
    except ImportError:
        raise SystemExit(
            "pymupdf is required to extract PDF text. "
            "Install it in .venv. There is no OCR fallback."
        ) from None


def run_python_script(script_name: str, extra: list[str] | None = None) -> None:
    python = require_venv_python()
    argv = [str(python), str(ROOT / "scripts" / script_name)]
    if extra:
        argv.extend(extra)
    completed = subprocess.run(argv, cwd=str(ROOT))
    if completed.returncode != 0:
        raise SystemExit(f"{script_name} failed with exit code {completed.returncode}")


def any_local_pdf() -> bool:
    if not RAW.exists():
        return False
    for path in RAW.rglob("*"):
        if path.suffix.lower() == ".pdf" and path.is_file() and path.stat().st_size > 500:
            return True
    return False


def fetch_mcas_pdf() -> None:
    append_log("\n## MCAS (bootstrap)")
    for url in MCAS_URLS:
        rec = download_url(url, MCAS_DEST)
        if rec["outcome"] in {"ok", "exists"}:
            return
        rec = download_url(archive_url(url), MCAS_DEST)
        if rec["outcome"] in {"ok", "exists"}:
            return
    print(
        "MCAS 2019 grade 7 PDF was not fetched; "
        "scripts/write_mcas_items.py still writes the transcribed census items.",
        file=sys.stderr,
    )
    append_log("- FAIL MCAS 2019 grade 7 PDF; transcribed items still come from write_mcas_items.py")


def download_corpora() -> None:
    require_curl()
    run_python_script("download_public_pdfs.py", ["--corpus", "all"])
    fetch_mcas_pdf()


def ensure_timss_2011_text() -> None:
    missing: list[str] = []
    for pdf_candidates, txt_path, label in TIMSS_2011:
        pdf_path = first_existing(pdf_candidates)
        if pdf_path is None:
            missing.append(label)
            continue
        dest_pdf = pdf_candidates[0]
        if dest_pdf != pdf_path and not dest_pdf.exists():
            dest_pdf.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf_path, dest_pdf)
        if txt_path.is_file() and txt_path.stat().st_size > 500:
            continue
        require_pymupdf()
        txt_path.write_text(extract_pdf_text(pdf_path), encoding="utf-8")
        append_log(f"- extracted text {pdf_path.name} -> {txt_path.name}")
    if missing:
        raise SystemExit(
            "required TIMSS 2011 PDFs missing after download: " + ", ".join(missing)
        )


def check_required_pdfs() -> None:
    missing: list[str] = []
    for label, patterns in REQUIRED_PDF_GLOBS:
        if not glob_has_file(patterns):
            missing.append(label)
    if first_existing(TIMSS_2011[0][0]) is None:
        missing.append("timss2011-g4")
    if first_existing(TIMSS_2011[1][0]) is None:
        missing.append("timss2011-g8")
    if missing:
        raise SystemExit(
            "required public-release PDFs missing after download: " + ", ".join(missing)
        )


def check_required_corpus_jsonl() -> None:
    missing: list[str] = []
    empty: list[str] = []
    for name in REQUIRED_CORPUS_JSONL:
        path = DATA / name
        if not path.is_file():
            missing.append(name)
            continue
        if count_jsonl_rows(path) < 1:
            empty.append(name)
    if missing or empty:
        parts: list[str] = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if empty:
            parts.append("empty " + ", ".join(empty))
        raise SystemExit("required corpus jsonl after parse: " + "; ".join(parts))


def parse_corpora() -> None:
    require_pymupdf()
    ensure_timss_2011_text()
    for script_name in PARSE_SCRIPTS:
        run_python_script(script_name)
    check_required_corpus_jsonl()
    n_items = count_jsonl_rows(ITEMS_PATH)
    if n_items < 1:
        raise SystemExit("data/items.jsonl is empty after collect_items.py")
    if n_items != FROZEN_N:
        print(
            f"warning: rebuilt items.jsonl has {n_items} rows; "
            f"frozen paper census is {FROZEN_N}. "
            "Keep the tracked data/items.jsonl for the paper N.",
            file=sys.stderr,
        )
    else:
        print(f"rebuilt frozen census N={n_items} -> {ITEMS_PATH.relative_to(ROOT)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Do not fetch PDFs. Fails if items.jsonl is missing and PDFs are not already local.",
    )
    parser.add_argument(
        "--download-pdfs",
        action="store_true",
        help="Fetch PDFs even when the frozen items.jsonl is present.",
    )
    parser.add_argument(
        "--force-parse",
        action="store_true",
        help="Re-run parsers into per-corpus jsonl and data/items.jsonl.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    n_items = count_jsonl_rows(ITEMS_PATH)
    frozen_present = n_items == FROZEN_N
    if frozen_present:
        print(
            f"frozen census present: {ITEMS_PATH.relative_to(ROOT)} "
            f"N={n_items}. A full recensus is not required."
        )
    elif n_items > 0:
        print(
            f"data/items.jsonl has {n_items} rows; frozen paper N is {FROZEN_N}.",
            file=sys.stderr,
        )

    need_parse = args.force_parse or n_items < 1
    need_download = args.download_pdfs or (need_parse and not args.skip_download)

    if need_parse and args.skip_download:
        if not any_local_pdf():
            raise SystemExit(
                "data/items.jsonl is missing or --force-parse was set, "
                "and --skip-download was set, and no local PDFs were found."
            )

    if need_download:
        download_corpora()
        check_required_pdfs()
    elif args.skip_download and need_parse:
        check_required_pdfs()

    if need_parse:
        parse_corpora()
    elif not need_download:
        print("nothing to fetch or parse. Pass --download-pdfs to redownload source PDFs.")


if __name__ == "__main__":
    main()
