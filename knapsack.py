"""
knapsack.py — 0/1 Knapsack DP for optimal question selection.

Given a pool of candidate questions (each with a mark value) and a
target total mark count, select the subset whose marks sum to
exactly (or as close as possible below) the target.

This is a 0/1 knapsack because each question can be included at most
once — you can't put the same past-paper question twice in a worksheet.
"""

from collections import defaultdict


def select_questions(candidates, target_marks):
    """
    Select an optimal subset of questions summing to `target_marks` (exact)
    or the largest achievable sum below target (closest match).

    Algorithm (bottom-up 1D DP):
      dp[m] holds either:
          - a list of question records whose marks sum to exactly m, or
          - None if m is not reachable with any subset of the seen questions.

      dp[0] = []              (the empty set sums to 0)

      For each question q with marks = m_q, iterate total from target
      DOWN TO m_q (this direction ensures 0/1 semantics — each question
      is considered at most once per DP pass). If dp[total - m_q] is
      reachable and dp[total] is not yet set, set:
          dp[total] = dp[total - m_q] + [q]

      After processing all questions, return dp[target] if non-None
      (exact match), otherwise return dp[t] for the largest t < target
      where dp[t] is non-None (closest under).

    Args:
        candidates:    list of question record dicts (each has a 'marks' key)
        target_marks:  int, desired total mark count

    Returns:
        (selected_questions, actual_total_marks)

    Complexity:
        Time:  O(n * W) where n = len(candidates), W = target_marks
        Space: O(W)
    """
    if not candidates or target_marks <= 0:
        return [], 0

    # Interleave candidates so the knapsack spreads across years
    # instead of clustering everything on one paper.
    ordered = _interleave_by_year(candidates)

    # dp[m] is either a list of question records or None
    dp = [None] * (target_marks + 1)
    dp[0] = []

    for q in ordered:
        m = q.get("marks", 0)
        if m <= 0 or m > target_marks:
            # Skip invalid (0-mark) questions and ones bigger than target.
            continue
        # Iterate from top down so each question enters the table at
        # most once per pass.
        for total in range(target_marks, m - 1, -1):
            if dp[total - m] is not None and dp[total] is None:
                dp[total] = dp[total - m] + [q]

    # Exact match — best case
    if dp[target_marks] is not None:
        return dp[target_marks], target_marks

    # Otherwise return the closest achievable sum below target
    for t in range(target_marks - 1, -1, -1):
        if dp[t] is not None:
            return dp[t], t

    return [], 0


def _interleave_by_year(candidates):
    """
    Round-robin through years so consecutive selections come from
    different papers. Keeps the resulting worksheet diverse.

    Algorithm:
      1. Group candidates by year.
      2. Repeatedly pop the front of each year's bucket in rotation,
         newest year first.

    Args:
        candidates: list of question record dicts

    Returns:
        list of the same records in interleaved order
    """
    groups = defaultdict(list)
    for q in candidates:
        groups[q.get("year", 0)].append(q)

    # Newest year first — small bias toward recent papers
    years = sorted(groups.keys(), reverse=True)

    result = []
    while any(groups[y] for y in years):
        for y in years:
            if groups[y]:
                result.append(groups[y].pop(0))
    return result
