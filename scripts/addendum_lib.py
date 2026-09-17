#!/usr/bin/env python3
"""Shared scoring helpers for addendum experiments. Matches runner TypeScript."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
ITEMS_PATH = ROOT / "data" / "items.jsonl"
ADDENDUM_DIR = ROOT / "exports" / "addendum"

MIN_N_WITNESS = 10
CHANCE_SELECTED = 0.25
SESSION_ORDER = {"jan": 1, "jun": 6, "aug": 8, "unk": 9}

ABSOLUTE_RE = re.compile(
    r"\b(always|never|all|none|only|every|impossible|certainly)\b",
    re.I,
)
HEDGE_RE = re.compile(
    r"\b("
    r"sometimes|often|usually|generally|typically|seldom|rarely|"
    r"occasionally|frequently|ordinarily|perhaps|possibly|probably|"
    r"maybe|approximately|nearly|roughly|about|around|"
    r"relatively|somewhat|mostly|likely|"
    r"tends|tend|may|might|could|"
    r"few|many|some|most"
    r")\b",
    re.I,
)
LEADING_NUMBER_RE = re.compile(r"^[^\d-]*(-?\d+(?:\.\d+)?)")
FRACTION_RE = re.compile(r"^(-?\d+)\s*/\s*(-?\d+)$")
REGENTS_ID_RE = re.compile(
    r"^nyregents-[a-z0-9-]+-(\d{4})-(jan|jun|aug|unk)-q\d+",
    re.I,
)
YEAR_IN_ID_RE = re.compile(r"(?:^|-)((?:19|20)\d{2})(?:-|$)")
STAAR_FOOTER_RE = re.compile(r"\b\d{5}_\d\b")
PAGE_FOOTER_RE = re.compile(
    r"(?i)(computations\.|\[over\]|page\s+\d+|geometry\s+[–—-]\s+"
    r"(jan|june|aug|august)\.?|algebra(?:\s*ii)?\s+[–—-])"
)
COUNTRY_FRAGMENT_RE = re.compile(
    r"(?i)\b("
    r"singapore|singapor|lithuania|lithuani|slovenia|sweden|norway|"
    r"ukraine|turkey|israel|qatar|armenia|georgia|thailand|malaysia|"
    r"kazakhstan|romania|croatia|poland|denmark|finland|portugal|"
    r"serbia|malta|oman|ghana|bahrain|bahra|syria|tunisia|tunis|"
    r"morocco|azerbaijan|azerbaija|belgium|netherlands|netherla|"
    r"australia|austria|ireland|spain|slovak|chinese|taipei|"
    r"hong\s*kong|hong\s*ko|new\s*zeal|united\s*a|united\s*ar|"
    r"russian\s*f|england-?|internat|palestinian|palestin|"
    r"northern\s*ireland|czech\s*r|iran,?\s*is"
    r")\b"
)


def tokenize(text: str) -> list[str]:
    return [tok for tok in re.split(r"[^a-z0-9]+", text.lower()) if len(tok) >= 2]


def parse_leading_number(text: str) -> float | None:
    match = LEADING_NUMBER_RE.match(text.strip())
    if not match:
        return None
    value = float(match.group(1))
    return value if math.isfinite(value) else None


def parse_fraction(text: str) -> float | None:
    match = FRACTION_RE.match(text.strip())
    if not match:
        return None
    denom = float(match.group(2))
    if denom == 0:
        return None
    return float(match.group(1)) / denom


def answers_match(expected: str, got: str) -> bool:
    left = expected.strip()
    right = got.strip()
    if left.lower() == right.lower():
        return True
    try:
        number_left = float(left.replace(",", ""))
        number_right = float(right.replace(",", ""))
    except ValueError:
        number_left = None
        number_right = None
    if number_left is not None and number_right is not None:
        scale = max(1.0, abs(number_left))
        if abs(number_left - number_right) <= 1e-6 * scale or abs(number_left - number_right) < 0.005:
            return True
    frac_left = parse_fraction(left)
    frac_right = parse_fraction(right)
    if frac_left is not None and frac_right is not None:
        return abs(frac_left - frac_right) < 1e-6
    return False


def choice_keys(item: dict[str, Any]) -> list[str]:
    return sorted((item.get("choices") or {}).keys())


def parsed_numeric_options(item: dict[str, Any]) -> list[tuple[str, float]]:
    choices = item.get("choices") or {}
    parsed: list[tuple[str, float]] = []
    for key in choice_keys(item):
        value = parse_leading_number(str(choices.get(key, "")))
        if value is not None:
            parsed.append((key, value))
    parsed.sort(key=lambda row: (row[1], row[0]))
    return parsed


def pick_first(keys: list[str]) -> str | None:
    return keys[0] if keys else None


def unique_max_keys(scores: dict[str, float], require_positive: bool = True) -> str | None:
    if not scores:
        return None
    best = -math.inf
    winners: list[str] = []
    for key in sorted(scores):
        value = scores[key]
        if value > best:
            best = value
            winners = [key]
        elif value == best:
            winners.append(key)
    if len(winners) != 1:
        return None
    if require_positive and best <= 0:
        return None
    return winners[0]


def chance_rate(item: dict[str, Any]) -> float | None:
    if item.get("responseType") != "selected":
        return None
    n_choices = len(item.get("choices") or {})
    return 1.0 / n_choices if n_choices > 0 else None


def load_items(path: Path = ITEMS_PATH) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("role") == "retrieval-pool":
            continue
        rows.append(item)
    return rows


def administration_id(item: dict[str, Any]) -> str:
    item_id = str(item.get("id", ""))
    corpus = str(item.get("corpus", ""))
    year = str(item.get("year") or "")
    cluster = str(item.get("clusterId") or "")
    match = REGENTS_ID_RE.match(item_id)
    if match:
        return f"{corpus}:{match.group(1)}-{match.group(2).lower()}"
    if corpus.startswith("eqao") or item.get("authority") == "eqao":
        year_match = re.match(r"eqao-(\d{4})-", item_id)
        return f"eqao:{year_match.group(1) if year_match else year or 'unknown'}"
    if corpus == "staar" or item.get("authority") == "teks":
        year_match = re.match(r"staar-(\d{4})-", item_id)
        return f"staar:{year_match.group(1) if year_match else year or 'unknown'}"
    if corpus.startswith("timss"):
        grade = str(item.get("grade") or "unk")
        return f"{corpus}:g{grade}"
    if cluster:
        return f"{corpus}:{cluster}"
    year_in_id = YEAR_IN_ID_RE.search(item_id)
    if year_in_id:
        return f"{corpus}:{year_in_id.group(1)}"
    if year:
        return f"{corpus}:{year}"
    return f"{corpus}:{item_id}"


def administration_sort_key(admin_id: str) -> tuple[str, int, int]:
    body = admin_id.split(":", 1)[-1]
    year_match = re.search(r"(19|20)\d{2}", body)
    year = int(year_match.group(0)) if year_match else 0
    session = 0
    for name, order in SESSION_ORDER.items():
        if re.search(rf"\b{name}\b", body):
            session = order
            break
    return (admin_id.split(":", 1)[0], year, session)


def to_int32(value: int) -> int:
    value = value % (2**32)
    if value >= 2**31:
        value -= 2**32
    return value


def to_uint32(value: int) -> int:
    return value % (2**32)


def math_imul(left: int, right: int) -> int:
    return to_int32(to_int32(left) * to_int32(right))


class Mulberry32:
    """Port of runner/src/stats.ts mulberry32."""

    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def random(self) -> float:
        self.state += 0x6D2B79F5
        t = int(self.state)
        t = math_imul(t ^ (to_uint32(t) >> 15), t | 1)
        t = t ^ (t + math_imul(t ^ (to_uint32(t) >> 7), t | 61))
        t = to_int32(t)
        return to_uint32(t ^ (to_uint32(t) >> 14)) / 4294967296.0


def bootstrap_ci_mulberry(
    flags: list[int],
    n_boot: int = 1000,
    seed: int = 11,
) -> tuple[float, float]:
    if not flags:
        return (0.0, 0.0)
    rng = Mulberry32(seed)
    n = len(flags)
    stats: list[float] = []
    for _ in range(n_boot):
        total = 0
        for _i in range(n):
            total += flags[int(math.floor(rng.random() * n))]
        stats.append(total / n)
    stats.sort()
    low = stats[int(math.floor(0.025 * n_boot))]
    high = stats[min(n_boot - 1, int(math.floor(0.975 * n_boot)))]
    return (low, high)


def cluster_bootstrap_ci(
    clusters: list[list[int]],
    n_boot: int = 2000,
    seed: int = 20260916,
) -> tuple[float, float]:
    if not clusters:
        return (0.0, 0.0)
    rng = Mulberry32(seed)
    n_clusters = len(clusters)
    sums = [sum(cluster) for cluster in clusters]
    sizes = [len(cluster) for cluster in clusters]
    stats: list[float] = []
    for _ in range(n_boot):
        total = 0
        count = 0
        for _i in range(n_clusters):
            index = int(math.floor(rng.random() * n_clusters))
            total += sums[index]
            count += sizes[index]
        stats.append(total / count if count else 0.0)
    stats.sort()
    low = stats[int(math.floor(0.025 * n_boot))]
    high = stats[min(n_boot - 1, int(math.floor(0.975 * n_boot)))]
    return (low, high)


def binomial_sf(k: int, n: int, p: float) -> float:
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    log_term = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log(1.0 - p)
    )
    term = math.exp(min(log_term, 700.0))
    total = 0.0
    for i in range(k, n + 1):
        total += term
        if total >= 1.0:
            return 1.0
        if i == n:
            break
        term *= (n - i) / (i + 1) * p / (1.0 - p)
    return min(1.0, total)


def holm_reject(p_values: list[float], alpha: float = 0.05) -> list[bool]:
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    rejected = [False] * m
    for rank, index in enumerate(order):
        threshold = alpha / (m - rank)
        if p_values[index] <= threshold:
            rejected[index] = True
        else:
            break
    return rejected


@dataclass
class ScoredItem:
    item: dict[str, Any]
    answer: str
    correct: bool
    chance: float
    administration: str


def score_program(
    items: Iterable[dict[str, Any]],
    program: Callable[[dict[str, Any]], str | None],
) -> list[ScoredItem]:
    scored: list[ScoredItem] = []
    for item in items:
        if item.get("responseType") != "selected":
            continue
        answer = program(item)
        if answer is None:
            continue
        chance = chance_rate(item)
        if chance is None:
            continue
        scored.append(
            ScoredItem(
                item=item,
                answer=answer,
                correct=answers_match(str(item["key"]), answer),
                chance=chance,
                administration=administration_id(item),
            )
        )
    return scored


def summarize_scored(
    scored: list[ScoredItem],
    *,
    item_seed: int = 11,
    cluster_seed: int = 20260916,
    n_boot: int = 2000,
) -> dict[str, Any]:
    flags = [1 if row.correct else 0 for row in scored]
    n = len(flags)
    n_correct = sum(flags)
    rate = n_correct / n if n else 0.0
    chance = sum(row.chance for row in scored) / n if n else 0.0
    item_ci = bootstrap_ci_mulberry(flags, 1000, item_seed) if n else (0.0, 0.0)
    by_admin: dict[str, list[int]] = defaultdict(list)
    for row, flag in zip(scored, flags):
        by_admin[row.administration].append(flag)
    clusters = [by_admin[key] for key in sorted(by_admin)]
    clustered_ci = cluster_bootstrap_ci(clusters, n_boot, cluster_seed) if clusters else (0.0, 0.0)
    return {
        "n": n,
        "nCorrect": n_correct,
        "passRate": rate,
        "chanceRate": chance,
        "itemBootstrapCi95": [item_ci[0], item_ci[1]],
        "clusterBootstrapCi95": [clustered_ci[0], clustered_ci[1]],
        "nAdministrations": len(clusters),
        "clearsItemBar": n >= MIN_N_WITNESS and item_ci[0] > chance,
        "clearsClusterBar": n >= MIN_N_WITNESS and clustered_ci[0] > chance,
    }


def lower_central_key(parsed: list[tuple[str, float]]) -> str | None:
    if len(parsed) < 3:
        return None
    mid_value = parsed[math.floor((len(parsed) - 1) / 2)][1]
    return pick_first([key for key, value in parsed if value == mid_value])


def upper_central_key(parsed: list[tuple[str, float]]) -> str | None:
    if len(parsed) < 3:
        return None
    mid_value = parsed[math.ceil((len(parsed) - 1) / 2)][1]
    return pick_first([key for key, value in parsed if value == mid_value])


def nearest_mean_key(parsed: list[tuple[str, float]]) -> str | None:
    if len(parsed) < 3:
        return None
    mean_value = sum(value for _key, value in parsed) / len(parsed)
    distances = {key: abs(value - mean_value) for key, value in parsed}
    best = min(distances.values())
    winners = sorted(key for key, distance in distances.items() if distance == best)
    return winners[0] if len(winners) == 1 else pick_first(winners)


def smallest_key(parsed: list[tuple[str, float]]) -> str | None:
    if len(parsed) < 3:
        return None
    min_value = parsed[0][1]
    return pick_first([key for key, value in parsed if value == min_value])


def largest_key(parsed: list[tuple[str, float]]) -> str | None:
    if len(parsed) < 3:
        return None
    max_value = parsed[-1][1]
    return pick_first([key for key, value in parsed if value == max_value])


def middle_value_option(item: dict[str, Any]) -> str | None:
    return lower_central_key(parsed_numeric_options(item))


NUMERIC_RULES: dict[str, Callable[[list[tuple[str, float]]], str | None]] = {
    "lower-central": lower_central_key,
    "upper-central": upper_central_key,
    "nearest-to-arithmetic-mean": nearest_mean_key,
    "smallest": smallest_key,
    "largest": largest_key,
}


def most_qualified_hedged_option(item: dict[str, Any]) -> str | None:
    choices = item.get("choices") or {}
    scores: dict[str, float] = {}
    for key in choice_keys(item):
        text = str(choices.get(key, ""))
        scores[key] = float(len(HEDGE_RE.findall(text)))
    return unique_max_keys(scores, require_positive=True)


def convergence_option(item: dict[str, Any]) -> str | None:
    choices = item.get("choices") or {}
    keys = choice_keys(item)
    if len(keys) < 2:
        return None
    elements: dict[str, set[str]] = {}
    for key in keys:
        text = str(choices.get(key, ""))
        toks = set(tokenize(text))
        number = parse_leading_number(text)
        if number is not None:
            toks.add(f"num:{number}")
            compact = re.sub(r"[^\d-]", "", text.strip())
            if compact:
                toks.add(f"digits:{compact}")
        elements[key] = toks
    scores: dict[str, float] = {}
    for key in keys:
        score = 0.0
        own = elements[key]
        for other in keys:
            if other == key:
                continue
            score += float(len(own & elements[other]))
        scores[key] = score
    return unique_max_keys(scores, require_positive=True)


def grammatical_fit_option(item: dict[str, Any]) -> str | None:
    stem = str(item.get("stem", "")).rstrip()
    wants_an = bool(re.search(r"(?i)\ban\s*$|\ban\s+_+\s*$", stem))
    wants_a = bool(re.search(r"(?i)\ba\s*$|\ba\s+_+\s*$", stem))
    if not wants_an and not wants_a:
        return None
    choices = item.get("choices") or {}
    fit: list[str] = []
    unfit: list[str] = []
    for key in choice_keys(item):
        text = str(choices.get(key, "")).strip()
        first = text[:1]
        vowel = bool(re.match(r"[aeiou]", first, re.I))
        agrees = (wants_an and vowel) or (wants_a and bool(first) and not vowel)
        (fit if agrees else unfit).append(key)
    if len(fit) == 1 and unfit:
        return fit[0]
    return None


def mean_of_other_options(item: dict[str, Any]) -> str | None:
    parsed = parsed_numeric_options(item)
    if len(parsed) < 3:
        return None
    total = sum(value for _key, value in parsed)
    distances: dict[str, float] = {}
    for key, value in parsed:
        others_mean = (total - value) / (len(parsed) - 1)
        distances[key] = abs(value - others_mean)
    best = min(distances.values())
    winners = sorted(key for key, distance in distances.items() if distance == best)
    if len(winners) != 1:
        return None
    return winners[0]


EXTENDED_PROGRAMS: dict[str, Callable[[dict[str, Any]], str | None]] = {
    "most-qualified-hedged-option": most_qualified_hedged_option,
    "convergence-option": convergence_option,
    "grammatical-fit-option": grammatical_fit_option,
    "mean-of-other-options": mean_of_other_options,
}

EXTENDED_CITATIONS = {
    "most-qualified-hedged-option": (
        "Millman, Bishop, and Ebel (1965) specific determiners / qualified language; "
        "Haladyna, Downing, and Rodriguez (2002) guideline against absolute wording "
        "and on similar-specificity options. Mechanical: unique maximum hedge-token count."
    ),
    "convergence-option": (
        "Millman, Bishop, and Ebel (1965) convergence strategy: choose the option that "
        "shares the most elements with the other options. Applied to word tokens and, "
        "for numeric options, the parsed number and digit string."
    ),
    "grammatical-fit-option": (
        "Millman, Bishop, and Ebel (1965) grammatical cue; Haladyna, Downing, and "
        "Rodriguez (2002) stem-option grammatical consistency. Applies only when the "
        "stem ends in a/an and exactly one option uniquely fits."
    ),
    "mean-of-other-options": (
        "Numeric companion to central-tendency test-wiseness (Millman et al. 1965; "
        "Haladyna et al. 2002 ordered numeric options). Pick the unique option closest "
        "to the mean of the remaining parsed option values; abstain on ties or fewer "
        "than three parsed numbers."
    ),
}


ENGLISH = set(
    "the of and to a in is it you that he was for on are with as his they be at one "
    "have this from or had by hot word but what some we can out other were all there "
    "when up use your how said each she which their time if will way about many then "
    "them write would like so these her long make thing see him two more has look day "
    "could go come did number sound no most people my over know water than call first "
    "who may down side been now find any new work part take get place made live where "
    "after back little only round year came show every good me give our under name very "
    "through just form sentence great think say help low line differ turn cause much "
    "mean before move right boy old too same tell does set three want air well also "
    "play small end put home read hand port large spell add even land here must high "
    "such follow act why ask men change went light kind off need house picture try us "
    "again animal point mother world near build self earth father head stand own page "
    "should country found answer school grow study still learn plant cover food sun four "
    "between state keep eye never last let thought city tree cross farm hard start might "
    "story saw far sea draw left late run don't while press close night real life few "
    "north open seem together next white children begin got walk example ease paper group "
    "always music those both mark often letter until book last room sea".split()
)
FEATURE_NAMES = [
    "longest",
    "positionC",
    "overlap",
    "numRepeat",
    "noAbsolute",
    "numericMin",
    "numericMed",
    "numericMax",
    "specificity",
    "grammarAgree",
    "distinctive",
]


def feature_matrix(item: dict[str, Any]) -> dict[str, dict[str, float]]:
    choices = item.get("choices") or {}
    letters = sorted(choices.keys())
    stem_tokens = {tok for tok in tokenize(str(item.get("stem", ""))) if len(tok) >= 4}
    stem_nums = re.findall(r"-?\d+(?:[.,]\d+)?", str(item.get("stem", "")))
    lengths = {key: len(str(choices.get(key, ""))) for key in letters}
    max_len = max(lengths.values()) if lengths else 0
    nums = [(key, parse_leading_number(str(choices.get(key, "")))) for key in letters]
    parsed = [(key, value) for key, value in nums if value is not None]
    parsed.sort(key=lambda row: row[1])
    min_v = parsed[0][1] if parsed else None
    max_v = parsed[-1][1] if parsed else None
    med_v = parsed[math.floor((len(parsed) - 1) / 2)][1] if parsed else None
    option_tokens = {key: set(tokenize(str(choices.get(key, "")))) for key in letters}
    stem = str(item.get("stem", "")).strip()
    wants_an = bool(re.search(r"(?i)\ban\s*$|\ban\s+_+\s*$", stem))
    wants_a = bool(re.search(r"(?i)\ba\s*$|\ba\s+_+\s*$", stem))
    matrix: dict[str, dict[str, float]] = {}
    for key in letters:
        text = str(choices.get(key, ""))
        toks = list(option_tokens[key])
        overlap = float(sum(1 for tok in toks if tok in stem_tokens))
        letter_match = re.match(r"^[A-Za-z]", text.strip())
        first = letter_match.group(0) if letter_match else ""
        vowel = bool(re.match(r"(?i)[aeiou]", first))
        grammar = 0.0
        if wants_an:
            grammar = 1.0 if vowel else 0.0
        elif wants_a:
            grammar = 1.0 if first and not vowel else 0.0
        english_hits = float(sum(1 for tok in toks if tok in ENGLISH))
        sim = 0.0
        others = 0
        for other in letters:
            if other == key:
                continue
            left = option_tokens[key]
            right = option_tokens[other]
            inter = len(left & right)
            union = len(left | right) or 1
            sim += inter / union
            others += 1
        mean_sim = sim / others if others else 0.0
        value = next((row[1] for row in nums if row[0] == key), None)
        matrix[key] = {
            "longest": 1.0 if lengths[key] == max_len and list(lengths.values()).count(max_len) == 1 else 0.0,
            "positionC": 1.0 if key == "C" else 0.0,
            "overlap": overlap,
            "numRepeat": 1.0 if any(num in text for num in stem_nums) else 0.0,
            "noAbsolute": 0.0 if ABSOLUTE_RE.search(text) else 1.0,
            "numericMin": 1.0
            if parsed and len(parsed) >= 2 and value == min_v and sum(1 for _k, v in parsed if v == min_v) == 1
            else 0.0,
            "numericMed": 1.0
            if parsed and len(parsed) >= 3 and value == med_v and sum(1 for _k, v in parsed if v == med_v) == 1
            else 0.0,
            "numericMax": 1.0
            if parsed and len(parsed) >= 2 and value == max_v and sum(1 for _k, v in parsed if v == max_v) == 1
            else 0.0,
            "specificity": english_hits + len(toks) * 0.1,
            "grammarAgree": grammar,
            "distinctive": 1.0 - mean_sim,
        }
    return matrix


def unique_max(scores: dict[str, float], require_positive: bool = True, allow_tie_first: bool = False) -> str | None:
    letters = sorted(scores)
    if not letters:
        return None
    best = -math.inf
    winners: list[str] = []
    for key in letters:
        value = scores[key]
        if value > best:
            best = value
            winners = [key]
        elif value == best:
            winners.append(key)
    if allow_tie_first and winners:
        return winners[0]
    if len(winners) != 1:
        return None
    if require_positive and best <= 0:
        return None
    return winners[0]


def parse_weighted_program(program_id: str) -> dict[str, Any]:
    body = program_id
    if body.startswith("search/"):
        body = body[len("search/") :]
    body = body.split("/")[0]
    if body.startswith("w:"):
        weights: dict[str, float] = {}
        features: list[str] = []
        for part in body[2:].split(","):
            match = re.match(r"([A-Za-z]+)([+-]\d+)$", part)
            if not match:
                raise ValueError(f"cannot parse weighted feature {part} in {program_id}")
            name = match.group(1)
            weight = float(match.group(2))
            features.append(name)
            weights[name] = weight
        return {
            "id": program_id,
            "kind": "weighted",
            "features": features,
            "weights": weights,
            "complexity": len(features),
        }
    if body.startswith("atom:"):
        name = body.split(":", 1)[1]
        return {
            "id": program_id,
            "kind": "atomic",
            "features": [name],
            "weights": {name: 1.0},
            "complexity": 1,
        }
    if body.startswith("and:"):
        features = body.split(":", 1)[1].split("+")
        return {
            "id": program_id,
            "kind": "conjunction",
            "features": features,
            "weights": {name: 1.0 for name in features},
            "complexity": 2,
        }
    raise ValueError(f"unsupported program id {program_id}")


def apply_cue_program(program: dict[str, Any], item: dict[str, Any]) -> str | None:
    letters = sorted((item.get("choices") or {}).keys())
    if not letters:
        return None
    matrix = feature_matrix(item)
    scores: dict[str, float] = {}
    for key in letters:
        if program["kind"] == "conjunction":
            values = [matrix[key].get(feat, 0.0) for feat in program["features"]]
            score = sum(values) if all(value > 0 for value in values) else 0.0
        else:
            score = 0.0
            for feat in program["features"]:
                score += program["weights"].get(feat, 0.0) * matrix[key].get(feat, 0.0)
        scores[key] = score
    if program["kind"] == "random":
        return unique_max(scores, require_positive=False, allow_tie_first=True)
    return unique_max(scores)


def option_features(item: dict[str, Any], letter: str) -> list[str]:
    choices = item.get("choices") or {}
    option = str(choices.get(letter, ""))
    stem_tokens = [tok for tok in tokenize(str(item.get("stem", ""))) if len(tok) >= 3]
    option_tokens = [tok for tok in tokenize(option) if len(tok) >= 3]
    stem_set = set(stem_tokens)
    feats: list[str] = []
    for tok in option_tokens:
        feats.append(f"o:{tok}")
        if tok in stem_set:
            feats.append(f"ov:{tok}")
    compact = re.sub(r"[^a-z0-9]+", " ", option.lower())
    for i in range(0, min(len(compact) - 2, 60)):
        feats.append(f"c3:{compact[i : i + 3]}")
    surf_longest = []
    lengths = {key: len(str(choices.get(key, ""))) for key in sorted(choices)}
    if lengths:
        max_len = max(lengths.values())
        surf_longest = [key for key, length in lengths.items() if length == max_len]
    parsed = parsed_numeric_options(item)
    middle = lower_central_key(parsed)
    stem_nums = re.findall(r"-?\d+(?:[.,]\d+)?", str(item.get("stem", "")))
    if letter in surf_longest:
        feats.append("cue:longest")
    if middle == letter:
        feats.append("cue:middle")
    if any(num in option for num in stem_nums):
        feats.append("cue:numrepeat")
    feats.append(f"pos:{letter}")
    feats.append(f"len:{min(8, math.floor(len(option) / 12))}")
    return feats


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
