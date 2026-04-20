"""
pdf_parser.py — PDF ingestion and question extraction.
Uses pymupdf4llm for robust structure detection and text extraction.
Images embedded in questions are extracted and their paths stored per record.
"""

import pymupdf4llm
import re
import os

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
        # Paths in markdown are relative to CWD (where the script is run from)
        images = extract_image_paths(q_text)

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


def extract_image_paths(text):
    """
    Parse all Markdown image references from a question text block and
    return a list of absolute file paths to the extracted images.

    pymupdf4llm writes image paths relative to the current working directory
    (i.e. wherever you run the script from).  We resolve them to absolute
    paths from CWD so they are portable regardless of how the module is imported.
    """
    cwd = os.getcwd()

    # Match standard Markdown image syntax: ![alt text](path)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, text)

    abs_paths = []
    for _alt, img_path in matches:
        if not os.path.isabs(img_path):
            img_path = os.path.join(cwd, img_path)
        img_path = os.path.normpath(img_path)
        abs_paths.append(img_path)

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
