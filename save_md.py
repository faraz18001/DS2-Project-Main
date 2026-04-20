import pymupdf4llm
from pathlib import Path

pdf_path = "data/5054_w25_qp_11.pdf"
md = pymupdf4llm.to_markdown(pdf_path, header=False, footer=False)
Path("output_md.md").write_text(md)
print("Markdown saved to output_md.md")
