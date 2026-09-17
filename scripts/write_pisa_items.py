#!/usr/bin/env python3
"""PISA 2012 released items transcribed from the OECD English PDF. No invented choices."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "pisa2012.jsonl"
SRC = "https://www.oecd.org/content/dam/oecd/en/about/programmes/edu/pisa/pisa-test/PISA%202012%20items%20for%20release_ENGLISH.pdf"
LICENSE = (
    "OECD PISA 2012 released mathematics items. Public. "
    "SOURCE: PISA 2012 Released Items (English), OECD."
)

def item(**kwargs: object) -> dict:
    rec = {
        "corpus": "pisa",
        "authority": "pisa",
        "sourceUrl": SRC,
        "licenseNote": LICENSE,
        "role": "target",
        "grade": "15",
    }
    rec.update(kwargs)
    return rec


ITEMS = [
    item(
        id="pisa2012-PM918Q01",
        claim="interpret",
        stem="How many CDs did the band The Metalfolkies sell in April?",
        choices={"A": "250", "B": "500", "C": "1000", "D": "1270"},
        key="B",
        responseType="selected",
        figure={"kind": "graph", "transcription": "bar chart of monthly CD sales Jan-Jun for four bands"},
        clusterId="pisa2012-PM918",
    ),
    item(
        id="pisa2012-PM918Q02",
        claim="interpret",
        stem="In which month did the band No One's Darling sell more CDs than the band The Kicking Kangaroos for the first time?",
        choices={"A": "No month", "B": "March", "C": "April", "D": "May"},
        key="C",
        responseType="selected",
        figure={"kind": "graph", "transcription": "same CD sales bar chart as PM918Q01"},
        clusterId="pisa2012-PM918",
    ),
    item(
        id="pisa2012-PM918Q05",
        claim="employ",
        stem="The manager of The Kicking Kangaroos is worried because the number of their CDs that sold decreased from February to June. What is the estimate of their sales volume for July if the same negative trend continues?",
        choices={"A": "70 CDs", "B": "370 CDs", "C": "670 CDs", "D": "1340 CDs"},
        key="B",
        responseType="selected",
        figure={"kind": "graph", "transcription": "same CD sales bar chart; linear decline Feb-Jun"},
        clusterId="pisa2012-PM918",
    ),
    item(
        id="pisa2012-PM921Q01",
        claim="employ",
        stem="Normally, a penguin couple produces two eggs every year. Usually the chick from the larger of the two eggs is the only one that survives. With rockhopper penguins, the first egg weighs approximately 78 g and the second egg weighs approximately 110 g. By approximately how many percent is the second egg heavier than the first egg?",
        choices={"A": "29%", "B": "32%", "C": "41%", "D": "71%"},
        key="C",
        responseType="selected",
        clusterId="pisa2012-PM921",
    ),
    item(
        id="pisa2012-PM921Q02",
        claim="formulate",
        stem="At the beginning of the year, the colony consists of 10 000 penguins (5 000 couples). Each penguin couple raises one chick in the spring of each year. By the end of the year 20% of all the penguins (adults and chicks) will die. At the end of the first year, how many penguins (adults and chicks) are there in the colony?",
        key="12000",
        responseType="numeric",
        clusterId="pisa2012-PM921",
    ),
    item(
        id="pisa2012-PM921Q03",
        claim="formulate",
        stem="Jean assumes the colony will continue to grow: equal numbers of male and female penguins form couples; each couple raises one chick in spring; by the end of each year 20% of all penguins die; one year old penguins will also raise chicks. Based on the above assumptions, which of the following formulae describes the total number of penguins, P, after 7 years?",
        choices={
            "A": "P = 10 000 x (1.5 x 0.2)^7",
            "B": "P = 10 000 x (1.5 x 0.8)^7",
            "C": "P = 10 000 x (1.2 x 0.2)^7",
            "D": "P = 10 000 x (1.2 x 0.8)^7",
        },
        key="B",
        responseType="selected",
        clusterId="pisa2012-PM921",
    ),
    item(
        id="pisa2012-PM923Q01",
        claim="employ",
        stem="One advantage of using a kite sail is that it flies at a height of 150 m. There, the wind speed is approximately 25% higher than down on the deck of the ship. At what approximate speed does the wind blow into a kite sail when a wind speed of 24 km/h is measured on the deck of the ship?",
        choices={"A": "6 km/h", "B": "18 km/h", "C": "25 km/h", "D": "30 km/h", "E": "49 km/h"},
        key="D",
        responseType="selected",
        clusterId="pisa2012-PM923",
    ),
    item(
        id="pisa2012-PM923Q03",
        claim="employ",
        stem="Approximately what is the length of the rope for the kite sail, in order to pull the ship at an angle of 45 degrees and be at a vertical height of 150 m?",
        choices={"A": "173 m", "B": "212 m", "C": "285 m", "D": "300 m"},
        key="B",
        responseType="selected",
        figure={"kind": "diagram", "transcription": "right triangle 45-90, opposite 150 m, hypotenuse is the rope"},
        clusterId="pisa2012-PM923",
    ),
    item(
        id="pisa2012-PM924Q02",
        claim="formulate",
        stem="You are making your own dressing for a salad. Here is a recipe for 100 millilitres (mL) of dressing. Salad oil: 60 mL. Vinegar: 30 mL. Soy sauce: 10 mL. How many millilitres (mL) of salad oil do you need to make 150 mL of this dressing?",
        key="90",
        responseType="numeric",
    ),
    item(
        id="pisa2012-PM934Q01",
        claim="employ",
        stem="A giant Ferris wheel has an external diameter of 140 metres and its highest point is 150 metres above the bed of the river. The letter M in the diagram indicates the centre of the wheel. How many metres (m) above the bed of the river is point M?",
        key="80",
        responseType="numeric",
        figure={"kind": "diagram", "transcription": "wheel diameter 140 m; highest point 150 m above river bed; M is the centre"},
    ),
    item(
        id="pisa2012-PM942Q01",
        claim="formulate",
        stem="Mount Fuji is only open to the public for climbing from 1 July to 27 August each year. About 200 000 people climb Mount Fuji during this time. On average, about how many people climb Mount Fuji each day?",
        choices={"A": "340", "B": "710", "C": "3400", "D": "7100", "E": "7400"},
        key="C",
        responseType="selected",
        clusterId="pisa2012-PM942",
    ),
    item(
        id="pisa2012-PM942Q02",
        claim="formulate",
        stem="The Gotemba walking trail up Mount Fuji is about 9 kilometres (km) long. Walkers need to return from the 18 km walk by 8 pm. Toshi estimates that he can walk up the mountain at 1.5 kilometres per hour on average, and down at twice that speed. These speeds take into account meal breaks and rest times. Using Toshi's estimated speeds, what is the latest time he can begin his walk so that he can return by 8 pm?",
        key="11",
        responseType="numeric",
        clusterId="pisa2012-PM942",
    ),
    item(
        id="pisa2012-PM942Q03",
        claim="employ",
        stem="Toshi wore a pedometer to count his steps on his walk along the Gotemba trail. His pedometer showed that he walked 22 500 steps on the way up. Estimate Toshi's average step length for his walk up the 9 km Gotemba trail. Give your answer in centimetres (cm).",
        key="40",
        responseType="numeric",
        clusterId="pisa2012-PM942",
    ),
    item(
        id="pisa2012-PM957Q01",
        claim="employ",
        stem="On one trip, Helen rode 4 km in the first 10 minutes and then 2 km in the next 5 minutes. Which one of the following statements is correct?",
        choices={
            "A": "Helen's average speed was greater in the first 10 minutes than in the next 5 minutes.",
            "B": "Helen's average speed was the same in the first 10 minutes and in the next 5 minutes.",
            "C": "Helen's average speed was less in the first 10 minutes than in the next 5 minutes.",
            "D": "It is not possible to tell anything about Helen's average speed from the information given.",
        },
        key="B",
        responseType="selected",
        clusterId="pisa2012-PM957",
    ),
    item(
        id="pisa2012-PM957Q02",
        claim="employ",
        stem="Helen rode 6 km to her aunt's house. Her speedometer showed that she had averaged 18 km/h for the whole trip. Which one of the following statements is correct?",
        choices={
            "A": "It took Helen 20 minutes to get to her aunt's house.",
            "B": "It took Helen 30 minutes to get to her aunt's house.",
            "C": "It took Helen 3 hours to get to her aunt's house.",
            "D": "It is not possible to tell how long it took Helen to get to her aunt's house.",
        },
        key="A",
        responseType="selected",
        clusterId="pisa2012-PM957",
    ),
    item(
        id="pisa2012-PM957Q03",
        claim="employ",
        stem="Helen rode her bike from home to the river, which is 4 km away. It took her 9 minutes. She rode home using a shorter route of 3 km. This only took her 6 minutes. What was Helen's average speed, in km/h, for the trip to the river and back?",
        key="28",
        responseType="numeric",
        clusterId="pisa2012-PM957",
    ),
]


def main() -> None:
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ITEMS), encoding="utf-8")
    print(f"wrote {len(ITEMS)} PISA items -> {OUT}")


if __name__ == "__main__":
    main()
