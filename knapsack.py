"""
knapsack.py — 0/1 Knapsack DP for optimal question selection.

Given a pool of candidate questions (each with a mark value) and a
target total mark count, selects the subset whose marks sum to
exactly (or as close as possible to) the target.
"""

from typing import Any, Dict, List, Tuple


def select_questions(
    candidates: List[Dict[str, Any]], target_marks: int
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Select optimal subset of questions using bottom-up 0/1 Knapsack DP.

    Steps:
    1. Pre-sort candidates to interleave by year (ensures diversity).
    2. Build DP table: dp[m] = list of questions summing to exactly m marks.
    3. Iterate each question; for each, scan from target down to question's
       mark value, filling dp entries that become newly reachable.
    4. Return dp[target] if exact match exists, otherwise dp[t] for the
       largest t < target that has a valid combination.

    Args:
        candidates: list of question record dicts (each has 'marks' key).
        target_marks: int, the desired total mark count.

    Returns:
        list of question record dicts forming the optimal subset.
        int, the actual total marks achieved.

    Time: O(n × W) where n = len(candidates), W = target_marks.
    Space: O(W) for the DP table.
    """
    pass


def _interleave_by_year(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Re-order candidates so consecutive questions come from different years.
    Prevents the knapsack from clustering questions from a single paper.

    Approach: group by year, then round-robin pick from each group.

    Args:
        candidates: list of question record dicts.

    Returns:
        list of question record dicts in interleaved order.
    """
    pass
