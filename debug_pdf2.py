import fitz
import re

def debug_all(pdf_path):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        
        for block in blocks:
            x0, y0, x1, y1, text, _, _ = block
            text = text.strip()
            
            # Match 1-2 digits, followed by space or dot, and AT LEAST some text to avoid standalone numbers
            match = re.match(r'^(\d{1,2})[\s]+([A-Z].*)', text.replace('\n', ' '))
            if match:
                print(f"P{page_num+1} Q{match.group(1)} | x0={x0:.2f}, y0={y0:.2f} | text='{text[:30].replace(chr(10), ' ')}...'")

if __name__ == "__main__":
    debug_all("data/5054_w25_qp_11.pdf")
