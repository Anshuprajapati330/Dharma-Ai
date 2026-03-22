# import json
# print("File is running...")
# with open("data/gita_verses.json", "r", encoding="utf-8") as f:

#     data = json.load(f)

# print("Total verses:", len(data))
# print("First verse:", data[0])


import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.Client()
collection = client.get_collection("ethics_collection")

query = "How to stay calm during success and failure"

embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[embedding],
    n_results=3
)

print(results["documents"])