"""referral_network.py

Implements:
- ReferralNetwork: directed acyclic graph of referrals with constraints:
    * No self-referrals
    * Unique referrer per candidate
    * Acyclic (reject operations that would create cycles)

- Influence metrics:
    * total_referral_count (BFS)
    * top_referrers_by_reach
    * unique_reach_greedy (select m influencers greedily by marginal coverage)
    * flow_centrality_scores (counts how many shortest paths each node lies on)
"""

from collections import deque, defaultdict
from typing import Dict, Set, List, Tuple

class ReferralNetwork:
    def __init__(self) -> None:
        # adjacency: referrer -> set of candidates
        self.adj: Dict[str, Set[str]] = defaultdict(set)
        # reverse map: candidate -> referrer (enforce unique referrer)
        self.rev: Dict[str, str] = {}
        # set of users (nodes)
        self.users: Set[str] = set()

    def add_user(self, user: str) -> None:
        self.users.add(user)
        # Ensure structures exist
        _ = self.adj[user]

    def _ensure_user(self, user: str) -> None:
        if user not in self.users:
            self.add_user(user)

    def _path_exists(self, src: str, target: str) -> bool:
        # BFS from src to see if target reachable
        if src == target:
            return True
        visited = set([src])
        q = deque([src])
        while q:
            u = q.popleft()
            for v in self.adj.get(u, ()):
                if v == target:
                    return True
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        return False

    def add_referral(self, referrer: str, candidate: str) -> None:
        """Add a directed referral edge referrer -> candidate.

        Raises ValueError on any constraint violation:
          - self-referral
          - candidate already has a referrer
          - adding edge would create a cycle
        """
        self._ensure_user(referrer)
        self._ensure_user(candidate)

        if referrer == candidate:
            raise ValueError("Self-referrals are not allowed.")

        # Enforce unique referrer per candidate
        if candidate in self.rev:
            raise ValueError(f"Candidate '{candidate}' already referred by '{self.rev[candidate]}'.")

        # Check acyclic: adding referrer->candidate would create a cycle if candidate can reach referrer
        if self._path_exists(candidate, referrer):
            raise ValueError("Adding this referral would create a cycle.")

        # Passed checks: add edge
        self.adj[referrer].add(candidate)
        self.rev[candidate] = referrer

    def get_direct_referrals(self, user: str) -> List[str]:
        """Return a list of immediate referrals made by user."""
        return list(self.adj.get(user, []))

    def reach_set(self, user: str) -> Set[str]:
        """Return the set of all nodes reachable from user (direct + indirect)."""
        visited = set()
        q = deque([user])
        while q:
            u = q.popleft()
            for v in self.adj.get(u, ()):
                if v not in visited:
                    visited.add(v)
                    q.append(v)
        # remove starting node if present
        visited.discard(user)
        return visited

    def total_referral_count(self, user: str) -> int:
        """Return the total number of referrals (unique) downstream of user."""
        return len(self.reach_set(user))

    def top_referrers_by_reach(self, k: int = 10) -> List[Tuple[str, int]]:
        """Return top-k users by total referral count (reach).

        Returns list of tuples: (user, reach_count), sorted descending by reach_count.
        """
        scores = []
        for u in sorted(self.users):
            scores.append((u, self.total_referral_count(u)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]

    def _all_reach_sets(self) -> Dict[str, Set[str]]:
        """Helper: compute reach set for every user and return dict user -> set."""
        reach = {}
        for u in self.users:
            reach[u] = self.reach_set(u)
        return reach

    def unique_reach_greedy(self, m: int) -> Tuple[List[str], Set[str]]:
        """Select m users greedily to maximize unique coverage (set cover heuristic).

        Returns a tuple (selected_list, covered_set)
        - selected_list: ordered list of selected users
        - covered_set: set of users covered by these selections
        """
        reach = self._all_reach_sets()
        selected = []
        covered = set()
        # Greedy selection by marginal gain
        for _ in range(m):
            best_user = None
            best_gain = -1
            for u, rset in reach.items():
                if u in selected:
                    continue
                gain = len(rset - covered)
                if gain > best_gain:
                    best_gain = gain
                    best_user = u
            if best_user is None or best_gain == 0:
                break
            selected.append(best_user)
            covered.update(reach[best_user])
        return selected, covered

    def _bfs_distances_from(self, src: str) -> Dict[str, int]:
        """Return dict node -> shortest distance (number of edges) from src using BFS."""
        dist = {}
        q = deque([src])
        dist[src] = 0
        while q:
            u = q.popleft()
            for v in self.adj.get(u, ()):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return dist

    def flow_centrality_scores(self) -> List[Tuple[str, int]]:
        """Compute a simple flow-centrality score: how many (s,t) shortest paths pass through v.

        Implementation (naive):
          - For every source s: run BFS to get dist_s
          - For every target t != s where dist_s[t] exists:
            - for every v not equal to s or t, if dist_s.get(v, inf) + dist_v.get(t, inf) == dist_s[t], increment score[v]

        Note: This counts ordered (s,t) pairs and does not normalize. It's clear and correct but not optimized.
        """
        nodes = sorted(self.users)
        # precompute distances from every node
        all_dist = {u: self._bfs_distances_from(u) for u in nodes}
        scores = {u: 0 for u in nodes}

        for s in nodes:
            dist_s = all_dist[s]
            for t in nodes:
                if t == s:
                    continue
                if t not in dist_s:
                    continue
                d_st = dist_s[t]
                for v in nodes:
                    if v == s or v == t:
                        continue
                    dist_sv = dist_s.get(v, None)
                    dist_vt = all_dist[v].get(t, None)
                    if dist_sv is None or dist_vt is None:
                        continue
                    if dist_sv + dist_vt == d_st:
                        scores[v] += 1
        # Return sorted list of (user, score) descending
        items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return items