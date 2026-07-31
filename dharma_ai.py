import logging
from functools import lru_cache
from dotenv import load_dotenv
import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ----------------------
# ChromaDB Setup
# ----------------------

@lru_cache(maxsize=1)
def load_chroma():
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

    return collection


@lru_cache(maxsize=1)
def load_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GROQ_API_KEY in .env file")
    return Groq(api_key=api_key)


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


def generate_quick_response(query, mode_instruction):
    q = (query or "").strip().lower()
    if not q:
        return None

    emotional_keywords = [
        "feel", "feeling", "sad", "angry", "stress", "stressed",
        "confused", "lost", "anxious", "depressed", "frustrated", "tired"
    ]
    guidance_keywords = [
        "should i", "what should i do", "advice", "help", "decision",
        "problem", "struggle", "difficult", "guide me"
    ]

    if any(keyword in q for keyword in emotional_keywords):
        return (
            f"{mode_instruction}\n\n"
            "Pause for a moment, take a slow breath, and name the feeling clearly. "
            "Then choose one small step that is honest, compassionate, and helpful right now."
        )

    if any(keyword in q for keyword in guidance_keywords):
        return (
            f"{mode_instruction}\n\n"
            "A balanced answer is to pause, reflect on your values, and choose the action that is honest, compassionate, and helpful to both yourself and others."
        )

    return None


# ----------------------
# MAIN FUNCTION
# ----------------------

def generate_response(query, mode="Calm"):
    if not query or not query.strip():
        return "Please enter a question so Dharma-AI can help you."

    mode_instruction = get_mode_prompt(mode)
    q = query.strip()

    fallback = (
        f"{mode_instruction}\n\n"
        f"You asked: {q}\n\n"
        "A balanced answer is to pause, reflect on your values, and choose the action that is honest, compassionate, and helpful to both yourself and others."
    )

    quick_reply = generate_quick_response(q, mode_instruction)
    if quick_reply:
        return quick_reply

    if not os.getenv("GROQ_API_KEY"):
        return fallback

    try:
        collection = load_chroma()
        groq_client = load_groq()

        results = collection.query(
            query_texts=[q],
            n_results=3
        )

        docs = results.get("documents", [[ ]])[0] or []
        context = "\n".join([doc for doc in docs if doc])

        prompt = f"""
You are Dharma AI, a wise and calm guide based on ethical teachings 
from Bhagavad Gita, Ramayana, Mahabharata, and world philosophy.

{mode_instruction}

Context:
{context}

Question:
{q}

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
            ],
            timeout=5,
        )

        if response and getattr(response, "choices", None):
            return response.choices[0].message.content

    except Exception as error:
        logging.exception("Failed to generate Dharma-AI response")

    return fallback
