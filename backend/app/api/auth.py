from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMe

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    return TokenResponse(access_token=create_access_token(str(user.id)))

@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user)):
    permissions = sorted({p.code for role in user.roles for p in role.permissions})
    return UserMe(
        id=str(user.id), identification=user.identification, first_name=user.first_name,
        last_name=user.last_name, email=user.email, roles=[r.name for r in user.roles],
        permissions=permissions,
    )
