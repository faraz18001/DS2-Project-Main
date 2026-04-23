"""
test_inverted_index.py — Unit tests for the InvertedIndex class.
"""
import os
import tempfile
import unittest

from inverted_index import InvertedIndex


def _q(qid, subject="5054", topic="Kinematics",
       paper_type="P1", year=2020, marks=5):
    """Build a minimal question record dict for test fixtures."""
    return {
        "id": qid, "subject": subject, "topic": topic,
        "paper_type": paper_type, "year": year, "marks": marks,
    }


class TestInvertedIndex(unittest.TestCase):

    def setUp(self):
        self.index = InvertedIndex()

    def test_insert_and_query(self):
        """A single insert is retrievable by the same key."""
        self.index.insert("5054_Kinematics_P1", _q("q1"))
        result = self.index.query("5054_Kinematics_P1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "q1")

    def test_query_missing_key_returns_empty(self):
        """Querying an unknown key returns [] (not None, not error)."""
        self.assertEqual(self.index.query("not_a_real_key"), [])

    def test_union_deduplicates(self):
        """Union of two keys that share a question must not duplicate it."""
        q1 = _q("q1")
        q2 = _q("q2")
        q3 = _q("q3", topic="Forces")
        self.index.insert("5054_Kinematics_P1", q1)
        self.index.insert("5054_Kinematics_P1", q2)
        self.index.insert("5054_Forces_P1", q3)
        self.index.insert("5054_Forces_P1", q1)  # q1 indexed under both keys

        merged = self.index.union(["5054_Kinematics_P1", "5054_Forces_P1"])
        ids = sorted(q["id"] for q in merged)
        self.assertEqual(ids, ["q1", "q2", "q3"])

    def test_intersect_returns_common(self):
        """Intersect returns only the ids in all listed keys."""
        q1 = _q("q1")
        q3 = _q("q3", topic="Forces")
        self.index.insert("5054_Kinematics_P1", q1)
        self.index.insert("5054_Forces_P1", q1)
        self.index.insert("5054_Forces_P1", q3)

        common = self.index.intersect(["5054_Kinematics_P1", "5054_Forces_P1"])
        ids = [q["id"] for q in common]
        self.assertEqual(ids, ["q1"])

    def test_intersect_missing_key_returns_empty(self):
        """If any key is missing, intersect returns []."""
        self.index.insert("5054_Kinematics_P1", _q("q1"))
        self.assertEqual(
            self.index.intersect(["5054_Kinematics_P1", "nope"]),
            [],
        )

    def test_filter_by_year(self):
        """Year filter subsets to [from, to] inclusive."""
        recs = [_q("q1", year=2019), _q("q2", year=2021),
                _q("q3", year=2023), _q("q4", year=2025)]
        filtered = self.index.filter_by_year(recs, 2020, 2023)
        ids = sorted(q["id"] for q in filtered)
        self.assertEqual(ids, ["q2", "q3"])

    def test_delete_whole_key(self):
        """Delete without a question_id removes the whole postings list."""
        self.index.insert("5054_Kinematics_P1", _q("q1"))
        self.index.insert("5054_Kinematics_P1", _q("q2"))
        self.index.delete("5054_Kinematics_P1")
        self.assertEqual(self.index.query("5054_Kinematics_P1"), [])

    def test_delete_single_id(self):
        """Delete with a question_id removes just that id from the list."""
        self.index.insert("5054_Kinematics_P1", _q("q1"))
        self.index.insert("5054_Kinematics_P1", _q("q2"))
        self.index.delete("5054_Kinematics_P1", "q1")
        remaining = self.index.query("5054_Kinematics_P1")
        self.assertEqual([q["id"] for q in remaining], ["q2"])

    def test_save_and_load_round_trip(self):
        """After save → load, the index returns identical results."""
        self.index.insert("5054_Kinematics_P1", _q("q1"))
        self.index.insert("5054_Forces_P1", _q("q3", topic="Forces"))

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        tmp.close()
        try:
            self.index.save(tmp.name)
            restored = InvertedIndex()
            restored.load(tmp.name)
            self.assertEqual(restored.query("5054_Kinematics_P1")[0]["id"], "q1")
            self.assertEqual(restored.query("5054_Forces_P1")[0]["id"], "q3")
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
