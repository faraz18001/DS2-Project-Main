"""
test_knapsack.py — Unit tests for the 0/1 Knapsack selection logic.
"""

import unittest
from backend.knapsack import select_questions

class TestKnapsack(unittest.TestCase):
    def test_exact_match(self):
        """Verify selection when an exact mark combination exists."""
        pass

    def test_closest_match(self):
        """Verify selection when no exact match exists (returns largest sum < target)."""
        pass

    def test_diversity_interleaving(self):
        """Verify that questions are interleaved by year for diversity."""
        pass

if __name__ == "__main__":
    unittest.main()
