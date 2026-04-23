"""
demo_runner.py — Terminal app to manage the question bank.
"""

import os
import time
from typing import Any, Dict, List

from build_index import build_master_index
from inverted_index import InvertedIndex
from pdf_parser import parse_paper
from topic_mapper import build_composite_keys, load_keyword_map, tag_question


def show_menu() -> None:
    print("\n" + "=" * 40)
    print(" QUESTION BANK MANAGER ")
    print("=" * 40)
    print("[1] View the Tree Structure")
    print("[2] Search by Topic")
    print("[3] Add a New Paper (PDF)")
    print("[4] Delete a Question")
    print("[5] Performance Benchmark")
    print("[0] Exit and Save")
    print("=" * 40)


def view_tree(index: InvertedIndex) -> None:
    print("\n--- INVERTED INDEX TREE ---")
    if not index.main_index:
        print("The tree is currently empty.")
        return

    # Sort keys so it looks organized
    all_keys: List[str] = sorted(list(index.main_index.keys()))

    for key in all_keys:
        print("\n" + key)
        question_ids: List[str] = index.main_index[key]
        for i in range(len(question_ids)):
            qid = question_ids[i]
            # Use connector to look like a tree
            connector = "├── "
            if i == len(question_ids) - 1:
                connector = "└── "
            print(connector + qid)


def search_topic(index: InvertedIndex) -> None:
    # Updated to show the new key format
    print("\nEnter topic/key to search (e.g., 9702_Kinematics_p13):")
    search_key: str = input(">> ")

    # SRP Fix: query() now only returns IDs
    result_ids: List[str] = index.query(search_key)

    if len(result_ids) == 0:
        print("No questions found for that key.")
    else:
        print("\nFound " + str(len(result_ids)) + " questions:")
        for qid in result_ids:
            # Look up the actual data in the store
            r = index.question_store[qid]
            print("-" * 20)
            print("ID: " + r["id"])
            print("Marks: " + str(r["marks"]))
            # Show just a little bit of text
            snippet = r["text"][:100].replace("\n", " ")
            print("Text: " + snippet + "...")


def add_paper(
    index: InvertedIndex, keyword_map: Dict[str, Dict[str, List[str]]]
) -> None:
    print("\nEnter path to PDF file (e.g., data/papers/9702_w25_qp_13.pdf):")
    pdf_path: str = input(">> ")
    if not os.path.exists(pdf_path):
        print("Error: File not found.")
        return

    # Auto-Ingestion Fix: The parser figures everything out from the filename now!
    print("Processing paper (auto-extracting metadata from filename)...")
    new_questions: List[Dict[str, Any]] = parse_paper(pdf_path)

    if not new_questions:
        print("Error: Could not parse paper. Check filename format.")
        return

    for q in new_questions:
        # Get topics using the text we extracted
        topics: List[str] = tag_question(q["text"], q["subject"], keyword_map)
        # Create keys
        keys: List[str] = build_composite_keys(q["subject"], topics, q["paper_type"])
        # Put in index
        for key in keys:
            index.insert(key, q)

    print("Success! Added " + str(len(new_questions)) + " questions.")


def delete_question(index: InvertedIndex) -> None:
    print("\nEnter the Question ID to delete:")
    target_id: str = input(">> ")

    if target_id not in index.question_store:
        print("Error: Question ID not found in store.")
        return

    index.remove_question(target_id)
    print("Question " + target_id + " has been removed from the tree.")


def run_benchmark(index: InvertedIndex) -> None:
    print("\nRunning performance test...")
    if not index.question_store or not index.main_index:
        print("Error: No data to benchmark. Add a paper first.")
        return

    # Get a key that actually exists
    target_key: str = list(index.main_index.keys())[0]

    # Key Splitting Fix: New keys only have 3 parts (Subject_Topic_PaperType)
    parts: List[str] = target_key.split("_")
    subject: str = parts[0]
    topic: str = parts[1]
    ptype: str = parts[2]

    all_records: List[Dict[str, Any]] = []
    for qid in index.question_store:
        all_records.append(index.question_store[qid])

    loops: int = 1000

    # Test Inverted Index
    start_time: float = time.time()
    for i in range(loops):
        _ = index.query(target_key)
    end_time: float = time.time()
    index_total: float = end_time - start_time

    # Test Naive Scan
    start_time = time.time()
    for i in range(loops):
        matches: List[Dict[str, Any]] = []
        for r in all_records:
            if r["subject"] == subject and r["paper_type"] == ptype:
                if "text" in r and topic.lower() in r["text"].lower():
                    matches.append(r)
    end_time = time.time()
    naive_total: float = end_time - start_time

    print("Results over " + str(loops) + " runs:")
    print("Inverted Index Search: " + format(index_total, ".5f") + " seconds")
    print("Naive Linear Scan:     " + format(naive_total, ".5f") + " seconds")

    if index_total > 0:
        ratio = naive_total / index_total
        print("The Inverted Index is about " + str(int(ratio)) + "x faster!")


def main() -> None:
    # Updated to match your new index folder structure
    index_file_path: str = "data/index/physics_master_index.json"
    keyword_file_path: str = "data/keywords/keyword_map.json"
    papers_pool_path: str = "data/papers/qp"

    # Create object
    bank_index: InvertedIndex = InvertedIndex()

    # Load data if it exists
    if os.path.exists(index_file_path):
        print("Loading existing index...")
        bank_index.load(index_file_path)
    else:
        print("Starting with a fresh index.")
        build_master_index(papers_pool_path, keyword_file_path)
        bank_index.load(index_file_path)

    # Load keywords
    kw_map: Dict[str, Dict[str, List[str]]] = load_keyword_map(keyword_file_path)

    while True:
        show_menu()
        choice: str = input("Select an option: ")

        if choice == "1":
            view_tree(bank_index)
        elif choice == "2":
            search_topic(bank_index)
        elif choice == "3":
            add_paper(bank_index, kw_map)
        elif choice == "4":
            delete_question(bank_index)
        elif choice == "5":
            run_benchmark(bank_index)
        elif choice == "0":
            print("Saving changes to " + index_file_path + "...")
            bank_index.save(index_file_path)
            print("Done. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
