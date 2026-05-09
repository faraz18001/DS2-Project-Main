"""
test_inverted_index.py — Unit tests for the InvertedIndex class.
"""
import os
import tempfile
import unittest

from inverted_index import InvertedIndex


def _q(qid, subject="5054", topic="Kinematics",
       paper_type="p11", year=2024, marks=5):
    return {
        "id": qid, "subject": subject, "topic": topic,
        "paper_type": paper_type, "year": year, "marks": marks,
    }


class TestInvertedIndex(unittest.TestCase):

    def setUp(self):
        self.index = InvertedIndex()

    # ── core ────────────────────────────────────────────────────────
    def test_insert_and_query(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        ids = self.index.query("5054_Kinematics_p11")
        self.assertEqual(ids, ["q1"])

    def test_insert_dedup_within_key(self):
        """Inserting the same record twice under one key is a no-op."""
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.assertEqual(self.index.query("5054_Kinematics_p11"), ["q1"])

    def test_query_missing_key(self):
        self.assertEqual(self.index.query("nope"), [])

    # ── set ops ─────────────────────────────────────────────────────
    def test_union_dedup_across_keys(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Kinematics_p11", _q("q2"))
        self.index.insert("5054_Forces_p11",     _q("q3", topic="Forces"))
        self.index.insert("5054_Forces_p11",     _q("q1"))   # cross-tagged
        u = sorted(self.index.union(["5054_Kinematics_p11", "5054_Forces_p11"]))
        self.assertEqual(u, ["q1", "q2", "q3"])

    def test_intersect_returns_common(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Forces_p11",     _q("q1"))
        self.index.insert("5054_Forces_p11",     _q("q3", topic="Forces"))
        self.assertEqual(
            self.index.intersect(["5054_Kinematics_p11", "5054_Forces_p11"]),
            ["q1"],
        )

    def test_intersect_with_unknown_key(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.assertEqual(
            self.index.intersect(["5054_Kinematics_p11", "ghost"]),
            [],
        )

    # ── delete / hydration / year ───────────────────────────────────
    def test_delete_whole_key(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Kinematics_p11", _q("q2"))
        self.index.delete("5054_Kinematics_p11")
        self.assertEqual(self.index.query("5054_Kinematics_p11"), [])

    def test_delete_single_id(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Kinematics_p11", _q("q2"))
        self.index.delete("5054_Kinematics_p11", "q1")
        self.assertEqual(self.index.query("5054_Kinematics_p11"), ["q2"])

    def test_remove_question_purges_everywhere(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Forces_p11",     _q("q1"))
        self.index.remove_question("q1")
        self.assertEqual(self.index.query("5054_Kinematics_p11"), [])
        self.assertEqual(self.index.query("5054_Forces_p11"), [])
        self.assertNotIn("q1", self.index.question_store)

    def test_fetch_documents_with_year_filter(self):
        self.index.insert("5054_Kinematics_p11", _q("q1", year=2019))
        self.index.insert("5054_Kinematics_p11", _q("q2", year=2024))
        ids = self.index.query("5054_Kinematics_p11")
        full = self.index.fetch_documents(ids, 2020, 2025)
        self.assertEqual([r["id"] for r in full], ["q2"])

    # ── demo introspection ─────────────────────────────────────────
    def test_list_subjects_topics_paper_types_years(self):
        self.index.insert("5054_Kinematics_p11", _q("q1", year=2023))
        self.index.insert("5054_Forces_p21",     _q("q2", topic="Forces",
                                                   paper_type="p21", year=2024))
        self.index.insert("9702_Dynamics_p41",   _q("q3", subject="9702",
                                                   topic="Dynamics",
                                                   paper_type="p41", year=2025))
        self.assertEqual(self.index.list_subjects(), ["5054", "9702"])
        self.assertEqual(self.index.list_topics("5054"), ["Forces", "Kinematics"])
        self.assertEqual(self.index.list_paper_types("5054"), ["p11", "p21"])
        self.assertEqual(self.index.list_years("5054"), [2023, 2024])
        self.assertEqual(self.index.list_years(), [2023, 2024, 2025])

    def test_keys_for_cross_product(self):
        keys = self.index.keys_for("5054", ["Forces", "Energy"], ["p11", "p21"])
        self.assertEqual(set(keys), {
            "5054_Forces_p11", "5054_Forces_p21",
            "5054_Energy_p11", "5054_Energy_p21",
        })

    def test_stats(self):
        self.index.insert("5054_Forces_p11", _q("q1"))
        self.index.insert("5054_Forces_p11", _q("q2"))
        self.index.insert("9702_Kinematics_p21", _q("q3", subject="9702",
                                                    paper_type="p21"))
        s = self.index.stats()
        self.assertEqual(s["n_keys"], 2)
        self.assertEqual(s["n_questions"], 3)
        self.assertEqual(s["n_subjects"], 2)

    # ── persistence ────────────────────────────────────────────────
    def test_save_and_load_round_trip(self):
        self.index.insert("5054_Kinematics_p11", _q("q1"))
        self.index.insert("5054_Forces_p21", _q("q3", topic="Forces",
                                                 paper_type="p21"))
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        tmp.close()
        try:
            self.index.save(tmp.name)
            other = InvertedIndex()
            other.load(tmp.name)
            self.assertEqual(other.query("5054_Kinematics_p11"), ["q1"])
            self.assertEqual(other.query("5054_Forces_p21"),     ["q3"])
            self.assertEqual(other.list_subjects(), ["5054"])
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
