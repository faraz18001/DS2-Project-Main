"""
test_worksheet_diagrams.py — Stress-test worksheet generation with
diagram-heavy questions from Paper 22 (9702_w25_qp_22.pdf).

Questions chosen:
  Q2  — Spacecraft thruster diagram + carrier/payload diagram
  Q3  — Spring-pulley diagram + pulley force diagram
  Q5  — Circuit diagram + resistance-intensity graph
"""

import os
from worksheet_generator import generate_worksheet

BASE_PDF = "data/papers/qp/9702_w25_qp_22.pdf"

sample_questions = [
    {
        "id": "9702_w25_p22_q2",
        "subject": "9702",
        "paper_type": "p22",
        "session": "w25",
        "year": 2025,
        "topic": "Forces Density and Pressure",
        "marks": 12,
        "pdf": BASE_PDF,
        "text": "2\nA spacecraft in deep space uses jets...",
        "regions": [
            {"page": 5, "rect": [0, 53.8, 595.3, 820.0]},
            {"page": 6, "rect": [0, 53.8, 595.3, 820.0]},
            {"page": 7, "rect": [0, 53.8, 595.3, 820.0]},
            {"page": 8, "rect": [0, 53.8, 595.3, 790.0]},
        ],
    },
    {
        "id": "9702_w25_p22_q3",
        "subject": "9702",
        "paper_type": "p22",
        "session": "w25",
        "year": 2025,
        "topic": "Deformation of Solids",
        "marks": 9,
        "pdf": BASE_PDF,
        "text": "3\nA spring is fixed at one end...",
        "regions": [
            {"page": 9, "rect": [0, 53.8, 595.3, 820.0]},
            {"page": 10, "rect": [0, 53.8, 595.3, 820.0]},
        ],
    },
    {
        "id": "9702_w25_p22_q5",
        "subject": "9702",
        "paper_type": "p22",
        "session": "w25",
        "year": 2025,
        "topic": "DC Circuits",
        "marks": 11,
        "pdf": BASE_PDF,
        "text": "5\nFig. 5.1 shows a circuit...",
        "regions": [
            {"page": 13, "rect": [0, 53.8, 595.3, 820.0]},
            {"page": 14, "rect": [0, 53.8, 595.3, 820.0]},
        ],
    },
]

output_path = os.path.join("data", "output", "test_worksheet_diagrams.pdf")
os.makedirs(os.path.dirname(output_path), exist_ok=True)

result = generate_worksheet(
    selected_questions=sample_questions,
    output_path=output_path,
    title="9702 AS Physics — Diagram Stress Test"
)

print(f"Done. Worksheet saved to: {result}")
