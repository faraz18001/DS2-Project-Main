"""
pipeline.py — End-to-end orchestration of the four-stage system.

Stage 1: PDF Ingestion    → parse PDFs, extract questions
Stage 2: Index Build      → insert records into inverted index
Stage 3: Query & Select   → filter by topic/year, run knapsack
Stage 4: Worksheet Output → generate the final PDF
"""

from typing import Any, Dict, List, Tuple

from config import *
from inverted_index import InvertedIndex
from knapsack import select_questions
from pdf_parser import parse_all_papers
from topic_mapper import build_composite_keys, load_keyword_map, tag_question
from worksheet_generator import generate_worksheet


def run_ingestion(subject_code: str) -> List[Dict[str, Any]]:
    """
    Stage 1: Parse all PDFs for a subject and tag each question with topics.

    Steps:
    1. Call parse_all_papers() to extract raw question records.
    2. Load the keyword map.
    3. For each question, run tag_question() to assign topic labels.
    4. Save the complete question bank to question_db.json.

    Args:
        subject_code: str, e.g. "9702".

    Returns:
        list of question record dicts (now with 'topics' field populated).
    """
    pass


def run_index_build(questions: List[Dict[str, Any]]) -> InvertedIndex:
    """
    Stage 2: Build the inverted index from tagged question records.

    Steps:
    1. Create a fresh InvertedIndex instance.
    2. For each question, build composite keys from its topics.
    3. Insert the question record under each composite key.
    4. Save the index to index.json for persistence.

    Args:
        questions: list of question record dicts with 'topics' field.

    Returns:
        InvertedIndex instance (populated and saved).
    """
    pass


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
    Stage 3: Query the index, filter results, and select via knapsack.

    Steps:
    1. Build composite keys from user-selected topics + paper type.
    2. Run union() or intersect() on the index depending on user choice.
    3. Apply year range filter on the results.
    4. Pass candidate pool to select_questions() with the target marks.

    Args:
        index: InvertedIndex instance.
        subject_code: str.
        topics: list of str, selected topics.
        paper_type: str, e.g. "P2".
        year_from: int.
        year_to: int.
        target_marks: int.

    Returns:
        list of selected question record dicts.
        int, actual total marks achieved.
    """
    pass


def run_generate(selected_questions: List[Dict[str, Any]], title: str) -> str:
    """
    Stage 4: Generate the worksheet PDF from selected questions.

    Steps:
    1. Build a descriptive output filename.
    2. Call generate_worksheet() with the selected questions.
    3. Return the path to the generated PDF.

    Args:
        selected_questions: list of question record dicts.
        title: str, worksheet title.

    Returns:
        str, path to the generated PDF file.
    """
    pass


def run_full_pipeline(
    subject_code: str,
    topics: List[str],
    paper_type: str,
    year_from: int,
    year_to: int,
    target_marks: int,
) -> str:
    """
    Run all four stages end-to-end.

    If a saved index exists, loads it instead of re-parsing (skip stages 1-2).
    Otherwise, runs ingestion → index build → query → generate.

    Args:
        subject_code, topics, paper_type, year_from, year_to, target_marks.

    Returns:
        str, path to the generated worksheet PDF.
    """
    pass
