"""
topic_mapper.py — Keyword-to-topic tagging engine.

Uses a keyword frequency scoring approach to assign topic labels
to extracted questions. Keyword maps are derived from Cambridge
syllabuses and stored as JSON files.
"""

import json


def load_keyword_map(path):
    """
    Load the keyword-to-topic mapping JSON file.

    Expected format:
    {
        "9702": {
            "Kinematics": ["velocity", "acceleration", "displacement", ...],
            "Dynamics": ["force", "newton", "momentum", ...],
            ...
        }
    }

    Args:
        path: str, path to keyword_map.json.

    Returns:
        dict mapping subject_code → topic → list of keywords.
    """
    pass


def tag_question(question_text, subject_code, keyword_map):
    """
    Assign one or more topic labels to a question based on keyword frequency.

    Steps:
    1. Normalize the question text (lowercase, strip punctuation).
    2. For each topic in the keyword map for this subject, count how many
       of its keywords appear in the text.
    3. Rank topics by hit count; assign the top-scoring topic(s).
    4. If no keywords match, tag as "Uncategorized".

    Args:
        question_text: str, raw text of the question.
        subject_code: str, e.g. "9702".
        keyword_map: dict, loaded from load_keyword_map().

    Returns:
        list of str, topic labels (usually 1, sometimes 2 for cross-topic).
    """
    pass


def build_composite_keys(subject_code, topics, paper_type):
    """
    Construct composite index keys from subject, topics, and paper type.

    Example: subject="9702", topics=["Kinematics"], paper_type="P2"
             → ["9702_Kinematics_P2"]

    Args:
        subject_code: str.
        topics: list of str.
        paper_type: str.

    Returns:
        list of composite key strings.
    """
    pass
