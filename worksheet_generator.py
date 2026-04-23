"""
worksheet_generator.py — A4 PDF worksheet builder.

Takes a list of selected question records and compiles them into
a clean, annotatable A4 PDF using PyMuPDF's vector-preserving
show_pdf_page() stamping method.
"""

from typing import Any, Dict, List, Tuple

import fitz


def generate_worksheet(
    selected_questions: List[Dict[str, Any]], output_path: str, title: str = "Worksheet"
) -> str:
    """
    Build the final A4 PDF worksheet from selected questions.

    Steps:
    1. Create a blank PDF with an A4 page.
    2. Stamp a header (title, date, total marks) at the top.
    3. Initialize a Y-cursor below the header.
    4. For each question:
       a. Open the source PDF and locate the page + bbox.
       b. Use show_pdf_page() to stamp the question region onto the
          worksheet at the current Y-cursor position — preserves vectors.
       c. Add a question label (Q1, Q2...) and source footer.
       d. Add proportional blank answer space (scaled by marks).
       e. Advance Y-cursor; if it exceeds page height, start a new page.
    5. Save the completed PDF to output_path.

    Args:
        selected_questions: list of question record dicts (ordered).
        output_path: str, where to save the generated PDF.
        title: str, worksheet title for the header.

    Returns:
        str, the output file path.
    """
    pass


def _stamp_header(page: fitz.Page, title: str, total_marks: int) -> float:
    """
    Draw the worksheet header on the first page.

    Includes: title text, date, total marks, a horizontal rule.

    Args:
        page: fitz.Page object (the current worksheet page).
        title: str, worksheet title.
        total_marks: int, sum of marks of all questions.

    Returns:
        float, the Y-coordinate just below the header (starting cursor).
    """
    pass


def _stamp_question(
    worksheet_doc: fitz.Document,
    page: fitz.Page,
    y_cursor: float,
    question: Dict[str, Any],
    question_number: int,
) -> Tuple[fitz.Page, float]:
    """
    Stamp a single question onto the worksheet at the given Y position.

    Uses fitz show_pdf_page() to copy the exact vector region from the
    source PDF onto the worksheet canvas — no rasterization.

    Also adds:
    - Question label: "Q{n}" to the left
    - Source footer: "[2022 P2 Q4 — Kinematics]" below the question
    - Blank answer space proportional to the question's mark value

    Args:
        worksheet_doc: fitz.Document, the worksheet being built.
        page: fitz.Page, current page of the worksheet.
        y_cursor: float, current vertical position on the page.
        question: dict, the question record.
        question_number: int, sequential question number (1-based).

    Returns:
        (fitz.Page, float): possibly a new page if overflow, and the updated y_cursor.
    """
    pass


def _calculate_answer_space(marks: int) -> float:
    """
    Determine how much blank space to leave for the answer.

    Rule of thumb: ~30 points per mark, clamped to a min/max range.

    Args:
        marks: int, the question's mark value.

    Returns:
        float, height in points for the answer space.
    """
    pass
