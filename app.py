"""
app.py — Flask web app that mirrors the terminal demo flow.

"""
import os
from flask import Flask, request, send_file, render_template, jsonify, redirect, url_for

from config import (
    SUBJECTS, A_LEVEL_SUBJECTS, O_LEVEL_SUBJECTS,
    INDEX_PATH, KEYWORD_MAP_PATH, QUESTION_DB_PATH,
)
from inverted_index import InvertedIndex
from pipeline import run_full_pipeline, run_ingestion, run_index_build

app = Flask(__name__)


def _load_index() -> InvertedIndex:
    """Load the cached index, or build it on the fly if missing."""
    idx = InvertedIndex(keyword_map_path=KEYWORD_MAP_PATH)
    if os.path.exists(INDEX_PATH):
        idx.load(INDEX_PATH)
    else:
        questions = run_ingestion()
        idx = run_index_build(questions)
    return idx


@app.route("/")
def index():
    """
    Render the form. We pre-compute a JSON-friendly map of the live index
    so the JS layer can populate dropdowns based on subject selection
    without round-tripping to the server for every change.
    """
    idx = _load_index()

    # Build a single payload describing what's in the data structure
    # right now. Topics, paper types, and years all come from the index —
    # these are the live "list_*" methods you saw in the terminal demo.
    subjects_payload = []
    for code in idx.list_subjects():
        if code not in SUBJECTS:
            continue
        subjects_payload.append({
            "code":        code,
            "name":        SUBJECTS[code],
            "level":       "A-Level" if code in A_LEVEL_SUBJECTS else "O-Level",
            "topics":      idx.list_topics(code),
            "paper_types": idx.list_paper_types(code),
            "years":       idx.list_years(code),
        })

    return render_template(
        "index.html",
        subjects=subjects_payload,
        index_stats=idx.stats(),
    )


@app.route("/generate", methods=["POST"])
def generate():
    """Run the same full pipeline used by the terminal demo."""
    subject_code    = request.form.get("subject")
    selected_topics = request.form.getlist("topics")
    paper_type      = request.form.get("paper_type")
    year_from       = int(request.form.get("year_from", 2018))
    year_to         = int(request.form.get("year_to", 2025))
    target_marks    = int(request.form.get("target_marks", 30))

    if not selected_topics:
        return ("<p style='font-family:sans-serif'>Please select at least one topic. "
                "<a href='/'>Back</a></p>", 400)

    try:
        pdf_path = run_full_pipeline(
            subject_code, selected_topics, paper_type,
            year_from, year_to, target_marks,
        )
    except FileNotFoundError as e:
        return (f"<p style='font-family:sans-serif'>Error: {e}<br>"
                "<a href='/'>Back</a></p>", 500)

    return send_file(pdf_path, as_attachment=True,
                     download_name=os.path.basename(pdf_path))


@app.route("/rebuild")
def rebuild():
    """Wipe cached index so the next request re-ingests."""
    for p in (INDEX_PATH, QUESTION_DB_PATH):
        if os.path.exists(p):
            os.remove(p)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False, port=5000)