"""
test_benchmark.py — Quantitative comparison: InvertedIndex vs naive scan.

Prints the speedup factor for the report.
"""
import random
import time
import unittest

from inverted_index import InvertedIndex


def _make_dataset(n=5000, topics=20, paper_types=4, subjects=3, years=10):
    topic_pool   = [f"Topic{i}" for i in range(topics)]
    paper_pool   = [f"P{i+1}"   for i in range(paper_types)]
    subject_pool = [f"S{i}"     for i in range(subjects)]
    out = []
    for i in range(n):
        out.append({
            "id":         f"q{i}",
            "subject":    random.choice(subject_pool),
            "topic":      random.choice(topic_pool),
            "paper_type": random.choice(paper_pool),
            "year":       2010 + random.randint(0, years - 1),
            "marks":      random.randint(1, 12),
        })
    return out


class TestBenchmark(unittest.TestCase):

    def setUp(self):
        random.seed(42)
        self.records = _make_dataset(n=5000)

        self.index = InvertedIndex()
        for r in self.records:
            key = f"{r['subject']}_{r['topic']}_{r['paper_type']}"
            self.index.insert(key, r)

        self.target_key = (
            f"{self.records[0]['subject']}_"
            f"{self.records[0]['topic']}_"
            f"{self.records[0]['paper_type']}"
        )

    def test_query_speedup(self):
        REPS = 2000

        t0 = time.perf_counter()
        for _ in range(REPS):
            _ = self.index.query(self.target_key)
        index_time = time.perf_counter() - t0

        ts, tt, tp = self.target_key.split("_", 2)
        t0 = time.perf_counter()
        for _ in range(REPS):
            hits = []
            for r in self.records:
                if r["subject"] == ts and r["topic"] == tt and r["paper_type"] == tp:
                    hits.append(r)
        naive_time = time.perf_counter() - t0

        speedup = naive_time / index_time if index_time > 0 else float("inf")
        print(f"\n--- {REPS} reps over {len(self.records)} records ---")
        print(f"  Inverted Index : {index_time*1000:8.2f} ms")
        print(f"  Linear Scan    : {naive_time*1000:8.2f} ms")
        print(f"  Speedup        : {speedup:8.1f}x")

        self.assertGreater(speedup, 10.0)


if __name__ == "__main__":
    unittest.main()
