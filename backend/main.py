from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import os
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .auth import create_access_token, decode_access_token, hash_password, verify_password
from .gateway import router as gateway_router
from .models import Base, ChatMessage, ChatSession, User, engine

Base.metadata.create_all(engine)

app = FastAPI(title="Dharma AI API", version="1.0.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=bool(allowed_origins),
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
    message: str = Field(..., min_length=1, max_length=2000)
    assistant_response: str = Field(..., min_length=1, max_length=10000)
    mode: str = "Calm"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")
        return user


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
        return {
            "id": user.id,
            "username": user.username,
            "created_at": user.created_at.isoformat(),
            "access_token": create_access_token({"sub": user.username}),
            "token_type": "bearer",
        }


@app.post("/auth/login")
def login(request: LoginRequest):
    username = request.username.strip().lower()
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.password_hash or not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid password")

        return {
            "id": user.id,
            "username": user.username,
            "access_token": create_access_token({"sub": user.username}),
            "token_type": "bearer",
        }


@app.post("/chat")
def save_chat(request: MessageRequest, user: User = Depends(current_user)):
    with Session(engine) as session:
        chat = session.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc()).first()
        if not chat:
            chat = ChatSession(user_id=user.id, title="New conversation")
            session.add(chat)
            session.flush()

        session.add(ChatMessage(session_id=chat.id, role="user", content=request.message))
        session.add(ChatMessage(session_id=chat.id, role="assistant", content=request.assistant_response))
        session.commit()

        return {"status": "saved", "session_id": chat.id}


@app.get("/chat/history")
def chat_history(user: User = Depends(current_user)):
    with Session(engine) as session:
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
