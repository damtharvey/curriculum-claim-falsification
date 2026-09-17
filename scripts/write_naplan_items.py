#!/usr/bin/env python3
"""NAPLAN Year 7 numeracy items transcribed from ACARA 2015-2016 papers + answer keys.

Only items whose stem and options (or numeric key) are in the PDF text layer.
Figure-only items are not invented. Keys from the matching year paper-test answers PDF.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "naplan.jsonl"
LICENSE = (
    "ACARA NAPLAN 2012-2016 public paper tests. "
    "Stems transcribed from the Year 7 numeracy PDFs; keys from the year paper-test answers. "
    "© Australian Curriculum, Assessment and Reporting Authority."
)
SRC = {
    "2015-calc": "https://acaraweb.blob.core.windows.net/acaraweb/docs/default-source/assessment-and-reporting-publications/naplan-2015-final-test-numeracy-(calculator)-year-7.pdf?sfvrsn=2",
    "2016-calc": "https://acaraweb.blob.core.windows.net/acaraweb/docs/default-source/assessment-and-reporting-publications/e5-naplan-2016-final-test-numeracy-year-7-(calc).pdf?sfvrsn=2",
}


def item(year: str, paper: str, q: int, **kwargs: object) -> dict:
    rec = {
        "id": f"naplan-{year}-y7-{paper}-q{q}",
        "corpus": "naplan",
        "authority": "acara",
        "claim": "y7-numeracy",
        "sourceUrl": SRC[f"{year}-{paper}"],
        "licenseNote": LICENSE,
        "role": "target",
        "grade": "7",
    }
    rec.update(kwargs)
    return rec


ITEMS = [
    item(
        "2015",
        "calc",
        3,
        stem="Fran makes $72 selling 9 cakes at a market. All her cakes are the same price. How much money will she make selling 12 cakes?",
        choices={"A": "$54", "B": "$76", "C": "$93", "D": "$96"},
        key="D",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        7,
        stem="Which one of these numbers is a factor of 38?",
        choices={"A": "3", "B": "8", "C": "19", "D": "76"},
        key="C",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        10,
        stem="There are 12 apples and 7 pears in a bowl. About what percentage of the fruit in the bowl is pears?",
        choices={"A": "7%", "B": "37%", "C": "58%", "D": "63%"},
        key="B",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        11,
        stem="Which one of these has the same value as 20^2?",
        choices={"A": "40^2 ÷ 4", "B": "2×2×5×2×5", "C": "4 × 5^2", "D": "2 × 10 × 10"},
        key="A",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        12,
        stem="Australian dress sizes 8,10,12,14,16,18 pair with European sizes 38,40,42,44,46,48. What is the rule connecting dress sizes in Australia and Europe?",
        choices={
            "A": "European size = Australian size – 30",
            "B": "European size = Australian size + 30",
            "C": "European size = (2 × Australian size) + 22",
            "D": "European size = (4 × Australian size) + 6",
        },
        key="B",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        14,
        stem="A concert starts at 10:28 am and runs for 124 minutes. What time does it finish?",
        choices={"A": "11:52 am", "B": "11:52 pm", "C": "12:32 am", "D": "12:32 pm"},
        key="D",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        15,
        stem="Tim has two large boxes of cereal with the same mass. He also has a smaller box that has a mass of 175 grams. He has 1675 grams of cereal in total. Which expression can be used to calculate the mass of one large box of cereal?",
        choices={
            "A": "2 × (1675 + 175)",
            "B": "2 × (1675 – 175)",
            "C": "(1675 + 175) ÷ 2",
            "D": "(1675 – 175) ÷ 2",
        },
        key="D",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        18,
        stem="A rectangle has a length of 15 cm and a width of 10 cm. A square has the same perimeter as this rectangle. What is the side length of this square in centimetres?",
        choices={"A": "5", "B": "6.25", "C": "12.5", "D": "37.5"},
        key="C",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        19,
        stem="Continent car production: Africa 636519, Asia/Oceania 45800878, Europe 19726405, North America 21136313, South America 4288654. How many more cars were produced in North and South America than in Europe and Africa?",
        key="5062043",
        responseType="numeric",
    ),
    item(
        "2015",
        "calc",
        20,
        stem="An unknown number is added to 4. The result is multiplied by 3 to give an answer of 9. Which of these is the unknown number?",
        choices={"A": "–3", "B": "–1", "C": "1", "D": "23"},
        key="B",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        21,
        stem="Ms Hogan has more than 20 students in her class. When she divides the class into groups of 5, there are 4 students left over. When she divides the class into groups of 4, there is 1 student left over. What is the least number of students that could be in Ms Hogan’s class?",
        key="29",
        responseType="numeric",
    ),
    item(
        "2015",
        "calc",
        24,
        stem="Rachel lives 2 km from her school. She walks to school at a constant speed of 5 km per hour. How many minutes does it take for Rachel to walk to her school?",
        choices={"A": "2.5", "B": "10", "C": "24", "D": "40"},
        key="C",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        26,
        stem="Simon is facing west. He turns 135° clockwise. Simon then turns anticlockwise until he faces east. By how many degrees did Simon turn anticlockwise?",
        choices={"A": "45°", "B": "180°", "C": "225°", "D": "315°"},
        key="D",
        responseType="selected",
    ),
    item(
        "2015",
        "calc",
        28,
        stem="Sarah was collecting money for charity. By Sunday night she had collected 55% of her target amount. On Monday she collected another $70, which meant she had now collected 75% of her target amount. What was Sarah’s target amount?",
        key="350",
        responseType="numeric",
    ),
    item(
        "2015",
        "calc",
        29,
        stem="Lin is seven years younger than Adrian. Adrian is four years older than half of Maya’s age. The sum of all three ages is 61. How old is Lin?",
        key="12",
        responseType="numeric",
    ),
    item(
        "2015",
        "calc",
        31,
        stem="Mark has a square photo with an area of 9 cm2. He enlarged the photo to have an area of 36 cm2. To do this, the length of each side was multiplied by a factor of",
        choices={"A": "two", "B": "three", "C": "four", "D": "five"},
        key="A",
        responseType="selected",
    ),
    item(
        "2016",
        "calc",
        1,
        stem="Grace is 16 years old. Mark is 5 years more than twice Grace’s age. How old is Mark?",
        choices={"A": "42", "B": "82", "C": "23", "D": "37"},
        key="D",
        responseType="selected",
    ),
    item(
        "2016",
        "calc",
        2,
        stem="When keeping horses, 1 hectare of land is recommended for every 2 horses. How many hectares of land would be needed for 8 horses?",
        choices={"A": "4", "B": "6", "C": "10", "D": "16"},
        key="A",
        responseType="selected",
    ),
    item(
        "2016",
        "calc",
        4,
        stem="Jane makes necklaces using beads. She has 345 beads in 23 different colours. She has the same number of beads in each colour. How many beads does Jane have of each colour?",
        key="15",
        responseType="numeric",
    ),
    item(
        "2016",
        "calc",
        5,
        stem="Tammy left her house at 8:35 in the morning and did not return until 4:45 in the afternoon. How long was Tammy away from her house?",
        choices={
            "A": "3 hours 50 minutes",
            "B": "4 hours 10 minutes",
            "C": "7 hours 50 minutes",
            "D": "8 hours 10 minutes",
        },
        key="D",
        responseType="selected",
    ),
    item(
        "2016",
        "calc",
        6,
        stem="A scientist is studying mice. Which unit would be the most appropriate to record the mass of a mouse?",
        choices={"A": "litre", "B": "millimetre", "C": "gram", "D": "kilogram"},
        key="C",
        responseType="selected",
    ),
]


def main() -> None:
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ITEMS), encoding="utf-8")
    print(f"wrote {len(ITEMS)} NAPLAN items -> {OUT}")


if __name__ == "__main__":
    main()
