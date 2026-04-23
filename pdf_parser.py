"""
pdf_parser.py — Bounding Box (BBox) PDF ingestion and question extraction.
"""

import os
import re
from typing import Any, Dict, List, Optional

import fitz  # Standard PyMuPDF


def parse_paper(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses a Cambridge past paper.
    Expects PapaCambridge naming convention: e.g., 9702_w25_qp_13.pdf
    """
    # 1. Parse the filename to get standard metadata
    file_name = os.path.basename(pdf_path)
    name_no_ext = os.path.splitext(file_name)[0]
    parts = name_no_ext.split("_")

    if len(parts) >= 4:
        subject_code = parts[0]  # e.g., "9702"
        session_year = parts[1]  # e.g., "w25"
        variant = parts[3]  # e.g., "13"
        paper_type = f"p{variant}"  # e.g., "p13"

        # Takes "w25", grabs the "25", and adds 2000 to make it 2025
        try:
            actual_year = 2000 + int(session_year[1:])
        except ValueError:
            actual_year = 2025  # Fallback
    else:
        print(f"Warning: Filename {file_name} does not match PapaCambridge standard.")
        return []

    doc = fitz.open(pdf_path)
    questions: List[Dict[str, Any]] = []
    current_q: Optional[Dict[str, Any]] = None
    expected_q = 1

    # Regex to catch Cambridge question starts: e.g., "1 ", "20", "3 " at the start of a block
    q_num_pattern = re.compile(r"^(\d+)\s")

    # Iterate through every page
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")

        # Sort blocks top-to-bottom so we read them in order
        blocks.sort(key=lambda b: b[1])

        # We will capture the full horizontal width of the page
        page_width = page.rect.width

        for b in blocks:
            x0, y0, x1, y1, text, block_no, block_type = b
            text = text.strip()

            # Check if this text block starts the NEXT sequential question
            match = q_num_pattern.match(text)
            if match and int(match.group(1)) == expected_q:
                # Close out the previous question and save it
                if current_q:
                    questions.append(current_q)

                # Start tracking the new question
                current_q = {
                    "id": f"{subject_code}_{session_year}_{paper_type}_q{expected_q}",
                    "subject": subject_code,
                    "paper_type": paper_type,
                    "session": session_year,
                    "year": actual_year,
                    "topic": "Unknown",
                    "marks": 0,
                    "pdf": os.path.abspath(pdf_path),
                    "text": "",  # Raw text for Bag-of-Words tagger
                    "regions": [],  # Multi-page BBox tracker!
                }
                expected_q += 1

            # If we are currently tracking a question, accumulate its text and BBoxes
            if current_q:
                current_q["text"] += text + "\n "

                # Extract marks like [2] or [ 3 ] anywhere in the text
                mark_matches = re.findall(r"\[\s*(\d+)\s*\]", text)
                for m in mark_matches:
                    current_q["marks"] += int(m)

                # Update Bounding Box Regions
                # If this is the FIRST block on this page for this question, start a new rect
                if (
                    not current_q["regions"]
                    or current_q["regions"][-1]["page"] != page_num
                ):
                    # Give it a tiny bit of vertical padding (-10 on top, +10 on bottom)
                    current_q["regions"].append(
                        {
                            "page": page_num,
                            "rect": [0, max(0, y0 - 10), page_width, y1 + 10],
                        }
                    )
                else:
                    # We are on the same page, just extend the bottom Y coordinate down
                    current_q["regions"][-1]["rect"][3] = max(
                        current_q["regions"][-1]["rect"][3], y1 + 10
                    )

    # Append the very last question when the document ends
    if current_q:
        questions.append(current_q)

    # Fix for Paper 1 (MCQs): If no brackets [ ] were found, it's a 1-mark question
    for q in questions:
        if q["marks"] == 0 and "p1" in q["paper_type"].lower():
            q["marks"] = 1

    doc.close()
    return questions


def parse_all_papers(papers_dir: str, subject_code: str) -> List[Dict[str, Any]]:
    """
    Legacy helper to parse all papers in a directory.
    """
    all_extracted_questions: List[Dict[str, Any]] = []

    for root, folders, files in os.walk(papers_dir):
        for file in files:
            if file.endswith(".pdf"):
                full_path = os.path.join(root, file)
                questions = parse_paper(full_path)
                all_extracted_questions.extend(questions)

    return all_extracted_questions
