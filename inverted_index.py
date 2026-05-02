"""
inverted_index.py — Custom Inverted Index data structure.

Maps composite keys (e.g. "9702_Kinematics_P2") to postings lists
of question records. Supports insert, query, union, intersection,
year filtering, and JSON persistence.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set


class InvertedIndex:
    """
    Inverted index mapping composite topic keys → postings lists.

    Key format: {SubjectCode}_{Topic}_{PaperType}
    Each posting is a question record dict with id, subject, topic,
    paper_type, year, marks, pdf, page, bbox fields.
    """

    def __init__(self) -> None:
        self.main_index: Dict[str, List[str]] = {}
        self.question_store: Dict[str, Dict[str, Any]] = {}
        with open("data/keywords/keyword_map.json") as file:
            self.keyword_map: Dict[str, Dict[str, Any]] = json.load(file)

    # ── Core Operations ──────────────────────────────────────────

    def insert(self, key: str, record: Dict[str, Any]) -> None:
        """
        Append a question record to the postings list for `key`.
        Creates the list if it doesn't exist yet.
        Skips duplicates (same question id already in that list).
        O(1) amortized.
        """
        question_id = record["id"]
        self.question_store[question_id] = record
        if key not in self.main_index:
            self.main_index[key] = []
        if question_id not in self.main_index[key]:
            self.main_index[key].append(question_id)

    def query(self, key: str) -> List[str]:
        """
        Return the list of Question IDs for a single composite key.
        Returns empty list if key not found.
        O(1) lookup.
        """
        return self.main_index.get(key, [])

    # ── Set Operations ───────────────────────────────────────────

    def union(self, keys: List[str]) -> List[str]:
        """
        Merge postings lists for multiple keys.
        Deduplicate by question id — each question appears once.
        Use case: "Give me all Kinematics OR Dynamics questions."
        O(k + n) where k = number of keys, n = total postings.
        """
        result_question_ids: Set[str] = set()
        for key in keys:
            if key in self.main_index:
                result_question_ids.update(self.main_index[key])
        return list(result_question_ids)

    def intersect(self, keys: List[str]) -> List[str]:
        """
        Return IDs present in ALL postings lists for given keys.
        Use case: "Give me questions tagged BOTH Kinematics AND Vectors."
        O(k × n) via set intersection on question ids.
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

    # ── Fetching & Filtering ─────────────────────────────────────

    def fetch_documents(
        self,
        question_ids: List[str],
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Takes a list of Question IDs, retrieves their full payload from the
        question_store, and optionally filters them by year.
        """
        results: List[Dict[str, Any]] = []
        for qid in question_ids:
            record = self.question_store.get(qid)
            if record:
                if year_from is not None and year_to is not None:
                    if year_from <= record["year"] <= year_to:
                        results.append(record)
                else:
                    results.append(record)
        return results

    def filter_by_year(
        self, results: List[Dict[str, Any]], year_from: int, year_to: int
    ) -> List[Dict[str, Any]]:
        """
        Legacy filter method. Consider using fetch_documents instead.
        """
        filtered_results: List[Dict[str, Any]] = []
        for record in results:
            if year_from <= record["year"] <= year_to:
                filtered_results.append(record)
        return filtered_results

    # ── Persistence ──────────────────────────────────────────────

    def remove_question(self, question_id):
        if question_id in self.question_store:
            del self.question_store[question_id]

        for key in self.main_index:
            cleaned_list = []
            for qid in self.main_index[key]:
                if qid != question_id:
                    cleaned_list.append(qid)
            self.main_index[key] = cleaned_list

    def save(self, path: str) -> None:
        data = {"main_index": self.main_index, "question_store": self.question_store}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as file:
            json.dump(data, file, indent=4)

    def load(self, path: str) -> None:
        """
        Deserialize the index from a JSON file at `path`.
        Replaces the current in-memory index with loaded data.
        """
        with open(path, "r") as file:
            data = json.load(file)

        self.main_index = data["main_index"]
        self.question_store = data["question_store"]

    #── Printing ──────────────────────────────────────────────
    def print_courses(self) -> list:
        for i, item in enumerate(self.keyword_map.keys()):
            print(i+1, "- ",item)
        
    def print_session(self, course_code: str) -> list:
        if(self.keyword_map[course_code].keys()) == ["ALL"]: 
            return "O3"
        else:
            for item in self.keyword_map[course_code].keys():
                print(item, " ")
                
    