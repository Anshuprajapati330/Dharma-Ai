from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .auth import hash_password, verify_password
from .gateway import router as gateway_router
from .models import Base, ChatMessage, ChatSession, User, engine

Base.metadata.create_all(engine)

app = FastAPI(title="Dharma AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(gateway_router)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class MessageRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    message: str = Field(..., min_length=1, max_length=2000)
    mode: str = "Calm"


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "dharma-ai-api"}


@app.post("/auth/register")
def register(request: RegisterRequest):
    username = request.username.strip().lower()
    with Session(engine) as session:
        existing = session.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        user = User(
            username=username,
            password_hash=hash_password(request.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "username": user.username, "created_at": user.created_at.isoformat()}


@app.post("/auth/login")
def login(request: LoginRequest):
    username = request.username.strip().lower()
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.password_hash or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")

        return {"id": user.id, "username": user.username}


@app.post("/chat")
def save_chat(request: MessageRequest):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == request.username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        chat = session.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc()).first()
        if not chat:
            chat = ChatSession(user_id=user.id, title="New conversation")
            session.add(chat)
            session.flush()

        session.add(ChatMessage(session_id=chat.id, role="user", content=request.message))
        session.add(ChatMessage(session_id=chat.id, role="assistant", content=f"Echo: {request.message} [{request.mode}]"))
        session.commit()

        return {"status": "saved", "session_id": chat.id}


@app.get("/chat/history/{username}")
def chat_history(username: str):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        chats = session.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc()).all()
        return [
            {
                "id": chat.id,
                "title": chat.title,
                "messages": [
                    {"role": message.role, "content": message.content}
                    for message in sorted(chat.messages, key=lambda m: m.created_at)
                ],
            }
            for chat in chats
        ]
