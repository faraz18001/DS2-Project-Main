"""
pipeline.py — End-to-end orchestration of the four-stage system.

Stage 1: PDF Ingestion    → parse PDFs into question records
Stage 2: Index Build      → tag topics, insert into inverted index
Stage 3: Query & Select   → filter by topic/paper/year, run knapsack
Stage 4: Worksheet Output → vector-stamp selected questions onto an A4 PDF

The parser uses the PapaCambridge naming convention:
    {subject}_{session}_qp_{paper_code}.pdf
    e.g. 9702_w25_qp_13.pdf  →  paper_type "p13"
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from config import (
    PAPERS_DIR, KEYWORD_MAP_PATH, INDEX_PATH, QUESTION_DB_PATH, OUTPUT_DIR,
)
from inverted_index import InvertedIndex
from knapsack import select_questions
from pdf_parser import parse_paper
from topic_mapper import build_composite_keys, load_keyword_map, tag_question
from worksheet_generator import generate_worksheet


# ── Stage 1: ingestion ───────────────────────────────────────────────
def run_ingestion(subject_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Walk PAPERS_DIR, parse every Cambridge-named PDF, and tag topics
    on every question. Records the result to question_db.json.

    `subject_code=None` ingests every subject found in the papers folder.
    Pass a code (e.g. "9702") to restrict to one subject.

    Returns the list of tagged question record dicts.
    """
    if not os.path.isdir(PAPERS_DIR):
        raise FileNotFoundError(
            f"Papers directory not found: {PAPERS_DIR}\n"
            f"Place your PDFs under data/papers/ — Cambridge-style filenames "
            f"like 9702_w25_qp_13.pdf are required."
        )

    keyword_map = load_keyword_map(KEYWORD_MAP_PATH)
    all_questions: List[Dict[str, Any]] = []

    pdf_count = 0
    for root, _dirs, files in os.walk(PAPERS_DIR):
        for fname in files:
            if not fname.lower().endswith(".pdf"):
                continue
            if "_qp_" not in fname:
                # Cambridge marking schemes are "_ms_"; we only want question papers.
                continue

            pdf_path = os.path.join(root, fname)
            questions = parse_paper(pdf_path)
            if not questions:
                print(f"[ingestion] no questions extracted from {fname}")
                continue

            # Optional subject filter
            if subject_code and questions[0].get("subject") != subject_code:
                continue

            print(f"[ingestion] {fname}: {len(questions)} questions extracted")

            # Tag every question (topic_mapper is tier-aware)
            for q in questions:
                topics = tag_question(
                    q.get("text", ""),
                    q["subject"],
                    keyword_map,
                    q.get("paper_type", ""),
                )
                q["topic"] = topics

            all_questions.extend(questions)
            pdf_count += 1

    print(f"[ingestion] {pdf_count} PDFs parsed, "
          f"{len(all_questions)} questions total")

    # Persist the tagged question bank for inspection / debugging
    os.makedirs(os.path.dirname(QUESTION_DB_PATH), exist_ok=True)
    with open(QUESTION_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, indent=2, ensure_ascii=False)

    return all_questions


# ── Stage 2: index build ─────────────────────────────────────────────
def run_index_build(questions: List[Dict[str, Any]]) -> InvertedIndex:
    """
    Insert every tagged question into the inverted index under each
    composite key (subject_topic_paperType) it qualifies for, then save.
    """
    index = InvertedIndex(keyword_map_path=KEYWORD_MAP_PATH)

    for q in questions:
        topics = q.get("topic") or ["Uncategorized"]
        if isinstance(topics, str):
            topics = [topics]
        keys = build_composite_keys(q["subject"], topics, q["paper_type"])
        for key in keys:
            index.insert(key, q)

    index.save(INDEX_PATH)
    s = index.stats()
    print(f"[index] {s['n_keys']} keys, {s['n_questions']} questions, "
          f"{s['n_subjects']} subjects, "
          f"avg postings/key = {s['avg_postings']}")
    return index


# ── Stage 3: query, filter, knapsack ─────────────────────────────────
def run_query(
    index: InvertedIndex,
    subject_code: str,
    topics: List[str],
    paper_type: str,
    year_from: int,
    year_to: int,
    target_marks: int,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    1. Build composite keys for every (topic × {paper_type}) combination.
    2. Union the postings lists.
    3. Hydrate ids → records, applying year filter.
    4. Run knapsack to hit the target marks.

    `paper_type` may be a single variant (e.g. "p21") or a tier code
    ("AS"/"A2"/"ALL") — for tier codes we match every variant whose
    first digit puts it in that tier.
    """
    paper_variants = _expand_paper_types(index, subject_code, paper_type)
    keys = index.keys_for(subject_code, topics, paper_variants)
    print(f"[query] composite keys to fetch ({len(keys)}):")
    for k in keys[:8]:
        n = len(index.query(k))
        print(f"          {k}  ({n} postings)")
    if len(keys) > 8:
        print(f"          ... and {len(keys) - 8} more")

    candidate_ids = index.union(keys)
    candidates = index.fetch_documents(candidate_ids, year_from, year_to)
    print(f"[query] {len(candidate_ids)} ids before year filter, "
          f"{len(candidates)} survive [{year_from}, {year_to}]")

    if not candidates:
        return [], 0

    selected, actual = select_questions(candidates, target_marks)
    print(f"[query] knapsack: selected {len(selected)} questions "
          f"summing to {actual}/{target_marks} marks")
    return selected, actual


def _expand_paper_types(
    index: InvertedIndex,
    subject: str,
    requested: str,
) -> List[str]:
    """Resolve "AS"/"A2"/"ALL" or a single variant code to a list of
    actual paper variants present in the index."""
    available = index.list_paper_types(subject)
    if not available:
        return [requested]

    if requested == "ALL":
        return available
    if requested == "AS":
        return [p for p in available if p[1:2] in {"1", "2", "3"}]
    if requested == "A2":
        return [p for p in available if p[1:2] in {"4", "5"}]
    return [requested]


# ── Stage 4: worksheet generation ────────────────────────────────────
def run_generate(selected_questions: List[Dict[str, Any]], title: str) -> str:
    """Stamp the selection onto an A4 PDF. Returns the output path."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:80]
    output_path = os.path.join(OUTPUT_DIR, f"{safe}.pdf")
    generate_worksheet(selected_questions, output_path, title)
    print(f"[generate] worksheet written to {output_path}")
    return output_path


# ── End-to-end ───────────────────────────────────────────────────────
def run_full_pipeline(
    subject_code: str,
    topics: List[str],
    paper_type: str,
    year_from: int,
    year_to: int,
    target_marks: int,
) -> str:
    """
    Run all four stages. Loads a cached index from INDEX_PATH if present;
    otherwise re-ingests + rebuilds first.
    """
    index = InvertedIndex(keyword_map_path=KEYWORD_MAP_PATH)

    if os.path.exists(INDEX_PATH):
        index.load(INDEX_PATH)
        print(f"[pipeline] loaded cached index ({index.stats()})")
    else:
        print("[pipeline] no cached index — running ingestion + build")
        questions = run_ingestion()
        index = run_index_build(questions)

    selected, actual = run_query(
        index, subject_code, topics, paper_type,
        year_from, year_to, target_marks,
    )

    if not selected:
        title = f"empty_{subject_code}_{paper_type}"
        return run_generate([], title)

    topics_slug = "-".join(topics)[:40] if topics else "all"
    title = f"{subject_code}_{paper_type}_{topics_slug}_{actual}marks"
    return run_generate(selected, title)
