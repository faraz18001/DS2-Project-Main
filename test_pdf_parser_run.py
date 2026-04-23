import os
from pdf_parser import parse_paper

def main():
    pdf_path = "data/5054_w25_qp_11.pdf"
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return
        
    print(f"Testing PDF parser on {pdf_path}...")
    try:
        results = parse_paper(pdf_path, subject_code="5054", paper_type="qp_11", year=2025)
        print(f"Extracted {len(results)} questions.")
        for idx, q in enumerate(results[:5]): # Print first 5 for brevity
            print(f"Q{idx+1}: {q['id']}, Marks: {q['marks']}, Text snippet: {q['text'][:50].replace(chr(10), ' ')}...")
            
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
