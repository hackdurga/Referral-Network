"""simulation.py

Implements:
- simulate(p, days): deterministic expected-value simulation of referrals over time
  Model assumptions (explicit):
    * Start with `initial_referrers` active referrers; each referrer has `capacity` lives (max successful referrals).
    * Each day, every active referrer independently succeeds with probability p (at most one success per day).
    * A successful referral produces a new referrer with full capacity.
    * When a referrer achieves capacity successes, they become inactive.
  The simulation computes exact expected counts using linearity of expectation.
- days_to_target(p, target_total, ...): efficient early-stopping simulation to find min days to reach target expected referrals.
- min_bonus_for_target(days, target_hires, adoption_prob, eps): binary search on bonus (in $10 units) using simulate and adoption_prob(bonus).
"""

from typing import List, Optional, Callable

def simulate(p: float, days: int, initial_referrers: int = 100, capacity: int = 10) -> List[float]:
    """Return list cumulative_expected_referrals at end of each day (length = days).

    Uses a state vector A[c] = expected number of referrers with remaining capacity c (0..capacity).
    Index 0 counts inactive referrers (capacity exhausted).
    """
    if p < 0 or p > 1:
        raise ValueError("p must be between 0 and 1")

    # A[c]: expected number of referrers with remaining capacity c
    A = [0.0] * (capacity + 1)
    A[capacity] = float(initial_referrers)

    cumulative = []
    total_cumulative = 0.0

    for day in range(days):
        active = sum(A[1:])  # those with capacity >=1
        expected_new = p * active
        total_cumulative += expected_new

        # compute next day's distribution
        A_next = [0.0] * (capacity + 1)
        # successes produce new referrers with full capacity
        A_next[capacity] += expected_new

        for c in range(1, capacity + 1):
            group = A[c]
            successes = p * group
            fails = (1 - p) * group
            # those who fail remain with same capacity
            A_next[c] += fails
            # those who succeed move to c-1 (or become inactive when c-1 == 0)
            if c - 1 >= 1:
                A_next[c - 1] += successes
            else:
                A_next[0] += successes  # moved to inactive

        A = A_next
        cumulative.append(total_cumulative)
    return cumulative

def days_to_target(p: float, target_total: float, initial_referrers: int = 100,
                   capacity: int = 10, max_days: int = 100000) -> Optional[int]:
    """Return minimum number of days required for cumulative expected referrals to meet/exceed target_total.

    If not achievable within max_days, return None.
    """
    A = [0.0] * (capacity + 1)
    A[capacity] = float(initial_referrers)
    total_cumulative = 0.0

    for day in range(1, max_days + 1):
        active = sum(A[1:])
        expected_new = p * active
        total_cumulative += expected_new
        if total_cumulative >= target_total:
            return day
        # update
        A_next = [0.0] * (capacity + 1)
        A_next[capacity] += expected_new
        for c in range(1, capacity + 1):
            group = A[c]
            successes = p * group
            fails = (1 - p) * group
            A_next[c] += fails
            if c - 1 >= 1:
                A_next[c - 1] += successes
            else:
                A_next[0] += successes
        A = A_next
        # early exit: if active becomes extremely small (floating underflow) and expected_new < 1e-12, it's effectively stalled
        if sum(A[1:]) < 1e-12:
            break
    return None

def min_bonus_for_target(days: int, target_hires: int,
                          adoption_prob: Callable[[float], float],
                          eps: float = 1e-3,
                          initial_referrers: int = 100,
                          capacity: int = 10,
                          max_multiplier: int = 1 << 20) -> Optional[int]:
    """Find minimal bonus (rounded up to nearest $10) to meet target_hires in `days`.

    adoption_prob(bonus) -> p in [0,1], monotonic non-decreasing.
    We binary search over discrete bonuses in $10 increments.

    Returns integer bonus in dollars (multiple of 10), or None if unachievable within sensible cap.
    """
    # Helper to evaluate if a bonus reaches target
    def reaches(bonus):
        p = adoption_prob(bonus)
        if p <= 0:
            return False
        cum = simulate(p, days, initial_referrers=initial_referrers, capacity=capacity)
        return cum[-1] >= target_hires

    # Quick checks
    if reaches(0):
        return 0

    # find an upper bound by doubling
    lo = 0
    hi = 10
    while hi <= max_multiplier * 10:
        try:
            if reaches(hi):
                break
        except Exception:
            # adoption_prob may raise for extremely large bonuses; treat as unreachable
            return None
        hi *= 2

    if hi > max_multiplier * 10:
        return None

    # binary search on multiples of 10: search integers m where bonus = 10*m
    lo_m = lo // 10
    hi_m = hi // 10

    while lo_m < hi_m:
        mid_m = (lo_m + hi_m) // 2
        bonus_mid = mid_m * 10
        if reaches(bonus_mid):
            hi_m = mid_m
        else:
            lo_m = mid_m + 1

    return lo_m * 10