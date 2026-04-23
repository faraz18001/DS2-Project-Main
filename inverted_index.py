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
        self.main_index = {}
        self.question_store = {}

    # ── Core Operations ──────────────────────────────────────────

    def insert(self, key, record):
        """
        Append a question record to the postings list for `key`.
        Creates the list if it doesn't exist yet.
        Skips duplicates (same question id already in that list).
        O(1) amortized.
        """
        question_id = record["id"]
        self.question_store[question_id] = record
        if key not in self.main_index: #agar main_ index mai topic ni hai to daldo
            self.main_index[key] = []
        if question_id not in self.main_index[key]: #agar topic k question pool mai question exist ni krta to daldo
            self.main_index[key].append(question_id)

    def query(self, key): #issue here, this should return the question ids, not the pdf parsing data
        """
        Return the full postings for a single composite key.
        Returns empty list if key not found.
        O(1) lookup.
        """
        full_posting_list = []
        if key in self.main_index:
            for question_id in self.main_index[key]:
                full_posting_list.append(self.question_store[question_id])
            return full_posting_list

        else:
            return []

    # ── Set Operations ───────────────────────────────────────────

    def union(self, keys): #issue here, this should return the question ids, not the pdf parsing data
        """
        Merge postings lists for multiple keys.
        Deduplicate by question id — each question appears once.
        Use case: "Give me all Kinematics OR Dynamics questions."
        O(k + n) where k = number of keys, n = total postings.
        """
        result_question_id = set()
        for key in keys:
            if key in self.main_index:
                result_question_id.update(self.main_index[key]) #this add the question ids in the set removing duplicates retaining set properties

        #remove this and return the resultant question ids as well
        full_posting_list = []
        for question_id in result_question_id:
            full_posting_list.append(self.question_store[question_id])
        return full_posting_list

    def intersect(self, keys):
        """
        Return records present in ALL postings lists for given keys.
        Use case: "Give me questions tagged BOTH Kinematics AND Vectors."
        O(k × n) via set intersection on question ids.
        """
        if keys is None or len(keys) == 0:
            return []

        for key in keys:
            if key not in self.main_index:
                return []

        result_ids = set(self.main_index[keys[0]])
        for key in keys[1:]:
            result_ids.intersection_update(self.main_index[key])

        #remove karna hai yeh, cuz this violates the DS thing
        full_posting_list = []
        for question_id in result_ids:
            full_posting_list.append(self.question_store[question_id])
        return full_posting_list

    # ── Filtering ────────────────────────────────────────────────

    def filter_by_year(self, results, year_from, year_to):
        """
        Filter a list of question records to only those within [year_from, year_to].
        Applied after query/union/intersect as a post-lookup step.
        O(n) linear scan.
        """
        filtered_results = []
        for record in results:
            if record["year"] >= year_from and record["year"] <= year_to:
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

    def save(self, path):
        data = {}
        data["main_index"] = self.main_index
        data["question_store"] = self.question_store

        with open(path, "w") as file:
            json.dump(data, file, indent=4)

    def load(self, path):
        """
        Deserialize the index from a JSON file at `path`.
        Replaces the current in-memory index with loaded data.
        """
        with open(path, "r") as file:
            data = json.load(file)

        self.main_index = data["main_index"]
        self.question_store = data["question_store"]
