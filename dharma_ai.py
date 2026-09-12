import logging
import json
import re
from functools import lru_cache
from dotenv import load_dotenv
import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

load_dotenv()
logging.basicConfig(level=logging.INFO)
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

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

    if collection.count() == 0:
        data_folder = os.path.join(os.path.dirname(__file__), "data")
        documents = []
        metadatas = []
        ids = []

        for filename in sorted(os.listdir(data_folder)):
            if not filename.endswith(".json"):
                continue

            with open(os.path.join(data_folder, filename), "r", encoding="utf-8") as data_file:
                records = json.load(data_file)

            if isinstance(records, dict):
                records = [records]

            for record in records:
                text = (
                    record.get("translation")
                    or record.get("summary")
                    or record.get("text")
                    or str(record)
                )
                principle = record.get("ethical_principle", "")
                documents.append(f"{text} Principle: {principle}")
                metadatas.append({"source": record.get("source", filename)})
                ids.append(f"{filename}-{len(ids)}")

        if documents:
            collection.add(documents=documents, metadatas=metadatas, ids=ids)

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
    if "stress" in q or "stressed" in q:
        return (
            "Reduce the pressure to the next manageable step. Write down what is urgent, "
            "what can wait, and one action you can finish in the next ten minutes."
        )

    if "anxious" in q or "anxiety" in q or "worry" in q or "worried" in q:
        return (
            "Separate what you can control from what you cannot. Take one slow breath, "
            "then act on the smallest useful thing within your control."
        )

    if "sad" in q or "sadness" in q or "depressed" in q:
        return (
            "Do not carry this alone. Tell someone you trust how you are feeling, "
            "and give yourself one gentle, practical task for today."
        )

    if "angry" in q or "anger" in q or "frustrated" in q or "upset" in q:
        if "upset" in q and "angry" not in q and "anger" not in q and "frustrated" not in q:
            return (
                "I am sorry you are feeling upset. Take a slow breath and give yourself a moment. "
                "You do not have to solve everything right now; tell me what happened, and we can think it through together."
            )
        return (
            "Create a little space before responding. Name what crossed a boundary, "
            "decide what outcome you want, and speak once your words can be constructive."
        )

    if "tired" in q or "exhausted" in q:
        return (
            "Treat rest as part of the work. Pause, drink some water, and choose one "
            "necessary task instead of trying to solve everything at once."
        )

    if "mental health" in q or "mental wellbeing" in q or "mental wellness" in q:
        return (
            "Care for your mental health one small step at a time:\n"
            "1. Keep a simple routine with regular sleep and meals.\n"
            "2. Take short breaks and gently bring your attention back when your mind wanders.\n"
            "3. Talk honestly with someone you trust.\n\n"
            "If these feelings continue or make daily life difficult, a qualified "
            "mental-health professional can support you. You do not have to handle it alone.\n\n"
            "Source: Bhagavad Gita, Chapter 6, Verses 5, 6, and 26 (adapted). "
            "These verses reflect self-support, awareness of the mind, and returning it "
            "gently to steadiness. The practical care steps above are modern supportive guidance."
        )

    if "fight" in q or "fighting" in q or "conflict" in q:
        return (
            "Do not choose a fight out of anger or pride. First try calm conversation, "
            "clear boundaries, and help from a trusted person. If someone is in immediate "
            "danger, move to a safe place and contact local emergency support.\n\n"
            "Source: Mahabharata, Krishna's diplomacy, and Bhagavad Gita, Chapter 2 "
            "(adapted): peaceful resolution should be tried first, and any difficult "
            "action must be guided by protection, responsibility, and dharma rather than anger."
        )

    decision_words = ("decision", "decide", "choose", "choice")
    family_words = ("family", "parents", "mother", "father")
    work_words = ("job", "career", "work", "office")
    if any(word in q for word in decision_words) and any(word in q for word in family_words) and any(word in q for word in work_words):
        return (
            "When family and career pull you in different directions, do not decide from guilt or pressure. "
            "Write down the real need on each side, check which responsibility is urgent, and look for a practical middle path "
            "such as flexible hours, shared support, or a clear timeline. Discuss the decision honestly with your family and choose "
            "the option that protects your responsibilities without abandoning your long-term well-being.\n\n"
            "Source: Mahabharata, Arjuna's moral dilemma (adapted). The teaching is that difficult choices should be guided by "
            "duty, responsibility, and righteousness rather than emotion alone."
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


@lru_cache(maxsize=128)
def generate_response(query, mode="Calm"):
    if not query or not query.strip():
        return "Please enter a question so Dharma-AI can help you."

    mode_instruction = get_mode_prompt(mode)
    q = query.strip()

    unable_to_answer = (
        "I couldn't find a reliable source in Dharma-AI's knowledge base for this question, "
        "so I won't invent an answer. Please ask about ethics, life decisions, mental well-being, "
        "or teachings from the Gita, Ramayana, and Mahabharata."
    )

    quick_reply = generate_quick_response(q, mode_instruction)
    if quick_reply:
        return quick_reply

    try:
        collection = load_chroma()

        q_clean = _preprocess_query(q)

        # Query ChromaDB
        results = collection.query(
            query_texts=[q_clean],
            n_results=3
        )

        docs = results.get("documents", [[]])[0] or []
        metas = results.get("metadatas", [[]])[0] or []
        dists = results.get("distances", [[]])[0] or []

        if not docs:
            return unable_to_answer

        # Build and sort by distance (smaller = more similar)
        items = []
        for idx, doc in enumerate(docs):
            meta = metas[idx] if idx < len(metas) else {}
            dist = dists[idx] if idx < len(dists) else 0
            items.append({"doc": doc, "meta": meta or {}, "dist": dist})

        items.sort(key=lambda x: x.get("dist", 0))

        # Guardrail: if top match is not similar enough, avoid hallucinating
        if dists and len(dists) and items[0].get("dist", 0) > 0.78:
            return unable_to_answer

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

        source_text = sources[0].split(". ", 1)[-1] if sources else "the Dharma-AI knowledge base"
        grounded_fallback = (
            "I found this relevant teaching in the knowledge base.\n\n"
            f"{top_items[0]['doc']}\n\n"
            "Reflection: apply this idea to your situation with compassion, responsibility, "
            f"and attention to what you can control.\n\nSource: {source_text}"
        )

        if not os.getenv("GROQ_API_KEY"):
            return grounded_fallback

        groq_client = load_groq()

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
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            timeout=3,
        )

        if response and getattr(response, "choices", None):
            text = response.choices[0].message.content

            # Append explicit source attribution produced from the retrieval step.
            if sources:
                text = text.strip() + "\n\nSources:\n" + "\n".join(sources)

            return text

    except Exception as error:
        logging.exception("Failed to generate Dharma-AI response")
        if "grounded_fallback" in locals():
            return grounded_fallback

    return unable_to_answer
