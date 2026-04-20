import fitz
import re

def find_all_questions(pdf_path):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")
        
        # Sort by y0, then x0
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        
        for block in blocks:
            x0, y0, x1, y1, text, _, _ = block
            text = text.strip()
            
            # Match standalone number OR number with text
            match = re.match(r'^(\d{1,2})\b', text)
            if match and int(match.group(1)) > 0 and int(match.group(1)) <= 40:
                print(f"P{page_num+1} Q{match.group(1)} | x0={x0:.2f}, y0={y0:.2f} | text='{text[:30].replace(chr(10), ' ')}...'")

if __name__ == "__main__":
    find_all_questions("data/5054_w25_qp_11.pdf")
