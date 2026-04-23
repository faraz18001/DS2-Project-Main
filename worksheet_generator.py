# """
# worksheet_generator.py — A4 PDF worksheet builder.

# Renders selected questions onto fresh A4 pages with:
#   - header: title, date, total marks, name/date fields
#   - bold "Q{n}." label
#   - question text (cleaned of markdown artefacts)
#   - embedded diagram images (scaled to fit width, preserves aspect ratio)
#   - ruled answer space, height proportional to marks
#   - grey italic source footer: [year session P{n} — topics — marks marks]
# """
# import os
# import re
# from datetime import datetime

# import fitz  # PyMuPDF

# from config import (
#     PAGE_WIDTH, PAGE_HEIGHT,
#     MARGIN_TOP, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT,
# )


# # ── Public entry point ───────────────────────────────────────────────────
# def generate_worksheet(selected_questions, output_path, title="Worksheet"):
#     """Build the worksheet PDF. Returns the output path."""
#     doc = fitz.open()  # blank PDF
#     page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

#     total_marks = sum(q.get("marks", 0) for q in selected_questions)
#     y_cursor = _stamp_header(page, title, total_marks)

#     if not selected_questions:
#         page.insert_text(
#             (MARGIN_LEFT, y_cursor + 40),
#             "No questions matched your filters.",
#             fontname="helv", fontsize=12, color=(0.55, 0.1, 0.1),
#         )
#     else:
#         for i, q in enumerate(selected_questions, start=1):
#             page, y_cursor = _stamp_question(doc, page, y_cursor, q, i)

#     os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
#     doc.save(output_path)
#     doc.close()
#     return output_path


# # ── Header ───────────────────────────────────────────────────────────────
# def _stamp_header(page, title, total_marks):
#     date_str = datetime.now().strftime("%d %B %Y")

#     page.insert_text(
#         (MARGIN_LEFT, MARGIN_TOP),
#         title[:60],
#         fontname="helv", fontsize=17,
#     )
#     page.insert_text(
#         (MARGIN_LEFT, MARGIN_TOP + 22),
#         f"{date_str}   |   Total marks: {total_marks}",
#         fontname="helv", fontsize=10, color=(0.4, 0.4, 0.4),
#     )

#     rule_y = MARGIN_TOP + 36
#     page.draw_line(
#         (MARGIN_LEFT, rule_y), (PAGE_WIDTH - MARGIN_RIGHT, rule_y),
#         width=0.75,
#     )

#     info_y = rule_y + 18
#     page.insert_text((MARGIN_LEFT, info_y),
#                      "Name: ____________________________________",
#                      fontname="helv", fontsize=10)
#     page.insert_text((MARGIN_LEFT + 300, info_y),
#                      "Date: _______________",
#                      fontname="helv", fontsize=10)

#     return info_y + 24


# # ── Per-question stamping ─────────────────────────────────────────────────
# def _stamp_question(doc, page, y_cursor, question, q_num):
#     content_w = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

#     text = question.get("text", "").strip()
#     images = question.get("images", [])
#     marks = question.get("marks", 0)

#     # Strip inline markdown image refs — images are rendered separately
#     clean_text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
#     # Strip basic markdown emphasis markers
#     clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)
#     clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)
#     clean_text = re.sub(r'_{2,}', '', clean_text)
#     # Collapse excessive blank lines
#     clean_text = re.sub(r'\n{3,}', '\n\n', clean_text).strip()

#     # If near the bottom of the page, start fresh
#     if y_cursor > PAGE_HEIGHT - MARGIN_BOTTOM - 120:
#         page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
#         y_cursor = MARGIN_TOP

#     # Question label
#     page.insert_text((MARGIN_LEFT, y_cursor),
#                      f"Q{q_num}.",
#                      fontname="helv", fontsize=12)
#     y_cursor += 18

#     # Question text — estimate required height and break page if needed
#     est_height = _estimate_text_height(clean_text, content_w, fontsize=10)
#     available = PAGE_HEIGHT - MARGIN_BOTTOM - y_cursor

#     if est_height > available:
#         page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
#         y_cursor = MARGIN_TOP
#         available = PAGE_HEIGHT - MARGIN_BOTTOM - y_cursor

#     # Give a generous rect — PyMuPDF just ignores unused space.
#     text_rect = fitz.Rect(
#         MARGIN_LEFT, y_cursor,
#         PAGE_WIDTH - MARGIN_RIGHT, y_cursor + min(est_height + 40, available),
#     )
#     # insert_textbox returns height used (positive) or negative on overflow.
#     leftover = page.insert_textbox(
#         text_rect, clean_text,
#         fontname="helv", fontsize=10, align=0,
#     )
#     if leftover < 0:
#         # Text overflowed — re-try on a fresh page with max height
#         page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
#         y_cursor = MARGIN_TOP
#         text_rect = fitz.Rect(
#             MARGIN_LEFT, y_cursor,
#             PAGE_WIDTH - MARGIN_RIGHT,
#             PAGE_HEIGHT - MARGIN_BOTTOM,
#         )
#         page.insert_textbox(text_rect, clean_text,
#                             fontname="helv", fontsize=10, align=0)
#     y_cursor += est_height + 8

#     # Images — scale each to at most 75% of content width, preserve aspect
#     for img_path in images:
#         if not os.path.isfile(img_path):
#             continue
#         iw, ih = _image_size(img_path)
#         if iw is None:
#             continue

#         max_w = content_w * 0.75
#         max_h = 260
#         scale = min(max_w / iw, max_h / ih, 1.0)
#         dw, dh = iw * scale, ih * scale

#         if y_cursor + dh > PAGE_HEIGHT - MARGIN_BOTTOM - 60:
#             page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
#             y_cursor = MARGIN_TOP

#         rect = fitz.Rect(MARGIN_LEFT, y_cursor,
#                          MARGIN_LEFT + dw, y_cursor + dh)
#         try:
#             page.insert_image(rect, filename=img_path)
#             y_cursor += dh + 8
#         except Exception:
#             pass    # unreadable image - skip

#     # Ruled answer space
#     ans_h = _calculate_answer_space(marks)
#     if y_cursor + ans_h > PAGE_HEIGHT - MARGIN_BOTTOM - 40:
#         page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
#         y_cursor = MARGIN_TOP

#     line_spacing = 22
#     y = y_cursor + line_spacing
#     end_y = y_cursor + ans_h
#     while y < end_y:
#         page.draw_line(
#             (MARGIN_LEFT, y), (PAGE_WIDTH - MARGIN_RIGHT, y),
#             width=0.3, color=(0.78, 0.78, 0.78),
#         )
#         y += line_spacing
#     y_cursor += ans_h + 4

#     # Source footer
#     topics_str = ", ".join(question.get("topics", ["?"]))
#     paper_code = question.get("paper_code", question.get("paper_type", "?"))
#     session = question.get("session", "")
#     footer = (f"[{question.get('year', '?')} "
#               f"{session}{paper_code} — "
#               f"{topics_str} — {marks} marks]")

#     if y_cursor > PAGE_HEIGHT - MARGIN_BOTTOM - 14:
#         page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
#         y_cursor = MARGIN_TOP

#     page.insert_text((MARGIN_LEFT, y_cursor), footer,
#                      fontname="helv", fontsize=8,
#                      color=(0.45, 0.45, 0.45))
#     y_cursor += 22

#     return page, y_cursor


# # ── Helpers ──────────────────────────────────────────────────────────────
# def _calculate_answer_space(marks):
#     """~30 points per mark, clamped between 60 and 400 points."""
#     if marks <= 0:
#         return 60
#     return max(60, min(marks * 30, 400))


# def _estimate_text_height(text, width, fontsize=10):
#     """
#     Rough height estimate for text wrapped at `width` points.
#     Tuned to over-estimate slightly — undershooting causes truncation.
#     """
#     if not text:
#         return 24
#     # Approx chars per line at this point size for Helvetica
#     chars_per_line = max(40, int(width / (fontsize * 0.52)))
#     lines = 0
#     for raw in text.split("\n"):
#         if not raw.strip():
#             lines += 0.6
#             continue
#         lines += max(1, -(-len(raw) // chars_per_line))  # ceil division
#     return lines * (fontsize * 1.4)


# def _image_size(image_path):
#     """Return (width, height) using Pillow; (None, None) if unreadable."""
#     try:
#         from PIL import Image
#         with Image.open(image_path) as im:
#             return im.size
#     except Exception:
#         return None, None

"""
worksheet_generator.py — Stable A4 PDF worksheet builder (FINAL FIXED VERSION)

Fixes:
- Image rendering issues resolved (path normalization + error logging)
- No silent failures in image insertion
- Stable pagination and text rendering
- PyMuPDF-safe workflow
"""

import os
import re
from datetime import datetime
import fitz  # PyMuPDF

from config import (
    PAGE_WIDTH, PAGE_HEIGHT,
    MARGIN_TOP, MARGIN_BOTTOM, MARGIN_LEFT, MARGIN_RIGHT,
)

LINE_HEIGHT = 14
SECTION_GAP = 10


# ─────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────
def generate_worksheet(selected_questions, output_path, title="Worksheet"):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)

    total_marks = sum(q.get("marks", 0) for q in selected_questions)

    y_cursor = _stamp_header(page, title, total_marks)

    if not selected_questions:
        page.insert_text(
            (MARGIN_LEFT, y_cursor + 40),
            "No questions matched your filters.",
            fontname="helv",
            fontsize=12,
            color=(0.5, 0.1, 0.1),
        )
    else:
        for i, q in enumerate(selected_questions, start=1):
            page, y_cursor = _stamp_question(page, doc, y_cursor, q, i)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()

    return output_path


# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
def _stamp_header(page, title, total_marks):
    date_str = datetime.now().strftime("%d %B %Y")

    page.insert_text(
        (MARGIN_LEFT, MARGIN_TOP),
        title[:60],
        fontname="helv",
        fontsize=17
    )

    page.insert_text(
        (MARGIN_LEFT, MARGIN_TOP + 22),
        f"{date_str} | Total marks: {total_marks}",
        fontname="helv",
        fontsize=10,
        color=(0.4, 0.4, 0.4)
    )

    y = MARGIN_TOP + 45

    page.draw_line(
        (MARGIN_LEFT, y),
        (PAGE_WIDTH - MARGIN_RIGHT, y),
        width=0.8
    )

    y += 20

    page.insert_text(
        (MARGIN_LEFT, y),
        "Name: ____________________________",
        fontname="helv",
        fontsize=10
    )

    page.insert_text(
        (MARGIN_LEFT + 300, y),
        "Date: ____________",
        fontname="helv",
        fontsize=10
    )

    return y + 30


# ─────────────────────────────────────────────────────────────
# QUESTION RENDERING
# ─────────────────────────────────────────────────────────────
def _stamp_question(page, doc, y_cursor, question, q_num):

    text = question.get("text", "").strip()
    marks = question.get("marks", 0)
    images = question.get("images", [])

    # clean markdown
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    # ── PAGE BREAK CHECK ──
    if y_cursor > PAGE_HEIGHT - MARGIN_BOTTOM - 150:
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        y_cursor = MARGIN_TOP

    # ── QUESTION LABEL ──
    page.insert_text(
        (MARGIN_LEFT, y_cursor),
        f"Q{q_num}.",
        fontname="helv",
        fontsize=12
    )

    y_cursor += 18

    # ── TEXT (SAFE LINE WRAPPING) ──
    max_chars = 95
    words = text.split()
    line = ""

    for word in words:
        if len(line + word) < max_chars:
            line += word + " "
        else:
            page.insert_text(
                (MARGIN_LEFT, y_cursor),
                line.strip(),
                fontname="helv",
                fontsize=10
            )
            y_cursor += LINE_HEIGHT
            line = word + " "

            if y_cursor > PAGE_HEIGHT - MARGIN_BOTTOM - 80:
                page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                y_cursor = MARGIN_TOP

    if line:
        page.insert_text(
            (MARGIN_LEFT, y_cursor),
            line.strip(),
            fontname="helv",
            fontsize=10
        )
        y_cursor += LINE_HEIGHT

    y_cursor += SECTION_GAP

    # ── IMAGES (FIXED + DEBUG ENABLED) ──
    for img_path in images:

        img_path = os.path.normpath(img_path)

        if not os.path.exists(img_path):
            print("[MISSING IMAGE]", img_path)
            continue

        try:
            pix = fitz.Pixmap(img_path)
        except Exception as e:
            print("[PIXMAP LOAD FAILED]", img_path, e)
            continue

        if pix.width == 0 or pix.height == 0:
            print("[INVALID IMAGE]", img_path)
            continue

        max_w = (PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT) * 0.75
        max_h = 260

        scale = min(max_w / pix.width, max_h / pix.height, 1.0)

        w = pix.width * scale
        h = pix.height * scale

        # page break safety
        if y_cursor + h > PAGE_HEIGHT - MARGIN_BOTTOM:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y_cursor = MARGIN_TOP

        rect = fitz.Rect(
            MARGIN_LEFT,
            y_cursor,
            MARGIN_LEFT + w,
            y_cursor + h
        )

        page.insert_image(rect, pixmap=pix)

        y_cursor += h + 10

        pix = None  # free memory

    # ── ANSWER SPACE ──
    ans_lines = max(3, marks * 2)

    for _ in range(ans_lines):
        if y_cursor > PAGE_HEIGHT - MARGIN_BOTTOM - 30:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y_cursor = MARGIN_TOP

        page.draw_line(
            (MARGIN_LEFT, y_cursor),
            (PAGE_WIDTH - MARGIN_RIGHT, y_cursor),
            width=0.3,
            color=(0.75, 0.75, 0.75)
        )
        y_cursor += LINE_HEIGHT

    y_cursor += SECTION_GAP

    # ── FOOTER ──
    topics = ", ".join(question.get("topics", ["?"]))
    footer = f"[{question.get('year','?')} {topics} — {marks} marks]"

    if y_cursor > PAGE_HEIGHT - MARGIN_BOTTOM - 20:
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        y_cursor = MARGIN_TOP

    page.insert_text(
        (MARGIN_LEFT, y_cursor),
        footer,
        fontname="helv",
        fontsize=8,
        color=(0.5, 0.5, 0.5)
    )

    y_cursor += 25

    return page, y_cursor


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def _image_size(image_path):
    try:
        from PIL import Image
        with Image.open(image_path) as im:
            return im.size
    except Exception:
        return None, None