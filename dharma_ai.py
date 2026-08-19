import logging
import re
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
    normalized_mode = (mode or "Calm").strip().split()[0]

    if normalized_mode == "Calm":
        return "Respond in a calm, peaceful, emotionally supportive manner."
    elif normalized_mode == "Logical":
        return "Respond with logical reasoning and clear step-by-step thinking."
    elif normalized_mode == "Ethical":
        return "Respond with strong ethical reasoning based on dharma and morality."
    elif normalized_mode == "Motivational":
        return "Respond in an inspiring, energetic, and uplifting way."
    elif normalized_mode == "Direct":
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

    simple_question_match = re.match(r"^(what|who|why|how)\s+(is|are|do|does|can)\s+(.+?)[?.]?$", q)
    if simple_question_match and len(q.split()) <= 8:
        subject = simple_question_match.group(3).strip().replace("-", " ").strip()
        return (
            f"{mode_instruction}\n\n"
            f"{subject.capitalize()} can be understood as a guiding idea rooted in awareness, balance, and kindness. "
            "A practical way to approach it is to pause, reflect on your values, and choose the action that is compassionate and helpful."
        )

    return None


# ----------------------
# MAIN FUNCTION
# ----------------------

def _preprocess_query(q: str) -> str:
    if not q:
        return ""
    # simple cleanup: strip and collapse whitespace
    q = q.strip()
    q = re.sub(r"\s+", " ", q)
    return q


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

        q_clean = _preprocess_query(q)

        # Query ChromaDB
        results = collection.query(
            query_texts=[q_clean],
            n_results=5
        )

        docs = results.get("documents", [[]])[0] or []
        metas = results.get("metadatas", [[]])[0] or []
        dists = results.get("distances", [[]])[0] or []

        if not docs:
            return fallback

        # Build and sort by distance (smaller = more similar)
        items = []
        for idx, doc in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            dist = dists[idx] if idx < len(dists) else 0
            items.append({"doc": doc, "meta": meta or {}, "dist": dist})

        items.sort(key=lambda x: x.get("dist", 0))

        # Guardrail: if top match is not similar enough, avoid hallucinating
        if dists and len(dists) and items[0].get("dist", 0) > 0.5:
            return (
                "I couldn't find reliable references in the knowledge base to confidently answer that. "
                "Here's a gentle fallback:\n\n" + fallback
            )

        # Compose context and a simple source list (first 3)
        top_items = items[:3]
        context = "\n\n".join([f"{i+1}. {it['doc']}" for i, it in enumerate(top_items)])
        sources = []
        for i, it in enumerate(top_items):
            src = None
            if isinstance(it.get("meta"), dict):
                src = it["meta"].get("source")
            if src:
                sources.append(f"{i+1}. {src}")

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
            text = response.choices[0].message.content

            # Append explicit source attribution produced from the retrieval step.
            if sources:
                text = text.strip() + "\n\nSources:\n" + "\n".join(sources)

            return text

    except Exception as error:
        logging.exception("Failed to generate Dharma-AI response")

    return fallback
