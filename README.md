# Inverted Index-Based Past Paper Worksheet Generator

**CS201: Data Structures II — Spring 2026**

A tool that parses O/A-Level past paper PDFs, indexes questions by topic using a custom inverted index, selects optimal question subsets via 0/1 Knapsack DP, and generates vector-quality A4 PDF worksheets.

## Team
| Member | Student ID | Role |
|---|---|---|
| Widad Khan | wk09758 | Data & Ingestion |
| Ayesha Imran | — | Core Data Structure |
| Muhammad Murtaza | mm09736 | Algorithms & PDF Engine |
| Syed Faraz Ahmed Shah | sf10162 | Frontend & Integration |

## Project Structure
```
DS2-Project/
├── backend/
│   ├── app.py                   # Flask entry point & routes
│   ├── config.py                # Project-wide constants & paths
│   ├── inverted_index.py        # Custom InvertedIndex (core DS)
│   ├── knapsack.py              # 0/1 Knapsack DP selector
│   ├── pdf_parser.py            # PDF ingestion & question extraction
│   ├── topic_mapper.py          # Keyword → topic tagging
│   ├── worksheet_generator.py   # A4 PDF worksheet builder
│   ├── pipeline.py              # End-to-end orchestration
│   ├── requirements.txt
│   ├── data/
│   │   ├── papers/              # Source past paper PDFs
│   │   ├── keywords/            # Keyword mapping JSONs
│   │   └── output/              # Generated worksheets
│   └── tests/
│       ├── test_inverted_index.py
│       ├── test_knapsack.py
│       └── test_benchmark.py
├── frontend/                    # Web UI (Flask templates + static)
└── README.md
```

## Quick Start
```bash
cd backend
pip install -r requirements.txt
python app.py
```

## Tech Stack
- **Python 3.x** — core language
- **PyMuPDF (fitz)** — PDF parsing & vector stamping
- **Flask** — web backend
- **JSON** — index & keyword map persistence
