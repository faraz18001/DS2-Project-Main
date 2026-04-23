"""
demo_runner.py — Terminal app to manage the question bank.
"""

import json
import os
import time
from typing import Any, Dict, List

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
    all_keys = []
    for k in index.main_index:
        all_keys.append(k)

    # Sort the list the long way
    for i in range(len(all_keys)):
        for j in range(i + 1, len(all_keys)):
            if all_keys[i] > all_keys[j]:
                temp = all_keys[i]
                all_keys[i] = all_keys[j]
                all_keys[j] = temp

    for key in all_keys:
        print("\n" + key)
        question_ids = index.main_index[key]
        for i in range(len(question_ids)):
            qid = question_ids[i]
            # Use connector to look like a tree
            connector = "├── "
            if i == len(question_ids) - 1:
                connector = "└── "
            print(connector + qid)


def search_topic(index: InvertedIndex) -> None:
    print("\nEnter topic/key to search (e.g., 5054_Forces_paper1_part1):")
    search_key = input(">> ")

    results = index.query(search_key)

    if len(results) == 0:
        print("No questions found for that key.")
    else:
        print("\nFound " + str(len(results)) + " questions:")
        for r in results:
            print("-" * 20)
            print("ID: " + r["id"])
            print("Marks: " + str(r["marks"]))
            # Show just a little bit of text
            snippet = r["text"][:100].replace("\n", " ")
            print("Text: " + snippet + "...")


def add_paper(
    index: InvertedIndex, keyword_map: Dict[str, Dict[str, List[str]]]
) -> None:
    print("\nEnter path to PDF file:")
    pdf_path = input(">> ")
    if not os.path.exists(pdf_path):
        print("Error: File not found.")
        return

    subject = input("Enter Subject Code (e.g., 5054): ")
    year = input("Enter Year: ")
    paper_type = input("Enter Paper Type (e.g., paper1_part1): ")

    print("Processing paper...")
    new_questions = parse_paper(pdf_path, subject, paper_type, int(year))

    for q in new_questions:
        # Get topics using the mapper
        topics = tag_question(q["text"], subject, keyword_map)
        # Create keys
        keys = build_composite_keys(subject, topics, paper_type)
        # Put in index
        for key in keys:
            index.insert(key, q)

    print("Success! Added " + str(len(new_questions)) + " questions.")


def delete_question(index: InvertedIndex) -> None:
    print("\nEnter the Question ID to delete:")
    target_id = input(">> ")

    if target_id not in index.question_store:
        print("Error: Question ID not found in store.")
        return

    index.remove_question(target_id)
    print("Question " + target_id + " has been removed from the tree.")


def run_benchmark(index: InvertedIndex) -> None:
    print("\nRunning performance test...")
    if not index.question_store:
        print("Error: No data to benchmark.")
        return

    # Get a key that actually exists
    target_key = ""
    for k in index.main_index:
        target_key = k
        break

    subject = "5054"
    # Find a topic from the key
    topic = target_key.split("_")[1]
    ptype = target_key.split("_")[2] + "_" + target_key.split("_")[3]

    all_records = []
    for qid in index.question_store:
        all_records.append(index.question_store[qid])

    loops = 1000

    # Test Inverted Index
    start_time = time.time()
    for i in range(loops):
        _ = index.query(target_key)
    end_time = time.time()
    index_total = end_time - start_time

    # Test Naive Scan
    start_time = time.time()
    for i in range(loops):
        matches = []
        for r in all_records:
            if r["subject"] == subject and r["paper_type"] == ptype:
                # This is a bit simplified but shows the point
                if "text" in r and topic.lower() in r["text"].lower():
                    matches.append(r)
    end_time = time.time()
    naive_total = end_time - start_time

    print("Results over " + str(loops) + " runs:")
    print("Inverted Index Search: " + format(index_total, ".5f") + " seconds")
    print("Naive Linear Scan:     " + format(naive_total, ".5f") + " seconds")

    if index_total > 0:
        ratio = naive_total / index_total
        print("The Inverted Index is about " + str(int(ratio)) + "x faster!")


def main() -> None:
    index_file = "physics_master_index.json"
    keyword_file = "data/keywords/keyword_map.json"

    # Create object
    bank_index = InvertedIndex()

    # Load data if it exists
    if os.path.exists(index_file):
        print("Loading existing index...")
        bank_index.load(index_file)
    else:
        print("Starting with a fresh index.")

    # Load keywords
    kw_map = load_keyword_map(keyword_file)

    while True:
        show_menu()
        choice = input("Select an option: ")

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
            print("Saving changes to " + index_file + "...")
            bank_index.save(index_file)
            print("Done. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
