"""
demo_runner.py — Interactive terminal walkthrough of the inverted index.

Designed for an in-class / live demonstration. The flow mirrors what a
student would do in real life:

    Level (O/A)  →  Subject  →  Topics  →  Years  →  Target marks  →  Worksheet

At every step we print exactly what's happening to the inverted index so
the audience SEES the data structure doing work — composite keys being
built, postings lists being fetched, set operations being applied.

Run it from the project root with:

    python demo_runner.py

Press Ctrl-C at any prompt to bail out.
"""

import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional

from config import (
    A_LEVEL_SUBJECTS, INDEX_PATH, KEYWORD_MAP_PATH,
    O_LEVEL_SUBJECTS, OUTPUT_DIR, SUBJECTS,
)
from inverted_index import InvertedIndex
from knapsack import select_questions
from pipeline import run_generate, run_index_build, run_ingestion


# ════════════════════════════════════════════════════════════════════
# UI helpers
# ════════════════════════════════════════════════════════════════════
RULE = "─" * 72
SECTION = "═" * 72


def banner(text: str) -> None:
    print()
    print(SECTION)
    print(f"  {text}")
    print(SECTION)


def section(text: str) -> None:
    print()
    print(RULE)
    print(f"  {text}")
    print(RULE)


def info(text: str) -> None:
    print(f"  ▸ {text}")


def kv(label: str, value: Any) -> None:
    print(f"    • {label:<22} {value}")


def show_keys(keys: List[str], index: InvertedIndex, max_show: int = 8) -> None:
    """Print the composite keys we're about to query, plus posting counts."""
    print(f"    composite keys ({len(keys)}):")
    for k in keys[:max_show]:
        n = len(index.query(k))
        print(f"        {k:<55s}  postings={n}")
    if len(keys) > max_show:
        print(f"        ... and {len(keys) - max_show} more")


def pause(prompt: str = "Press Enter to continue ") -> None:
    try:
        input(f"\n  {prompt}")
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)


def ask_choice(
    prompt: str,
    options: List[str],
    labeller: Optional[Callable[[str], str]] = None,
    allow_back: bool = False,
) -> Optional[str]:
    """
    Show numbered options and read a choice. Returns the selected value
    (or None if user typed 'b' for back when allow_back=True).
    """
    if not options:
        info("(no options available — returning)")
        return None
    print()
    for i, opt in enumerate(options, start=1):
        label = labeller(opt) if labeller else opt
        print(f"    [{i}]  {label}")
    if allow_back:
        print(f"    [b]  back")
    while True:
        try:
            raw = input(f"\n  {prompt} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if allow_back and raw == "b":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print(f"    invalid — pick a number 1–{len(options)}"
              + (" or 'b'" if allow_back else ""))


def ask_multi(
    prompt: str,
    options: List[str],
    min_one: bool = True,
) -> List[str]:
    """Multi-select. Accepts comma-separated indices or 'all'."""
    if not options:
        return []
    print()
    for i, opt in enumerate(options, start=1):
        print(f"    [{i:>2}]  {opt}")
    print("    [all] select every option")
    while True:
        try:
            raw = input(f"\n  {prompt} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if raw == "all":
            return list(options)
        try:
            picks = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            print("    invalid — use comma-separated numbers, e.g. 1,3,5")
            continue
        if not picks and min_one:
            print("    pick at least one")
            continue
        if any(p < 1 or p > len(options) for p in picks):
            print(f"    out of range — must be 1–{len(options)}")
            continue
        return [options[p - 1] for p in picks]


def ask_int(prompt: str, default: int, lo: int = 0, hi: int = 9999) -> int:
    while True:
        try:
            raw = input(f"  {prompt} [default {default}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
        if not raw:
            return default
        if raw.isdigit() and lo <= int(raw) <= hi:
            return int(raw)
        print(f"    please enter a number between {lo} and {hi}")


# ════════════════════════════════════════════════════════════════════
# Demo: load (or build) the index
# ════════════════════════════════════════════════════════════════════

def load_or_build_index() -> InvertedIndex:
    """
    Use the cached index if available; otherwise run the ingestion +
    build pipeline live so the audience sees it happen.
    """
    index = InvertedIndex(keyword_map_path=KEYWORD_MAP_PATH)

    if os.path.exists(INDEX_PATH):
        section("STAGE 0  ·  Loading cached inverted index")
        info(f"reading {INDEX_PATH}")
        t0 = time.perf_counter()
        index.load(INDEX_PATH)
        dt = (time.perf_counter() - t0) * 1000
        info(f"loaded in {dt:.1f} ms")
        s = index.stats()
        kv("keys",      s["n_keys"])
        kv("questions", s["n_questions"])
        kv("subjects",  s["n_subjects"])
        kv("avg postings/key", s["avg_postings"])
        return index

    section("STAGE 0  ·  No cached index — building from PDFs")
    info("running ingestion (this may take a moment)")
    questions = run_ingestion()
    index = run_index_build(questions)
    return index


# ════════════════════════════════════════════════════════════════════
# Demo: walk the user through a query
# ════════════════════════════════════════════════════════════════════

def pick_level() -> str:
    section("STAGE 1  ·  Pick a curriculum level")
    info("This filters which subject codes you can pick next.")
    info("O-Level = pure-syllabus papers; A-Level = AS / A2 split.")
    return ask_choice("level: ", ["O-Level", "A-Level"])


def pick_subject(index: InvertedIndex, level: str) -> Optional[str]:
    section("STAGE 2  ·  Pick a subject")
    available = index.list_subjects()
    info(f"index.list_subjects() → {available}")
    info("(this walks every key in main_index and peels off the subject prefix)")

    target_set = O_LEVEL_SUBJECTS if level == "O-Level" else A_LEVEL_SUBJECTS
    candidates = [s for s in available if s in target_set]

    if not candidates:
        info(f"no {level} subjects in the index — try the other level")
        return None

    chosen = ask_choice(
        "subject: ",
        candidates,
        labeller=lambda code: f"{SUBJECTS.get(code, code)}  ({code})",
        allow_back=True,
    )
    return chosen


def pick_topics(index: InvertedIndex, subject: str) -> List[str]:
    section("STAGE 3  ·  Pick topics")
    topics = index.list_topics(subject)

    info(f"index.list_topics({subject!r})  →  {len(topics)} topics found")
    info("(walks keys starting with '" + subject + "_' and pulls the topic out)")

    if not topics:
        info("(no topics — was anything indexed for this subject?)")
        return []

    return ask_multi("pick topics (comma-separated, e.g. 1,3,5): ", topics)


def pick_paper_type(index: InvertedIndex, subject: str) -> str:
    section("STAGE 4  ·  Pick a paper type")
    variants = index.list_paper_types(subject)
    info(f"index.list_paper_types({subject!r})  →  {variants}")

    options: List[str] = []
    if subject in A_LEVEL_SUBJECTS:
        options.append("AS  (papers 1, 2, 3 — first two years of A-Level)")
        options.append("A2  (papers 4, 5 — final year of A-Level)")
    options.append("ALL (every variant)")
    options.extend(variants)

    chosen = ask_choice("paper type: ", options)
    if chosen.startswith("AS"):
        return "AS"
    if chosen.startswith("A2"):
        return "A2"
    if chosen.startswith("ALL"):
        return "ALL"
    return chosen


def pick_year_range(index: InvertedIndex, subject: str) -> tuple:
    section("STAGE 5  ·  Pick a year range")
    years = index.list_years(subject)
    info(f"index.list_years({subject!r})  →  {years}")

    if not years:
        return 2000, 2030

    earliest, latest = years[0], years[-1]
    info(f"available range is {earliest}–{latest}")
    yfrom = ask_int("from year", earliest, 2000, 2030)
    yto   = ask_int("to year",   latest,   yfrom, 2030)
    return yfrom, yto


# ════════════════════════════════════════════════════════════════════
# The meat: show the index doing work
# ════════════════════════════════════════════════════════════════════

def run_search(
    index: InvertedIndex,
    subject: str,
    topics: List[str],
    paper_type: str,
    year_from: int,
    year_to: int,
) -> List[Dict[str, Any]]:
    """Show every step of the retrieval visibly."""
    section("STAGE 6  ·  Run the inverted index")

    # 6a — expand "AS"/"A2"/"ALL" to actual variants in this index
    variants = index.list_paper_types(subject)
    if paper_type == "ALL":
        chosen_variants = variants
    elif paper_type == "AS":
        chosen_variants = [v for v in variants if v[1:2] in {"1", "2", "3"}]
    elif paper_type == "A2":
        chosen_variants = [v for v in variants if v[1:2] in {"4", "5"}]
    else:
        chosen_variants = [paper_type]

    info(f"resolved paper type {paper_type!r} → {chosen_variants}")

    # 6b — composite keys
    keys = index.keys_for(subject, topics, chosen_variants)
    info(f"built {len(keys)} composite keys via topic × variant cross-product:")
    show_keys(keys, index)

    # 6c — query each key (this is the O(1) hash hit per key)
    print()
    info("query each key — direct dict lookup, O(1):")
    t0 = time.perf_counter()
    per_key_counts: List[int] = []
    for k in keys:
        per_key_counts.append(len(index.query(k)))
    dt_q = (time.perf_counter() - t0) * 1000
    kv("total time for all queries", f"{dt_q:.3f} ms")
    kv("total postings retrieved",   sum(per_key_counts))

    # 6d — union (set dedup)
    print()
    info("UNION — collapse postings lists across keys, deduplicating ids")
    t0 = time.perf_counter()
    candidate_ids = index.union(keys)
    dt_u = (time.perf_counter() - t0) * 1000
    kv("union time", f"{dt_u:.3f} ms")
    kv("unique candidate ids", len(candidate_ids))

    # 6e — fetch + year filter
    print()
    info("fetch_documents — resolve ids → full records, apply year filter")
    t0 = time.perf_counter()
    candidates = index.fetch_documents(candidate_ids, year_from, year_to)
    dt_f = (time.perf_counter() - t0) * 1000
    kv("fetch + filter time", f"{dt_f:.3f} ms")
    kv(f"records in [{year_from}, {year_to}]", len(candidates))

    # 6f — preview a few
    if candidates:
        print()
        info("first few candidates:")
        for c in candidates[:5]:
            topics_str = ", ".join(c.get("topic", []))[:36]
            print(f"        {c['id']:<35s}  "
                  f"y={c['year']}  "
                  f"marks={c['marks']:<3d}  "
                  f"topic={topics_str}")
        if len(candidates) > 5:
            print(f"        ... and {len(candidates) - 5} more")
    return candidates


def run_knapsack(
    candidates: List[Dict[str, Any]],
    target: int,
) -> tuple:
    section("STAGE 7  ·  0/1 Knapsack — hit the target marks")
    info(f"target = {target} marks   pool = {len(candidates)} questions")
    info("DP table size = target+1 = " + str(target + 1))
    info("(top-down inner loop = 0/1 semantics — every Q used at most once)")

    t0 = time.perf_counter()
    selected, actual = select_questions(candidates, target)
    dt = (time.perf_counter() - t0) * 1000

    kv("DP time",        f"{dt:.2f} ms")
    kv("questions chosen", len(selected))
    kv("marks achieved",   f"{actual}/{target}")
    if selected:
        print()
        info("selection:")
        for q in selected:
            print(f"        Q{q['id']:<35s}  "
                  f"y={q['year']}  marks={q['marks']:<3d}")
    return selected, actual


def maybe_generate(selected: List[Dict[str, Any]], subject: str,
                   paper_type: str, actual: int) -> None:
    if not selected:
        info("(nothing to compile — skipping worksheet generation)")
        return

    section("STAGE 8  ·  Compile the worksheet")
    print()
    try:
        choice = input("  generate the PDF worksheet now? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if choice and choice.startswith("n"):
        info("skipped — selection retained in memory only")
        return

    title = f"{subject}_{paper_type}_{actual}marks"
    path = run_generate(selected, title)
    info(f"open the worksheet: {os.path.abspath(path)}")


# ════════════════════════════════════════════════════════════════════
# Demonstration of the data structure operations themselves
# ════════════════════════════════════════════════════════════════════

def show_data_structure_demo(index: InvertedIndex) -> None:
    """
    Optional final stage: show INSERT, DELETE, INTERSECT operating on
    a tiny scratch index built right in front of the audience. This
    isolates the data structure from the surrounding pipeline so the
    audience can see exactly what each operation does.
    """
    section("BONUS  ·  Hands-on: the InvertedIndex operations in isolation")
    info("we build a tiny scratch index, then poke at it")

    scratch = InvertedIndex()

    fake_records = [
        {"id": "qA", "subject": "5054", "year": 2024, "marks": 5, "paper_type": "p11"},
        {"id": "qB", "subject": "5054", "year": 2024, "marks": 7, "paper_type": "p11"},
        {"id": "qC", "subject": "5054", "year": 2025, "marks": 6, "paper_type": "p21"},
    ]
    info("INSERT")
    scratch.insert("5054_Forces_p11",     fake_records[0])
    scratch.insert("5054_Forces_p11",     fake_records[1])
    scratch.insert("5054_Kinematics_p11", fake_records[0])    # qA tagged twice
    scratch.insert("5054_Energy_p21",     fake_records[2])
    print(f"        scratch.main_index    = {scratch.main_index}")
    print(f"        len(question_store)   = {len(scratch.question_store)}")

    print()
    info("SEARCH (query)")
    print(f"        scratch.query('5054_Forces_p11') = "
          f"{scratch.query('5054_Forces_p11')}")

    print()
    info("UNION  ·  questions in EITHER 'Forces' OR 'Energy'")
    u = scratch.union(["5054_Forces_p11", "5054_Energy_p21"])
    print(f"        union → {sorted(u)}")

    print()
    info("INTERSECT  ·  questions tagged BOTH 'Forces' AND 'Kinematics'")
    i = scratch.intersect(["5054_Forces_p11", "5054_Kinematics_p11"])
    print(f"        intersect → {i}    (qA was inserted under both)")

    print()
    info("DELETE  ·  remove 'qA' from one key only")
    scratch.delete("5054_Forces_p11", "qA")
    print(f"        after delete: '5054_Forces_p11' → "
          f"{scratch.query('5054_Forces_p11')}")
    print(f"                     '5054_Kinematics_p11' → "
          f"{scratch.query('5054_Kinematics_p11')}    "
          f"(qA still here)")

    print()
    info("REMOVE_QUESTION  ·  purge 'qA' everywhere")
    scratch.remove_question("qA")
    print(f"        scratch.main_index    = {scratch.main_index}")
    print(f"        question_store has qA?  "
          f"{'qA' in scratch.question_store}")

    print()
    info("Live index summary (the real one used above):")
    s = index.stats()
    for k, v in s.items():
        kv(k, v)


# ════════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════════

def main() -> None:
    banner("CS201  ·  Inverted Index Past-Paper Worksheet Generator  ·  Demo")

    try:
        index = load_or_build_index()

        while True:
            level = pick_level()

            subject = pick_subject(index, level)
            if subject is None:
                continue

            topics = pick_topics(index, subject)
            if not topics:
                info("no topics selected — restarting")
                continue

            paper_type = pick_paper_type(index, subject)
            yfrom, yto = pick_year_range(index, subject)

            section("REVIEW  ·  what you've selected")
            kv("level",        level)
            kv("subject",      f"{SUBJECTS.get(subject)}  ({subject})")
            kv("topics",       ", ".join(topics))
            kv("paper type",   paper_type)
            kv("year range",   f"{yfrom}–{yto}")
            target = ask_int("target marks", 30, 5, 200)
            kv("target marks", target)

            candidates = run_search(index, subject, topics,
                                    paper_type, yfrom, yto)

            if not candidates:
                info("no questions found — relax your filters")
            else:
                selected, actual = run_knapsack(candidates, target)
                maybe_generate(selected, subject, paper_type, actual)

            print()
            try:
                again = input("  another query? [y/N]  ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                again = "n"
            if not again.startswith("y"):
                break

        try:
            extra = input("\n  show the data-structure operations demo? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            extra = "n"
        if extra.startswith("y"):
            show_data_structure_demo(index)

        # ── Hand off to the web UI ────────────────────────────────────────
        try:
            ui = input("\n  launch the web UI for the same demo? [y/N]  ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            ui = "n"
        if ui.startswith("y"):
            launch_web_ui()

    except KeyboardInterrupt:
        print("\n  interrupted — bye")
        sys.exit(0)

    banner("End of demo")


def launch_web_ui() -> None:
    """
    Start the Flask app in a subprocess and open the browser.
    The UI uses the SAME index this demo just walked through —
    so the dropdowns will show exactly the same options.
    """
    import subprocess
    import webbrowser
    import time

    section("WEB UI  ·  launching Flask on http://127.0.0.1:5000")
    info("the UI dropdowns are populated from index.list_subjects(),")
    info("index.list_topics(), index.list_paper_types(), index.list_years()")
    info("— the same methods the terminal demo just used.")
    info("")
    info("Ctrl-C in this terminal to stop the server when you're done.")

    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)) or ".",
    )
    time.sleep(1.5)  # give Flask a moment to bind the port
    try:
        webbrowser.open("http://127.0.0.1:5000")
    except Exception:
        pass

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
