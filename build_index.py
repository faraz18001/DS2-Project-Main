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
        if file_name.endswith(".pdf") and "_qp_" in file_name:
            pdf_path = os.path.join(data_dir, file_name)

            print(f"Ingesting {file_name}...")
            # We don't need to pass subject/year anymore, it figures it out!
            questions = parse_paper(pdf_path)

            for q in questions:
                # 4. Categorize (Using the text we secretly extracted)
                topics = tag_question(q["text"], q["subject"], keyword_map)

                # 5. Build Keys & Insert
                # Generates keys like: "9702_w25_p13_Kinematics"
                keys = build_composite_keys(q["subject"], topics, q["paper_type"])
                for key in keys:
                    index.insert(key, q)

    # 6. Persist
    index_path = "data/index/physics_master_index.json"
    index.save(index_path)
    print(f"Master index saved to {index_path}")
    return index


if __name__ == "__main__":
    build_master_index("data/papers/qp", "data/keywords/keyword_map.json")
