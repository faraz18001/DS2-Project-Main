"""
app.py — Flask web application entry point.

Provides simplified routes for the UI: subject selection,
worksheet generation, and direct PDF download.
"""

from flask import Flask, request, send_file, render_template
from config import SUBJECTS
from pipeline import run_full_pipeline

app = Flask(__name__)

# ── Page Routes ──────────────────────────────────────────────────

@app.route("/")
def index():
    """
    Main page: Show the worksheet generation form.
    Pass list of subjects from config to the template.
    """
    return render_template("index.html", subjects=SUBJECTS)


@app.route("/generate", methods=["POST"])
def generate():
    """
    Handle the worksheet generation form submission.
    
    1. Extract form data (subject, topics, marks, etc.)
    2. Run the pipeline to find questions and build PDF.
    3. Return the PDF file directly to the user's browser.
    """
    # Get values from standard HTML <form>
    subject_code = request.form.get("subject")
    selected_topics = request.form.getlist("topics")
    paper_type = request.form.get("paper_type")
    year_from = int(request.form.get("year_from", 2010))
    year_to = int(request.form.get("year_to", 2024))
    target_marks = int(request.form.get("target_marks", 20))

    # Run the generator logic
    pdf_path = run_full_pipeline(
        subject_code, 
        selected_topics, 
        paper_type, 
        year_from, 
        year_to, 
        target_marks
    )

    # Send the finished PDF to the user
    return send_file(pdf_path, as_attachment=True)


# ── Entry Point ──────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)
