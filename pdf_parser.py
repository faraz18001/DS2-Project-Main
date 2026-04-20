"""
pdf_parser.py — PDF ingestion and question extraction.
Uses pymupdf4llm for robust structure detection and text extraction.
Images embedded in questions are extracted and filtered to keep only
question diagrams (graphs, circuits, experiment setups, etc.).
Tiny decorative images, text-line renders, and MCQ label strips are
automatically discarded based on pixel dimensions.
"""

import pymupdf4llm
import re
import os
import struct

# ---------------------------------------------------------------------------
# Image-filtering thresholds – tweak these if legitimate diagrams are
# being dropped or junk images are sneaking through.
# ---------------------------------------------------------------------------
MIN_IMG_WIDTH  = 40     # pixels – reject images narrower than this
MIN_IMG_HEIGHT = 25     # pixels – reject images shorter than this
MIN_IMG_AREA   = 2500   # sq px  – reject overall tiny images
MAX_ASPECT     = 12.0   # w/h    – reject extremely thin horizontal strips


def parse_paper(pdf_path, subject_code, paper_type, year):
    """
    Parse a single past paper PDF using pymupdf4llm and extract all questions.
    Images found in the PDF are saved to an 'images/' subdirectory next to the PDF.
    Each question record includes:
      - 'text':       the extracted markdown text (with inline image references)
      - 'images':     list of absolute paths to images belonging to this question
      - 'has_images': True if any images were found in the question
    """
    # Save images into a sibling 'images/<pdf_stem>/' directory
    pdf_dir = os.path.dirname(os.path.abspath(pdf_path))
    pdf_stem = os.path.splitext(os.path.basename(pdf_path))[0]
    image_output_dir = os.path.join(pdf_dir, "images", pdf_stem)
    os.makedirs(image_output_dir, exist_ok=True)

    # Extract as markdown, writing any embedded images to disk
    md = pymupdf4llm.to_markdown(
        pdf_path,
        header=False,
        footer=False,
        write_images=True,
        image_path=image_output_dir,
    )

    # Split by potential question number pattern:
    # A line starting with bold number: **1** or bulleted bold: - **1**
    raw_questions = re.split(r'\n(?:-\s*)?\*\*(\d+)\*\*\s', md)

    # The first part is header, so skip it.
    # raw_questions will be [header, q1_num, q1_text, q2_num, q2_text, ...]

    results = []
    if len(raw_questions) < 3:
        return results

    # Start from index 1 (the first question number)
    i = 1
    while i < len(raw_questions):
        q_num = raw_questions[i]
        q_text = raw_questions[i + 1]

        # Extract marks from q_text
        marks = extract_marks(q_text)

        # Extract image paths referenced in this question's markdown block
        images = extract_image_paths(q_text, image_output_dir)

        q_id = f"{subject_code}_{year}_{paper_type}_q{q_num}"

        record = { 
            "id": q_id,
            "subject": subject_code,
            "topic": "Unknown",
            "paper_type": paper_type,
            "year": year,
            "marks": marks,
            "pdf": pdf_path,
            "page": 0,       # Not easily available in simple markdown approach
            "bbox": [],      # Not available
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
    """
    Read width and height from a PNG file header (bytes 16-23 of IHDR chunk).
    Returns (width, height) or (None, None) on failure.
    """
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
    """
    Return True if the image at *image_path* looks like a real question
    diagram rather than a tiny icon, a text-line render, or an MCQ label
    strip.  The check is purely dimension-based and intentionally lenient
    so that genuine but small diagrams are not accidentally dropped.
    """
    width, height = _get_png_dimensions(image_path)
    if width is None or height is None:
        # Can't read dimensions — keep the image to be safe
        return True

    # Too narrow or too short → decorative / icon
    if width < MIN_IMG_WIDTH or height < MIN_IMG_HEIGHT:
        return False

    # Overall area too small
    if width * height < MIN_IMG_AREA:
        return False

    # Extremely wide-and-thin → text rendered as an image strip
    aspect = width / max(height, 1)
    if aspect > MAX_ASPECT:
        return False

    return True


def extract_image_paths(text, image_output_dir):
    """
    Parse all Markdown image references from a question text block and
    return a list of absolute file paths to the extracted *diagram* images.

    pymupdf4llm writes images with paths like:
        ![](relative/path/to/image.png)
    or
        ![](absolute/path/to/image.png)

    We resolve each path, check that the file exists, apply the diagram
    filter, and return only images that pass.
    """
    # Match standard Markdown image syntax: ![alt text](path)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)

    abs_paths = []
    for _alt, img_path in matches:
        # pymupdf4llm may emit a path relative to CWD (including the
        # image_output_dir prefix) or just a bare filename.  Try to
        # resolve correctly without doubling the directory.
        resolved = None

        # 1. Try as-is (relative to CWD or absolute)
        if os.path.isfile(img_path):
            resolved = os.path.abspath(img_path)

        # 2. Try as a bare filename inside image_output_dir
        if resolved is None:
            candidate = os.path.join(image_output_dir, os.path.basename(img_path))
            if os.path.isfile(candidate):
                resolved = os.path.abspath(candidate)

        # 3. Try joining full path with image_output_dir (legacy fallback)
        if resolved is None:
            candidate = os.path.normpath(os.path.join(image_output_dir, img_path))
            if os.path.isfile(candidate):
                resolved = os.path.abspath(candidate)

        if resolved is None:
            # File not found at all – skip silently
            continue

        # Apply diagram filter – skip tiny / text-line / decorative images
        if not _is_diagram_image(resolved):
            continue

        abs_paths.append(resolved)

    return abs_paths


def extract_marks(text):
    """
    Extract the mark value from a question's text.
    """
    pattern = r'\[\s*(\d+)\s*(?:marks?)?\]'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    total_marks = 0
    for string_val in matches:
        total_marks += int(string_val)

    return total_marks


def parse_all_papers(papers_dir, subject_code):
    """
    Walk the papers directory for a subject and parse every PDF found.
    """
    all_questions = []

    for root, dirs, files in os.walk(papers_dir):
        for file_name in files:
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(root, file_name)
                # Infer metadata from path
                parts = pdf_path.split(os.sep)
                year_str = parts[-2]
                paper_type_pdf = parts[-1]
                year = int(year_str)
                paper_type = paper_type_pdf.split(".")[0]

                all_questions.extend(
                    parse_paper(pdf_path, subject_code, paper_type, year)
                )

    return all_questions
