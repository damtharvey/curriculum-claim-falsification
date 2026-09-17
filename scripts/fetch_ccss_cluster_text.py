"""Fetch the Common Core State Standards (CCSS) text for every cluster code the Regents tables use.

NYSED maps each Regents question to a CCSS cluster such as ``A-REI.B``. The CCSS
publish one heading sentence per cluster and one or more numbered standards under
it. This script fetches the domain pages from thecorestandards.org (the CCSSO
mirror of corestandards.org), parses heading and standard text, and writes
``exports/standards-split/standards-text.json`` keyed by the Regents-style code.

The text is stored before any classification so the verb-class rule in
``preregistration.md`` can quote it and be hashed before hit rates are joined.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STANDARDS_DIRECTORY = REPO_ROOT / "exports/standards-split"
ITEM_STANDARDS_PATH = STANDARDS_DIRECTORY / "item-standards.jsonl"
OUTPUT_PATH = STANDARDS_DIRECTORY / "standards-text.json"
HTML_CACHE_DIRECTORY = STANDARDS_DIRECTORY / "ccss-html"
BASE_URL = "https://www.thecorestandards.org/Math/Content/HS{category}/{domain}/"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) curriculum-claim-falsification standards fetch"
REQUEST_PAUSE_SECONDS = 1.5

CLUSTER_CODE_PATTERN = re.compile(r"^([A-Z])-([A-Z]{1,3})\.([A-Z])$")
HEADING_PATTERN = re.compile(r"<h4>(.*?)</h4>", re.S)
STANDARD_BLOCK_PATTERN = re.compile(
    r'<div class="(standard|substandard)"><a [^>]*name="(CCSS\.Math\.Content\.[A-Z0-9.\-a-z]+)">[^<]*</a><br/>(.*?)</div>',
    re.S,
)
TAG_PATTERN = re.compile(r"<[^>]+>")


def clean_text(fragment: str) -> str:
    text = TAG_PATTERN.sub("", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_domain_page(category: str, domain: str) -> tuple[str, str]:
    url = BASE_URL.format(category=category, domain=domain)
    HTML_CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    cache_path = HTML_CACHE_DIRECTORY / f"HS{category}-{domain}.html"
    if cache_path.exists():
        return url, cache_path.read_text(encoding="utf-8")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode("utf-8")
    cache_path.write_text(body, encoding="utf-8")
    time.sleep(REQUEST_PAUSE_SECONDS)
    return url, body


def parse_domain_page(body: str, category: str, domain: str) -> dict[str, dict[str, object]]:
    """Return clusters of one domain page keyed by cluster letter.

    Each ``<h4>`` is a cluster heading; the ``<div class="standard">`` blocks that
    follow it, up to the next ``<h4>``, are its standards. The cluster letter is read
    from the standards' identifiers (``CCSS.Math.Content.HSA.REI.B.4`` is cluster B).
    """
    content_start = body.find("Standards in this domain")
    if content_start < 0:
        raise ValueError(f"HS{category}.{domain}: page has no 'Standards in this domain' section")
    content = body[content_start:]
    segments = re.split(r"(?=<h4>)", content)
    clusters: dict[str, dict[str, object]] = {}
    for segment in segments:
        heading_match = HEADING_PATTERN.search(segment)
        if heading_match is None:
            continue
        heading = clean_text(heading_match.group(1))
        standards: list[dict[str, str]] = []
        letters: set[str] = set()
        for block_kind, identifier, text in STANDARD_BLOCK_PATTERN.findall(segment):
            identifier_parts = identifier.split(".")
            # CCSS.Math.Content.HSA.REI.B.4 -> ['CCSS','Math','Content','HSA','REI','B','4']
            if identifier_parts[3] != f"HS{category}" or identifier_parts[4] != domain:
                raise ValueError(f"identifier {identifier} does not belong to HS{category}.{domain}")
            letters.add(identifier_parts[5])
            standards.append({"kind": block_kind, "id": identifier, "text": clean_text(text)})
        if not standards:
            raise ValueError(f"HS{category}.{domain}: heading {heading!r} has no standards beneath it")
        if len(letters) != 1:
            raise ValueError(f"HS{category}.{domain}: heading {heading!r} spans cluster letters {sorted(letters)}")
        letter = letters.pop()
        if letter in clusters:
            raise ValueError(f"HS{category}.{domain}: cluster {letter} parsed twice")
        clusters[letter] = {"heading": heading, "standards": standards}
    if not clusters:
        raise ValueError(f"HS{category}.{domain}: no clusters parsed")
    return clusters


def codes_in_use(item_standards_path: Path) -> list[str]:
    codes: set[str] = set()
    for line in item_standards_path.read_text().splitlines():
        if line.strip():
            codes.add(str(json.loads(line)["standard"]))
    return sorted(codes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--item-standards", type=Path, default=ITEM_STANDARDS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    arguments = parser.parse_args()

    codes = codes_in_use(arguments.item_standards)
    domains_needed: dict[tuple[str, str], list[str]] = {}
    for code in codes:
        match = CLUSTER_CODE_PATTERN.match(code)
        if match is None:
            raise ValueError(f"unexpected cluster code {code!r}")
        category, domain, _letter = match.groups()
        domains_needed.setdefault((category, domain), []).append(code)

    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    output: dict[str, object] = {
        "source": "thecorestandards.org (CCSSO mirror of corestandards.org), Common Core State Standards for Mathematics, high school",
        "fetchedAt": fetched_at,
        "codesInUse": codes,
        "clusters": {},
        "domainPages": {},
    }
    for (category, domain), domain_codes in sorted(domains_needed.items()):
        url, body = fetch_domain_page(category, domain)
        clusters = parse_domain_page(body, category, domain)
        output["domainPages"][f"HS{category}.{domain}"] = {"url": url, "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}
        for code in domain_codes:
            letter = code.rsplit(".", 1)[1]
            if letter not in clusters:
                raise KeyError(f"{code}: cluster {letter} is not on {url}; clusters there are {sorted(clusters)}")
            output["clusters"][code] = {
                "ccssIdentifier": f"CCSS.Math.Content.HS{category}.{domain}.{letter}",
                "heading": clusters[letter]["heading"],
                "standards": clusters[letter]["standards"],
                "sourceUrl": url,
            }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(output, indent=1, ensure_ascii=False) + "\n")
    for code in codes:
        print(code, "|", output["clusters"][code]["heading"])


if __name__ == "__main__":
    main()
