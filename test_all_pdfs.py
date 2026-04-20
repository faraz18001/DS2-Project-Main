import os
import glob
from pdf_parser import parse_paper
import traceback

def main():
    pdf_files = sorted(glob.glob("data/*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in data/ directory.")
    
    success_count = 0
    fail_count = 0
    total_questions = 0
    
    for pdf in pdf_files:
        print(f"\nTesting {pdf}...")
        try:
            basename = os.path.basename(pdf)
            parts = basename.replace('.pdf', '').split('_')
            subject_code = parts[0] if len(parts) > 0 else "0000"
            year = parts[1] if len(parts) > 1 else "0000"
            paper_type = parts[2] + "_" + parts[3] if len(parts) > 3 else "unknown"
            
            questions = parse_paper(pdf, subject_code, paper_type, year)
            print(f"  Success: Extracted {len(questions)} questions.")
            success_count += 1
            total_questions += len(questions)
        except Exception as e:
            print(f"  Failed with exception:")
            traceback.print_exc()
            fail_count += 1
            
    print(f"\n--- Summary ---")
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Total Questions Extracted: {total_questions}")

if __name__ == "__main__":
    main()
