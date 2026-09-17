#!/usr/bin/env python3
"""Download public released-test PDFs. Log every URL. Do not invent items."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ingest_lib import RAW, ROOT, append_log, archive_url, download_url

HTML_DIR = RAW / "_html"


def scrape_hrefs(page_url: str, dest_name: str) -> list[str]:
    html_path = HTML_DIR / dest_name
    rec = download_url(page_url, html_path, timeout=60)
    if rec["outcome"] not in {"ok", "exists"}:
        rec2 = download_url(archive_url(page_url), HTML_DIR / f"aw_{dest_name}", timeout=60)
        if rec2["outcome"] not in {"ok", "exists"}:
            return []
        html_path = HTML_DIR / f"aw_{dest_name}"
    html = html_path.read_text(encoding="utf-8", errors="replace")
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
    out: list[str] = []
    for href in hrefs:
        if href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        abs_url = urljoin(page_url, href)
        out.append(abs_url)
    return out


def keep_math_files(urls: list[str], needles: list[str]) -> list[str]:
    kept: list[str] = []
    for url in urls:
        low = url.lower()
        if not any(n in low for n in needles):
            continue
        if any(low.endswith(ext) for ext in (".pdf", ".xlsx", ".xls", ".csv", ".txt")):
            kept.append(url.split("#")[0])
        elif "released" in low and "math" in low:
            kept.append(url.split("#")[0])
    return sorted(set(kept))


def dest_for(url: str, subdir: str) -> Path:
    name = Path(urlparse(url).path).name or "index"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    if not name.lower().endswith((".pdf", ".xlsx", ".xls", ".csv", ".txt", ".html")):
        name = name + ".bin"
    return RAW / subdir / name


def fetch_list(urls: list[str], subdir: str) -> list[dict]:
    rows: list[dict] = []
    for url in urls:
        dest = dest_for(url, subdir)
        rec = download_url(url, dest)
        if rec["outcome"] == "fail":
            rec = download_url(archive_url(url), dest)
            rec["via"] = "archive.org"
        rec["subdir"] = subdir
        rows.append(rec)
    return rows


def staar_templates() -> list[str]:
    urls: list[str] = []
    grades = ["3", "4", "5", "6", "7", "8"]
    for year in range(2013, 2024):
        for g in grades:
            urls.extend(
                [
                    f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-{g}-math-test.pdf",
                    f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-{g}-math-key.pdf",
                    f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-grade-{g}-math-test.pdf",
                    f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-gr{g}-math-test.pdf",
                    f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-gr{g}-mathematics-test.pdf",
                    f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-gr{g}-mathematics-test-tagged.pdf",
                    f"https://tea.texas.gov/data-reports/staar/released-test-questions/{year}-staar-gr{g}-mathematics-test-tagged.pdf",
                    f"https://tea.texas.gov/data-reports/staar/released-test-questions/{year}-staar-gr{g}-mathematics-answer-key.pdf",
                    f"https://tea.texas.gov/data-reports/staar/released-test-questions/{year}-staar-may-grade-{g}-math-releasedtest.pdf",
                    f"https://tea.texas.gov/data-reports/staar/released-test-questions/{year}-staar-may-grade-{g}-math-answerkey.pdf",
                    f"https://tea.texas.gov/student-assessment/testing/staar/released-test-questions/{year}-staar-{g}-math-test.pdf",
                    f"https://tea.texas.gov/sites/default/files/{year}_staar_released_test_grade_{g}_math.pdf",
                    f"https://tea.texas.gov/student-assessment/testing/staar/{year}-staar-released-grade-{g}-math.pdf",
                ]
            )
        urls.extend(
            [
                f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-algebra-i-test.pdf",
                f"https://tea.texas.gov/student-assessment/staar/released-test-questions/{year}-staar-algebra-i-key.pdf",
                f"https://tea.texas.gov/data-reports/staar/released-test-questions/{year}-staar-algebra-i-test-tagged.pdf",
                f"https://tea.texas.gov/data-reports/staar/released-test-questions/{year}-staar-may-algebra-i-releasedtest.pdf",
                f"https://tea.texas.gov/student-assessment/testing/staar/released-test-questions/{year}-staar-algebra-i-test.pdf",
            ]
        )
    urls.extend(
        [
            "https://tea.texas.gov/student-assessment/staar/released-test-questions/2013-staar-6-math-test.pdf",
            "https://tea.texas.gov/student-assessment/staar/released-test-questions/2015-staar-algebra-i-test.pdf",
            "https://tea.texas.gov/data-reports/staar/released-test-questions/2021-staar-gr3-mathematics-test-tagged.pdf",
            "https://tea.texas.gov/data-reports/staar/staar-released-test-questions",
            "https://tea.texas.gov/student-assessment/testing/staar/staar-released-test-questions",
        ]
    )
    return urls


def nysed_3_8_templates() -> list[str]:
    urls: list[str] = []
    for year in range(2015, 2024):
        for g in range(3, 9):
            urls.extend(
                [
                    f"https://www.nysedregents.org/ei/math/{year}/english/{year}-released-items-math-g{g}.pdf",
                    f"https://www.nysedregents.org/elementary/math/{year}/{year}-released-items-math-g{g}.pdf",
                    f"https://www.nysed.gov/sites/default/files/programs/state-assessment/{year}-released-items-math-g{g}.pdf",
                    f"https://www.nysed.gov/sites/default/files/programs/state-assessment/math-grade-{g}-{year}.pdf",
                ]
            )
    urls.append("https://www.nysed.gov/state-assessment/past-grades-3-8-tests")
    urls.append("https://www.nysedregents.org/elementary/")
    return urls


def naplan_templates() -> list[str]:
    base = "https://acaraweb.blob.core.windows.net/acaraweb/docs/default-source/assessment-and-reporting-publications/"
    urls = [
        "https://www.acara.edu.au/assessment/naplan/naplan-2012-2016-test-papers",
        "https://www.acara.edu.au/assessment/naplan/naplan-2008-2011-test-papers",
    ]
    for year in range(2012, 2017):
        for y in (3, 5, 7, 9):
            urls.extend(
                [
                    f"{base}naplan-{year}-final-test-numeracy-year-{y}.pdf",
                    f"{base}naplan-{year}-final-test-numeracy-year-{y}-(calculator).pdf",
                    f"{base}naplan-{year}-final-test-numeracy-year-{y}-(no-calculator).pdf",
                    f"{base}naplan-{year}-final-test-numeracy-year-{y}-(non-calculator).pdf",
                    f"{base}e5-naplan-{year}-final-test-numeracy-year-{y}-(calc).pdf",
                    f"{base}naplan-{year}-final-test-numeracy-(calculator)-year-{y}.pdf",
                    f"{base}naplan-{year}-paper-test-answers.pdf",
                    f"{base}naplan-{year}-final-test-answers.pdf",
                ]
            )
    urls.extend(
        [
            f"{base}naplan-2012-final-test---numeracy-year-3-(redacted-image-of-face-page-14).pdf?sfvrsn=2",
            f"{base}naplan-2012-final-test-numeracy-year-9-(no-calculator).pdf",
            f"{base}naplan-2014-final-test-numeracy-year-9-(calculator).pdf",
        ]
    )
    return urls


def timss_templates() -> list[str]:
    return [
        "https://nces.ed.gov/timss/released-questions.asp",
        "https://nces.ed.gov/timss/pdf/TIMSS2011_G8_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS2011_G4_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS2007_G8_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS2007_G4_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS2003_G8_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS2003_G4_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS1999_G8_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS1995_G4_Math.pdf",
        "https://nces.ed.gov/timss/pdf/TIMSS1995_G8_Math.pdf",
        "https://timss.bc.edu/timss1995i/timsspdf/bmitems.pdf",
        "https://timss.bc.edu/timss1995i/timsspdf/amitems.pdf",
        "https://nces.ed.gov/timss/xls/TIMSS_Grade4_Math_Released_Item_Statistics.xlsx",
        "https://nces.ed.gov/timss/xls/TIMSS_Grade8_Math_Released_Item_Statistics.xlsx",
        "https://timss.bc.edu/timss1995i/Items.html",
        "https://timss.bc.edu/TIMSS2003i/released.html",
        "https://timss.bc.edu/TIMSS2007/items.html",
    ]


def pisa_templates() -> list[str]:
    return [
        "https://www.oecd.org/pisa/test/",
        "https://www.oecd.org/content/dam/oecd/en/about/programmes/edu/pisa/pisa-test/PISA%202012%20items%20for%20release_ENGLISH.pdf",
        "https://www.oecd.org/pisa/38709418.pdf",
        "https://www.oecd.org/pisa/39744146.pdf",
        "https://www.oecd.org/content/dam/oecd/en/publications/reports/2009/07/take-the-test_g1ghc6d2/9789264050815-en.pdf",
        "https://www.oecd.org/pisa/pisaproducts/Take%20the%20test%20e%20book.pdf",
        "https://www.oecd.org/pisa/pisaproducts/pisa2003/PISA_2003_Released_Math_Items.pdf",
        "https://www.oecd.org/pisa/test/PISA2012_released_MAT_items.pdf",
        "https://nces.ed.gov/surveys/pisa/pdf/items_math2012.pdf",
        "https://nces.ed.gov/surveys/pisa/pdf/items2_math.pdf",
    ]


def eqao_templates() -> list[str]:
    return [
        "https://www.eqao.com/",
        "https://www.eqao.com/the-assessments/assessment-documents/",
        "https://www.eqao.com/wp-content/uploads/2021/07/g6-language-math-assessment-booklet-2016.pdf",
        "https://www.eqao.com/wp-content/uploads/g6-2016-released-questions-language-answers.pdf",
        "https://www.eqao.com/wp-content/uploads/junior-division-assessment-math-language-2016.pdf",
        "https://www.eqao.com/the-assessments/grade-9-math/",
        "https://www.eqao.com/wp-content/uploads/2022/10/g9-released-questions-academic-2019.pdf",
        "https://www.eqao.com/wp-content/uploads/g3-2016-assessment-booklet.pdf",
    ]


def run_staar() -> None:
    append_log("\n## STAAR")
    page_urls = scrape_hrefs(
        "https://tea.texas.gov/data-reports/staar/staar-released-test-questions",
        "tea-staar.html",
    )
    page_urls += scrape_hrefs(
        "https://tea.texas.gov/student-assessment/testing/staar/staar-released-test-questions",
        "tea-staar-old.html",
    )
    wanted = keep_math_files(
        page_urls,
        ["math", "algebra", "staar", "released"],
    )
    wanted = [u for u in wanted if any(x in u.lower() for x in ("math", "algebra", "alg"))]
    fetch_list(wanted, "staar")
    fetch_list(staar_templates(), "staar")


def run_regents() -> None:
    append_log("\n## NY Regents")
    pages = [
        ("https://www.nysedregents.org/algebraone/", "regents-alg1.html", "regents-alg1"),
        ("https://nysedregents.org/algebraone/home.html", "regents-alg1b.html", "regents-alg1"),
        ("https://www.nysedregents.org/geometryre/", "regents-geo.html", "regents-geo"),
        ("https://nysedregents.org/Geometry/", "regents-geo-old.html", "regents-geo"),
        ("https://www.nysedregents.org/algebratwo/", "regents-alg2.html", "regents-alg2"),
    ]
    for page, html_name, sub in pages:
        hrefs = scrape_hrefs(page, html_name)
        files = [
            u
            for u in hrefs
            if any(u.lower().endswith(ext) for ext in (".pdf", ".xlsx", ".xls"))
            and not any(x in u.lower() for x in ("chinese", "spanish", "haitian", "arabic", "large-type", "largetype"))
        ]
        fetch_list(files, sub)


def run_nysed() -> None:
    append_log("\n## NYSED 3-8")
    hrefs = scrape_hrefs("https://www.nysed.gov/state-assessment/past-grades-3-8-tests", "nysed-38.html")
    hrefs += scrape_hrefs("https://www.nysedregents.org/elementary/", "nysed-elem.html")
    wanted = keep_math_files(hrefs, ["math", "released"])
    fetch_list(wanted, "nysed")
    fetch_list(nysed_3_8_templates(), "nysed")


def run_naplan() -> None:
    append_log("\n## NAPLAN")
    hrefs = scrape_hrefs(
        "https://www.acara.edu.au/assessment/naplan/naplan-2012-2016-test-papers",
        "naplan-2012-2016.html",
    )
    hrefs += scrape_hrefs(
        "https://www.acara.edu.au/assessment/naplan/naplan-2008-2011-test-papers",
        "naplan-2008-2011.html",
    )
    wanted = [u for u in hrefs if "numeracy" in u.lower() or "answer" in u.lower()]
    fetch_list(wanted, "naplan")
    fetch_list(naplan_templates(), "naplan")


def run_timss() -> None:
    append_log("\n## TIMSS")
    hrefs = scrape_hrefs("https://nces.ed.gov/timss/released-questions.asp", "timss-nces.html")
    hrefs += scrape_hrefs("https://timss.bc.edu/timss1995i/Items.html", "timss-1995.html")
    wanted = [
        u
        for u in hrefs
        if any(x in u.lower() for x in ("math", "xls", "xlsx")) and any(u.lower().endswith(ext) for ext in (".pdf", ".xlsx", ".xls"))
    ]
    fetch_list(wanted, "timss")
    fetch_list(timss_templates(), "timss")


def run_pisa() -> None:
    append_log("\n## PISA")
    hrefs = scrape_hrefs("https://www.oecd.org/pisa/test/", "pisa-oecd.html")
    wanted = [u for u in hrefs if u.lower().endswith(".pdf") and "math" in u.lower()]
    fetch_list(wanted, "pisa")
    fetch_list(pisa_templates(), "pisa")


def run_eqao() -> None:
    append_log("\n## EQAO")
    hrefs = scrape_hrefs("https://www.eqao.com/the-assessments/assessment-documents/", "eqao.html")
    wanted = [
        u
        for u in hrefs
        if u.lower().endswith(".pdf") and any(x in u.lower() for x in ("math", "g3", "g6", "g9", "grade-3", "grade-6", "grade-9"))
    ]
    fetch_list(wanted, "eqao")
    fetch_list(eqao_templates(), "eqao")


def run_mcas() -> None:
    append_log("\n## MCAS")
    dest = RAW / "mcas-2019-g7.pdf"
    urls = [
        "https://www.doe.mass.edu/mcas/2019/release/gr7-math.pdf",
        "https://web.archive.org/web/2020/https://www.doe.mass.edu/mcas/2019/release/gr7-math.pdf",
    ]
    for url in urls:
        rec = download_url(url, dest)
        if rec["outcome"] in {"ok", "exists"}:
            return
        rec = download_url(archive_url(url), dest)
        if rec["outcome"] in {"ok", "exists"}:
            rec["via"] = "archive.org"
            return
    append_log("- FAIL MCAS 2019 grade 7 PDF")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus",
        default="all",
        choices=["all", "staar", "regents", "nysed", "naplan", "timss", "pisa", "eqao", "mcas"],
    )
    args = parser.parse_args()
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    append_log(f"\n# download_public_pdfs.py corpus={args.corpus}")
    runners = {
        "staar": run_staar,
        "regents": run_regents,
        "nysed": run_nysed,
        "naplan": run_naplan,
        "timss": run_timss,
        "pisa": run_pisa,
        "eqao": run_eqao,
        "mcas": run_mcas,
    }
    if args.corpus == "all":
        for fn in runners.values():
            fn()
    else:
        runners[args.corpus]()
    append_log("done " + args.corpus)
    print("logged to", ROOT / "ingest-log.md")


if __name__ == "__main__":
    main()
