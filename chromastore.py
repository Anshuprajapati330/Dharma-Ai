import os
import json
import chromadb
from chromadb.utils import embedding_functions

# ----------------------
# Setup ChromaDB
# ----------------------

client = chromadb.Client()

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="ethics_collection",
    embedding_function=embedding_fn
)

# ----------------------
# Get correct data folder path
# ----------------------

base_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(base_dir, "data")

print("Working Directory:", base_dir)
print("Data Folder Path:", data_folder)

# ----------------------
# Load JSON datasets
# ----------------------

documents = []
metadatas = []
ids = []

counter = 0

# Check if folder exists
if not os.path.exists(data_folder):
    raise FileNotFoundError(f"Data folder not found at: {data_folder}")

for file in os.listdir(data_folder):

    if file.endswith(".json"):

        file_path = os.path.join(data_folder, file)
        source = file.replace(".json", "")

        print("Loading:", file)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure it's a list
        if isinstance(data, dict):
            data = [data]

        for item in data:

            # ----------------------
            # Extract text
            # ----------------------
            if "translation" in item:
                text = item["translation"]

            elif "summary" in item:
                text = item["summary"]

            elif "text" in item:
                text = item["text"]

            else:
                text = str(item)

            # ----------------------
            # Add ethical principle
            # ----------------------
            principle = item.get("ethical_principle", "")

            full_text = f"{text} Principle: {principle}"

            documents.append(full_text)

            metadatas.append({
                "source": item.get("source", source)
            })

            ids.append(str(counter))
            counter += 1

# ----------------------
# Store in ChromaDB
# ----------------------

existing = collection.get()

if len(existing["ids"]) == 0:

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print("Data stored in ChromaDB successfully!")

else:
    print("Data already exists in ChromaDB.")

# ----------------------
# User Query
# ----------------------

query = input("\nEnter your question for DharmaAI: ")

results = collection.query(
    query_texts=[query],
    n_results=5
)

top_results = results["documents"][0]
sources = results["metadatas"][0]

print("\n=== Retrieved Ethical Teachings ===")

for doc, meta in zip(top_results, sources):
    print("\nSource:", meta["source"])
    print("-", doc)