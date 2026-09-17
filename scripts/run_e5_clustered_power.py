#!/usr/bin/env python3
"""E5: clustered minimum detectable bypass rate at 80% power for every cell with n>=10."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from addendum_lib import (
    ADDENDUM_DIR,
    MIN_N_WITNESS,
    Mulberry32,
    administration_id,
    chance_rate,
    cluster_bootstrap_ci,
    dump_json,
    load_items,
)


def min_detectable_clustered(
    cluster_sizes: list[int],
    chance: float,
    *,
    power: float = 0.8,
    n_power: int = 120,
    n_boot: int = 400,
    seed: int = 77,
) -> dict[str, Any]:
    n = sum(cluster_sizes)
    n_clusters = len(cluster_sizes)
    if n < MIN_N_WITNESS:
        return {
            "min_detectable_rate_clustered": None,
            "nClusters": n_clusters,
            "degenerate": n_clusters < 2,
            "note": f"n={n} below witness bar",
        }
    if n_clusters < 2:
        return {
            "min_detectable_rate_clustered": None,
            "nClusters": n_clusters,
            "degenerate": True,
            "note": "cluster bootstrap is degenerate with one administration; field left null rather than silently iid",
        }

    rng = Mulberry32(seed)

    def power_at(k: int) -> float:
        p = k / n
        wins = 0
        for trial in range(n_power):
            clusters: list[list[int]] = []
            for size in cluster_sizes:
                flags = [1 if rng.random() < p else 0 for _i in range(size)]
                clusters.append(flags)
            lo, _hi = cluster_bootstrap_ci(clusters, n_boot, seed + 1009 * k + trial)
            if lo > chance:
                wins += 1
        return wins / n_power

    lo_k = 0
    hi_k = n
    ans = n
    powers: dict[int, float] = {}
    while lo_k <= hi_k:
        mid = (lo_k + hi_k) // 2
        est = power_at(mid)
        powers[mid] = est
        if est >= power:
            ans = mid
            hi_k = mid - 1
        else:
            lo_k = mid + 1
    return {
        "min_detectable_rate_clustered": ans / n,
        "minDetectableCount": ans,
        "nItems": n,
        "nClusters": n_clusters,
        "chanceRate": chance,
        "power": power,
        "nPowerTrials": n_power,
        "nBoot": n_boot,
        "degenerate": False,
        "searchedPowers": {str(k): v for k, v in sorted(powers.items())},
    }


def main() -> None:
    items = load_items()
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_cell[(str(item["authority"]), str(item["claim"]))].append(item)

    rows: list[dict[str, Any]] = []
    for (authority, claim), subset in sorted(by_cell.items()):
        selected = [item for item in subset if item.get("responseType") == "selected"]
        n = len(selected)
        if n < MIN_N_WITNESS:
            continue
        chances = [chance_rate(item) for item in selected]
        chance_vals = [c for c in chances if c is not None]
        chance = sum(chance_vals) / len(chance_vals) if chance_vals else 0.25
        by_admin: dict[str, int] = defaultdict(int)
        for item in selected:
            by_admin[administration_id(item)] += 1
        sizes = [by_admin[key] for key in sorted(by_admin)]
        result = min_detectable_clustered(sizes, chance, seed=77 + n)
        rows.append(
            {
                "authority": authority,
                "claim": claim,
                "nSelected": n,
                "nItems": len(subset),
                "nClusters": len(sizes),
                "clusterSizes": sizes,
                "chanceRate": chance,
                "min_detectable_rate_clustered": result["min_detectable_rate_clustered"],
                "minDetectableCount": result.get("minDetectableCount"),
                "degenerate": result["degenerate"],
                "powerMeta": {k: result[k] for k in result if k not in {"searchedPowers"}},
                "cite": f"exports/addendum/power-by-cell.json rows[authority={authority} claim={claim}].min_detectable_rate_clustered",
            }
        )

    finite = [row for row in rows if row["min_detectable_rate_clustered"] is not None]
    payload = {
        "experiment": "E5",
        "question": (
            "At the observed administration clustering, what bypass rate is needed for "
            "80% power to clear the witness bar against format chance?"
        ),
        "field": "min_detectable_rate_clustered",
        "nCellsNAtLeast10": len(rows),
        "nCellsWithClusteredEstimate": len(finite),
        "minFloorAmongEligible": min((row["min_detectable_rate_clustered"] for row in finite), default=None),
        "rows": rows,
        "cite": "exports/addendum/power-by-cell.json",
    }
    dump_json(ADDENDUM_DIR / "power-by-cell.json", payload)
    print("wrote", ADDENDUM_DIR / "power-by-cell.json")
    print("cells", len(rows), "clustered estimates", len(finite))
    if finite:
        print("min floor", min(row["min_detectable_rate_clustered"] for row in finite))
        for row in sorted(finite, key=lambda r: r["min_detectable_rate_clustered"])[:8]:
            print(
                row["authority"],
                row["claim"],
                "n",
                row["nSelected"],
                "clusters",
                row["nClusters"],
                "mdr",
                round(row["min_detectable_rate_clustered"], 3),
            )


if __name__ == "__main__":
    main()
