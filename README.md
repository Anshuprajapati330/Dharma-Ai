# Dharma-AI

Dharma-AI is an interview-ready AI assistant project that combines a Streamlit frontend, a FastAPI backend, SQLite persistence, and a vector database for retrieval-based responses.

## What makes it interview-ready

- Backend API with authentication and chat persistence
- Database-backed user and chat storage using SQLAlchemy
- Retrieval-augmented responses using ChromaDB and embeddings
- Container and cloud deployment support with Docker and Render
- Test coverage for the backend API

## Project structure

- chatbot.py: Streamlit frontend experience
- backend/main.py: FastAPI backend endpoints
- backend/models.py: SQLAlchemy database models
- dharma_ai.py: response generation with retrieval and Groq
- load_data.py: embedding ingestion for knowledge data
- tests/test_backend.py: backend regression tests

## Run locally

### One-command startup

```bash
python run_app.py
```

This launches:
- Backend API at http://127.0.0.1:8000
- Streamlit UI at http://127.0.0.1:8501

### Manual startup

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
API_BASE_URL=http://127.0.0.1:8000
DATABASE_URL=sqlite:///./dharma.db
```

3. Start the backend API:

```bash
uvicorn backend.main:app --reload
```

4. Start the Streamlit UI:

```bash
streamlit run chatbot.py
```

## Run tests

```bash
python -m pytest -q tests/test_backend.py
```

## Deployment

- Docker: build with `docker build -t dharma-ai .`
- Render: use the included `render.yaml`
- Production idea: move SQLite to PostgreSQL and add auth tokens, logging, and CI/CD

## Interview talking points

- Architecture: frontend + API + database + vector search
- Scalability: replace local file storage with PostgreSQL and managed embeddings
- Production readiness: add Docker, environment variables, tests, and deployment automation
- Future upgrades: JWT auth, Redis caching, async workers, monitoring, and Kubernetes
