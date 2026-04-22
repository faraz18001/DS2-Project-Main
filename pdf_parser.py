"""
pdf_parser.py — PDF ingestion and question extraction.
"""

import pymupdf4llm
import re
import os
import struct

def parse_paper(pdf_path, subject_code, paper_type, year):
    # Setup directory for images
    parent_folder = os.path.dirname(os.path.abspath(pdf_path))
    file_name = os.path.basename(pdf_path)
    file_name_no_ext = os.path.splitext(file_name)[0]
    folder_for_images = os.path.join(parent_folder, "images", file_name_no_ext)
    
    if not os.path.exists(folder_for_images):
        os.makedirs(folder_for_images)

    # Use library to get text in markdown format
    md_content = pymupdf4llm.to_markdown(
        pdf_path,
        header=False,
        footer=False,
        write_images=True,
        image_path=folder_for_images,
    )

    # Split the markdown content into pieces based on the question number
    # It looks for lines that have a number surrounded by ** like **1**
    # and maybe a dash before it
    pieces = re.split(r'\n(?:- )?\*\*(\d{1,2})\*\*\s', md_content)
    
    # The first piece is the intro/header stuff which we do not want
    # So we start processing from the next piece
    final_results = []
    
    # Loop through the pieces in steps of 2
    i = 1
    while i < len(pieces):
        question_number = pieces[i]
        question_text = pieces[i+1]
        
        # Calculate marks
        total_marks = 0
        
        # Look for patterns like [2] or [ 2 marks ]
        mark_pattern = r'\[\s*(\d+)\s*(?:marks?)?\]'
        matches = re.findall(mark_pattern, question_text, flags=re.IGNORECASE)
        
        for found_text in matches:
            total_marks = total_marks + int(found_text)
            
        # Find images used in this question
        images_in_question = []
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        image_matches = re.findall(image_pattern, question_text)
        
        image_count = 0
        for alt_text, image_path_str in image_matches:
            # Check if image file exists
            original_path = image_path_str
            if not os.path.exists(original_path):
                original_path = os.path.join(folder_for_images, os.path.basename(image_path_str))
                
            if os.path.exists(original_path):
                # Make a new, simple name: Q[number]_[count].png
                new_name = "Q" + question_number + "_" + str(image_count) + ".png"
                new_path = os.path.join(folder_for_images, new_name)
                
                # Rename the file
                os.rename(original_path, new_path)
                
                # Update the markdown text so it points to the new name
                question_text = question_text.replace(os.path.basename(image_path_str), new_name)
                
                images_in_question.append(os.path.abspath(new_path))
                image_count = image_count + 1
        
        # Build the question dictionary
        question_record = {}
        question_record["id"] = subject_code + "_" + str(year) + "_" + paper_type + "_q" + question_number
        question_record["subject"] = subject_code
        question_record["topic"] = "Unknown"
        question_record["paper_type"] = paper_type
        question_record["year"] = year
        question_record["marks"] = total_marks
        question_record["pdf"] = pdf_path
        question_record["text"] = question_text
        question_record["images"] = images_in_question
        
        # Add to our list
        final_results.append(question_record)
        
        # Move to next pair
        i = i + 2
        
    return final_results

def parse_all_papers(papers_dir, subject_code):
    all_extracted_questions = []
    
    for root, folders, files in os.walk(papers_dir):
        for file in files:
            if file.endswith(".pdf"):
                full_path = os.path.join(root, file)
                
                # Get info from file path
                parts = full_path.split(os.sep)
                year_part = parts[-2]
                file_part = parts[-1]
                
                the_year = int(year_part)
                the_type = file_part.split(".")[0]
                
                questions = parse_paper(full_path, subject_code, the_type, the_year)
                
                for q in questions:
                    all_extracted_questions.append(q)
                    
    return all_extracted_questions
