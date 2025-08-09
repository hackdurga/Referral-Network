import math
from source.simulation import simulate, days_to_target, min_bonus_for_target

def test_simulate_zero_prob():
    cum = simulate(0.0, 10)
    assert all(c == 0.0 for c in cum)

def test_simulate_full_prob_small_days():
    cum = simulate(1.0, 3, initial_referrers=1, capacity=2)
    # With p=1 and 1 initial referrer with capacity=2:
    # Day1: active=1 -> new=1, cumulative=1
    # Day2: active=1 (original now has capacity1, new has capacity2) -> new=1, cumulative=2
    # Day3: new successes continue, cumulative=3
    assert len(cum) == 3
    assert cum[0] == 1.0

def test_days_to_target_and_min_bonus():
    # simple linear adoption_prob: p = min(1, bonus / 100)
    def adoption(bonus):
        return min(1.0, bonus / 100.0)

    # target small achievable with small bonus
    bonus = min_bonus_for_target(days=5, target_hires=5, adoption_prob=adoption)
    assert bonus is not None
    # days_to_target with p=0.1 should eventually reach small target
    d = days_to_target(0.1, 1, initial_referrers=100, capacity=10)
    assert d is not None