"""
pdf_parser.py — PDF ingestion and question extraction.
Uses pymupdf4llm for robust structure detection and text extraction.
"""

import pymupdf4llm
import re
import os

def parse_paper(pdf_path, subject_code, paper_type, year):
    """
    Parse a single past paper PDF using pymupdf4llm and extract all questions.
    """
    # Extract as markdown
    md = pymupdf4llm.to_markdown(pdf_path, header=False, footer=False)
    
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
        q_text = raw_questions[i+1]
        
        # Extract marks from q_text
        marks = extract_marks(q_text)
        
        q_id = f"{subject_code}_{year}_{paper_type}_q{q_num}"
        
        record = {
            "id": q_id,
            "subject": subject_code,
            "topic": "Unknown",
            "paper_type": paper_type,
            "year": year,
            "marks": marks,
            "pdf": pdf_path,
            "page": 0, # Not easily available in simple markdown approach
            "bbox": [], # Not available
            "text": q_text
        }
        results.append(record)
        i += 2
        
    return results

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
                # Infer metadata from path (same as before)
                parts = pdf_path.split(os.sep)
                year_str = parts[-2]
                paper_type_pdf = parts[-1]
                year = int(year_str)
                paper_type = paper_type_pdf.split(".")[0]
                
                all_questions.extend(parse_paper(pdf_path, subject_code, paper_type, year))
    return all_questions
