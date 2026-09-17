#!/usr/bin/env python3
"""MCAS 2019 G7 items transcribed from the released PDF. No invented choices."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mcas.jsonl"
SRC = "https://www.doe.mass.edu/mcas/2019/release/gr7-math.pdf"
LICENSE = "Massachusetts DESE MCAS Spring 2019 Grade 7 Mathematics released items. Public."


def item(**kwargs: object) -> dict:
    rec = {
        "corpus": "mcas",
        "authority": "ccss",
        "sourceUrl": SRC,
        "licenseNote": LICENSE,
        "role": "target",
        "grade": "7",
    }
    rec.update(kwargs)
    return rec


ITEMS = [
    item(
        id="mcas-2019-7-q1",
        claim="7.RP.A.1",
        stem="A student can run 6 miles in 3/4 hour. At this rate, what is the total number of miles the student can run in 1 hour?",
        choices={"A": "1/8", "B": "2/9", "C": "8", "D": "9"},
        key="C",
        responseType="selected",
    ),
    item(
        id="mcas-2019-7-q2",
        claim="7.NS.A.2",
        stem="What is the value of this expression? (2 − 3)(4 − 5)",
        key="1",
        responseType="numeric",
    ),
    item(
        id="mcas-2019-7-q3",
        claim="7.SP.A.2",
        stem="A principal surveyed 200 seventh-grade students to find out whether they prefer to participate in fall sports or spring sports. This table shows the results. Season Boys Girls: fall 63 45; spring 37 55. Based on the table, what is the probability that a seventh-grade student chosen at random would prefer to participate in spring sports rather than fall sports?",
        choices={"A": "37%", "B": "46%", "C": "54%", "D": "92%"},
        key="B",
        responseType="selected",
        figure={"kind": "table", "transcription": "fall: 63 boys, 45 girls; spring: 37 boys, 55 girls; n=200"},
    ),
    item(
        id="mcas-2019-7-q5",
        claim="7.NS.A.2",
        stem="What is the value of this expression? 2.4 ÷ 0.12",
        choices={"A": "0.05", "B": "0.2", "C": "5", "D": "20"},
        key="D",
        responseType="selected",
    ),
    item(
        id="mcas-2019-7-q7",
        claim="7.NS.A.3",
        stem="One evening, the temperature decreased by 5°F during the first hour after sunset, and then decreased by 2°F each hour for the next 7 hours. The temperature increased by 14.5°F the next morning and then increased by 11°F that afternoon. What was the total change in temperature?",
        choices={
            "A": "The temperature decreased by a total of 15.5°F.",
            "B": "The temperature decreased by a total of 16.5°F.",
            "C": "The temperature increased by a total of 6.5°F.",
            "D": "The temperature increased by a total of 32.5°F.",
        },
        key="C",
        responseType="selected",
    ),
    item(
        id="mcas-2019-7-q8",
        claim="7.G.A.3",
        stem="One of the vertices of a square pyramid is labeled V. What two-dimensional figure will result from slicing the pyramid perpendicular to its base through vertex V?",
        choices={"A": "square", "B": "triangle", "C": "pentagon", "D": "trapezoid"},
        key="B",
        responseType="selected",
        figure={"kind": "diagram", "transcription": "square pyramid with vertex V at the apex"},
    ),
    item(
        id="mcas-2019-7-q9",
        claim="7.EE.B.3",
        stem="A student had 500 milliliters of water in a water bottle. She drank 25% of the water before soccer practice. After practice, she drank 1/3 of the remaining water. How much water, in milliliters, does the student have left in the bottle?",
        choices={"A": "250", "B": "290", "C": "330", "D": "375"},
        key="A",
        responseType="selected",
    ),
    item(
        id="mcas-2019-7-q10",
        claim="7.NS.A.1",
        stem="What is the value of the expression |4| + |-7|?",
        key="11",
        responseType="numeric",
    ),
    item(
        id="mcas-2019-7-q11",
        claim="7.SP.A.1",
        stem="The manager of a company wants to survey a representative sample of the company’s employees to choose a company logo. Which of the following is a representative sample of the company’s employees?",
        choices={
            "A": "every third employee from the largest department in the company",
            "B": "every employee who enters the employee cafeteria",
            "C": "every third employee on the company’s payroll",
            "D": "every employee who is under the age of 35",
        },
        key="C",
        responseType="selected",
    ),
    item(
        id="mcas-2019-7-q16",
        claim="7.EE.A.2",
        stem="This expression can be used to find the price of a television that is on sale for 20% off the regular price of p dollars: p − (1/5)p. Which of the following is another expression that can be used to find the sale price of the television?",
        choices={"A": "0.20p", "B": "0.20p − p", "C": "0.80p", "D": "0.80p − p"},
        key="C",
        responseType="selected",
    ),
    item(
        id="mcas-2019-7-q20",
        claim="7.RP.A.3",
        stem="Released item 20: solve a multi-step percent problem using proportional relationships involving markdowns.",
        choices={"A": "see PDF", "B": "see PDF", "C": "see PDF", "D": "see PDF"},
        key="C",
        responseType="selected",
    ),
]


def main() -> None:
    # Drop the placeholder whose choices were not transcribed.
    items = [r for r in ITEMS if r["id"] != "mcas-2019-7-q20"]
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items), encoding="utf-8")
    print(f"wrote {len(items)} MCAS items -> {OUT}")


if __name__ == "__main__":
    main()
