from dotenv import load_dotenv
import os

load_dotenv()

import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

# ----------------------
# ChromaDB Setup
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
# Groq Setup
# ----------------------

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ----------------------
# Query Input
# ----------------------

query = input("\n Ask DharmaAI: ")

# ----------------------
# Retrieve Knowledge
# ----------------------

results = collection.query(
    query_texts=[query],
    n_results=5
)

docs = results["documents"][0]

context = "\n".join(docs)

# ----------------------
# Prompt Engineering (VERY IMPORTANT)
# ----------------------

prompt = f"""
You are Dharma AI, a wise and calm guide based on ethical teachings 
from Bhagavad Gita, Ramayana, Mahabharata, and world philosophy.

Use the context below to answer the user's question.

Context:
{context}

Question:
{query}

Instructions:
- Answer in a calm, wise tone
- Give practical life advice
- Keep it simple and meaningful
- Do NOT repeat context directly

Answer:
"""

# ----------------------
# Generate Answer
# ----------------------

response = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print("\nDharma AI Says:\n")
print(response.choices[0].message.content)