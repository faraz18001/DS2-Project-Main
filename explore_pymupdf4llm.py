import pymupdf4llm

pdf_path = "data/5054_w25_qp_11.pdf"
md = pymupdf4llm.to_markdown(pdf_path, header=False, footer=False)

print(md[:1000])
