"""
config.py — Project-wide constants and path definitions.
"""

import os
from typing import Dict, List

# ── Directory Paths ──────────────────────────────────────────────
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = os.path.join(BASE_DIR, "data")
PAPERS_DIR: str = os.path.join(DATA_DIR, "papers")
KEYWORDS_DIR: str = os.path.join(DATA_DIR, "keywords")
OUTPUT_DIR: str = os.path.join(DATA_DIR, "output")
TEMPLATES_DIR: str = os.path.join(BASE_DIR, "templates")
STATIC_DIR: str = os.path.join(BASE_DIR, "static")

# ── Index Persistence ───────────────────────────────────────────
INDEX_PATH: str = os.path.join(DATA_DIR, "index.json")
QUESTION_DB_PATH: str = os.path.join(DATA_DIR, "question_db.json")

# ── Keyword Map ─────────────────────────────────────────────────
KEYWORD_MAP_PATH: str = os.path.join(KEYWORDS_DIR, "keyword_map.json")

# ── PDF Generation Settings ─────────────────────────────────────
PAGE_WIDTH: int = 595  # A4 width in points
PAGE_HEIGHT: int = 842  # A4 height in points
MARGIN_TOP: int = 60
MARGIN_BOTTOM: int = 60
MARGIN_LEFT: int = 40
MARGIN_RIGHT: int = 40

# ── Supported Subjects ──────────────────────────────────────────
# Maps subject code → display name
SUBJECTS: Dict[str, str] = {
    "9702": "A-Level Physics",
    "9701": "A-Level Chemistry",
    "9709": "A-Level Mathematics",
    "4024": "O-Level Mathematics",
    "5070": "O-Level Chemistry",
    "5054": "O-Level Physics",
}

# ── Paper Types ──────────────────────────────────────────────────
PAPER_TYPES: List[str] = ["P1", "P2", "P3", "P4"]
