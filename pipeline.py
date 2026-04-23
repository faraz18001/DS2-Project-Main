"""
pipeline.py — End-to-end orchestration of the four-stage system.

Stage 1: PDF Ingestion    → parse PDFs, extract questions + images + marks
Stage 2: Index Build      → tag topics, insert records into inverted index
Stage 3: Query & Select   → filter by topic/year, run knapsack for target marks
Stage 4: Worksheet Output → stamp selected questions onto an A4 PDF
"""

import json
import os

from config import (
    PAPERS_DIR, KEYWORD_MAP_PATH, INDEX_PATH, QUESTION_DB_PATH, OUTPUT_DIR,
)
from inverted_index import InvertedIndex
from pdf_parser import parse_all_papers
from topic_mapper import load_keyword_map, tag_question, build_composite_keys
from knapsack import select_questions
from worksheet_generator import generate_worksheet


# ── Stage 1: Ingestion ────────────────────────────────────────────────────
def run_ingestion(subject_code):
    """
    Parse every PDF under data/papers/<subject_code>/, tag topics from the
    keyword map, and persist the full tagged question bank to question_db.json.

    Returns the list of tagged question record dicts.
    """
    subject_papers_dir = os.path.join(PAPERS_DIR, subject_code)
    if not os.path.isdir(subject_papers_dir):
        raise FileNotFoundError(
            f"No papers directory found at {subject_papers_dir}. "
            f"Put your PDFs there before running ingestion."
        )

    questions = parse_all_papers(subject_papers_dir, subject_code)
    print(f"[ingestion] extracted {len(questions)} questions from PDFs")

    keyword_map = load_keyword_map(KEYWORD_MAP_PATH)

    for q in questions:
        q["topics"] = tag_question(q.get("text", ""), subject_code, keyword_map)

    os.makedirs(os.path.dirname(QUESTION_DB_PATH), exist_ok=True)
    with open(QUESTION_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)

    # Diagnostic: topic distribution
    topic_counts = {}
    for q in questions:
        for t in q["topics"]:
            topic_counts[t] = topic_counts.get(t, 0) + 1
    print(f"[ingestion] topic distribution: {topic_counts}")
    print(f"[ingestion] wrote {QUESTION_DB_PATH}")

    return questions


# ── Stage 2: Index build ──────────────────────────────────────────────────
def run_index_build(questions):
    """
    Insert each tagged question into the inverted index under every
    composite key (subject, topic, paper_type) it qualifies for.
    Persist to index.json.
    """
    index = InvertedIndex()
    for q in questions:
        topics = q.get("topics") or ["Uncategorized"]
        for topic in topics:
            key = f"{q['subject']}_{topic}_{q['paper_type']}"
            index.insert(key, q)

    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    index.save(INDEX_PATH)
    print(f"[index] {index.key_count()} keys, {len(index)} unique questions")
    return index


# ── Stage 3: Query, filter, select ────────────────────────────────────────
def run_query(index, subject_code, topics, paper_type, year_from, year_to, target_marks):
    """
    Compose keys from user selections, union postings lists, apply year
    filter, pass candidates to knapsack.

    Returns (selected_questions, actual_total_marks).
    """
    keys = build_composite_keys(subject_code, topics, paper_type)
    print(f"[query] searching keys: {keys}")

    candidates = index.union(keys)
    print(f"[query] {len(candidates)} candidates before year filter")

    filtered = index.filter_by_year(candidates, year_from, year_to)
    print(f"[query] {len(filtered)} candidates after year filter "
          f"[{year_from}, {year_to}]")

    if not filtered:
        print("[query] no candidates matched — returning empty selection")
        return [], 0

    selected, actual = select_questions(filtered, target_marks)
    print(f"[query] knapsack selected {len(selected)} questions "
          f"totalling {actual}/{target_marks} marks")
    return selected, actual


# ── Stage 4: Worksheet generation ─────────────────────────────────────────
def run_generate(selected_questions, title):
    """Write the worksheet PDF. Returns the output file path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
    output_path = os.path.join(OUTPUT_DIR, f"{safe}.pdf")
    generate_worksheet(selected_questions, output_path, title)
    print(f"[generate] worksheet written to {output_path}")
    return output_path


# ── End-to-end orchestration ──────────────────────────────────────────────
def run_full_pipeline(subject_code, topics, paper_type, year_from, year_to, target_marks):
    """
    Full pipeline. Reuses a cached index if one exists on disk, otherwise
    runs ingestion + index build first.
    """
    index = InvertedIndex()

    if os.path.exists(INDEX_PATH):
        index.load(INDEX_PATH)
        print(f"[pipeline] loaded cached index from {INDEX_PATH}")
    else:
        print("[pipeline] no cached index — running ingestion")
        questions = run_ingestion(subject_code)
        index = run_index_build(questions)

    selected, actual = run_query(
        index, subject_code, topics, paper_type,
        year_from, year_to, target_marks,
    )

    if not selected:
        # Still produce an (empty) PDF so the Flask route has something to send.
        title = f"empty_worksheet_{subject_code}_{paper_type}"
        return run_generate([], title)

    topics_slug = '-'.join(topics) if topics else 'all'
    title = f"{subject_code}_{paper_type}_{topics_slug}_{actual}marks"
    return run_generate(selected, title)
