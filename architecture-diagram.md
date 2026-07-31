# Architecture Diagram

```mermaid
flowchart LR
    User[User] --> Frontend[Streamlit Frontend]
    Frontend --> Gateway[FastAPI Gateway / Auth API]
    Gateway --> DB[(PostgreSQL / SQLite)]
    Gateway --> Vector[(ChromaDB Vector Store)]
    Gateway --> LLM[Groq LLM]
    Vector --> LLM
```

## Components
- Streamlit frontend for the chat experience
- FastAPI backend for API routes and auth
- SQLAlchemy models for users and chat sessions
- PostgreSQL for production persistence
- ChromaDB for semantic retrieval
- Groq for LLM-based answer generation
