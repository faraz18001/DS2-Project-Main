"""
demo_runner.py — Intern Demo Script

Demonstrates all InvertedIndex operations on real parsed 5054
O-Level Physics past paper data (Winter 2025, Papers 21 & 22).

Run:
    python demo_runner.py
"""

import os
import time
from pdf_parser import parse_paper
from topic_mapper import load_keyword_map, tag_question, build_composite_keys
from inverted_index import InvertedIndex
from config import KEYWORD_MAP_PATH, INDEX_PATH

# ── Formatting helpers ───────────────────────────────────────────────────────

W = 62  # banner width

def banner(title):
    print("\n" + "═" * W)
    pad = (W - len(title) - 2) // 2
    print("║" + " " * pad + title + " " * (W - pad - len(title) - 2) + "║")
    print("═" * W)

def section(title):
    print(f"\n{'─' * W}")
    print(f"  {title}")
    print(f"{'─' * W}")

def ok(msg):
    print(f"  ✓  {msg}")

def info(msg):
    print(f"  →  {msg}")

def bar_chart(label, count, total, width=20):
    filled = round((count / total) * width) if total else 0
    bar = "█" * filled + "░" * (width - filled)
    print(f"    {label:<22} {bar}  {count}")


# ── Stage 1: Parse PDFs ──────────────────────────────────────────────────────

def stage_parse(pdfs, subject_code):
    banner("STAGE 1 — PDF Parsing")
    questions = []
    for pdf_path, paper_type, year in pdfs:
        t0 = time.perf_counter()
        qs = parse_paper(pdf_path, subject_code, paper_type, year)
        elapsed = (time.perf_counter() - t0) * 1000
        info(f"Parsed {os.path.basename(pdf_path):<30} → {len(qs):>2} questions  ({elapsed:.0f} ms)")
        questions.extend(qs)
    print()
    ok(f"Total questions extracted: {len(questions)}")
    return questions


# ── Stage 2: Topic Tagging ───────────────────────────────────────────────────

def stage_tag(questions, subject_code, kw_map):
    banner("STAGE 2 — Topic Tagging  (keyword frequency scoring)")
    topic_counts = {}
    for q in questions:
        topics = tag_question(q["text"], subject_code, kw_map)
        q["topics"] = topics
        q["topic"]  = topics[0]
        for t in topics:
            topic_counts[t] = topic_counts.get(t, 0) + 1

    ok(f"Tagged {len(questions)} questions across {len(topic_counts)} topics\n")
    total = sum(topic_counts.values())
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
        bar_chart(topic, count, total)
    return questions, topic_counts


# ── Stage 3: Build Index ─────────────────────────────────────────────────────

def stage_build_index(questions):
    banner("STAGE 3 — Building Inverted Index")
    idx = InvertedIndex()
    for q in questions:
        keys = build_composite_keys(q["subject"], q["topics"], q["paper_type"])
        for key in keys:
            idx.insert(key, q)

    ok(f"Inserted {len(questions)} records")
    ok(f"Composite keys generated: {len(idx.main_index)}")
    print()
    info("Sample keys:")
    for key in sorted(idx.main_index.keys())[:6]:
        print(f"    {key:<40} ({len(idx.main_index[key])} posting{'s' if len(idx.main_index[key]) > 1 else ''})")
    return idx


# ── Stage 4: Demonstrate Operations ─────────────────────────────────────────

def stage_demo_operations(idx, subject_code, paper_type):
    banner("STAGE 4 — Inverted Index Operations")

    # ── 4a. query() ─────────────────────────────────────────────
    section(f"4a.  query(\"{subject_code}_Electricity_{paper_type}\")")
    info("Use case: fetch all Electricity questions from one paper type.")
    results = idx.query(f"{subject_code}_Electricity_{paper_type}")
    print()
    for r in results:
        print(f"    {r['id']:<35}  {r['marks']:>2} marks")
    ok(f"Returned {len(results)} record(s)   — O(1) lookup")

    # ── 4b. union() ─────────────────────────────────────────────
    keys_union = [
        f"{subject_code}_Electricity_{paper_type}",
        f"{subject_code}_Forces_{paper_type}",
    ]
    section(f"4b.  union({keys_union})")
    info("Use case: retrieve Electricity OR Forces questions (either topic).")
    results_union = idx.union(keys_union)
    print()
    for r in sorted(results_union, key=lambda x: x["id"]):
        print(f"    {r['id']:<35}  {r['marks']:>2} marks  [{r['topic']}]")
    ok(f"Returned {len(results_union)} record(s) (deduplicated)   — O(k + n)")

    # ── 4c. intersect() ─────────────────────────────────────────
    keys_intersect = [
        f"{subject_code}_Forces_{paper_type}",
        f"{subject_code}_Energy_{paper_type}",
    ]
    section(f"4c.  intersect({keys_intersect})")
    info("Use case: find questions tagged with BOTH Forces AND Energy.")
    results_intersect = idx.intersect(keys_intersect)
    print()
    if results_intersect:
        for r in results_intersect:
            print(f"    {r['id']:<35}  {r['marks']:>2} marks  [{r['topic']}]")
    else:
        print("    (no questions shared across both keys)")
    ok(f"Returned {len(results_intersect)} record(s)   — O(k × n) via set intersection")

    # ── 4d. filter_by_year() ────────────────────────────────────
    section(f"4d.  filter_by_year(results, year_from=2024, year_to=2025)")
    info("Use case: narrow a result set to a specific year range.")
    all_elec = idx.union([
        f"{subject_code}_Electricity_qp_21",
        f"{subject_code}_Electricity_qp_22",
    ])
    filtered = idx.filter_by_year(all_elec, 2024, 2025)
    print()
    for r in sorted(filtered, key=lambda x: x["id"]):
        print(f"    {r['id']:<35}  year={r['year']}  {r['marks']:>2} marks")
    ok(f"Filtered {len(all_elec)} → {len(filtered)} record(s)   — O(n) linear scan")

    # ── 4e. save() / load() ─────────────────────────────────────
    section("4e.  save(\"data/index.json\")  +  load(\"data/index.json\")")
    info("Use case: persist the index to disk; reload without re-parsing PDFs.")

    idx.save(INDEX_PATH)
    size_kb = os.path.getsize(INDEX_PATH) / 1024
    ok(f"Saved  →  {INDEX_PATH}  ({size_kb:.1f} KB)")

    idx2 = InvertedIndex()
    idx2.load(INDEX_PATH)
    assert idx2.main_index == idx.main_index, "main_index mismatch after load!"
    assert idx2.question_store == idx.question_store, "question_store mismatch!"
    ok(f"Loaded →  {len(idx2.main_index)} keys, {len(idx2.question_store)} records — integrity verified ✓")


# ── Stage 5: Performance Benchmark ──────────────────────────────────────────

def stage_benchmark(idx, subject_code, paper_type):
    banner("STAGE 5 — Performance Benchmark")
    info("Comparing InvertedIndex O(1) query vs. naive O(n) linear scan")
    info(f"Dataset: {len(idx.question_store)} question records\n")

    target_topic = "Electricity"
    target_key   = f"{subject_code}_{target_topic}_{paper_type}"

    # Flat list for the naive scan
    all_records = list(idx.question_store.values())

    RUNS = 10_000

    # ── Inverted index lookup
    t0 = time.perf_counter()
    for _ in range(RUNS):
        _ = idx.query(target_key)
    idx_time = (time.perf_counter() - t0) / RUNS * 1_000_000   # µs per call

    # ── Naive linear scan
    t0 = time.perf_counter()
    for _ in range(RUNS):
        _ = [r for r in all_records
             if r["subject"] == subject_code
             and r["topic"] == target_topic
             and r["paper_type"] == paper_type]
    naive_time = (time.perf_counter() - t0) / RUNS * 1_000_000  # µs per call

    speedup = naive_time / idx_time if idx_time > 0 else float("inf")

    print(f"    {'Method':<30} {'Time per query':>16}")
    print(f"    {'─'*30} {'─'*16}")
    print(f"    {'InvertedIndex.query()  O(1)':<30} {idx_time:>13.2f} µs")
    print(f"    {'Naive linear scan      O(n)':<30} {naive_time:>13.2f} µs")
    print()
    ok(f"Inverted index is  {speedup:.0f}×  faster  ({RUNS:,} runs averaged)")
    # for terminal display 
def print_index_tree(idx):
    banner("INVERTED INDEX — TREE STRUCTURE")

    if not idx.main_index:
        print("  (empty index)")
        return

    for key in sorted(idx.main_index.keys()):
        print(f"\n{key}")
        postings = idx.main_index[key]

        for i, q_id in enumerate(postings):
            record = idx.question_store[q_id]

            connector = "├──"
            if i == len(postings) - 1:
                connector = "└──"

            print(f"  {connector} {q_id}  ({record['marks']} marks)")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    SUBJECT   = "5054"
    DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
    DEMO_PDFS = [
        (os.path.join(DATA_DIR, "5054_w25_qp_21.pdf"), "qp_21", 2025),
        (os.path.join(DATA_DIR, "5054_w25_qp_22.pdf"), "qp_22", 2025),
    ]
    DEMO_PAPER_TYPE = "qp_21"   # used for single-paper demos

    print()
    banner(" DS2 PROJECT DEMO — Inverted Index + Topic Mapper ")
    print(f"  Subject : {SUBJECT} — O-Level Physics")
    print(f"  Papers  : {', '.join(os.path.basename(p[0]) for p in DEMO_PDFS)}")
    print(f"  Dataset : Winter 2025")

    # Load keyword map
    kw_map = load_keyword_map(KEYWORD_MAP_PATH)

    questions            = stage_parse(DEMO_PDFS, SUBJECT)
    questions, _         = stage_tag(questions, SUBJECT, kw_map)
    idx                  = stage_build_index(questions)
    print_index_tree(idx) # terminal 
    stage_demo_operations(idx, SUBJECT, DEMO_PAPER_TYPE)
    stage_benchmark(idx, SUBJECT, DEMO_PAPER_TYPE)

    banner("  DEMO COMPLETE ✓  ")
    print()


if __name__ == "__main__":
    main()
