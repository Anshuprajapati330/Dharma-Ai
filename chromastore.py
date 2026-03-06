import json
import chromadb
from chromadb.utils import embedding_functions

# Load data
with open("New folder/gita_verses.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Create Chroma client
client = chromadb.Client()

# Use sentence transformer embedding
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create collection
collection = client.create_collection(
    name="gita_collection",
    embedding_function=sentence_transformer_ef
)

# Prepare documents
documents = []
ids = []

for i, verse in enumerate(data):
    text = f"Chapter {verse['chapter']} Verse {verse['verse']}. {verse['translation']}. Principle: {verse['ethical_principle']}"
    documents.append(text)
    ids.append(str(i))

# Add to Chroma
collection.add(
    documents=documents,
    ids=ids
)

print("Data stored in ChromaDB successfully!")

# Query
query = "Should I switch my job due to stress?"

results = collection.query(
    query_texts=[query],
    n_results=3
)

print("\n=== DharmaAI Response ===")
for result in results["documents"][0]:
    print("-", result)