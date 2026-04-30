"""
worksheet_generator.py — A4 PDF worksheet builder.

Takes a list of selected question records and compiles them into
a clean, annotatable A4 PDF using PyMuPDF's vector-preserving
show_pdf_page() stamping method.
"""
import os
import fitz
from typing import Any, Dict, List, Tuple

# A4 dimensions in PDF points (1 point = 1/72 inch)
PAGE_W = 595.0
PAGE_H = 842.0
MARGIN = 50.0   # left/right/top/bottom margin on the worksheet


def generate_worksheet(
    selected_questions: List[Dict[str, Any]],
    output_path: str,
    title: str = "Worksheet"
) -> str:

    # ── 1. Create blank A4 worksheet ──────────────────────────────
    ws_doc = fitz.open()   # new empty document

    ws_page = ws_doc.new_page(width=PAGE_W, height=PAGE_H)
    y_cursor = _stamp_header(ws_page, title, sum(q["marks"] for q in selected_questions))

    # ── 2. Stamp each question ────────────────────────────────────
    for q_num, question in enumerate(selected_questions, start=1):
        ws_page, y_cursor = _stamp_question(
            ws_doc, ws_page, y_cursor, question, q_num
        )

    # ── 3. Save ───────────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ws_doc.save(output_path)
    ws_doc.close()
    return output_path


def _stamp_header(page: fitz.Page, title: str, total_marks: int) -> float:
    """Draw the worksheet title and return the y position just below it."""
    
    # fitz.Page.insert_text(point, text, fontsize, color)
    # point = (x, y) where y is the BASELINE of the text
    page.insert_text(
        (MARGIN, MARGIN + 20),
        title,
        fontsize=16,
        color=(0, 0, 0)   # RGB 0-1 float, not 0-255
    )
    page.insert_text(
        (MARGIN, MARGIN + 38),
        f"Total Marks: {total_marks}",
        fontsize=10,
        color=(0.3, 0.3, 0.3)
    )

    # Draw a horizontal line using draw_line(p1, p2) then finish_shape()
    page.draw_line(
        fitz.Point(MARGIN, MARGIN + 48),
        fitz.Point(PAGE_W - MARGIN, MARGIN + 48)
    )

    return MARGIN + 65.0   # return y cursor just below the header


def _stamp_question(
    ws_doc: fitz.Document,
    ws_page: fitz.Page,
    y_cursor: float,
    question: Dict[str, Any],
    q_number: int,
) -> Tuple[fitz.Page, float]:

    src_doc = fitz.open(question["pdf"])

    for region in question["regions"]:
        src_page_num = region["page"]
        src_rect = fitz.Rect(region["rect"])  # e.g. [0, 53.8, 595.2, 717.6]

        # Height of this region in the source — used as-is, no scaling
        region_height = src_rect.height       # e.g. 717.6 - 53.8 = 663.8

        # Does this region fit on the current page?
        if y_cursor + region_height > PAGE_H:
            ws_page = ws_doc.new_page(width=PAGE_W, height=PAGE_H)
            y_cursor = 0.0

        # dest_rect is the SAME SIZE as src_rect → scale = 1.0
        dest_rect = fitz.Rect(
            0,                          # align to left edge of worksheet
            y_cursor,
            src_rect.width,             # same width as source (≈595)
            y_cursor + region_height    # same height as source
        )

        ws_page.show_pdf_page(
            dest_rect,
            src_doc,
            src_page_num,
            clip=src_rect        # crop exactly this region from source page
        )

        y_cursor += region_height   # advance cursor by exact content height

    src_doc.close()

    # Answer space below the question
    answer_height = _calculate_answer_space(question["marks"])

    if y_cursor + answer_height > PAGE_H:
        ws_page = ws_doc.new_page(width=PAGE_W, height=PAGE_H)
        y_cursor = 0.0

    answer_rect = fitz.Rect(40, y_cursor, PAGE_W - 40, y_cursor + answer_height)
    ws_page.draw_rect(answer_rect, color=(0.8, 0.8, 0.8), fill=None, width=0.5)

    y_cursor += answer_height + 20

    return ws_page, y_cursor

def _calculate_answer_space(marks: int) -> float:
    """30 points per mark, clamped between 60 and 300."""
    return max(60.0, min(300.0, marks * 30.0))