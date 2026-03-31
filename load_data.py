import os
import json
import chromadb
from chromadb.utils import embedding_functions

# Persistent DB
client = chromadb.Client(
    settings=chromadb.Settings(
        persist_directory="./chroma_db"
    )
)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="ethics_collection",
    embedding_function=embedding_fn
)

data_folder = "data"

documents = []
metadatas = []
ids = []

counter = 0

for file in os.listdir(data_folder):
    if file.endswith(".json"):
        with open(os.path.join(data_folder, file), "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]

        for item in data:
            text = (
                item.get("translation")
                or item.get("summary")
                or item.get("text")
                or str(item)
            )

            principle = item.get("ethical_principle", "")

            full_text = f"{text} Principle: {principle}"

            documents.append(full_text)

            metadatas.append({
                "source": item.get("source", file)
            })

            ids.append(str(counter))
            counter += 1

# Store
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)



print("✅ Data stored successfully!")