# """
# pdf_parser.py — Bounding Box (BBox) PDF ingestion and question extraction.
# """

# import os
# import re
# from typing import Any, Dict, List, Optional

# import fitz  # Standard PyMuPDF


# def parse_paper(pdf_path: str) -> List[Dict[str, Any]]:
#     """
#     Parses a Cambridge past paper.
#     Expects PapaCambridge naming convention: e.g., 9702_w25_qp_13.pdf
#     """
#     # 1. Parse the filename to get standard metadata
#     file_name = os.path.basename(pdf_path)
#     name_no_ext = os.path.splitext(file_name)[0]
#     parts = name_no_ext.split("_")

#     if len(parts) >= 4:
#         subject_code = parts[0]  # e.g., "9702"
#         session_year = parts[1]  # e.g., "w25"
#         variant = parts[3]  # e.g., "13"
#         paper_type = f"p{variant}"  # e.g., "p13"

#         # Takes "w25", grabs the "25", and adds 2000 to make it 2025
#         try:
#             actual_year = 2000 + int(session_year[1:])
#         except ValueError:
#             actual_year = 2025  # Fallback
#     else:
#         print(f"Warning: Filename {file_name} does not match PapaCambridge standard.")
#         return []

#     doc = fitz.open(pdf_path)
#     questions: List[Dict[str, Any]] = []
#     current_q: Optional[Dict[str, Any]] = None
#     expected_q = 1

#     # Regex to catch Cambridge question starts: e.g., "1 ", "20", "3 " at the start of a block
#     q_num_pattern = re.compile(r"^(\d+)\s")

#     # Iterate through every page
#     for page_num in range(len(doc)):
#         page = doc[page_num]
#         blocks = page.get_text("blocks")

#         # Sort blocks top-to-bottom so we read them in order
#         blocks.sort(key=lambda b: b[1])

#         # We will capture the full horizontal width of the page
#         page_width = page.rect.width

#         for b in blocks:
#             x0, y0, x1, y1, text, block_no, block_type = b
#             text = text.strip()

#             # Check if this text block starts the NEXT sequential question
#             match = q_num_pattern.match(text)
#             if match and int(match.group(1)) == expected_q:
#                 # Close out the previous question and save it
#                 if current_q:
#                     questions.append(current_q)

#                 # Start tracking the new question
#                 current_q = {
#                     "id": f"{subject_code}_{session_year}_{paper_type}_q{expected_q}",
#                     "subject": subject_code,
#                     "paper_type": paper_type,
#                     "session": session_year,
#                     "year": actual_year,
#                     "topic": "Unknown",
#                     "marks": 0,
#                     "pdf": os.path.abspath(pdf_path),
#                     "text": "",  # Raw text for Bag-of-Words tagger
#                     "regions": [],  # Multi-page BBox tracker!
#                 }
#                 expected_q += 1

#             # If we are currently tracking a question, accumulate its text and BBoxes
#             if current_q:
#                 current_q["text"] += text + "\n "

#                 # Extract marks like [2] or [ 3 ] anywhere in the text
#                 mark_matches = re.findall(r"\[\s*(\d+)\s*\]", text)
#                 for m in mark_matches:
#                     current_q["marks"] += int(m)

#                 # Update Bounding Box Regions
#                 # If this is the FIRST block on this page for this question, start a new rect
#                 if (
#                     not current_q["regions"]
#                     or current_q["regions"][-1]["page"] != page_num
#                 ):
#                     # Give it a tiny bit of vertical padding (-10 on top, +10 on bottom)
#                     current_q["regions"].append(
#                         {
#                             "page": page_num,
#                             "rect": [0, max(0, y0 - 10), page_width, y1 + 10],
#                         }
#                     )
#                 else:
#                     # We are on the same page, just extend the bottom Y coordinate down
#                     current_q["regions"][-1]["rect"][3] = max(
#                         current_q["regions"][-1]["rect"][3], y1 + 10
#                     )

#     # Append the very last question when the document ends
#     if current_q:
#         questions.append(current_q)

#     # Fix for Paper 1 (MCQs): If no brackets [ ] were found, it's a 1-mark question
#     for q in questions:
#         if q["marks"] == 0 and "p1" in q["paper_type"].lower():
#             q["marks"] = 1

#     doc.close()
#     return questions


# def parse_all_papers(papers_dir: str, subject_code: str) -> List[Dict[str, Any]]:
#     """
#     Legacy helper to parse all papers in a directory.
#     """
#     all_extracted_questions: List[Dict[str, Any]] = []

#     for root, folders, files in os.walk(papers_dir):
#         for file in files:
#             if file.endswith(".pdf"):
#                 full_path = os.path.join(root, file)
#                 questions = parse_paper(full_path)
#                 all_extracted_questions.extend(questions)

#     return all_extracted_questions

"""
pdf_parser.py — Bounding Box (BBox) PDF ingestion and question extraction.

FIX (v2): Switched from block-level to LINE-level parsing.
Root cause of original bug:
  - Cambridge PDFs merge multiple questions into one block, e.g.:
      "D  46 ± 4 cm s–2 \n\n\n3  What are the SI base units..."
    The regex ^(\d+)\s only checked the BLOCK start, so Q3 was never found.
  - Additionally, formula fractions (e.g. "3" from 3/2) and page number
    headers (e.g. "3" printed at top of page 3) both triggered false matches.

Fix approach:
  1. Use get_text("dict") for LINE-level bounding boxes.
  2. Only detect question numbers on lines in the LEFT MARGIN (x0 < Q_NUM_MAX_X=85).
     - Real question numbers: x0 ≈ 50 (always left-aligned in Cambridge papers).
     - Formula fractions: x0 ≥ 95 (centre/right of page).
     - Page number headers: x0 ≈ 295 (right-aligned or centre).
  3. Skip the header/footer zones (ly0 < MARGIN_TOP or ly0 > MARGIN_BOTTOM).
"""

import os
import re
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF


# ── Layout constants (A4 Cambridge past paper geometry) ─────────────
MARGIN_TOP: float = 55.0      # Skip PDF header region (page numbers, logos)
MARGIN_BOTTOM: float = 788.0  # Skip PDF footer region (copyright, page refs)
Q_NUM_MAX_X: float = 85.0     # Question numbers are always in the left margin


def parse_paper(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parse a Cambridge past paper PDF and extract questions as structured records.

    Each record contains:
        id, subject, paper_type, session, year, topic, marks, pdf, text, regions

    'regions' is a list of {page, rect} dicts — one per page the question spans —
    with rect = [x0, y0, x1, y1] in PDF points. Used by the worksheet generator
    to crop exact question areas from the source PDF without rasterization.

    Expects PapaCambridge naming convention: e.g. 9702_w25_qp_13.pdf
    """

    # ── 1. Extract metadata from filename ─────────────────────────────
    file_name = os.path.basename(pdf_path)
    name_no_ext = os.path.splitext(file_name)[0]
    parts = name_no_ext.split("_")

    if len(parts) >= 4:
        subject_code = parts[0]          # e.g. "9702"
        session_year = parts[1]          # e.g. "w25"
        variant = parts[3]               # e.g. "13"
        paper_type = f"p{variant}"       # e.g. "p13"
        try:
            actual_year = 2000 + int(session_year[1:])
        except ValueError:
            actual_year = 2025
    else:
        print(f"Warning: Filename '{file_name}' does not match PapaCambridge standard.")
        return []

    # ── 2. Regex: match a question number at the START of a line ──────
    # Accepts:
    #   "3"           → number only (question number on its own line)
    #   "3 What are…" → number followed by space and content
    # Does NOT accept:
    #   "3/2"         → filtered by x0 check (appears in centre of page)
    #   "30 Green…"   → correctly matches Q30
    q_num_pattern = re.compile(r"^(\d{1,2})(?:\s+\S|\s*$)")

    # ── 3. Parse PDF line-by-line ──────────────────────────────────────
    doc = fitz.open(pdf_path)
    questions: List[Dict[str, Any]] = []
    current_q: Optional[Dict[str, Any]] = None
    expected_q: int = 1

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dict = page.get_text("dict")
        page_width = page.rect.width

        # Collect all text lines from all blocks on this page
        all_lines: List[tuple] = []
        for block in page_dict["blocks"]:
            if block.get("type") != 0:          # skip image blocks
                continue
            for line in block["lines"]:
                lx0, ly0, lx1, ly1 = line["bbox"]
                # Join spans into a single string for this line
                line_text = " ".join(
                    span["text"] for span in line["spans"]
                ).strip()
                if line_text:
                    all_lines.append((lx0, ly0, lx1, ly1, line_text))

        # Sort lines by visual row first, then left-to-right within that row.
        # Cambridge PDFs render question numbers and their text on the SAME
        # visual line but as separate elements with y0 differing by ~1-2 px
        # (e.g. number "3" at y0=520.8, question text at y0=519.7).
        # Grouping into 5-pt buckets ensures the left-most element (question
        # number, x0≈50) is processed before the question text (x0≈71), so
        # the question boundary is detected before the text is accumulated.
        all_lines.sort(key=lambda l: (round(l[1] / 5) * 5, l[0]))

        for lx0, ly0, lx1, ly1, line_text in all_lines:

            # ── Skip header / footer zones ─────────────────────────────
            if ly0 < MARGIN_TOP or ly0 > MARGIN_BOTTOM:
                continue

            # ── Detect start of next question ──────────────────────────
            # Only consider lines that are in the left margin — the column
            # where Cambridge prints question numbers (x0 ≈ 50).
            # This filters out formula fractions, superscripts, and any
            # right-aligned page numbers that happen to be digits.
            if lx0 < Q_NUM_MAX_X:
                match = q_num_pattern.match(line_text)
                if match and int(match.group(1)) == expected_q:
                    # Save the completed previous question
                    if current_q:
                        questions.append(current_q)

                    # Initialise the new question record
                    current_q = {
                        "id": f"{subject_code}_{session_year}_{paper_type}_q{expected_q}",
                        "subject": subject_code,
                        "paper_type": paper_type,
                        "session": session_year,
                        "year": actual_year,
                        "topic": "Unknown",
                        "marks": 0,
                        "pdf": os.path.abspath(pdf_path),
                        "text": "",
                        "regions": [],
                    }
                    expected_q += 1

            # ── Accumulate content into the active question ────────────
            if current_q is None:
                continue

            current_q["text"] += line_text + "\n"

            # Extract marks e.g. [2] or [ 3 ]
            for m in re.findall(r"\[\s*(\d+)\s*\]", line_text):
                current_q["marks"] += int(m)

            # Update bounding-box regions (one rect per page)
            if (
                not current_q["regions"]
                or current_q["regions"][-1]["page"] != page_num
            ):
                # New page → start a new region rect
                current_q["regions"].append(
                    {
                        "page": page_num,
                        "rect": [0, max(0.0, ly0 - 10), page_width, ly1 + 10],
                    }
                )
            else:
                # Same page → extend the bottom of the existing rect
                current_q["regions"][-1]["rect"][3] = max(
                    current_q["regions"][-1]["rect"][3], ly1 + 10
                )

    # Append the final question
    if current_q:
        questions.append(current_q)

    # ── MCQ mark fix ───────────────────────────────────────────────────
    # Paper 1 questions carry no [N] marks bracket — each is worth 1 mark.
    for q in questions:
        if q["marks"] == 0 and paper_type.startswith("p1"):
            q["marks"] = 1

    doc.close()
    return questions


# ── Batch helper ────────────────────────────────────────────────────

def parse_all_papers(papers_dir: str, subject_code: str) -> List[Dict[str, Any]]:
    """
    Legacy helper: parse all PDFs in a directory tree.
    """
    all_questions: List[Dict[str, Any]] = []
    for root, _, files in os.walk(papers_dir):
        for file in files:
            if file.endswith(".pdf"):
                questions = parse_paper(os.path.join(root, file))
                all_questions.extend(questions)
    return all_questions