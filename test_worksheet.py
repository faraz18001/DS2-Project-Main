"""
test_worksheet.py — Standalone test for worksheet generation.
Run from project root: python test_worksheet.py
"""

import os
from worksheet_generator import generate_worksheet

# ── Sample questions ─────────────────────────────────────────────
# Copy the pdf path to match where YOUR pdfs actually are on disk.
# Use raw strings (r"...") on Windows to avoid backslash issues.

BASE_PDF = r"data\papers\qp\9702_w25_qp_21.pdf"

sample_questions = [
    {
        "id": "9702_w25_p21_q1",
        "subject": "9702",
        "paper_type": "p21",
        "session": "w25",
        "year": 2025,
        "topic": "Kinematics",
        "marks": 10,
        "pdf": BASE_PDF,
        "text": "1\n(a) Define acceleration...",
        "regions": [
            {"page": 3, "rect": [0, 53.8, 595.2, 717.6]},
            {"page": 4, "rect": [0, 52.1, 595.2, 656.8]},
        ],
    },
    {
        "id": "9702_w25_p21_q2",
        "subject": "9702",
        "paper_type": "p21",
        "session": "w25",
        "year": 2025,
        "topic": "Forces Density and Pressure",
        "marks": 12,
        "pdf": BASE_PDF,
        "text": "2\n(a)(i) Define pressure...",
        "regions": [
            {"page": 5, "rect": [0, 53.8, 595.2, 757.2]},
            {"page": 6, "rect": [0, 54.2, 595.2, 618.2]},
        ],
    },
]

# ── Run ──────────────────────────────────────────────────────────
output_path = os.path.join("data", "output", "test_worksheet.pdf")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

result = generate_worksheet(
    selected_questions=sample_questions,
    output_path=output_path,
    title="9702 AS Physics — Test Worksheet"
)

print(f"Done. Worksheet saved to: {result}")