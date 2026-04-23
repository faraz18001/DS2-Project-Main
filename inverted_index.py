"""
inverted_index.py — Custom Inverted Index data structure.

Maps composite keys (e.g. "9702_Kinematics_P2") to postings lists
of question records. Supports insert, delete, query (search), union,
intersection, year filtering, and JSON persistence.

DATA STRUCTURE OVERVIEW
-----------------------
An inverted index reverses the natural question->topics direction of storage.
Instead of:
    question1 -> [Kinematics, Dynamics]
    question2 -> [Kinematics]
    question3 -> [Energy]

we store:
    Kinematics -> [question1, question2]
    Dynamics   -> [question1]
    Energy     -> [question3]

Why: given a topic, retrieving all matching questions is now O(1) direct
lookup instead of an O(n) scan through every question.

We use two dicts:
    main_index     : key (str) -> list of question ids (list of str)
    question_store : question id -> full record (dict)

This separation prevents duplicating the full record across multiple keys
when a question is tagged with more than one topic — postings lists hold
compact ids, the store holds the heavyweight record once.
"""

import json


class InvertedIndex:

    def __init__(self):
        # Primary structure — maps composite key -> list of question ids
        self.main_index = {}
        # Secondary structure — maps question id -> full record
        self.question_store = {}

    # ────────────────────────────────────────────────────────────────────
    # Core Operations: INSERT, SEARCH (query), DELETE
    # ────────────────────────────────────────────────────────────────────

    def insert(self, key, record):
        """
        INSERT — append `record` to the postings list under `key`.

        Algorithm:
        1. Store the full record in question_store, keyed by its id.
        2. If `key` is new to main_index, create an empty postings list for it.
        3. Append the record's id to that list.

        Time: O(1) amortized (dict insert + list append).
        """
        question_id = record["id"]
        self.question_store[question_id] = record
        if key not in self.main_index:
            self.main_index[key] = []
        self.main_index[key].append(question_id)

    def query(self, key):
        """
        SEARCH — return the full postings list for a single composite key.

        Algorithm:
        1. Check if the key exists in main_index.
        2. If yes, walk the id list and resolve each id back to its record.
        3. If no, return an empty list.

        Time: O(k) where k = size of postings list (O(1) for the lookup itself).
        """
        full_posting_list = []
        if key in self.main_index:
            for question_id in self.main_index[key]:
                full_posting_list.append(self.question_store[question_id])
            return full_posting_list
        return []

    def delete(self, key, question_id=None):
        """
        DELETE — remove either the entire postings list for a key, or a
        specific question id from that list.

        If question_id is None: delete the key and its whole postings list.
        If question_id is given: delete just that one id from the list;
                                 if the list becomes empty, delete the key too.

        Also cleans up question_store when the id is no longer referenced
        by any other key.

        Time: O(n) worst-case to remove an id from the list.
        """
        if key not in self.main_index:
            return

        if question_id is None:
            ids_to_check = list(self.main_index[key])
            del self.main_index[key]
            # Remove orphan records from question_store
            for qid in ids_to_check:
                if not self._is_referenced(qid):
                    self.question_store.pop(qid, None)
            return

        # Remove a single id
        if question_id in self.main_index[key]:
            self.main_index[key].remove(question_id)
            if len(self.main_index[key]) == 0:
                del self.main_index[key]
            if not self._is_referenced(question_id):
                self.question_store.pop(question_id, None)

    def _is_referenced(self, question_id):
        """Check if a question id still appears in any postings list."""
        for ids in self.main_index.values():
            if question_id in ids:
                return True
        return False

    # ────────────────────────────────────────────────────────────────────
    # Set Operations: UNION, INTERSECT
    # ────────────────────────────────────────────────────────────────────

    def union(self, keys):
        """
        UNION — merge postings lists for multiple keys, deduplicated by id.

        Use case: "Give me all Kinematics OR Dynamics OR Energy questions."

        Algorithm:
        1. Collect all question ids from every key's postings list into a set
           (dedup is automatic).
        2. Resolve each id back to its full record.

        Time: O(k + n) where k = number of keys, n = total postings size.
        """
        result_ids = set()
        for key in keys:
            if key in self.main_index:
                result_ids.update(self.main_index[key])

        full_posting_list = []
        for qid in result_ids:
            full_posting_list.append(self.question_store[qid])
        return full_posting_list

    def intersect(self, keys):
        """
        INTERSECT — return records present in ALL postings lists for the given keys.

        Use case: "Questions tagged BOTH Kinematics AND Vectors."

        Algorithm:
        1. Start with the first key's id set.
        2. Intersect it with every subsequent key's id set.
        3. Resolve the remaining ids back to records.

        Time: O(k × n) where k = number of keys, n = smallest postings size.
        """
        if keys is None or len(keys) == 0:
            return []

        for key in keys:
            if key not in self.main_index:
                return []

        result_ids = set(self.main_index[keys[0]])
        for key in keys[1:]:
            result_ids.intersection_update(self.main_index[key])

        full_posting_list = []
        for qid in result_ids:
            full_posting_list.append(self.question_store[qid])
        return full_posting_list

    # ────────────────────────────────────────────────────────────────────
    # Post-lookup Filtering
    # ────────────────────────────────────────────────────────────────────

    def filter_by_year(self, results, year_from, year_to):
        """
        Filter a list of records to those with year in [year_from, year_to].
        Applied after query/union/intersect as a post-retrieval step.

        Time: O(n) linear scan.
        """
        filtered = []
        for record in results:
            if year_from <= record["year"] <= year_to:
                filtered.append(record)
        return filtered

    # ────────────────────────────────────────────────────────────────────
    # Persistence
    # ────────────────────────────────────────────────────────────────────

    def save(self, path):
        """Serialize the index to JSON so it survives across program runs."""
        data = {
            "main_index": self.main_index,
            "question_store": self.question_store,
        }
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False)

    def load(self, path):
        """Replace the in-memory index with data loaded from JSON."""
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.main_index = data["main_index"]
        self.question_store = data["question_store"]

    # ────────────────────────────────────────────────────────────────────
    # Diagnostics
    # ────────────────────────────────────────────────────────────────────

    def __len__(self):
        """Number of unique questions in the store."""
        return len(self.question_store)

    def key_count(self):
        """Number of composite keys in the index."""
        return len(self.main_index)
