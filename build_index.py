import json
import os

from inverted_index import InvertedIndex
from pdf_parser import parse_paper
from topic_mapper import build_composite_keys, load_keyword_map, tag_question


def build_master_index(data_dir, keyword_map_path):
    # 1. Initialize
    index = InvertedIndex()
    keyword_map = load_keyword_map(keyword_map_path)
    subject_code = "5054"  # Hardcoded based on project context

    # 2. Ingestion
    for file_name in os.listdir(data_dir):
        if file_name.startswith("physics_paper") and file_name.endswith(".pdf"):
            pdf_path = os.path.join(data_dir, file_name)

            # 3. Clean up the paper_type mapping
            # physics_paper1_part1.pdf -> paper1_part1
            name_without_ext = file_name.replace(".pdf", "")
            parts = name_without_ext.split("_")
            # parts will be ['physics', 'paper1', 'part1']
            paper_type = parts[1] + "_" + parts[2]

            year = 2025

            print(f"Ingesting {file_name} as {paper_type}...")
            questions = parse_paper(pdf_path, subject_code, paper_type, year)

            for q in questions:
                # 4. Categorize
                topics = tag_question(q["text"], subject_code, keyword_map)

                # 5. Build Keys & Insert
                keys = build_composite_keys(subject_code, topics, paper_type)
                for key in keys:
                    index.insert(key, q)

    # 6. Persist
    index_path = "physics_master_index.json"
    index.save(index_path)
    print(f"Master index saved to {index_path}")
    return index


if __name__ == "__main__":
    build_master_index("data/papers", "data/keywords/keyword_map.json")
