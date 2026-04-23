import sys
import json
import os
from pdf_parser import parse_paper

def extract_to_json(pdf_path):
    # Ensure file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    # Infer metadata from filename
    # Example filename: 5054_w25_qp_11.pdf
    filename = os.path.basename(pdf_path)
    base_name = filename.replace(".pdf", "")
    parts = base_name.split("_")
    
    # Metadata extraction
    subject_code = parts[0]
    # w25 -> 2025
    year = 2000 + int(parts[1][1:]) 
    # qp_11
    paper_type = "_".join(parts[2:])

    print(f"Parsing {filename} (Subject: {subject_code}, Year: {year}, Type: {paper_type})...")
    
    results = parse_paper(pdf_path, subject_code, paper_type, year)
    
    output_filename = base_name + ".json"
    with open(output_filename, "w") as f:
        json.dump(results, f, indent=4)
    print(f"Successfully saved {len(results)} questions to {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_to_json.py <pdf_path>")
    else:
        extract_to_json(sys.argv[1])
