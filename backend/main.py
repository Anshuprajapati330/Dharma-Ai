from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import hash_password, verify_password
from .gateway import router as gateway_router
from .models import ChatMessage, ChatSession, User, engine
from .models import Base

Base.metadata.create_all(engine)

app = FastAPI(title="Dharma AI API", version="1.0.0")
app.include_router(gateway_router)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class MessageRequest(BaseModel):
    username: str
    message: str
    mode: str = "Calm"


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "dharma-ai-api"}


@app.post("/auth/register")
def register(request: RegisterRequest):
    with Session(engine) as session:
        existing = session.query(User).filter(User.username == request.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        user = User(
            username=request.username,
            password_hash=hash_password(request.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "username": user.username, "created_at": user.created_at.isoformat()}


@app.post("/auth/login")
def login(request: LoginRequest):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == request.username).first()
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
