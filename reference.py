"""Compute the exact outer allocation for the twelve-stop dispatch case."""

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Case:
    forward_demand: int = 760
    reverse_demand: int = 789
    forward_peak: int = 420
    reverse_peak: int = 424
    loop_km: float = 30.407112627765024
    large_available: int = 50
    medium_available: int = 150
    direct_minibus_cost: float = 2889.713184077323


def exact_reference(case):
    """Return the best score and (large, medium) counts for each direction.

    Assumes feasible direct minibus requirements and positive marginal costs.
    Uses the manuscript's class coefficients and effective seating capacities.
    """
    large_cost = case.loop_km * 2 - 1
    medium_cost = case.loop_km * (2.75 / 3 + 2.8 / 3) - 0.9 / 1.2
    needs = (max(case.forward_demand, case.forward_peak),
             max(case.reverse_demand, case.reverse_peak))
    best = None
    for forward in range(case.large_available + 1):
        for reverse in range(case.large_available - forward + 1):
            medium_forward = max(0, ceil((needs[0] - 30 * forward) / 8))
            medium_reverse = max(0, ceil((needs[1] - 30 * reverse) / 8))
            medium_total = medium_forward + medium_reverse
            if medium_total > case.medium_available:
                continue
            score = case.direct_minibus_cost + (forward + reverse) * large_cost + medium_total * medium_cost
            if best is None or score < best[0]:
                best = (score, (forward, medium_forward, reverse, medium_reverse))
    if best is None:
        raise ValueError("Fixed-route demand exceeds the available fleet capacity.")
    return best


if __name__ == "__main__":
    score, counts = exact_reference(Case())
    print(f"Optimal normalized objective: {score:.6f}")
    print(f"Forward (large, medium): {counts[:2]}")
    print(f"Reverse (large, medium): {counts[2:]}")
