import json
import chromadb
from chromadb.utils import embedding_functions
import os

# ----------------------
# Load data
# ----------------------
with open("data/gita_verses.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ----------------------
# ChromaDB setup
# ----------------------
client = chromadb.Client()

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

try:
    collection = client.get_collection("gita_collection")
except:
    collection = client.create_collection(
        name="gita_collection",
        embedding_function=embedding_fn
    )

# Add documents if empty
if len(collection.get()["documents"]) == 0:
    documents = [
        f"Chapter {v['chapter']} Verse {v['verse']}. {v['translation']}. Principle: {v['ethical_principle']}"
        for v in data
    ]
    ids = [str(i) for i in range(len(documents))]
    collection.add(documents=documents, ids=ids)

print("Data stored in ChromaDB successfully!")

# ----------------------
# User query
# ----------------------
query = input("Enter your question for DharmaAI: ")

# Query ChromaDB
results = collection.query(query_texts=[query], n_results=3)

top_verses = results["documents"][0]
print("\n=== Retrieved Verses ===")
for v in top_verses:
    print("-", v)

# ----------------------
# Mocked AI Advice (without OpenAI)
# ----------------------
# This is temporary advice until you have OpenAI API quota
print("\n=== DharmaAI Ethical Advice (Mocked) ===")
mock_advice = """
Based on the Bhagavad Gita principles:
- Focus on performing your duty (dharma) without attachment to results.
- Control your mind and emotions; respond wisely rather than react impulsively.
- Seek balance and act according to righteousness, considering the wellbeing of others.
"""
print(mock_advice)