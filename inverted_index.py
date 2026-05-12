"""
inverted_index.py — Custom Inverted Index data structure.

Maps composite keys (e.g. "9702_Kinematics_p21") to postings lists
of question IDs. Full question records live in a parallel store keyed
by id, so we never duplicate the heavy payload across multiple keys.

Public operations:
    Core
        insert(key, record)           — add a question id under a key
        query(key)                    — get list of ids under a key  (SEARCH)
        delete(key, qid=None)         — remove a single id, or a whole key
        remove_question(qid)          — purge an id from EVERY postings list

    Set ops
        union(keys)                   — ids appearing in ANY of the keys
        intersect(keys)               — ids appearing in ALL of the keys

    Hydration
        fetch_documents(ids, …)       — resolve ids to full records, optional year filter
        filter_by_year(records, …)    — legacy filter on already-resolved records

    Demo / Introspection (used by the terminal demo)
        list_subjects()               — distinct subject codes seen in the index
        list_topics(subject)          — distinct topics under a subject
        list_paper_types(subject)     — distinct paper variants (p11, p21, …) under a subject
        list_years(subject=None)      — sorted list of years present
        keys_for(subject, topics, ptype) — composite keys built from filters
        sample_postings(key, n)       — first N records under a key (preview)
        stats()                       — quick summary numbers

    Persistence
        save(path) / load(path)       — JSON round-trip

KEY FORMAT
----------
"{subject_code}_{topic}_{paper_type}"

    "9702_Kinematics_p21"   →  A-Level Physics, Kinematics, AS-tier paper variant 21
    "5054_Forces_p11"       →  O-Level Physics, Forces, paper variant 11

Year is NOT in the key (it is a range, not a point) — applied as a
post-lookup filter via fetch_documents().
"""

import json
import os
from typing import Any, Dict, List, Optional, Set


class InvertedIndex:
    """Inverted index: composite key → list of question ids."""

    def __init__(self, keyword_map_path: Optional[str] = None) -> None:
        self.main_index: Dict[str, List[str]] = {}
        self.question_store: Dict[str, Dict[str, Any]] = {}

        # # Optional keyword map — used by the terminal demo to enumerate
        # # the topics it should offer the user when they pick a subject.
        # self.keyword_map: Dict[str, Any] = {}
        # if keyword_map_path and os.path.isfile(keyword_map_path):
        #     with open(keyword_map_path, "r", encoding="utf-8") as f:
        #         self.keyword_map = json.load(f)

    # ────────────────────────────────────────────────────────────────────
    # CORE OPERATIONS — Insert, Search (Query), Delete
    # ────────────────────────────────────────────────────────────────────

    def insert(self, key: str, record: Dict[str, Any]) -> None:
        """
        INSERT — add a question record under `key`.

        Algorithm:
          1. Store the full record once in question_store, keyed by its id.
          2. Create an empty postings list for this key if not seen before.
          3. Append the record's id to that list (skip if already present).

        Time: O(1) amortised.
        """
        question_id = record["id"]
        self.question_store[question_id] = record
        if key not in self.main_index:
            self.main_index[key] = []
        if question_id not in self.main_index[key]:
            self.main_index[key].append(question_id)

    def query(self, key: str) -> List[str]:
        """
        SEARCH — return the list of question ids under `key`.
        Returns [] if key is unknown.
        Time: O(1) (single dict lookup).
        """
        return self.main_index.get(key, [])

    def delete(self, key: str, question_id: Optional[str] = None) -> None:
        """
        DELETE.

        Two modes:
          - delete(key)               → remove the whole key + its postings list
          - delete(key, question_id)  → remove just that one id from the list

        Time: O(1) for whole-key delete; O(n) over the postings list for
        single-id delete.
        """
        if key not in self.main_index:
            return

        if question_id is None:
            ids_to_check = list(self.main_index[key])
            del self.main_index[key]
            for qid in ids_to_check:
                if not self._is_referenced(qid):
                    self.question_store.pop(qid, None)
            return

        if question_id in self.main_index[key]:
            self.main_index[key].remove(question_id)
            if not self.main_index[key]:
                del self.main_index[key]
            if not self._is_referenced(question_id):
                self.question_store.pop(question_id, None)

    def remove_question(self, question_id: str) -> None:
        """
        Purge a question id from EVERY postings list and drop it from
        the store. Useful when you want to mass-remove a question
        without knowing which keys reference it.
        """
        self.question_store.pop(question_id, None)
        empty_keys: List[str] = []
        for key, ids in self.main_index.items():
            if question_id in ids:
                self.main_index[key] = [q for q in ids if q != question_id]
                if not self.main_index[key]:
                    empty_keys.append(key)
        for k in empty_keys:
            del self.main_index[k]

    def _is_referenced(self, question_id: str) -> bool:
        """True if `question_id` still appears in any postings list."""
        for ids in self.main_index.values():
            if question_id in ids:
                return True
        return False

    # ────────────────────────────────────────────────────────────────────
    # SET OPERATIONS — Union, Intersect
    # ────────────────────────────────────────────────────────────────────

    def union(self, keys: List[str]) -> List[str]:
        """
        UNION — ids that appear in ANY of the listed keys (deduplicated).

        Use case: "Kinematics OR Dynamics OR Energy".
        Time: O(k + total postings).
        """
        result_ids: Set[str] = set()
        for key in keys:
            if key in self.main_index:
                result_ids.update(self.main_index[key])
        return list(result_ids)

    def intersect(self, keys: List[str]) -> List[str]:
        """
        INTERSECT — ids that appear in ALL of the listed keys.

        Use case: "Kinematics AND Vectors" (cross-topic questions).
        Time: O(k × smallest postings list).
        """
        if not keys:
            return []
        for key in keys:
            if key not in self.main_index:
                return []

        result_ids = set(self.main_index[keys[0]])
        for key in keys[1:]:
            result_ids.intersection_update(self.main_index[key])
        return list(result_ids)

    # ────────────────────────────────────────────────────────────────────
    # HYDRATION — id → full record
    # ────────────────────────────────────────────────────────────────────

    def fetch_documents(
        self,
        question_ids: List[str],
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Resolve a list of question ids back to their full records,
        optionally filtering by year range (inclusive).
        """
        results: List[Dict[str, Any]] = []
        for qid in question_ids:
            record = self.question_store.get(qid)
            if record is None:
                continue
            if year_from is not None and year_to is not None:
                if not (year_from <= record["year"] <= year_to):
                    continue
            results.append(record)
        return results

    def filter_by_year(
        self,
        results: List[Dict[str, Any]],
        year_from: int,
        year_to: int,
    ) -> List[Dict[str, Any]]:
        """Filter already-resolved records by inclusive year range."""
        return [r for r in results if year_from <= r["year"] <= year_to]


    # ────────────────────────────────────────────────────────────────────
    # View Operation:
    # ────────────────────────────────────────────────────────────────────
    
    def view_tree(self, max_keys: int = 10) -> None:
        """
        Print the main_index as a tree structure.
        Shows composite keys with their postings lists beneath them.
        """
        if not self.main_index:
            print("  (index is empty)")
            return

        all_keys = list(self.main_index.keys())
        # Manual bubble sort
        for i in range(len(all_keys)):
            for j in range(i + 1, len(all_keys)):
                if all_keys[i] > all_keys[j]:
                    all_keys[i], all_keys[j] = all_keys[j], all_keys[i]

        for key in all_keys[:max_keys]:
            print(f"  {key}")
            question_ids = self.main_index[key]
            for i, qid in enumerate(question_ids):
                connector = "└── " if i == len(question_ids) - 1 else "├── "
                print(f"  {connector}{qid}")

        if len(all_keys) > max_keys:
            print(f"  ... and {len(all_keys) - max_keys} more keys")
    
    

    # ────────────────────────────────────────────────────────────────────
    # DEMO / INTROSPECTION
    # Used by demo_runner.py to walk the user through what's in the index.
    # ────────────────────────────────────────────────────────────────────

    def list_subjects(self) -> List[str]:
        """
        Distinct subject codes that appear in any indexed key.
        Returned sorted ascending.

        How: every composite key starts with "{subject}_…", so we just
        peel the first underscore-segment off every key.
        """
        subjects: Set[str] = set()
        for key in self.main_index:
            subjects.add(key.split("_", 1)[0])
        return sorted(subjects)

    def list_topics(self, subject: str) -> List[str]:
        """
        Distinct topics for `subject`, derived from existing index keys.

        Key form is "{subject}_{topic}_{paper_type}", and topics may
        themselves contain spaces or hyphens but Cambridge subject codes
        are always pure digits — so splitting "from the right once" lets
        us peel paper_type off, and "from the left once" peels subject
        off, leaving the topic in the middle untouched.
        """
        topics: Set[str] = set()
        prefix = subject + "_"
        for key in self.main_index:
            if not key.startswith(prefix):
                continue
            no_subject = key[len(prefix):]              # "Kinematics_p21"
            if "_" in no_subject:
                topic = no_subject.rsplit("_", 1)[0]    # "Kinematics"
                topics.add(topic)
        return sorted(topics)

    def list_paper_types(self, subject: str) -> List[str]:
        """Distinct paper variants under a subject (e.g. ['p11','p21','p41'])."""
        ptypes: Set[str] = set()
        prefix = subject + "_"
        for key in self.main_index:
            if not key.startswith(prefix):
                continue
            ptypes.add(key.rsplit("_", 1)[1])
        return sorted(ptypes)

    def list_years(self, subject: Optional[str] = None) -> List[int]:
        """
        Distinct years present in the question_store.
        If `subject` is given, restrict to records of that subject.
        """
        years: Set[int] = set()
        for record in self.question_store.values():
            if subject and record.get("subject") != subject:
                continue
            y = record.get("year")
            if isinstance(y, int):
                years.add(y)
        return sorted(years)

    def keys_for(
        self,
        subject: str,
        topics: List[str],
        paper_types: List[str],
    ) -> List[str]:
        """
        Build the composite keys you'd pass to union()/intersect() for
        a (subject, topics, paper_types) selection. Convenience helper
        for the terminal demo so it can show the user exactly which
        keys are about to be queried.

        Cartesian product over topics × paper_types.
        """
        out: List[str] = []
        for t in topics:
            for p in paper_types:
                out.append(f"{subject}_{t}_{p}")
        return out

    def sample_postings(self, key: str, n: int = 3) -> List[Dict[str, Any]]:
        """First `n` resolved records for a key — used as a preview."""
        ids = self.query(key)[:n]
        return self.fetch_documents(ids)

    def stats(self) -> Dict[str, Any]:
        """Quick summary of what's in the index."""
        return {
            "n_keys":       len(self.main_index),
            "n_questions":  len(self.question_store),
            "n_subjects":   len(self.list_subjects()),
            "avg_postings": round(
                sum(len(v) for v in self.main_index.values())
                / max(1, len(self.main_index)), 2,
            ),
        }

    def __len__(self) -> int:
        return len(self.question_store)

    def __contains__(self, key: str) -> bool:
        return key in self.main_index


    # ────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ────────────────────────────────────────────────────────────────────

    def save(self, path: str) -> None:
        data = {
            "main_index":     self.main_index,
            "question_store": self.question_store,
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.main_index     = data["main_index"]
        self.question_store = data["question_store"]
