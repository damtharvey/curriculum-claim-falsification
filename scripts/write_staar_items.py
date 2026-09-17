#!/usr/bin/env python3
"""STAAR May 2022 released items transcribed from TEA PDFs + item-analysis keys.

F/G/H/J choices are stored as A/B/C/D (A=F, B=G, C=H, D=J). No invented choices.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "staar.jsonl"
G7 = "https://tea.texas.gov/data-reports/staar/released-test-questions/2022-staar-may-grade-7-math-releasedtest.pdf"
G8 = "https://tea.texas.gov/data-reports/staar/released-test-questions/2022-staar-may-grade-8-math-releasedtest.pdf"
LICENSE = (
    "Texas Education Agency STAAR May 2022 released mathematics test. "
    "Public released form. Keys from the statewide item-analysis report (* = correct). "
    "TEA copyright; research use of released items."
)


def item(grade: str, **kwargs: object) -> dict:
    rec = {
        "corpus": "staar",
        "authority": "teks",
        "claim": f"g{grade}",
        "sourceUrl": G7 if grade == "7" else G8,
        "licenseNote": LICENSE,
        "role": "target",
        "grade": grade,
        "responseType": "selected",
    }
    rec.update(kwargs)
    return rec


ITEMS = [
    item(
        "7",
        id="staar-2022-7-q1",
        stem="The length of a ruler is 12 inches. There are approximately 25.4 millimeters in 1 inch. Which measurement is closest to the length of the ruler in millimeters?",
        choices={"A": "3,048 mm", "B": "30.48 mm", "C": "304.8 mm", "D": "3.048 mm"},
        key="C",
    ),
    item(
        "7",
        id="staar-2022-7-q2",
        stem="The table shows the numbers of bags of different flavors of potato chips on a store shelf. Plain 12, Jalapeño 18, Ranch 8, Cheese 20. A customer will randomly select one bag. Which statement about the flavor of the potato chips chosen is best supported by the information in the table?",
        choices={
            "A": "The flavor is least likely to be plain.",
            "B": "The flavor is twice as likely to be jalapeño as ranch.",
            "C": "The flavor is equally likely to be plain, jalapeño, ranch, or cheese.",
            "D": "The flavor is more than twice as likely to be cheese as it is to be ranch.",
        },
        key="D",
        figure={"kind": "table", "transcription": "Plain 12, Jalapeño 18, Ranch 8, Cheese 20"},
    ),
    item(
        "7",
        id="staar-2022-7-q5",
        stem="Triangle QRS has side lengths 6 cm, 12 cm, and 15 cm. Which measurements in centimeters represent the dimensions of a triangle that is similar to triangle QRS?",
        choices={
            "A": "8 cm, 14 cm, 17 cm",
            "B": "10 cm, 20 cm, 25 cm",
            "C": "4 cm, 10 cm, 13 cm",
            "D": "12 cm, 24 cm, 36 cm",
        },
        key="B",
        figure={"kind": "diagram", "transcription": "triangle QRS sides 6 cm, 12 cm, 15 cm"},
    ),
    item(
        "7",
        id="staar-2022-7-q6",
        stem="Which equation is true when x = 4?",
        choices={"A": "3x + 4 = 8", "B": "5x − 2 = 18", "C": "2x + 8 = 40", "D": "4x + 4 = 12"},
        key="B",
    ),
    item(
        "7",
        id="staar-2022-7-q7",
        stem="A rectangular pyramid has dimensions 6 mm, 5 mm, and 4 mm as labeled on the diagram. What is the volume of the rectangular pyramid in cubic millimeters?",
        choices={"A": "15 mm^3", "B": "120 mm^3", "C": "60 mm^3", "D": "40 mm^3"},
        key="D",
        figure={"kind": "diagram", "transcription": "rectangular pyramid 6 mm by 5 mm by 4 mm"},
    ),
    item(
        "7",
        id="staar-2022-7-q8",
        stem="Imani compared fluid ounces per bottle of sunscreen to cost. Brand W 20 oz $12.00; X 15 oz $11.25; Y 10 oz $6.50; Z 5 oz $2.50. Which brand has the greatest cost per fluid ounce?",
        choices={"A": "Brand W", "B": "Brand X", "C": "Brand Y", "D": "Brand Z"},
        key="B",
        figure={"kind": "table", "transcription": "W 20/$12; X 15/$11.25; Y 10/$6.50; Z 5/$2.50"},
    ),
    item(
        "7",
        id="staar-2022-7-q18",
        stem="Angle F and angle H are supplementary angles. The measure of angle F is 77°. The measure of angle H is (5x + 18)°. Which equation can be used to find the value of x?",
        choices={
            "A": "77 = 5x + 18",
            "B": "77 + (5x + 18) = 180",
            "C": "77 + (5x + 18) = 90",
            "D": "77 + (5x + 18) = 360",
        },
        key="B",
    ),
    item(
        "7",
        id="staar-2022-7-q24",
        stem="The radius of circle S is half the radius of circle L. The radius of circle L is 8 millimeters. Which measurement is closest to the area of circle S in square millimeters?",
        choices={"A": "50.24 mm^2", "B": "25.12 mm^2", "C": "200.96 mm^2", "D": "12.56 mm^2"},
        key="A",
    ),
    item(
        "7",
        id="staar-2022-7-q25",
        stem="Which situation is best represented by the following equation? 68.50x + 127.95 = 675.95",
        choices={
            "A": "An office manager paid $675.95 to build a web site. The office manager bought a software package for $68.50 and paid an employee $127.95 for each hour she worked on the website. What is x, the number of hours the employee worked on the website?",
            "B": "An office manager paid $675.95 for computer equipment. The office manager bought one monitor for $127.95 and hard drives for $68.50 each. What is x, the number of hard drives the office manager bought?",
            "C": "A sales manager paid $675.95 for advertising. The sales manager paid $127.95 per hour for consulting and received a $68.50 discount. What is x, the number of hours the manager paid for consulting?",
            "D": "A business owner paid a total of $675.95 for two employees to work the same number of days. The business owner paid one employee $68.50. The business paid a second employee $127.95 per day. What is x, the number of days the employees worked?",
        },
        key="B",
    ),
    item(
        "7",
        id="staar-2022-7-q32",
        stem="Alice has a loan of $24,820. This loan has a simple interest rate of 3.5% per year. No payments will be made on the loan until the end of one year. How much interest will Alice pay on this loan at the end of one year?",
        choices={"A": "$868.70", "B": "$72.39", "C": "$8,687.00", "D": "$25,688.70"},
        key="A",
    ),
    item(
        "7",
        id="staar-2022-7-q38",
        stem="The dimensions of a rectangular prism are 1.5 feet by 3.5 feet by 2 feet. What is the volume of the rectangular prism in cubic feet?",
        choices={"A": "7 ft^3", "B": "7.25 ft^3", "C": "8.5 ft^3", "D": "10.5 ft^3"},
        key="D",
    ),
    item(
        "8",
        id="staar-2022-8-q2",
        stem="The diagram shows a right triangle and the lengths of two of its sides in inches: 11.9 in. and 7.9 in. Which measurement is closest to the value of d in inches?",
        choices={"A": "6.3 in.", "B": "4.0 in.", "C": "14.3 in.", "D": "19.8 in."},
        key="C",
        figure={"kind": "diagram", "transcription": "right triangle; 11.9 in. and 7.9 in. on the two given sides; unknown d"},
    ),
]


def main() -> None:
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ITEMS), encoding="utf-8")
    print(f"wrote {len(ITEMS)} STAAR items -> {OUT}")


if __name__ == "__main__":
    main()
