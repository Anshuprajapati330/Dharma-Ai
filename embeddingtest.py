

import json
from sentence_transformers import SentenceTransformer

# load data
with open("New folder/gita_verses.json", "r", encoding="utf-8") as f:
    data = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [
    f"Chapter {v['chapter']} Verse {v['verse']} {v['ethical_principle']}"
    for v in data
]

embeddings = model.encode(texts)

print("Total embeddings:", len(embeddings))
print("Embedding size:", len(embeddings[0]))
import numpy as np

query = "Should I switch my job due to stress?"

query_embedding = model.encode([query])

# cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# similarity check
scores = []

for emb in embeddings:
    score = cosine_similarity(query_embedding[0], emb)
    scores.append(score)

# best match
best_index = np.argmax(scores)

print("Best Match:")
print(data[best_index])
