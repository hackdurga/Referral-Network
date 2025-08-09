# Mercor Challenge – Referral Network (Python)

I implemented the Referral Network exercise in Python. The repo includes the core graph model, influence metrics, a deterministic referral simulation, and tests that validate the main requirements from the assignment.

## 1. Language & Setup
Python 3.8+ (developed & tested on 3.12)

Create & activate a virtual environment (recommended):
```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS / Linux (bash/zsh)
source .venv/bin/activate
```
Install dependencies & run tests:
```bash
python -m pip install -r requirements.txt
pytest -q
```

## 2. Repository Structure
```
mercor_challenge/
├── README.md                # This file  
├── requirements.txt         # Dependency manifest (runtime + tests)
├── source/
│   ├── referral_network.py  # Parts 1–3 (graph + reach + influencer metrics)
│   └── simulation.py        # Parts 4–5 (growth simulation + bonus optimization)
└── tests/
    ├── test_referral_network.py
    └── test_simulation.py
```

## 3. Design Choices (Part 1 – Referral Graph)
Data structure: Directed Acyclic Graph with a unique incoming edge per candidate.

Internal state:
- `adj: dict[str, set[str]]` — outgoing edges (referrer -> candidates)
- `rev: dict[str, str]` — candidate -> single referrer (O(1) uniqueness enforcement)
- `users: set[str]` — all known users

`add_referral(referrer, candidate)` enforces:
1. No self-referral (referrer != candidate)
2. Unique referrer (`candidate not in rev`)
3. Acyclicity: BFS from candidate to check if referrer is reachable (would form a cycle)

Complexity:
- add_referral: O(E) worst-case (BFS) ; space O(V+E)
- get_direct_referrals: O(outdegree)

## 4. Full Network Reach (Part 2)
Definitions & Functions:
- `reach_set(user)`: BFS to collect all downstream unique nodes (direct + indirect) – O(V+E)
- `total_referral_count(user)`: size of reach_set
- `top_referrers_by_reach(k)`: compute reach for each user, sort, take top k (naive O(V*(V+E)))

Choosing k: (a) team review bandwidth (e.g. number analysts can vet), (b) stop when marginal added reach < threshold (plateau), or (c) reporting overview (k ≈ √V).

## 5. Identify Influencers (Part 3)
Implemented Metrics:
1. Reach (single-node downstream size) – breadth of influence.
2. Unique Reach Greedy (`unique_reach_greedy(m)`): Precompute each user’s reach set; iteratively pick user with maximum marginal uncovered nodes (standard set cover heuristic).
3. Flow Centrality (`flow_centrality_scores()`): For each source run BFS distances; a node v gets +1 for ordered pair (s,t) if `dist(s,v)+dist(v,t)=dist(s,t)` and v ∉ {s,t}. Emphasizes brokerage.

Business Scenarios:
- Reach: Initial seeding / broad awareness.
- Unique Reach: Selecting limited ambassador cohort while minimizing overlap.
- Flow Centrality: Finding structural bridges whose involvement (or removal) affects cross-cluster connectivity.

## 6. Network Growth Simulation (Part 4)
Model Parameters (fixed):
- 100 initial active referrers
- Each has capacity = 10 successful referrals (then becomes inactive)
- Discrete days; per day each active referrer succeeds with probability p (≤ 1 success/day)

Functions:
- `simulate(p, days, initial_referrers=100, capacity=10)` → list[float] cumulative expected referrals per day. Uses capacity buckets A[c] (expected count with c remaining). Time O(days * capacity), space O(capacity).
- `days_to_target(p, target_total, ...)` → minimum days until cumulative expected referrals ≥ target or None. Time O(D * capacity) where D is returned day.

## 7. Referral Bonus Optimization (Part 5)
Goal: Find minimal bonus (multiple of $10) so expected cumulative hires after `days` ≥ `target_hires`.
Assumptions: `adoption_prob(bonus)` is monotone non-decreasing.
Algorithm (`min_bonus_for_target`):
1. If bonus 0 already works, return 0.
2. Exponential search (double bonus ceiling) to find upper bound B.
3. Binary search on [0, B] in $10 increments; each step calls `simulate` with p = adoption_prob(bonus).
Complexity: O((log B*) * days * capacity) where B* is minimal satisfying bonus; space O(capacity).

## 8. Metric & Algorithm Complexity Summary
| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| add_referral | O(E) | O(V+E) | BFS cycle check |
| get_direct_referrals | O(outdeg) | O(1) | set -> list |
| reach_set / total_referral_count | O(V+E) | O(V) | BFS |
| top_referrers_by_reach | O(V*(V+E)) | O(V) | naive recompute |
| unique_reach_greedy (after precompute) | O(V*(V+E) + m*V) | O(V^2) worst | set cover heuristic |
| flow_centrality_scores | O(V*(V+E)) | O(V^2) | BFS from every node + counting |
| simulate | O(days*capacity) | O(capacity) | deterministic expected values |
| days_to_target | O(D*capacity) | O(capacity) | stops early when target met |
| min_bonus_for_target | O((log B*)*days*capacity) | O(capacity) | exponential + binary search |

## 9. Tests (Single Command)
Run all tests:
```bash
pytest -q
```
Coverage: constraint enforcement (self, unique, cycle), reach & ranking, unique reach greedy, flow centrality (broker path), simulation (p=0 & p=1), bonus search feasibility.

## 10. Usage Snippets
```bash
# Add referrals & compute reach
python -c "from source.referral_network import ReferralNetwork as R; rn=R(); rn.add_referral('A','B'); rn.add_referral('B','C'); print(rn.total_referral_count('A'))"
# Unique reach selection (m=2)
python -c "from source.referral_network import ReferralNetwork as R; rn=R(); rn.add_referral('A','B'); rn.add_referral('A','C'); rn.add_referral('D','E'); print(rn.unique_reach_greedy(2))"
# Flow centrality
python -c "from source.referral_network import ReferralNetwork as R; rn=R(); rn.add_referral('A','B'); rn.add_referral('B','C'); rn.add_referral('A','D'); print(rn.flow_centrality_scores())"
# Simulation & bonus search
python -c "from source.simulation import simulate, min_bonus_for_target; print(simulate(0.1,5)[:3]); print(min_bonus_for_target(5,5, lambda b: min(1.0,b/100)))"
```

## 11. Dependency Management
`requirements.txt` declares all needed Python dependencies (pytest + standard library usage). No hidden or transitive system requirements.
