"""
app.py — Flask web application entry point.

Provides:
  - GET  /           — worksheet generation form (topics filtered by subject)
  - POST /generate   — run the pipeline and stream back the PDF
  - GET  /rebuild    — wipe cache and force re-ingestion (for debugging)
"""
import json
import os
from flask import Flask, request, send_file, render_template, redirect, url_for

from config import SUBJECTS, PAPER_TYPES, KEYWORD_MAP_PATH, INDEX_PATH, QUESTION_DB_PATH
from pipeline import run_full_pipeline

app = Flask(__name__)


@app.route("/")
def index():
    """Render the form with topic chips grouped per subject."""
    with open(KEYWORD_MAP_PATH, "r", encoding="utf-8") as f:
        keyword_map = json.load(f)
    topic_map = {code: list(topics.keys()) for code, topics in keyword_map.items()}

    return render_template(
        "index.html",
        subjects=SUBJECTS,
        topic_map=topic_map,
        paper_types=PAPER_TYPES,
    )


@app.route("/generate", methods=["POST"])
def generate():
    """Run the pipeline and send the generated PDF as a download."""
    subject_code = request.form.get("subject")
    selected_topics = request.form.getlist("topics")
    paper_type = request.form.get("paper_type")
    year_from = int(request.form.get("year_from", 2018))
    year_to = int(request.form.get("year_to", 2025))
    target_marks = int(request.form.get("target_marks", 30))

    if not selected_topics:
        return (
            "<p style='font-family:sans-serif'>Please select at least one topic. "
            "<a href='/'>Back</a></p>",
            400,
        )

    try:
        pdf_path = run_full_pipeline(
            subject_code, selected_topics, paper_type,
            year_from, year_to, target_marks,
        )
    except FileNotFoundError as e:
        return (
            f"<p style='font-family:sans-serif'>Error: {e}<br>"
            "Make sure you've added past paper PDFs to data/papers/&lt;subject&gt;/. "
            "<a href='/'>Back</a></p>",
            500,
        )

    return send_file(pdf_path, as_attachment=True,
                     download_name=os.path.basename(pdf_path))


@app.route("/rebuild")
def rebuild():
    """Delete cached index + question DB so the next /generate re-ingests."""
    for p in (INDEX_PATH, QUESTION_DB_PATH):
        if os.path.exists(p):
            os.remove(p)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
