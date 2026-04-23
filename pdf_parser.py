"""
pdf_parser.py — PDF ingestion and question extraction.

Uses pymupdf4llm for robust structure detection and text extraction.
Images embedded in questions are extracted and filtered to keep only
question diagrams (graphs, circuits, experiment setups, etc.).
Tiny decorative images, text-line renders, and MCQ label strips are
automatically discarded based on pixel dimensions.

Handles Cambridge filename convention:
    {subject}_{session}{yy}_{paper_code}.pdf
    e.g. 5054_mj25_11.pdf  →  subject=5054, session=mj, year=2025, code=11
    e.g. 9702_on24_22.pdf  →  subject=9702, session=on, year=2024, code=22

Paper code first digit is the paper type (11,12,13 → P1; 21,22,23 → P2; etc.)
"""

import pymupdf4llm
import re
import os
import struct


# ---------------------------------------------------------------------------
# Image-filtering thresholds
# ---------------------------------------------------------------------------
MIN_IMG_WIDTH  = 40     # pixels – reject images narrower than this
MIN_IMG_HEIGHT = 25     # pixels – reject images shorter than this
MIN_IMG_AREA   = 2500   # sq px  – reject overall tiny images
MAX_ASPECT     = 12.0   # w/h    – reject extremely thin horizontal strips


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------
def parse_cambridge_filename(filename):
    """
    Parse a Cambridge-format PDF filename into metadata.
    Returns None if the filename doesn't match the pattern.

    Expected: {subject}_{session}{yy}_{paper_code}.pdf
    Examples:
        5054_mj25_11.pdf → subject=5054, year=2025, session=mj, paper_type=P1, code=11
        9702_on24_22.pdf → subject=9702, year=2024, session=on, paper_type=P2, code=22
    """
    base = filename.replace(".pdf", "")
    parts = base.split("_")
    if len(parts) < 3:
        return None

    subject = parts[0]
    session_year = parts[1]   # "mj25", "on24", "f23"
    paper_code = parts[2]     # "11", "22", "42"

    # Split session (letters) from year (digits)
    session = ''.join(c for c in session_year if c.isalpha())
    year_str = ''.join(c for c in session_year if c.isdigit())

    if not year_str:
        return None

    # 2-digit year -> 20xx
    if len(year_str) == 2:
        year = 2000 + int(year_str)
    else:
        year = int(year_str)

    # First digit of paper_code is paper number
    if paper_code and paper_code[0].isdigit():
        paper_type = f"P{paper_code[0]}"
    else:
        paper_type = "P1"

    return {
        "subject":    subject,
        "year":       year,
        "session":    session or "x",
        "paper_type": paper_type,
        "paper_code": paper_code,
    }


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------
def parse_paper(pdf_path, subject_code, paper_type, year, paper_code=None, session=None):
    """
    Parse a single past paper PDF and extract all questions.

    Each question record includes:
      - id, subject, topic, paper_type, year, marks, pdf, page, bbox
      - text:       extracted markdown text (with inline image references stripped later)
      - images:     list of absolute paths to diagram images
      - has_images: True if any images were found
      - paper_code, session: original Cambridge metadata (for the source footer)
    """
    pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
    pdf_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    image_output_dir = os.path.join(pdf_dir, "images", pdf_stem)
    os.makedirs(image_output_dir, exist_ok=True)

    md = pymupdf4llm.to_markdown(
        pdf_path,
        write_images=True,
        image_path=image_output_dir,
    )

    # Split markdown at every question-start marker.
    # Matches: "\n1 Text", "\n- 1 Text", with 1-2 digit question numbers
    # and a capital-letter lookahead to avoid false splits inside "Fig. 2.1".
    raw_questions = re.split(r'\n(?:- )?(\d{1,2}) (?=[A-Z])', md)

    results = []
    if len(raw_questions) < 3:
        return results

    i = 1
    while i < len(raw_questions):
        if i + 1 >= len(raw_questions):
            break
        q_num = raw_questions[i]
        q_text = raw_questions[i + 1]

        marks = extract_marks(q_text)
        images = extract_image_paths(q_text, image_output_dir)

        q_id = f"{subject_code}_{year}_{paper_type}_{paper_code or 'x'}_q{q_num}"

        record = {
            "id": q_id,
            "subject": subject_code,
            "topic": "Unknown",
            "paper_type": paper_type,
            "paper_code": paper_code or paper_type,
            "session": session or "x",
            "year": year,
            "marks": marks,
            "pdf": pdf_path,
            "page": 0,
            "bbox": [],
            "text": q_text,
            "images": images,
            "has_images": len(images) > 0,
        }
        results.append(record)
        i += 2

    return results


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------
def _get_png_dimensions(image_path):
    """Read width/height from a PNG header (bytes 16-23 of IHDR chunk)."""
    try:
        with open(image_path, 'rb') as f:
            header = f.read(24)
            if len(header) >= 24 and header[:8] == b'\x89PNG\r\n\x1a\n':
                width  = struct.unpack('>I', header[16:20])[0]
                height = struct.unpack('>I', header[20:24])[0]
                return width, height
    except (IOError, struct.error):
        pass
    return None, None


def _is_diagram_image(image_path):
    """Reject tiny icons, text-strip renders, MCQ label strips, etc."""
    width, height = _get_png_dimensions(image_path)
    if width is None or height is None:
        return True    # can't tell - keep it
    if width < MIN_IMG_WIDTH or height < MIN_IMG_HEIGHT:
        return False
    if width * height < MIN_IMG_AREA:
        return False
    aspect = width / max(height, 1)
    if aspect > MAX_ASPECT:
        return False
    return True


def extract_image_paths(text, image_output_dir):
    """Extract image references from markdown, resolve paths, apply diagram filter."""
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)

    abs_paths = []
    for _alt, img_path in matches:
        resolved = None
        if os.path.isfile(img_path):
            resolved = os.path.abspath(img_path)

        if resolved is None:
            candidate = os.path.join(image_output_dir, os.path.basename(img_path))
            if os.path.isfile(candidate):
                resolved = os.path.abspath(candidate)

        if resolved is None:
            candidate = os.path.normpath(os.path.join(image_output_dir, img_path))
            if os.path.isfile(candidate):
                resolved = os.path.abspath(candidate)

        if resolved is None:
            continue
        if not _is_diagram_image(resolved):
            continue
        abs_paths.append(resolved)

    return abs_paths


def extract_marks(text):
    """
    Extract total marks from a question's text.
    Matches patterns like [3], [3 marks], [ 2 marks ].
    If a question has sub-parts with their own [n marks], they sum.
    """
    pattern = r'\[\s*(\d+)\s*(?:marks?)?\s*\]'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    total_marks = 0
    for s in matches:
        total_marks += int(s)
    return total_marks


# ---------------------------------------------------------------------------
# Batch parser
# ---------------------------------------------------------------------------
def parse_all_papers(papers_dir, subject_code):
    """
    Walk `papers_dir` recursively. For every PDF whose filename matches the
    Cambridge convention, parse it and accumulate the resulting question records.

    Files that can't be parsed from their filename are skipped with a warning.
    """
    all_questions = []

    if not os.path.isdir(papers_dir):
        print(f"[parse_all_papers] directory not found: {papers_dir}")
        return all_questions

    for root, _dirs, files in os.walk(papers_dir):
        for file_name in files:
            if not file_name.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(root, file_name)
            meta = parse_cambridge_filename(file_name)

            if meta is None:
                print(f"[parse_all_papers] skipping (name unparseable): {file_name}")
                continue

            # If the caller asked for a specific subject, filter.
            if subject_code and meta["subject"] != subject_code:
                continue

            print(f"[parse_all_papers] {file_name}  →  "
                  f"subject={meta['subject']}, year={meta['year']}, "
                  f"paper_type={meta['paper_type']} (code={meta['paper_code']})")

            questions = parse_paper(
                pdf_path,
                subject_code=meta["subject"],
                paper_type=meta["paper_type"],
                year=meta["year"],
                paper_code=meta["paper_code"],
                session=meta["session"],
            )
            all_questions.extend(questions)

    return all_questions
