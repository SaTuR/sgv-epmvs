from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserMe(BaseModel):
    id: str
    identification: str | None = None
    first_name: str
    last_name: str
    email: EmailStr
    roles: list[str]
    permissions: list[str]
