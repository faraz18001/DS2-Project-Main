import fitz

def dump_all_text(pdf_path):
    doc = fitz.open(pdf_path)
    # Dump just pages 2 and 3 and 4 to find Q2, Q4, Q7
    for page_num in [1, 2, 3]: # Pages 2, 3, 4
        page = doc[page_num]
        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))
        
        print(f"\n--- PAGE {page_num+1} ---")
        for block in blocks:
            x0, y0, x1, y1, text, _, _ = block
            print(f"[{x0:.1f}, {y0:.1f}] {text[:50].replace(chr(10), ' ')}")

if __name__ == "__main__":
    dump_all_text("data/5054_w25_qp_11.pdf")
