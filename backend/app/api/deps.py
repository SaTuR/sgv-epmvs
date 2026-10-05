import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.db import SessionLocal
from app.models import User

bearer = HTTPBearer(auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload.get("sub", ""))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o vencido")
    user = db.scalar(select(User).where(User.id == user_id, User.active.is_(True)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no disponible")
    return user

def require_permission(code: str):
    def checker(user: User = Depends(get_current_user)):
        granted = {p.code for role in user.roles for p in role.permissions}
        if "system.admin" not in granted and code not in granted:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para esta acción")
        return user
    return checker


def require_any_permission(*codes: str):
    def checker(user: User = Depends(get_current_user)):
        granted = {p.code for role in user.roles for p in role.permissions}
        if "system.admin" not in granted and not any(code in granted for code in codes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para esta acción")
        return user
    return checker
