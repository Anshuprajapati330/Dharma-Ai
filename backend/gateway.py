from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .auth import create_access_token, decode_access_token, hash_password, verify_password
from .models import User, engine

router = APIRouter(prefix="/api", tags=["gateway"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


@router.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        existing = session.query(User).filter(User.username == form.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")

        user = User(username=form.username, password_hash=hash_password(form.password))
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token({"sub": user.username})
        return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == form.username).first()
        if not user or not verify_password(form.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": user.username})
        return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "username": user.username}}


@router.get("/me")
def me(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"username": username}
