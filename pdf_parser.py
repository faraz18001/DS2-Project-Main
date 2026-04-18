"""
pdf_parser.py — PDF ingestion and question extraction.

Parses past paper PDFs using PyMuPDF (fitz), detects individual
question boundaries, extracts metadata (marks, page, bounding box),
and produces structured question records.
"""

import fitz
import re
import os

def parse_paper(pdf_path, subject_code, paper_type, year):
    """
    Parse a single past paper PDF and extract all questions.
    """
    doc = fitz.open(pdf_path)
    results = []
    
    page_num = 0
    while page_num < len(doc):
        page = doc[page_num]
        boundaries = detect_question_boundaries(page)
        
        b_idx = 0
        while b_idx < len(boundaries):
            b = boundaries[b_idx]
            q_num = b[0]
            start_y = b[1]
            end_y = b[2]
            
            bbox = compute_bbox(page, start_y, end_y)
            rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
            text = page.get_text("text", clip=rect)
            marks = extract_marks(text)
            
            q_id = str(subject_code) + "_" + str(year) + "_" + str(paper_type) + "_q" + str(q_num)
            
            record = {}
            record["id"] = q_id
            record["subject"] = subject_code
            record["topic"] = "Unknown" 
            record["paper_type"] = paper_type
            record["year"] = year
            record["marks"] = marks
            record["pdf"] = pdf_path
            record["page"] = page_num + 1
            record["bbox"] = bbox
            
            results.append(record)
            
            b_idx += 1
            
        page_num += 1
        
    return results

def detect_question_boundaries(page):
    """
    Identify where each question starts and ends on a single PDF page.
    """
    blocks = page.get_text("blocks")
    temp_boundaries = []
    
    i = 0
    while i < len(blocks):
        block = blocks[i]
        text = block[4].strip()
        
        match = re.match(r'^(\d+)[\.\s]', text)
        if match is not None:
            q_num = match.group(1)
            start_y = block[1]
            temp_boundaries.append([q_num, start_y])
        
        i += 1
        
    result_boundaries = []
    j = 0
    while j < len(temp_boundaries):
        curr = temp_boundaries[j]
        q_num = curr[0]
        start_y = curr[1]
        
        if j + 1 < len(temp_boundaries):
            end_y = temp_boundaries[j + 1][1]
        else:
            end_y = page.rect.y1
            
        result_boundaries.append((q_num, start_y, end_y))
        j += 1
        
    return result_boundaries

def extract_marks(text):
    """
    Extract the mark value from a question's text.
    """
    pattern = r'\[\s*(\d+)\s*(?:marks?)?\]'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    
    total_marks = 0
    idx = 0
    while idx < len(matches):
        string_val = matches[idx]
        total_marks += int(string_val)
        idx += 1
        
    return total_marks

def compute_bbox(page, start_y, end_y):
    """
    Compute the bounding box [x0, y0, x1, y1] for a question region.
    """
    x0 = page.rect.x0
    x1 = page.rect.x1
    y0 = start_y - 2.0
    y1 = end_y
    
    if y0 < page.rect.y0:
        y0 = page.rect.y0
        
    bbox = []
    bbox.append(x0)
    bbox.append(y0)
    bbox.append(x1)
    bbox.append(y1)
    
    return bbox

def parse_all_papers(papers_dir, subject_code):
    """
    Walk the papers directory for a subject and parse every PDF found.
    """
    all_questions = []
    
    for root, dirs, files in os.walk(papers_dir):
        file_idx = 0
        while file_idx < len(files):
            file_name = files[file_idx]
            
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(root, file_name)
                
                parts = pdf_path.split(os.sep)
                year_str = parts[-2]
                paper_type_pdf = parts[-1]
                
                year = int(year_str)
                temp = paper_type_pdf.split(".")
                paper_type = temp[0]
                
                paper_questions = parse_paper(pdf_path, subject_code, paper_type, year)
                
                q_idx = 0
                while q_idx < len(paper_questions):
                    q = paper_questions[q_idx]
                    all_questions.append(q)
                    q_idx += 1
                    
            file_idx += 1
            
    return all_questions
