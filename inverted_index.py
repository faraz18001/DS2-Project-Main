"""
inverted_index.py — Custom Inverted Index data structure.

Maps composite keys (e.g. "9702_Kinematics_P2") to postings lists
of question records. Supports insert, query, union, intersection,
year filtering, and JSON persistence.
"""

import json


class InvertedIndex:
    """
    Inverted index mapping composite topic keys → postings lists.

    Key format: {SubjectCode}_{Topic}_{PaperType}
    Each posting is a question record dict with id, subject, topic,
    paper_type, year, marks, pdf, page, bbox fields.
    """

    def __init__(self):
        # Internal dict: key (str) → list of question record dicts
        pass

    # ── Core Operations ──────────────────────────────────────────

    def insert(self, key, record):
        """
        Append a question record to the postings list for `key`.
        Creates the list if it doesn't exist yet.
        Skips duplicates (same question id already in that list).
        O(1) amortized.
        """
        pass

    def query(self, key):
        """
        Return the full postings list for a single composite key.
        Returns empty list if key not found.
        O(1) lookup.
        """
        pass

    # ── Set Operations ───────────────────────────────────────────

    def union(self, keys):
        """
        Merge postings lists for multiple keys.
        Deduplicate by question id — each question appears once.
        Use case: "Give me all Kinematics OR Dynamics questions."
        O(k + n) where k = number of keys, n = total postings.
        """
        pass

    def intersect(self, keys):
        """
        Return records present in ALL postings lists for given keys.
        Use case: "Give me questions tagged BOTH Kinematics AND Vectors."
        O(k × n) via set intersection on question ids.
        """
        pass

    # ── Filtering ────────────────────────────────────────────────

    def filter_by_year(self, results, year_from, year_to):
        """
        Filter a list of question records to only those within [year_from, year_to].
        Applied after query/union/intersect as a post-lookup step.
        O(n) linear scan.
        """
        pass

    # ── Persistence ──────────────────────────────────────────────

    def save(self, path):
        """
        Serialize the entire index to a JSON file at `path`.
        Allows reuse across runs without re-parsing PDFs.
        """
        pass

    def load(self, path):
        """
        Deserialize the index from a JSON file at `path`.
        Replaces the current in-memory index with loaded data.
        """
        pass

    # ── Utility ──────────────────────────────────────────────────

    def keys(self):
        """Return all composite keys currently in the index."""
        pass

    def __len__(self):
        """Return total number of keys in the index."""
        pass

    def __repr__(self):
        """Display summary: number of keys and total postings count."""
        pass
