"""
test_image_extraction.py — Verify that pdf_parser correctly extracts images.
Run with:  python test_image_extraction.py
"""

import os
from pdf_parser import parse_paper

PDF_PATH   = "data/5054_w25_qp_12.pdf"   # pick a visually rich paper
SUBJECT    = "5054"
PAPER_TYPE = "qp_12"
YEAR       = 2025

print(f"Parsing: {PDF_PATH}\n{'='*60}")

questions = parse_paper(PDF_PATH, SUBJECT, PAPER_TYPE, YEAR)

print(f"Total questions extracted: {len(questions)}\n")

# --- Summary table ---
image_qs = [q for q in questions if q["has_images"]]
text_only = [q for q in questions if not q["has_images"]]

print(f"  Questions WITH images : {len(image_qs)}")
print(f"  Text-only questions   : {len(text_only)}")
print()

# --- Detail for image questions ---
if image_qs:
    print("Questions containing images:")
    print("-" * 60)
    for q in image_qs:
        print(f"  [{q['id']}]  marks={q['marks']}")
        for img in q["images"]:
            exists = "✓ exists" if os.path.isfile(img) else "✗ MISSING"
            print(f"    image: {img}  ({exists})")
        print()
else:
    print("No image-containing questions found in this paper.")
    print("(This may mean the paper is text-only, or the split regex needs tuning.)")

# --- Sanity-check first 3 questions ---
print("\nFirst 3 question previews:")
print("-" * 60)
for q in questions[:3]:
    preview = q["text"][:200].replace("\n", " ")
    print(f"[{q['id']}] marks={q['marks']} has_images={q['has_images']}")
    print(f"  text preview: {preview!r}")
    print()
