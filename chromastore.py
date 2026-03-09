# # import json
# # import chromadb
# # from chromadb.utils import embedding_functions
# # import os

# # # ----------------------
# # # Load data
# # # ----------------------
# # with open("data/gita_verses.json", "r", encoding="utf-8") as f:
# #     data = json.load(f)

# # # ----------------------
# # # ChromaDB setup
# # # ----------------------
# # client = chromadb.Client()

# # embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
# #     model_name="all-MiniLM-L6-v2"
# # )
# # data_folder = "data"

# # documents = []
# # metadatas = []
# # ids = []

# # counter = 0

# # for file in os.listdir(data_folder):

# #     if file.endswith(".json"):

# #         source = file.replace(".json", "")

# #         with open(os.path.join(data_folder, file), "r", encoding="utf-8") as f:
# #             data = json.load(f)

# #         for item in data:

# #             documents.append(
# #         f"{item['translation']} Principle: {item['ethical_principle']}"
# #     )

# #             metadatas.append({
# #                 "source": source
# #             })

# #             ids.append(str(counter))
# #             counter += 1
# # collection = client.get_or_create_collection(
# #     name="gita_collection",
# #     embedding_function=embedding_fn
# # )

# # # Add documents if empty
# # if len(collection.get()["documents"]) == 0:
# #     documents = [
# #         f"Chapter {v['chapter']} Verse {v['verse']}. {v['translation']}. Principle: {v['ethical_principle']}"
# #         for v in data
# #     ]
# #     ids = [str(i) for i in range(len(documents))]
# #     collection.add(documents=documents, ids=ids)

# # print("Data stored in ChromaDB successfully!")

# # # ----------------------
# # # User query
# # # ----------------------
# # query = input("Enter your question for DharmaAI: ")

# # # Query ChromaDB
# # results = collection.query(query_texts=[query], n_results=3)

# # top_verses = results["documents"][0]
# # print("\n=== Retrieved Verses ===")
# # for v in top_verses:
# #     print("-", v)

# # ----------------------
# # Mocked AI Advice (without OpenAI)
# # ----------------------
# # This is temporary advice until you have OpenAI API quota
# # print("\n=== DharmaAI Ethical Advice (Mocked) ===")
# # mock_advice = """
# # Based on the Bhagavad Gita principles:
# # - Focus on performing your duty (dharma) without attachment to results.
# # - Control your mind and emotions; respond wisely rather than react impulsively.
# # - Seek balance and act according to righteousness, considering the wellbeing of others.
# # """
# # print(mock_advice)


# # # JSON files (Gita + ethics)
# #         ↓
# # Auto source detection
# #         ↓
# # Store in ChromaDB
# #         ↓
# # User question
# #         ↓
# # Semantic search
# #         ↓
# # Relevant teachings
import os
import json
import chromadb
from chromadb.utils import embedding_functions

# # ----------------------
# ChromaDB setup
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
# Load JSON datasets
# ----------------------

data_folder = "data"

documents = []
metadatas = []
ids = []

counter = 0

for file in os.listdir(data_folder):

    if file.endswith(".json"):

        source = file.replace(".json", "")

        with open(os.path.join(data_folder, file), "r", encoding="utf-8") as f:
            data = json.load(f)
for item in data:

    # ---------- Text extraction ----------
    text = ""

    if "translation" in item:
        text = item["translation"]

    elif "summary" in item:
        text = item["summary"]

    elif "text" in item:
        text = item["text"]

    else:
        text = str(item)

    # ---------- Add ethical principle ----------
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

    print("✅ Data stored in ChromaDB successfully!")

else:
    print("⚡ Data already exists in ChromaDB.")


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

    print(f"\nSource: {meta['source']}")
    print("-", doc)
