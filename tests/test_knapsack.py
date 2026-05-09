"""
test_knapsack.py — Unit tests for 0/1 Knapsack question selection.
"""
import unittest

from knapsack import select_questions, _interleave_by_year


def _q(qid, marks, year=2024):
    return {"id": qid, "marks": marks, "year": year}


class TestKnapsack(unittest.TestCase):

    def test_exact_match(self):
        pool = [_q("a", 3), _q("b", 5), _q("c", 7), _q("d", 10)]
        sel, total = select_questions(pool, 10)
        self.assertEqual(total, 10)
        self.assertEqual(sum(q["marks"] for q in sel), 10)

    def test_closest_below_when_no_exact(self):
        pool = [_q("a", 4), _q("b", 6), _q("c", 9)]
        sel, total = select_questions(pool, 20)
        self.assertEqual(total, 19)             # 4 + 6 + 9
        self.assertEqual(sum(q["marks"] for q in sel), 19)

    def test_empty_pool(self):
        self.assertEqual(select_questions([], 10), ([], 0))

    def test_zero_target(self):
        sel, total = select_questions([_q("a", 5)], 0)
        self.assertEqual(total, 0)
        self.assertEqual(sel, [])

    def test_no_question_used_twice(self):
        """0/1 knapsack — single 5-mark Q can't fill a target of 10."""
        sel, total = select_questions([_q("a", 5)], 10)
        self.assertEqual(total, 5)
        self.assertEqual(len(sel), 1)

    def test_skip_question_bigger_than_target(self):
        sel, total = select_questions([_q("a", 50), _q("b", 3)], 10)
        self.assertEqual(total, 3)
        self.assertEqual(sel[0]["id"], "b")

    def test_interleave_spreads_years(self):
        pool = [
            _q("a", 1, year=2020), _q("b", 1, year=2020),
            _q("c", 1, year=2021), _q("d", 1, year=2021),
            _q("e", 1, year=2022),
        ]
        ordered = _interleave_by_year(pool)
        self.assertEqual(len({q["year"] for q in ordered[:3]}), 3)


if __name__ == "__main__":
    unittest.main()
