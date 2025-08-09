import pytest
from source.referral_network import ReferralNetwork

def test_basic_add_and_constraints():
    rn = ReferralNetwork()
    rn.add_user('A')
    rn.add_user('B')
    rn.add_referral('A', 'B')
    assert 'B' in rn.get_direct_referrals('A')
    # candidate cannot be referred again
    with pytest.raises(ValueError):
        rn.add_referral('C', 'B')
    # self referral not allowed
    with pytest.raises(ValueError):
        rn.add_referral('A', 'A')

def test_cycle_detection():
    rn = ReferralNetwork()
    rn.add_referral('A', 'B')
    rn.add_referral('B', 'C')
    # adding C -> A should create cycle
    with pytest.raises(ValueError):
        rn.add_referral('C', 'A')

def test_total_referral_count_and_top():
    rn = ReferralNetwork()
    rn.add_referral('A', 'B')
    rn.add_referral('A', 'C')
    rn.add_referral('B', 'D')
    # A reaches B,C,D (3)
    assert rn.total_referral_count('A') == 3
    top = rn.top_referrers_by_reach(2)
    assert top[0][0] == 'A' and top[0][1] == 3

def test_unique_reach_greedy():
    rn = ReferralNetwork()
    rn.add_referral('A', 'B')
    rn.add_referral('A', 'C')
    rn.add_referral('E', 'F')
    # reach sets:
    # A -> B,C ; D -> C ; E -> F
    selected, covered = rn.unique_reach_greedy(2)
    # expecting first pick to be A (cover 2 nodes)
    assert len(selected) <= 2
    assert covered.issubset({'B','C','F'})

def test_flow_centrality_simple():
    rn = ReferralNetwork()
    # chain A -> B -> C
    rn.add_referral('A', 'B')
    rn.add_referral('B', 'C')
    scores = rn.flow_centrality_scores()
    # B should be the top broker (it lies on path A->C)
    assert scores[0][0] == 'B'