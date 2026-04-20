import fitz
import re

def debug_page(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1] # 0-indexed
    blocks = page.get_text("blocks")
    
    print(f"\n--- Debugging Page {page_num} of {pdf_path} ---")
    for block in blocks:
        x0, y0, x1, y1, text, _, _ = block
        text = text.strip()
        
        match = re.match(r'^(\d{1,2})([\.\s]|$)', text)
        if match:
            print(f"Match found: '{text[:20].replace(chr(10), ' ')}...' -> q_num={match.group(1)}, x0={x0:.2f}, y0={y0:.2f}, x1={x1:.2f}, y1={y1:.2f}")

if __name__ == "__main__":
    debug_page("data/5054_w25_qp_11.pdf", 3)
    debug_page("data/5054_w25_qp_11.pdf", 4)
    debug_page("data/5054_w25_qp_11.pdf", 5)
