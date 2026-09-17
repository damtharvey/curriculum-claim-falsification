#!/usr/bin/env python3
"""Extract numeric literals from paper .tex files for the number audit."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
TEX_FILES = [
    "abstract.tex",
    "intro.tex",
    "related.tex",
    "method.tex",
    "results.tex",
    "limitations.tex",
    "main.tex",
]


def main() -> None:
    pattern = re.compile(
        r"(?<![A-Za-z])(?:\d{1,3}(?:\{,\}?\d{3})+|\d+)(?:\.\d+)?(?:/\d+)?"
    )
    for name in TEX_FILES:
        path = PAPER / name
        text = path.read_text(encoding="utf-8")
        print(f"===== {name} =====")
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.split("%", 1)[0]
            hits = pattern.findall(stripped)
            if hits:
                print(f"{i:4d}: {hits} | {stripped.strip()[:120]}")


if __name__ == "__main__":
    main()
