from dotenv import load_dotenv
import os

load_dotenv()

import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

# ----------------------
# ChromaDB Setup
# ----------------------

import streamlit as st

@st.cache_resource
def load_chroma():
    client = chromadb.Client()

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name="ethics_collection",
        embedding_function=embedding_fn
    )

    return collection

collection = load_chroma()

# ----------------------
# Groq Setup
# ----------------------

@st.cache_resource
def load_groq():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

groq_client = load_groq()



def get_mode_prompt(mode):
    if mode == "Calm":
        return "Respond in a calm, peaceful, emotionally supportive manner."

    elif mode == "Logical":
        return "Respond with logical reasoning and clear step-by-step thinking."

    elif mode == "Ethical":
        return "Respond with strong ethical reasoning based on dharma and morality."

    elif mode == "Motivational":
        return "Respond in an inspiring, energetic, and uplifting way."

    elif mode == "Direct":
        return "Respond briefly, clearly, and directly without extra explanation."

    else:
        return "Respond normally."

# ----------------------
<<<<<<< HEAD
# MAIN FUNCTION
=======
# Query Input 
>>>>>>> 4a3ed04e6760f2b5c43e0b29877c74ef4c57577c
# ----------------------

def generate_response(query, mode="Calm"):
    import chromadb
    # Retrieve knowledge
    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    docs = results["documents"][0]
    context = "\n".join(docs)

    # Mode instruction
    mode_instruction = get_mode_prompt(mode)

    # Final Prompt
    prompt = f"""
You are Dharma AI, a wise and calm guide based on ethical teachings 
from Bhagavad Gita, Ramayana, Mahabharata, and world philosophy.

{mode_instruction}

Context:
{context}

Question:
{query}

Instructions:
- Give practical life advice
- Keep it simple and meaningful
- Do NOT repeat context directly

Answer:
"""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

<<<<<<< HEAD
    return response.choices[0].message.content
=======
response = groq_client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print("\nDharma AI Says:\n")
print(response.choices[0].message.content)
>>>>>>> 4a3ed04e6760f2b5c43e0b29877c74ef4c57577c
