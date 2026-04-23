"""
pdf_parser.py — PDF ingestion and question extraction.
"""
"""
pdf_parser.py — Bounding Box (BBox) PDF ingestion and question extraction.
"""

import os
import re
import fitz  # Standard PyMuPDF

def parse_paper(pdf_path):
    """
    Parses a Cambridge past paper.
    Expects PapaCambridge naming convention: e.g., 9702_w25_qp_13.pdf
    """
    # 1. Parse the filename to get standard metadata
    file_name = os.path.basename(pdf_path)
    name_no_ext = os.path.splitext(file_name)[0]    
    parts = name_no_ext.split('_')
    
    if len(parts) >= 4:
        subject_code = parts[0]       # e.g., "9702"
        session_year = parts[1]       # e.g., "w25"
        variant = parts[3]            # e.g., "13"
        paper_type = f"p{variant}"    # e.g., "p13"


        # Takes "w25", grabs the "25", and adds 2000 to make it 2025
        actual_year = 2000 + int(session_year[1:])
    else:
        print(f"Warning: Filename {file_name} does not match PapaCambridge standard.")
        return []

    doc = fitz.open(pdf_path)
    questions = []
    current_q = None
    expected_q = 1
    
    # Regex to catch Cambridge question starts: e.g., "1 ", "2(a)", "3 " at the start of a block
    q_num_pattern = re.compile(r'^(\d+)\s')
    
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
                    "year" : actual_year,
                    "topic": "Unknown",
                    "marks": 0,
                    "pdf": os.path.abspath(pdf_path),
                    "text": "",  # Raw text for Bag-of-Words tagger
                    "regions": [] # Multi-page BBox tracker!
                }
                expected_q += 1

            # If we are currently tracking a question, accumulate its text and BBoxes
            if current_q:
                current_q["text"] += text + "\n "
                
                # Extract marks like [2] or [ 3 ] anywhere in the text
                mark_matches = re.findall(r'\[\s*(\d+)\s*\]', text)
                for m in mark_matches:
                    current_q["marks"] += int(m)
                    
                # Update Bounding Box Regions
                # If this is the FIRST block on this page for this question, start a new rect
                if not current_q["regions"] or current_q["regions"][-1]["page"] != page_num:
                    # Give it a tiny bit of vertical padding (-10 on top, +10 on bottom)
                    current_q["regions"].append({
                        "page": page_num,
                        "rect": [0, max(0, y0 - 10), page_width, y1 + 10] 
                    })
                else:
                    # We are on the same page, just extend the bottom Y coordinate down
                    current_q["regions"][-1]["rect"][3] = max(current_q["regions"][-1]["rect"][3], y1 + 10)

    # Append the very last question when the document ends
    if current_q:
        questions.append(current_q)
        
    # Fix for Paper 1 (MCQs): If no brackets [ ] were found, it's a 1-mark question
    for q in questions:
        if q["marks"] == 0 and "p1" in q["paper_type"].lower():
            q["marks"] = 1
            
    doc.close()
    return questions






# import os
# import re
# import struct

# import pymupdf4llm


# def parse_paper(pdf_path, subject_code, paper_type, year):
#     # Setup directory for images
#     project_root = os.path.dirname(os.path.abspath(__file__))
#     file_name = os.path.basename(pdf_path)
#     file_name_no_ext = os.path.splitext(file_name)[0]
#     folder_for_images = os.path.join(project_root, "data", "images", file_name_no_ext)

#     if not os.path.exists(folder_for_images):
#         os.makedirs(folder_for_images)

#     # Use library to get text in markdown format
#     md_content = pymupdf4llm.to_markdown(
#         pdf_path,
#         header=False,
#         footer=False,
#         write_images=True,
#         image_path=folder_for_images,
#     )

#     # Split the markdown content into pieces based on the question number
#     # It looks for lines that have a number surrounded by ** like **1**
#     # and maybe a dash before it
#     pieces = re.split(r"\n(?:- )?\*\*(\d{1,2})\*\*\s", md_content)

#     # The first piece is the intro/header stuff which we do not want
#     # So we start processing from the next piece
#     final_results = []

#     # Loop through the pieces in steps of 2
#     i = 1
#     while i < len(pieces):
#         question_number = pieces[i]
#         question_text = pieces[i + 1]

#         # Calculate marks
#         total_marks = 0

#         # Look for patterns like [2] or [ 2 marks ]
#         mark_pattern = r"\[\s*(\d+)\s*(?:marks?)?\]"
#         matches = re.findall(mark_pattern, question_text, flags=re.IGNORECASE)

#         for found_text in matches:
#             total_marks = total_marks + int(found_text)

#         # Find images used in this question
#         images_in_question = []
#         image_pattern = r"!\[([^\]]*)\]\(([^)]+)\)"
#         image_matches = re.findall(image_pattern, question_text)

#         image_count = 0
#         for alt_text, image_path_str in image_matches:
#             # Check if image file exists
#             original_path = image_path_str
#             if not os.path.exists(original_path):
#                 original_path = os.path.join(
#                     folder_for_images, os.path.basename(image_path_str)
#                 )

#             if os.path.exists(original_path):
#                 # Make a new, simple name: Q[number]_[count].png
#                 new_name = "Q" + question_number + "_" + str(image_count) + ".png"
#                 new_path = os.path.join(folder_for_images, new_name)

#                 # Rename the file
#                 os.rename(original_path, new_path)

#                 # Update the markdown text so it points to the new name
#                 question_text = question_text.replace(
#                     os.path.basename(image_path_str), new_name
#                 )

#                 images_in_question.append(os.path.abspath(new_path))
#                 image_count = image_count + 1

#         # Build the question dictionary
#         question_record = {}
#         question_record["id"] = (
#             subject_code + "_" + str(year) + "_" + paper_type + "_q" + question_number
#         )
#         question_record["subject"] = subject_code
#         question_record["topic"] = "Unknown"
#         question_record["paper_type"] = paper_type
#         question_record["year"] = year
#         question_record["marks"] = total_marks
#         question_record["pdf"] = pdf_path
#         question_record["text"] = question_text
#         question_record["images"] = images_in_question

#         # Add to our list
#         final_results.append(question_record)

#         # Move to next pair
#         i = i + 2

#     return final_results


# def parse_all_papers(papers_dir, subject_code):
#     all_extracted_questions = []

#     for root, folders, files in os.walk(papers_dir):
#         for file in files:
#             if file.endswith(".pdf"):
#                 full_path = os.path.join(root, file)

#                 # Get info from file path
#                 parts = full_path.split(os.sep)
#                 year_part = parts[-2]
#                 file_part = parts[-1]

#                 the_year = int(year_part)
#                 the_type = file_part.split(".")[0]

#                 questions = parse_paper(full_path, subject_code, the_type, the_year)

#                 for q in questions:
#                     all_extracted_questions.append(q)

#     return all_extracted_questions
