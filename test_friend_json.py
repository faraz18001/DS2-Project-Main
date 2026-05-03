import json
from worksheet_generator import generate_worksheet
import os

with open('data/index/physics_master_index.json') as f:
    data = json.load(f)

# Get some questions from the store
questions = []
qs = data.get('question_store', {})
if isinstance(qs, dict):
    q_list = list(qs.values())
else:
    q_list = qs

# Pick specific diagram-heavy questions from Paper 22
target_ids = ['9702_w25_p22_q2', '9702_w25_p22_q3', '9702_w25_p22_q5']
questions = [q for q in q_list if q.get('id') in target_ids]

for q in questions:
    print(f"Using question {q.get('id')} from {q.get('pdf')}")

output_path = os.path.join('data', 'output', 'friend_test_worksheet.pdf')
result = generate_worksheet(
    selected_questions=questions,
    output_path=output_path,
    title='Friend JSON Test Worksheet'
)
print(f"Done. Worksheet saved to: {result}")
