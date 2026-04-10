"""
pdf_parser.py — PDF ingestion and question extraction.

Parses past paper PDFs using PyMuPDF (fitz), detects individual
question boundaries, extracts metadata (marks, page, bounding box),
and produces structured question records.
"""


def parse_paper(pdf_path, subject_code, paper_type, year):
    """
    Parse a single past paper PDF and extract all questions.

    Steps:
    1. Open the PDF with fitz.
    2. Iterate pages; on each page, extract text blocks.
    3. Use regex to detect question boundaries ("1 ", "2 ", etc.).
    4. For each detected question, compute bounding-box coordinates
       by combining the text block rects from start to the next question.
    5. Extract mark value from the question text (e.g. "[4]" → 4 marks).
    6. Build a question record dict with all metadata fields.

    Args:
        pdf_path: str, absolute path to the PDF file.
        subject_code: str, e.g. "9702".
        paper_type: str, e.g. "P2".
        year: int, e.g. 2022.

    Returns:
        list of question record dicts.
    """
    pass


def _detect_question_boundaries(page):
    """
    Identify where each question starts and ends on a single PDF page.

    Approach: scan text blocks for patterns matching question numbers
    (e.g. bold "1", "2" at the left margin). Each match marks the start
    of a new question; the previous question ends just above it.

    Args:
        page: fitz.Page object.

    Returns:
        list of (question_number, start_y, end_y) tuples.
    """
    pass


def _extract_marks(text):
    """
    Extract the mark value from a question's text.

    Looks for patterns like "[4]", "[6 marks]", or "....... [3]"
    at the end of the question or sub-parts. Sums marks if multi-part.

    Args:
        text: str, the raw text content of one question.

    Returns:
        int, total marks for the question.
    """
    pass


def _compute_bbox(page, start_y, end_y):
    """
    Compute the bounding box [x0, y0, x1, y1] for a question region.

    Uses the page width and the detected vertical boundaries,
    adding small padding for clean cropping.

    Args:
        page: fitz.Page object.
        start_y: float, top Y coordinate of the question.
        end_y: float, bottom Y coordinate of the question.

    Returns:
        list of four floats [x0, y0, x1, y1].
    """
    pass


def parse_all_papers(papers_dir, subject_code):
    """
    Walk the papers directory for a subject and parse every PDF found.

    Expected directory layout:
        papers/{subject_code}/{year}/{paper_type}.pdf

    Aggregates all question records across all years and paper types.

    Args:
        papers_dir: str, path to the top-level papers directory.
        subject_code: str, e.g. "9702".

    Returns:
        list of all question record dicts for the subject.
    """
    pass
