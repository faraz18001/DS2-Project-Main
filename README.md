# Inverted Index-Based Past Paper Worksheet Generator

**CS201: Data Structures II — Spring 2026**

A tool that parses O/A-Level past paper PDFs, indexes questions by topic using a custom inverted index, selects optimal question subsets via 0/1 Knapsack DP, and generates vector-quality A4 PDF worksheets.

## Overview

This project automates the creation of custom worksheets for Cambridge International Examinations (CIE) past papers. It is designed to extract questions from raw PDF papers, index them based on their subject and topic, and finally generate a clean, consolidated worksheet.

### Key Features
- **PDF Parser**: Uses PyMuPDF to extract text lines and bounding boxes from raw PDF files. It uses a 5-point bucket sorting algorithm and coordinate boundaries to reliably separate questions from headers, footers, and sidebars.
- **Inverted Index**: Implements a custom inverted index to map topics directly to specific questions, allowing for lightning-fast retrieval of questions by subject, year, and topic.
- **Knapsack Selection Algorithm**: Automatically selects the optimal subset of questions to reach a desired total mark count using a 0/1 Knapsack Dynamic Programming approach.
- **Worksheet Generator**: Compiles selected questions into a clean A4 PDF worksheet, completely removing source watermarks, barcodes, and margin text.

## Generated Worksheet Preview

![Generated Worksheet Preview](data/output/worksheet_preview.png)

## Project Structure
```text
DS2-Project/
├── backend/
│   ├── app.py                   # Flask entry point & routes
│   ├── config.py                # Project-wide constants & paths
│   ├── inverted_index.py        # Custom InvertedIndex (core DS)
│   ├── knapsack.py              # 0/1 Knapsack DP selector
│   ├── pdf_parser.py            # PDF ingestion & question extraction
│   ├── topic_mapper.py          # Keyword to topic tagging
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
- **Python 3.x**: Core programming language
- **PyMuPDF (fitz)**: PDF parsing and vector stamping
- **Flask**: Web backend routing
- **JSON**: Index and keyword map persistence
