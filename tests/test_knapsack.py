"""
test_knapsack.py — Unit tests for the 0/1 Knapsack selection logic.
"""
import unittest

from knapsack import select_questions, _interleave_by_year


def _q(qid, marks, year=2020):
    return {"id": qid, "marks": marks, "year": year}


class TestKnapsack(unittest.TestCase):

    def test_exact_match_exists(self):
        """If some subset hits the target exactly, knapsack returns it."""
        pool = [_q("a", 3), _q("b", 5), _q("c", 7), _q("d", 10)]
        sel, total = select_questions(pool, 10)
        self.assertEqual(total, 10)
        self.assertEqual(sum(q["marks"] for q in sel), 10)

    def test_returns_closest_below_when_no_exact(self):
        """With pool={4,6,9} target=20 — reach 19 (=4+6+9), not 20."""
        pool = [_q("a", 4), _q("b", 6), _q("c", 9)]
        sel, total = select_questions(pool, 20)
        self.assertEqual(total, 19)
        self.assertEqual(sum(q["marks"] for q in sel), 19)

    def test_empty_pool(self):
        """Empty candidate pool returns empty selection."""
        sel, total = select_questions([], 10)
        self.assertEqual(sel, [])
        self.assertEqual(total, 0)

    def test_zero_target(self):
        """target=0 is a valid edge case; nothing selected."""
        pool = [_q("a", 5)]
        sel, total = select_questions(pool, 0)
        self.assertEqual(total, 0)

    def test_no_question_reused(self):
        """0/1 knapsack: the same question can't be picked twice."""
        pool = [_q("a", 5)]
        sel, total = select_questions(pool, 10)
        self.assertEqual(total, 5)
        self.assertEqual(len(sel), 1)

    def test_interleave_spreads_years(self):
        """The interleaver should fan questions out across years."""
        pool = [
            _q("a", 1, year=2020), _q("b", 1, year=2020),
            _q("c", 1, year=2021), _q("d", 1, year=2021),
            _q("e", 1, year=2022),
        ]
        ordered = _interleave_by_year(pool)
        first_three_years = {q["year"] for q in ordered[:3]}
        self.assertEqual(len(first_three_years), 3)


if __name__ == "__main__":
    unittest.main()
