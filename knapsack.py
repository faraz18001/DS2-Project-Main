"""
knapsack.py — 0/1 Knapsack DP for optimal question selection.

Given a candidate pool of questions (each with a `marks` value) and a
target total mark count, pick the subset whose marks sum to exactly
target, or — if that's not reachable — to the largest sum below target.

This is 0/1 knapsack (not unbounded) because each past-paper question
can appear in the worksheet at most once.
"""

from collections import defaultdict
from typing import Any, Dict, List, Tuple


def select_questions(
    candidates: List[Dict[str, Any]],
    target_marks: int,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Choose an optimal subset of `candidates` whose marks sum to
    `target_marks` (exact) or as close as possible below it.

    DP RECURRENCE
    -------------
    dp[m] is either:
        - a list of question records summing to exactly m, or
        - None if m is unreachable.

    Base:
        dp[0] = []   (the empty set sums to 0)

    Transition (for each question q with marks m_q, iterating total
    DOWNWARD from target to m_q so each question enters at most once):

        if dp[total - m_q] is not None and dp[total] is None:
            dp[total] = dp[total - m_q] + [q]

    Result:
        return dp[target] if exact;
        else dp[t] for the largest t < target that's reachable.

    Args:
        candidates    : list of question record dicts (each has 'marks')
        target_marks  : int, desired total

    Returns:
        (selected_subset, actual_total_marks)

    Complexity:
        Time  : O(n × W) where n = len(candidates), W = target_marks
        Space : O(W)
    """
    if not candidates or target_marks <= 0:
        return [], 0

    # Spread questions across years so the chosen subset doesn't all come
    # from one paper. The DP picks greedily in source-order from `dp[0]`,
    # so feeding interleaved input changes the *composition* of the result
    # (still optimal in marks-sum, more diverse in year coverage).
    ordered = _interleave_by_year(candidates)

    dp: List[Any] = [None] * (target_marks + 1)
    dp[0] = []

    for q in ordered:
        m = q.get("marks", 0)
        if m <= 0 or m > target_marks:
            continue
        # Top-down iteration enforces 0/1 semantics
        for total in range(target_marks, m - 1, -1):
            if dp[total - m] is not None and dp[total] is None:
                dp[total] = dp[total - m] + [q]

    if dp[target_marks] is not None:
        return dp[target_marks], target_marks

    for t in range(target_marks - 1, -1, -1):
        if dp[t] is not None:
            return dp[t], t

    return [], 0


def _interleave_by_year(
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Round-robin through years (newest first) so consecutive candidates
    come from different papers.
    """
    groups: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for q in candidates:
        groups[q.get("year", 0)].append(q)

    years = sorted(groups.keys(), reverse=True)

    result: List[Dict[str, Any]] = []
    while any(groups[y] for y in years):
        for y in years:
            if groups[y]:
                result.append(groups[y].pop(0))
    return result
